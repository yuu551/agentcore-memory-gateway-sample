"""Memoryへの直接アクセスを拒否するリソースベースポリシーを適用/削除する。

GATEWAY_IAM_ROLEモードではMemoryから見える主体がGateway実行ロールになるため、
aws:PrincipalArn を実行ロールに限定するDenyでGateway経由を強制する。
(実行ロールを共有する全Gatewayに効く点に注意)

usage:
    uv run scripts/put_deny_resource_policy.py --memory-id <memory-id> \
        --gateway-role-name memory-gateway-role
    uv run scripts/put_deny_resource_policy.py --memory-id <memory-id> --delete
"""
import argparse
import json

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-id", required=True)
    parser.add_argument("--gateway-role-name")
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    memory_arn = (
        f"arn:aws:bedrock-agentcore:{args.region}:{account_id}"
        f":memory/{args.memory_id}"
    )

    if args.delete:
        client.delete_resource_policy(resourceArn=memory_arn)
        print("リソースポリシーを削除しました")
        return

    if not args.gateway_role_name:
        parser.error("--gateway-role-name is required unless --delete")

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyExceptGatewayRole",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "bedrock-agentcore:ListActors",
                "Resource": memory_arn,
                "Condition": {
                    "StringNotLike": {
                        "aws:PrincipalArn": f"*role/{args.gateway_role_name}*"
                    }
                },
            }
        ],
    }
    client.put_resource_policy(resourceArn=memory_arn, policy=json.dumps(policy))
    print("リソースポリシーを適用しました(ListActorsが実行ロール以外から拒否されます)")


if __name__ == "__main__":
    main()
