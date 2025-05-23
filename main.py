from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Form
import vertexai, re, logging, os, uuid
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore
from google.cloud import storage
from google.cloud import speech
import asyncio


app = FastAPI()
BUCKET = os.getenv("AUDIO_BUCKET", "zenn-hackthon")
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "zenn-hackthon-2")
vertexai.init(project=PROJECT, location="us-central1")
storage_client = storage.Client(project=PROJECT)
speech_client = speech.SpeechClient()
db = firestore.Client(project=PROJECT)


# Firestore からユーザのカラーパレットを取得
def get_user_palette(uid: str) -> dict[str, str]:
    """
    users/{uid} ドキュメントから 4 色を取り出す。無ければデフォルト。
    """
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
        # --- (1) GCS にアップロード ---
        ext = os.path.splitext(audio.filename)[1]
        blob_name = f"audio/{uid}/{date}/{uuid.uuid4()}{ext}"
        bucket = storage_client.bucket(BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(audio.file, content_type=audio.content_type)
        gcs_uri = f"gs://{BUCKET}/{blob_name}"
        logging.info(f"Uploaded audio to GCS: {gcs_uri}")

        # --- (2) 短時間音声の同期文字起こし ---
        recognition_audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding    = speech.RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz = 44100,
            language_code= "ja-JP",
            enable_automatic_punctuation=True,
            audio_channel_count=2,
        )
        logging.info("Calling speech_client.recognize() …")
        response = await asyncio.to_thread(
            lambda: speech_client.recognize(
                config=config,
                audio=recognition_audio,
            )
        )
        logging.info(f"Speech-to-Text response: {response}")  # 結果オブジェクト全体
        logging.info(f"Number of results: {len(response.results)}")
        transcript = "".join(
            result.alternatives[0].transcript for result in response.results
        )
        logging.info(f"Transcript: {transcript!r}")

        # --- (3) 感情解析＆Firestore 保存 ---
        palette = get_user_palette(uid)
        print(palette)
        x, y, color = analyze_emotion_and_color(transcript, palette)
        background_tasks.add_task(
            save_to_firestore, uid, date, transcript, x, y, color
        )

        return {
            "x": x,
            "y": y,
            "color": color,
            "transcript": transcript,
        }

    except Exception as e:
        logging.exception(e)
        # 内部エラー詳細はログに残しつつ、レスポンスは汎用メッセージに
        raise HTTPException(status_code=500, detail="Internal server error")

def transcribe_audio(content: bytes, mime_type: str) -> str:
    """
    音声バイト列を文字起こしして返す。
    """
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP",
        audio_channel_count=2,
    )
    resp = speech_client.recognize(config=config, audio=audio)
    # 複数結果を連結
    return "".join([result.alternatives[0].transcript for result in resp.results])


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
次の日本語テキストを読み取り、感情を 2 軸 (x, y) で評価し、
**必ず 1 行のみ** 下記フォーマットで出力してください。

フォーマット:
x={{整数}},y={{整数}},color=#RRGGBB

座標定義 (整数 −10〜+10):
・x 軸  -10 = 強い不快感   +10 = 強い快感
・y 軸  -10 = 沈静（リラックス） +10 = 覚醒（高い活力）

利用可能パレット:
BRIGHT     = {palette['bright']}   # 快 + 高覚醒
ENERGETIC  = {palette['energetic']} # 不快 + 高覚醒
DARK       = {palette['dark']}     # 不快 + 沈静
CALM       = {palette['calm']}     # 快 + 沈静

**色選定ルール**  
1. color には上記 4 色のうち **最多でも 2 色** を線形ブレンドして RGB 6 桁で出力する。  
   - ブレンド比率は |x| : |y| に比例して決めること。  
     例) x=8, y=2 → 快方向 80%, 覚醒方向 20%   
2. 余計な説明・改行・コードブロックは一切含めない。

入力:
{text}

出力:
""".strip()


    logging.info(f"Emotion analysis prompt:\n{prompt}")

    raw = model.generate_content(prompt).text.strip()
    logging.info(f"[DEBUG] Vertex AI raw output: {raw!r}")
    pattern = (
        r"^x\s*=\s*(-?\d+)\s*,\s*y\s*=\s*(-?\d+)\s*,\s*color\s*=\s*#([0-9A-Fa-f]{6})$"
    )
    m = re.match(pattern, raw)
    if not m:
        raise ValueError(f"Unexpected model output: {raw!r}")

    x, y = int(m.group(1)), int(m.group(2))
    color = f"#{m.group(3).upper()}"
    x = max(-10, min(10, x))
    y = max(-10, min(10, y))
    return x, y, color


def save_to_firestore(uid: str, date: str, text: str, x: int, y: int, color: str):
    """Firestore に解析結果を保存 (バックグラウンド用)。"""
    try:
        doc_id = f"{uid}_{date}"
        user_diary_ref = db.collection("users").document(uid).collection("diary")
        user_diary_ref.document(doc_id).set(
            {
                "date": date,
                "transcript": text,
                "x": x,
                "y": y,
                "color": color,
            }
        )
        logging.info("Firestore write success")
    except Exception as e:
        logging.exception(repr(e))



@app.post("/diary/text")
async def analyze_text(
    background_tasks: BackgroundTasks,
    uid: str = Form(...),
    date: str = Form(...),
    text: str = Form(...),
):
    try:
        palette = get_user_palette(uid)
        x, y, color = analyze_emotion_and_color(text, palette)
        background_tasks.add_task(save_to_firestore, uid, date, text, x, y, color)
        return {"x": x, "y": y, "color": color}
    except Exception as e:
        logging.exception("text analysis error")
        raise HTTPException(status_code=500, detail=str(e))
