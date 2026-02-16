"""
Internationalization (i18n) Module for Home Page
Supports: PT-BR (Brazilian Portuguese) + EN-US (English)
"""

from typing import Literal, Dict, Any
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

Language = Literal["pt-BR", "en-US"]
DEFAULT_LANGUAGE: Language = "pt-BR"

TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    # === HERO SECTION ===
    "hero_title": {
        "pt-BR": "Kaio H. Siqueira",
        "en-US": "Kaio H. Siqueira"
    },
    "hero_subtitle": {
        "pt-BR": "Engenheiro de Machine Learning",
        "en-US": "Machine Learning Engineer"
    },
    "hero_description": {
        "pt-BR": "Especialista em ML/IA com foco em sistemas prontos para produção. FastAPI, PyTorch, XGBoost, Voyage AI, RAG Systems.",
        "en-US": "ML/AI specialist focused on production-ready systems. FastAPI, PyTorch, XGBoost, Voyage AI, RAG Systems."
    },
    "hero_cta_projects": {
        "pt-BR": "Ver Projetos",
        "en-US": "View Projects"
    },
    "hero_cta_github": {
        "pt-BR": "GitHub",
        "en-US": "GitHub"
    },

    # === STATS SECTION ===
    "stats_projects": {
        "pt-BR": "Projetos",
        "en-US": "Projects"
    },
    "stats_technologies": {
        "pt-BR": "Tecnologias",
        "en-US": "Tech Stack"
    },
    "stats_experience": {
        "pt-BR": "Experiência",
        "en-US": "Experience"
    },

    # === SKILLS SECTION ===
    "section_title_skills": {
        "pt-BR": "Stack Tecnológica",
        "en-US": "Tech Stack"
    },
    "skill_category_ml": {
        "pt-BR": "ML/IA",
        "en-US": "ML/AI"
    },
    "skill_category_backend": {
        "pt-BR": "Backend",
        "en-US": "Backend"
    },
    "skill_category_frontend": {
        "pt-BR": "Frontend",
        "en-US": "Frontend"
    },
    "skill_category_devops": {
        "pt-BR": "DevOps",
        "en-US": "DevOps"
    },

    # === PROJECTS SECTION ===
    "section_title_projects": {
        "pt-BR": "Projetos em Destaque",
        "en-US": "Featured Projects"
    },
    "project_status_active": {
        "pt-BR": "Ativo",
        "en-US": "Active"
    },
    "project_cta": {
        "pt-BR": "Ver Projeto",
        "en-US": "View Project"
    },

    # === PROJECT 1: Doc QA ===
    "project_docqa_name": {
        "pt-BR": "Doc QA - Perguntas sobre Documentos",
        "en-US": "Doc QA - Document Question & Answering"
    },
    "project_docqa_description": {
        "pt-BR": "Sistema RAG de perguntas sobre documentos corporativos com verificação de fatos e explicabilidade",
        "en-US": "RAG-based document Q&A system with fact verification and explainability for business documents"
    },

    # === PROJECT 2: Credit Risk ===
    "project_credit_name": {
        "pt-BR": "API de Score de Crédito",
        "en-US": "Credit Risk Scoring API"
    },
    "project_credit_description": {
        "pt-BR": "Modelo preditivo com explicabilidade SHAP para decisões transparentes e conformidade regulatória",
        "en-US": "Predictive model with SHAP explainability for transparent decisions and regulatory compliance"
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
    """Detect language from request"""
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
