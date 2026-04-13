# MCP reponses Forms (`tools/forms-mcp`)

Utiliser les **API Microsoft Forms** depuis **Cursor** (ou un autre client MCP) pour lire et resumer les **reponses soumises**. Les donnees viennent de **Forms**, pas du corps des messages Teams.

## Quand utiliser cette page

- Vous avez l'URL d'un formulaire (`forms.office.com` ou equivalent) et vous voulez des **resumes de reponses** ou des synthese par question dans l'editeur.
- Vous avez besoin des **soumissions cote Forms**, pas de savoir « qui a poste le lien dans un canal ».

## Installation et configuration

Les etapes completes (venv, MCP Cursor, `summarize_form_responses`, connexion, droits) sont dans le depot :

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
