# Contributing to Kaio Portfolio

Obrigado por considerar contribuir! 🎉

## 📋 Código de Conduta

Este projeto segue o [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). Ao participar, você deve seguir este código.

## 🚀 Como Contribuir

### Reportar Bugs

Antes de criar uma issue:
1. Verifique se já existe uma issue similar
2. Use a template de bug report
3. Inclua informações de ambiente (Python version, OS, etc.)

### Sugerir Features

1. Abra uma issue descrevendo a feature
2. Explique o problema que ela resolve
3. Considere implementá-la você mesmo (PRs são bem-vindos!)

### Pull Requests

1. **Fork** o repositório
2. **Clone** seu fork localmente
   ```bash
   git clone https://github.com/seu-usuario/kaio-portfolio.git
   cd kaio-portfolio
   ```

3. **Configure** o ambiente de desenvolvimento
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dev dependencies
   ```

4. **Crie uma branch** para sua feature
   ```bash
   git checkout -b feature/nome-da-feature
   ```

5. **Faça suas mudanças** seguindo as convenções do projeto

6. **Teste** suas mudanças
   ```bash
   # Rodar testes
   pytest

   # Verificar types
   mypy app/

   # Formatar código
   black app/ tests/
   ruff check app/ tests/
   ```

7. **Commit** usando [Conventional Commits](https://www.conventionalcommits.org/)
   ```bash
   git commit -m "feat: adiciona feature X"
   # Tipos: feat, fix, docs, style, refactor, test, chore
   ```

8. **Push** para seu fork
   ```bash
   git push origin feature/nome-da-feature
   ```

9. **Abra um Pull Request** no GitHub

## 📝 Convenções de Código

### Python Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff (replaces flake8, isort, pylint)
- **Type Checker**: Mypy (strict mode)
- **Docstrings**: Google style

```python
from typing import Optional

def calculate_risk_score(
    age: int,
    income: float,
    credit_history: Optional[str] = None
) -> float:
    """
    Calculate credit risk score based on applicant data.

    Args:
        age: Applicant age in years
        income: Annual income in BRL
        credit_history: Optional credit history ("good" | "poor" | None)

    Returns:
        Risk score between 0.0 (low risk) and 1.0 (high risk)

    Raises:
        ValueError: If age < 18 or income <= 0
    """
    if age < 18:
        raise ValueError("Age must be >= 18")
    # ...
```

### Commit Messages

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: Nova feature
- `fix`: Bug fix
- `docs`: Documentação
- `style`: Formatação (sem mudança lógica)
- `refactor`: Refatoração
- `test`: Adicionar/modificar testes
- `chore`: Tarefas de manutenção

**Exemplos**:
```
feat(creditrisk): add SHAP explanation endpoint

Implement POST /credit-risk/explain endpoint that returns
SHAP values for model interpretability.

Closes #42
```

```
fix(docqa): resolve rate limiting race condition

Fixes concurrent access to quota tracker JSON file by
adding file lock mechanism.

Fixes #38
```

### Project Structure

Novos projetos ML devem seguir o padrão:

```
app/projects/<name>/
├── config.py           # Pydantic Settings singleton
├── models.py           # Request/Response schemas
├── routes.py           # FastAPI router
├── i18n.py             # PT-BR + EN-US translations
├── services/           # Business logic
│   ├── __init__.py
│   └── <service>.py    # Singleton factories (get_*_service)
├── templates/          # Jinja2 templates
└── README.md           # Project-specific docs
```

### Testing

- **Unit tests**: Testa lógica isolada
- **Integration tests**: Testa API endpoints
- **Coverage target**: >85%

```python
# tests/test_creditrisk.py
import pytest
from app.projects.creditrisk.services.risk_scoring import get_risk_scoring_service

def test_predict_low_risk():
    """Test prediction for low-risk applicant."""
    service = get_risk_scoring_service()
    data = {
        "age": 35,
        "income": 5000.0,
        "credit_history": "good"
    }
    result = service.predict(data)
    assert result["risk_score"] < 0.3
    assert result["decision"] == "approved"
```

## 🔧 Desenvolvimento

### Setup Completo

```bash
# 1. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Configurar pre-commit hooks
pre-commit install

# 3. Setup datasets (para Credit Risk)
./scripts/setup.sh

# 4. Rodar servidor dev
uvicorn app.main:app --reload --log-level debug
```

### Ferramentas Úteis

```bash
# Auto-format código
black app/ tests/
ruff check --fix app/ tests/

# Type check
mypy app/

# Testes com coverage
pytest --cov=app --cov-report=html
# Abra htmlcov/index.html no browser

# Rodar apenas testes rápidos
pytest -m "not slow"

# Profile performance
python -m cProfile -o profile.stats app/main.py
```

## 📚 Recursos

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [HTMX Documentation](https://htmx.org/docs/)

## ❓ Dúvidas?

- Abra uma [Discussion](https://github.com/KaioH3/kaio-portfolio/discussions)
- Entre em contato: contato@kaio.ia.br

---

**Obrigado por contribuir! 🚀**
