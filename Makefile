# Kaio Portfolio - Development & Deployment Commands
# Usage: make <target>
#
# For VPS operations, set VPS_HOST before running:
#   VPS_HOST=user@your-server-ip make deploy
#   or export VPS_HOST=user@your-server-ip

.PHONY: help dev test lint deploy-setup deploy upload-model logs status ssh

# IPv6 VPS: use bracket notation for scp, plain for ssh
# Usage: make deploy VPS_HOST=user@ip VPS_HOST_BRACKET="user@[ip]"
VPS_HOST         ?= $(error Set VPS_HOST: user@server-ip)
VPS_HOST_BRACKET ?= $(error Set VPS_HOST_BRACKET: "user@[server-ip]")

help:
	@echo "Commands:"
	@echo "  make dev                         - Start local dev server"
	@echo "  make test                        - Run tests"
	@echo "  make lint                        - Check code style"
	@echo "  make deploy-setup VPS_HOST=...   - First-time VPS setup"
	@echo "  make deploy       VPS_HOST=...   - Deploy latest code"
	@echo "  make upload-model VPS_HOST=...   - Upload Credit Risk model"
	@echo "  make logs         VPS_HOST=...   - Tail VPS logs"
	@echo "  make status       VPS_HOST=...   - Service status"
	@echo "  make ssh          VPS_HOST=...   - SSH into VPS"

# ── Local Development ─────────────────────────────────────────────────────────
dev:
	source venv/bin/activate && uvicorn app.main:app --reload

test:
	source venv/bin/activate && pytest -v

lint:
	source venv/bin/activate && ruff check app/ tests/ 2>/dev/null || echo "ruff not installed"

# ── VPS Operations ────────────────────────────────────────────────────────────
# VPS is IPv6-only: deploy uses scp/ssh directly (no git pull on server)

deploy:
	@echo "Syncing code to VPS..."
	tar --exclude='venv' --exclude='.env' --exclude='__pycache__' \
	    --exclude='*.pyc' --exclude='.git' --exclude='data' \
	    --exclude='.pytest_cache' --exclude='.ruff_cache' \
	    -czf /tmp/kaio-deploy.tar.gz .
	scp -i ~/.ssh/id_rsa /tmp/kaio-deploy.tar.gz "$(VPS_HOST_BRACKET):/tmp/"
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) \
	    'tar -xzf /tmp/kaio-deploy.tar.gz -C ~/kaio-portfolio && rm /tmp/kaio-deploy.tar.gz && cd ~/kaio-portfolio && podman-compose up -d --build'
	rm /tmp/kaio-deploy.tar.gz
	@echo "Deployed. Check: make status"

upload-model:
	@echo "Uploading Credit Risk model to VPS..."
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'mkdir -p ~/kaio-portfolio/data/models'
	scp -i ~/.ssh/id_rsa data/models/credit_risk_model.joblib "$(VPS_HOST_BRACKET):~/kaio-portfolio/data/models/"
	scp -i ~/.ssh/id_rsa data/models/feature_engineering.joblib "$(VPS_HOST_BRACKET):~/kaio-portfolio/data/models/"
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'cd ~/kaio-portfolio && podman-compose restart'

logs:
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'podman logs kaio-api -f'

status:
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'podman ps && curl -s http://localhost:8000/api/health'

ssh:
	ssh -i ~/.ssh/id_rsa $(VPS_HOST)
