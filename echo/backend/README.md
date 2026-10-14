Backend for echo (FastAPI)

Requirements:
- Python 3.10+
- See requirements.txt

Run locally:
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000

Optional AI configuration:
  cp .env.example .env
  # Add your OPENAI_API_KEY to .env, then start the backend.
  # OPENAI_CHAT_MODEL defaults to gpt-4o-mini.
  # OPENAI_IMAGE_MODEL defaults to gpt-image-1.

The SQLite database is created at `data/echo.db` on startup. Generated files are stored in `media/`.

Endpoints (stubs):
- GET /health
- POST /image/create (form: prompt, optional file)
- POST /video/edit (form: clip video, optional music file)
- POST /chat (JSON: {"message": "...", optional "conversation_id": "..."})
- GET /history/images
- GET /history/videos
- GET /conversations/{conversation_id}

These are placeholders for integrating real image/video/chat services or models.