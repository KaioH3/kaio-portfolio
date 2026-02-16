# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI-based ML Engineer portfolio (Python 3.11) with a production-ready RAG Document Intelligence system. Uses HTMX for frontend interactivity instead of a JS framework. Primary language in code/docs is Brazilian Portuguese.

## Commands

```bash
# Run dev server
source venv/bin/activate
uvicorn app.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_rag_system.py -v

# Run tests with coverage for RAG module
pytest tests/test_rag_system.py --cov=app/projects/ragsystem

# Setup Credit Risk project (download dataset + train model)
./scripts/setup_creditrisk.sh

# Train Credit Risk model manually
python -m app.projects.creditrisk.services.model_training

# Run Credit Risk tests
pytest tests/test_creditrisk.py -v

# Build container
podman build -t kaio-portfolio-api:latest -f containerfiles/Containerfile.api .

# Run with compose
podman-compose -f deploy/podman-compose.yml up -d
```

## Architecture

**App entry point**: `app/main.py` creates the FastAPI app, mounts middleware (CORS, GZip), static files, and includes routers.

**Configuration**: Environment-driven via Pydantic Settings. `app/core/config.py` handles global settings (loaded from `.env`). `app/projects/ragsystem/config.py` handles RAG-specific settings. Both use `@lru_cache` singletons.

**Router registration pattern**: Routers are included in `app/main.py` via `app.include_router()`:
- `app/routers/home.py` — Landing page (`/`)
- `app/routers/health.py` — Health probes (`/api/health`, `/api/ready`)
- `app/projects/ragsystem/routes.py` — RAG system (`/rag-system/`)
- `app/projects/creditrisk/routes.py` — Credit Risk Scoring (`/credit-risk/`)

**Projects structure**: Each project lives under `app/projects/<name>/` with its own config, models, routes, services, and templates. Currently: `ragsystem` (active) and `creditrisk` (active).

**RAG service layer** (`app/projects/ragsystem/services/`):
- `embeddings.py` — FastEmbed wrapper (CPU-only, paraphrase-multilingual-MiniLM-L12-v2)
- `vector_store.py` — Qdrant embedded client
- `document_processor.py` — PDF/TXT chunking (400-token chunks)
- `retrieval.py` — Hybrid search (semantic + BM25 reranking)
- `generation.py` — Multi-provider LLM with fallback chain: Groq -> Perplexity -> OpenAI
- `verification.py` — Chain-of-Verification to reduce hallucinations

- `rate_limiter.py` — IP-based monthly query limit (persisted to JSON)

Services use a singleton pattern with `get_*_service()` factory functions. Document processor uses SHA-256 content hashing for deduplication.

**Credit Risk service layer** (`app/projects/creditrisk/services/`):
- `data_loader.py` — Loads and merges Kaggle CSV datasets (97k+ applications)
- `feature_engineering.py` — Feature pipeline (ratios, encoding, scaling) with singleton pattern
- `model_training.py` — XGBoost training with hyperparameter tuning
- `risk_scoring.py` — Prediction + SHAP explanations (singleton, lazy loading)

Credit Risk uses same patterns as RAG: Pydantic config, singleton services, i18n support, HTMX + JSON endpoints. Model artifacts saved in `data/models/`. Requires manual dataset download from Kaggle (see `app/projects/creditrisk/README.md`).

**i18n**: Both projects provide PT-BR and EN-US translations via `i18n.py`. Detection order: query param `?lang=` -> cookie -> Accept-Language header -> default `en-US`.

**Templates**: Jinja2 templates in `templates/` (global) and `app/projects/ragsystem/templates/` (RAG-specific). Base layout at `templates/base.html`.

**Static assets**: `static/css/`, `static/js/`, `static/images/`. Uses FrontRender Design System (custom CSS, no build step).

## Key Environment Variables

```
GROQ_API_KEY          # Primary LLM provider (free tier)
PERPLEXITY_API_KEY    # Backup LLM
OPENAI_API_KEY        # Fallback LLM
LLM_PROVIDER          # groq|perplexity|openai
RATE_LIMIT_MONTHLY    # Per-IP monthly query cap (default: 15)
ENV                   # development|production (controls /docs visibility)
```

## Conventions

- All I/O operations use async/await
- Full type annotations with Pydantic models for API request/response validation
- Structured logging via `app/core/logging_config.py` (JSON in production, text in dev)
- Docs endpoints (`/docs`, `/redoc`) are only exposed when `ENV=development`
- Prometheus metrics exposed at `/metrics` when `PROMETHEUS_ENABLED=True`
- Container runs as non-root user (appuser:1000)

## Frontend Guidelines

- Use semantic HTML for accessibility and SEO
- CSS uses variables for colors, fonts, and spacing (FrontRender design system)
- HTMX handles dynamic interactions (no JS framework)
- Ensure keyboard navigation and ARIA attributes where appropriate
- Maintain good color contrast ratios
