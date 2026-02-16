"""
Risk Scoring Service
Predição de risco + SHAP explanations
"""
import joblib
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import numpy as np

from app.projects.creditrisk.config import get_credit_risk_config
from app.projects.creditrisk.models import LoanApplication, RiskPrediction, RiskCategory
from app.projects.creditrisk.services.feature_engineering import get_feature_engineering

logger = logging.getLogger(__name__)


class RiskScoring:
    """
    Singleton service para scoring de risco
    - Carrega modelo treinado
    - Predição de probabilidade de aprovação
    - SHAP explanations
    - Categorização de risco
    """

    def __init__(self):
        self.config = get_credit_risk_config()
        self.feature_engineering = get_feature_engineering()
        self._model = None
        self._shap_explainer = None

    @property
    def model(self):
        """Lazy loading do modelo"""
        if self._model is None:
            self._load_model()
        return self._model

    @property
    def shap_explainer(self):
        """Lazy loading do SHAP explainer"""
        if self._shap_explainer is None:
            self._init_shap_explainer()
        return self._shap_explainer

    def _load_model(self) -> None:
        """Carrega modelo XGBoost"""
        model_path = Path(self.config.MODEL_PATH)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Modelo não encontrado em {model_path}. "
                f"Execute o treinamento primeiro: python -m app.projects.creditrisk.services.model_training"
            )

        self._model = joblib.load(model_path)
        logger.info(f"✅ Modelo carregado de {model_path}")

    def _init_shap_explainer(self) -> None:
        """Inicializa SHAP explainer"""
        try:
            import shap

            # TreeExplainer para XGBoost
            self._shap_explainer = shap.TreeExplainer(self.model)
            logger.info("✅ SHAP explainer inicializado")

        except ImportError:
            logger.warning("⚠️  SHAP não instalado. Explanations desabilitados.")
            self._shap_explainer = None
        except Exception as e:
            logger.error(f"Erro ao inicializar SHAP: {e}")
            self._shap_explainer = None

    async def score(self, application: LoanApplication) -> RiskPrediction:
        """
        Score de risco para uma aplicação

        Args:
            application: LoanApplication com dados do cliente

        Returns:
            RiskPrediction com probabilidade, categoria, SHAP values
        """
        start_time = time.time()

        # 1. Converter aplicação para dict
        app_dict = application.model_dump()

        # 2. Feature engineering
        try:
            X = self.feature_engineering.transform_single(app_dict)
        except Exception as e:
            logger.error(f"Erro no feature engineering: {e}")
            raise ValueError(f"Erro ao processar features: {e}")

        # 3. Predição
        try:
            approval_proba = self.model.predict_proba(X)[0, 1]  # Prob de aprovação (classe 1)
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            raise ValueError(f"Erro ao fazer predição: {e}")

        # 4. Categorização de risco
        risk_category = self._categorize_risk(approval_proba)

        # 5. Ação recomendada
        recommended_action = self._get_recommended_action(risk_category, approval_proba)

        # 6. SHAP explanations
        shap_features = self._get_shap_explanations(X)

        # 7. Confiança (baseada em distância do threshold)
        confidence = self._calculate_confidence(approval_proba)

        # Tempo de processamento
        processing_time_ms = (time.time() - start_time) * 1000

        # Construir resposta
        prediction = RiskPrediction(
            approval_probability=float(approval_proba),
            risk_category=risk_category,
            recommended_action=recommended_action,
            shap_top_features=shap_features,
            confidence=float(confidence),
            processing_time_ms=processing_time_ms,
            model_version="1.0.0"
        )

        logger.info(
            f"Prediction: prob={approval_proba:.3f}, risk={risk_category.value}, "
            f"time={processing_time_ms:.1f}ms"
        )

        return prediction

    def _categorize_risk(self, approval_proba: float) -> RiskCategory:
        """Categoriza risco baseado em thresholds"""
        if approval_proba >= self.config.RISK_LOW_THRESHOLD:
            return RiskCategory.LOW
        elif approval_proba >= self.config.RISK_MEDIUM_THRESHOLD:
            return RiskCategory.MEDIUM
        elif approval_proba >= self.config.RISK_HIGH_THRESHOLD:
            return RiskCategory.HIGH
        else:
            return RiskCategory.VERY_HIGH

    def _get_recommended_action(self, risk_category: RiskCategory, approval_proba: float) -> str:
        """Retorna ação recomendada baseada no risco"""
        actions = {
            RiskCategory.LOW: f"✅ Aprovação recomendada (confiança: {approval_proba*100:.1f}%)",
            RiskCategory.MEDIUM: f"⚠️  Análise manual recomendada (confiança: {approval_proba*100:.1f}%)",
            RiskCategory.HIGH: f"⚠️  Solicitar garantias adicionais (risco: {(1-approval_proba)*100:.1f}%)",
            RiskCategory.VERY_HIGH: f"❌ Rejeição recomendada (risco: {(1-approval_proba)*100:.1f}%)"
        }
        return actions[risk_category]

    def _get_shap_explanations(self, X) -> Dict[str, float]:
        """
        Calcula SHAP values para as top features

        Returns:
            Dict com top N features e seus SHAP values
        """
        if self._shap_explainer is None:
            return {}

        try:
            # Calcular SHAP values
            shap_values = self._shap_explainer.shap_values(X)

            # Pegar valores absolutos (magnitude do impacto)
            shap_abs = np.abs(shap_values[0])

            # Top features
            feature_names = X.columns.tolist()
            top_indices = np.argsort(shap_abs)[::-1][:self.config.SHAP_TOP_FEATURES]

            # Construir dict
            top_features = {}
            for idx in top_indices:
                feature_name = feature_names[idx]
                shap_value = float(shap_values[0][idx])
                top_features[feature_name] = shap_value

            return top_features

        except Exception as e:
            logger.error(f"Erro ao calcular SHAP values: {e}")
            return {}

    def _calculate_confidence(self, approval_proba: float) -> float:
        """
        Calcula confiança baseada em distância dos thresholds
        Quanto mais longe dos thresholds (0.3, 0.5, 0.7), maior a confiança
        """
        # Distância do threshold mais próximo
        thresholds = [
            self.config.RISK_HIGH_THRESHOLD,
            self.config.RISK_MEDIUM_THRESHOLD,
            self.config.RISK_LOW_THRESHOLD
        ]

        min_distance = min([abs(approval_proba - t) for t in thresholds])

        # Normalizar para [0, 1] (distância máxima = 0.3)
        confidence = min(min_distance / 0.3, 1.0)

        return confidence

    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do serviço"""
        try:
            model_loaded = self._model is not None
            scaler_loaded = self.feature_engineering._scaler is not None
            encoder_loaded = len(self.feature_engineering._encoders) > 0
            total_features = len(self.feature_engineering._feature_names) if self.feature_engineering._feature_names else 0

            return {
                'status': 'healthy' if model_loaded else 'unhealthy',
                'model_loaded': model_loaded,
                'scaler_loaded': scaler_loaded,
                'encoder_loaded': encoder_loaded,
                'total_features': total_features,
                'model_version': '1.0.0'
            }
        except Exception as e:
            logger.error(f"Erro no health check: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Singleton instance
_risk_scoring: Optional[RiskScoring] = None


def get_risk_scoring() -> RiskScoring:
    """Factory function para singleton"""
    global _risk_scoring
    if _risk_scoring is None:
        _risk_scoring = RiskScoring()
    return _risk_scoring
