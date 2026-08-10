#!/usr/bin/env bash
# Gateway実行ロールにPolicy Engineへのアクセス権限を追加する
# (ENFORCEでの紐付けに必要。公式記載の3アクションに加えCheckAuthorizePermissionsも実機で要求された)
# usage: ACCOUNT_ID=123456789012 POLICY_ENGINE_ID=xxx GATEWAY_ID=yyy ./setup/add_policy_engine_access.sh
set -euo pipefail

ROLE_NAME="${ROLE_NAME:-memory-gateway-role}"
REGION="${REGION:-us-east-1}"
: "${ACCOUNT_ID:?ACCOUNT_ID を設定してください}"
: "${POLICY_ENGINE_ID:?POLICY_ENGINE_ID を設定してください}"
: "${GATEWAY_ID:?GATEWAY_ID を設定してください}"

aws iam put-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name policy-engine-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:GetPolicyEngine",
        "bedrock-agentcore:AuthorizeAction",
        "bedrock-agentcore:PartiallyAuthorizeActions",
        "bedrock-agentcore:CheckAuthorizePermissions"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:'"${REGION}"':'"${ACCOUNT_ID}"':policy-engine/'"${POLICY_ENGINE_ID}"'*",
        "arn:aws:bedrock-agentcore:'"${REGION}"':'"${ACCOUNT_ID}"':gateway/'"${GATEWAY_ID}"'"
      ]
    }]
  }'

echo "policy-engine-access を ${ROLE_NAME} に追加しました"
