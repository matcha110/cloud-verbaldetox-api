# システムアーキテクチャ

以下の構成でモバイルアプリから認証付き API → AI モデル → データベースまでを安全・スケーラブルに運用します。

---

## 1. 全体図（High-Level）
```text
[Flutter App]               ←─ ユーザー操作／認証トークン取得
     │
     │ 1) IDトークン付きリクエスト
     ▼
[Firebase Authentication]   ←─ サインイン／IDトークン発行
     │
     │ 2) 認証チェック
     ▼
[FastAPI (Cloud Run)]       ←─ テキスト送信／AI推論／DB書き込み
     │            │
     │            │ 4) AI 推論リクエスト
     │            ▼
     │         [Vertex AI]   ←─ テキスト解析 → (x, y, color)
     │            │
     │ 5) 推論結果
     │            │
     │ 6) Firestore 保存
     ▼
[Cloud Firestore]           ←─ ユーザー設定 & 日記データ保持
```

---

## 2. コンポーネント詳細

| レイヤー            | 技術／サービス                   | 役割                                                  |
|---------------------|---------------------------------|-------------------------------------------------------|
| **Frontend**        | Flutter                         | ・UI (テキスト入力、カラー & グラフ表示)
|                     |                                 | ・FastAPI への API 呼び出し
|                     |                                 | ・Firebase Auth によるログイン                        |
| **Authentication**  | Firebase Authentication         | ・ユーザー認証 (サインアップ / サインイン)
|                     |                                 | ・ID トークン発行                                     |
| **API 層**          | FastAPI (Cloud Run)             | ・REST エンドポイント (`/diary` 等)
|                     |                                 | ・Firebase Auth トークン検証
|                     |                                 | ・Vertex AI 呼び出し
|                     |                                 | ・Firestore 読み書き                                  |
| **AI**              | Vertex AI (GenerativeModel)     | ・テキスト解析 → (x, y, color) 抽出                   |
| **Storage**         | Cloud Firestore                 | ・ユーザー設定 (`users/{uid}`)
|                     |                                 | ・日記データ (`diary/{uid_date}`)                    |

---

## 3. データフロー

1. **ログイン／トークン取得**  
   Flutter → Firebase Auth でサインイン → ID トークン取得  
2. **感情分析リクエスト**  
   Flutter → FastAPI `/diary` へ POST (`uid`, `date`, `text`, Authorization ヘッダ)  
3. **認証チェック**  
   FastAPI で Firebase Admin SDK を使いトークン検証  
4. **AI 推論**  
   FastAPI → Vertex AI 呼び出し → `(x, y, color)` 取得  
5. **保存**  
   - 日記データ: `diary/{uid}_{date}` に `{uid, date, text, x, y}` を保存  
   - ユーザー設定: `users/{uid}` にブレンド用の 4 色を保持  
6. **レスポンス返却**  
   FastAPI → Flutter `{x, y, color}` を返送  
7. **UI 表示**  
   Flutter で受信した `(x, y)` と `users/{uid}` の 4 色設定を `mixEmotionColors()` で混色

---

## 4. セキュリティ／運用ポイント

- **Firestore セキュリティルール**  
  ```js
  rules_version = '2';
  service cloud.firestore {
    match /databases/{database}/documents {
      match /users/{userId} {
        allow read, write: if request.auth.uid == userId;
      }
      match /diary/{docId} {
        allow read, write: if request.auth.uid == docId.split('_')[0];
      }
    }
  }
  ```
- **FastAPI (Cloud Run)**  
  - Firebase Admin SDK で ID トークン検証
  - Cloud Run IAM でサービス間のアクセス制御
- **運用**  
  - 環境変数: GCP プロジェクト ID, API_URL などを Cloud Run に設定  
  - モニタリング: Cloud Logging / Error Reporting で API エラーを監視

---