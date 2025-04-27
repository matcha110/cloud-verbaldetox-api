# GCP CLIのコマンドまとめ

### Cloud Build
```
gcloud builds submit --tag gcr.io/zenn-hackthon-2/verbaldetox-api

gcloud run deploy verbaldetox-api \
  --image gcr.io/zenn-hackthon-2/verbaldetox-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 300s
```

### test ヘルスチェック
```
curl https://verbaldetox-api-160302376986.us-central1.run.app/diary
```

### test テキスト -> カラー取得
```
curl -X POST \
  -F "uid=test" \
  -F "date=$(date +%Y-%m-%d)"\
  -F "text=今日はとても嬉しい気持ちです" \
  https://verbaldetox-api-160302376986.us-central1.run.app/diary


curl -X POST \
  -F "uid=test" \
  -F "date=$(date +%Y-%m-%d)"\
  -F "text=今日は仕事の締め切りが終わり開放的な気持ちです" \
  https://verbaldetox-api-160302376986.us-central1.run.app/diary


```

### サービスアカウント名の取得
```
gcloud run services describe verbaldetox-api \
  --platform=managed \
  --region=us-central1 \
  --project=zenn-hackthon-2 \
  --format="value(spec.template.spec.serviceAccountName)"
```

### ロールの一覧を取得
```
gcloud projects get-iam-policy zenn-hackthon-2 \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:serviceAccount:160302376986-compute@developer.gserviceaccount.com"

```