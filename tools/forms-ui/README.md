# Forms UI (simple web front-end)

This is a minimal web UI for non-technical users to summarize Microsoft Forms responses.

It calls the existing logic in `tools/forms-mcp/server.py`, so output structure matches the MCP tool behavior.

## What users do

1. Open the page in a browser.
2. Paste a Forms URL.
3. Click **Generate summary**.
4. Read the executive summary and per-question highlights.

## One-time setup

From repository root:

```bash
cd tools/forms-ui
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

From `tools/forms-ui`:

```bash
BROWSER=google-chrome .venv/bin/python app.py
```

Then open:

`http://127.0.0.1:7860`

## Notes

- First run may open Microsoft sign-in when Forms auth is needed.
- Token cache is still managed by `tools/forms-mcp` (for example `.forms_token_cache.json` there).
- This UI is intentionally simple (single page). It is a good MVP for internal users.

## Deploy on Vercel

This repo now includes a root `vercel.json` that routes all requests to `tools/forms-ui/app.py`.

### 1) Create the Vercel project

From repo root:

```bash
npm i -g vercel
vercel
```

For production:

```bash
vercel --prod
```

### 2) Set environment variables in Vercel

In Vercel Project Settings -> Environment Variables, add at least:

- `FORMS_UI_HOST=0.0.0.0`
- `FORMS_UI_PORT=7860`
- `BROWSER=none`

If you move to server-side OAuth for Microsoft Graph, also add app credentials and callback settings there.

### 3) Important auth caveat

Current Teams auth in this app uses local interactive sign-in and local token cache files.
That pattern is fine locally, but it is not ideal for serverless production.
For a robust Vercel deployment you should migrate to web OAuth callback + durable token storage (for example Redis/Postgres).

### 4) Quick check

After deploy, open your Vercel URL and verify:

- Team list loads
- Channel changes refresh context
- Summary generation works
- Person filter works (Fast mode on/off)
