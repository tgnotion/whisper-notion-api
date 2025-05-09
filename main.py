from fastapi import FastAPI, Request
from notion_client import Client
import yt_dlp, whisper, os
import requests

app = FastAPI()

notion = Client(auth=os.getenv("ntn_g22675070349Syg1Yqo1mBzgTdnqSl3xL3WOMf3QH7F29s"))
DB_ID = os.getenv("1ed08727695a800fbe1efc717a210929")
model = whisper.load_model("base")

@app.post("/process")
async def process(request: Request):
    data = await request.json()
    url = data["url"]

    # yt-dlpでXポストのメディアURLを取得（動画 or 画像）
    ydl_opts = {
        'outtmpl': 'media.%(ext)s',
        'skip_download': True,
        'quiet': True,
        'force_generic_extractor': True,
        'simulate': True,
        'get_url': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        media_urls = []
        if 'url' in info:
            media_urls.append(info['url'])
        elif 'entries' in info:
            media_urls = [entry['url'] for entry in info['entries']]

    # 動画 or 画像の最初の1つだけ処理
    media_url = media_urls[0]

    transcript = ""
    if ".mp4" in media_url or "video" in media_url:
        # 動画ならダウンロード＆文字起こし
        r = requests.get(media_url)
        with open("video.mp4", "wb") as f:
            f.write(r.content)
        result = model.transcribe("video.mp4")
        transcript = result["text"]
    else:
        transcript = "画像ポストです（文字起こしはありません）"

    # Notionに転記
    notion.pages.create(
        parent={"database_id": DB_ID},
        properties={
            "Name": {"title": [{"text": {"content": "Xポスト文字起こし"}}]},
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": transcript}}]
                }
            },
            {
                "object": "block",
                "type": "image" if "image" in media_url else "video",
                "image" if "image" in media_url else "video": {
                    "type": "external",
                    "external": {"url": media_url}
                }
            }
        ]
    )

    return {"status": "ok", "media": media_url, "text": transcript}