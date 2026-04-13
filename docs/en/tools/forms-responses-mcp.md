# Forms responses MCP (`tools/forms-mcp`)

Use **Microsoft Forms APIs** from **Cursor** (or another MCP client) to read and summarize **submitted responses**. Data comes from **Forms**, not from Teams channel message bodies.

## When to use this page

- You have a `forms.office.com` (or equivalent) form URL and want **response summaries** or per-question rollups in the editor.
- You need **submission records from Forms**, not “who posted the link in a channel.”

## Install and configuration

Full steps (venv, Cursor MCP, `summarize_form_responses`, sign-in, permissions) live in the repo:

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
