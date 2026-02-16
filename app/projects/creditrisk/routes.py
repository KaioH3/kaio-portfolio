"""Credit Risk Scoring API Routes - HTMX + JSON endpoints"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
import logging
from typing import Optional

from .models import (
    LoanApplication, RiskPrediction, HealthCheck,
    ErrorResponse, EducationLevel, HousingType,
    IncomeType, FamilyStatus
)
from .services.risk_scoring import get_risk_scoring
from .config import get_credit_risk_config
from .i18n import t, get_language_from_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credit-risk", tags=["Credit Risk"])

# Templates com fallback para base
templates = Jinja2Templates(
    directory=[
        str(Path(__file__).parent / "templates"),
        str(Path(__file__).resolve().parent.parent.parent.parent / "templates"),
    ]
)

# Adicionar função de tradução ao contexto do Jinja2
templates.env.globals["t"] = t


@router.get("/", response_class=HTMLResponse)
async def credit_risk_index(request: Request):
    """
    Interface principal do Credit Risk Scoring
    Renderiza formulário HTMX para análise de risco
    """
    lang = get_language_from_request(request)
    config = get_credit_risk_config()

    # Passar enums para o template
    context = {
        "request": request,
        "lang": lang,
        "education_levels": [e.value for e in EducationLevel],
        "housing_types": [h.value for h in HousingType],
        "income_types": [i.value for i in IncomeType],
        "family_statuses": [f.value for f in FamilyStatus],
    }

    return templates.TemplateResponse("creditrisk_index.html", context)


@router.post("/score", response_class=HTMLResponse)
async def score_htmx(
    request: Request,
    # Demographic
    gender: str = Form(...),
    age_years: int = Form(...),
    # Family
    family_status: str = Form(...),
    family_members: int = Form(...),
    children_count: int = Form(0),
    # Financial
    annual_income: float = Form(...),
    income_type: str = Form(...),
    # Employment
    employment_days: int = Form(...),
    # Education & Housing
    education_level: str = Form(...),
    housing_type: str = Form(...),
    # Properties
    has_car: bool = Form(False),
    has_property: bool = Form(False),
    has_work_phone: bool = Form(False),
    has_phone: bool = Form(False),
    has_email: bool = Form(False),
    # Optional
    occupation_type: Optional[str] = Form(None),
):
    """
    HTMX endpoint - Retorna HTML fragment com resultado da análise

    Security:
    - Input validation via Pydantic
    - Sanitização de inputs via Form validators
    - Rate limiting (se implementado)
    """
    lang = get_language_from_request(request)

    try:
        # Construir LoanApplication (validação automática via Pydantic)
        application = LoanApplication(
            gender=gender,
            age_years=age_years,
            family_status=FamilyStatus(family_status),
            family_members=family_members,
            children_count=children_count,
            annual_income=annual_income,
            income_type=IncomeType(income_type),
            employment_days=employment_days,
            education_level=EducationLevel(education_level),
            housing_type=HousingType(housing_type),
            has_car=has_car,
            has_property=has_property,
            has_work_phone=has_work_phone,
            has_phone=has_phone,
            has_email=has_email,
            occupation_type=occupation_type or "Unknown"
        )

        # Score de risco
        scorer = get_risk_scoring()
        prediction = await scorer.score(application)

        # Renderizar resultado
        return _render_prediction_result(prediction, lang)

    except ValueError as e:
        # Erro de validação
        logger.warning(f"Validation error: {e}")
        error_msg = t("error_invalid_input", lang, detail=str(e))
        return f'<div class="result error">{error_msg}</div>'

    except Exception as e:
        # Erro interno
        logger.error(f"Prediction error: {e}", exc_info=True)
        error_msg = t("error_prediction", lang, error=str(e))
        return f'<div class="result error">{error_msg}</div>'


@router.post("/api/score", response_model=RiskPrediction)
async def score_api(application: LoanApplication) -> RiskPrediction:
    """
    JSON API endpoint - Retorna predição em JSON

    Security:
    - Input validation via Pydantic model
    - Type safety
    - Automatic OpenAPI documentation

    Usage:
        curl -X POST http://localhost:8000/credit-risk/api/score \\
            -H "Content-Type: application/json" \\
            -d '{"gender": "M", "age_years": 30, ...}'
    """
    try:
        scorer = get_risk_scoring()
        prediction = await scorer.score(application)
        return prediction

    except Exception as e:
        logger.error(f"API prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint
    Verifica se modelo e artefatos estão carregados
    """
    try:
        scorer = get_risk_scoring()
        status = scorer.get_health_status()

        return HealthCheck(**status)

    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")


@router.get("/api/info")
async def get_info():
    """
    Informações sobre o modelo e dataset
    """
    config = get_credit_risk_config()

    return {
        "model": {
            "type": "XGBoost Classifier",
            "version": "1.0.0",
            "hyperparameters": {
                "max_depth": config.XGBOOST_MAX_DEPTH,
                "learning_rate": config.XGBOOST_LEARNING_RATE,
                "n_estimators": config.XGBOOST_N_ESTIMATORS,
            }
        },
        "dataset": {
            "name": "Credit Card Approval Prediction",
            "source": "Kaggle",
            "url": "https://www.kaggle.com/datasets/rikdifos/credit-card-approval-prediction",
            "downloads": "97k+",
            "features": 18
        },
        "explainability": {
            "method": "SHAP TreeExplainer",
            "top_features": config.SHAP_TOP_FEATURES
        },
        "performance": {
            "min_auc_threshold": config.MIN_AUC_THRESHOLD,
            "target_latency_ms": 100
        }
    }


# === Helper Functions ===

def _render_prediction_result(prediction: RiskPrediction, lang: str) -> str:
    """
    Renderiza resultado da predição como HTML fragment

    Security:
    - Escaping automático via f-strings
    - Sem user-generated content direto no HTML
    """
    # Mapear categoria de risco para tradução
    risk_translations = {
        "low": t("risk_low", lang),
        "medium": t("risk_medium", lang),
        "high": t("risk_high", lang),
        "very_high": t("risk_very_high", lang),
    }

    risk_label = risk_translations.get(prediction.risk_category.value, prediction.risk_category.value)

    # CSS class baseada no risco
    risk_class = f"risk-{prediction.risk_category.value.replace('_', '-')}"

    # Renderizar SHAP features
    shap_html = ""
    if prediction.shap_top_features:
        shap_items = []
        for feature, value in list(prediction.shap_top_features.items())[:5]:
            impact_class = "positive" if value > 0 else "negative"
            impact_label = t("shap_positive_impact", lang) if value > 0 else t("shap_negative_impact", lang)
            shap_items.append(
                f'<li class="shap-item {impact_class}">'
                f'<span class="feature-name">{feature}</span>: '
                f'<span class="shap-value">{value:.4f}</span> '
                f'<span class="impact-label">({impact_label})</span>'
                f'</li>'
            )
        shap_html = f'''
        <div class="shap-section">
            <h4>{t("shap_title", lang)}</h4>
            <p class="shap-subtitle">{t("shap_subtitle", lang)}</p>
            <ul class="shap-list">{"".join(shap_items)}</ul>
        </div>
        '''
    else:
        shap_html = f'<p class="shap-warning">{t("shap_no_data", lang)}</p>'

    # HTML do resultado
    html = f'''
    <div class="result success {risk_class}">
        <h3>{t("results_title", lang)}</h3>

        <div class="result-grid">
            <div class="result-item">
                <label>{t("results_approval_probability", lang)}</label>
                <div class="probability-bar">
                    <div class="probability-fill" style="width: {prediction.approval_probability*100}%"></div>
                    <span class="probability-text">{prediction.approval_probability*100:.1f}%</span>
                </div>
            </div>

            <div class="result-item">
                <label>{t("results_risk_category", lang)}</label>
                <div class="risk-badge {risk_class}">{risk_label}</div>
            </div>

            <div class="result-item">
                <label>{t("results_recommendation", lang)}</label>
                <div class="recommendation">{prediction.recommended_action}</div>
            </div>

            <div class="result-item">
                <label>{t("results_confidence", lang)}</label>
                <div class="confidence">{prediction.confidence*100:.1f}%</div>
            </div>

            <div class="result-item">
                <label>{t("results_processing_time", lang)}</label>
                <div class="processing-time">{prediction.processing_time_ms:.1f}ms</div>
            </div>
        </div>

        {shap_html}
    </div>
    '''

    return html
