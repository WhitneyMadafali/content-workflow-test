# Flux de Contenu

**Objectif :** Cadre de gestion du cycle de vie du contenu, flux de travail et outils pour le système content-as-code d'Omnivoltaic.

**Périmètre :** Genèse → Semence → Formes → Applications → Diffusion

---

## Aperçu

Ce dépôt contient les cadres conceptuels, la documentation des processus et les outils d'automatisation qui soutiennent le cycle de vie du contenu de bout en bout d'Omnivoltaic.

### Étapes du cycle de vie du contenu

1. **Genèse (Genesis)** — Capture des sources (chaotique, non structuré)
2. **Semence (Seed)** — Documentation structurée (Markdown, schémas)
3. **Formes (Forms)** — Intentions et designs de contenu (présentations, sites)
4. **Applications (Apps)** — Implémentations de composants (React/JSX)
5. **Diffusion (Serving)** — Livraison publiée (domaines, CDN)

---

## Sections de documentation

### [Cadres](frameworks.md)
Modèles conceptuels et fondements philosophiques du content-as-code.

### [Flux de travail](workflows.md)
Documentation des processus opérationnels pour chaque étape du cycle de vie.

### [Intentions de livraison](delivery-intents.md)
Stratégie de domaine et architecture de livraison de contenu.

---

## Outils

Les outils d'automatisation soutenant le cycle de vie du contenu sont situés dans le répertoire `/tools` :

- **Analyseur de contenu SharePoint** — Extraction de contenu depuis SharePoint pour le traitement en phase Genèse
- La documentation d'utilisation des outils est couverte dans la section [Flux de travail](workflows.md)

---

## Dépôts associés

- **oves-decks** — Formulaires de présentation et feuilles de style
- **oves-sites** — Intentions de conception de sites Web et architecture
- **dirac-uxi** — Implémentations d'applications de contenu

---

Pour la documentation détaillée, référez-vous à [docs.omnivoltaic.com/content-workflow](https://docs.omnivoltaic.com/content-workflow)
