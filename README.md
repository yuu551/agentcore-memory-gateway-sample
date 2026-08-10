# AgentCore Gateway Memory Connector Sample

Amazon Bedrock AgentCore GatewayのHTTPコネクタターゲット(agentcore-memory)で、AgentCore MemoryをGateway越しに公開する検証用サンプルです。

解説記事: (公開後にURLを追記)

公式ドキュメント: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-gateway-connector.html

## 前提

- [uv](https://docs.astral.sh/uv/) がインストール済みであること
- AWS認証情報が設定済みであること(検証リージョン: us-east-1)
- AgentCore Memoryが作成済みであること
- botocore 1.43.65以降(スクリプトの依存としてuvが自動解決します)

各スクリプトは[PEP 723](https://peps.python.org/pep-0723/)のインラインメタデータで依存を宣言しているので、`uv run` だけで実行できます。仮想環境の準備は不要です。

## 実行手順

### 1. IAM認証のGatewayでMemoryを公開する

```sh
# Gateway実行ロールの作成(Memoryへのアクセス権限つき)
ACCOUNT_ID=<アカウントID> MEMORY_ID=<MemoryのID> ./setup/create_role.sh

# Gatewayの作成
uv run scripts/create_gateway.py --name memory-gateway-blog \
  --role-arn arn:aws:iam::<アカウントID>:role/memory-gateway-role

# Memoryコネクタターゲットの作成
uv run scripts/create_target.py --gateway-id <GatewayのID> \
  --name memory-connector --memory-id <MemoryのID>

# 動作確認(ListActors)
uv run scripts/invoke_memory.py --gateway-id <GatewayのID> --memory-id <MemoryのID>

# 書き込み(CreateEvent)と会話履歴の閲覧
uv run scripts/create_event.py --gateway-id <GatewayのID> --memory-id <MemoryのID>
uv run scripts/viewer_demo.py --gateway-id <GatewayのID> --memory-id <MemoryのID> \
  --actor-id blog-test-user
```

### 2. JWT認証とCedarでの認可制御

```sh
# Cognitoユーザープール一式の作成
PASSWORD='<パスワード>' ./setup/setup_cognito.sh

# JWT認証のGateway作成(ターゲット追加は 1. と同じ create_target.py)
uv run scripts/create_gateway_jwt.py --name memory-gateway-jwt \
  --role-arn arn:aws:iam::<アカウントID>:role/memory-gateway-role \
  --pool-id <プールID> --client-id <クライアントID>

# Policy EngineとCedarポリシー一式の作成
uv run scripts/create_jwt_policies.py --engine-name memory_gateway_jwt_engine \
  --gateway-arn arn:aws:bedrock-agentcore:us-east-1:<アカウントID>:gateway/<GatewayのID>

# Gateway実行ロールにPolicy Engineアクセス権限を追加してから紐付け
ACCOUNT_ID=<アカウントID> POLICY_ENGINE_ID=<エンジンID> GATEWAY_ID=<GatewayのID> \
  ./setup/add_policy_engine_access.sh
uv run scripts/attach_policy_engine.py --gateway-id <GatewayのID> \
  --engine-id <エンジンID> --mode LOG_ONLY   # 確認後にENFORCEへ

# トークンで呼び出し(テナント・ロール・アクター単位の認可を確認)
uv run scripts/invoke_with_jwt.py --gateway-id <GatewayのID> \
  --client-id <クライアントID> --username tenant-a-user --password '<パスワード>' \
  --path "/memory-connector/memories/<MemoryのID>/actors"
```

### 3. 直接アクセスの制限

```sh
# Gateway実行ロール以外の直接アクセスを拒否(検証用: ListActorsのみ)
uv run scripts/put_deny_resource_policy.py --memory-id <MemoryのID> \
  --gateway-role-name memory-gateway-role

# 削除(原状復帰)
uv run scripts/put_deny_resource_policy.py --memory-id <MemoryのID> --delete
```

## 後片付け

検証で作成したリソース(Gateway、ターゲット、Policy Engine、Cognitoユーザープール、IAMロール)は、不要になったら削除してください。GatewayはターゲットとPolicy Engineの紐付けを外してから、Policy Engineはポリシーを全削除してから削除します。

## 注意事項

- Cedarポリシーの作成に `validationMode="IGNORE_ALL_FINDINGS"` を使用しています。検証用の回避策のため、本番適用前にはLOG_ONLYモードでの動作確認を挟んでください
- `put_deny_resource_policy.py` のDenyは実行ロールを共有するすべてのGatewayに適用されます
