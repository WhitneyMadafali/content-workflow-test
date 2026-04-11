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
├── tools/             # Content workflow automation tools
│   └── sharepoint/    # SharePoint content extraction (genesis stage)
├── hooks/             # MkDocs build hooks
├── overrides/         # MkDocs theme customization
└── mkdocs.yml         # Documentation site configuration
```

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
