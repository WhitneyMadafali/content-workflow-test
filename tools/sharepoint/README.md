# OVES SharePoint Tools

Workspace-wide tooling for SharePoint file and folder analysis using Microsoft Graph API.

## Features

- ✅ **Secure Authentication**: Microsoft OAuth 2.0 with cached tokens
- ✅ **Folder Scanning**: List all files and folders from SharePoint links
- ✅ **File Analysis**: Extract content from PowerPoint, PDFs, and more
- ✅ **Session Management**: Downloaded files cached for re-analysis
- ✅ **Workspace-Wide**: Single session folder shared across all repos

## Installation

```bash
cd d:/github/oves-sharepoint-tools
pip install -r requirements.txt
```

## Usage

### Scan a SharePoint Folder

```bash
python scripts/scan-sharepoint-graph.py "https://oves159.sharepoint.com/:f:/s/..."
```

### Analyze a PowerPoint File

```bash
python scripts/scan-sharepoint-graph.py "https://oves159.sharepoint.com/:p:/s/..." --analyze-file
```

### List Your SharePoint Sites

```bash
python scripts/scan-sharepoint-graph.py --list-sites
```

### Save Analysis to JSON

```bash
python scripts/scan-sharepoint-graph.py <URL> -o analyses/output.json
```

### Clean Up Session Files

```bash
python scripts/scan-sharepoint-graph.py --cleanup-session
```

## Architecture

### Directory Structure

```
oves-sharepoint-tools/
├── scripts/
│   └── scan-sharepoint-graph.py      # Main scanner tool
├── analyses/                         # Analysis outputs (JSON)
├── .sharepoint_token_cache.json     # Auth token (cached)
└── requirements.txt

d:/github/.sharepoint-session/        # Workspace-wide temp files
```

### Session Management

- **Downloaded files** → Cached in `d:/github/.sharepoint-session/`
- **Shared across repos** → Available from any project
- **Manual cleanup** → Explicit `--cleanup-session` command required
- **Re-analysis** → No re-download if file already cached

## Authentication

First run opens a browser for Microsoft 365 login. Token is cached for future use.

**Required permissions:**
- `Files.Read.All` - Read SharePoint files
- `Sites.Read.All` - Access SharePoint sites
- `User.Read` - Basic profile info

## Examples

### Extract PowerPoint Content

```bash
cd d:/github/oves-sharepoint-tools/scripts
python scan-sharepoint-graph.py \
  "https://oves159.sharepoint.com/:p:/s/OVES/..." \
  --analyze-file \
  -o ../analyses/presentation-analysis.json
```

**Output includes:**
- Total slides, images, shapes
- Text content per slide
- Image formats and counts
- Slide layouts

### Use from Other Repos

```bash
# From dirac-uxi, oves-decks, etc.
cd d:/github/dirac-uxi
python ../oves-sharepoint-tools/scripts/scan-sharepoint-graph.py <URL>
```

## Supported File Types

- ✅ PowerPoint (.pptx) - Full content extraction
- 🚧 Excel (.xlsx) - Coming soon
- 🚧 PDF (.pdf) - Coming soon
- 🚧 Word (.docx) - Coming soon

## Notes

- Session files persist until explicit cleanup
- Token cache is workspace-scoped
- All analysis outputs saved to `analyses/` folder
- Works with any SharePoint sharing link you have access to
