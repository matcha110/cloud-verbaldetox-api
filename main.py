from fastapi import FastAPI, Form, BackgroundTasks, HTTPException, UploadFile, File
import vertexai, re, logging, os
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore, storage, speech_v2 as speech
from uuid import uuid4
import google.auth


app = FastAPI()
BUCKET = os.getenv("AUDIO_BUCKET", "verbaldetox-audio")
vertexai.init(project="zenn-hackthon-2", location="us-central1")
db = firestore.Client()
storage_client = storage.Client()
speech_client = speech.SpeechClient()


# Firestore からユーザのカラーパレットを取得
def get_user_palette(uid: str) -> dict[str, str]:
    """users/{uid} ドキュメントから 4 色を取り出す。無ければデフォルト。"""
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        # デフォルト 4 色（例）
        return {
            "bright": "#FFCCCC",
            "energetic": "#FFE066",
            "dark": "#666699",
            "calm": "#A8E6CF",
        }
    data = doc.to_dict()
    return {
        "bright": data.get("bright_color", "#FFCCCC"),
        "energetic": data.get("energetic_color", "#FFE066"),
        "dark": data.get("dark_color", "#666699"),
        "calm": data.get("calm_color", "#A8E6CF"),
    }


@app.post("/diary/audio")
async def analyze_audio(
    background_tasks: BackgroundTasks,
    uid: str = Form(...),
    date: str = Form(...),
    audio: UploadFile = File(...),
):
    try:
        # 1) GCS にアップロード
        blob_name = f"audio/{uid}/{date}/{uuid4()}{os.path.splitext(audio.filename)[1]}"
        bucket = storage_client.bucket(BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(audio.file, content_type=audio.content_type)
        gcs_uri = f"gs://{BUCKET}/{blob_name}"

        # 2) 音声認識
        config = {
            "language_code": "ja-JP",
            "auto_decoding_config": {},
            "model": "latest_long",
        }
        op = speech_client.long_running_recognize(
            recognizer=f"projects/{PROJECT}/locations/us-central1/recognizers/_",
            config=config,
            uri=gcs_uri,
        )
        response = op.result(timeout=30)
        transcript = " ".join(
            r.text for res in response.results for r in res.alternatives
        )

        # 3) 既存ロジックへ
        palette = get_user_palette(uid)
        x, y, color = analyze_emotion_and_color(transcript, palette)

        background_tasks.add_task(save_to_firestore, uid, date, transcript, x, y, color)
        return {
            "x": x,
            "y": y,
            "color": color,
            "transcript": transcript,
        }

    except Exception as e:
        logging.exception(e)
        raise HTTPException(500, str(e))


@app.post("/diary")
async def analyze_text(
    background_tasks: BackgroundTasks,
    uid: str = Form(...),
    date: str = Form(...),
    text: str = Form(...),
):
    """日記テキストを 1 回の Gemini 呼び出しで解析し、(x, y, color) を返す。"""
    try:
        palette = get_user_palette(uid)
        x, y, color = analyze_emotion_and_color(text, palette)
        background_tasks.add_task(save_to_firestore, uid, date, text, x, y, color)
        return {"x": x, "y": y, "color": color}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def analyze_emotion_and_color(
    text: str, palette: dict[str, str]
) -> tuple[int, int, str]:
    """
    Gemini に 1 回のプロンプトで
    ・x, y 座標（x: 不快→快, y: 沈静→覚醒）
    ・emotion_color : ブレンド済みカラー (#RRGGBB)
    を返させてパースして整形
    """
    model = GenerativeModel("gemini-1.5-flash-002")

    prompt = f"""
あなたは感情心理学と配色設計の専門家です。
次の日本語テキストを読み取り、感情を 2 軸 (x, y) で評価し、
**必ず 1 行のみ** 下記フォーマットで出力してください。

フォーマット:
x={{整数}},y={{整数}},color=#RRGGBB

座標定義 (整数 −10〜+10):
・x 軸  -10 = 強い不快感   +10 = 強い快感
・y 軸  -10 = 沈静（リラックス） +10 = 覚醒（高い活力）

利用可能パレット:
BRIGHT     = {palette['bright']}   # 快 + 覚醒
ENERGETIC  = {palette['energetic']} # 快 + 高覚醒
DARK       = {palette['dark']}     # 不快 + 沈静
CALM       = {palette['calm']}     # 快 + 沈静

**色選定ルール**  
1. color には上記 4 色のうち **最多でも 2 色** を線形ブレンドして RGB 6 桁で出力する。  
   - ブレンド比率は |x| : |y| に比例して決めること。  
     例) x=8, y=2 → 快方向 80%, 覚醒方向 20%  
2. |x| または |y| が **7 以上** の場合は、その軸に対応する 1 色だけを使用する。  
3. ブレンド候補 2 色の色差 (ΔE) が **20 未満** なら、より色差が大きい別の組み合わせを優先する。  
   （似た色同士を混ぜてくすまないようにするため）  
4. 余計な説明・改行・コードブロックは一切含めない。

入力:
{text}

出力:
""".strip()


    raw = model.generate_content(prompt).text.strip()
    pattern = (
        r"^x\s*=\s*(-?\d+)\s*,\s*y\s*=\s*(-?\d+)\s*,\s*color\s*=\s*#([0-9A-Fa-f]{6})$"
    )
    m = re.match(pattern, raw)
    if not m:
        raise ValueError(f"Unexpected model output: {raw!r}")

    x, y = int(m.group(1)), int(m.group(2))
    color = f"#{m.group(3).upper()}"
    x, y = max(-10, min(10, x)), max(-10, min(10, y))
    return x, y, color


def save_to_firestore(uid: str, date: str, text: str, x: int, y: int, color: str):
    """Firestore に解析結果を保存 (バックグラウンド用)。"""
    import os, google.auth, logging

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
