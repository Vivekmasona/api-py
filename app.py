from typing import Optional
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models import GithubUserModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
timeout = httpx.Timeout(timeout=5.0, read=15.0)
client = httpx.AsyncClient(limits=limits, timeout=timeout)


@app.on_event("shutdown")
async def shutdown_event():
    print("shutting down...")
    await client.aclose()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = None):
    if not username:
        return templates.TemplateResponse("index.html", context={"request": request})

    user = await get_github_profile(request, username)
    if not user:
        return templates.TemplateResponse("404.html", context={"request": request})

    return templates.TemplateResponse("index.html", context={"request": request, "user": user})

@app.route("/audio/<video_id>", methods=["GET"])
def audio(video_id):
    youtube_link = f"https://www.youtube.com/watch?v={video_id}"
    buffer = BytesIO()
    url = YouTube(youtube_link)
    audio_stream = url.streams.filter(only_audio=True).first()

    if audio_stream:
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=f"{url.title}.mp3", mimetype="audio/mpeg")

    return "Invalid or missing YouTube link parameter."

@app.route("/video", methods=["GET"])
def download():
    youtube_link = request.args.get("url")
    if youtube_link:
        buffer = BytesIO()
        url = YouTube(youtube_link)
        video = url.streams.get_highest_resolution()

        # Stream the video to the buffer
        video.stream_to_buffer(buffer)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=video.title, mimetype=video.mime_type)


@app.get("/{username}", response_model=GithubUserModel)
async def get_github_profile(request: Request, username: str) -> Optional[GithubUserModel]:
    headers = {"accept": "application/vnd.github.v3+json"}

    response = await client.get(f"https://api.github.com/users/{username}", headers=headers)

    if response.status_code == 404:
        return None

    user = GithubUserModel(**response.json())

    return user
