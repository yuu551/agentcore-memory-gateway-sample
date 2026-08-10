# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""CognitoでログインしてIDトークンを取得し、JWT Gateway経由でMemoryを呼び出す。

usage:
    uv run scripts/invoke_with_jwt.py --gateway-id <gateway-id> --memory-id <memory-id> \
        --client-id <app-client-id> --username tenant-a-user --password '<password>' \
        --path "/memory-connector/memories/<memory-id>/actors"
"""
import argparse
import json
import urllib.request

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-id", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    cognito = boto3.client("cognito-idp", region_name=args.region)
    result = cognito.initiate_auth(
        ClientId=args.client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": args.username, "PASSWORD": args.password},
    )
    # カスタム属性はIDトークンにのみ含まれる(アクセストークンには入らない)
    id_token = result["AuthenticationResult"]["IdToken"]

    url = (
        f"https://{args.gateway_id}.gateway.bedrock-agentcore."
        f"{args.region}.amazonaws.com{args.path}"
    )
    data = json.dumps({"maxResults": 10}).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {id_token}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())


if __name__ == "__main__":
    main()
