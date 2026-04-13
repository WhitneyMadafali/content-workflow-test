# Forms responses MCP (`tools/forms-mcp`)

Use **Microsoft Forms APIs** from **Cursor** (or another MCP client) to read and summarize **submitted responses**. Data comes from **Forms**, not from Teams channel message bodies.

## When to use this page

- You have a `forms.office.com` (or equivalent) form URL and want **response summaries** or per-question rollups in the editor.
- You need **submission records from Forms**, not “who posted the link in a channel.”

## Step-by-step

Assume the **repo is cloned** and **Python 3** is installed. Replace paths below with **absolute paths** on your machine.

### A. You have a form URL: summarize in Cursor (typical path)

**1) Install the Forms MCP dependencies (once per machine)**

From the repository root:

```bash
cd tools/forms-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Note the full path to `tools/forms-mcp` for the next step.

**2) Register the MCP server in Cursor (once per machine)**

Open **Cursor → Settings → MCP** and add a server:

- **Command:** path to `.venv/bin/python` from step 1 (full path).
- **Args:** full path to `server.py` in the same folder.
- **Environment:** set `BROWSER` (e.g. `google-chrome`) so device login can open a browser.

Save, then **restart Cursor** or reload MCP if needed. Example JSON (edit paths):

```json
{
  "mcpServers": {
    "forms-responses": {
      "command": "/your/path/content-workflow/tools/forms-mcp/.venv/bin/python",
      "args": ["/your/path/content-workflow/tools/forms-mcp/server.py"],
      "env": {
        "BROWSER": "google-chrome"
      }
    }
  }
}
```

**3) Sign in to Microsoft Forms (usually once per machine)**

In a terminal:

```bash
cd /your/path/content-workflow/tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py auth-test
```

Complete browser sign-in. On success, **`.forms_token_cache.json`** is created next to `server.py` (it is **not** in git—do not commit it). Later runs reuse it until it expires or you delete it.

**4) Ask for a summary in chat**

1. Ensure the Forms MCP server is enabled if your UI has a toggle.
2. Ask the assistant to call **`summarize_form_responses`** with **`form_url`** (e.g. `https://forms.office.com/r/...`) or **`form_id`** if you know it.
3. Ask for a **short prose summary**, not raw JSON. The repo Cursor rule steers answers toward **`executive_summary`**-style text first.

**5) If sign-in or API calls fail**

- Confirm your tenant allows **Microsoft Forms** delegated permissions; set **`FORMS_CLIENT_ID`** to an Entra app that has Forms permissions if required. See **Required permissions** and the troubleshooting table in [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md).

### B. Without Cursor: quick CLI check

Same install as **§A**. From `tools/forms-mcp` (use your real form URL):

```bash
BROWSER=google-chrome .venv/bin/python server.py summarize-test --brief --form-url "https://forms.office.com/r/..." --top 25
```

`--brief` prints **`executive_summary`** first, then short theme lines per question. Omit `--brief` for full JSON including **`respondent_texts`**.

### C. Optional: the form link only appears in a Teams channel

You need a **second** setup: `tools/teams` venv and **Microsoft Graph** sign-in (separate token from Forms). Outline:

1. Scan the channel with `tools/teams` and export JSON that contains Forms URLs (see [Forms links in Teams](forms-mcp.md)).
2. From `tools/forms-mcp`, run `summarize_from_teams_export.py` pointing at that JSON, or use `scan_channel_forms_summary.sh`.

Full commands, the one-shot script, and **`--pick N`** when several forms appear are in **Teams channel → Forms summary** in [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md).

## Further reading

Permissions, exposed tools, and troubleshooting:

- On GitHub: [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md)
- After clone, local path: `tools/forms-mcp/README.md`

## vs. “Forms links in Teams channels”

| | **Forms responses MCP** (this page) | **[Forms links in Teams](forms-mcp.md)** |
| --- | --- | --- |
| Data source | Forms API (submissions) | Teams channel messages (posts/replies with URLs) |
| Typical entry | `tools/forms-mcp/server.py` | `tools/teams` scan scripts, `tools/teams-mcp` |
| Typical use | Summarize real responses | Export JSON of posts that contain Forms URLs |

## See also

- [Forms links in Teams](forms-mcp.md)
- [Teams MCP](teams-mcp.md)
