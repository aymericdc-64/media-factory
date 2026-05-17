#!/usr/bin/env bash
# ============================================================
# Bootstrap a fresh OVH VPS Starter (Ubuntu 24.04 LTS) for the factory.
# ============================================================
# Usage : ./scripts/setup-vps.sh ubuntu@<your-ovh-ip>
#   (l'utilisateur par défaut sur OVH Ubuntu est "ubuntu" avec sudo.
#    Si tu as activé le login root, passe root@<ip>.)
# ============================================================
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <ssh-target>  (ex: ubuntu@1.2.3.4)"
  exit 1
fi

SSH_TARGET="$1"

echo "▶ Provisioning $SSH_TARGET (Ubuntu 24.04 LTS, OVH VPS Starter) ..."

ssh -o StrictHostKeyChecking=accept-new "$SSH_TARGET" bash -s <<'REMOTE'
set -euo pipefail

# Détection : sommes-nous root ou un user sudoers ?
if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "→ Vérif distribution"
. /etc/os-release
if [ "$ID" != "ubuntu" ]; then
  echo "⚠️  Ce script est conçu pour Ubuntu. Détecté : $ID $VERSION_ID"
  echo "    Continue à tes risques (les repos Docker diffèrent)."
fi
echo "    Ubuntu $VERSION_ID ($VERSION_CODENAME)"

echo "→ apt update + upgrade"
export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get update -y
$SUDO apt-get upgrade -y
$SUDO apt-get install -y \
  ca-certificates curl gnupg lsb-release \
  ufw fail2ban git unattended-upgrades \
  htop iotop ncdu

echo "→ Swap 1 GB (compense les 2 GB RAM du tier Starter)"
if [ ! -f /swapfile ]; then
  $SUDO fallocate -l 1G /swapfile
  $SUDO chmod 600 /swapfile
  $SUDO mkswap /swapfile
  $SUDO swapon /swapfile
  echo "/swapfile none swap sw 0 0" | $SUDO tee -a /etc/fstab >/dev/null
  # Réduire l'agressivité du swap (n'utiliser que sous pression mémoire réelle)
  echo "vm.swappiness=10" | $SUDO tee /etc/sysctl.d/99-swappiness.conf >/dev/null
  $SUDO sysctl -p /etc/sysctl.d/99-swappiness.conf
  echo "    Swap 1 GB actif (swappiness=10)"
else
  echo "    Swap déjà présent"
fi

echo "→ Docker install (repo officiel Ubuntu)"
$SUDO install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
$SUDO chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
  | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null

$SUDO apt-get update -y
$SUDO apt-get install -y \
  docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

echo "→ UFW firewall : allow ssh / http / https only"
$SUDO ufw --force reset
$SUDO ufw default deny incoming
$SUDO ufw default allow outgoing
$SUDO ufw allow 22/tcp
$SUDO ufw allow 80/tcp
$SUDO ufw allow 443/tcp
$SUDO ufw --force enable

echo "→ fail2ban : protection ssh"
$SUDO systemctl enable --now fail2ban

echo "→ unattended-upgrades : patches sécurité auto"
$SUDO dpkg-reconfigure -f noninteractive unattended-upgrades

echo "→ User non-root 'factory' + accès docker"
if ! id -u factory >/dev/null 2>&1; then
  $SUDO useradd -m -s /bin/bash factory
fi
$SUDO usermod -aG docker factory

echo "→ Créer /opt/media-factory"
$SUDO mkdir -p /opt/media-factory
$SUDO chown factory:factory /opt/media-factory

# Si l'utilisateur connecté n'est ni root ni factory, on l'ajoute aussi à docker
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" != "root" ] && [ "$CURRENT_USER" != "factory" ]; then
  $SUDO usermod -aG docker "$CURRENT_USER"
  echo "    $CURRENT_USER ajouté au groupe docker (reconnecte-toi pour appliquer)"
fi

echo ""
echo "✓ VPS bootstrap terminé"
echo "  - Docker version : $(docker --version)"
echo "  - Swap          : $(free -h | grep Swap | awk '{print $2}')"
echo "  - Firewall      : $($SUDO ufw status | head -1)"
REMOTE

echo
echo "▶ Étapes suivantes depuis ta machine locale :"
echo "  1. Pousser le repo sur le VPS :"
echo "       ./deploy/scripts/push-to-vps.sh $SSH_TARGET"
echo "  2. Remplir le .env sur le VPS :"
echo "       ssh $SSH_TARGET 'cd /opt/media-factory/deploy && cp .env.example .env && nano .env'"
echo "  3. Démarrer la stack :"
echo "       ssh $SSH_TARGET 'cd /opt/media-factory/deploy && docker compose up -d --build'"
echo "  4. Configurer 2 records DNS A (n8n.<domain> et skills.<domain>) → IP du VPS"
echo "  5. Ouvrir https://n8n.<domain> et créer le compte admin"
