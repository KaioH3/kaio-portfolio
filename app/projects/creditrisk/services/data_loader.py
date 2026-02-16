"""
Data Loader para Credit Card Approval Dataset
Carrega e processa os CSVs do Kaggle
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Optional, Tuple

from app.projects.creditrisk.config import get_credit_risk_config

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Singleton service para carregar dataset do Kaggle
    Dataset: Credit Card Approval Prediction (913 upvotes, 97k downloads)
    """

    def __init__(self):
        self.config = get_credit_risk_config()
        self._data: Optional[pd.DataFrame] = None
        self._is_loaded = False

    @property
    def data(self) -> pd.DataFrame:
        """Lazy loading do dataset"""
        if not self._is_loaded:
            self._load_data()
        return self._data

    def _load_data(self) -> None:
        """Carrega e processa os dois CSVs"""
        try:
            logger.info("Carregando dataset de Credit Card Approval...")

            # Verificar se arquivos existem
            app_path = Path(self.config.DATASET_PATH_APPLICATION)
            credit_path = Path(self.config.DATASET_PATH_CREDIT)

            if not app_path.exists() or not credit_path.exists():
                raise FileNotFoundError(
                    f"Dataset não encontrado. "
                    f"Baixe de: https://www.kaggle.com/datasets/rikdifos/credit-card-approval-prediction\n"
                    f"Esperado em:\n"
                    f"  - {app_path}\n"
                    f"  - {credit_path}"
                )

            # Carregar application_record.csv
            df_app = pd.read_csv(app_path)
            logger.info(f"Application records carregados: {len(df_app):,} registros")

            # Carregar credit_record.csv
            df_credit = pd.read_csv(credit_path)
            logger.info(f"Credit records carregados: {len(df_credit):,} registros")

            # Processar credit history para criar target
            df_processed = self._process_credit_history(df_app, df_credit)

            self._data = df_processed
            self._is_loaded = True

            logger.info(f"Dataset processado: {len(self._data):,} registros, {len(self._data.columns)} features")
            logger.info(f"Target distribution: {self._data['TARGET'].value_counts().to_dict()}")

        except Exception as e:
            logger.error(f"Erro ao carregar dataset: {e}")
            raise

    def _process_credit_history(self, df_app: pd.DataFrame, df_credit: pd.DataFrame) -> pd.DataFrame:
        """
        Processa histórico de crédito para criar target
        TARGET = 1 (Good) se nunca teve atraso > 60 dias
        TARGET = 0 (Bad) se teve atraso > 60 dias
        """
        # Criar target baseado em STATUS
        # C = Closed, X = Unknown, 0 = 1-29 days overdue, 1 = 30-59 days, 2 = 60-89 days, etc.
        df_credit['IS_BAD'] = df_credit['STATUS'].isin(['2', '3', '4', '5'])

        # Agrupar por ID - cliente é BAD se teve algum atraso > 60 dias
        bad_clients = df_credit.groupby('ID')['IS_BAD'].max().reset_index()
        bad_clients.columns = ['ID', 'HAD_BAD_DEBT']

        # Merge com application data
        df_merged = df_app.merge(bad_clients, on='ID', how='left')

        # Clientes sem histórico = considerar GOOD (conservador, pode ajustar)
        df_merged['HAD_BAD_DEBT'].fillna(0, inplace=True)

        # TARGET: 1 = Good (approved), 0 = Bad (rejected)
        df_merged['TARGET'] = (df_merged['HAD_BAD_DEBT'] == 0).astype(int)

        # Limpar e preparar features
        df_merged = self._clean_features(df_merged)

        return df_merged

    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e prepara features"""

        # Remover colunas desnecessárias
        df = df.drop(columns=['ID', 'HAD_BAD_DEBT'], errors='ignore')

        # Converter DAYS_BIRTH para AGE em anos
        df['AGE_YEARS'] = (-df['DAYS_BIRTH'] / 365).astype(int)

        # Converter DAYS_EMPLOYED (negativo = dias desde início do emprego)
        # Valores positivos (365243) indicam desempregado - substituir por 0
        df['EMPLOYMENT_DAYS'] = df['DAYS_EMPLOYED'].apply(
            lambda x: x if x < 0 else 0
        )

        # Converter FLAG_OWN_CAR e FLAG_OWN_REALTY para boolean
        df['HAS_CAR'] = (df['FLAG_OWN_CAR'] == 'Y').astype(int)
        df['HAS_PROPERTY'] = (df['FLAG_OWN_REALTY'] == 'Y').astype(int)

        # Renomear colunas para padronizar
        df = df.rename(columns={
            'CODE_GENDER': 'GENDER',
            'CNT_FAM_MEMBERS': 'FAMILY_MEMBERS',
            'CNT_CHILDREN': 'CHILDREN_COUNT',
            'AMT_INCOME_TOTAL': 'ANNUAL_INCOME',
            'NAME_INCOME_TYPE': 'INCOME_TYPE',
            'NAME_EDUCATION_TYPE': 'EDUCATION_LEVEL',
            'NAME_FAMILY_STATUS': 'FAMILY_STATUS',
            'NAME_HOUSING_TYPE': 'HOUSING_TYPE',
            'FLAG_MOBIL': 'HAS_MOBILE',
            'FLAG_WORK_PHONE': 'HAS_WORK_PHONE',
            'FLAG_PHONE': 'HAS_PHONE',
            'FLAG_EMAIL': 'HAS_EMAIL',
            'OCCUPATION_TYPE': 'OCCUPATION_TYPE'
        })

        # Remover colunas originais que foram transformadas
        df = df.drop(columns=['DAYS_BIRTH', 'DAYS_EMPLOYED', 'FLAG_OWN_CAR', 'FLAG_OWN_REALTY'], errors='ignore')

        # Tratar valores nulos em OCCUPATION_TYPE
        df['OCCUPATION_TYPE'].fillna('Unknown', inplace=True)

        # Remover outliers extremos de income
        df = df[df['ANNUAL_INCOME'] < df['ANNUAL_INCOME'].quantile(0.99)]

        # Remover idades impossíveis
        df = df[(df['AGE_YEARS'] >= 18) & (df['AGE_YEARS'] <= 100)]

        logger.info(f"Features após limpeza: {df.shape}")
        logger.info(f"Features disponíveis: {list(df.columns)}")

        return df

    def get_train_test_split(self, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Retorna train/test split"""
        from sklearn.model_selection import train_test_split

        df = self.data.copy()

        X = df.drop(columns=['TARGET'])
        y = df['TARGET']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        train_df = pd.concat([X_train, y_train], axis=1)
        test_df = pd.concat([X_test, y_test], axis=1)

        logger.info(f"Train set: {len(train_df):,} | Test set: {len(test_df):,}")

        return train_df, test_df

    def get_feature_names(self) -> list:
        """Retorna nomes das features (exceto TARGET)"""
        return [col for col in self.data.columns if col != 'TARGET']

    def get_stats(self) -> dict:
        """Retorna estatísticas do dataset"""
        df = self.data
        return {
            'total_records': len(df),
            'total_features': len(self.get_feature_names()),
            'target_distribution': df['TARGET'].value_counts().to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_features': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_features': df.select_dtypes(include=['object']).columns.tolist()
        }


# Singleton instance
_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """Factory function para singleton"""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader
