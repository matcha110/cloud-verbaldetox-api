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
### test 音声ファイル渡す APItest
```bash
SERVICE_URL="https://verbaldetox-api-160302376986.us-central1.run.app/diary/audio"
FLAC_PATH="./diary/audio/audio_20250522_020600.flac"

curl -v -X POST "${SERVICE_URL}" \
  -F "uid=RqHYhyuPJRTQUCC944gsJPev6vB2" \
  -F "date=2025-05-21" \
  -F "audio=@${FLAC_PATH};type=audio/flac"
```

### logging出力
```bash
gcloud run services logs read verbaldetox-api \
  --project=zenn-hackthon-2 \
  --region=us-central1 \
  --limit=60

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


### 例文(4月)
```bash
curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-01" \
  -F text="4月最初の日は新しい目標を立てて、一日中読書に集中した。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-02" \
  -F text="今日は久しぶりに雨が降り、家でゆっくり映画を観て過ごした。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-03" \
  -F text="週末なので友人とカフェでおしゃべりしながらお茶を楽しんだ。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-04" \
  -F text="散歩中に見つけた野花が可愛くて写真を撮った。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-05" \
  -F text="仕事で少し忙しかったが、夜に美味しいご飯を作ってリフレッシュした。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-06" \
  -F text="朝早く起きてジョギングをしたら気持ちよく一日をスタートできた。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-07" \
  -F text="久しぶりに家族と電話で話して、元気そうな声に安心した。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-08" \
  -F text="仕事終わりに新しいレシピを試して料理を楽しんだ。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-09" \
  -F text="図書館で借りた本が面白くて、つい長時間読みふけってしまった。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-10" \
  -F text="桜が満開の公園を散策して春の訪れを感じた。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-11" \
  -F text="ジムで体を動かした後、心身ともにリフレッシュできた。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-12" \
  -F text="友人からおすすめされた映画を観て感動した。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-13" \
  -F text="仕事の合間に散歩して、青空の下でリラックスした。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-14" \
  -F text="週末のマーケットで新鮮な野菜を買って料理した。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-15" \
  -F text="雨の音を聞きながらゆっくり読書タイムを満喫した。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-16" \
  -F text="久しぶりに絵を描いて創作の楽しさを思い出した。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-17" \
  -F text="山へハイキングに行き、頂上からの景色が最高だった。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-18" \
  -F text="新しいプロジェクトのアイデアを思いついてワクワクした。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-19" \
  -F text="仕事で大きなタスクを終えて達成感を味わった。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-20" \
  -F text="オンラインセミナーに参加して知識を深めることができた。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-21" \
  -F text="公園で読書しながら美味しいアイスを食べた。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-22" \
  -F text="友人と映画館で最新作を一緒に観賞して笑いあった。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-23" \
  -F text="夜空を眺めながら星の輝きに心癒された。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-24" \
  -F text="カフェで仕事をして集中でき、生産的な一日だった。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-25" \
  -F text="家でゆったり音楽を聴きながらリラックスした時間を過ごした。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-26" \
  -F text="美術展を訪れて芸術作品に触れたことで感性が刺激された。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-27" \
  -F text="公園でジョギングして健康的な一日を楽しんだ。"

curl -X POST https://verbaldetox-api-160302376986.us-central1.run.app/diary \
  -F uid="9LZa2PRpt6YW3tzwgUYaP9N11jC2" \
  -F date="2025-04-28" \
  -F text="月末の振り返りをして、来月の目標を考えた。"


```