# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""Memoryコネクタターゲットを作成し、READYになるまで待つ。

usage:
    uv run scripts/create_target.py --gateway-id <gateway-id> \
        --name memory-connector --memory-id <memory-id>
"""
import argparse
import time

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--memory-id", required=True)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    response = client.create_gateway_target(
        gatewayIdentifier=args.gateway_id,
        name=args.name,
        targetConfiguration={
            "http": {
                "connector": {
                    "source": {"connectorId": "agentcore-memory"},
                    "parameters": {"memoryId": args.memory_id},
                }
            }
        },
        credentialProviderConfigurations=[
            {"credentialProviderType": "GATEWAY_IAM_ROLE"}
        ],
    )
    target_id = response["targetId"]
    print(f"targetId: {target_id}")

    while True:
        time.sleep(10)
        target = client.get_gateway_target(
            gatewayIdentifier=args.gateway_id, targetId=target_id
        )
        print(f"status: {target['status']}")
        if target["status"] in ("READY", "FAILED"):
            break

    if target["status"] == "FAILED":
        print(f"statusReasons: {target.get('statusReasons')}")


if __name__ == "__main__":
    main()
