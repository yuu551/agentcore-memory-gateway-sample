#!/usr/bin/env bash
# Gateway実行ロールを作成し、対象Memoryへのアクセス権限を付与する
# 権限は検証で使う操作に絞っている。削除系・抽出ジョブ系(DeleteEvent /
# DeleteMemoryRecord / ListMemoryExtractionJobs / StartMemoryExtractionJob)も
# Gateway経由で使う場合は対応するアクションを追加すること
# usage: ACCOUNT_ID=123456789012 MEMORY_ID=xxx ./setup/create_role.sh
set -euo pipefail

ROLE_NAME="${ROLE_NAME:-memory-gateway-role}"
REGION="${REGION:-us-east-1}"
: "${ACCOUNT_ID:?ACCOUNT_ID を設定してください}"
: "${MEMORY_ID:?MEMORY_ID を設定してください}"

aws iam create-role \
  --role-name "${ROLE_NAME}" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
      "Action": "sts:AssumeRole",
      "Condition": {"StringEquals": {"aws:SourceAccount": "'"${ACCOUNT_ID}"'"}}
    }]
  }'

aws iam put-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name memory-connector-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:GetMemory",
        "bedrock-agentcore:CreateEvent",
        "bedrock-agentcore:GetEvent",
        "bedrock-agentcore:ListEvents",
        "bedrock-agentcore:ListSessions",
        "bedrock-agentcore:ListActors",
        "bedrock-agentcore:GetMemoryRecord",
        "bedrock-agentcore:ListMemoryRecords",
        "bedrock-agentcore:RetrieveMemoryRecords"
      ],
      "Resource": "arn:aws:bedrock-agentcore:'"${REGION}"':'"${ACCOUNT_ID}"':memory/'"${MEMORY_ID}"'"
    }]
  }'

echo "created: arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
