"""
Landing Page Configuration
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class LandingConfig(BaseSettings):
    # === Course Settings ===
    COURSE_NAME: str = "Curso Profissional de Unha Gel"
    COURSE_PRICE: str = "297.00"
    COURSE_PRICE_PROMO: str = "197.00"
    COURSE_CURRENCY: str = "R$"

    # === Checkout Settings ===
    CHECKOUT_PLATFORM: str = "hotmart"  # hotmart | kiwify | mercadopago
    CHECKOUT_URL: str = os.getenv("CHECKOUT_URL", "https://pay.hotmart.com/YOUR_LINK_HERE")

    # === Timer Settings ===
    OFFER_DURATION_MINUTES: int = 30  # Timer de urgência

    # === Lead Capture ===
    ENABLE_LEAD_CAPTURE: bool = False  # Desabilitar por enquanto
    LEAD_STORAGE_PATH: str = "./data/leads.json"

    # === Contact ===
    WHATSAPP_NUMBER: str = os.getenv("WHATSAPP_NUMBER", "5511999999999")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "contato@example.com")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_landing_config() -> LandingConfig:
    return LandingConfig()


landing_config = get_landing_config()
