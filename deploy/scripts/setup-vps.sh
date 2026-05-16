#!/usr/bin/env bash
# ============================================================
# Bootstrap a fresh Hetzner CX22 (Ubuntu 24.04) for the factory.
# ============================================================
# Usage : ./scripts/setup-vps.sh root@<your-hetzner-ip>
# ============================================================
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <ssh-target>  (ex: root@1.2.3.4)"
  exit 1
fi

SSH_TARGET="$1"

echo "▶ Provisioning $SSH_TARGET..."

ssh -o StrictHostKeyChecking=accept-new "$SSH_TARGET" bash -s <<'REMOTE'
set -euo pipefail

echo "→ apt update + harden"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y \
  ca-certificates curl gnupg lsb-release \
  ufw fail2ban git unattended-upgrades

echo "→ Docker install (official repo)"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "→ UFW firewall : allow ssh / http / https only"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "→ fail2ban : ssh protection"
systemctl enable --now fail2ban

echo "→ unattended-upgrades : security patches auto"
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "→ create /opt/factory + non-root user"
useradd -m -s /bin/bash factory 2>/dev/null || true
usermod -aG docker factory
mkdir -p /opt/factory
chown factory:factory /opt/factory

echo "✓ VPS bootstrap complete"
REMOTE

echo
echo "▶ Now from your local machine :"
echo "  1. rsync -avh --exclude '.git' ../../media-factory $SSH_TARGET:/opt/"
echo "  2. ssh $SSH_TARGET 'cd /opt/media-factory/deploy && cp .env.example .env && nano .env'"
echo "  3. ssh $SSH_TARGET 'cd /opt/media-factory/deploy && docker compose up -d --build'"
echo "  4. Point DNS A records for n8n.<domain> and skills.<domain> to your VPS IP."
echo "  5. Open https://n8n.<domain> and create the admin account."
