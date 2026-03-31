# Processus d'analyse Teams

Ce guide explique comment utiliser l'outil `tools/teams` pour exporter la structure Teams, les messages/reponses de canaux et, si besoin, les fichiers en JSON.

## 1) Installation

```bash
cd tools/teams
pip install -r requirements.txt
```

## 2) Lister les equipes rejointes

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --list-teams
```

## 3) Analyser uniquement la structure Teams + canaux

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py -o analyses/teams-structure.json
```

## 4) Inclure messages et fils de reponses

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --message-limit 50 --reply-limit 50 -o analyses/teams-messages.json
```

## 5) Ignorer les reponses

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --skip-channel-replies -o analyses/teams-no-replies.json
```

## 6) Telecharger les fichiers de canaux

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --download-channel-files --max-channel-files 25 -o analyses/teams-full-scan.json
```

## 7) Notes d'utilisation

- Le premier lancement demande une authentification Microsoft interactive.
- Utilisez Chrome avec `BROWSER=google-chrome`.
- Commencez avec des limites basses pour valider les permissions.
- Conservez les sorties JSON dans `tools/teams/analyses/`.
