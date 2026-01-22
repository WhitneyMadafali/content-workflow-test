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

---

For detailed documentation, refer to [docs.omnivoltaic.com/content-workflow](https://docs.omnivoltaic.com/content-workflow)
