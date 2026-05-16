# factory-skills-service

Mini-service Python / FastAPI qui expose **30 skills atomiques** aux agents Claude via le protocole **Tool Use** d'Anthropic. n8n appelle l'agent (Anthropic API), l'agent décide d'invoquer un skill, l'appel arrive ici, le service exécute, retourne, l'agent continue.

## Aperçu

| Agent | Routes | Skills |
|---|---|---|
| 🧠 Strategist | `/strategist/*` | `read_content_catalog`, `read_performance_tracker`, `read_content_themes`, `read_bible_creative`, `write_brief_to_pipeline` |
| 🛠️ Producer | `/producer/*` | `generate_image`, `compose_card`, `animate_video`, `get_audio`, `compose_final_video`, `upload_asset`, `update_pipeline_status` |
| 📊 Scorer | `/scorer/*` | `read_production_pipeline`, `score_video`, `write_caption_score` |
| 📤 Publisher | `/publisher/*` | `read_pipeline_approved`, `read_channels_active`, `post_instagram`, `post_tiktok`, `post_youtube_shorts`, `create_performance_row` |
| 📈 Analyst | `/analyst/*` | `fetch_metrics`, `compute_engagement_rate`, `compute_verdict`, `write_analyst_notes`, `update_performance`, `read_snapshot` |

## Run local

```bash
# 1. Install
cd skills-service
python -m venv .venv && source .venv/bin/activate
pip install uv
uv pip install -e ".[dev]"

# 2. Configure
cp .env.example .env
# remplis les clés réelles (Anthropic, Notion, fal.ai, ...)

# 3. Run
uvicorn src.main:app --reload --port 8000

# 4. Tester
curl http://localhost:8000/health
curl http://localhost:8000/tools | jq '.strategist[0]'
```

## Auth

Toutes les routes `/strategist`, `/producer`, `/scorer`, `/publisher`, `/analyst` exigent :

```
Authorization: Bearer $SKILLS_AUTH_SECRET
```

`GET /health` et `GET /tools` sont **publics** (utilisés par les health checks Docker et par les agents pour découvrir les schemas).

## Layout

```
skills-service/
├── pyproject.toml
├── Dockerfile
├── .env.example
├── src/
│   ├── main.py                 # FastAPI app + lifespan
│   ├── config.py               # Settings (pydantic-settings)
│   ├── auth.py                 # Bearer middleware
│   ├── logging_config.py       # JSON structured logs
│   ├── clients/                # 1 client par API externe
│   │   ├── notion.py
│   │   ├── anthropic_client.py
│   │   ├── falai.py
│   │   ├── creatomate.py
│   │   ├── epidemic.py
│   │   ├── r2.py
│   │   ├── social_platforms.py
│   │   └── telegram.py
│   ├── schemas/                # Pydantic in/out par agent
│   ├── skills/                 # Logique métier par agent
│   ├── routers/                # FastAPI APIRouter par agent
│   └── tool_definitions/       # JSON Schemas Anthropic Tool Use
└── tests/
    └── test_basic.py
```

## Standards

- **Idempotence** : les writes Notion utilisent `Prod ID` / `Post ID` (unique_id) — `update_page` est rejouable sans dup.
- **Retry** : non géré côté skill — c'est n8n qui retry (cf. spec n8n).
- **Erreurs** : `400` (validation Pydantic), `401/403` (auth), `5xx` propagé pour retry n8n.
- **Logs** : JSON structuré sur stdout — capté par `docker logs` puis n8n natif.

## Test

```bash
pytest -v
```

Les tests utilisent `TestClient` (synchrone) avec auth stubbée — ils valident que :
- `/health` et `/tools` sont publics
- les routes protégées exigent un bearer valide
- les schemas Pydantic acceptent les payloads attendus

## Lien avec le HQ Notion

Les `data_source_id` exacts sont câblés dans `.env` (variables `NOTION_DS_*`). Toute évolution de schéma Notion doit être répercutée :
1. dans le schéma Notion (UI)
2. dans `src/skills/<agent>.py` (champs lus/écrits)
3. dans `src/schemas/<agent>.py` (Pydantic)
4. dans `src/tool_definitions/<agent>.json` (Anthropic enums)

## Roadmap

- [ ] Frame-extractor ffmpeg pour vrai scoring vision du premier frame
- [ ] Endpoints `/threads`, `/x`, `/pinterest`, `/linkedin` (publisher)
- [ ] Exposition MCP `/mcp/list_tools` pour Claude Desktop
- [ ] OpenTelemetry → Grafana Cloud
