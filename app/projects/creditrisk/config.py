"""
Credit Risk Scoring Configuration
XGBoost + SHAP para análise de risco de crédito
"""
import os
from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class CreditRiskConfig(BaseSettings):
    # === Dataset Paths ===
    DATASET_PATH_APPLICATION: str = "./data/credit_card_approval/application_record.csv"
    DATASET_PATH_CREDIT: str = "./data/credit_card_approval/credit_record.csv"
    MODEL_PATH: str = "./data/models/credit_risk_xgboost.pkl"
    SCALER_PATH: str = "./data/models/credit_risk_scaler.pkl"
    ENCODER_PATH: str = "./data/models/credit_risk_encoder.pkl"
    FEATURE_NAMES_PATH: str = "./data/models/credit_risk_features.json"

    # === XGBoost Hyperparameters ===
    XGBOOST_MAX_DEPTH: int = 6
    XGBOOST_LEARNING_RATE: float = 0.1
    XGBOOST_N_ESTIMATORS: int = 200
    XGBOOST_MIN_CHILD_WEIGHT: int = 1
    XGBOOST_SUBSAMPLE: float = 0.8
    XGBOOST_COLSAMPLE_BYTREE: float = 0.8
    XGBOOST_SCALE_POS_WEIGHT: float = 3.0  # Para lidar com imbalance
    XGBOOST_RANDOM_STATE: int = 42

    # === Training ===
    TEST_SIZE: float = 0.2
    VALIDATION_SIZE: float = 0.2
    MIN_AUC_THRESHOLD: float = 0.75

    # === Feature Engineering ===
    INCOME_BINS: int = 5
    AGE_BINS: int = 5
    EMPLOYMENT_BINS: int = 4

    # === Risk Categorization Thresholds ===
    RISK_LOW_THRESHOLD: float = 0.7  # > 70% approval prob = Low Risk
    RISK_MEDIUM_THRESHOLD: float = 0.5  # 50-70% = Medium Risk
    RISK_HIGH_THRESHOLD: float = 0.3  # 30-50% = High Risk
    # < 30% = Very High Risk

    # === SHAP Explanations ===
    SHAP_TOP_FEATURES: int = 10
    SHAP_SAMPLE_SIZE: int = 100  # Amostras para calcular SHAP values (performance)

    # === API Settings ===
    MAX_REQUESTS_PER_HOUR: int = 100
    REQUEST_TIMEOUT: float = 30.0

    # === Monitoring ===
    ENABLE_DRIFT_DETECTION: bool = False
    PSI_THRESHOLD: float = 0.25  # Population Stability Index threshold

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_credit_risk_config() -> CreditRiskConfig:
    """Singleton para evitar recarregar config"""
    return CreditRiskConfig()
