"""
Data Preprocessing Pipeline for Network Intrusion Detection
Ensures strict prevention of data leakage by fitting encoders and scalers
EXCLUSIVELY on training data, handling missing/infinite values, and
safely transforming testing or real-time streaming data.
"""

import os
import joblib
import logging
from typing import Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from src.config import config
from src.data_loader import clean_data_values

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    Robust feature preprocessor fitted strictly on training data.
    Guarantees no data leakage across train, test, and streaming records.
    """

    def __init__(self):
        self.num_imputer = SimpleImputer(strategy="median")
        self.cat_imputer = SimpleImputer(strategy="constant", fill_value="-")
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        
        self.num_cols: List[str] = []
        self.cat_cols: List[str] = []
        self.feature_names_in_: List[str] = []
        self.transformed_feature_names_: List[str] = []
        self.is_fitted: bool = False

    def _extract_feature_columns(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Identify numerical and categorical input features, excluding targets/IDs."""
        candidate_cols = [c for c in df.columns if c not in config.DROP_COLS]
        
        cat_cols = [c for c in candidate_cols if c in config.CATEGORICAL_COLS or df[c].dtype == "object"]
        num_cols = [c for c in candidate_cols if c not in cat_cols]
        return num_cols, cat_cols

    def fit(self, train_df: pd.DataFrame) -> "DataPreprocessor":
        """
        Fit imputers, scaler, and one-hot encoder ONLY on training data.
        """
        df = clean_data_values(train_df)
        self.num_cols, self.cat_cols = self._extract_feature_columns(df)
        self.feature_names_in_ = self.num_cols + self.cat_cols
        
        logger.info(f"Fitting preprocessor on {len(self.num_cols)} numerical and {len(self.cat_cols)} categorical features...")

        # 1. Fit numerical imputer and scaler
        if self.num_cols:
            num_data = df[self.num_cols].values
            imputed_num = self.num_imputer.fit_transform(num_data)
            self.scaler.fit(imputed_num)

        # 2. Fit categorical imputer and encoder
        if self.cat_cols:
            cat_data = df[self.cat_cols].astype(str).values
            imputed_cat = self.cat_imputer.fit_transform(cat_data)
            self.encoder.fit(imputed_cat)
            encoded_cat_names = self.encoder.get_feature_names_out(self.cat_cols).tolist()
        else:
            encoded_cat_names = []

        self.transformed_feature_names_ = self.num_cols + encoded_cat_names
        self.is_fitted = True
        logger.info(f"Preprocessor fitted. Transformed feature vector dimension: {len(self.transformed_feature_names_)}")
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform arbitrary data (test set or streaming record) using fitted parameters.
        Does not fit anything new, preventing data leakage.
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted on training data before calling transform().")

        df = clean_data_values(df)

        # Ensure all expected columns exist (fill missing columns with default values if necessary)
        df_clean = df.copy()
        for col in self.num_cols:
            if col not in df_clean.columns:
                df_clean[col] = np.nan
        for col in self.cat_cols:
            if col not in df_clean.columns:
                df_clean[col] = "-"

        # 1. Transform numerical
        if self.num_cols:
            num_data = df_clean[self.num_cols].values
            imputed_num = self.num_imputer.transform(num_data)
            scaled_num = self.scaler.transform(imputed_num)
        else:
            scaled_num = np.empty((len(df_clean), 0))

        # 2. Transform categorical
        if self.cat_cols:
            cat_data = df_clean[self.cat_cols].astype(str).values
            imputed_cat = self.cat_imputer.transform(cat_data)
            encoded_cat = self.encoder.transform(imputed_cat)
        else:
            encoded_cat = np.empty((len(df_clean), 0))

        # Combine
        features = np.hstack([scaled_num, encoded_cat])
        return features

    def fit_transform(self, train_df: pd.DataFrame) -> np.ndarray:
        """Fit on train and transform."""
        return self.fit(train_df).transform(train_df)

    def extract_targets(self, df: pd.DataFrame) -> Tuple[Optional[np.ndarray], Optional[pd.Series]]:
        """
        Extracts binary labels (y) and attack categories if available.
        """
        y = df[config.TARGET_COL].values if config.TARGET_COL in df.columns else None
        attack_cats = df[config.ATTACK_CAT_COL] if config.ATTACK_CAT_COL in df.columns else None
        return y, attack_cats

    def save(self, filepath: Optional[str] = None):
        """Persist fitted preprocessor to disk."""
        path = filepath or config.PREPROCESSOR_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self, path)
        logger.info(f"Preprocessor saved to: {path}")

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "DataPreprocessor":
        """Load preprocessor from disk."""
        path = filepath or config.PREPROCESSOR_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fitted preprocessor not found at {path}. Run training first.")
        preprocessor = joblib.load(path)
        logger.info(f"Preprocessor loaded from: {path}")
        return preprocessor
