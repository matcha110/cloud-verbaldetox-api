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
    """日記テキストを 1 回の Gemini 呼び出しで解析し、楽しさ・明るさ・元気 (0‑10) とカラーコードを返す。"""
    try:
        fun, bright, energy, color = analyze_traits(text)
        background_tasks.add_task(
            save_to_firestore, uid, date, text, fun, bright, energy, color
        )
        return {
            "fun": fun,
            "bright": bright,
            "energy": energy,
            "color": color,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def analyze_traits(text: str) -> tuple[int, int, int, str]:
    """Gemini で一度に 3 軸 + 色を数値化して返す。各値は 0‑10 の整数。"""
    model = GenerativeModel("gemini-1.5-flash-002")
    prompt = (
        "以下の日本語テキストを読み取り、作者の心情を次のフォーマットで **厳密に 1 行** 出力してください。\n"
        "fun=<整数0-10>,bright=<整数0-10>,energy=<整数0-10>,color=#RRGGBB\n\n"
        "評価軸:\n"
        "・fun    : つまらない = 0, 楽しい = 10\n"
        "・bright : 暗い       = 0, 明るい = 10\n"
        "・energy : 元気がない = 0, とても元気 = 10\n\n"
        "余計な説明や注釈、改行は一切含めないでください。\n\n"
        f"入力:\n{text}\n\n出力:\n"
    )
    raw = model.generate_content(prompt).text.strip()
    m = re.match(
        r"fun\s*=\s*(\d+)\s*,\s*bright\s*=\s*(\d+)\s*,\s*energy\s*=\s*(\d+)\s*,\s*color\s*=\s*#([0-9A-Fa-f]{6})",
        raw,
    )
    if not m:
        raise ValueError(f"Unexpected model output: {raw!r}")

    fun = max(0, min(10, int(m.group(1))))
    bright = max(0, min(10, int(m.group(2))))
    energy = max(0, min(10, int(m.group(3))))
    color = f"#{m.group(4).upper()}"
    return fun, bright, energy, color


def save_to_firestore(
    uid: str,
    date: str,
    text: str,
    fun: int,
    bright: int,
    energy: int,
    color: str,
):
    """Firestore に (fun, bright, energy, color) を保存。バックグラウンド用。"""
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
                "fun": fun,
                "bright": bright,
                "energy": energy,
                "color": color,
            }
        )
        logging.info("Firestore write success")
    except Exception as e:
        logging.exception(repr(e))
