# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""Gateway経由でMemoryにイベント(CreateEvent)を書き込む。

usage:
    uv run scripts/create_event.py --gateway-id <gateway-id> --memory-id <memory-id> \
        --actor-id blog-test-user --session-id blog-test-session \
        --text "Gateway経由で書き込むテストメッセージです"
"""
import argparse
import json
import time
import urllib.request
import uuid

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-id", required=True)
    parser.add_argument("--memory-id", required=True)
    parser.add_argument("--actor-id", default="blog-test-user")
    parser.add_argument("--session-id", default="blog-test-session")
    parser.add_argument("--text", default="Gateway経由で書き込むテストメッセージです")
    parser.add_argument("--target-name", default="memory-connector")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    gateway_url = (
        f"https://{args.gateway_id}.gateway.bedrock-agentcore."
        f"{args.region}.amazonaws.com"
    )
    url = gateway_url + f"/{args.target_name}/memories/{args.memory_id}/events"
    # SDK経由では自動設定されるclientTokenを、生のHTTPリクエストでは明示的に指定する
    body = {
        "clientToken": str(uuid.uuid4()),
        "actorId": args.actor_id,
        "sessionId": args.session_id,
        "eventTimestamp": int(time.time()),
        "payload": [
            {
                "conversational": {
                    "content": {"text": args.text},
                    "role": "USER",
                }
            }
        ],
    }

    creds = boto3.Session().get_credentials().get_frozen_credentials()
    data = json.dumps(body).encode()
    request = AWSRequest(
        method="POST", url=url, data=data,
        headers={"Content-Type": "application/json"},
    )
    SigV4Auth(creds, "bedrock-agentcore", args.region).add_auth(request)
    req = urllib.request.Request(
        url, data=data, headers=dict(request.headers), method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())


if __name__ == "__main__":
    main()
