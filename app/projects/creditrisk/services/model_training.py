"""
Model Training para Credit Risk Scoring
XGBoost com hyperparameter tuning e validação
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from app.projects.creditrisk.config import get_credit_risk_config
from app.projects.creditrisk.services.data_loader import get_data_loader
from app.projects.creditrisk.services.feature_engineering import get_feature_engineering

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Treina e avalia modelo XGBoost"""

    def __init__(self):
        self.config = get_credit_risk_config()
        self.data_loader = get_data_loader()
        self.feature_engineering = get_feature_engineering()
        self.model = None

    def train(self, save_model: bool = True) -> Dict[str, Any]:
        """
        Pipeline completo de treinamento
        Returns: métricas do modelo
        """
        logger.info("=" * 60)
        logger.info("Iniciando treinamento do modelo Credit Risk")
        logger.info("=" * 60)

        # 1. Carregar dados
        logger.info("\n[1/5] Carregando dados...")
        df = self.data_loader.data.copy()
        logger.info(f"Dataset carregado: {len(df):,} registros")

        # 2. Split train/test
        logger.info("\n[2/5] Dividindo dados em train/test...")
        train_df, test_df = self._split_data(df)

        # 3. Feature engineering
        logger.info("\n[3/5] Aplicando feature engineering...")
        X_train, y_train = self._prepare_features(train_df, fit=True)
        X_test, y_test = self._prepare_features(test_df, fit=False)

        logger.info(f"Features shape: {X_train.shape}")
        logger.info(f"Train set: {len(X_train):,} | Test set: {len(X_test):,}")

        # 4. Treinar modelo
        logger.info("\n[4/5] Treinando XGBoost...")
        self.model = self._train_xgboost(X_train, y_train)

        # 5. Avaliar modelo
        logger.info("\n[5/5] Avaliando modelo...")
        metrics = self._evaluate_model(X_test, y_test)

        # Validar AUC mínimo
        if metrics['auc_roc'] < self.config.MIN_AUC_THRESHOLD:
            logger.warning(
                f"AUC ({metrics['auc_roc']:.4f}) abaixo do threshold "
                f"({self.config.MIN_AUC_THRESHOLD})"
            )
        else:
            logger.info(f"AUC ({metrics['auc_roc']:.4f}) acima do threshold!")

        # Salvar modelo e artefatos
        if save_model:
            logger.info("\n[Salvando modelo e artefatos...]")
            self._save_model()
            self.feature_engineering.save()
            self._save_metrics(metrics)

        logger.info("\n" + "=" * 60)
        logger.info("Treinamento concluído!")
        logger.info("=" * 60)

        return metrics

    def _split_data(self, df: pd.DataFrame) -> tuple:
        """Split em train/test com stratify"""
        train_df, test_df = self.data_loader.get_train_test_split(
            test_size=self.config.TEST_SIZE,
            random_state=self.config.XGBOOST_RANDOM_STATE
        )
        return train_df, test_df

    def _prepare_features(self, df: pd.DataFrame, fit: bool = False) -> tuple:
        """Prepara features (fit se treino, transform se test)"""
        X = df.drop(columns=['TARGET'])
        y = df['TARGET']

        if fit:
            X_transformed = self.feature_engineering.fit_transform(X)
        else:
            X_transformed = self.feature_engineering.transform(X)

        # Garantir ordem correta das features
        feature_names = self.feature_engineering._feature_names
        X_final = X_transformed[feature_names]

        return X_final, y

    def _train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
        """Treina XGBoost com hyperparameters do config"""

        # Criar modelo
        model = XGBClassifier(
            max_depth=self.config.XGBOOST_MAX_DEPTH,
            learning_rate=self.config.XGBOOST_LEARNING_RATE,
            n_estimators=self.config.XGBOOST_N_ESTIMATORS,
            min_child_weight=self.config.XGBOOST_MIN_CHILD_WEIGHT,
            subsample=self.config.XGBOOST_SUBSAMPLE,
            colsample_bytree=self.config.XGBOOST_COLSAMPLE_BYTREE,
            scale_pos_weight=self.config.XGBOOST_SCALE_POS_WEIGHT,
            random_state=self.config.XGBOOST_RANDOM_STATE,
            n_jobs=-1,
            eval_metric='logloss'
        )

        # Treinar
        logger.info("Treinando XGBoost...")
        model.fit(
            X_train,
            y_train,
            verbose=False
        )

        logger.info(f"Modelo treinado com {model.n_estimators} árvores")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        logger.info("\nTop 10 features mais importantes:")
        for idx, row in feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        return model

    def _evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """Avalia modelo no test set"""

        # Predições
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        # Métricas
        metrics = {
            'auc_roc': roc_auc_score(y_test, y_pred_proba),
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'training_samples': len(X_test),
            'test_samples': len(X_test)
        }

        # Log métricas
        logger.info("\nMétricas do Modelo:")
        logger.info(f"  AUC-ROC:   {metrics['auc_roc']:.4f}")
        logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
        logger.info(f"  Precision: {metrics['precision']:.4f}")
        logger.info(f"  Recall:    {metrics['recall']:.4f}")
        logger.info(f"  F1-Score:  {metrics['f1_score']:.4f}")

        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info("\nConfusion Matrix:")
        logger.info(f"  TN: {cm[0][0]:,} | FP: {cm[0][1]:,}")
        logger.info(f"  FN: {cm[1][0]:,} | TP: {cm[1][1]:,}")

        # Classification Report
        logger.info("\nClassification Report:")
        logger.info("\n" + classification_report(y_test, y_pred, target_names=['Rejected', 'Approved']))

        return metrics

    def _save_model(self) -> None:
        """Salva modelo treinado"""
        model_path = Path(self.config.MODEL_PATH)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model, model_path)
        logger.info(f"Modelo salvo em: {model_path}")

    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Salva métricas em JSON"""
        metrics_path = Path(self.config.MODEL_PATH).parent / "metrics.json"

        metrics_with_timestamp = {
            **metrics,
            'training_date': datetime.utcnow().isoformat(),
            'model_version': '1.0.0',
            'config': {
                'max_depth': self.config.XGBOOST_MAX_DEPTH,
                'learning_rate': self.config.XGBOOST_LEARNING_RATE,
                'n_estimators': self.config.XGBOOST_N_ESTIMATORS
            }
        }

        with open(metrics_path, 'w') as f:
            json.dump(metrics_with_timestamp, f, indent=2)

        logger.info(f"Métricas salvas em: {metrics_path}")


def main():
    """Script standalone para treinar modelo"""
    import sys
    from pathlib import Path

    # Adicionar root ao path
    root_dir = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(root_dir))

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Treinar
    trainer = ModelTrainer()
    metrics = trainer.train(save_model=True)

    print("\n" + "=" * 60)
    print("Treinamento concluído com sucesso!")
    print(f"AUC-ROC: {metrics['auc_roc']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
