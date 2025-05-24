from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Form
import vertexai, re, logging, os, uuid
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore
from google.cloud import storage
from google.cloud import speech
import asyncio
from typing import Dict, Tuple

app = FastAPI()
BUCKET: str = os.getenv("AUDIO_BUCKET", "zenn-hackthon")
PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "zenn-hackthon-2")
vertexai.init(project=PROJECT, location="us-central1")
storage_client = storage.Client(project=PROJECT)
speech_client = speech.SpeechClient()
db = firestore.Client(project=PROJECT)


def get_user_palette(uid: str) -> Dict[str, str]:
    """
    Firestore から指定ユーザのカラーパレット（4色）を取得

    Args:
        uid (str): ユーザID

    Returns:
        dict[str, str]: パレット名（'bright'等）をキーとし、カラーコード('#RRGGBB')を値とする辞書
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
) -> dict:
    """
    音声ファイルを受け取り、GCSへ保存→Speech-to-Textで文字起こし→Geminiによる感情解析を実施し、
    Firestoreへ結果をバックグラウンドで保存

    Args:
        background_tasks (BackgroundTasks): バックグラウンドタスク管理
        uid (str): ユーザID
        date (str): 日付(任意の形式、通常 'YYYY-MM-DD')
        audio (UploadFile): アップロードされた音声ファイル

    Returns:
        dict: 解析結果 { "x": int, "y": int, "color": str, "transcript": str }
    """
    try:
        # --- (1) GCS にアップロード ---
        ext: str = os.path.splitext(audio.filename)[1]
        blob_name: str = f"audio/{uid}/{date}/{uuid.uuid4()}{ext}"
        bucket = storage_client.bucket(BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(audio.file, content_type=audio.content_type)
        gcs_uri: str = f"gs://{BUCKET}/{blob_name}"

        # --- (2) 短時間音声の同期文字起こし ---
        recognition_audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz=44100,
            language_code="ja-JP",
            enable_automatic_punctuation=True,
            audio_channel_count=2,
        )
        response = await asyncio.to_thread(
            lambda: speech_client.recognize(
                config=config,
                audio=recognition_audio,
            )
        )
        transcript: str = "".join(
            result.alternatives[0].transcript for result in response.results
        )

        # --- (3) 感情解析＆Firestore 保存 ---
        palette: Dict[str, str] = get_user_palette(uid)
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
        raise HTTPException(status_code=500, detail="Internal server error")


def transcribe_audio(content: bytes, mime_type: str) -> str:
    """
    音声バイト列をSpeech-to-Textで文字起こしして返します。

    Args:
        content (bytes): 音声ファイルのバイト列
        mime_type (str): 音声ファイルのMIMEタイプ（例: "audio/wav"）

    Returns:
        str: 文字起こし結果（全文）
    """
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP",
        audio_channel_count=2,
    )
    resp = speech_client.recognize(config=config, audio=audio)
    return "".join([result.alternatives[0].transcript for result in resp.results])


def analyze_emotion_and_color(
    text: str, palette: Dict[str, str]
) -> Tuple[int, int, str]:
    """
    Gemini API を使い、日本語テキストから感情座標 (x, y) と
    指定パレットによる色コード (#RRGGBB) を推論します。

    Args:
        text (str): 入力テキスト（日本語）
        palette (dict[str, str]): 4色のカラーパレット

    Returns:
        tuple[int, int, str]: (x, y, color)  
            x (int): -10～+10（不快→快）  
            y (int): -10～+10（沈静→覚醒）  
            color (str): 6桁のカラーコード "#RRGGBB"
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


    raw: str = model.generate_content(prompt).text.strip()
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


def save_to_firestore(
    uid: str, date: str, text: str, x: int, y: int, color: str
) -> None:
    """
    感情解析結果をFirestoreに保存します（バックグラウンドタスク用）。

    Args:
        uid (str): ユーザID
        date (str): 日付
        text (str): 文字起こしテキスト or 入力テキスト
        x (int): x軸値
        y (int): y軸値
        color (str): カラーコード("#RRGGBB")
    """
    try:
        doc_id: str = f"{uid}_{date}"
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
) -> dict:
    """
    テキストを受け取り、Geminiによる感情分析を実施し、
    Firestoreへ結果をバックグラウンドで保存します。

    Args:
        background_tasks (BackgroundTasks): バックグラウンドタスク管理
        uid (str): ユーザID
        date (str): 日付
        text (str): 入力テキスト

    Returns:
        dict: 解析結果 { "x": int, "y": int, "color": str }
    """
    try:
        palette: Dict[str, str] = get_user_palette(uid)
        x, y, color = analyze_emotion_and_color(text, palette)
        background_tasks.add_task(save_to_firestore, uid, date, text, x, y, color)
        return {"x": x, "y": y, "color": color}
    except Exception as e:
        logging.exception("text analysis error")
        raise HTTPException(status_code=500, detail=str(e))
