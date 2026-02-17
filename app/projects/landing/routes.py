"""
Landing Page Routes - Sales Funnel Implementation

TECH SHOWCASE FOR RECRUITERS:
- Psychology-driven UX (urgency, scarcity, social proof)
- Mobile-first responsive design
- Performance optimized (target: <1s LCP, >95 Lighthouse)
- A/B testing ready (configurable CTAs, pricing, copy)
- Analytics hooks for conversion tracking
- LGPD compliant (no cookies without consent)
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
from datetime import datetime

from .config import landing_config
from .models import LeadCapture, LeadResponse, CourseInfo
from .i18n import t

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cursos", tags=["Landing Page"])

# Template engine with fallback to global templates
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(
    directory=[
        str(template_dir),
        str(Path(__file__).resolve().parent.parent.parent.parent / "templates"),
    ]
)

# Make translation function available in templates
templates.env.globals["t"] = t


@router.get("/unha-gel", response_class=HTMLResponse)
async def landing_unha_gel(request: Request):
    """
    Landing page with conversion-optimized funnel

    CONVERSION PSYCHOLOGY APPLIED:
    1. Hero: Benefit-driven headline (not feature)
    2. Problem-Agitate-Solution framework
    3. Social proof (testimonials strategically placed)
    4. Scarcity (limited spots) + Urgency (timer)
    5. Risk reversal (7-day guarantee)
    6. Multiple CTAs (above fold, mid-page, bottom)
    7. FAQ to handle objections

    PERFORMANCE OPTIMIZATION:
    - Critical CSS inlined
    - Lazy loading images
    - No external dependencies (jQuery, etc)
    - Minified assets
    - Preload key resources

    TARGET METRICS:
    - LCP (Largest Contentful Paint): < 1.5s
    - FID (First Input Delay): < 100ms
    - CLS (Cumulative Layout Shift): < 0.1
    - Lighthouse Score: > 95
    """

    # Course info (A/B test ready - change in config)
    course = CourseInfo(
        name=landing_config.COURSE_NAME,
        price=landing_config.COURSE_PRICE,
        price_promo=landing_config.COURSE_PRICE_PROMO,
        currency=landing_config.COURSE_CURRENCY,
        checkout_url=landing_config.CHECKOUT_URL,
        whatsapp=landing_config.WHATSAPP_NUMBER,
    )

    # Testimonials (social proof - in production, load from DB)
    testimonials = [
        {
            "name": "Maria Silva",
            "image": "/static/images/testimonial-1.jpg",
            "text": "Em 3 meses já estava faturando R$ 2.500/mês! O curso mudou minha vida.",
            "rating": 5,
            "verified": True,
        },
        {
            "name": "Ana Costa",
            "image": "/static/images/testimonial-2.jpg",
            "text": "Consegui largar meu emprego e agora trabalho de casa. Melhor decisão!",
            "rating": 5,
            "verified": True,
        },
        {
            "name": "Juliana Santos",
            "image": "/static/images/testimonial-3.jpg",
            "text": "As técnicas são muito bem explicadas. Até quem nunca fez unha consegue!",
            "rating": 5,
            "verified": True,
        },
    ]

    # Stats (credibility boost)
    stats = {
        "students": "500+",
        "rating": "4.9/5.0",
        "satisfaction": "98%",
    }

    # FAQ (objection handling)
    faq_items = [
        {"q": t("faq_1_q"), "a": t("faq_1_a")},
        {"q": t("faq_2_q"), "a": t("faq_2_a")},
        {"q": t("faq_3_q"), "a": t("faq_3_a")},
        {"q": t("faq_4_q"), "a": t("faq_4_a")},
        {"q": t("faq_5_q"), "a": t("faq_5_a")},
        {"q": t("faq_6_q"), "a": t("faq_6_a")},
        {"q": t("faq_7_q"), "a": t("faq_7_a")},
        {"q": t("faq_8_q"), "a": t("faq_8_a")},
    ]

    # GoatCounter analytics code (if configured)
    import os
    goatcounter_code = os.getenv("GOATCOUNTER_CODE", "")

    context = {
        "request": request,
        "course": course,
        "testimonials": testimonials,
        "stats": stats,
        "faq": faq_items,
        "timer_duration": landing_config.OFFER_DURATION_MINUTES,
        "goatcounter_code": goatcounter_code,
        "year": datetime.now().year,
    }

    logger.info("Landing page viewed", extra={
        "page": "unha-gel",
        "timestamp": datetime.now().isoformat(),
    })

    return templates.TemplateResponse("landing_index.html", context)


@router.post("/lead", response_class=HTMLResponse)
async def capture_lead(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(...),
):
    """
    Lead capture endpoint (optional - for email marketing funnel)

    FUTURE ENHANCEMENT:
    - Integrate with Mailchimp/ActiveCampaign
    - Send to Google Sheets via API
    - Trigger automated email sequence
    - Track conversion in analytics

    Currently: Just logs (LGPD compliant - no storage without consent)
    """

    try:
        lead = LeadCapture(nome=nome, email=email, telefone=telefone)

        # TODO: In production, integrate with CRM/email marketing
        # For now, just log (no PII storage without explicit consent)
        logger.info("Lead captured", extra={
            "nome_length": len(lead.nome),
            "has_email": bool(lead.email),
            "has_phone": bool(lead.telefone),
        })

        # Return success message (HTMX will swap this into the form)
        return HTMLResponse(
            content=f"""
            <div class="lead-success">
                <h3>Obrigada, {lead.nome}!</h3>
                <p>Em breve você receberá mais informações no email <strong>{lead.email}</strong>.</p>
                <p>Fique de olho na caixa de entrada e no spam!</p>
            </div>
            """,
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Lead capture error: {e}")
        return HTMLResponse(
            content=f"""
            <div class="lead-error">
                <p>Ops! Algo deu errado. Tente novamente ou entre em contato via WhatsApp.</p>
            </div>
            """,
            status_code=400,
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "landing-page",
        "checkout_configured": bool(landing_config.CHECKOUT_URL),
    }
