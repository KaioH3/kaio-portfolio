"""Pydantic models para Credit Risk Scoring API"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Literal, Optional
from datetime import datetime
from enum import Enum


class EducationLevel(str, Enum):
    """Níveis de educação"""
    LOWER_SECONDARY = "Lower secondary"
    SECONDARY = "Secondary / secondary special"
    INCOMPLETE_HIGHER = "Incomplete higher"
    HIGHER_EDUCATION = "Higher education"
    ACADEMIC_DEGREE = "Academic degree"


class HousingType(str, Enum):
    """Tipos de moradia"""
    HOUSE_APARTMENT = "House / apartment"
    WITH_PARENTS = "With parents"
    MUNICIPAL_APARTMENT = "Municipal apartment"
    RENTED_APARTMENT = "Rented apartment"
    OFFICE_APARTMENT = "Office apartment"
    CO_OP_APARTMENT = "Co-op apartment"


class IncomeType(str, Enum):
    """Tipos de renda"""
    WORKING = "Working"
    STATE_SERVANT = "State servant"
    COMMERCIAL_ASSOCIATE = "Commercial associate"
    PENSIONER = "Pensioner"
    STUDENT = "Student"


class FamilyStatus(str, Enum):
    """Status familiar"""
    MARRIED = "Married"
    SINGLE = "Single / not married"
    CIVIL_MARRIAGE = "Civil marriage"
    SEPARATED = "Separated"
    WIDOW = "Widow"


class RiskCategory(str, Enum):
    """Categorias de risco"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class LoanApplication(BaseModel):
    """Request model para análise de risco de crédito"""

    # Informações demográficas
    gender: Literal["M", "F"] = Field(..., description="Gênero (M/F)")
    age_years: int = Field(..., ge=18, le=100, description="Idade em anos")

    # Informações familiares
    family_status: FamilyStatus = Field(..., description="Status familiar")
    family_members: int = Field(..., ge=1, le=20, description="Número de membros da família")
    children_count: int = Field(default=0, ge=0, le=10, description="Número de filhos")

    # Informações financeiras
    annual_income: float = Field(..., gt=0, description="Renda anual total")
    income_type: IncomeType = Field(..., description="Tipo de renda")

    # Informações profissionais
    employment_days: int = Field(..., description="Dias de emprego (negativo = dias desde o início)")

    # Informações educacionais e habitacionais
    education_level: EducationLevel = Field(..., description="Nível educacional")
    housing_type: HousingType = Field(..., description="Tipo de moradia")

    # Propriedades
    has_car: bool = Field(default=False, description="Possui carro")
    has_property: bool = Field(default=False, description="Possui imóvel")
    has_work_phone: bool = Field(default=False, description="Possui telefone comercial")
    has_phone: bool = Field(default=False, description="Possui telefone")
    has_email: bool = Field(default=False, description="Possui email")

    # Ocupação
    occupation_type: Optional[str] = Field(default=None, description="Tipo de ocupação")

    @field_validator("employment_days")
    @classmethod
    def validate_employment_days(cls, v):
        """Employment days é negativo no dataset (dias desde o início)"""
        if v > 0:
            raise ValueError("employment_days deve ser <= 0 (formato do dataset)")
        return v

    @field_validator("annual_income")
    @classmethod
    def validate_income(cls, v):
        """Validar renda razoável"""
        if v > 10_000_000:
            raise ValueError("Renda anual muito alta")
        return v


class RiskPrediction(BaseModel):
    """Response model com predição de risco"""

    # Predição
    approval_probability: float = Field(..., ge=0.0, le=1.0, description="Probabilidade de aprovação (0-1)")
    risk_category: RiskCategory = Field(..., description="Categoria de risco")
    recommended_action: str = Field(..., description="Ação recomendada")

    # Explicabilidade (SHAP)
    shap_top_features: Dict[str, float] = Field(
        ...,
        description="Top features que influenciaram a decisão (SHAP values)"
    )

    # Métricas
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança do modelo")
    processing_time_ms: float = Field(..., description="Tempo de processamento em ms")

    # Metadata
    model_version: str = Field(default="1.0.0", description="Versão do modelo")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da predição")


class HealthCheck(BaseModel):
    """Health check do serviço"""
    status: str
    model_loaded: bool
    scaler_loaded: bool
    encoder_loaded: bool
    total_features: int
    model_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Response de erro"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelMetrics(BaseModel):
    """Métricas do modelo treinado"""
    auc_roc: float = Field(..., description="AUC-ROC score")
    accuracy: float = Field(..., description="Accuracy")
    precision: float = Field(..., description="Precision")
    recall: float = Field(..., description="Recall")
    f1_score: float = Field(..., description="F1 Score")
    training_samples: int = Field(..., description="Número de amostras de treino")
    test_samples: int = Field(..., description="Número de amostras de teste")
    training_date: datetime = Field(default_factory=datetime.utcnow)
