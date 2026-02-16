"""
Comprehensive tests for RAG System
Run with: pytest tests/test_rag_system.py -v
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from io import BytesIO
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.projects.ragsystem.i18n import t, verify_translations

client = TestClient(app)

class TestI18n:
    """Test internationalization"""
    
    def test_translation_basic(self):
        pt = t("upload_section_title", "pt-BR")
        en = t("upload_section_title", "en-US")
        assert pt != en
        assert isinstance(pt, str)
    
    def test_translation_with_params(self):
        result = t("upload_success", "pt-BR", filename="test.pdf", chunks=10, time_ms=1234.5)
        assert "test.pdf" in result
        assert "10" in result
    
    def test_translation_integrity(self):
        report = verify_translations()
        assert len(report["missing_pt_br"]) == 0
        assert len(report["missing_en_us"]) == 0
        assert len(report["placeholder_mismatches"]) == 0

class TestHealthCheck:
    """Test health endpoint"""
    
    def test_health_exists(self):
        response = client.get("/rag-system/health")
        assert response.status_code == 200
    
    def test_health_structure(self):
        response = client.get("/rag-system/health")
        data = response.json()
        assert "status" in data

class TestFrontend:
    """Test frontend"""
    
    def test_index_loads(self):
        response = client.get("/rag-system/")
        assert response.status_code == 200
    
    def test_index_has_htmx(self):
        response = client.get("/rag-system/")
        assert "htmx" in response.text.lower()

@pytest.fixture(scope="session", autouse=True)
def setup_tests():
    print("\n Chain of Verification - Test Suite")
    yield
    print("\n Tests completed!")
