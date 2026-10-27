"""
Data Loading and Inspection Module for UNSW-NB15
Loads train/test datasets, handles missing/infinite values, and strips whitespace.
"""

import os
import logging
from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from src.config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def clean_data_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw DataFrame:
    1. Strips leading/trailing spaces from column names and string cells.
    2. Replaces +/- infinity with NaN.
    3. Replaces whitespace-only string entries with standard '-' or NaN.
    """
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Clean object/string columns
    str_cols = df.select_dtypes(include=['object', 'string']).columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        # Replace empty strings or literal 'nan' strings with standard missing representation
        df[c] = df[c].replace({'': '-', 'nan': '-', 'None': '-'})

    # Clean numerical columns: replace +/- infinity with NaN
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].replace([np.inf, -np.inf], np.nan)

    return df

def load_dataset(
    file_path: str,
    nrows: Optional[int] = None
) -> pd.DataFrame:
    """
    Loads a single UNSW-NB15 CSV dataset file with utf-8-sig encoding,
    performs initial cleaning and reports basic sanity statistics.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    logger.info(f"Loading dataset from: {file_path}")
    df = pd.read_csv(file_path, encoding="utf-8-sig", nrows=nrows, low_memory=False)
    df = clean_data_values(df)
    logger.info(f"Loaded {df.shape[0]:,} rows and {df.shape[1]} columns.")
    return df

def load_train_test_split(
    train_path: Optional[str] = None,
    test_path: Optional[str] = None,
    use_sample: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads both training and testing datasets using existing benchmark splits.
    
    Args:
        train_path: Path to training CSV (overrides config defaults).
        test_path: Path to testing CSV (overrides config defaults).
        use_sample: If True and paths not provided, loads sample datasets.
    
    Returns:
        (train_df, test_df)
    """
    if train_path is None:
        train_path = config.SAMPLE_TRAIN_PATH if use_sample else config.DEFAULT_TRAIN_PATH
    if test_path is None:
        test_path = config.SAMPLE_TEST_PATH if use_sample else config.DEFAULT_TEST_PATH

    train_df = load_dataset(train_path)
    test_df = load_dataset(test_path)

    return train_df, test_df

def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates a diagnostic dictionary summarizing dimensions, class balance,
    missing counts, and categorical cardinality.
    """
    summary = {
        "num_rows": int(len(df)),
        "num_columns": int(len(df.columns)),
        "columns": df.columns.tolist(),
        "missing_counts": df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
        "infinite_counts": {
            col: int(np.isinf(df[col]).sum())
            for col in df.select_dtypes(include=[np.number]).columns
            if np.isinf(df[col]).sum() > 0
        }
    }

    if config.TARGET_COL in df.columns:
        counts = df[config.TARGET_COL].value_counts().to_dict()
        pcts = (df[config.TARGET_COL].value_counts(normalize=True) * 100).round(2).to_dict()
        summary["class_balance"] = {
            "counts": counts,
            "percentages": pcts,
            "normal_count": int(counts.get(0, 0)),
            "attack_count": int(counts.get(1, 0)),
            "attack_ratio": float(round(counts.get(1, 0) / max(len(df), 1), 4))
        }

    if config.ATTACK_CAT_COL in df.columns:
        summary["attack_categories"] = df[config.ATTACK_CAT_COL].value_counts().to_dict()

    return summary
