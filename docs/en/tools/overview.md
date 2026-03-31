# Tools Overview

Use this page to quickly decide whether to run the SharePoint scanner or the Teams scanner.

## Quick Decision

- If your source is a **SharePoint folder/file link**, use [SharePoint Scan](sharepoint-scan.md).
- If your source is **Teams teams/channels/messages/replies**, use [Teams Scan](teams-scan.md).
- If you need **files stored in Teams channels**, still use the Teams scanner with file download enabled.

## Decision Flow

```mermaid
flowchart TD
  A[Start] --> B{What is the source?}
  B -->|SharePoint link| C[Run SharePoint Scan]
  B -->|Teams team/channel| D[Run Teams Scan]
  C --> E[Export JSON]
  D --> F{Need messages and replies?}
  F -->|Yes| G[Enable --include-channel-messages]
  F -->|No| H[Structure-only scan]
  G --> I{Need channel files?}
  I -->|Yes| J[Enable --download-channel-files]
  I -->|No| K[Export messages/replies JSON only]
```

## Recommended Execution Order

1. Start with a small scope (low limits, single target).
2. Confirm permissions and output structure.
3. Scale up and save final outputs in `analyses/`.
