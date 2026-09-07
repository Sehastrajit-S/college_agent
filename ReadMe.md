# College Assistant Agent

College Assistant Agent reads Canvas notification emails from Gmail, extracts
tasks and course information with OpenAI, and creates Google Tasks or Google
Calendar events. It is a local, single-user FastAPI application.

> **Important:** Running the pipeline can create real Google Tasks and Calendar
> events automatically. Start with a test Google account and a narrow Gmail query.

## What the app does

1. Reads recent inbox messages matching the configured Gmail search query.
2. Sends their text to OpenAI for structured extraction.
3. Saves generated data under `output/`.
4. Creates an all-day Calendar event for a dated course record; other relevant
   records become Google Tasks.
5. Records created Google object IDs to avoid creating them again on later runs.

## Prerequisites

- Python 3.10 or newer
- An OpenAI API key
- A Google account
- A Google Cloud project that you can configure

## 1. Install the application

From the repository root:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI key to `.env`:

```dotenv
OPENAI_API_KEY=your_key_here
```

Do not add quotes unless they are part of the value. The `.env` file is ignored
by Git.

## 2. Configure Google Cloud

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and create
   or select a project.
2. In **APIs & Services > Library**, enable all three APIs:
   - Gmail API
   - Google Tasks API
   - Google Calendar API
3. Open **Google Auth Platform** and configure the OAuth consent screen.
4. For a personal/test project, choose **External**, leave the app in testing,
   and add the Google account you will connect under **Test users**.
5. Under **Data Access**, add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/tasks`
   - `https://www.googleapis.com/auth/calendar.events`
6. Open **Clients**, create an OAuth client, and select **Desktop app**. This is
   required because the current application opens the system browser locally.
7. Download the client JSON. Rename it to `credentials.json` and place it in the
   repository root.

Do not manually fill in `credentials.example.json`; it exists only to show the
expected shape. Use the JSON downloaded from Google.

Google may show an unverified-app warning while the OAuth project is in testing.
Only accounts listed as test users can authorize it. A public deployment must
complete Google's applicable OAuth verification requirements.

## 3. Configure environment variables

The defaults in `.env.example` work when `credentials.json` is in the repository
root:

| Variable | Required | Description |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | API key used for email extraction |
| `OPENAI_MODEL` | No | Extraction model; defaults to `gpt-4o-mini` |
| `GMAIL_CREDENTIALS_PATH` | No | Desktop OAuth client JSON path |
| `GMAIL_TOKEN_PATH` | No | Local authorized-user token path |
| `GMAIL_QUERY` | No | Fallback Gmail search query |

Relative credential and token paths are resolved from the repository root, so
the app behaves consistently regardless of the current working directory.

`config.json` controls run defaults:

```json
{
  "gmailQuery": "from:notifications@instructure.com",
  "limit": 15
}
```

`gmailQuery` accepts normal
[Gmail search syntax](https://support.google.com/mail/answer/7190). Use a narrow
query while testing, for example:

```text
from:notifications@instructure.com newer_than:7d
```

A `gmail_query` or `limit` supplied to `POST /api/run` overrides `config.json`.

## 4. Start and connect

Run this from the repository root with the virtual environment active:

```bash
python -m uvicorn src.backend.main:app --reload --port 8000
```

Verify that the API loaded:

```bash
curl http://localhost:8000/api/health
```

It should return `{"status":"ok"}`. Interactive documentation is available at
<http://localhost:8000/docs>.

Start Google authorization:

```bash
curl -X POST http://localhost:8000/api/gmail-auth
```

A browser window opens. Sign in as a configured test user and approve access.
The resulting `token.json` contains a refresh token and must never be committed,
shared, printed, or uploaded.

Check connection status:

```bash
curl http://localhost:8000/api/gmail-auth
```

## 5. Run the pipeline

Use a small limit first:

```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"limit": 3, "gmail_query": "from:notifications@instructure.com newer_than:7d"}'
```

In PowerShell, `Invoke-RestMethod` avoids shell quoting differences:

```powershell
$body = @{ limit = 3; gmail_query = "from:notifications@instructure.com newer_than:7d" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/run -ContentType application/json -Body $body
```

Generated files are stored in `output/` and may contain private email content.
That directory is ignored by Git.

## Troubleshooting

### `credentials.json` was not found

Download a **Desktop app** OAuth client from Google Cloud. Put it at the repository
root or set an absolute `GMAIL_CREDENTIALS_PATH` in `.env`.

### `redirect_uri_mismatch` or the credentials type is rejected

The current local flow requires a **Desktop app** OAuth client. Do not use a Web,
Android, iOS, or service-account credential file.

### `Access blocked`, `access_denied`, or an unverified-app screen

Confirm the OAuth app is in testing and the selected Google account is listed as
a test user. Also confirm that the three requested scopes are configured on the
consent screen. A Workspace administrator can block third-party Gmail access.

### Authorization worked before but scopes changed

Stop the server, delete the local `token.json`, restart, and connect again. Only
delete that exact token file; deleting it requires the user to grant consent again.

### Port or browser problems

The OAuth library starts a temporary localhost callback on an available port. Run
the app on a machine with a browser. Headless/server deployment requires a web
OAuth callback implementation and persistent encrypted per-user token storage.

### OpenAI or Google API request fails

Read the API response returned by `/api/run`, confirm all APIs are enabled, and
confirm billing/quota/account policies. Avoid repeated rapid retries because Gmail
enforces per-user and project quotas.

## Security and deployment boundary

This repository's OAuth flow and JSON storage are intended for one user running
the app locally. They are not a production multi-user connector. Before deploying
for other users, replace the desktop OAuth flow and local token file with:

- HTTPS web-server OAuth callbacks with CSRF `state` validation and PKCE
- encrypted, per-user refresh-token storage
- persistent jobs, bounded exponential-backoff retries, and dead-letter handling
- incremental Gmail synchronization using `historyId`
- authenticated Pub/Sub push notifications and scheduled watch renewal
- audit logging, user disconnect/data deletion, and Google OAuth verification

`credentials.json` was tracked in the repository's initial history. If that file
ever contained a real OAuth client secret, create or rotate the OAuth client in
Google Cloud before sharing or publishing the repository. Ignoring or untracking
the file prevents future commits but does not remove it from existing Git history.

See Google's [web-server OAuth guide](https://developers.google.com/identity/protocols/oauth2/web-server),
[Gmail synchronization guide](https://developers.google.com/workspace/gmail/api/guides/sync),
and [Gmail error-handling guide](https://developers.google.com/workspace/gmail/api/guides/handle-errors).

## Project layout

- `src/backend/main.py` — FastAPI application and health endpoint
- `src/backend/routers/` — HTTP endpoints
- `src/backend/services/pipelines.py` — Gmail → OpenAI → Google pipeline
- `src/backend/services/google_auth.py` — local Google OAuth credentials
- `src/backend/services/google_actions.py` — Tasks/Calendar routing
- `src/backend/services/sync_store.py` — duplicate-push protection
- `config.json` — safe run defaults
- `output/` — generated private data; created at runtime and ignored by Git


###Used the help of Codex to generate some