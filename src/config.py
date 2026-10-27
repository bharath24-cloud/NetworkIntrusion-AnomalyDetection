"""
Configuration settings for the Network Intrusion and Anomaly Detection project.
Centralizes paths, hyperparameters, random seeds, and feature definitions.
"""

import os
from dataclasses import dataclass

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "saved")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

@dataclass(frozen=True)
class Config:
    """Project-wide configuration constants."""
    
    # Random Seed for Reproducibility
    RANDOM_SEED: int = 42

    # Dataset Paths - Configured for easy switching
    # Full UNSW-NB15 datasets (checks data/ first, then CSV Files/)
    FULL_TRAIN_PATH: str = os.environ.get(
        "UNSW_TRAIN_PATH",
        os.path.join(DATA_DIR, "UNSW_NB15_training-set.csv") if os.path.exists(os.path.join(DATA_DIR, "UNSW_NB15_training-set.csv"))
        else os.path.join(BASE_DIR, "CSV Files", "Training and Testing Sets", "UNSW_NB15_training-set.csv")
    )
    FULL_TEST_PATH: str = os.environ.get(
        "UNSW_TEST_PATH",
        os.path.join(DATA_DIR, "UNSW_NB15_testing-set.csv") if os.path.exists(os.path.join(DATA_DIR, "UNSW_NB15_testing-set.csv"))
        else os.path.join(BASE_DIR, "CSV Files", "Training and Testing Sets", "UNSW_NB15_testing-set.csv")
    )
    
    # Lightweight sample datasets for rapid laptop execution
    SAMPLE_TRAIN_PATH: str = os.path.join(DATA_DIR, "sample_training-set.csv")
    SAMPLE_TEST_PATH: str = os.path.join(DATA_DIR, "sample_testing-set.csv")
    
    # Active default paths (can be overridden via CLI / training options)
    DEFAULT_TRAIN_PATH: str = os.path.join(DATA_DIR, "sample_training-set.csv")
    DEFAULT_TEST_PATH: str = os.path.join(DATA_DIR, "sample_testing-set.csv")

    # Saved Artifact Paths
    PREPROCESSOR_PATH: str = os.path.join(MODELS_DIR, "preprocessor.joblib")
    RF_MODEL_PATH: str = os.path.join(MODELS_DIR, "random_forest_model.joblib")
    AUTOENCODER_PATH: str = os.path.join(MODELS_DIR, "autoencoder_model.pt")
    METRICS_PATH: str = os.path.join(MODELS_DIR, "evaluation_metrics.json")
    AE_CONFIG_PATH: str = os.path.join(MODELS_DIR, "autoencoder_config.json")

    # Target & Metadata Columns to exclude from input feature matrix
    TARGET_COL: str = "label"
    ATTACK_CAT_COL: str = "attack_cat"
    DROP_COLS: tuple = ("id", "attack_cat", "label")

    # Categorical Features in UNSW-NB15
    CATEGORICAL_COLS: tuple = ("proto", "service", "state")

    # Model Hyperparameters
    # Random Forest
    RF_N_ESTIMATORS: int = 100
    RF_MAX_DEPTH: int = 15
    RF_CLASS_WEIGHT: str = "balanced"

    # Deep Autoencoder (PyTorch)
    AE_HIDDEN_DIMS: tuple = (64, 32, 16)  # Encoder: D -> 64 -> 32 -> 16 (bottleneck)
    AE_LEARNING_RATE: float = 1e-3
    AE_BATCH_SIZE: int = 128
    AE_EPOCHS: int = 20
    AE_WEIGHT_DECAY: float = 1e-5
    AE_THRESHOLD_PERCENTILE: float = 95.0  # Percentile of normal errors used as anomaly cutoff

# Global instance
config = Config()
