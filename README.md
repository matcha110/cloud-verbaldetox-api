# 気分屋の芝日記: "音声入力 × AI感情分析 × カラーパレット"日記アプリ

- 「忙しくて日記が続かない…」
- 「タイピングや手帳に書くのが面倒くさい…」
- 「自分の出来事を文字ではなく、一目見てわかる形で客観視したい」
- 「仕事でもプライベートでも文字情報過多で疲れた…」

そんな悩みを解決するために、**音声入力 → AI 感情分析 → カラーパレット**を生成する日記アプリです。

## 概要

ユーザーが音声で日記を記録すると、AIがその内容を分析し、感情を「快・不快」と「覚醒・沈静」の2軸でマッピングします。

分析結果は、ユーザーが設定したカラーパレットに基づいて色付けされ、GitHub風のヒートマップUIに表示されます。これにより、日々の感情の波を直感的に振り返ることができます。

## 対象とするユーザー層
- 忙しい社会人・学生 — まとまった入力時間を確保しにくい
- ライティングが苦手／スマホ入力が遅い人 — 音声入力なら心理的ハードルが低い
- 子育て・介護中のユーザー — 両手がふさがっていても記録できる
- カウンセリングやコーチングを受けているクライアント — 日々の感情を手軽に記録し、セルフケアに役立てたい。客観的な感情の変化を共有したい

## ユーザーが抱える具体的課題
- 入力のハードルが高い — キーボード入力、フリック入力や手書きはまとまった時間や場所を要し、継続が難しい
- 継続モチベーションの低下 — 成果が視覚化されないと達成感が得にくく、習慣化しづらい
- 感情の一目把握が困難 — 長文が蓄積するだけでは気分の傾向が見えない
- 主観に偏った振り返り — 自己評価のみでは感情を過小・過大評価しがち

## 課題へのソリューションと特徴
- 音声入力で録音ボタンを押すだけで記録開始。忙しいシーンでも即座にメモができます。
- Gemini による感情分析 & 1日ごとのカラーパレットを採用
- ラッセルの円環モデル（快／不快 × 覚醒／沈静）に沿って (x, y) 座標を算出し、ユーザーが設定したパレットで色を用いて、AIが感情に合わせて混色
　GitHub風のヒートマップUIに反映し、月・年単位で一目で気分の波を把握できます。
- ヒートマップの空白（未登録日）がひと目で分かるため、自然と「今日も記録しよう」という気持ちが湧き、継続率を向上。
- カスタムパレットで各象限の色を自由に設定可能。好みの色味や見やすいコントラストを選んで自分らしいダイアリーにできます。また、特定の見えにくい色があるユーザーでも楽しめるように意識しています。

## 主要な機能
- ログイン機能
- 1月毎、1年(1月～12月)毎のカレンダー表示
- 音声入力で日記を記録
- 各ユーザー毎に感情に合う色の設定
- 記録した音声をAIが感情分析し、設定した色に合わせて混色・記録
- 感情分析において、ラッセルの円環モデルに基づいて、X軸を快(+)・不快(-)、Y軸を覚醒(+)・沈静(-)とし、各象限を下記のように設定
  - 第一象限：わくわく、楽しい
  - 第二象限：ストレス、緊張、怒り
  - 第三象限：悲しみ、退屈
  - 第四象限：落ち着く、リラックス、癒し

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| バックエンド | FastAPI |
| AI/ML | Vertex AI (Gemini 1.5 Flash) |
| 音声認識 | Google Cloud Speech-to-Text |
| データベース | Google Cloud Firestore |
| ストレージ | Google Cloud Storage |
| フロントエンド | Flutter |

## セットアップ

### 前提条件

- Python 3.9+
- Google Cloud SDK
- Flutter SDK

### インストール

1. リポジトリをクローンします:
   ```bash
   git clone https://github.com/matcha110/verbaldetox.git
   cd cloud-verbaldetox
   ```

2. Pythonの依存関係をインストールします:
   ```bash
   pip install -r requirements.txt
   ```

3. (フロントエンド) Flutterの依存関係をインストールします:
   ```bash
   flutter pub get
   ```

### 実行

1. バックエンドサーバーを起動します:
   ```bash
   uvicorn main:app --reload
   ```

2. (フロントエンド) Flutterアプリを実行します:
   ```bash
   flutter run
   ```

## APIエンドポイント

- `POST /diary/audio`: 音声ファイルをアップロードし、感情分析を実行します。

## 今後の展望
- ランニングコストの削減
- 混色のアルゴリズム、Geminiへのプロンプトの改善　　等