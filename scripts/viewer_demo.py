# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3>=1.43.65"]
# ///
"""管理画面役: Gateway経由でMemoryの会話履歴を閲覧する(Memoryへの直接権限は不要)。

usage:
    uv run scripts/viewer_demo.py --gateway-id <gateway-id> --memory-id <memory-id> \
        --actor-id customer-001
"""
import argparse
import json
import urllib.request

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-id", required=True)
    parser.add_argument("--memory-id", required=True)
    parser.add_argument("--actor-id", required=True)
    parser.add_argument("--target-name", default="memory-connector")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    gateway_url = (
        f"https://{args.gateway_id}.gateway.bedrock-agentcore."
        f"{args.region}.amazonaws.com"
    )
    creds = boto3.Session().get_credentials().get_frozen_credentials()

    def call(path: str, body: dict) -> dict:
        url = gateway_url + path
        data = json.dumps(body).encode()
        request = AWSRequest(
            method="POST", url=url, data=data,
            headers={"Content-Type": "application/json"},
        )
        SigV4Auth(creds, "bedrock-agentcore", args.region).add_auth(request)
        req = urllib.request.Request(
            url, data=data, headers=dict(request.headers), method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    # 1. 顧客のセッション一覧
    sessions = call(
        f"/{args.target_name}/memories/{args.memory_id}/actor/{args.actor_id}/sessions",
        {"maxResults": 10},
    )
    print(f"=== {args.actor_id} のセッション一覧 ===")
    for s in sessions["sessionSummaries"]:
        print(f"  {s['sessionId']}")

    # 2. セッションを選んで会話履歴を表示
    session_id = sessions["sessionSummaries"][0]["sessionId"]
    events = call(
        f"/{args.target_name}/memories/{args.memory_id}"
        f"/actor/{args.actor_id}/sessions/{session_id}",
        {"maxResults": 50},
    )
    print(f"\n=== 会話履歴: {session_id} ===")
    for e in sorted(events["events"], key=lambda x: x["eventTimestamp"]):
        for p in e["payload"]:
            conv = p.get("conversational")
            if conv:
                speaker = "顧客" if conv["role"] == "USER" else "エージェント"
                print(f"  [{speaker}] {conv['content']['text']}")


if __name__ == "__main__":
    main()
