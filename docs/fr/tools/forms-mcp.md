# MCP Forms (retours Forms dans les canaux Teams)

Cette page explique comment analyser et exporter des **messages de canal** Teams au format JSON lorsque des **liens ou consignes Microsoft Forms sont publies dans un canal**.

!!! note "Important"

    Ce depot ne fournit **pas** de serveur MCP autonome nomme `forms-mcp`. Un point d'entree est decrit dans `tools/forms-mcp/README.md`. Les retours presents dans le canal sont accessibles via **l'analyse Teams** (CLI) ou **MCP Teams**, qui lisent les **messages de canal**.  
    Ce flux **ne** recupere **pas** la base complete des reponses Forms ; pour les donnees brutes, utilisez l'export Forms, Power Automate ou les API Graph Forms (selon la politique du tenant).

## 1) Cas d'usage

- Liens Forms, consignes ou discussions dans un canal Teams dedie
- Exporter les publications dont le corps contient une URL Microsoft Forms (optionnellement avec fils de reponses)

## 2) Installation

Identique a [Analyse Teams](teams-scan.md), depuis `tools/teams` (environnement virtuel recommande si `pip` global est bloque) :

```bash
cd tools/teams
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3) Recommande : ne garder que les messages contenant un lien Forms

Utiliser `scan-teams-graph.py` avec `--forms-links-only` pour ne conserver que les messages parents dont le corps contient `forms.office.com` ou `forms.microsoft.com` (combinable avec `--message-contains`; les deux filtres s'appliquent au message parent) :

```bash
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "Nom de l'equipe" \
  --channel-name "Nom du canal" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 100 \
  --reply-limit 30 \
  -o analyses/channel-forms-posts.json
```

Test sur petite portee :

```bash
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "Nom de l'equipe" \
  --channel-name "Nom du canal" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 20 \
  --reply-limit 10 \
  -o analyses/channel-forms-posts-sample.json
```

## 4) Meme canal depuis un client MCP

1. Demarrer `tools/teams-mcp` comme dans [MCP Teams](teams-mcp.md) et se connecter.
2. Utiliser `list_joined_teams` et `list_team_channels` pour obtenir `team_id` et `channel_id`.
3. Appeler `list_channel_messages`, puis filtrer `body_preview` sur `forms.office.com` ou `forms.microsoft.com`.

## 5) Limites

| Capacite | Detail |
|----------|--------|
| Messages et reponses de canal | Export JSON (analyse Teams) ou apercus (MCP) |
| Base de reponses Forms complete | **Hors perimetre** de ce flux |

## 6) Voir aussi

- [Analyse Teams](teams-scan.md)
- [MCP Teams](teams-mcp.md)
