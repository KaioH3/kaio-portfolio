# Kaio Portfolio - Development & Deployment Commands
# Usage: make <target>
#
# For VPS operations, set VPS_HOST before running:
#   VPS_HOST=user@your-server-ip make deploy
#   or export VPS_HOST=user@your-server-ip

.PHONY: help dev test lint deploy-setup deploy upload-model logs status ssh

VPS_HOST ?= $(error Set VPS_HOST: e.g. make deploy VPS_HOST=user@ip)
VPS_DIR  ?= ~/kaio-portfolio

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
deploy-setup:
	ssh $(VPS_HOST) 'bash -s' < scripts/vps-setup.sh

deploy:
	ssh $(VPS_HOST) 'cd $(VPS_DIR) && bash scripts/vps-update.sh'

upload-model:
	@echo "Uploading Credit Risk model artifacts to $(VPS_HOST)..."
	ssh $(VPS_HOST) 'mkdir -p $(VPS_DIR)/data/models'
	scp data/models/credit_risk_model.joblib $(VPS_HOST):$(VPS_DIR)/data/models/
	scp data/models/feature_engineering.joblib $(VPS_HOST):$(VPS_DIR)/data/models/
	ssh $(VPS_HOST) 'sudo systemctl restart kaio-portfolio'

logs:
	ssh $(VPS_HOST) 'journalctl -u kaio-portfolio -f'

status:
	ssh $(VPS_HOST) 'systemctl status kaio-portfolio --no-pager'

ssh:
	ssh $(VPS_HOST)
