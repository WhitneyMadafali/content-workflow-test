# Forms MCP Server

MCP server for **actual Microsoft Forms response data** (not Teams link posts).

## What this server does

- Authenticate to Microsoft Forms (`forms.office.com`) using MSAL
- Resolve a Forms URL to a form ID
- Fetch real response records from Forms API
- Provide compact summaries for quick triage

## Install

```bash
cd tools/forms-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
cd tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py
```

## Configure in MCP client

```bash
BROWSER=google-chrome /absolute/path/content-workflow/tools/forms-mcp/.venv/bin/python /absolute/path/content-workflow/tools/forms-mcp/server.py
```

## Exposed tools

- `whoami_forms()`
  - Auth check + token context (`tenant_id`, `user_object_id`, scope used)
- `resolve_form(form_url)`
  - Resolve a Forms URL to `form_id`
- `list_form_responses(form_url|form_id, tenant_id?, user_object_id?, top?, skip?)`
  - Fetch real response rows from Forms API
- `summarize_form_responses(...)`
  - Response count + sample rows for quick review

## Required permissions

Your Entra app registration must allow Microsoft Forms delegated access.
If authentication fails, set a client ID with the right Forms permissions:

```bash
export FORMS_CLIENT_ID="<your-forms-enabled-client-id>"
```

Optional scope override:

```bash
export FORMS_SCOPES="https://forms.office.com/.default"
```

## Notes

- This uses Forms API endpoints under `https://forms.office.com/formapi/api/...`.
- If your tenant blocks Forms API for your app, token acquisition or response calls will fail.
- This server is separate from `tools/teams-mcp` and is intended for **form response data**.
