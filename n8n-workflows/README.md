# n8n-workflows

4 workflows n8n exportés en JSON, importables tels quels via l'UI.

| Fichier | Trigger | Rôle |
|---|---|---|
| [`daily-run.json`](./daily-run.json) | Cron 06h UTC | Génère 5 vidéos, score, envoie top 3 sur Telegram pour validation |
| [`approval-webhook.json`](./approval-webhook.json) | Webhook POST `/telegram-callback` | Reçoit clic Approve/Reject Telegram → met à jour Notion |
| [`publish-slots.json`](./publish-slots.json) | Cron 12h + 18h UTC | Publie sur chaque channel actif les rows Approved dont le slot est arrivé |
| [`analyst-daily.json`](./analyst-daily.json) | Cron 23h UTC | Fetch métriques D+1/D+7/D+30, compute verdict, écrit notes |

## Import

1. UI n8n → **Workflows** → bouton `…` (top right) → **Import from File**
2. Sélectionner les 4 fichiers JSON, l'un après l'autre.
3. Pour chaque workflow, ouvrir et :
   - Activer si tu veux qu'il tourne tout seul (laisser **off** pendant les tests).
   - Renseigner les credentials (cf. ci-dessous).

## Credentials requises (à créer dans n8n une seule fois)

| Nom dans n8n | Type | Valeur |
|---|---|---|
| `Skills Service Bearer` | HTTP Header Auth | `Name: Authorization` · `Value: Bearer $SKILLS_AUTH_SECRET` |
| `Anthropic API Key` | HTTP Header Auth | `Name: x-api-key` · `Value: $ANTHROPIC_API_KEY` |

> 💡 Les autres clés (fal.ai, Creatomate, Notion, IG, TT, YT, Telegram bot) ne sont **pas** appelées directement depuis n8n — elles vivent côté Skills Service.

## Variables d'environnement n8n requises

À renseigner dans `n8n` via UI **Settings → Environment Variables**, ou via le fichier `deploy/.env` :

```
SKILLS_BASE_URL=https://skills.<ton-domaine>
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

(le service n8n les expose dans `$env.NAME` à chaque nœud HTTP Request)

## Webhook Telegram — point de configuration

Après import du workflow **Approval Webhook**, l'URL publique du webhook devient :

```
https://n8n.<ton-domaine>/webhook/telegram-callback
```

(version test : `/webhook-test/telegram-callback`)

Renseigner cette URL dans **BotFather** :

```
/setdomain
@TonBot
https://n8n.<ton-domaine>
```

puis enregistrer le webhook côté API Telegram :

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://n8n.<ton-domaine>/webhook/telegram-callback"
```

## Test manuel des 4 workflows

Dans n8n UI, ouvrir le workflow puis cliquer **Execute Workflow** (bouton bleu en bas). Cela bypass le cron / webhook et exécute l'ensemble manuellement avec les nœuds enchainés.

Vérifier dans Notion que :

- Daily Run → 5 rows créées avec `Status=Scored` dans Production Pipeline
- Telegram reçoit un message avec 3 vidéos + boutons Approve / Reject
- Cliquer Approve → la row passe à `Status=Approved` et `Scheduled Publish` se remplit
- Publish Slots (manual) → la row passe à `Status=Published`, et une row apparaît dans Performance Tracker
- Analyst (manual) → si tu mets `Snapshot=D+1` sur une row de la veille, les métriques se remplissent

## Standards n8n appliqués

- **Idempotence** : tous les writes Notion passent par les skills, qui s'appuient sur `Prod ID` / `Post ID` pour PATCH plutôt que CREATE.
- **Retry** : `options.retryOnFail` et `options.maxTries` sont à activer manuellement par nœud HTTP (recommandé : 3 retries, 30s backoff).
- **Erreur** : `settings.saveDataErrorExecution=all` permet de relancer un workflow échoué depuis l'UI.
- **Timeouts** : déjà câblés à des valeurs sensées (30s read Notion, 600s long-poll fal.ai/Creatomate, 300s upload R2).

## Évolutions

- [ ] Ajouter retry/backoff sur chaque nœud HTTP Request (UI → settings)
- [ ] Ajouter Error Trigger workflow → Telegram alerte ops
- [ ] Migrer les payloads d'authentification vers HTTP Header Auth typed credentials plutôt que `$env`
- [ ] Splitter Daily Run en 2 sous-workflows (Strategist + Producer/Scorer) pour parallélisation propre
