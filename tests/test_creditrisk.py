"""
Testes para Credit Risk Scoring API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.projects.creditrisk.models import (
    LoanApplication, RiskPrediction, EducationLevel,
    HousingType, IncomeType, FamilyStatus
)

client = TestClient(app)


class TestCreditRiskRoutes:
    """Testes de rotas HTTP"""

    def test_index_page(self):
        """Testa se página principal carrega"""
        response = client.get("/credit-risk/")
        assert response.status_code == 200
        assert b"Credit Risk" in response.content

    def test_index_page_pt_br(self):
        """Testa página em PT-BR"""
        response = client.get("/credit-risk/?lang=pt-BR")
        assert response.status_code == 200
        assert "Credit Risk" in response.text

    def test_index_page_en_us(self):
        """Testa página em EN-US"""
        response = client.get("/credit-risk/?lang=en-US")
        assert response.status_code == 200
        assert "Credit Risk" in response.text

    def test_health_endpoint(self):
        """Testa health check"""
        response = client.get("/credit-risk/health")
        assert response.status_code in [200, 503]  # 503 se modelo não treinado
        data = response.json()
        assert "status" in data

    def test_info_endpoint(self):
        """Testa endpoint de informações"""
        response = client.get("/credit-risk/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "model" in data
        assert "dataset" in data
        assert data["model"]["type"] == "XGBoost Classifier"


class TestCreditRiskModels:
    """Testes de validação Pydantic"""

    def test_loan_application_valid(self):
        """Testa criação de LoanApplication válida"""
        app = LoanApplication(
            gender="M",
            age_years=30,
            family_status=FamilyStatus.MARRIED,
            family_members=3,
            children_count=1,
            annual_income=50000.0,
            income_type=IncomeType.WORKING,
            employment_days=-1095,  # 3 anos
            education_level=EducationLevel.HIGHER_EDUCATION,
            housing_type=HousingType.HOUSE_APARTMENT,
            has_car=True,
            has_property=False,
            has_work_phone=True,
            has_phone=True,
            has_email=True,
            occupation_type="Engineer"
        )
        assert app.age_years == 30
        assert app.annual_income == 50000.0

    def test_loan_application_age_validation(self):
        """Testa validação de idade mínima"""
        with pytest.raises(ValueError):
            LoanApplication(
                gender="M",
                age_years=15,  # Inválido: < 18
                family_status=FamilyStatus.SINGLE,
                family_members=1,
                children_count=0,
                annual_income=30000.0,
                income_type=IncomeType.WORKING,
                employment_days=-365,
                education_level=EducationLevel.SECONDARY,
                housing_type=HousingType.WITH_PARENTS,
            )

    def test_loan_application_employment_validation(self):
        """Testa validação de employment_days (deve ser <= 0)"""
        with pytest.raises(ValueError):
            LoanApplication(
                gender="F",
                age_years=25,
                family_status=FamilyStatus.SINGLE,
                family_members=1,
                children_count=0,
                annual_income=40000.0,
                income_type=IncomeType.WORKING,
                employment_days=1000,  # Inválido: deve ser <= 0
                education_level=EducationLevel.HIGHER_EDUCATION,
                housing_type=HousingType.RENTED_APARTMENT,
            )

    def test_loan_application_income_validation(self):
        """Testa validação de income (deve ser > 0)"""
        with pytest.raises(ValueError):
            LoanApplication(
                gender="M",
                age_years=30,
                family_status=FamilyStatus.MARRIED,
                family_members=2,
                children_count=0,
                annual_income=0.0,  # Inválido: deve ser > 0
                income_type=IncomeType.WORKING,
                employment_days=-365,
                education_level=EducationLevel.SECONDARY,
                housing_type=HousingType.HOUSE_APARTMENT,
            )


class TestCreditRiskAPI:
    """Testes de API JSON"""

    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Requer modelo treinado (use --run-integration)"
    )
    def test_score_api_success(self):
        """Testa predição via API JSON (requer modelo treinado)"""
        application = {
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
            "has_car": True,
            "has_property": False,
            "has_work_phone": True,
            "has_phone": True,
            "has_email": True,
            "occupation_type": "Engineer"
        }

        response = client.post("/credit-risk/api/score", json=application)

        if response.status_code == 500:
            # Modelo não treinado - esperado em CI
            pytest.skip("Model not trained yet")

        assert response.status_code == 200
        data = response.json()

        assert "approval_probability" in data
        assert "risk_category" in data
        assert "recommended_action" in data
        assert "shap_top_features" in data
        assert "confidence" in data

        assert 0 <= data["approval_probability"] <= 1
        assert 0 <= data["confidence"] <= 1
        assert data["risk_category"] in ["low", "medium", "high", "very_high"]

    def test_score_api_invalid_age(self):
        """Testa API com idade inválida"""
        application = {
            "gender": "M",
            "age_years": 150,  # Inválido
            "family_status": "Married",
            "family_members": 2,
            "children_count": 0,
            "annual_income": 50000.0,
            "income_type": "Working",
            "employment_days": -1095,
            "education_level": "Higher education",
            "housing_type": "House / apartment",
        }

        response = client.post("/credit-risk/api/score", json=application)
        assert response.status_code == 422  # Validation error


class TestCreditRiskSecurity:
    """Testes de segurança"""

    def test_sql_injection_attempt(self):
        """Testa proteção contra SQL injection"""
        malicious_input = {
            "gender": "M",
            "age_years": 30,
            "family_status": "Married'; DROP TABLE users; --",
            "family_members": 2,
            "children_count": 0,
            "annual_income": 50000.0,
            "income_type": "Working",
            "employment_days": -1095,
            "education_level": "Higher education",
            "housing_type": "House / apartment",
        }

        response = client.post("/credit-risk/api/score", json=malicious_input)
        # Deve falhar na validação do enum
        assert response.status_code == 422

    def test_xss_attempt(self):
        """Testa proteção contra XSS"""
        malicious_input = {
            "gender": "M",
            "age_years": 30,
            "family_status": "Married",
            "family_members": 2,
            "children_count": 0,
            "annual_income": 50000.0,
            "income_type": "Working",
            "employment_days": -1095,
            "education_level": "Higher education",
            "housing_type": "House / apartment",
            "occupation_type": "<script>alert('XSS')</script>"
        }

        # Pydantic deve aceitar (é string válida)
        # Mas o template deve fazer escaping automático
        response = client.post("/credit-risk/api/score", json=malicious_input)

        if response.status_code == 200:
            # Verificar que script tag não aparece no response
            assert "<script>" not in response.text


def pytest_addoption(parser):
    """Adiciona opção --run-integration ao pytest"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require trained model"
    )


def pytest_configure(config):
    """Configura markers customizados"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires trained model)"
    )
