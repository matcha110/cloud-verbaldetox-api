# GCP CLIのコマンドまとめ

### Cloud Build
```
gcloud builds submit --tag gcr.io/zenn-hackthon-2/verbaldetox-api
```
### Cloud Run
```
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
  -F "date=$(date +%Y%m%d)" \
  -F "text=今日はとても嬉しい気持ちです" \
  https://verbaldetox-api-160302376986.us-central1.run.app/diary

```