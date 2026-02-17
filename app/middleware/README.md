# Middleware Layer - Rate Limiting & Quota Tracking

Sistema de proteção em 3 camadas para APIs externas (Voyage AI, Qdrant Cloud, Groq).

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    3 Camadas de Proteção                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Camada 1: IP-Based Rate Limiting (Por Usuário)             │
│  ├─ Arquivo: app/projects/docqa/services/rate_limiter.py    │
│  ├─ Escopo: Usuários finais (/docqa/query)                  │
│  ├─ Limite: 15 queries/IP/mês                               │
│  └─ Storage: ./data/rate_limits.json                        │
│                                                               │
│  Camada 2: Global API Rate Limiting (Horário)               │
│  ├─ Arquivo: app/middleware/rate_limit.py                   │
│  ├─ Escopo: Proteção de APIs externas                       │
│  ├─ Recursos rastreados:                                    │
│  │   ├─ voyage_embeddings: 1000 calls/hora                  │
│  │   ├─ qdrant_writes: 100 upserts/hora                     │
│  │   └─ groq_queries: 500 queries/hora                      │
│  └─ Storage: In-memory (reset automático)                   │
│                                                               │
│  Camada 3: Quota Tracking (Cumulativo)                      │
│  ├─ Arquivo: app/middleware/quota_tracker.py                │
│  ├─ Escopo: Monitoramento lifetime                          │
│  ├─ Métricas:                                               │
│  │   ├─ Voyage AI: Total tokens vs 200M                     │
│  │   ├─ Qdrant: Total docs vs 400K (1GB)                    │
│  │   └─ Groq: Total tokens lifetime                         │
│  └─ Persistência: ./data/quota_usage.json                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## rate_limit.py - Global Rate Limiter

### Funcionalidade

Protege APIs externas contra abuse com limites por hora que resetam automaticamente.

### Uso

```python
from app.middleware.rate_limit import get_global_rate_limiter

def embed_documents(texts):
    limiter = get_global_rate_limiter()

    # Check BEFORE calling external API
    if not limiter.check_and_increment("voyage_embeddings"):
        raise HTTPException(
            status_code=429,
            detail="Voyage AI rate limit exceeded. Try again in 1 hour."
        )

    # Proceed with API call
    result = voyage_client.embed(texts)
    return result
```

### Limites Configurados

| Recurso             | Limite/Hora | Proteção                          |
|---------------------|-------------|-----------------------------------|
| `voyage_embeddings` | 1000        | Evita esgotar 200M tokens         |
| `qdrant_writes`     | 100         | Evita spam de indexação           |
| `groq_queries`      | 500         | Respeita free tier                |

### Thread Safety

Thread-safe com `threading.Lock`

### API

```python
class GlobalRateLimiter:
    def check_and_increment(resource: ResourceType) -> bool:
        """Verifica limite e incrementa. Retorna False se excedeu."""

    def get_stats() -> Dict:
        """Retorna estatísticas para dashboard."""
```

---

## quota_tracker.py - Quota Tracker

### Funcionalidade

Rastreia uso **cumulativo** (lifetime) de quotas das APIs externas. Persiste em JSON para sobreviver restarts.

### Uso

```python
from app.middleware.quota_tracker import get_quota_tracker

def embed_documents(texts):
    # ... rate limit check ...
    result = voyage_client.embed(texts)

    # Track usage AFTER successful call
    tracker = get_quota_tracker()
    estimated_tokens = sum(len(t.split()) * 1.3 for t in texts)
    tracker.record_voyage_usage(int(estimated_tokens))

    return result
```

### Métricas Rastreadas

| API          | Métrica              | Limite         | Arquivo                     |
|--------------|----------------------|----------------|-----------------------------|
| Voyage AI    | Total tokens         | 200M (one-time)| `voyage_tokens`             |
| Qdrant Cloud | Total documentos     | 400K (1GB)     | `qdrant_documents`          |
| Groq         | Total tokens         | Ilimitado*     | `groq_tokens`               |

*Daily limit de 100K tokens, mas não aplicado no tracker

### Persistência

Dados salvos em `./data/quota_usage.json`:

```json
{
  "voyage_tokens": 1234567,
  "qdrant_documents": 850,
  "groq_tokens": 45230
}
```

### API

```python
class QuotaTracker:
    def record_voyage_usage(num_tokens: int)
    def record_qdrant_documents(num_docs: int)
    def record_groq_tokens(num_tokens: int)
    def get_usage_summary() -> Dict
```

---

## Dashboard Administrativo

### Endpoint

```
GET /admin/quotas
```

### Resposta

```json
{
  "rate_limits_hourly": {
    "voyage_embeddings": {
      "calls": 45,
      "max": 1000,
      "reset_in": 2341
    },
    "qdrant_writes": {
      "calls": 12,
      "max": 100,
      "reset_in": 2341
    },
    "groq_queries": {
      "calls": 23,
      "max": 500,
      "reset_in": 2341
    }
  },
  "quota_usage_cumulative": {
    "voyage_ai": {
      "tokens_used": 123456,
      "tokens_limit": 200000000,
      "percentage": 0.06
    },
    "qdrant": {
      "documents": 850,
      "storage_mb": 2.08,
      "limit_gb": 1.0,
      "percentage": 0.2
    },
    "groq": {
      "tokens_used_lifetime": 45230,
      "daily_limit": 100000
    }
  },
  "qdrant_realtime": {
    "points_count": 2550,
    "vectors_count": 2550,
    "status": "green"
  },
  "endpoints": {
    "voyage_embeddings": "/docqa/upload (document indexing)",
    "qdrant_writes": "/docqa/upload (vector storage)",
    "groq_queries": "/docqa/query (LLM generation)"
  }
}
```

### Uso

```bash
# Ver quotas em tempo real
curl http://localhost:8000/admin/quotas | jq .

# Monitorar continuamente
watch -n 5 'curl -s http://localhost:8000/admin/quotas | jq .quota_usage_cumulative'
```

---

## Testes

```bash
# Testes unitários (11 testes)
pytest tests/test_rate_limiting.py -v

# Testes de integração (7 testes)
pytest tests/test_rate_limiting_integration.py -v

# Todos os testes
pytest tests/test_rate_limiting*.py -v
```

### Cobertura

- Rate limiting funciona (permite até limite, bloqueia depois)
- Reset automático após 1 hora
- Thread safety (concurrent access)
- Quota tracking persiste entre restarts
- Dashboard retorna dados corretos
- Error handling (arquivo corrompido, etc)

---

## Benefícios para Recrutadores

### Demonstra

1. **Arquitetura Defensiva**
   - Proteção em múltiplas camadas
   - Fail-safe contra abuse
   - Production-ready mindset

2. **Monitoramento Proativo**
   - Visibilidade em tempo real
   - Rastreamento cumulativo
   - Dashboard para troubleshooting

3. **Custo-consciência**
   - Entende limites de free tiers
   - Implementa proteções antes de problemas
   - Trade-offs bem documentados

4. **Engineering Best Practices**
   - Singleton pattern consistente
   - Thread-safe operations
   - Persistência de dados críticos
   - 100% test coverage

---

## Próximos Passos (Opcional)

- [ ] Prometheus metrics integration
- [ ] Email alerts quando quota > 80%
- [ ] Grafana dashboard com histórico
- [ ] Admin autenticação (HTTP Basic Auth)
- [ ] Rate limit configurável via .env
