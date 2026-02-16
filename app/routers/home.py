"""
Home page router - Landing page with portfolio presentation
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.core.logging_config import get_logger
from .i18n import get_language_from_request, t

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = get_logger(__name__)


@router.get("/")
async def home(request: Request):
    """
    Landing page with hero section, skills, and featured projects
    """
    logger.info("Home page accessed", extra={"ip": request.client.host if request.client else "unknown"})

    # Detect language
    lang = get_language_from_request(request)

    # Skills data
    skills = {
        "ml_frameworks": ["PyTorch", "TensorFlow", "XGBoost", "Voyage AI", "SHAP", "Scikit-learn"],
        "backend": ["FastAPI", "Python 3.11+", "Pydantic", "PostgreSQL", "Qdrant Cloud"],
        "frontend": ["HTMX", "Jinja2", "FrontRender CSS"],
        "devops": ["Podman", "Podman Compose", "Caddy", "GitHub Actions", "Prometheus"]
    }

    # Featured projects
    projects = [
        {
            "name": t("project_docqa_name", lang),
            "description": t("project_docqa_description", lang),
            "tech": ["FastAPI", "Voyage AI", "Qdrant Cloud", "Groq"],
            "status": t("project_status_active", lang),
            "url": "/docqa"
        },
        {
            "name": t("project_credit_name", lang),
            "description": t("project_credit_description", lang),
            "tech": ["XGBoost", "SHAP", "FastAPI", "Scikit-learn"],
            "status": t("project_status_active", lang),
            "url": "/credit-risk"
        }
    ]

    # Stats
    stats = {
        "projects": 2,
        "technologies": 19,
        "experience": "3+ anos" if lang == "pt-BR" else "3+ years"
    }

    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "title": "Kaio H. - ML Engineer",
            "skills": skills,
            "projects": projects,
            "stats": stats,
            "lang": lang,
            "t": lambda key: t(key, lang)
        }
    )
