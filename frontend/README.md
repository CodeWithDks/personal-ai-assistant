# Personal AI Assistant — React Frontend

Replaces the Streamlit UI. Talks to the same FastAPI backend at
`VITE_API_BASE_URL` (defaults to `http://127.0.0.1:8000`).

## Setup

```bash
npm install
cp .env.example .env   # edit VITE_API_BASE_URL if your backend runs elsewhere
npm run dev
```

Opens at http://localhost:5173.

## Backend CORS

The React dev server runs on a different origin than FastAPI, so add
CORS middleware to your backend's `main.py` if you haven't already:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Structure

- `src/api/` — one file per backend resource (auth, tasks, notes, chat).
  Every function returns `{ ok: true, data }` or `{ ok: false, error }`,
  same pattern as the original Streamlit `api_request` helper.
- `src/hooks/` — `useTasks` / `useNotes` own all state, filtering,
  sorting, and pagination for their resource. Components just render.
- `src/components/` — grouped by feature (`tasks/`, `notes/`, `chat/`,
  `auth/`, `layout/`) plus `shared/` for cross-feature UI primitives.
- `src/context/AuthContext.tsx` — owns login state; token lives in
  `localStorage` so a page refresh doesn't log you out (the Streamlit
  version lost the session on every refresh).

## Design

Warm paper background, ink text, a teal "signal" accent. User input
renders in the body sans font; assistant/system output (chat replies,
status badges, timestamps) renders in monospace — a deliberate visual
split between "what you typed" and "what the system says."

## Build for production

```bash
npm run build
```

Outputs static files to `dist/`, deployable to any static host (the
backend URL still needs to be reachable from wherever you host it).
