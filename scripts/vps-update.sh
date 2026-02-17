#!/usr/bin/env bash
# VPS Update - Pull latest code and restart service
# Usage: bash scripts/vps-update.sh
set -euo pipefail

APP_DIR="$HOME/kaio-portfolio"
SERVICE_NAME="kaio-portfolio"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
ok()  { echo "[$(date '+%H:%M:%S')] OK: $*"; }

cd "$APP_DIR"

log "Pulling latest code..."
git pull
ok "Code updated"

log "Updating Python dependencies..."
venv/bin/pip install --quiet -r requirements.txt
ok "Dependencies updated"

log "Restarting service..."
sudo systemctl restart "${SERVICE_NAME}"
sleep 3

if systemctl is-active --quiet "${SERVICE_NAME}"; then
    ok "Service restarted successfully"
    echo ""
    echo "Logs (last 20 lines):"
    journalctl -u "${SERVICE_NAME}" -n 20 --no-pager
else
    echo "ERROR: Service failed to restart"
    journalctl -u "${SERVICE_NAME}" -n 30 --no-pager
    exit 1
fi
