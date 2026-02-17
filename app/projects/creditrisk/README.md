# Credit Risk Scoring API

Sistema de scoring de crédito production-ready usando **XGBoost + SHAP** para análise de risco com explicabilidade.

## Características

- **Dataset Real**: 97k+ aplicações do Kaggle (Credit Card Approval Prediction)
- **Modelo**: XGBoost Classifier com AUC-ROC > 0.75
- **Explicabilidade**: SHAP values para compliance regulatório
- **Interface**: HTMX (interativa) + JSON API (integrações)
- **i18n**: Suporte PT-BR e EN-US
- **Segurança**: Validação Pydantic, sanitização de inputs, type safety

## Arquitetura

```
app/projects/creditrisk/
 config.py                    # Configurações (Pydantic Settings)
 models.py                    # Request/Response models
 routes.py                    # FastAPI endpoints (HTMX + JSON)
 i18n.py                      # Traduções PT-BR + EN-US
 services/
    data_loader.py          # Carregamento do dataset
    feature_engineering.py   # Pipeline de features
    model_training.py        # Treinamento XGBoost
    risk_scoring.py          # Predição + SHAP (singleton)
 templates/
    creditrisk_index.html    # Interface HTMX
 static/
     creditrisk.css           # Estilos customizados
```

## Setup

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

Dependências principais:
- `xgboost>=2.0.0` - Modelo de ML
- `shap>=0.44.0` - Explicabilidade
- `scikit-learn>=1.4.0` - Feature engineering
- `pandas>=2.2.0` - Data manipulation
- `joblib>=1.3.0` - Model persistence

### 2. Download do Dataset

O dataset precisa ser baixado manualmente do Kaggle:

**URL**: https://www.kaggle.com/datasets/rikdifos/credit-card-approval-prediction

Após download, extrair para:
```
data/credit_card_approval/
 application_record.csv
 credit_record.csv
```

**Alternativa**: Use a API do Kaggle:
```bash
pip install kaggle
kaggle datasets download -d rikdifos/credit-card-approval-prediction
unzip credit-card-approval-prediction.zip -d data/credit_card_approval/
```

### 3. Treinar Modelo

```bash
python -m app.projects.creditrisk.services.model_training
```

Este comando irá:
1. Carregar e processar os dados (97k+ registros)
2. Criar features engineered (ratios, bins, encodings)
3. Treinar XGBoost com hyperparameters otimizados
4. Avaliar no test set (AUC-ROC, Precision, Recall, F1)
5. Salvar modelo e artefatos em `data/models/`

**Artefatos gerados**:
- `credit_risk_xgboost.pkl` - Modelo treinado
- `credit_risk_scaler.pkl` - StandardScaler
- `credit_risk_encoder.pkl` - LabelEncoders
- `credit_risk_features.json` - Feature names
- `metrics.json` - Métricas do modelo

### 4. Iniciar Servidor

```bash
uvicorn app.main:app --reload
```

Acesse:
- **Interface HTMX**: http://localhost:8000/credit-risk/
- **API JSON**: http://localhost:8000/credit-risk/api/score
- **Docs**: http://localhost:8000/docs (se ENV=development)
- **Health**: http://localhost:8000/credit-risk/health

## Uso

### Interface Web (HTMX)

1. Acesse http://localhost:8000/credit-risk/
2. Preencha o formulário com dados da aplicação
3. Clique em "Analisar Risco"
4. Veja resultado com:
   - Probabilidade de aprovação
   - Categoria de risco (Low/Medium/High/Very High)
   - Recomendação
   - Top 10 features SHAP

### API JSON

```bash
curl -X POST http://localhost:8000/credit-risk/api/score \
  -H "Content-Type: application/json" \
  -d '{
    "gender": "M",
    "age_years": 30,
    "family_status": "Married",
    "family_members": 3,
    "children_count": 1,
    "annual_income": 50000.0,
    "income_type": "Working",
    "employment_days": -1095,
    "education_level": "Higher education",
    "housing_type": "House / apartment",
    "has_car": true,
    "has_property": false,
    "has_work_phone": true,
    "has_phone": true,
    "has_email": true,
    "occupation_type": "Engineer"
  }'
```

**Response**:
```json
{
  "approval_probability": 0.78,
  "risk_category": "low",
  "recommended_action": " Aprovação recomendada (confiança: 78.0%)",
  "shap_top_features": {
    "ANNUAL_INCOME": 0.123,
    "AGE_YEARS": 0.089,
    "EMPLOYMENT_YEARS": 0.067,
    ...
  },
  "confidence": 0.85,
  "processing_time_ms": 45.2,
  "model_version": "1.0.0"
}
```

## Testes

```bash
# Testes básicos
pytest tests/test_creditrisk.py -v

# Testes de integração (requer modelo treinado)
pytest tests/test_creditrisk.py -v --run-integration

# Com coverage
pytest tests/test_creditrisk.py --cov=app/projects/creditrisk
```

##  Métricas Esperadas

Após treinamento, o modelo deve atingir:
- **AUC-ROC**: > 0.75
- **Accuracy**: > 0.70
- **Precision**: > 0.65
- **Recall**: > 0.60
- **Inference Time**: < 100ms

##  Segurança

-  **Validação de Inputs**: Pydantic models com type checking
-  **Sanitização**: Enums para campos categóricos (previne injection)
-  **Error Handling**: Try/catch em todos os endpoints
-  **Logging**: Structured logging para auditoria
-  **Type Safety**: Full type annotations

##  Internacionalização

Suporta PT-BR e EN-US via query param, cookie ou Accept-Language header:

```
http://localhost:8000/credit-risk/?lang=pt-BR
http://localhost:8000/credit-risk/?lang=en-US
```

##  Dataset

**Nome**: Credit Card Approval Prediction
**Fonte**: Kaggle
**Downloads**: 97k+
**Upvotes**: 913
**Registros**: ~430k aplicações
**Features**: 18 variáveis (demográficas, financeiras, profissionais)

**Target**: Aprovação de cartão de crédito (classificação binária)
- 1 = Good (sem atrasos > 60 dias)
- 0 = Bad (teve atrasos > 60 dias)

##  Tech Stack

- **ML**: XGBoost, Scikit-learn, SHAP, Pandas, NumPy
- **Backend**: FastAPI, Pydantic, Uvicorn
- **Frontend**: HTMX, Jinja2, FrontRender CSS
- **Persistence**: Joblib (model serialization)
- **Testing**: Pytest, HTTPX

##  Licença

MIT License - Use livremente para portfolio e projetos comerciais.

## Autor

**Kaio H. Siqueira** - ML Engineer
Portfolio: https://github.com/kaioH3
