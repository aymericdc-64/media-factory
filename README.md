# media-factory

Stack technique du média social autonome **TheMoodex** (et template réutilisable pour tout média short-form).

Le pilotage et la mémoire stratégique vivent dans **Notion** (le HQ). Ce repo contient **la machine** : orchestration n8n + Skills Service Python + déploiement sur VPS OVH.

## Architecture en 30 secondes

```
┌──────────────────────────────────────────────────────────────────┐
│  Notion HQ  (Content Catalog, Production Pipeline, Performance,  │
│              Channels, Themes, Asset Templates, Prompts, ...)    │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ read / write
                              ▼
┌──────────────┐   tool_use   ┌──────────────────────────────────┐
│  Anthropic   │ ◀──────────▶ │  Skills Service (FastAPI Python) │
│  Claude API  │              │  • 30 skills atomiques            │
└──────────────┘              │  • clients Notion / fal.ai /      │
                              │    Creatomate / Epidemic / R2 /   │
                              │    IG / TT / YT                   │
                              └──────────────────────────────────┘
                                            ▲
                                            │ HTTP (bearer auth)
                                            ▼
                              ┌──────────────────────────────────┐
                              │  n8n  (orchestrateur visuel)     │
                              │  • daily-run    06h UTC          │
                              │  • approval-webhook (Telegram)   │
                              │  • publish-slots  12h / 18h UTC  │
                              │  • analyst-daily  23h UTC        │
                              └──────────────────────────────────┘
                                            ▲
                                            │
                              ┌──────────────────────────────────┐
                              │  OVH VPS Starter (Ubuntu 24.04)  │
                              │  caddy · n8n · postgres · skills │
                              └──────────────────────────────────┘
```

## Sous-dossiers

| Dossier | Rôle | Stack |
|---|---|---|
| [`skills-service/`](./skills-service) | Le cerveau atomique. Expose 30 skills aux agents Claude (Tool Use). | Python 3.12 · FastAPI · uvicorn |
| [`n8n-workflows/`](./n8n-workflows) | 4 workflows exportés en JSON, importables tels quels dans n8n. | n8n 1.x |
| [`deploy/`](./deploy) | docker-compose + Caddyfile + scripts pour provisionner un OVH VPS Starter (Ubuntu 24.04). | Docker · Caddy · PostgreSQL 16 |

## Mise en route (TL;DR)

```bash
# 1. Cloner
git clone https://github.com/aymericdc-64/media-factory.git
cd media-factory

# 2. Provisionner le VPS OVH (cf. deploy/README.md)
cd deploy
cp .env.example .env
# remplir les secrets (NOTION_API_KEY, ANTHROPIC_API_KEY, ...)
./scripts/setup-vps.sh ubuntu@<your-ovh-ip>

# 3. Importer les workflows n8n (cf. n8n-workflows/README.md)
# UI → Settings → Import from File → les 4 fichiers JSON

# 4. Vérifier que le skills-service répond
curl -H "Authorization: Bearer $SKILLS_AUTH_SECRET" https://skills.<domaine>/health
```

## Lien avec le HQ Notion

Les `data_source_id` exacts sont dans [`deploy/.env.example`](./deploy/.env.example). La spec complète des bases vit dans Notion :

- HQ : <https://www.notion.so/35ff03a55574815bbf5ce67ac379979d>
- Ops & Stack : <https://www.notion.so/35ff03a55574819b9ea2fb815d090649>
- Architecture n8n complète : <https://www.notion.so/35ff03a5557481eba61cd0c61d3e47a0>
- Spec Skills Service : <https://www.notion.so/35ff03a555748151b225c80dc7358e73>

## Règle de sécurité immuable

**Aucun secret en clair dans Notion.** Les credentials vivent uniquement dans :

- `deploy/.env` (jamais commité, voir `.gitignore`)
- n8n encrypted credentials
- Bitwarden (ou équivalent)

## Licence

Privé. Tous droits réservés Aymeric Delahaye-Conté.
