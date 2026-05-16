#!/usr/bin/env bash
# Sync the repo to the VPS and rebuild the stack.
# Usage : ./scripts/push-to-vps.sh root@<ip>
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <ssh-target>"
  exit 1
fi

SSH_TARGET="$1"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "▶ rsync repo to $SSH_TARGET:/opt/media-factory ..."
rsync -avh --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  --exclude 'node_modules' \
  --exclude 'deploy/.env' \
  --exclude 'skills-service/.env' \
  "$ROOT_DIR/" "$SSH_TARGET:/opt/media-factory/"

echo "▶ docker compose up -d --build ..."
ssh "$SSH_TARGET" "cd /opt/media-factory/deploy && docker compose up -d --build && docker compose ps"

echo "✓ Deploy done"
