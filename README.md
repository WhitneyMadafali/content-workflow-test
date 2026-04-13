# Content Workflow

**Purpose:** Content lifecycle management framework, workflows, and tools for Omnivoltaic's content-as-code system.

**Scope:** Genesis → Seed → Forms → Apps → Serving

---

## Repository Structure

```
content-workflow/
├── docs/               # MkDocs documentation
│   ├── frameworks.md  # Conceptual models and content-as-code philosophy
│   ├── workflows.md   # Content lifecycle process documentation
│   └── delivery-intents.md  # Domain strategy and delivery documentation
├── tools/             # Content workflow automation tools (see tools/README.md)
│   ├── sharepoint/    # SharePoint content extraction (genesis stage)
│   ├── teams/         # Teams channel scan (Graph)
│   └── forms-mcp/     # Microsoft Forms responses via MCP (see below)
├── hooks/             # MkDocs build hooks
├── overrides/         # MkDocs theme customization
└── mkdocs.yml         # Documentation site configuration
```

### Forms MCP (`tools/forms-mcp`)

**What it is:** A [Model Context Protocol](https://modelcontextprotocol.io) server that connects **Cursor** (or another MCP client) to **Microsoft Forms** so you can **read and summarize submitted responses** through the Forms API—not by scraping Teams chat.

**What it is not:** It does not replace the “Forms” stage in the lifecycle diagram above (decks/sites intents); it is **tooling** for **survey/quiz response data** from `forms.office.com`.

**Where to start:** [tools/forms-mcp/README.md](tools/forms-mcp/README.md) (install, Cursor MCP config, auth, summarize). Overview of all tools: [tools/README.md](tools/README.md).

---

## Content Lifecycle Stages

1. **Genesis** - Source material capture (chaotic, unstructured)
2. **Seed** - Structured documentation (markdown, schemas)
3. **Forms** - Content intents and designs (decks, sites)
4. **Apps** - Component implementations (React/JSX)
5. **Serving** - Published delivery (domains, CDN)

---

## Related Repositories

- **oves-decks** - Presentation forms and stylesheets
- **oves-sites** - Website design intents and architecture
- **dirac-uxi** - Content application implementations

---

## Quick Start

See the documentation site for detailed information:
- [Frameworks](https://docs.omnivoltaic.com/content-workflow/frameworks) - Conceptual models
- [Workflows](https://docs.omnivoltaic.com/content-workflow/workflows) - Process guides
- [Delivery Intents](https://docs.omnivoltaic.com/content-workflow/delivery-intents) - Domain and publishing strategies

**For local development:**
```bash
pip install -r requirements.txt
mkdocs serve
```

## Local Auth Cache Files (Not Committed)

These files are **not** part of the repository and **cannot** be downloaded with the project. Each developer or machine **creates** them the first time they sign in with the corresponding tool (browser / device code flow). Typical paths:

- `tools/forms-mcp/.forms_token_cache.json` — after `auth-test`, MCP use, or CLI against Forms  
- `tools/teams/.teams_token_cache.json` — after Teams/Graph scanner sign-in  
- `tools/sharepoint/.sharepoint_token_cache.json` — after SharePoint tool sign-in  

They are environment-specific and may contain sensitive auth state. They are listed in **`.gitignore`** and must not be committed. **Setup:** follow each tool’s README (e.g. `tools/forms-mcp/README.md`); no separate “token file download” step exists.

---

For detailed documentation, refer to [docs.omnivoltaic.com/content-workflow](https://docs.omnivoltaic.com/content-workflow)
