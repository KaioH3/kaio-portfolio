# Kaio Portfolio - Development & Deployment Commands
# Usage: make <target>

.PHONY: help dev test lint deploy-setup deploy-update logs status

VPS_HOST ?= aikadmin@aik-cax11-production
APP_DIR  := /home/aikadmin/kaio-portfolio

help:
	@echo "Available commands:"
	@echo "  make dev          - Start local dev server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Check code style"
	@echo "  make deploy-setup - First-time VPS setup"
	@echo "  make deploy       - Deploy latest code to VPS"
	@echo "  make upload-model - Upload trained Credit Risk model to VPS"
	@echo "  make logs         - Tail VPS application logs"
	@echo "  make status       - Check VPS service status"
	@echo "  make ssh          - SSH into VPS"

# ── Local Development ─────────────────────────────────────────────────────────
dev:
	source venv/bin/activate && uvicorn app.main:app --reload

test:
	source venv/bin/activate && pytest -v

lint:
	source venv/bin/activate && ruff check app/ tests/ 2>/dev/null || echo "ruff not installed, run: pip install ruff"

# ── VPS Operations ────────────────────────────────────────────────────────────
deploy-setup:
	ssh $(VPS_HOST) 'bash -s' < scripts/vps-setup.sh

deploy:
	ssh $(VPS_HOST) 'cd $(APP_DIR) && bash scripts/vps-update.sh'

upload-model:
	@echo "Uploading Credit Risk model artifacts..."
	ssh $(VPS_HOST) 'mkdir -p $(APP_DIR)/data/models'
	scp data/models/credit_risk_model.joblib $(VPS_HOST):$(APP_DIR)/data/models/
	scp data/models/feature_engineering.joblib $(VPS_HOST):$(APP_DIR)/data/models/
	@echo "Model uploaded. Restarting service..."
	ssh $(VPS_HOST) 'sudo systemctl restart kaio-portfolio'

logs:
	ssh $(VPS_HOST) 'journalctl -u kaio-portfolio -f'

status:
	ssh $(VPS_HOST) 'systemctl status kaio-portfolio --no-pager'

ssh:
	ssh $(VPS_HOST)
