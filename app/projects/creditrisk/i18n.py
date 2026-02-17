"""
Internationalization (i18n) Module for Credit Risk Scoring
Supports: PT-BR (Brazilian Portuguese) + EN-US (English)
"""

from typing import Literal, Dict, Any
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

Language = Literal["pt-BR", "en-US"]
DEFAULT_LANGUAGE: Language = "en-US"

TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    # === PAGE TITLES ===
    "page_title": {
        "pt-BR": "API de Score de Crédito",
        "en-US": "Credit Risk Scoring API"
    },
    "page_subtitle": {
        "pt-BR": "Análise de Risco de Crédito com XGBoost e Explicações SHAP",
        "en-US": "Credit Risk Analysis with XGBoost and SHAP Explanations"
    },
    "page_description": {
        "pt-BR": "Sistema de pontuação de crédito baseado em 97k+ aplicações reais do Kaggle. Utiliza XGBoost para predição e SHAP para explicabilidade, seguindo boas práticas de conformidade regulatória.",
        "en-US": "Credit scoring system based on 97k+ real applications from Kaggle. Uses XGBoost for prediction and SHAP for explainability, following regulatory compliance best practices."
    },

    # === FORM SECTION ===
    "form_title": {
        "pt-BR": "Dados da Aplicação",
        "en-US": "Application Data"
    },
    "form_demographic_section": {
        "pt-BR": "Informações Demográficas",
        "en-US": "Demographic Information"
    },
    "form_financial_section": {
        "pt-BR": "Informações Financeiras",
        "en-US": "Financial Information"
    },
    "form_employment_section": {
        "pt-BR": "Informações Profissionais",
        "en-US": "Employment Information"
    },
    "form_additional_section": {
        "pt-BR": "Informações Adicionais",
        "en-US": "Additional Information"
    },

    # === FORM FIELDS ===
    "field_gender": {
        "pt-BR": "Gênero:",
        "en-US": "Gender:"
    },
    "field_age": {
        "pt-BR": "Idade (anos):",
        "en-US": "Age (years):"
    },
    "field_family_status": {
        "pt-BR": "Status Familiar:",
        "en-US": "Family Status:"
    },
    "field_family_members": {
        "pt-BR": "Membros da Família:",
        "en-US": "Family Members:"
    },
    "field_children": {
        "pt-BR": "Número de Filhos:",
        "en-US": "Number of Children:"
    },
    "field_annual_income": {
        "pt-BR": "Renda Anual (R$):",
        "en-US": "Annual Income ($):"
    },
    "field_income_type": {
        "pt-BR": "Tipo de Renda:",
        "en-US": "Income Type:"
    },
    "field_employment_days": {
        "pt-BR": "Dias de Emprego (negativo):",
        "en-US": "Employment Days (negative):"
    },
    "employment_days_help": {
        "pt-BR": "Formato: negativo (ex: -1095 = 3 anos)",
        "en-US": "Format: negative (e.g., -1095 = 3 years)"
    },
    "field_education": {
        "pt-BR": "Nível Educacional:",
        "en-US": "Education Level:"
    },
    "field_housing": {
        "pt-BR": "Tipo de Moradia:",
        "en-US": "Housing Type:"
    },
    "field_occupation": {
        "pt-BR": "Ocupação:",
        "en-US": "Occupation:"
    },
    "field_has_car": {
        "pt-BR": "Possui Carro",
        "en-US": "Has Car"
    },
    "field_has_property": {
        "pt-BR": "Possui Imóvel",
        "en-US": "Has Property"
    },
    "field_has_phone": {
        "pt-BR": "Possui Telefone",
        "en-US": "Has Phone"
    },
    "field_has_work_phone": {
        "pt-BR": "Possui Telefone Comercial",
        "en-US": "Has Work Phone"
    },
    "field_has_email": {
        "pt-BR": "Possui Email",
        "en-US": "Has Email"
    },

    # === BUTTONS ===
    "analyze_button": {
        "pt-BR": "Analisar Risco",
        "en-US": "Analyze Risk"
    },
    "clear_button": {
        "pt-BR": "Limpar",
        "en-US": "Clear"
    },
    "analyzing_indicator": {
        "pt-BR": "Analisando...",
        "en-US": "Analyzing..."
    },

    # === RISK CATEGORIES ===
    "risk_low": {
        "pt-BR": "Baixo Risco",
        "en-US": "Low Risk"
    },
    "risk_medium": {
        "pt-BR": "Risco Médio",
        "en-US": "Medium Risk"
    },
    "risk_high": {
        "pt-BR": "Alto Risco",
        "en-US": "High Risk"
    },
    "risk_very_high": {
        "pt-BR": "Risco Muito Alto",
        "en-US": "Very High Risk"
    },

    # === RESULTS ===
    "results_title": {
        "pt-BR": "Resultado da Análise",
        "en-US": "Analysis Result"
    },
    "results_approval_probability": {
        "pt-BR": "Probabilidade de Aprovação:",
        "en-US": "Approval Probability:"
    },
    "results_risk_category": {
        "pt-BR": "Categoria de Risco:",
        "en-US": "Risk Category:"
    },
    "results_recommendation": {
        "pt-BR": "Recomendação:",
        "en-US": "Recommendation:"
    },
    "results_confidence": {
        "pt-BR": "Confiança do Modelo:",
        "en-US": "Model Confidence:"
    },
    "results_processing_time": {
        "pt-BR": "Tempo de Processamento:",
        "en-US": "Processing Time:"
    },

    # === SHAP EXPLANATIONS ===
    "shap_title": {
        "pt-BR": "Fatores que Influenciaram a Decisão (SHAP)",
        "en-US": "Factors Influencing Decision (SHAP)"
    },
    "shap_subtitle": {
        "pt-BR": "Variáveis com maior impacto na predição:",
        "en-US": "Variables with highest impact on prediction:"
    },
    "shap_positive_impact": {
        "pt-BR": "Impacto Positivo (aumenta aprovação)",
        "en-US": "Positive Impact (increases approval)"
    },
    "shap_negative_impact": {
        "pt-BR": "Impacto Negativo (reduz aprovação)",
        "en-US": "Negative Impact (reduces approval)"
    },
    "shap_no_data": {
        "pt-BR": "Explicações SHAP não disponíveis (instale: pip install shap)",
        "en-US": "SHAP explanations not available (install: pip install shap)"
    },

    # === ERRORS ===
    "error_title": {
        "pt-BR": "Erro",
        "en-US": "Error"
    },
    "error_prediction": {
        "pt-BR": "Erro ao fazer predição: {error}",
        "en-US": "Error making prediction: {error}"
    },
    "error_invalid_input": {
        "pt-BR": "Dados inválidos: {detail}",
        "en-US": "Invalid input: {detail}"
    },
    "error_model_not_loaded": {
        "pt-BR": "Modelo não carregado. Execute o treinamento primeiro.",
        "en-US": "Model not loaded. Run training first."
    },

    # === INFO SECTION ===
    "info_title": {
        "pt-BR": "Sobre o Sistema",
        "en-US": "About the System"
    },
    "info_description": {
        "pt-BR": "Preencha o formulário à esquerda para obter uma análise de risco de crédito completa com explicabilidade SHAP.",
        "en-US": "Fill out the form on the left to get a complete credit risk analysis with SHAP explainability."
    },
    "info_dataset": {
        "pt-BR": "Dataset: Credit Card Approval (Kaggle - 97k downloads)",
        "en-US": "Dataset: Credit Card Approval (Kaggle - 97k downloads)"
    },
    "info_model": {
        "pt-BR": "Modelo: XGBoost Classifier",
        "en-US": "Model: XGBoost Classifier"
    },
    "info_features": {
        "pt-BR": "Features: {count} variáveis (demográficas, financeiras, profissionais)",
        "en-US": "Features: {count} variables (demographic, financial, employment)"
    },
    "info_accuracy": {
        "pt-BR": "Métricas: AUC-ROC > 0.75, Precision, Recall",
        "en-US": "Metrics: AUC-ROC > 0.75, Precision, Recall"
    },
    "info_explainability": {
        "pt-BR": "Explicabilidade: SHAP values para compliance regulatório",
        "en-US": "Explainability: SHAP values for regulatory compliance"
    },

    # === LANGUAGE SELECTOR ===
    "language_pt_br": {
        "pt-BR": "Português",
        "en-US": "Portuguese"
    },
    "language_en_us": {
        "pt-BR": "Inglês",
        "en-US": "English"
    },

    # === FOOTER ===
    "footer_tech_stack": {
        "pt-BR": "Desenvolvido com XGBoost + SHAP + FastAPI + Scikit-learn",
        "en-US": "Built with XGBoost + SHAP + FastAPI + Scikit-learn"
    },
    "footer_dataset": {
        "pt-BR": "Dataset: 97k+ aplicações reais (Kaggle)",
        "en-US": "Dataset: 97k+ real applications (Kaggle)"
    },
    "footer_performance": {
        "pt-BR": "Inference: <100ms | AUC-ROC: >0.75",
        "en-US": "Inference: <100ms | AUC-ROC: >0.75"
    },
}


def t(key: str, lang: Language = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get translated string with optional parameter substitution"""
    try:
        translations = TRANSLATIONS.get(key, {})
        text = translations.get(lang)

        if text is None:
            text = translations.get(DEFAULT_LANGUAGE, key)
            logger.warning(f"Translation missing: key={key}, lang={lang}")

        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing parameter in translation: {e}")
                return text

        return text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return key


def get_language_from_request(request: Request) -> Language:
    """Detect language from request (query param > cookie > Accept-Language header)"""
    # 1. Check query parameter
    lang_param = request.query_params.get("lang")
    if lang_param in ["pt-BR", "en-US"]:
        return lang_param  # type: ignore

    # 2. Check cookie
    lang_cookie = request.cookies.get("lang")
    if lang_cookie in ["pt-BR", "en-US"]:
        return lang_cookie  # type: ignore

    # 3. Check Accept-Language header
    accept_lang = request.headers.get("accept-language", "")
    if "pt" in accept_lang.lower():
        return "pt-BR"

    return DEFAULT_LANGUAGE
