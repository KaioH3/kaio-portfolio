"""
Home page router - Landing page with portfolio presentation
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.core.logging_config import get_logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = get_logger(__name__)


@router.get("/")
async def home(request: Request):
    """
    Landing page with hero section, skills, and featured projects
    """
    logger.info("Home page accessed", extra={"ip": request.client.host})
    
    # Skills data
    skills = {
        "ml_frameworks": ["PyTorch", "TensorFlow", "XGBoost", "LangChain"],
        "backend": ["FastAPI", "Python 3.11+", "Podman", "PostgreSQL"],
        "frontend": ["FrontRender", "Jinja2", "Pure CSS", "Responsive Design"],
        "devops": ["Podman Compose", "Caddy", "Prometheus", "Grafana", "GitHub Actions"]
    }
    
    # Featured projects (MVP - placeholders)
    projects = [
        {
            "name": "RAG Document Intelligence",
            "description": "Sistema modular com Chain-of-Verification que reduz alucinações em 50%",
            "tech": ["FastAPI", "LangChain", "Qdrant", "GPT-4o"],
            "status": "Em breve",
            "url": "/rag-system"
        },
        {
            "name": "Credit Scoring API",
            "description": "Modelo XGBoost para análise de risco de crédito com SHAP explanations",
            "tech": ["XGBoost", "FastAPI", "Podman", "MLflow"],
            "status": "Em breve",
            "url": "/credit-risk"
        }
    ]
    
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "title": "Kaio H. - ML Engineer",
            "skills": skills,
            "projects": projects,
            "stats": {
                "projects": 2,
                "technologies": 15,
                "experience": "3+ anos"
            }
        }
    )
