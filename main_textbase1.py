from fastapi import FastAPI, Form, BackgroundTasks, HTTPException
import vertexai, re, logging
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore
import google.auth

app = FastAPI()
vertexai.init(project="zenn-hackthon-2", location="us-central1")

db = firestore.Client()          # ← project は省略して Cloud Run 環境変数を利用

@app.post("/diary")
async def analyze_text(
    background_tasks: BackgroundTasks,
    uid: str = Form(...),
    date: str = Form(...),
    text: str = Form(...),
):
    try:
        color = analyze_sentiment(text)
        background_tasks.add_task(save_to_firestore, date, color)

        # 方法A: 辞書を返す（これが一番手軽）
        return {"color": color}

        # 方法B: どうしても JSONResponse を使うなら
        # return JSONResponse(content={"color": color}, background=background_tasks)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def analyze_sentiment(text: str) -> str:
    model = GenerativeModel("gemini-1.5-flash-002")
    prompt = (
        "以下の日本語テキストを読み取り、テキストの内容に最もふさわしい単一のカラーコードを "
        "#RRGGBB 形式で**厳密に**出力してください。\n"
        "余計な説明や注釈、改行等は一切含めないでください。\n\n"
        f"入力:\n{text}\n\n出力:\n"
    )
    raw = model.generate_content(prompt).text.strip()
    m = re.search(r"#([0-9A-Fa-f]{6})", raw)
    return f"#{m.group(1).upper()}" if m else "#88E0A6"


def save_to_firestore(date: str, color: str):
    import os
    logging.info(f"PROJECT={os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    logging.info(f"SA Email={google.auth.default()[1]}")
    try:
        db.collection("diary").document(date).set({"date": date, "color": color})
        logging.info("Firestore write success")
    except Exception as e:
        logging.exception(repr(e))      # repr で例外本体を文字列化


