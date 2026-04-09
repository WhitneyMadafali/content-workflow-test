# Guide MCP Teams

Cette page explique comment lancer le serveur MCP `tools/teams-mcp` pour acceder aux canaux et chats Teams.

## 1) Demarrage depuis zero (sans depot local)

### Prerequis

- `git` installe
- `python3` et `pip` installes
- compte Microsoft 365 avec acces Teams

### Cloner le depot

```bash
git clone https://github.com/ovesorg/content-workflow.git
cd content-workflow
```

## 2) Installation

```bash
cd tools/teams-mcp
pip install -r requirements.txt
```

## 3) Demarrer le serveur MCP

```bash
BROWSER=google-chrome python server.py
```

Au premier lancement, une authentification Microsoft interactive est requise.

## 4) Connecter dans votre client MCP

Configurez la commande serveur MCP comme suit :

```bash
python tools/teams-mcp/server.py
```

Pour forcer Chrome :

```bash
BROWSER=google-chrome python tools/teams-mcp/server.py
```

## 5) Outils MCP exposes

- `list_joined_teams` : lister les Teams accessibles
- `list_team_channels` : lister les canaux d'une Team
- `list_channel_messages` : lire les messages de canal (avec reponses en option)
- `list_chats` : lister les chats personnels/groupe/reunion
- `list_chat_messages` : lire les messages d'un chat
- `search_chat_messages` : recherche par mot-cle sur plusieurs chats

## 6) Cas d'usage

- Recherche ciblee par Team/canal
- Recherche de discussions par mot-cle libre
- Export JSON structure pour des workflows en aval
