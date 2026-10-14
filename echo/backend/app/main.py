import os
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import connection, fetch_all, fetch_one, init_db, insert, utc_now
from .providers import AIProviderError, generate_chat_reply, generate_image

app = FastAPI(title="echo-backend")
BASE_DIR = Path(__file__).resolve().parents[1]
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.on_event("startup")
async def startup():
    init_db()
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)


cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "ECHO_CORS_ORIGINS", "http://localhost:5173,http://localhost:5174"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "project": "echo", "database": "ready"}


@app.post("/image/create")
async def create_image(prompt: str = Form(...), file: UploadFile | None = File(None)):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    image_url, provider = await generate_image(prompt.strip(), MEDIA_DIR)
    image_id = str(uuid.uuid4())
    insert(
        "image_generations",
        {
            "id": image_id,
            "prompt": prompt,
            "provider": provider,
            "image_url": image_url,
            "created_at": utc_now(),
        },
    )
    return {"id": image_id, "url": image_url, "prompt": prompt, "provider": provider}


@app.post("/video/edit")
async def edit_video(
    clip: UploadFile = File(...), music: UploadFile | None = File(None)
):
    job_id = str(uuid.uuid4())
    job_dir = MEDIA_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    clip_path = job_dir / (clip.filename or "clip.mp4")
    with clip_path.open("wb") as output:
        shutil.copyfileobj(clip.file, output)
    music_path = None
    if music:
        music_path = job_dir / (music.filename or "music.mp3")
        with music_path.open("wb") as output:
            shutil.copyfileobj(music.file, output)

    output_path = job_dir / "edited.mp4"
    status = "uploaded"
    if music_path and shutil.which("ffmpeg"):
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(clip_path),
            "-i",
            str(music_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-shortest",
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        status = "completed" if result.returncode == 0 else "failed"
    elif music_path:
        status = "uploaded_ffmpeg_required"
    insert(
        "video_jobs",
        {
            "id": job_id,
            "clip_name": clip.filename or "clip.mp4",
            "music_name": music.filename if music else None,
            "status": status,
            "output_path": str(output_path) if output_path.exists() else None,
            "created_at": utc_now(),
        },
    )
    return {"id": job_id, "status": status, "clip_id": clip.filename}


@app.post("/chat")
async def chat(req: ChatRequest):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    if req.conversation_id and not fetch_one("conversations", conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not req.conversation_id:
        insert(
            "conversations",
            {"id": conversation_id, "title": req.message[:60], "created_at": utc_now()},
        )
    with connection() as db:
        history = [
            {"role": row["role"], "content": row["content"]}
            for row in db.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,),
            ).fetchall()
        ]
    try:
        reply, provider = await generate_chat_reply(req.message, history)
    except AIProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    insert(
        "messages",
        {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": "user",
            "content": req.message,
            "created_at": utc_now(),
        },
    )
    insert(
        "messages",
        {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": reply,
            "created_at": utc_now(),
        },
    )
    return {"response": reply, "conversation_id": conversation_id, "provider": provider}


@app.get("/history/images")
async def image_history():
    return fetch_all("image_generations")


@app.get("/history/videos")
async def video_history():
    return fetch_all("video_jobs")


@app.get("/conversations/{conversation_id}")
async def conversation(conversation_id: str):
    record = fetch_one("conversations", conversation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Conversation not found")
    with connection() as db:
        messages = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,),
            ).fetchall()
        ]
    return {"conversation": record, "messages": messages}
