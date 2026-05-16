# deploy

Tout ce qu'il faut pour faire tourner la stack sur un Hetzner CX22.

## Architecture

```
                 ┌──────────────────────────────┐
                 │  https://n8n.<domain>        │
                 │  https://skills.<domain>     │
                 └─────────────┬────────────────┘
                               │ 80/443
                       ┌───────▼────────┐
                       │  Caddy (TLS)   │
                       └───────┬────────┘
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       ┌─────────┐       ┌───────────┐      ┌──────────────────┐
       │  n8n    │  ──▶  │ Postgres  │      │  skills-service  │
       │ :5678   │       │  :5432    │      │  :8000           │
       └────┬────┘       └───────────┘      └──────────────────┘
            │ HTTP                                  ▲
            └───────────  http://skills-service:8000┘
                 (via Docker network "factory")
```

Tout est dans `docker-compose.yml`.

## Prérequis

- **VPS Hetzner CX22** (2 vCPU, 4 GB RAM, 40 GB SSD) — ~5€/mois
- **Ubuntu 24.04 LTS**
- **2 DNS A records** pointant vers l'IP du VPS :
  - `n8n.<ton-domaine>` (par ex. `n8n.themoodex.cards`)
  - `skills.<ton-domaine>` (par ex. `skills.themoodex.cards`)
- Une clé SSH publique chargée sur le VPS

## Setup en 10 commandes

```bash
# 1. (Sur ton poste) Cloner le repo
git clone https://github.com/aymericdc-64/media-factory.git
cd media-factory

# 2. Provisioner le VPS (installe Docker, UFW, fail2ban)
chmod +x deploy/scripts/*.sh
./deploy/scripts/setup-vps.sh root@<your-hetzner-ip>

# 3. Préparer .env
cp deploy/.env.example deploy/.env
# Édite deploy/.env et remplis :
#   - N8N_HOST / SKILLS_HOST (DNS pointés vers le VPS)
#   - N8N_ENCRYPTION_KEY (openssl rand -hex 32)
#   - POSTGRES_PASSWORD (openssl rand -hex 24)
#   - SKILLS_AUTH_SECRET (openssl rand -hex 32)
#   - NOTION_API_KEY, ANTHROPIC_API_KEY, ...

# 4. Pousser le repo + démarrer la stack
./deploy/scripts/push-to-vps.sh root@<your-hetzner-ip>

# 5. Vérifier que tout tourne
ssh root@<your-hetzner-ip> 'cd /opt/media-factory/deploy && docker compose ps'

# 6. Ouvrir n8n
# https://n8n.<ton-domaine>
# → créer le compte admin (1ère visite)

# 7. Importer les 4 workflows (cf. n8n-workflows/README.md)

# 8. Créer les 2 credentials n8n (cf. n8n-workflows/README.md)

# 9. Configurer le webhook Telegram
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://n8n.<ton-domaine>/webhook/telegram-callback"

# 10. Tester
curl -H "Authorization: Bearer $SKILLS_AUTH_SECRET" https://skills.<ton-domaine>/health
# → {"status":"ok","version":"0.1.0"}
```

## Sécurité

- **UFW activé** : seuls 22/80/443 sont ouverts.
- **fail2ban** protège ssh.
- **unattended-upgrades** applique les patches sécurité auto.
- **Aucun secret en dur** : tout dans `deploy/.env` (gitignored).
- **Skills Service** est joignable uniquement depuis :
  - le réseau Docker interne (depuis n8n)
  - l'extérieur via Caddy mais protégé par bearer token

## Backup

```bash
ssh root@<ip> '/opt/media-factory/deploy/scripts/backup-n8n.sh'
# → /opt/factory-backups/factory-backup-YYYYMMDD-HHMMSS.tar.gz
scp root@<ip>:/opt/factory-backups/factory-backup-*.tar.gz ~/backups/
```

À mettre en cron sur le VPS (ex: `0 4 * * * /opt/media-factory/deploy/scripts/backup-n8n.sh`).

## Logs

```bash
ssh root@<ip> 'cd /opt/media-factory/deploy && docker compose logs -f --tail=100 skills-service'
ssh root@<ip> 'cd /opt/media-factory/deploy && docker compose logs -f --tail=100 n8n'
```

Les logs sont en JSON structuré côté skills-service — pipable dans `jq`.

## Mise à jour du code

```bash
# Sur le poste local
git pull
./deploy/scripts/push-to-vps.sh root@<your-hetzner-ip>
# rebuild + restart automatique
```

## Troubleshooting

| Symptôme | Cause probable | Fix |
|---|---|---|
| `502 Bad Gateway` sur n8n.<domain> | n8n pas encore démarré | `docker compose logs n8n` |
| `Invalid bearer token` côté skills | `SKILLS_AUTH_SECRET` désynchronisé entre n8n env et skills env | Vérifier qu'il est identique dans `.env` |
| `Notion 401` dans skills-service | Clé NOTION_API_KEY non partagée avec la page racine | UI Notion → Settings → Connections → Add page |
| Workflow daily-run échoue à `read_content_catalog` | data_source_id n'existe pas ou non partagé | Vérifier dans `.env` les UUID, puis dans Notion partager la racine avec l'intégration |
| Telegram callback 404 | Webhook URL non enregistrée auprès du bot | Re-lancer la commande `setWebhook` de l'étape 9 |
