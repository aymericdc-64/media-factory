# Connectors & Webhooks — Reference

Cartographie complète des points d'entrée/sortie de la factory : qui appelle qui, quels payloads, quelles URLs publiques.

## Index

1. [Skills Service — 30 routes](#skills-service--30-routes)
2. [Webhook Telegram (n8n)](#webhook-telegram-n8n)
3. [Webhooks plateformes (futur)](#webhooks-plateformes-futur)
4. [APIs sortantes (depuis Skills Service)](#apis-sortantes-depuis-skills-service)
5. [Crons et déclencheurs](#crons-et-déclencheurs)

---

## Skills Service — 30 routes

Toutes les routes nécessitent `Authorization: Bearer $SKILLS_AUTH_SECRET`.
Base URL en prod : `https://skills.<domaine>`. Base URL interne (depuis n8n) : `http://skills-service:8000`.

### Routes méta (publiques)

| Méthode | Route | But |
|---|---|---|
| GET | `/health` | Health check (utilisé par Docker + Caddy) |
| GET | `/tools` | Retourne le JSON Schema Anthropic Tool Use de tous les skills (5 agents) |

### Strategist (5)

```bash
curl -X POST https://skills.<domain>/strategist/read_content_catalog \
  -H "Authorization: Bearer $SKILLS_AUTH_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"status":"À produire","min_days_since_publish":30,"limit":20}'

curl -X POST https://skills.<domain>/strategist/read_performance_tracker \
  -H "Authorization: Bearer $SKILLS_AUTH_SECRET" -d '{"window_days":90,"limit":50}'

curl -X POST https://skills.<domain>/strategist/read_content_themes \
  -H "Authorization: Bearer $SKILLS_AUTH_SECRET" -d '{"status":"Active"}'

curl -X POST https://skills.<domain>/strategist/read_bible_creative \
  -H "Authorization: Bearer $SKILLS_AUTH_SECRET" \
  -d '{"page_id":"35ff03a5-5574-8174-a913-cd036b2bca35"}'

curl -X POST https://skills.<domain>/strategist/write_brief_to_pipeline \
  -H "Authorization: Bearer $SKILLS_AUTH_SECRET" \
  -d '{"title":"Test","brief":"...","script":"..."}'
```

### Producer (7)

```bash
curl -X POST https://skills.<domain>/producer/generate_image -H "..." \
  -d '{"prompt":"Pokemon-style card hero portrait, 9:16","aspect_ratio":"9:16"}'

curl -X POST https://skills.<domain>/producer/compose_card -H "..." \
  -d '{"image_url":"https://...","title":"Le Burnout","hp":"60","energy_type":"Feu"}'

curl -X POST https://skills.<domain>/producer/animate_video -H "..." \
  -d '{"image_url":"https://...","prompt":"slight breathing motion","duration_seconds":5}'

curl -X POST https://skills.<domain>/producer/get_audio -H "..." \
  -d '{"mood":"Épique","max_duration_s":10}'

curl -X POST https://skills.<domain>/producer/compose_final_video -H "..." \
  -d '{"card_image_url":"https://...","animation_url":"https://...","audio_url":"https://..."}'

curl -X POST https://skills.<domain>/producer/upload_asset -H "..." \
  -d '{"source_url":"https://...","key":"videos/PROD-42.mp4"}'

curl -X POST https://skills.<domain>/producer/update_pipeline_status -H "..." \
  -d '{"page_id":"abc-def","status":"Produced","final_asset_url":"https://..."}'
```

### Scorer (3)

```bash
curl -X POST https://skills.<domain>/scorer/read_production_pipeline -H "..." \
  -d '{"status":"Produced","limit":10}'

curl -X POST https://skills.<domain>/scorer/score_video -H "..." \
  -d '{"page_id":"abc","final_asset_url":"https://...","brief":"..."}'

curl -X POST https://skills.<domain>/scorer/write_caption_score -H "..." \
  -d '{"page_id":"abc","score":8.4,"caption_fr":"...","caption_en":"...","hashtags":"#x #y"}'
```

### Publisher (6)

```bash
curl -X POST https://skills.<domain>/publisher/read_pipeline_approved -H "..." \
  -d '{"limit":20}'

curl -X POST https://skills.<domain>/publisher/read_channels_active -H "..." -d '{}'

curl -X POST https://skills.<domain>/publisher/post_instagram -H "..." \
  -d '{"page_id":"abc","video_url":"https://...","caption":"..."}'

curl -X POST https://skills.<domain>/publisher/post_tiktok -H "..." \
  -d '{"page_id":"abc","video_url":"https://...","caption":"..."}'

curl -X POST https://skills.<domain>/publisher/post_youtube_shorts -H "..." \
  -d '{"page_id":"abc","video_url":"https://...","caption":"...","title":"..."}'

curl -X POST https://skills.<domain>/publisher/create_performance_row -H "..." \
  -d '{"pipeline_page_id":"abc","title":"...","platform":"Instagram","post_id":"...","post_url":"https://...","publish_date":"2026-05-15T12:00:00Z"}'
```

### Analyst (6)

```bash
curl -X POST https://skills.<domain>/analyst/fetch_metrics -H "..." \
  -d '{"platform":"Instagram","post_id":"123456789"}'

curl -X POST https://skills.<domain>/analyst/compute_engagement_rate -H "..." \
  -d '{"views":10000,"likes":850,"comments":42,"shares":67,"saves":120}'

curl -X POST https://skills.<domain>/analyst/compute_verdict -H "..." \
  -d '{"views":12000,"engagement_rate":0.09,"benchmarks":{"views":{"p25":500,"p50":2000,"p75":10000,"p90":50000},"er":{}}}'

curl -X POST https://skills.<domain>/analyst/write_analyst_notes -H "..." \
  -d '{"metrics":{"views":12000,"likes":850},"verdict":"Solid","context":"D+1 IG"}'

curl -X POST https://skills.<domain>/analyst/update_performance -H "..." \
  -d '{"performance_page_id":"abc","views":12000,...,"verdict":"Solid","notes":"..."}'

curl -X POST https://skills.<domain>/analyst/read_snapshot -H "..." \
  -d '{"snapshot":"D+1"}'
```

---

## Webhook Telegram (n8n)

### URL publique

```
POST https://n8n.<domain>/webhook/telegram-callback
```

(version test pour debug : `/webhook-test/telegram-callback`)

### Enregistrement auprès de Telegram

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://n8n.<domain>/webhook/telegram-callback" \
  -d "allowed_updates=[\"callback_query\"]"

# Vérification :
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

### Payload reçu (exemple)

```json
{
  "update_id": 123456,
  "callback_query": {
    "id": "987654321",
    "from": {"id": 12345, "first_name": "Aymeric", "is_bot": false},
    "message": {
      "message_id": 42,
      "chat": {"id": 67890, "type": "private"},
      "date": 1747315200,
      "video": {"file_id": "AgADxxx", "duration": 9, "width": 1080, "height": 1920},
      "caption": "🎬 PROD-12 · score 8.4/10"
    },
    "chat_instance": "...",
    "data": "approve_PROD-12"
  }
}
```

Le workflow `approval-webhook.json` parse `callback_query.data`, retrouve la row Notion correspondant à `PROD-12`, met à jour `Status=Approved` + calcule le `Scheduled Publish`, et ack à Telegram.

---

## Webhooks plateformes (futur)

Les plateformes natives proposent des webhooks pour notifier en temps réel des événements (likes, comments, follower count). À activer en P2 quand on aura > 10k followers.

| Plateforme | URL webhook | Doc |
|---|---|---|
| Instagram Graph | `https://n8n.<domain>/webhook/ig-event` | [Meta webhooks](https://developers.facebook.com/docs/graph-api/webhooks) |
| TikTok | `https://n8n.<domain>/webhook/tt-event` | [TikTok webhooks](https://developers.tiktok.com/doc/webhooks-overview) |
| YouTube (PubSubHubbub) | `https://n8n.<domain>/webhook/yt-event` | [YT PubSubHubbub](https://developers.google.com/youtube/v3/guides/push_notifications) |

Pour l'instant on **poll** les métriques à 23h UTC dans `analyst-daily.json` — moins temps-réel mais beaucoup plus simple. Re-évaluer à 10k followers.

---

## APIs sortantes (depuis Skills Service)

Liste exhaustive de ce que le skills-service appelle vers l'extérieur. Chaque ligne = un point de friction potentiel à monitorer.

| Service | Endpoint | Méthode | Auth | Skill qui l'appelle |
|---|---|---|---|---|
| Notion | `https://api.notion.com/v1/data_sources/<id>/query` | POST | Bearer | tous les `read_*` |
| Notion | `https://api.notion.com/v1/pages` | POST | Bearer | `write_brief_to_pipeline`, `create_performance_row` |
| Notion | `https://api.notion.com/v1/pages/<id>` | PATCH | Bearer | `update_pipeline_status`, `update_performance`, `write_caption_score` |
| Notion | `https://api.notion.com/v1/blocks/<id>/children` | GET | Bearer | `read_bible_creative` |
| Anthropic | `https://api.anthropic.com/v1/messages` | POST | x-api-key | `score_video`, `write_analyst_notes` |
| fal.ai | `https://queue.fal.run/<model>` | POST puis GET status | Key | `generate_image`, `animate_video` |
| Creatomate | `https://api.creatomate.com/v1/renders` | POST puis GET status | Bearer | `compose_card`, `compose_final_video` |
| Epidemic Sound | `https://api.epidemicsound.com/v1/tracks/search` | GET | Bearer | `get_audio` |
| Cloudflare R2 | `https://<account>.r2.cloudflarestorage.com/<bucket>/<key>` | PUT (boto3 S3) | SigV4 | `upload_asset` |
| Instagram Graph | `https://graph.facebook.com/v21.0/<ig_id>/media` + `media_publish` | POST | Access Token | `post_instagram`, `fetch_instagram_metrics` |
| TikTok | `https://open.tiktokapis.com/v2/post/publish/video/init/` | POST | Bearer | `post_tiktok`, `fetch_tiktok_metrics` |
| YouTube Data v3 | `https://www.googleapis.com/upload/youtube/v3/videos` | POST | OAuth Bearer | `post_youtube_shorts`, `fetch_youtube_metrics` |
| Telegram | `https://api.telegram.org/bot<token>/sendVideo` | POST | URL token | n8n (pas le skills-service) |

---

## Crons et déclencheurs

Tous en **UTC**. Ils tournent côté n8n (cron triggers).

| Workflow | Cron | Trigger | Action |
|---|---|---|---|
| Daily Run | `0 6 * * *` | 06:00 UTC tous les jours | Génère 5 vidéos, score, envoie top 3 sur Telegram |
| Approval Webhook | — | Reçu sur clic Telegram | Approve / Reject la row |
| Publish Slots | `0 12,18 * * *` | 12:00 et 18:00 UTC | Publie sur les channels actifs |
| Analyst Daily | `0 23 * * *` | 23:00 UTC tous les jours | Fetch métriques D+1/D+7/D+30 |

### Setup BotFather (résumé)

```
/newbot
TheMoodexBot
themoodex_factory_bot

→ Telegram te renvoie le BOT_TOKEN — à coller dans deploy/.env (TELEGRAM_BOT_TOKEN)
```

Puis dans Telegram, démarrer une conversation avec le bot et envoyer `/start`. Récupérer `TELEGRAM_CHAT_ID` :

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates" | jq '.result[0].message.chat.id'
```

---

## Smoke tests post-déploiement

```bash
# 1. Health
curl https://skills.<domain>/health
# → {"status":"ok","version":"0.1.0"}

# 2. Tools (public)
curl https://skills.<domain>/tools | jq 'keys'
# → ["analyst","producer","publisher","scorer","strategist"]

# 3. Auth qui marche
curl -H "Authorization: Bearer $SKILLS_AUTH_SECRET" \
     -H "Content-Type: application/json" \
     -X POST https://skills.<domain>/strategist/read_content_catalog \
     -d '{"status":"À produire","limit":3}'
# → {"concepts":[],"total":0} (si pas encore de concepts dans Notion)

# 4. Telegram dry-run
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
     -d "chat_id=$TELEGRAM_CHAT_ID" \
     -d "text=Factory online ✓"

# 5. n8n alive
curl -I https://n8n.<domain>/
# → HTTP/2 200
```
