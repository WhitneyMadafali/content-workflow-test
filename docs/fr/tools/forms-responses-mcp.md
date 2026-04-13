# MCP reponses Forms (`tools/forms-mcp`)

Utiliser les **API Microsoft Forms** depuis **Cursor** (ou un autre client MCP) pour lire et resumer les **reponses soumises**. Les donnees viennent de **Forms**, pas du corps des messages Teams.

## Quand utiliser cette page

- Vous avez l'URL d'un formulaire (`forms.office.com` ou equivalent) et vous voulez des **resumes de reponses** ou des synthese par question dans l'editeur.
- Vous avez besoin des **soumissions cote Forms**, pas de savoir « qui a poste le lien dans un canal ».

## Procedure pas a pas

Supposons le **depot clone** et **Python 3** installe. Remplacez les chemins ci-dessous par des **chemins absolus** sur votre machine.

### A. Vous avez l'URL du formulaire : resumer dans Cursor (parcours courant)

**1) Installer les dependances du MCP Forms (une fois par machine)**

Depuis la racine du depot :

```bash
cd tools/forms-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Notez le chemin complet vers `tools/forms-mcp` pour l'etape suivante.

**2) Enregistrer le serveur MCP dans Cursor (une fois par machine)**

Ouvrez **Cursor → Settings → MCP** et ajoutez un serveur :

- **Command :** chemin vers `.venv/bin/python` de l'etape 1 (chemin complet).
- **Args :** chemin complet vers `server.py` dans le meme dossier.
- **Environnement :** definir `BROWSER` (ex. `google-chrome`) pour que la connexion par navigateur s'ouvre.

Enregistrez, puis **redemarrez Cursor** ou rechargez MCP si necessaire. Exemple JSON (adaptez les chemins) :

```json
{
  "mcpServers": {
    "forms-responses": {
      "command": "/votre/chemin/content-workflow/tools/forms-mcp/.venv/bin/python",
      "args": ["/votre/chemin/content-workflow/tools/forms-mcp/server.py"],
      "env": {
        "BROWSER": "google-chrome"
      }
    }
  }
}
```

**3) Se connecter a Microsoft Forms (en general une fois par machine)**

Dans un terminal :

```bash
cd /votre/chemin/content-workflow/tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py auth-test
```

Terminez la connexion dans le navigateur. En cas de succes, **`.forms_token_cache.json`** est cree a cote de `server.py` (fichier **hors** git — ne pas le committer). Les executions suivantes reutilisent ce cache jusqu'a expiration ou suppression.

**4) Demander un resume dans le chat**

1. Verifiez que le serveur MCP Forms est active si l'interface propose un interrupteur.
2. Demandez a l'assistant d'appeler **`summarize_form_responses`** avec **`form_url`** (ex. `https://forms.office.com/r/...`) ou **`form_id`** si vous le connaissez.
3. Precisez un **resume en prose**, pas du JSON brut. La regle Cursor du depot oriente vers un texte type **`executive_summary`** en premier.

**5) Si la connexion ou les appels API echouent**

- Verifiez les permissions deleguees **Microsoft Forms** du tenant ; definissez **`FORMS_CLIENT_ID`** vers une application Entra avec les bons droits si besoin. Voir **Required permissions** et le tableau de depannage dans [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md).

### B. Sans Cursor : test rapide en CLI

Meme installation que **§A**. Depuis `tools/forms-mcp` (URL reelle du formulaire) :

```bash
BROWSER=google-chrome .venv/bin/python server.py summarize-test --brief --form-url "https://forms.office.com/r/..." --top 25
```

`--brief` affiche d'abord **`executive_summary`**, puis de courtes lignes thematiques par question. Sans `--brief`, JSON complet avec **`respondent_texts`**.

### C. Option : le lien du formulaire n'apparait que dans un canal Teams

Deuxieme environnement necessaire : venv **`tools/teams`** et connexion **Microsoft Graph** (jeton distinct de Forms). Schema :

1. Analyser le canal avec `tools/teams` et exporter un JSON contenant des URL Forms (voir [Liens Forms dans Teams](forms-mcp.md)).
2. Depuis `tools/forms-mcp`, lancer `summarize_from_teams_export.py` sur ce JSON, ou utiliser `scan_channel_forms_summary.sh`.

Commandes completes, script tout-en-un et **`--pick N`** si plusieurs formulaires : section **Teams channel → Forms summary** dans [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md).

## Pour aller plus loin

Permissions, outils exposes, depannage :

- Sur GitHub : [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md)
- Apres clonage, chemin local : `tools/forms-mcp/README.md`

## Par rapport aux « liens Forms dans Teams »

| | **MCP reponses Forms** (cette page) | **[Liens Forms dans Teams](forms-mcp.md)** |
| --- | --- | --- |
| Source des donnees | API Forms (soumissions) | Messages de canal Teams (publications/reponses avec URL) |
| Point d'entree typique | `tools/forms-mcp/server.py` | scripts d'analyse `tools/teams`, `tools/teams-mcp` |
| Usage typique | Resumer les vraies reponses | Exporter en JSON les messages contenant des URL Forms |

## Voir aussi

- [Liens Forms dans Teams](forms-mcp.md)
- [MCP Teams](teams-mcp.md)
