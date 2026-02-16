# ML Engineer Portfolio

Production-ready Machine Learning portfolio com FastAPI, XGBoost, RAG system e deploy containerizado.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Live Demo

- **Portfolio**: [Em desenvolvimento]
- **Swagger Docs**: `/docs` (quando rodando localmente)

## Projetos

### 1. RAG Document Intelligence
Sistema de Retrieval-Augmented Generation com Chain-of-Verification para reduzir alucinações.

**Stack**: FastEmbed (CPU-only), Qdrant, Groq API, HTMX
**Features**: Upload de PDFs/TXT, busca híbrida (semântica + BM25), i18n (PT-BR/EN-US)
**Endpoint**: `/rag-system/`

### 2. Credit Risk Scoring API
Sistema de scoring de crédito com XGBoost + SHAP explanations para compliance regulatório.

**Stack**: XGBoost, SHAP, Scikit-learn, Pandas
**Dataset**: Credit Card Approval (Kaggle - 97k downloads, 430k registros)
**Features**: Predição de risco, explicabilidade SHAP, API JSON + interface HTMX
**Endpoint**: `/credit-risk/`

**Métricas**: AUC-ROC > 0.75, Inference < 100ms, 30+ features engineered

## Tech Stack

**Backend**
- FastAPI 0.115+ com validação Pydantic
- Python 3.11 com type hints completos
- Async/await para I/O operations

**ML/Data**
- XGBoost para classificação
- SHAP para explicabilidade
- FastEmbed para embeddings (CPU-only)
- Qdrant para vector search

**Frontend**
- HTMX para interatividade (sem JS framework)
- Jinja2 templates
- FrontRender Design System (CSS puro)

**DevOps**
- Podman Compose (containers rootless)
- Prometheus + Grafana (monitoring)
- Caddy 2 (reverse proxy)
- Systemd (process management)

## Quick Start

### Requisitos
- Python 3.11+
- 4GB+ RAM
- Conta Kaggle (para dataset)

### Setup em 3 passos

```bash
# 1. Clonar e criar ambiente
git clone https://github.com/seu-usuario/kaio-portfolio.git
cd kaio-portfolio
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar Kaggle API (para Credit Risk)
# Acesse: https://www.kaggle.com/settings/account
# Download kaggle.json
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# 3. Setup Credit Risk (download + train)
./scripts/setup.sh

# 4. Rodar servidor
uvicorn app.main:app --reload
```

Acesse: `http://localhost:8000`

## Estrutura

```
kaio-portfolio/
├── app/
│   ├── core/              # Config, logging, security
│   ├── routers/           # API routes (home, health)
│   └── projects/          # Projetos ML
│       ├── ragsystem/     # RAG Document Intelligence
│       └── creditrisk/    # Credit Risk Scoring
├── data/                  # Datasets e modelos
├── tests/                 # Pytest (unit + integration)
├── scripts/               # Setup automático
├── deploy/                # Configs de produção
└── static/                # Assets (CSS, imagens)
```

## Testes

```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=app

# Apenas Credit Risk
pytest tests/test_creditrisk.py -v
```

## Documentação

- **CLAUDE.md**: Guia completo de arquitetura e comandos
- **app/projects/creditrisk/README.md**: Documentação específica do Credit Risk
- **Swagger UI**: `/docs` (ambiente development)

## Segurança

- Input validation via Pydantic
- Sanitização de dados categóricos (Enums)
- Rate limiting (IP-based)
- CORS configurável
- Containers rootless (Podman)

## Performance

**Credit Risk API**
- Latência: < 100ms (p95)
- Throughput: ~100 req/s (single CPU)
- Footprint: ~500MB RAM

**RAG System**
- Latência: < 2s (com LLM call)
- Embedding: CPU-only (~200MB)
- Vector DB: Embedded Qdrant

## Deploy

```bash
# Build container
podman build -t kaio-portfolio:latest -f containerfiles/Containerfile.api .

# Run com compose
podman-compose -f deploy/podman-compose.yml up -d
```

## License

MIT License - Kaio H. Siqueira © 2026

---

**Contato**: [GitHub](https://github.com/kaioH3) | [LinkedIn](https://www.linkedin.com/in/kaiohsiqueira/) | [Medium](https://medium.com/@KaioH3)
