echo

Echo is a focused AI assistant with a ChatGPT-style conversation interface.

Stack: FastAPI backend + React (Vite) frontend

Folders:
- backend/: FastAPI app, SQLite persistence, and AI provider integration
- frontend/: React (Vite) chat interface

Quick start (backend):
From the workspace directory (`project echo`), run:

1. `cd echo/backend`
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `python -m pip install -r requirements.txt`
5. `python -m uvicorn app.main:app --reload --port 8000`

Alternatively, from the workspace directory, run `./echo/run.sh` to start both services.

Quick start (frontend):
From the workspace directory, run:

1. `cd echo/frontend`
2. `npm install`
3. `npm run dev`

AI provider:
- Chat uses OpenAI for dynamic answers, including coding questions and follow-up questions.
- Copy `backend/.env.example` to `backend/.env`, add your OpenAI API key, and restart `./echo/run.sh`. The default model is `gpt-4o-mini`; override it with `OPENAI_CHAT_MODEL`.
- Without `OPENAI_API_KEY`, the backend returns a clear configuration error instead of a fake answer.
- You can also export `OPENAI_API_KEY` in the terminal before starting the backend. Never commit `backend/.env` or share its key.

Required environment variables:
- `OPENAI_API_KEY`: your OpenAI API key
- `OPENAI_CHAT_MODEL`: optional chat model, default `gpt-4o-mini`
- `OPENAI_IMAGE_MODEL`: optional image model, default `gpt-image-1`
- `ECHO_CORS_ORIGINS`: optional comma-separated frontend origins

The backend creates `backend/data/echo.db` automatically and stores conversations and messages.
