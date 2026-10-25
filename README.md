# 🧠 Personal AI Assistant — Backend

The REST API behind a personal AI assistant: manage **tasks and notes
through plain-language chat**, with a tool-calling LangChain/LangGraph
agent, persistent per-user conversation memory, JWT authentication and
voice input/output.

- **Live API:** https://personal-ai-assistant-euur.onrender.com
  ([interactive docs](https://personal-ai-assistant-euur.onrender.com/docs) ·
  [health check](https://personal-ai-assistant-euur.onrender.com/health))
- **Live app:** https://personal-assistant-09.lovable.app
- **Frontend (Lovable):** https://github.com/CodeWithDks/personal-ai-assistant-web

> The API runs on Render's free tier, which sleeps after ~15 minutes of
> inactivity. The first request after a quiet period can take 30–60 seconds
> while the service wakes up.

---

## ✨ Features

- 🤖 **Conversational AI agent** — a LangChain `create_agent` tool-calling
  agent (OpenAI `gpt-4o-mini`) that creates, searches, updates and deletes
  tasks and notes from natural language (`backend/app/ai/agent.py`)
- 💾 **Persistent conversation memory** — a LangGraph checkpointer,
  thread-scoped per user. Stored in **Postgres** in production
  (`PostgresSaver`), with a local SQLite fallback for development
  (`backend/app/ai/memory.py`)
- 🔐 **JWT authentication** — registration/login, bcrypt password hashing,
  7-day access tokens (`core/security.py`, `routes/auth.py`)
- 🔒 **Strict per-user data isolation** — every query is scoped to the
  authenticated user, and the agent's tools are built per user, so the model
  can never touch another user's rows
- ✅ **Task management** — full CRUD plus search, available both as agent
  tools (`ai/tools/tasks.py`) and as a REST API (`routes/task_routes.py`)
- 📝 **Note management** — same pattern (`ai/tools/notes.py`,
  `routes/note_routes.py`)
- 🎙️ **Voice** — speech-to-text (Whisper) and text-to-speech (OpenAI TTS)
  (`ai/voice.py`)
- 🛡️ **Abuse and cost protection** — per-user rate limits on the chat
  endpoints, per-IP limits on login/registration, a 2,000-character cap on
  chat messages, and password length validation
- 🗄️ **Real database migrations** — Alembic, not just `create_all()`
- 🌐 **Production-ready config** — environment-driven CORS, logging, health
  check, generic error responses (no internal details leaked to clients)
- 🧪 **Test suite** — 74 pytest tests covering auth, chat, rate limiting,
  tasks, notes and the AI tool layer

---

## 🏗 Architecture

```
  Lovable frontend (separate repo)
        │  HTTPS / JSON  (Authorization: Bearer <JWT>)
        ▼
  FastAPI backend  (Render)
        │
        ├── routes/      auth, chat, tasks, notes — HTTP layer
        ├── services/    business logic (auth, tasks, notes)
        ├── ai/
        │     ├── agent.py     builds a per-user LangChain agent
        │     ├── llm.py       chat model (OpenAI gpt-4o-mini)
        │     ├── memory.py    LangGraph checkpointer (Postgres / SQLite)
        │     ├── prompts.py   system prompt construction
        │     ├── voice.py     Whisper (STT) + OpenAI TTS
        │     └── tools/       tasks.py, notes.py — tools the agent can call
        ├── database/    SQLAlchemy models + engine
        ├── core/        JWT / hashing (security.py), rate limiting
        └── schemas/     Pydantic request/response models
        │
        ├──────────────► OpenAI API (chat, Whisper, TTS)
        ▼
  Supabase Postgres
        ├── users, tasks, notes                 (SQLAlchemy + Alembic)
        └── checkpoints, checkpoint_blobs, …    (LangGraph conversation memory)
```

Application data and conversation memory live in the same Postgres
database but are managed separately: Alembic owns the application schema,
while LangGraph creates and manages its own checkpoint tables.

---

## 🔌 API Overview

Full interactive documentation is served at **`/docs`** (Swagger UI).

All routes except `/health` and `/auth/*` require the header
`Authorization: Bearer <access_token>`.

| Method | Path | Description | Rate limit |
|---|---|---|---|
| GET | `/health` | Liveness check → `{"status": "ok"}` | — |
| POST | `/auth/register` | Create an account (JSON: `email`, `password` 8–72 chars) | 5/min per IP |
| POST | `/auth/login` | Log in (**form-encoded**: `username` = email, `password`) → `access_token` | 10/min per IP |
| GET | `/tasks/` | List tasks (`limit`, `offset`) | — |
| GET | `/tasks/search` | Search tasks (`keyword`, `status`, `priority`) | — |
| POST | `/tasks/` | Create a task | — |
| GET · PUT · DELETE | `/tasks/{id}` | Read / update / delete one task | — |
| GET | `/notes/` | List notes (`limit`, `offset`) | — |
| GET | `/notes/search` | Search notes (`keyword`) | — |
| POST | `/notes/` | Create a note | — |
| GET · PUT · DELETE | `/notes/{id}` | Read / update / delete one note | — |
| POST | `/chat/` | Send a message to the assistant (JSON: `message`, max 2,000 chars) → `reply` | 10/min per user |
| POST | `/chat/voice` | Send recorded audio (multipart field `audio`) → `transcript`, `reply`, `audio_base64` (mp3) | 5/min per user |

Notes for API consumers:

- **Use the paths exactly as shown, including trailing slashes**
  (`/tasks/`, not `/tasks`). A missing slash causes a redirect, which breaks
  cross-origin (CORS) requests from a browser.
- Task `status` is `pending` or `completed`; `priority` is `low`, `medium`
  or `high`; `due_date` is an ISO 8601 timestamp.
- Error responses: `401` expired/invalid token, `422` validation error,
  `429` rate limit exceeded, `500` generic server error.

---

## 📂 Project Structure

```
personal-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── ai/                 agent, memory, voice, prompts, tools/
│   │   ├── api/                shared dependencies (deps.py — current user)
│   │   ├── core/               security (JWT, hashing), rate_limit.py
│   │   ├── database/           SQLAlchemy models + engine
│   │   ├── routes/             auth, chat, tasks, notes
│   │   ├── schemas/            Pydantic models
│   │   ├── services/           business logic
│   │   └── main.py             FastAPI entry point
│   ├── alembic/                database migrations
│   ├── alembic.ini
│   ├── normalize_status_casing.py   one-off data-cleanup script
│   ├── requirements.txt
│   └── .env.example
│
├── tests/                      pytest suite (74 tests)
├── pytest.ini
├── render.yaml                 Render Blueprint (see Deployment notes)
└── README.md
```

---

## ⚙ Local Setup

**Requirements:** Python 3.12+ (use the same version you deploy with), an
OpenAI API key.

All commands below are run from the **repository root** (the `backend`
package resolves from there).

### 1. Create a virtual environment and install dependencies

```bash
python -m venv venv
```

**Windows**
```bash
venv\Scripts\activate
```
**Linux / macOS**
```bash
source venv/bin/activate
```

```bash
pip install -r backend/requirements.txt
```

### 2. Configure environment variables

Copy the example file and fill in your values. The app loads the file from
exactly this path:

```bash
cp backend/.env.example backend/.env
```

Generate a real `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Choose a database

- **Quick local start (SQLite):** leave `DATABASE_URL` unset. Tables are
  created automatically on startup, and chat memory is stored in a local
  `chat_memory.db`.
- **Postgres / Supabase:** set `DATABASE_URL` (see below) and run the
  migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

### 4. Run the API

```bash
uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

---

## 🔧 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI key (chat model, Whisper, TTS) |
| `SECRET_KEY` | ✅ | JWT signing key — **at least 32 characters**; the app refuses to start otherwise. Use a different value in production than in development |
| `DATABASE_URL` | production | Postgres connection string. Defaults to a local SQLite file when unset. `postgres://` and `postgresql://` URLs are converted to the `psycopg` driver automatically |
| `CORS_ORIGINS` | production | Comma-separated list of allowed browser origins, no trailing slashes. Defaults to local dev origins plus the Lovable app URL |
| `CORS_ORIGIN_REGEX` | optional | Regex for additional allowed origins. Defaults to `*.lovable.app` / `*.lovableproject.com` |
| `LOG_LEVEL` | optional | Python log level (default `INFO`) |

Never commit `backend/.env`. It is listed in `.gitignore`.

---

## 🗄 Database and Migrations

- **Alembic owns the application schema** in Postgres. When you change
  `backend/app/database/models.py`, generate and apply a migration:

  ```bash
  alembic -c backend/alembic.ini revision --autogenerate -m "describe the change"
  alembic -c backend/alembic.ini upgrade head
  ```

- The LangGraph checkpoint tables (`checkpoints`, `checkpoint_blobs`,
  `checkpoint_writes`, `checkpoint_migrations`) are created automatically by
  the checkpointer on first start. Do not manage them with Alembic.
- **Supabase connection string:** use the **Session pooler** string
  (IPv4-compatible), not the direct connection (IPv6-only on the free tier,
  which fails from IPv4-only hosts such as Render). If your database
  password contains special characters (`@`, `#`, `/`, `:`, `%`), URL-encode
  them inside `DATABASE_URL`.
- **Supabase security:** tables created through migrations are not
  protected by Row Level Security by default. This backend connects directly
  to Postgres and does not use Supabase's auto-generated Data API, so turn
  the Data API off (Project Settings → Data API) and/or enable RLS on every
  table, including any new ones you add later.

---

## 🚀 Deployment (Render + Supabase)

Production runs as a **Render web service** (free tier) connected to a
**Supabase Postgres** database.

### Render service settings

| Setting | Value |
|---|---|
| Runtime | Python 3 (set `PYTHON_VERSION` to match your local version) |
| Root Directory | *(empty — the repo root)* |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `alembic -c backend/alembic.ini upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"` |
| Health Check Path | `/health` |

The start command applies pending migrations on every boot (a no-op when
the schema is current). `--proxy-headers` makes the app see each visitor's
real IP behind Render's proxy; without it, all users would share a single
login rate-limit bucket.

Set these environment variables in the Render dashboard (never in the
repo): `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `CORS_ORIGINS`,
`LOG_LEVEL`, `PYTHON_VERSION`.

After deploying, check `https://<your-service>.onrender.com/health`, then
try registration, login and a chat message from `/docs`.

### Deployment notes

- Render redeploys automatically on every push to the connected branch.
- The free instance's filesystem is ephemeral, which is why conversation
  memory is stored in Postgres rather than a local SQLite file.
- Free Supabase projects can pause after a period of inactivity and need to
  be resumed from the dashboard.
- `render.yaml` is a Blueprint template that provisions a Render-managed
  Postgres database. The live deployment uses Supabase and was configured
  manually with the settings above.

---

## 🧪 Running Tests

From the repository root:

```bash
pytest
```

The suite uses an in-memory SQLite database that is completely separate
from your real data, resets the rate limiter before every test, and covers:

| File | Covers |
|---|---|
| `tests/test_auth_api.py` | registration, login, validation |
| `tests/test_tasks_api.py` | task endpoints and per-user isolation |
| `tests/test_notes_api.py` | note endpoints and per-user isolation |
| `tests/test_chat_api.py` | chat endpoints |
| `tests/test_chat_rate_limit.py` | chat rate limit and message-length cap |
| `tests/test_ai_tools.py` | the agent's task and note tools |

---

## 🛠 Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL (Supabase),
SQLite (local fallback), LangChain, LangGraph, OpenAI (chat, Whisper, TTS),
python-jose (JWT), passlib (bcrypt), slowapi (rate limiting), pytest

**Hosting:** Render (API), Supabase (database)

**Frontend:** built with Lovable in a
[separate repository](https://github.com/CodeWithDks/personal-ai-assistant-web)
(React, TanStack Start, Tailwind CSS)

---

## 🎯 Status

- [x] Task and note CRUD (API + agent tools)
- [x] Tool-calling conversational agent
- [x] Persistent, per-user conversation memory (Postgres)
- [x] JWT authentication
- [x] Voice input (speech-to-text) and output (text-to-speech)
- [x] Database migrations (Alembic)
- [x] Test suite (pytest)
- [x] Rate limiting and input validation
- [x] Deployed: Render (API) + Supabase (database)
- [x] Frontend connected (Lovable)

### Planned
- [ ] Chat history endpoints (`GET` / `DELETE /chat/history`) so the UI can
  reload and reset conversations
- [ ] Upload size limit on `/chat/voice`
- [ ] Streaming agent responses
- [ ] Multi-turn voice conversations (not just single utterances)

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

---

## 👨‍💻 Author

**Deepak Kumar Singh**
GitHub: [github.com/CodeWithDks](https://github.com/CodeWithDks)
LinkedIn: [linkedin.com/in/deepaksinghai](https://linkedin.com/in/deepaksinghai)