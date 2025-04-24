from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
import vertexai
from vertexai.generative_models import GenerativeModel
import re

app = FastAPI()

PROJECT_ID = "zenn-hackthon-2"
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)


@app.post("/diary")
async def analyze_text(
    uid: str = Form(...),
    date: str = Form(...),
    text: str = Form(...),
):
    try:
        color = analyze_sentiment(text)
        return JSONResponse(content={"color": color})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/")
def health():
    return {"status": "ok"}


def analyze_sentiment(text: str) -> str:
    model = GenerativeModel("gemini-1.5-flash-002")

    prompt = f"""以下の日本語テキストを読み取り、テキストの内容に最もふさわしい単一のカラーコードを #RRGGBB 形式で**厳密に**出力してください。
余計な説明や注釈、改行等は一切含めないでください。

入力:
{text}

出力:
"""
    response = model.generate_content(prompt)

    raw = response.text.strip()
    # #RRGGBB の形式でマッチ
    m = re.search(r'#([0-9A-Fa-f]{{6}})', raw)
    if m:
        # 大文字に統一して返す
        return f'#{m.group(1).upper()}'
    # マッチしなかった場合のフォールバック
    return "#88E0A6"