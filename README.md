# Kaio Portfolio - ML Engineer

Portfolio profissional de Machine Learning Engineer com arquitetura production-ready.

## Stack Técnica

- **Backend**: FastAPI 0.115+ | Python 3.11
- **Container**: Podman Compose (rootless)
- **Server**: Caddy 2 (reverse proxy, SSL automático)
- **Frontend**: FrontRender Design System (3.48KB)
- **Deploy**: Oracle Cloud | Hetzner VPS
- **Monitoring**: Prometheus + Grafana

## Estrutura do Projeto

```
kaio-portfolio/
├── app/                    # Core application
│   ├── core/              # Utilities (logging, security)
│   ├── routers/           # API routes
│   ├── projects/          # Project-specific modules
│   └── models/            # Database models
├── templates/             # Jinja2 templates
├── static/                # CSS/JS/Images
├── tests/                 # Pytest tests
├── deploy/                # Deployment configs
├── monitoring/            # Observability
└── containerfiles/        # Podman container definitions
```

## Setup

```bash
# 1. Executar script de estrutura
chmod +x setup-estrutura-fix.sh
./setup-estrutura-fix.sh

# 2. Gerar código (próximo script)
./2-gerar-codigo.sh

# 3. Rodar localmente
source venv/bin/activate
uvicorn app.main:app --reload
```

## Projetos

1. **RAG Document Intelligence** - Sistema modular com Chain-of-Verification que reduz alucinações
2. **Credit Scoring API** - XGBoost para análise de risco com SHAP explanations

## License

MIT License - Kaio Siqueira © 2026
