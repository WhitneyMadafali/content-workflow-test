# SharePoint Scan Process

This guide explains how to use the `tools/sharepoint` scanner to scan SharePoint folders/files and export results to JSON.

## 1) Install

```bash
cd tools/sharepoint
pip install -r requirements.txt
```

## 2) Basic Folder Scan

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>"
```

## 3) Export Scan to JSON

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" -o analyses/folder-scan.json
```

## 4) Recursive Folder Scan

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" --recursive --max-depth 10 -o analyses/folder-tree.json
```

## 5) File Content Analysis (PPT/Excel)

### Analyze a single file link

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-file-link>" --analyze-file -o analyses/file-analysis.json
```

### Filter files from folder listing and analyze

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" --filter "1,4,5" --download-analyze -o analyses/filtered-analysis.json
```

## 6) Utility Commands

### List accessible SharePoint sites

```bash
python scripts/scan-sharepoint-graph.py --list-sites
```

### Clean session cache

```bash
python scripts/scan-sharepoint-graph.py --cleanup-session
```

## 7) Operator Notes

- First run opens Microsoft login; complete consent/authorization.
- Start with a small, non-recursive scan to validate access.
- Then enable recursion and analysis to scale up safely.
- Keep JSON outputs under `tools/sharepoint/analyses/` for consistency.
