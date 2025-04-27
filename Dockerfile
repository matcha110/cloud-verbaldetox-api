# ベースイメージはお好みで
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 依存ファイルを先にコピーしてキャッシュ効かせる
COPY requirements.txt .

# 必要なパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Cloud Run 側がプローブしてくるポート（必ず EXPOSE 8080）
EXPOSE 8080

# Uvicorn 起動。PORT 環境変数があればそちらを使い、なければ 8080
ENTRYPOINT ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
