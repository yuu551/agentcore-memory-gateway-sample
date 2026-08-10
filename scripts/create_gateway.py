"""IAM認証(AWS_IAM)のGatewayを作成し、READYになるまで待つ。

usage:
    uv run scripts/create_gateway.py --name memory-gateway-blog \
        --role-arn arn:aws:iam::<account-id>:role/memory-gateway-role
"""
import argparse
import time

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--role-arn", required=True)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    # protocolTypeは指定しない(指定するとMCP専用になりHTTPターゲットを追加できない)
    response = client.create_gateway(
        name=args.name,
        roleArn=args.role_arn,
        authorizerType="AWS_IAM",
    )
    gateway_id = response["gatewayId"]
    print(f"gatewayId: {gateway_id}")

    while True:
        time.sleep(10)
        gateway = client.get_gateway(gatewayIdentifier=gateway_id)
        print(f"status: {gateway['status']}")
        if gateway["status"] in ("READY", "FAILED"):
            break

    if gateway["status"] == "FAILED":
        print(f"statusReasons: {gateway.get('statusReasons')}")
    else:
        print(f"gatewayUrl: {gateway['gatewayUrl']}")


if __name__ == "__main__":
    main()
