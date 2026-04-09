# Content Workflow Tools

Automation tools supporting the content lifecycle.

**Documentation:** Tool usage workflows are documented in [docs/workflows.md](../docs/workflows.md)

---

## Available Tools

### SharePoint Content Scanner

**Location:** `./sharepoint/`

**Purpose:** Extract content from SharePoint for genesis stage processing

**Usage:**
```bash
cd tools/sharepoint
pip install -r requirements.txt
python scripts/scan-sharepoint-graph.py
```

**Documentation:** See [sharepoint/README.md](./sharepoint/README.md)

---

### Teams Scanner

**Location:** `./teams/`

**Purpose:** Extract Teams groups, channels, messages/replies, and optional channel files to JSON

**Usage:**
```bash
cd tools/teams
pip install -r requirements.txt
python scripts/scan-teams-graph.py --include-channel-messages -o analyses/teams-scan.json
```

**Documentation:** See [teams/README.md](./teams/README.md)

---

### Teams MCP Server

**Location:** `./teams-mcp/`

**Purpose:** MCP integration for Teams channels and chats (listing, reading, searching)

**Usage:**
```bash
cd tools/teams-mcp
pip install -r requirements.txt
python server.py
```

**Documentation:** See [teams-mcp/README.md](./teams-mcp/README.md)

---

## Future Tools

As workflow needs evolve, additional tools will be added:
- Content extractors (CMS, databases)
- Content transformers (format converters)
- Content validators (schema checkers)
- Deployment utilities (CDN sync, cache invalidation)

---

## Contributing Tools

When adding new tools:
1. Create subdirectory under `tools/`
2. Include README.md with usage instructions
3. Add dependencies file (requirements.txt, package.json, etc.)
4. Update this index
