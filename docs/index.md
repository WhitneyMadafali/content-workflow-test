# Content Workflow

**Purpose:** Content lifecycle management framework, workflows, and tools for Omnivoltaic's content-as-code system.

**Scope:** Genesis → Seed → Forms → Apps → Serving

---

## Overview

This repository houses the conceptual frameworks, process documentation, and automation tools that support Omnivoltaic's end-to-end content lifecycle.

### Content Lifecycle Stages

1. **Genesis** - Source material capture (chaotic, unstructured)
2. **Seed** - Structured documentation (markdown, schemas)
3. **Forms** - Content intents and designs (decks, sites)
4. **Apps** - Component implementations (React/JSX)
5. **Serving** - Published delivery (domains, CDN)

---

## Documentation Sections

### [Frameworks](frameworks.md)
Conceptual models and philosophical foundations for content-as-code.

### [Workflows](workflows.md)
Operational process documentation for each lifecycle stage.

### [Delivery Intents](delivery-intents.md)
Domain strategy and content delivery architecture.

---

## Tools

Automation tools supporting the content lifecycle are located in the `/tools` directory:

- **SharePoint Content Scanner** - Extract content from SharePoint for genesis stage processing
- Tool usage documentation is covered in the [Workflows](workflows.md) section

---

## Related Repositories

- **oves-decks** - Presentation forms and stylesheets
- **oves-sites** - Website design intents and architecture
- **dirac-uxi** - Content application implementations

---

For detailed documentation, refer to [docs.omnivoltaic.com/content-workflow](https://docs.omnivoltaic.com/content-workflow)
