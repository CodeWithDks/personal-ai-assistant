# 🧠 Personal AI Assistant

A full-stack, LangChain/LangGraph-powered personal assistant — manage
tasks and notes through natural-language chat, with a tool-calling agent
that decides which action to take, persistent per-user conversation
memory, JWT authentication, and voice input/output. Backend in FastAPI,
frontend in React.

---

## ✨ Features

- 🤖 **Conversational AI agent** — a LangChain `create_agent` tool-calling
  agent that manages tasks and notes through plain-language chat
  (`backend/app/ai/agent.py`)
- 💾 **Persistent conversation memory** — a LangGraph `SqliteSaver`
  checkpointer, thread-scoped per user, so the assistant remembers
  context across messages and sessions (`backend/app/ai/memory.py`)
- 🔐 **JWT authentication** — signup/login with bcrypt password hashing
  and signed tokens (`backend/app/core/security.py`, `routes/auth.py`)
- ✅ **Task management** — full CRUD, exposed to the agent as tools
  (`ai/tools/tasks.py`) and as a normal REST API (`routes/task_routes.py`)
- 📝 **Note management** — same pattern: agent tools + REST API
  (`ai/tools/notes.py`, `routes/note_routes.py`)
- 🎙️ **Voice input/output** — speech-to-text (Whisper) and
  text-to-speech (OpenAI TTS), so the assistant can be talked to, not
  just typed to (`backend/app/ai/voice.py`)
- 🗄️ **Real database migrations** — Alembic, not just `create_all()`
  (`backend/alembic/`)
- 🧪 **Test suite** — pytest, covering auth, chat, notes, tasks, and the
  AI tools layer (`tests/`)
- 💻 **React frontend** — TypeScript, Vite, Tailwind (`frontend/`)

---

## 🏗 Architecture

```
User (chat, voice, or direct task/note actions)
        │
        ▼
  React frontend (Vite + TypeScript + Tailwind)
        │  REST API calls
        ▼
  FastAPI backend
        │
        ├── routes/          auth, chat, tasks, notes — HTTP layer
        ├── services/        business logic (auth_service, task_service, note_service)
        ├── ai/
        │     ├── agent.py       builds a per-user LangChain agent
        │     ├── llm.py         the underlying chat model
        │     ├── memory.py      LangGraph SqliteSaver — per-user thread memory
        │     ├── prompts.py     system prompt construction
        │     ├── voice.py       Whisper (speech-to-text) + OpenAI TTS
        │     └── tools/         tasks.py, notes.py — the tools the agent can call
        ├── database/         SQLAlchemy models + engine (models.py, database.py)
        ├── core/             security (JWT, password hashing)
        └── schemas/          Pydantic request/response models
        │
        ▼
  SQLite (assistant.db — tasks/notes/users, via SQLAlchemy + Alembic)
  SQLite (chat_memory.db — conversation checkpoints, via LangGraph SqliteSaver)
```

Two separate SQLite databases by design: `assistant.db` holds structured
application data (users, tasks, notes) through SQLAlchemy, while
`chat_memory.db` holds LangGraph's own conversation checkpoints — keeping
the agent's memory format independent of the application's own schema.

---

## 📂 Project Structure

```
personal-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── ai/                  Agent, memory, voice, tools, prompts
│   │   ├── api/                 Shared dependencies (deps.py)
│   │   ├── core/                Security (JWT, hashing)
│   │   ├── database/            SQLAlchemy models + engine
│   │   ├── routes/               auth, chat, tasks, notes
│   │   ├── schemas/               Pydantic models
│   │   ├── services/              Business logic
│   │   └── main.py                 FastAPI app entry point
│   ├── alembic/                  Database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env                       (not committed — see Setup)
│
├── frontend/
│   ├── src/
│   │   ├── api/                  API client calls to the backend
│   │   ├── components/            auth, chat, tasks, notes, layout, shared
│   │   ├── context/                 React context providers
│   │   ├── hooks/                    Custom hooks
│   │   ├── pages/                     Route-level pages
│   │   ├── types/                      TypeScript types
│   │   └── utils/                       Helpers
│   ├── package.json
│   └── .env.example
│
├── tests/                       pytest — auth, chat, tasks, notes, AI tools
├── pytest.ini
└── README.md
```

---

## ⚙ Setup

### 1. Backend

```bash
cd backend
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
pip install -r requirements.txt
```

Create a `.env` file **inside `backend/`** (not the project root — the
app loads it from this exact path):

```env
OPENAI_API_KEY=your_api_key_here
SECRET_KEY=your_generated_secret_here
```

Generate a real `SECRET_KEY`:
```bash
openssl rand -hex 32
```

Run database migrations:
```bash
alembic upgrade head
```

Start the backend:
```bash
uvicorn backend.app.main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm i
```

Create `frontend/.env` from the provided example:
```bash
cp .env.example .env
```

```bash
npm run dev
```

---

## 🧪 Running Tests

From the project root:

```bash
pytest
```

Covers authentication, chat, task and note endpoints, and the agent's
tool layer (`tests/test_auth_api.py`, `test_chat_api.py`,
`test_tasks_api.py`, `test_notes_api.py`, `test_ai_tools.py`).

---

## 🛠 Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, Alembic, SQLite, LangChain,
LangGraph, OpenAI (chat, Whisper, TTS), python-jose (JWT), passlib
(bcrypt), pytest

**Frontend:** React, TypeScript, Vite, Tailwind CSS

---

## 🎯 Status

- [x] Task and note CRUD (API + agent tools)
- [x] Tool-calling conversational agent
- [x] Persistent, per-user conversation memory
- [x] JWT authentication
- [x] Voice input (speech-to-text) and output (text-to-speech)
- [x] Database migrations (Alembic)
- [x] Test suite (pytest)
- [x] React frontend (replacing an earlier Streamlit UI)

### Planned
- [ ] Deployment (Docker / hosted)
- [ ] Streaming agent responses in the UI
- [ ] Multi-turn voice conversations (not just single utterances)

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

---

## 👨‍💻 Author

**Deepak Kumar Singh**
GitHub: [github.com/CodeWithDks](https://github.com/CodeWithDks)
LinkedIn: [linkedin.com/in/deepaksinghai](https://linkedin.com/in/deepaksinghai)