#!/usr/bin/env bash
# Backup n8n workflows + credentials + postgres DB to a local tarball.
# Run on the VPS, then scp the resulting file elsewhere.
set -euo pipefail

BACKUP_DIR="/opt/factory-backups"
DATE="$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "▶ Dumping postgres ..."
docker exec factory-postgres pg_dump -U n8n n8n | gzip > "$BACKUP_DIR/n8n-db-$DATE.sql.gz"

echo "▶ Exporting workflows + credentials ..."
docker exec factory-n8n n8n export:workflow --all --output=/tmp/workflows.json
docker exec factory-n8n n8n export:credentials --all --decrypted=false --output=/tmp/credentials.json
docker cp factory-n8n:/tmp/workflows.json "$BACKUP_DIR/workflows-$DATE.json"
docker cp factory-n8n:/tmp/credentials.json "$BACKUP_DIR/credentials-$DATE.json"

echo "▶ Tarballing ..."
cd "$BACKUP_DIR"
tar -czf "factory-backup-$DATE.tar.gz" \
  "n8n-db-$DATE.sql.gz" "workflows-$DATE.json" "credentials-$DATE.json"

# Cleanup raw files; keep tarballs
rm "n8n-db-$DATE.sql.gz" "workflows-$DATE.json" "credentials-$DATE.json"

echo "✓ Backup at $BACKUP_DIR/factory-backup-$DATE.tar.gz"
echo "  Don't forget to copy it off the VPS."
