from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

# from google.cloud import speech
import vertexai
from vertexai.generative_models import GenerativeModel

import tempfile
import os
import datetime

app = FastAPI()

vertexai.init(project="zenn-hackthon-2", location="us-central1")

# @app.post("/diary")
# async def diary(uid: str = Form(...), date: str = Form(...), file: UploadFile = Form(...)):
#     # 一時ファイルに保存
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
#         content = await file.read()
#         tmp.write(content)
#         path = tmp.name

#     # 音声をテキストに変換
#     text = speech_to_text(path)
#     print("Transcript:", text)


#     # 感情分析
#     level, color = analyze_sentiment(text)
#     return JSONResponse(content={"level": level, "color": color})
@app.post("/diary")
async def analyze_text(
    uid: str = Form(...),
    date: str = Form(...),
    text: str = Form(...),
):
    try:
        level, color = analyze_sentiment(text)
        return JSONResponse(content={"level": level, "color": color})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# def speech_to_text(file_path: str) -> str:
#     client = speech.SpeechClient()
#     with open(file_path, "rb") as audio_file:
#         content = audio_file.read()
#     audio = speech.RecognitionAudio(content=content)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
#         sample_rate_hertz=16000,
#         language_code="ja-JP",
#         enable_automatic_punctuation=True,
#     )
#     response = client.recognize(config=config, audio=audio)
#     if not response.results:
#         return ""
#     return response.results[0].alternatives[0].transcript


@app.get("/")
def health():
    return {"status": "ok"}


def analyze_sentiment(text: str):
    # プロジェクトとリージョンはご自身の値に
    import vertexai

    vertexai.init(project="zenn-hackthon-2", location="us-central1")

    model = GenerativeModel("gemini-1.5-flash-002")

    prompt = f"""あなたは日本語の文章を読み取り、感情を分析してください。

出力形式:
level: 1〜4 （1=悲しい、4=とても嬉しい）
color: #RRGGBB （感情に応じた色）

入力:
{text}

出力:
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # パース
    try:
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        level = int(
            next(l for l in lines if l.lower().startswith("level")).split(":", 1)[1]
        )
        color = (
            next(l for l in lines if l.lower().startswith("color"))
            .split(":", 1)[1]
            .strip()
        )
    except Exception:
        level, color = 2, "#88E0A6"

    return level, color
