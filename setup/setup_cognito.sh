#!/usr/bin/env bash
# JWT検証用のCognitoユーザープール一式を作成する
# (プール、カスタム属性 tenant_id / role、アプリクライアント、テナントA/Bのユーザー2人)
# usage: PASSWORD='<password>' ./setup/setup_cognito.sh
set -euo pipefail

POOL_NAME="${POOL_NAME:-memory-gateway-jwt-pool}"
REGION="${REGION:-us-east-1}"
: "${PASSWORD:?PASSWORD を設定してください}"

POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "${POOL_NAME}" --region "${REGION}" \
  --query 'UserPool.Id' --output text)
echo "POOL_ID=${POOL_ID}"

aws cognito-idp add-custom-attributes --user-pool-id "${POOL_ID}" \
  --custom-attributes \
  Name=tenant_id,AttributeDataType=String,Mutable=true \
  Name=role,AttributeDataType=String,Mutable=true

CLIENT_ID=$(aws cognito-idp create-user-pool-client --user-pool-id "${POOL_ID}" \
  --client-name user-client \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query 'UserPoolClient.ClientId' --output text)
echo "CLIENT_ID=${CLIENT_ID}"

create_user() {
  local username="$1" tenant="$2" role="$3"
  aws cognito-idp admin-create-user --user-pool-id "${POOL_ID}" \
    --username "${username}" \
    --user-attributes "Name=custom:tenant_id,Value=${tenant}" "Name=custom:role,Value=${role}" \
    --message-action SUPPRESS > /dev/null
  aws cognito-idp admin-set-user-password --user-pool-id "${POOL_ID}" \
    --username "${username}" --password "${PASSWORD}" --permanent
  echo "user ${username} (${tenant}/${role}) OK"
}

create_user tenant-a-user tenant-a viewer
create_user tenant-b-user tenant-b admin
