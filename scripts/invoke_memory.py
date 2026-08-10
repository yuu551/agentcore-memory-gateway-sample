# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""IAM認証のGateway経由でMemoryのListActorsを呼び出す(SigV4署名)。

usage:
    uv run scripts/invoke_memory.py --gateway-id <gateway-id> --memory-id <memory-id>
"""
import argparse
import json
import urllib.request

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def call(gateway_url: str, region: str, path: str, body: dict) -> None:
    creds = boto3.Session().get_credentials().get_frozen_credentials()
    url = gateway_url + path
    data = json.dumps(body).encode()
    request = AWSRequest(
        method="POST", url=url, data=data,
        headers={"Content-Type": "application/json"},
    )
    SigV4Auth(creds, "bedrock-agentcore", region).add_auth(request)
    req = urllib.request.Request(
        url, data=data, headers=dict(request.headers), method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-id", required=True)
    parser.add_argument("--memory-id", required=True)
    parser.add_argument("--target-name", default="memory-connector")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    gateway_url = (
        f"https://{args.gateway_id}.gateway.bedrock-agentcore."
        f"{args.region}.amazonaws.com"
    )
    call(
        gateway_url, args.region,
        f"/{args.target_name}/memories/{args.memory_id}/actors",
        {"maxResults": 10},
    )


if __name__ == "__main__":
    main()
