# Kaio Portfolio - Development & Deployment Commands
# Usage: make <target>
#
# For VPS operations, set VPS_HOST before running:
#   VPS_HOST=user@your-server-ip make deploy

.PHONY: help dev test lint deploy upload-model logs status ssh

VPS_HOST ?= $(error Set VPS_HOST: make <target> VPS_HOST=user@server-ip)
# VPS_HOST_BRACKET defaults to VPS_HOST (no brackets needed for IPv4)
VPS_HOST_BRACKET ?= $(VPS_HOST)

help:
	@echo "Commands:"
	@echo "  make dev                       - Start local dev server"
	@echo "  make test                      - Run tests"
	@echo "  make lint                      - Check code style"
	@echo "  make deploy       VPS_HOST=... - Deploy latest code"
	@echo "  make upload-model VPS_HOST=... - Upload Credit Risk model"
	@echo "  make logs         VPS_HOST=... - Tail VPS logs"
	@echo "  make status       VPS_HOST=... - Service status"
	@echo "  make ssh          VPS_HOST=... - SSH into VPS"

# ── Local Development ─────────────────────────────────────────────────────────
dev:
	source venv/bin/activate && uvicorn app.main:app --reload

test:
	source venv/bin/activate && pytest -v

lint:
	source venv/bin/activate && ruff check app/ tests/ 2>/dev/null || echo "ruff not installed"

# ── VPS Operations ────────────────────────────────────────────────────────────
deploy:
	@echo "Syncing code to VPS..."
	tar --exclude='venv' --exclude='.env' --exclude='__pycache__' \
	    --exclude='*.pyc' --exclude='.git' --exclude='data' \
	    --exclude='.pytest_cache' --exclude='.ruff_cache' \
	    -czf /tmp/kaio-deploy.tar.gz .
	scp -i ~/.ssh/id_rsa /tmp/kaio-deploy.tar.gz "$(VPS_HOST_BRACKET):/tmp/"
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) '\
	    tar -xzf /tmp/kaio-deploy.tar.gz -C ~/kaio-portfolio && \
	    rm /tmp/kaio-deploy.tar.gz && \
	    cd ~/kaio-portfolio && \
	    podman build -t localhost/kaio-portfolio-api:latest -f containerfiles/Containerfile.api . && \
	    podman stop kaio-api && \
	    podman rm kaio-api && \
	    podman run -d --name kaio-api --network=host \
	      --env-file ~/kaio-portfolio/.env \
	      -e ENV=production -e PROMETHEUS_ENABLED=true \
	      -v ~/kaio-portfolio/data:/app/data \
	      --security-opt no-new-privileges:true \
	      --restart unless-stopped \
	      --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 \
	      localhost/kaio-portfolio-api:latest'
	rm -f /tmp/kaio-deploy.tar.gz
	@echo "Deployed."

upload-model:
	@echo "Uploading Credit Risk model to VPS..."
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'mkdir -p ~/kaio-portfolio/data/models'
	scp -i ~/.ssh/id_rsa data/models/credit_risk_xgboost.pkl "$(VPS_HOST_BRACKET):~/kaio-portfolio/data/models/"
	scp -i ~/.ssh/id_rsa data/models/credit_risk_scaler.pkl "$(VPS_HOST_BRACKET):~/kaio-portfolio/data/models/"
	scp -i ~/.ssh/id_rsa data/models/credit_risk_encoder.pkl "$(VPS_HOST_BRACKET):~/kaio-portfolio/data/models/"
	scp -i ~/.ssh/id_rsa data/models/credit_risk_features.json "$(VPS_HOST_BRACKET):~/kaio-portfolio/data/models/"
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'podman restart kaio-api'

logs:
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'podman logs kaio-api -f'

status:
	ssh -i ~/.ssh/id_rsa $(VPS_HOST) 'podman ps && curl -s http://localhost:8000/api/health'

ssh:
	ssh -i ~/.ssh/id_rsa $(VPS_HOST)
