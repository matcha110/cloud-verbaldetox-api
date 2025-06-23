---
title: "FastAPI × Gemini × Flutter で作る『声で書くカラーダイアリー』徹底解説"
emoji: "🎨"
type: "tech"
topics: ["flutter", "fastapi", "vertexai", "gemini", "firebase", "speech-to-text"]
published: false
---
# はじめに
「忙しくて日記が続かない」「自分の感情パターンを文字ではなく、一目見てわかる形で客観視したい」  
そんな悩みを解決するために、**音声／テキスト入力 → AI 感情分析 → カラーヒートマップ**をワンタップで生成するアプリを開発しました。

このアプリを作る際に参考にしたのは、github contributionのheatmapです。
自分がgithubをする中でheatmapを見返したときに、仕事が忙しくて草を生やせなかったことや個人開発や勉強に勤しんでいたときが一目で明らかにわかるので、
日記的な使い方としても楽しんでいる自分に気付きました。
githubを使わない人でも、同じように一目見て、過去の思い出を色だけのカレンダーを見ることで一目で楽しめるアプリを作成したいと思ったことが開発の理由です。
また、日記の欠点である
・書く、打ち込むのが面倒くさい
・後から見返したときに、ある程度読み返せば細かい気持ちなどを見返すことはできるが、一目見て気持ちの変化等がわからない
・自分の感情に対する客観的な評価がしにくい
を解決するという点も配慮しています。


##　1.使用スタック
```
● Python 3.12
● FastAPI 0.110
● Vertex AI (Gemini 1.5‑flash‑002)
● Cloud Speech‑to‑Text
● Cloud Firestore / Cloud Storage
● Flutter 3.22       ● Riverpod 3
● Firebase Auth & AppCheck
● GitHub Actions + Cloud Run
```

## 2. システム全体図

```mermaid

sequenceDiagram
  participant U as Flutter Client
  participant A as FastAPI
  participant GCS as Cloud Storage
  participant STT as Speech‑to‑Text
  participant GEM as Gemini 1.5
  participant FS as Firestore

  U->>A: multipart/form-data (audio/text, uid, date)
  alt audio
    A->>GCS: upload .flac
    A->>STT: gs://.../audio.flac
    STT-->>A: transcript
  end
  A->>GEM: prompt(transcript, palette)
  GEM-->>A: "x=8,y=-2,color=#FFC1CC"
  par
    A->>U: {x,y,color,...} (≤300 ms)
    A->>FS: save(uid/date, x,y,color,transcript)
  end
  FS-->>U: onSnapshot(diagram update)
```

## 3. 採用技術・バージョン詳細

| レイヤ | サービス / ライブラリ | v | 選定理由 |
| --- | --- | --- | --- |
| Backend | **FastAPI** | 0.110 | ASGI + `BackgroundTasks` で簡潔に非同期実装 |
| LLM | **Vertex AI Gemini 1.5‑flash‑002** | 2025‑05 | 128k token, 低レイテンシ & 従量課金 |
| 音声認識 | **Cloud Speech‑to‑Text** | GA | 日本語 diarization が安定、FLAC 対応 |
| Storage | **Cloud Storage** | multi‑reg | 音声を安価に保存、署名 URL も利用可 |
| DB | **Cloud Firestore** | Native | リアルタイムリスナー × クライアントキャッシュ |
| Mobile | **Flutter 3.22** | stable | 単一コードで iOS / Android / Web |
| 状態管理 | **Riverpod 3** | ‑ | DI とスコープが明確、テスト容易 |
| Router | **GoRouter 14** | ‑ | URL ベースの宣言的ナビゲーション |
| Auth | **Firebase Auth** | GA | Email + Google + App Check Debug |
| DevOps | **GitHub Actions** | 2025Q2 | ビルド → コンテナ push → Cloud Run deploy |
| Observability | **Cloud Logging / Error Reporting** | ‑ | Python の `logging.exception` を集約 |

---

## 4 .全体フロー

1. **ユーザー操作**

   * 音声録音を開始／停止
2. **クライアント → API**

   * 音声分析: `POST /diary/audio` に `uid`, `date`, `audio` ファイルを multipart で送信
3. **FastAPI サーバー（Cloud Run）受信**

   * リクエストを受け取り、パラメータ／ファイルを取得
4. **音声 → 文字起こし**（音声送信時）

   * Google Cloud Speech-to-Text API でバイト列を文字化
5. **感情解析 & 配色生成**

   * 文字列を Vertex AI（Gemini）に投げ、
   * レスポンスから (x, y) 座標とカラーコードをパース
6. **Firestore 書き込み**

   * `BackgroundTasks` で非同期にドキュメントを保存
   * ドキュメントID: `{uid}_{date}`
7. **API → クライアント**

   * JSON レスポンスで `x`, `y`, `color` を返却
8. **クライアント表示**

   * 受け取ったカラーを UI に反映、ユーザーが結果を確認

## テキスト結果の編集フロー

1. ユーザーが解析結果テキストを編集
2. 修正テキストを別エンドポイント（例: `POST /diary/text`）に送信
3. API で再解析し、Firestore ドキュメントを更新
4. 更新済み結果をクライアントに返却

以上が、音声対応の感情解析アプリにおける処理概要です。

### 5 Gemini プロンプト要点
- 色のブレンドは、Geminiを利用(線形補完等は行わない)
- **1 行出力**のみ許可 → `re.match()` で厳格パース
- `|x| : |y|` 比で 2 色ブレンド → *色を連続空間に落とし込む*

## 6. ランニングコスト概算

| サービス | 単価 | 月間利用 (例) | 金額 |
| --- | --- | ---:| ---:|
| Cloud Run | 0.000012 $/vCPU‑s | 50 k req × 0.3 s | **0.18 $** |
| Speech‑to‑Text | 0.006 $/min | 1 k 分 | **6.00 $** |
| Gemini Flash | 0.000125 $/1k tokens | 50 k req × 0.5k T | **3.13 $** |
| Storage | 0.026 $/GB | 5 GB | **0.13 $** |
| Firestore | 無料枠内 | – | 0 $ |
| **合計** | — | — | **≈9.4 $/月** |
5000requestで約1500円程度と想定しています。

## 7. セキュリティ / プライバシー

- **認証トークン検証**：Cloud Run *Audience* = Firebase プロジェクト
- **ボイスデータ自動削除**：Lifecycle で 30 日後に削除

## 今後の改善予定
- デザインやUI/UXの改善
- ランニングコストの削減
- 収集した声のデータを用いて、AI学習に使用し、聞き取りの改善・補完
- 色の好みを収集して、提案する色の調整　等
