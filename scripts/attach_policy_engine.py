# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""Policy EngineをGatewayに紐付ける(LOG_ONLY / ENFORCE)。

Gateway実行ロールにPolicy Engineへのアクセス権限
(GetPolicyEngine / AuthorizeAction / PartiallyAuthorizeActions / CheckAuthorizePermissions)
が必要。setup/add_policy_engine_access.sh を参照。

usage:
    uv run scripts/attach_policy_engine.py --gateway-id <gateway-id> \
        --engine-id <policy-engine-id> --mode LOG_ONLY
"""
import argparse
import time

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-id", required=True)
    parser.add_argument("--engine-id", required=True)
    parser.add_argument("--mode", choices=["LOG_ONLY", "ENFORCE"], default="LOG_ONLY")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    engine_arn = (
        f"arn:aws:bedrock-agentcore:{args.region}:{account_id}"
        f":policy-engine/{args.engine_id}"
    )

    gateway = client.get_gateway(gatewayIdentifier=args.gateway_id)
    client.update_gateway(
        gatewayIdentifier=args.gateway_id,
        name=gateway["name"],
        roleArn=gateway["roleArn"],
        authorizerType=gateway["authorizerType"],
        authorizerConfiguration=gateway["authorizerConfiguration"],
        policyEngineConfiguration={"arn": engine_arn, "mode": args.mode},
    )

    while True:
        time.sleep(10)
        gateway = client.get_gateway(gatewayIdentifier=args.gateway_id)
        print(f"status: {gateway['status']}")
        if gateway["status"] in ("READY", "FAILED"):
            break

    print(f"policyEngineConfiguration: {gateway.get('policyEngineConfiguration')}")


if __name__ == "__main__":
    main()
