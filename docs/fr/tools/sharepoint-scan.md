# Processus d'analyse SharePoint

Ce guide explique comment utiliser l'outil `tools/sharepoint` pour analyser des dossiers/fichiers SharePoint et exporter les resultats en JSON.

## 1) Installation

```bash
cd tools/sharepoint
pip install -r requirements.txt
```

## 2) Analyse de base d'un dossier

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>"
```

## 3) Exporter en JSON

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" -o analyses/folder-scan.json
```

## 4) Analyse recursive

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" --recursive --max-depth 10 -o analyses/folder-tree.json
```

## 5) Analyse de contenu de fichier (PPT/Excel)

### Analyser un lien de fichier unique

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-file-link>" --analyze-file -o analyses/file-analysis.json
```

### Filtrer des fichiers du dossier puis analyser

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" --filter "1,4,5" --download-analyze -o analyses/filtered-analysis.json
```

## 6) Commandes utilitaires

### Lister les sites SharePoint accessibles

```bash
python scripts/scan-sharepoint-graph.py --list-sites
```

### Nettoyer le cache de session

```bash
python scripts/scan-sharepoint-graph.py --cleanup-session
```

## 7) Notes d'utilisation

- Le premier lancement ouvre la connexion Microsoft.
- Commencez par une analyse limitee (non recursive) pour verifier les droits.
- Activez ensuite la recursion et l'analyse complete.
- Conservez les sorties JSON dans `tools/sharepoint/analyses/`.
