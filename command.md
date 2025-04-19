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