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

## 8) Cibler une equipe, un canal, ou un texte de chat

### Filtrer par nom d'equipe

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES All" -o analyses/team-filtered.json
```

### Filtrer par nom de canal dans une equipe

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES All" --channel-name "General" -o analyses/channel-filtered.json
```

### Rechercher des messages contenant un texte specifique

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "Equipe Produit" --channel-name "General" --include-channel-messages --message-contains "invoice approval" -o analyses/message-search.json
```

### Comportement de correspondance (casse/espace/approximation)

- La recherche est insensible a la casse.
- Les differences d'espaces et de ponctuation sont tolerees.
- Les correspondances approximatives (petites fautes) sont prises en charge.

## 9) Liens Microsoft Forms dans un canal

Lorsque des liens Forms sont publies dans un canal, ne conserver que les messages parents dont le corps contient `forms.office.com` ou `forms.microsoft.com` :

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py \
  --team-name "OVES All" \
  --channel-name "General" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 100 \
  --reply-limit 30 \
  -o analyses/channel-forms-posts.json
```

Guide complet : [Liens Forms dans Teams](forms-mcp.md).
