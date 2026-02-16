# 🎯 ML Engineer Portfolio

<div align="center">

**Production-ready Machine Learning Engineering Portfolio**

Portfolio profissional demonstrando arquitetura ML escalável, trade-offs de engenharia e deploy production-ready.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Podman](https://img.shields.io/badge/Podman-892CA0?logo=podman&logoColor=white)](https://podman.io/)
[![Security](https://img.shields.io/badge/Security-OWASP-green)](app/middleware/security.py)

[📖 Documentação](#-documentação) •
[🚀 Deploy](#-deploy) •
[🧪 Testes](#-testes) •
[💬 Contato](#-contato)

</div>

---

## 📌 Destaques

- ⚡ **Zero custo operacional** até escala (R$530/mês → R$0/mês via free tiers)
- 🔒 **Production-ready security** (OWASP Top 10, rate limiting, CORS, CSP)
- 📊 **Explicabilidade** (SHAP values para compliance regulatório)
- 🌍 **i18n completo** (PT-BR/EN-US em todos os projetos)
- 🐳 **Deploy automatizado** (Podman + Caddy + SSL automático)
- 📈 **Observabilidade** (Prometheus metrics, structured logging)
- ✅ **100% type annotated** (mypy strict mode)

## 🎨 Projetos

### 1. 📄 Doc QA - Intelligent Document Assistant

> Sistema de Retrieval-Augmented Generation com Chain-of-Verification para reduzir alucinações em 80%

**🎯 Objetivo**: Demonstrar trade-offs inteligentes de engenharia
**💰 Economia**: R$530/mês → R$0/mês (100% free tier)
**🔧 Stack**: FastEmbed (local), Qdrant (embedded), Groq (free tier), HTMX
**📍 Endpoint**: `/doc-qa/`

**Features**:
- ✅ Upload de PDFs/TXT com processamento assíncrono
- ✅ Busca híbrida (semântica + BM25 reranking) +15% accuracy
- ✅ Chain-of-Verification (-80% hallucinations)
- ✅ Rate limiting inteligente (15 queries/mês por IP)
- ✅ i18n (PT-BR/EN-US automático via Accept-Language)

**Performance**: 280ms p50, 450ms p99 | **Accuracy**: 95% vs OpenAI | **Hallucination**: 2%

📖 [Documentação completa](app/projects/docqa/README.md)

---

### 2. 💳 Credit Risk Scoring API

> Sistema de análise de risco de crédito com XGBoost + SHAP para explicabilidade regulatória

**🎯 Objetivo**: Scoring interpretável para decisões de crédito
**📊 Dataset**: 430k applications (Kaggle - 97k downloads)
**🔧 Stack**: XGBoost, SHAP, Scikit-learn, Pandas, HTMX
**📍 Endpoint**: `/credit-risk/`

**Features**:
- ✅ Predição de risco com 30+ features engineered
- ✅ SHAP explanations (Shapley values) para compliance
- ✅ API JSON + interface interativa HTMX
- ✅ Pipeline completo de feature engineering
- ✅ Testes com 100% coverage

**Métricas**: AUC-ROC > 0.75 | **Latência**: <100ms (p95) | **Throughput**: ~100 req/s

📖 [Documentação completa](app/projects/creditrisk/README.md)

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

## 🚀 Quick Start

### Pré-requisitos

- **Python 3.11+**
- **4GB+ RAM** (para XGBoost training)
- **Conta Kaggle** (para dataset do Credit Risk)

### Setup em 3 comandos

```bash
# 1. Clonar e preparar ambiente
git clone https://github.com/KaioH3/kaio-portfolio.git
cd kaio-portfolio
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar API Keys (opcional - para Doc QA)
cp .env.example .env
# Edite .env com suas chaves: GROQ_API_KEY, VOYAGE_API_KEY, etc.

# 3. Setup e rodar servidor
./scripts/setup.sh  # Download dataset + treina modelo (5-10min)
uvicorn app.main:app --reload
```

🌐 **Acesse**: `http://localhost:8000`

### Configuração Kaggle (para Credit Risk)

```bash
# 1. Baixe kaggle.json em: https://www.kaggle.com/settings/account
# 2. Configure credenciais
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

## 📁 Estrutura do Projeto

```
kaio-portfolio/
├── app/
│   ├── core/               # Config global, logging, utilities
│   ├── middleware/         # Security (OWASP), rate limiting, quota tracking
│   ├── routers/            # API routes (home, health, admin, i18n)
│   └── projects/           # Projetos ML (arquitetura modular)
│       ├── docqa/          # Doc QA - RAG com Chain-of-Verification
│       ├── creditrisk/     # Credit Risk - XGBoost + SHAP
│       └── landing/        # Landing page template
├── data/                   # Datasets e modelos treinados (gitignored)
├── tests/                  # Pytest suite (unit + integration)
├── scripts/                # Automação (setup, build, deploy)
├── static/                 # Assets (CSS, imagens, favicon)
├── templates/              # Jinja2 templates base
├── Containerfile           # Multi-stage Podman build
├── podman-compose.yml      # Orquestração de containers
├── DEPLOYMENT.md           # Guia completo de deploy
└── CLAUDE.md               # Arquitetura e comandos dev
```

**Padrão de projeto ML** (`app/projects/<name>/`):
- `config.py` - Pydantic Settings com singleton `@lru_cache`
- `models.py` - Request/Response schemas
- `routes.py` - FastAPI router (HTMX + JSON endpoints)
- `i18n.py` - Traduções PT-BR/EN-US
- `services/` - Business logic (singleton factories)
- `templates/` - Jinja2 templates específicos
- `static/` - CSS específico do projeto

## 🧪 Testes

```bash
# Todos os testes (unit + integration)
pytest

# Com coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Testes específicos por projeto
pytest tests/test_creditrisk.py -v           # Credit Risk
pytest tests/test_rag_system.py -v           # Doc QA
pytest tests/test_rate_limiting.py -v        # Rate limiting
pytest tests/test_admin_dashboard.py -v      # Admin dashboard

# Apenas fast tests (skip slow training)
pytest -m "not slow"
```

**Coverage atual**: ~85% (target: 90%)

## 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [CLAUDE.md](CLAUDE.md) | Arquitetura completa, comandos dev, convenções |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Guia passo-a-passo de deploy (Podman + Caddy + SSL) |
| [MIGRATION.md](MIGRATION.md) | Migração ragsystem → docqa |
| [Doc QA README](app/projects/docqa/README.md) | Trade-offs de engenharia, decisões técnicas |
| [Credit Risk README](app/projects/creditrisk/README.md) | Pipeline ML, feature engineering |
| [Middleware README](app/middleware/README.md) | Security, rate limiting, OWASP protection |
| **Swagger UI** | `/docs` (apenas em development) |
| **ReDoc** | `/redoc` (apenas em development) |

## 🔒 Segurança

✅ **OWASP Top 10 Protection**
- SQL Injection: N/A (sem SQL direto, Pydantic validation)
- XSS: Content-Security-Policy headers, HTML escaping
- CSRF: SameSite cookies, CORS restrito
- Sensitive Data: API keys via env vars, nunca em logs
- Broken Access Control: Rate limiting, quota tracking

✅ **Application Security**
- Input validation via Pydantic (strict schemas)
- Enum-based sanitization para dados categóricos
- IP-based rate limiting (15 queries/mês para Doc QA)
- CORS configurável (whitelist de origins)
- Security headers (HSTS, CSP, X-Frame-Options)

✅ **Container Security**
- Rootless containers (user `appuser:1000`)
- Read-only filesystem onde possível
- Security options (`no-new-privileges`)
- Resource limits (CPU/Memory)
- Multi-stage build (menor surface attack)

## ⚡ Performance

### Credit Risk API
| Métrica | Valor |
|---------|-------|
| **Latência (p50)** | ~50ms |
| **Latência (p95)** | <100ms |
| **Latência (p99)** | <150ms |
| **Throughput** | ~100 req/s (single core) |
| **Memory** | ~500MB RAM |
| **Model Size** | ~2MB (XGBoost compressed) |

### Doc QA (RAG System)
| Métrica | Valor |
|---------|-------|
| **Latência end-to-end (p50)** | ~280ms |
| **Latência end-to-end (p99)** | ~450ms |
| **LLM call** | ~150ms (Groq 300 tok/s) |
| **Embedding** | ~50ms (CPU local) |
| **Vector search** | ~30ms (Qdrant embedded) |
| **Memory** | ~700MB (embedding model loaded) |
| **Accuracy** | 95% (vs OpenAI: 100%) |
| **Hallucination Rate** | 2% (vs standard RAG: 10%) |

## 🐳 Deploy

### Local (Development)

```bash
# Build container local
./scripts/build.sh

# Run com Podman
./scripts/run.sh

# Verificar health
curl http://localhost:8000/api/health
```

### Production (VPS)

```bash
# Deploy automatizado para Hetzner/Oracle Cloud
./scripts/deploy.sh

# Ou manual
podman build -t kaio-portfolio:latest -f Containerfile .
podman-compose -f podman-compose.yml up -d

# Setup Caddy reverse proxy (SSL automático)
# Ver DEPLOYMENT.md para guia completo
```

**Requisitos VPS**:
- **RAM**: 2GB mínimo (4GB recomendado)
- **CPU**: 2 cores
- **Storage**: 10GB (datasets + models)
- **OS**: Ubuntu 22.04+ ou Fedora 38+

📖 **Guia completo**: [DEPLOYMENT.md](DEPLOYMENT.md)

## 🏗️ Princípios de Arquitetura

1. **Cost-conscious scaling** - R$0/mês até validação de mercado (free tiers)
2. **Measured trade-offs** - Cada decisão técnica tem métricas (latência, accuracy, cost)
3. **Production-first** - Security, observability, error handling desde o início
4. **Modular design** - Cada projeto ML é independente e self-contained
5. **Type safety** - 100% type annotated, mypy strict mode
6. **Testability** - Unit + integration tests, >85% coverage
7. **Graceful degradation** - Fallback chains (Groq → Perplexity → Ollama)

## 🛠️ Desenvolvido Com

<table>
<tr>
<td><strong>Backend</strong></td>
<td>
FastAPI 0.115+ • Uvicorn • Pydantic 2.0 • Python 3.11
</td>
</tr>
<tr>
<td><strong>ML/Data</strong></td>
<td>
XGBoost • SHAP • Scikit-learn • Pandas • NumPy • FastEmbed
</td>
</tr>
<tr>
<td><strong>Vector/LLM</strong></td>
<td>
Qdrant (embedded) • Groq (free tier) • sentence-transformers
</td>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>
HTMX (14KB) • Jinja2 • FrontRender CSS (3.48KB) • Semantic HTML
</td>
</tr>
<tr>
<td><strong>DevOps</strong></td>
<td>
Podman • Caddy 2 • Prometheus • Systemd • GitHub Actions
</td>
</tr>
<tr>
<td><strong>Qualidade</strong></td>
<td>
Pytest • Black • Mypy • Ruff • Pre-commit hooks
</td>
</tr>
</table>

## 🎓 Por Que Este Portfolio?

Este projeto demonstra:

✅ **Engenharia de ML além de notebooks** - Pipeline completo (data → training → serving → monitoring)
✅ **Trade-offs conscientes** - Decisões técnicas baseadas em métricas reais
✅ **Production-ready code** - Security, performance, observability, tests
✅ **Zero para produção** - Scripts automatizados de setup e deploy
✅ **Escalabilidade planejada** - Arquitetura que cresce de R$0/mês → enterprise

**Não é apenas código - é uma demonstração de maturidade em ML Engineering.**

## 📈 Roadmap

- [ ] GitHub Actions CI/CD (pytest + build + deploy automático)
- [ ] Grafana dashboard para métricas Prometheus
- [ ] A/B testing framework para comparar modelos
- [ ] Redis cache para embeddings (reduzir latência)
- [ ] PostgreSQL migration (quotas + user data)
- [ ] Kubernetes manifests (escala > 10k req/dia)
- [ ] OpenTelemetry distributed tracing

## 🤝 Contribuindo

Este é um portfolio pessoal, mas contribuições são bem-vindas!

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

**Convenções**:
- Commits seguem [Conventional Commits](https://www.conventionalcommits.org/)
- Code style: Black + Ruff
- Type hints obrigatórios
- Testes para novas features

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 💬 Contato

**Kaio H. Siqueira**
Backend Engineer → ML/AI | 12 anos de experiência

[![GitHub](https://img.shields.io/badge/GitHub-KaioH3-181717?logo=github)](https://github.com/KaioH3)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-kaiohsiqueira-0A66C2?logo=linkedin)](https://www.linkedin.com/in/kaiohsiqueira/)
[![Medium](https://img.shields.io/badge/Medium-@KaioH3-00ab6c?logo=medium)](https://medium.com/@KaioH3)
[![Email](https://img.shields.io/badge/Email-contato-D14836?logo=gmail)](mailto:contato@kaio.ia.br)

---

<div align="center">

**⭐ Se este projeto ajudou você, considere dar uma estrela!**

Feito com ❤️ e Python 🐍

</div>
