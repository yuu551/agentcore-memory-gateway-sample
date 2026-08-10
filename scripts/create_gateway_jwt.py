"""JWT認証(CUSTOM_JWT)のGatewayを作成し、READYになるまで待つ。

カスタム属性を含むIDトークンで認証するため、allowedAudience(audクレーム)で検証する。

usage:
    uv run scripts/create_gateway_jwt.py --name memory-gateway-jwt \
        --role-arn arn:aws:iam::<account-id>:role/memory-gateway-role \
        --pool-id <cognito-user-pool-id> --client-id <app-client-id>
"""
import argparse
import time

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--role-arn", required=True)
    parser.add_argument("--pool-id", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    discovery_url = (
        f"https://cognito-idp.{args.region}.amazonaws.com/"
        f"{args.pool_id}/.well-known/openid-configuration"
    )
    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    response = client.create_gateway(
        name=args.name,
        roleArn=args.role_arn,
        authorizerType="CUSTOM_JWT",
        authorizerConfiguration={
            "customJWTAuthorizer": {
                "discoveryUrl": discovery_url,
                "allowedAudience": [args.client_id],
            }
        },
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
