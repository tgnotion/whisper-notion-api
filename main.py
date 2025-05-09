# main.py
import os, io, logging, requests
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from notion_client import Client as Notion
import whisper

app = FastAPI()

# ───────────────────────────────────────────────
# 環境変数
SECRET_KEY   = os.getenv("SECRET_KEY")            # 例: abc123
NOTION_TOKEN = os.getenv("NOTION_TOKEN")          # secret_xxxxxxxxxxxxxxxxx
DB_ID        = os.getenv("DB_ID")                 # 32桁 + ハイフン
# ───────────────────────────────────────────────

notion = Notion(auth=NOTION_TOKEN)
model  = whisper.load_model("tiny")               # 起動時に 1 回だけロード

# ───────────────────────────────────────────────
@app.post("/process")
async def process(req: Request, bg: BackgroundTasks):
    """iOS から呼ばれるエンドポイント (即レスポンス)"""
    data = await req.json()

    if data.get("secret") != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Wrong secret")

    tweet_url = data["url"]
    bg.add_task(run_pipeline, tweet_url)
    return {"status": "accepted"}                 # ← iOS はここで完了扱い
# ───────────────────────────────────────────────

# def run_pipeline(url: str):
#     """動画DL → 音声抽出 → Whisper 文字起こし → Notion 保存"""
    # try:
    #     # 1️⃣ 動画 or 音声データを取得（↓はダミーで空 WAV 生成）
    #     logging.info(f"Downloading media from {url}")
    #     wav_bytes = generate_silence_wav()        # ← 好きな DL 処理に置換

    #     # 2️⃣ Whisper で文字起こし
    #     logging.info("Running Whisper…")
    #     result = model.transcribe(io.BytesIO(wav_bytes), fp16=False)
    #     transcript = result["text"].strip()

    #     # 3️⃣ Notion データベースへ保存
    #     logging.info("Saving to Notion…")
    #     notion.pages.create(
    #         parent={"database_id": DB_ID},
    #         properties={
    #             "名前":    {"title": [{"text": {"content": transcript[:50] or "No speech"}}]},
    #             "URL":     {"url": url},
    #             "Content": {"rich_text": [{"text": {"content": transcript}}]},
    #         }
    #     )
    #     logging.info("✅ Saved to Notion")

    # except Exception as e:
    #     # 失敗時は Render の Logs に Traceback を残す
    #     logging.exception("❌ Pipeline failed")

def run_pipeline(tweet_url: str):
    try:
        transcript = f"URL: {tweet_url}"      # ← とりあえず文字列を作るだけ

        notion.pages.create(
            parent={"database_id": DB_ID},
            properties={
                "Name":    {"title": [{"text": {"content": transcript[:50]}}]},
                "URL":     {"url": tweet_url},
                "Content": {"rich_text": [{"text": {"content": transcript}}]},
            }
        )
        logging.info("Saved to Notion 👍")

    except Exception:
        logging.exception("Pipeline failed")

def generate_silence_wav(seconds: int = 1) -> bytes:
    """簡易的に無音WAVを返すデモ関数（実運用では不要）"""
    import wave, struct
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
        wf.writeframes(struct.pack("<h", 0) * int(16000 * seconds))
    return buf.getvalue()
