"""
Feature Engineering para Credit Risk Scoring
Pipeline de transformação de features
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from app.projects.creditrisk.config import get_credit_risk_config

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """
    Pipeline de feature engineering
    - Cria features derivadas (ratios, bins, etc)
    - Encoding de categóricas
    - Scaling de numéricas
    """

    def __init__(self):
        self.config = get_credit_risk_config()
        self._scaler: Optional[StandardScaler] = None
        self._encoders: Dict[str, LabelEncoder] = {}
        self._feature_names: Optional[list] = None
        self._income_bins: Optional[list] = None  # Bins do qcut salvos
        self._is_fitted = False

    def fit(self, df: pd.DataFrame) -> 'FeatureEngineering':
        """Fit nos dados de treino"""
        logger.info("Fitting feature engineering pipeline...")

        # Criar features derivadas e salvar bins
        df_engineered = self._create_derived_features(df.copy(), fit=True)

        # Separar numéricas e categóricas
        numeric_features = df_engineered.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = df_engineered.select_dtypes(include=['object', 'category']).columns.tolist()

        # Remover TARGET se existir
        if 'TARGET' in numeric_features:
            numeric_features.remove('TARGET')

        logger.info(f"Numeric features: {len(numeric_features)}")
        logger.info(f"Categorical features: {len(categorical_features)}")

        # Fit scaler para numéricas
        self._scaler = StandardScaler()
        self._scaler.fit(df_engineered[numeric_features])

        # Fit encoders para categóricas
        for col in categorical_features:
            encoder = LabelEncoder()
            encoder.fit(df_engineered[col].astype(str))
            self._encoders[col] = encoder

        # Salvar nomes das features
        self._feature_names = numeric_features + categorical_features
        self._is_fitted = True

        logger.info(f"Pipeline fitted com {len(self._feature_names)} features")
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform dados (treino ou produção)"""
        if not self._is_fitted:
            raise ValueError("Pipeline precisa ser fitted antes de transform")

        # Criar features derivadas (usando bins salvos)
        df_engineered = self._create_derived_features(df.copy(), fit=False)

        # Separar numéricas e categóricas
        numeric_features = [f for f in self._feature_names if f in df_engineered.select_dtypes(include=[np.number]).columns]
        categorical_features = [f for f in self._feature_names if f in df_engineered.select_dtypes(include=['object', 'category']).columns]

        # Transform numéricas
        df_scaled = df_engineered.copy()
        df_scaled[numeric_features] = self._scaler.transform(df_engineered[numeric_features])

        # Transform categóricas
        for col in categorical_features:
            df_scaled[col] = self._encoders[col].transform(df_engineered[col].astype(str))

        return df_scaled

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit e transform de uma vez"""
        return self.fit(df).transform(df)

    def _create_derived_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Cria features derivadas"""

        # === Ratios ===
        df['INCOME_PER_PERSON'] = df['ANNUAL_INCOME'] / df['FAMILY_MEMBERS']
        df['INCOME_PER_CHILD'] = df['ANNUAL_INCOME'] / (df['CHILDREN_COUNT'] + 1)  # +1 para evitar divisão por zero

        # === Employment features ===
        df['EMPLOYMENT_YEARS'] = (-df['EMPLOYMENT_DAYS'] / 365).round(2)
        df['IS_EMPLOYED'] = (df['EMPLOYMENT_DAYS'] < 0).astype(int)

        # === Age groups ===
        df['AGE_GROUP'] = pd.cut(
            df['AGE_YEARS'],
            bins=[0, 25, 35, 45, 55, 100],
            labels=['18-25', '26-35', '36-45', '46-55', '55+']
        ).astype(str)

        # === Income groups ===
        if fit:
            # Durante fit, calcular e salvar os bins
            df['INCOME_GROUP'], self._income_bins = pd.qcut(
                df['ANNUAL_INCOME'],
                q=self.config.INCOME_BINS,
                labels=[f'Q{i+1}' for i in range(self.config.INCOME_BINS)],
                duplicates='drop',
                retbins=True
            )
            df['INCOME_GROUP'] = df['INCOME_GROUP'].astype(str)
        else:
            # Durante transform, usar bins salvos
            df['INCOME_GROUP'] = pd.cut(
                df['ANNUAL_INCOME'],
                bins=self._income_bins,
                labels=[f'Q{i+1}' for i in range(len(self._income_bins)-1)],
                include_lowest=True
            ).astype(str)

        # === Family features ===
        df['HAS_CHILDREN'] = (df['CHILDREN_COUNT'] > 0).astype(int)
        df['LARGE_FAMILY'] = (df['FAMILY_MEMBERS'] >= 4).astype(int)

        # === Education score (ordinal encoding manual) ===
        education_score = {
            'Lower secondary': 1,
            'Secondary / secondary special': 2,
            'Incomplete higher': 3,
            'Higher education': 4,
            'Academic degree': 5
        }
        df['EDUCATION_SCORE'] = df['EDUCATION_LEVEL'].map(education_score).fillna(2)

        # === Housing score ===
        housing_score = {
            'With parents': 1,
            'Rented apartment': 2,
            'Municipal apartment': 2,
            'Co-op apartment': 3,
            'Office apartment': 3,
            'House / apartment': 4
        }
        df['HOUSING_SCORE'] = df['HOUSING_TYPE'].map(housing_score).fillna(2)

        # === Digital presence score ===
        df['DIGITAL_SCORE'] = (
            df['HAS_MOBILE'] +
            df['HAS_EMAIL'] +
            df['HAS_PHONE'] +
            df['HAS_WORK_PHONE']
        )

        # === Assets score ===
        df['ASSETS_SCORE'] = df['HAS_CAR'] + df['HAS_PROPERTY']

        return df

    def transform_single(self, application: Dict[str, Any]) -> pd.DataFrame:
        """
        Transform uma única aplicação (para produção)
        Input: dict com features do LoanApplication
        Output: DataFrame pronto para predição
        """
        # Converter dict para DataFrame
        df = pd.DataFrame([application])

        # Mapear nomes do modelo Pydantic para nomes do dataset
        column_mapping = {
            'age_years': 'AGE_YEARS',
            'gender': 'GENDER',
            'family_status': 'FAMILY_STATUS',
            'family_members': 'FAMILY_MEMBERS',
            'children_count': 'CHILDREN_COUNT',
            'annual_income': 'ANNUAL_INCOME',
            'income_type': 'INCOME_TYPE',
            'employment_days': 'EMPLOYMENT_DAYS',
            'education_level': 'EDUCATION_LEVEL',
            'housing_type': 'HOUSING_TYPE',
            'has_car': 'HAS_CAR',
            'has_property': 'HAS_PROPERTY',
            'has_work_phone': 'HAS_WORK_PHONE',
            'has_phone': 'HAS_PHONE',
            'has_email': 'HAS_EMAIL',
            'occupation_type': 'OCCUPATION_TYPE'
        }

        df = df.rename(columns=column_mapping)

        # Adicionar features faltantes com valores padrão
        if 'HAS_MOBILE' not in df.columns:
            df['HAS_MOBILE'] = 1  # Assume que tem mobile

        # Garantir tipos corretos
        for col in df.columns:
            if col in ['HAS_CAR', 'HAS_PROPERTY', 'HAS_WORK_PHONE', 'HAS_PHONE', 'HAS_EMAIL', 'HAS_MOBILE']:
                df[col] = df[col].astype(int)

        # Transform
        df_transformed = self.transform(df)

        # Retornar apenas features usadas no modelo
        return df_transformed[self._feature_names]

    def save(self) -> None:
        """Salva scaler, encoders e feature names"""
        if not self._is_fitted:
            raise ValueError("Pipeline precisa ser fitted antes de salvar")

        scaler_path = Path(self.config.SCALER_PATH)
        encoder_path = Path(self.config.ENCODER_PATH)
        features_path = Path(self.config.FEATURE_NAMES_PATH)

        # Criar diretório se não existir
        scaler_path.parent.mkdir(parents=True, exist_ok=True)

        # Salvar scaler
        joblib.dump(self._scaler, scaler_path)
        logger.info(f"Scaler salvo em {scaler_path}")

        # Salvar encoders
        joblib.dump(self._encoders, encoder_path)
        logger.info(f"Encoders salvos em {encoder_path}")

        # Salvar feature names e income bins
        features_data = {
            'feature_names': self._feature_names,
            'income_bins': self._income_bins.tolist() if self._income_bins is not None else None
        }
        with open(features_path, 'w') as f:
            json.dump(features_data, f, indent=2)
        logger.info(f"Feature names e bins salvos em {features_path}")

    def load(self) -> 'FeatureEngineering':
        """Carrega scaler, encoders e feature names"""
        scaler_path = Path(self.config.SCALER_PATH)
        encoder_path = Path(self.config.ENCODER_PATH)
        features_path = Path(self.config.FEATURE_NAMES_PATH)

        if not scaler_path.exists() or not encoder_path.exists() or not features_path.exists():
            raise FileNotFoundError(
                "Arquivos de feature engineering não encontrados. "
                "Execute o treinamento primeiro."
            )

        self._scaler = joblib.load(scaler_path)
        self._encoders = joblib.load(encoder_path)

        with open(features_path, 'r') as f:
            features_data = json.load(f)
            # Suportar formato antigo (só lista) e novo (dict)
            if isinstance(features_data, list):
                self._feature_names = features_data
                self._income_bins = None
            else:
                self._feature_names = features_data['feature_names']
                self._income_bins = np.array(features_data['income_bins']) if features_data.get('income_bins') else None

        self._is_fitted = True
        logger.info(f"Feature engineering carregado: {len(self._feature_names)} features")

        return self


# Singleton instance
_feature_engineering: Optional[FeatureEngineering] = None


def get_feature_engineering() -> FeatureEngineering:
    """Factory function para singleton"""
    global _feature_engineering
    if _feature_engineering is None:
        _feature_engineering = FeatureEngineering()
        try:
            _feature_engineering.load()
        except FileNotFoundError:
            logger.warning("Feature engineering não carregado (arquivos não encontrados)")
    return _feature_engineering
