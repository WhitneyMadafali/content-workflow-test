# Forms MCP Server

MCP server for **actual Microsoft Forms response data** (not Teams link posts).

## What this server does

- Authenticate to Microsoft Forms (`forms.office.com`) using MSAL
- Resolve a Forms URL to a form ID
- Fetch real response records from Forms API
- Summarize responses with **`executive_summary`** (thematic paragraph) plus **`by_question`** detail

## Before you start

- **Python 3** installed (`python3 --version`)
- This repo **cloned** on your machine (you will `cd` into `.../content-workflow` or similar)
- **Cursor** (if using MCP in the editor) or a terminal only (if using CLI commands)
- A Microsoft work/school account that can **open the form** and (for API access) use an Entra app with **Forms** permissions — your IT may need to approve the default app or yours via `FORMS_CLIENT_ID`

**Paths:** Commands below use **`cd tools/forms-mcp` from the repository root**. If your terminal is **already** in `tools/forms-mcp`, do **not** run `cd tools/forms-mcp` again (that path would not exist).

**Tokens / login files:** The repo **does not** include (and **never** commits) Microsoft token caches such as **`.forms_token_cache.json`**. There is **nothing to copy from GitHub**. After you install the venv, you **sign in once** (see **§3 Sign in** or the first MCP/CLI call that needs Forms). The app then **creates** `.forms_token_cache.json` next to `server.py` on **your** machine only. If you clone on another PC, run sign-in again there.

## Quick start: I just found this repo and want a summary of form responses

**Goal:** Use **Forms MCP** in Cursor so the assistant can call **`summarize_form_responses`** and give you a readable summary (not row-by-row reading in the Forms website).

### 1. Install the server (once)

From the **repository root**:

```bash
cd tools/forms-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Remember the **full path** to `tools/forms-mcp` on your machine (you will paste it into Cursor).

### 2. Register the MCP server in Cursor (once)

Open **Cursor Settings → MCP** and add a server. Point **command** at the venv **python** and pass **`server.py`** as the **argument** (exact field names depend on your Cursor version; “Command” vs “Args” split is typical).

**Environment:** set `BROWSER` to your browser (e.g. `google-chrome`) so device login can open a window.

**Example** (replace paths with your machine):

```json
{
  "mcpServers": {
    "forms-responses": {
      "command": "/home/you/projects/content-workflow/tools/forms-mcp/.venv/bin/python",
      "args": ["/home/you/projects/content-workflow/tools/forms-mcp/server.py"],
      "env": {
        "BROWSER": "google-chrome"
      }
    }
  }
}
```

If your Cursor UI only has a single “command line”, it is often equivalent to:

`BROWSER=google-chrome /absolute/path/to/content-workflow/tools/forms-mcp/.venv/bin/python /absolute/path/to/content-workflow/tools/forms-mcp/server.py`

After saving, restart Cursor or reload MCP if needed.

### 3. Sign in to Microsoft Forms (once per machine)

In a terminal (same machine):

```bash
cd /absolute/path/to/content-workflow/tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py auth-test
```

Complete the browser login if prompted. On success, **`tools/forms-mcp/.forms_token_cache.json`** is **created automatically** (it is not in git—you do not check out or download this file). Later runs reuse it until it expires or you delete it.

### 4. Get a summary in chat

1. In Cursor, enable the **Forms** MCP server (if your UI has a toggle).
2. Open a chat and ask the assistant to call **`summarize_form_responses`** with:
   - **`form_url`:** your form link, e.g. `https://forms.office.com/r/...` (or **`form_id`** if you know it), **or**
   - If the form was only posted in Teams, use the **Teams channel → Forms summary** section below (scan channel first, then summarize).
3. Ask for a **short written summary** of what people said. The repo includes a Cursor rule so the assistant should answer in **prose**, not dump raw JSON.

**Optional — terminal only (no Cursor MCP):**

```bash
cd tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py summarize-test --brief --form-url "https://forms.office.com/r/..." --top 25
```

`--brief` prints **`executive_summary`** (thematic paragraph) first, then short **theme lines per question** (not full quotes). Omit `--brief` for complete JSON including **`respondent_texts`**.

### 5. If sign-in or API calls fail

- Set **`FORMS_CLIENT_ID`** to an Azure (Entra) app that has **Microsoft Forms** delegated permissions for your tenant.  
- See **Required permissions** below.

### 6. Form link only lives in a Teams channel

Use the next section (**Teams channel → Forms summary**) so you do **not** have to paste the Forms URL by hand.

---

## Teams channel → Forms summary (no pasted URL)

Requires a **second** setup: Python venv under **`tools/teams`** and Microsoft Graph sign-in (see **`tools/teams/README.md`**). Forms MCP and Teams scanner use **different** token files.

Use the **Teams scanner** to pull channel posts into JSON; each post now includes **`forms_urls`** (real `https://forms.office.com/...` links, including links wrapped in Outlook Safe Links). Then run the **bridge script** so Forms auth uses those URLs automatically.

**1) Scan the channel** (Microsoft Graph — uses `tools/teams` venv and token cache). Paths below assume the **repository root** (`content-workflow/`). If you are already in `tools/forms-mcp`, use `cd ../teams` instead of `cd tools/teams`.

```bash
cd tools/teams
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --select-account \
  --team-name "Exact team display name" \
  --channel-name "Exact channel name" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 50 \
  -o analyses/channel-forms.json
```

Use **`--select-account`** the first time (or to switch users) so the browser signs in as **you**, not whoever is cached in `tools/teams/scripts/.teams_token_cache.json`. Replace team/channel names with real values from **`--list-teams`** (not the placeholder text `"Your Team"`).

**2) Summarize using the first Forms link found** (Forms API — `tools/forms-mcp` venv). From repo root:

```bash
cd tools/forms-mcp
BROWSER=google-chrome .venv/bin/python summarize_from_teams_export.py ../teams/analyses/channel-forms.json
```

If you are still under `tools/forms-mcp`, the same command works as long as you pass the JSON path relative to your cwd, e.g. `../teams/analyses/channel-forms.json`.

**One-shot script** (scan + summarize) from the repo root — replace with your real team and channel **display names**:

```bash
bash tools/forms-mcp/scan_channel_forms_summary.sh "Your real team name" "General"
```

First time (or to sign in as yourself instead of a cached user):

```bash
SCAN_SELECT_ACCOUNT=1 bash tools/forms-mcp/scan_channel_forms_summary.sh "Your real team name" "General"
```

The script prints **`--brief`** output by default (**`executive_summary`** + per-question theme lines). For the full JSON payload, run `FULL_JSON=1 bash tools/forms-mcp/scan_channel_forms_summary.sh ...`.

Use **`--pick N`** if several forms appear in the file. This calls the same logic as the MCP tool **`summarize_form_responses`** (which returns **`executive_summary`**, **`by_question`**, **`respondent_texts`**, etc.).

You need **both** sign-ins (Graph for Teams, Forms for responses) unless your tenant uses a single app with both permissions.

## Run (stdio MCP server)

```bash
cd tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py
```

## Test with real Microsoft auth (local)

1. **Sign-in / token check** — prints `tenant_id` and `user_object_id` when the Forms token is valid (browser may open on first run):

```bash
cd tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py auth-test
```

2. **Summarize smoke test** — use your real form URL; add **`--brief`** for **`executive_summary`** + theme lines only:

```bash
BROWSER=google-chrome .venv/bin/python server.py summarize-test --brief --form-url "https://forms.office.com/r/..." --top 25
```

Token cache is written to `.forms_token_cache.json` next to `server.py` (gitignored).

**Prose-first workflow:** The repo includes a Cursor rule (`.cursor/rules/forms-mcp-summaries.mdc`) so the **assistant** leads with a thematic summary. The MCP tool **prepends** short instructions on every `summarize_form_responses` result. For terminal runs, use **`--brief`** on `summarize-test` or `summarize_from_teams_export.py` for **`executive_summary`** + theme lines without dumping full JSON.

## Troubleshooting (common issues)

| Problem | What to try |
|--------|-------------|
| `cd tools/forms-mcp` fails | Your shell is already **inside** `tools/forms-mcp`. Stay there, or `cd` to the **repo root** first. |
| Teams scan shows **0 joined Teams** | Use real **team/channel** names (not `"Your Team"`). Run with **`--select-account`**. Delete `tools/teams/scripts/.teams_token_cache.json` if the wrong account is cached. |
| Forms auth fails | Set **`FORMS_CLIENT_ID`** to an app with Forms delegated permissions; see **Required permissions**. |
| Question titles look like `r1a2b3c…` | The Forms “light” definition may omit titles; content in **`respondent_texts`** is still correct. |
| I want every answer verbatim | Omit **`--brief`** in CLI, or read **`respondent_texts`** in the full MCP JSON. |

## Exposed tools

- `whoami_forms()`
  - Auth check + token context (`tenant_id`, `user_object_id`, scope used)
- `resolve_form(form_url)`
  - Resolve a Forms URL to `form_id`
- `list_form_responses(form_url|form_id, tenant_id?, user_object_id?, top?, skip?)`
  - Fetch real response rows from Forms API
- `summarize_form_responses(...)`
  - Returns **`executive_summary`** (automatic thematic paragraph), **`by_question`** ( **`rating`**, **`respondent_texts`**, theme lines), **`summary_text`**, **`synthesis_hint`**, **`sample_respondents`**, and pagination via **`fetch_all`** / **`max_responses`**. Prefer showing **`executive_summary`** to users first; use **`respondent_texts`** for detail.

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
