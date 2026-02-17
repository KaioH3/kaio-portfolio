#!/usr/bin/env bash
# VPS Initial Setup - Kaio Portfolio
# Run ONCE on your VPS as your deploy user
# Usage: bash vps-setup.sh
set -euo pipefail

REPO_URL="git@github.com:KaioH3/kaio-portfolio.git"
APP_DIR="$HOME/kaio-portfolio"
SERVICE_NAME="kaio-portfolio"
PYTHON_VERSION="3.11"
VPS_USER="$(whoami)"   # uses the current user — no hardcoded names

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] OK: $*"; }
die()  { echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2; exit 1; }

# ── 1. System dependencies ───────────────────────────────────────────────────
log "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip \
    git curl nginx certbot python3-certbot-nginx \
    build-essential libssl-dev
ok "System dependencies installed"

# ── 2. GitHub deploy key ──────────────────────────────────────────────────────
if [[ ! -f "$HOME/.ssh/deploy_kaio" ]]; then
    log "Generating GitHub deploy key..."
    ssh-keygen -t ed25519 -C "deploy@$(hostname)" -f "$HOME/.ssh/deploy_kaio" -N ""
    echo ""
    echo "=========================================================="
    echo "  Add this DEPLOY KEY to GitHub:"
    echo "  github.com/KaioH3/kaio-portfolio → Settings → Deploy keys"
    echo "  Title: hetzner-vps | Allow write access: NO"
    echo "=========================================================="
    cat "$HOME/.ssh/deploy_kaio.pub"
    echo "=========================================================="
    echo ""
    echo "Press ENTER after adding the key to GitHub..."
    read -r

    # Configure SSH to use deploy key for this repo
    cat >> "$HOME/.ssh/config" << EOF

Host github-kaio
  HostName github.com
  User git
  IdentityFile ~/.ssh/deploy_kaio
  IdentitiesOnly yes
  StrictHostKeyChecking no
EOF
    chmod 600 "$HOME/.ssh/config"
    ok "Deploy key configured"
fi

# ── 3. Clone repository ───────────────────────────────────────────────────────
if [[ -d "$APP_DIR" ]]; then
    log "Directory $APP_DIR already exists, pulling latest..."
    cd "$APP_DIR" && git pull
else
    log "Cloning repository..."
    # Use the deploy key host alias
    git clone "git@github-kaio:KaioH3/kaio-portfolio.git" "$APP_DIR"
fi
ok "Repository ready at $APP_DIR"
cd "$APP_DIR"

# ── 4. Python virtual environment ─────────────────────────────────────────────
if [[ ! -d "$APP_DIR/venv" ]]; then
    log "Creating Python virtual environment..."
    python${PYTHON_VERSION} -m venv venv
fi
log "Installing Python dependencies..."
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet -r requirements.txt
ok "Python environment ready"

# ── 5. Create directories ─────────────────────────────────────────────────────
mkdir -p data/models logs
ok "Directories created"

# ── 6. Environment file ───────────────────────────────────────────────────────
if [[ ! -f "$APP_DIR/.env" ]]; then
    log "Creating .env from template..."
    cp .env.example .env
    chmod 600 .env  # owner-only read/write

    echo ""
    echo "=========================================================="
    echo "  IMPORTANT: Fill in your API keys in .env"
    echo "  nano $APP_DIR/.env"
    echo ""
    echo "  Required keys:"
    echo "    GROQ_API_KEY     - groq.com (free)"
    echo "    VOYAGE_API_KEY   - dash.voyageai.com (free 200M tokens)"
    echo "    QDRANT_URL       - cloud.qdrant.io (free 1GB)"
    echo "    QDRANT_API_KEY"
    echo ""
    echo "  Also set:"
    echo "    ENV=production"
    echo "    BASE_URL=https://yourdomain.com"
    echo "=========================================================="
    echo ""
    echo "Press ENTER after editing .env..."
    read -r
else
    ok ".env already exists"
fi

# ── 7. Credit Risk model ──────────────────────────────────────────────────────
if [[ ! -f "$APP_DIR/data/models/credit_risk_model.joblib" ]]; then
    echo ""
    echo "=========================================================="
    echo "  Credit Risk model not found."
    echo "  Option A: Copy pre-trained artifacts from your local machine:"
    echo "    scp -r local_machine:~/kaio-portfolio/data/models/ aikadmin@VPS_IP:$APP_DIR/data/"
    echo ""
    echo "  Option B: Train from scratch (needs Kaggle dataset first):"
    echo "    Follow: $APP_DIR/app/projects/creditrisk/README.md"
    echo "=========================================================="
    echo ""
fi

# ── 8. Test application starts ────────────────────────────────────────────────
log "Testing application startup..."
if timeout 15 venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from app.main import app
print('App imports OK')
"; then
    ok "Application imports successfully"
else
    die "Application failed to import. Check .env and dependencies."
fi

# ── 9. Install systemd service ────────────────────────────────────────────────
log "Installing systemd service..."
# Fill in placeholders from the template (no credentials in repo)
sed -e "s|__VPS_USER__|${VPS_USER}|g" \
    -e "s|__APP_DIR__|${APP_DIR}|g" \
    deploy/systemd/${SERVICE_NAME}.service \
    | sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}
sleep 3

if systemctl is-active --quiet ${SERVICE_NAME}; then
    ok "Service ${SERVICE_NAME} is running"
else
    echo "Service failed to start. Check logs:"
    echo "  journalctl -u ${SERVICE_NAME} -n 50"
    die "Service startup failed"
fi

# ── 10. Nginx configuration ───────────────────────────────────────────────────
NGINX_CONF="/etc/nginx/sites-available/${SERVICE_NAME}"
if [[ ! -f "$NGINX_CONF" ]]; then
    log "Configuring nginx reverse proxy..."
    sudo tee "$NGINX_CONF" > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        client_max_body_size 15M;
    }
}
NGINX
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    ok "Nginx configured"
fi

echo ""
echo "=========================================================="
echo "  SETUP COMPLETE"
echo ""
echo "  Service: systemctl status ${SERVICE_NAME}"
echo "  Logs:    journalctl -u ${SERVICE_NAME} -f"
echo "  Update:  bash scripts/vps-update.sh"
echo ""
echo "  OPTIONAL - Enable HTTPS:"
echo "    sudo certbot --nginx -d yourdomain.com"
echo "=========================================================="
