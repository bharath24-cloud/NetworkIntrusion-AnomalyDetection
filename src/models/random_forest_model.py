"""
Random Forest Classifier for Supervised Network Intrusion Detection.
Trained on labeled network flows (Normal vs. Attack) with balanced class weights
to handle class distribution skew.
"""

import os
import joblib
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from src.config import config

logger = logging.getLogger(__name__)

class RandomForestModel:
    """
    Supervised Random Forest Classifier for intrusion detection.
    Predicts whether a network connection record is Normal (0) or an Attack (1).
    """

    def __init__(
        self,
        n_estimators: int = config.RF_N_ESTIMATORS,
        max_depth: Optional[int] = config.RF_MAX_DEPTH,
        class_weight: str = config.RF_CLASS_WEIGHT,
        random_state: int = config.RANDOM_SEED
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.class_weight = class_weight
        self.random_state = random_state
        
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            class_weight=self.class_weight,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.is_trained = False
        self.feature_names: List[str] = []

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "RandomForestModel":
        """
        Train Random Forest model on training features and binary targets.
        """
        logger.info(f"Training Random Forest (n_estimators={self.n_estimators}, max_depth={self.max_depth})...")
        self.model.fit(X, y)
        self.is_trained = True
        if feature_names:
            self.feature_names = feature_names
        logger.info("Random Forest training complete.")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary class (0: Normal, 1: Attack)."""
        if not self.is_trained:
            raise ValueError("Model is not trained. Call fit() or load() first.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict attack probability P(Attack=1 | X).
        Returns 1D array of probabilities.
        """
        if not self.is_trained:
            raise ValueError("Model is not trained. Call fit() or load() first.")
        # If binary classification, class 1 is index 1
        probs = self.model.predict_proba(X)
        if probs.shape[1] == 2:
            return probs[:, 1]
        return probs[:, 0]

    def get_feature_importances(self, top_n: int = 15) -> List[Tuple[str, float]]:
        """Return the top N most important features."""
        if not self.is_trained or not hasattr(self.model, "feature_importances_"):
            return []
        importances = self.model.feature_importances_
        names = self.feature_names if self.feature_names else [f"feature_{i}" for i in range(len(importances))]
        pairs = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)
        return pairs[:top_n]

    def save(self, filepath: Optional[str] = None):
        """Persist model and metadata to disk."""
        path = filepath or config.RF_MODEL_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "model": self.model,
            "feature_names": self.feature_names,
            "params": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "class_weight": self.class_weight,
                "random_state": self.random_state
            }
        }
        joblib.dump(data, path)
        logger.info(f"Random Forest model saved to: {path}")

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "RandomForestModel":
        """Load trained model from disk."""
        path = filepath or config.RF_MODEL_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"Trained Random Forest model not found at {path}.")
        data = joblib.load(path)
        instance = cls(
            n_estimators=data["params"]["n_estimators"],
            max_depth=data["params"]["max_depth"],
            class_weight=data["params"]["class_weight"],
            random_state=data["params"]["random_state"]
        )
        instance.model = data["model"]
        instance.feature_names = data.get("feature_names", [])
        instance.is_trained = True
        logger.info(f"Random Forest model loaded from: {path}")
        return instance
