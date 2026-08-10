# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""JWT Gateway用のPolicy EngineとCedarポリシー一式を作成する。

作成するポリシー:
  1. ベース許可(OAuthUser + 対象Gatewayに限定したpermit)
  2. テナントA制御(Aターゲットの全アクションをtenant_idクレームで制限)
  3. テナントB制御(同上のB版)
  4. 書き込みは管理者のみ(両ターゲットのCreateEventをroleクレームで制限)
  5. 自分のアクター以外を拒否(ListEventsのactorIdをsubクレームと突き合わせ)

クレーム条件は事前検証がOverly Restrictive判定でCREATE_FAILEDになるため、
内容を確認したうえで validationMode="IGNORE_ALL_FINDINGS" を指定している。
本番適用前にはLOG_ONLYモードでの動作確認を推奨。

usage:
    uv run scripts/create_jwt_policies.py --engine-name memory_gateway_jwt_engine \
        --gateway-arn arn:aws:bedrock-agentcore:us-east-1:<account-id>:gateway/<gateway-id> \
        --tenant-a-target memory-connector --tenant-b-target tenant-b-memory
"""
import argparse
import time

import boto3


def wait_active(client, engine_id: str, policy_id: str) -> str:
    while True:
        time.sleep(5)
        policy = client.get_policy(policyEngineId=engine_id, policyId=policy_id)
        if policy["status"] in ("ACTIVE", "FAILED", "CREATE_FAILED"):
            return policy["status"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-name", required=True)
    parser.add_argument("--gateway-arn", required=True)
    parser.add_argument("--tenant-a-target", default="memory-connector")
    parser.add_argument("--tenant-b-target", default="tenant-b-memory")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)

    engine = client.create_policy_engine(name=args.engine_name)
    engine_id = engine["policyEngineId"]
    while True:
        time.sleep(5)
        if client.get_policy_engine(policyEngineId=engine_id)["status"] == "ACTIVE":
            break
    print(f"policyEngineId: {engine_id}")

    gw = args.gateway_arn
    a, b = args.tenant_a_target, args.tenant_b_target
    events_path = "___POST:/memories/{memoryId}/events"
    list_events_path = "___POST:/memories/{memoryId}/actor/{actorId}/sessions/{sessionId}"
    policies = {
        "MemJwtBase": (
            "permit (principal is AgentCore::OAuthUser, action, "
            f'resource == AgentCore::Gateway::"{gw}");'
        ),
        "MemJwtTenantA": (
            "forbid (principal is AgentCore::OAuthUser, "
            f'action in AgentCore::Action::"{a}", '
            f'resource == AgentCore::Gateway::"{gw}") '
            'unless { principal.hasTag("custom:tenant_id") '
            '&& principal.getTag("custom:tenant_id") == "tenant-a" };'
        ),
        "MemJwtTenantB": (
            "forbid (principal is AgentCore::OAuthUser, "
            f'action in AgentCore::Action::"{b}", '
            f'resource == AgentCore::Gateway::"{gw}") '
            'unless { principal.hasTag("custom:tenant_id") '
            '&& principal.getTag("custom:tenant_id") == "tenant-b" };'
        ),
        "MemJwtWriteAdmin": (
            "forbid (principal is AgentCore::OAuthUser, "
            f'action in [AgentCore::Action::"{a}{events_path}", '
            f'AgentCore::Action::"{b}{events_path}"], '
            f'resource == AgentCore::Gateway::"{gw}") '
            'unless { principal.hasTag("custom:role") '
            '&& principal.getTag("custom:role") == "admin" };'
        ),
        "MemJwtActorSelf": (
            "forbid (principal is AgentCore::OAuthUser, "
            f'action == AgentCore::Action::"{a}{list_events_path}", '
            f'resource == AgentCore::Gateway::"{gw}") '
            'unless { principal.hasTag("sub") && context has input '
            "&& context.input has actorId "
            '&& context.input.actorId == principal.getTag("sub") };'
        ),
    }

    for name, statement in policies.items():
        response = client.create_policy(
            policyEngineId=engine_id,
            name=name,
            definition={"policy": {"statement": statement}},
            validationMode="IGNORE_ALL_FINDINGS",
        )
        status = wait_active(client, engine_id, response["policyId"])
        print(f"{name}: {status}")

    print("\n次のコマンドでGatewayにENFORCEモードで紐付けてください:")
    print(
        "  uv run scripts/attach_policy_engine.py "
        f"--gateway-id <gateway-id> --engine-id {engine_id} --mode ENFORCE"
    )


if __name__ == "__main__":
    main()
