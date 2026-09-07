# College  Assistant Agent - Task & Course Extraction from Email

Stux Agent reads live Canvas notification emails from Gmail, extracts structured
tasks and course facts with OpenAI, saves the results as JSON, and automatically
creates Google Tasks or Google Calendar events. It is a backend-only FastAPI app;
there is no dashboard or manual review step.

## Flow

1. Fetch recent Gmail messages matching the configured query.
2. Extract relevance, type, title, course code, due date, priority, overview, and
   checklist steps with OpenAI.
3. Write relevant records to `output/tasks_and_courses.json` and all processed
   messages to `output/all_messages.json`.
4. Immediately push each new relevant record to Google:
   - A dated `course` record becomes an all-day Google Calendar event.
   - Everything else becomes a Google Task.
5. Record successful pushes in `output/google_actions_sync.json` to avoid duplicates.

## Requirements

- Python 3.10+
- An OpenAI API key
- A Google Cloud desktop OAuth client with the Gmail, Google Tasks, and Google
  Calendar APIs enabled

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Set these values in `.env`:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required for extraction |
| `OPENAI_MODEL` | Optional; defaults to `gpt-4o-mini` |
| `GMAIL_CREDENTIALS_PATH` | OAuth client file; defaults to `credentials.json` |
| `GMAIL_TOKEN_PATH` | OAuth token file; defaults to `token.json` |

`config.json` is optional and can contain `gmailQuery` and `limit`. The built-in
query defaults to `from:notifications@instructure.com`, and the default limit is 10.

## Run

Start the API:

```bash
uvicorn backend.main:app --reload --port 8000
```

Trigger the full fetch, extraction, and automatic Google push:

```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"limit": 15}'
```

Interactive API documentation is available at `http://localhost:8000/docs`.
The first run opens Google's OAuth consent flow. Successful and failed pushes are
reported in the `/api/run` response; one failed record does not prevent the others
from being processed.

## Structure

- `backend/main.py` — FastAPI application
- `backend/routers/run.py` — full-run endpoint
- `backend/services/pipeline.py` — Gmail → OpenAI → JSON → Google pipeline
- `backend/services/google_actions.py` — automatic routing and delivery
- `backend/services/google_auth.py` — shared Google OAuth credentials
- `backend/services/sync_store.py` — duplicate-push protection
- `output/` — generated JSON results and sync state
- `examples/readme.md` — configuration reference

Because delivery is automatic, extracted content can create real Tasks or Calendar
events immediately. Use credentials for an account where that behavior is intended.
