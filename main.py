from fastapi import FastAPI, Form, BackgroundTasks, HTTPException
import vertexai, re, logging
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore
import google.auth

app = FastAPI()
vertexai.init(project="zenn-hackthon-2", location="us-central1")

db = firestore.Client()


@app.post("/diary")
async def analyze_text(
    background_tasks: BackgroundTasks,
    uid: str = Form(...),
    date: str = Form(...),
    text: str = Form(...),
):
    """日記テキストを 1 回の Gemini 呼び出しで解析し、(x, y, color) を返す。"""
    try:
        x, y, color = analyze_emotion_and_color(text)
        background_tasks.add_task(save_to_firestore, uid, date, text, x, y, color)
        return {"x": x, "y": y, "color": color}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def analyze_emotion_and_color(text: str) -> tuple[int, int, str]:
    """Gemini に 1 回のプロンプトで Russell の円環モデルに従った座標とカラーコードを出力させてパースする。"""
    model = GenerativeModel("gemini-1.5-flash-002")
    prompt = (
        "以下の日本語テキストを読み取り、Russellの円環構造モデルに従い、"
        "水平軸 (快=+10, 不快=-10)、"
        "垂直軸 (覚醒=+10, 鎮静=-10) の2軸で心情を評価し、"
        "以下の形式で**厳密に**1行で出力してください。\n"
        "x=<整数>,y=<整数>,color=#RRGGBB\n"
        "余計な説明や注釈、改行は一切含めないでください。\n\n"
        f"入力:\n{text}\n\n出力:\n"
    )
    raw = model.generate_content(prompt).text.strip()
    m = re.match(r"x\s*=\s*(-?\d+)\s*,\s*y\s*=\s*(-?\d+)\s*,\s*color\s*=\s*#([0-9A-Fa-f]{6})", raw)
    if not m:
        raise ValueError(f"Unexpected model output: {raw!r}")

    x, y = int(m.group(1)), int(m.group(2))
    color = f"#{m.group(3).upper()}"
    x = max(-10, min(10, x))
    y = max(-10, min(10, y))
    return x, y, color


def save_to_firestore(uid: str, date: str, text: str, x: int, y: int, color: str):
    """Firestore に解析結果を保存 (バックグラウンド用)。"""
    import os
    logging.info(f"PROJECT={os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    logging.info(f"SA Email={google.auth.default()[1]}")
    try:
        doc_id = f"{uid}_{date}"
        db.collection("diary").document(doc_id).set(
            {
                "uid": uid,
                "date": date,
                "text": text,
                "x": x,
                "y": y,
                "color": color,
            }
        )
        logging.info("Firestore write success")
    except Exception as e:
        logging.exception(repr(e))
