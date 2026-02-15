
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
import ta
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

from strategies.base import BaseStrategy, StrategyMetadata
from utils.validation import (
    ValidationError,
    validate_window_size,
    validate_ratio,
    validate_range,
    validate_positive,
)
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIStrategyConfig:
    """
    Configuración para la estrategia AI basada en Gradient Boosting.

    Attributes:
        lookback_window: Ventana de lookback para indicadores (5-100).
        training_size_pct: Porcentaje de datos para entrenamiento (0.3-0.9).
        prediction_threshold: Umbral de probabilidad para señales (0.5-0.9).
        learning_rate: Tasa de aprendizaje del modelo (0.01-1.0).
        max_iter: Número máximo de iteraciones (10-500).
        max_depth: Profundidad máxima del árbol (1-50).
        model_path: Ruta opcional para cargar/guardar modelo persistido.
    """
    lookback_window: int = 14
    training_size_pct: float = 0.6
    prediction_threshold: float = 0.55

    # Gradient Boosting Hyperparameters
    learning_rate: float = 0.1
    max_iter: int = 100
    max_depth: int = 10

    # Persistencia del modelo
    model_path: Optional[str] = None

    def __post_init__(self) -> None:
        """Valida los parámetros de configuración."""
        validate_window_size(self.lookback_window, "lookback_window", min_window=5, max_window=100)
        validate_ratio(self.training_size_pct, "training_size_pct", min_val=0.3, max_val=0.9)
        validate_ratio(self.prediction_threshold, "prediction_threshold", min_val=0.5, max_val=0.9)
        validate_range(self.learning_rate, 0.01, 1.0, "learning_rate")
        validate_range(self.max_iter, 10, 500, "max_iter")
        validate_range(self.max_depth, 1, 50, "max_depth")


class AIStrategy(BaseStrategy[AIStrategyConfig]):
    """
    AI Strategy using Gradient Boosting (HistGradientBoostingClassifier).
    Predicts if the next close will be higher than the current close.

    Features:
    - Persistencia del modelo para evitar reentrenamiento
    - Validación de parámetros
    - Logging de entrenamiento y predicciones
    """
    name: str = "AI_GB_STRATEGY"

    def __init__(self, config: AIStrategyConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)
        self.is_trained = False
        self._feature_cols: list[str] = []

        # Intentar cargar modelo persistido si existe
        if config.model_path and Path(config.model_path).exists():
            self._load_model(config.model_path)
        else:
            self.model = HistGradientBoostingClassifier(
                learning_rate=config.learning_rate,
                max_iter=config.max_iter,
                max_depth=config.max_depth,
                random_state=42
            )
            logger.debug("Modelo AI inicializado (no entrenado)")

    def _load_model(self, path: str) -> None:
        """Carga un modelo persistido desde disco."""
        try:
            model_data = joblib.load(path)
            self.model = model_data["model"]
            self._feature_cols = model_data.get("feature_cols", [])
            self.is_trained = True
            logger.info(f"Modelo AI cargado desde {path}")
        except Exception as e:
            logger.warning(f"No se pudo cargar el modelo desde {path}: {e}")
            self.model = HistGradientBoostingClassifier(
                learning_rate=self.config.learning_rate,
                max_iter=self.config.max_iter,
                max_depth=self.config.max_depth,
                random_state=42
            )
            self.is_trained = False

    def save_model(self, path: str) -> None:
        """
        Guarda el modelo entrenado a disco.

        Args:
            path: Ruta donde guardar el modelo.

        Raises:
            ValidationError: Si el modelo no está entrenado.
        """
        if not self.is_trained:
            raise ValidationError("No se puede guardar un modelo no entrenado")

        model_data = {
            "model": self.model,
            "feature_cols": self._feature_cols,
            "config": self.config,
        }
        joblib.dump(model_data, path)
        logger.info(f"Modelo AI guardado en {path}")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing columns: {missing}")

        data = df.copy()
        
        # 1. Feature Engineering
        data = self._add_features(data)
        
        valid_data = data.dropna()
        
        if len(valid_data) < 100: # Not enough data to train
             data["signal"] = 0
             return data

        # 2. Prepare Targets (1 if Close[t+1] > Close[t], else 0)
        valid_data = valid_data.copy()
        valid_data["target"] = (valid_data["close"].shift(-1) > valid_data["close"]).astype(int)
        
        # Split Train/Inference
        train_data = valid_data.iloc[:-1].copy()
        
        # Features columns
        feature_cols = [c for c in train_data.columns if c not in required_cols and c != "target" and c != "signal"]
        
        X = train_data[feature_cols]
        y = train_data["target"]
        
        # 3. Train/Test Split with gap to prevent data leakage
        split_idx = int(len(train_data) * self.config.training_size_pct)

        # Gap = max lookback used in features (lagged features use up to 3 + lookback_window)
        gap = self.config.lookback_window + 3

        X_train = X.iloc[:split_idx]
        y_train = y.iloc[:split_idx]

        # Train
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Predict on ALL valid data
        X_all = valid_data[feature_cols]
        all_probs = self.model.predict_proba(X_all)[:, 1]

        valid_data["prob_up"] = all_probs
        valid_data["signal"] = 0

        long_cond = valid_data["prob_up"] > self.config.prediction_threshold
        short_cond = valid_data["prob_up"] < (1 - self.config.prediction_threshold)

        valid_data.loc[long_cond, "signal"] = 1
        valid_data.loc[short_cond, "signal"] = -1

        # Zero out signals in training period AND gap period
        gap_end = min(split_idx + gap, len(valid_data))
        valid_data.iloc[:gap_end, valid_data.columns.get_loc("signal")] = 0
        
        # Merge back
        data["signal"] = 0
        data.loc[valid_data.index, "signal"] = valid_data["signal"]
        
        return data

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Basic Indicators
        df["rsi"] = ta.momentum.rsi(df["close"], window=self.config.lookback_window)
        
        macd = ta.trend.MACD(df["close"])
        df["macd"] = macd.macd()
        df["macd_diff"] = macd.macd_diff()
        
        bb = ta.volatility.BollingerBands(df["close"])
        df["bb_width"] = bb.bollinger_wband()
        
        df["pct_change"] = df["close"].pct_change()
        df["volatility"] = df["close"].rolling(window=self.config.lookback_window).std()
        
        # Volume Change
        df["vol_change"] = df["volume"].pct_change()
        
        # Lagged Features (Context)
        for lag in [1, 2, 3]:
            df[f"pct_change_lag_{lag}"] = df["pct_change"].shift(lag)
            df[f"rsi_lag_{lag}"] = df["rsi"].shift(lag)
            df[f"vol_change_lag_{lag}"] = df["vol_change"].shift(lag)
            
        return df
