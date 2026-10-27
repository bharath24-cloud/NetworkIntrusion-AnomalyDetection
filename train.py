"""
Training and Evaluation Pipeline for Network Intrusion and Anomaly Detection.
Supports both lightweight sample mode (for typical student laptops) and full benchmark training.
Compares Supervised Random Forest with Unsupervised/Semi-Supervised Deep Autoencoder.
"""

import os
import sys
import argparse
import logging
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.config import config
from src.data_loader import load_dataset, inspect_dataset
from src.preprocessor import DataPreprocessor
from src.models.random_forest_model import RandomForestModel
from src.models.autoencoder_model import DeepAutoencoderModel
from src.evaluation import (
    evaluate_binary_classifier,
    compare_models,
    save_evaluation_metrics,
    CLASS_IMBALANCE_EXPLANATION
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrainPipeline")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Train Network Intrusion & Anomaly Detection Models on UNSW-NB15"
    )
    parser.add_argument(
        "--mode",
        choices=["sample", "full"],
        default="sample",
        help="Use 'sample' for rapid execution on a student laptop, or 'full' for entire UNSW-NB15 dataset."
    )
    parser.add_argument("--train-path", type=str, default=None, help="Custom path to training CSV")
    parser.add_argument("--test-path", type=str, default=None, help="Custom path to testing CSV")
    parser.add_argument("--rf-trees", type=int, default=config.RF_N_ESTIMATORS, help="Number of trees in Random Forest")
    parser.add_argument("--rf-depth", type=int, default=config.RF_MAX_DEPTH, help="Max depth of Random Forest")
    parser.add_argument("--ae-epochs", type=int, default=15, help="Number of Autoencoder training epochs")
    parser.add_argument("--ae-batch-size", type=int, default=config.AE_BATCH_SIZE, help="Batch size for Autoencoder")
    parser.add_argument("--seed", type=int, default=config.RANDOM_SEED, help="Random seed for reproducibility")
    return parser.parse_args()

def run_training_pipeline(args):
    logger.info("=" * 80)
    logger.info("REAL-TIME NETWORK INTRUSION & ANOMALY DETECTION TRAINING PIPELINE")
    logger.info("=" * 80)

    # 1. Determine dataset file paths
    if args.train_path and args.test_path:
        train_path = args.train_path
        test_path = args.test_path
        mode_label = "Custom"
    elif args.mode == "full":
        train_path = config.FULL_TRAIN_PATH
        test_path = config.FULL_TEST_PATH
        mode_label = "Full UNSW-NB15 Benchmark"
    else:
        train_path = config.SAMPLE_TRAIN_PATH
        test_path = config.SAMPLE_TEST_PATH
        mode_label = "Lightweight Student Sample"

    logger.info(f"Execution Mode: {mode_label}")
    logger.info(f"Training Data Path: {train_path}")
    logger.info(f"Testing Data Path:  {test_path}")

    # Check existence
    for p, name in [(train_path, "Training file"), (test_path, "Testing file")]:
        if not os.path.exists(p):
            logger.error(f"{name} not found at {p}. Run 'python data/download_data.py' first.")
            sys.exit(1)

    # 2. Load Raw Datasets
    logger.info("\n--- STEP 1: Loading Datasets ---")
    train_df = load_dataset(train_path)
    test_df = load_dataset(test_path)

    train_stats = inspect_dataset(train_df)
    test_stats = inspect_dataset(test_df)

    logger.info(f"Training Set: {train_stats['num_rows']:,} rows, {train_stats['num_columns']} columns")
    logger.info(f"  -> Normal: {train_stats.get('class_balance', {}).get('normal_count', 'N/A'):,}")
    logger.info(f"  -> Attack: {train_stats.get('class_balance', {}).get('attack_count', 'N/A'):,}")
    logger.info(f"Testing Set:  {test_stats['num_rows']:,} rows, {test_stats['num_columns']} columns")
    logger.info(f"  -> Normal: {test_stats.get('class_balance', {}).get('normal_count', 'N/A'):,}")
    logger.info(f"  -> Attack: {test_stats.get('class_balance', {}).get('attack_count', 'N/A'):,}")

    # 3. Fit Preprocessing Pipeline (Fit ONLY on Train to Prevent Data Leakage)
    logger.info("\n--- STEP 2: Preprocessing (Strict Zero-Leakage Fit on Training Data) ---")
    preprocessor = DataPreprocessor()
    X_train = preprocessor.fit_transform(train_df)
    y_train, train_attack_cats = preprocessor.extract_targets(train_df)

    # Transform testing set with the fitted preprocessor
    X_test = preprocessor.transform(test_df)
    y_test, test_attack_cats = preprocessor.extract_targets(test_df)

    preprocessor.save(config.PREPROCESSOR_PATH)
    logger.info(f"Processed feature matrix dimensions: Train {X_train.shape}, Test {X_test.shape}")

    # 4. Train Model 1: Supervised Random Forest Classifier
    logger.info("\n--- STEP 3: Training Supervised Random Forest Classifier ---")
    rf_model = RandomForestModel(
        n_estimators=args.rf_trees,
        max_depth=args.rf_depth,
        class_weight=config.RF_CLASS_WEIGHT,
        random_state=args.seed
    )
    rf_model.fit(X_train, y_train, feature_names=preprocessor.transformed_feature_names_)
    rf_model.save(config.RF_MODEL_PATH)

    # Evaluate RF on test set
    rf_preds = rf_model.predict(X_test)
    rf_probs = rf_model.predict_proba(X_test)
    rf_metrics = evaluate_binary_classifier(
        y_true=y_test,
        y_pred=rf_preds,
        y_scores=rf_probs,
        model_name="Random Forest Classifier",
        attack_categories=test_attack_cats
    )
    logger.info(f"Random Forest Test F1-Score: {rf_metrics['f1_score']:.4f} | Recall: {rf_metrics['recall']:.4f} | Precision: {rf_metrics['precision']:.4f}")

    # 5. Train Model 2: Semi-Supervised Deep Autoencoder (Only Normal Traffic)
    logger.info("\n--- STEP 4: Training Deep Learning Autoencoder (Trained ONLY on Normal Traffic) ---")
    # Filter normal traffic records from training set
    normal_mask_train = (y_train == 0)
    X_train_normal = X_train[normal_mask_train]
    logger.info(f"Extracted {len(X_train_normal):,} normal traffic records out of {len(X_train):,} total training records.")

    ae_model = DeepAutoencoderModel(
        input_dim=X_train.shape[1],
        hidden_dims=config.AE_HIDDEN_DIMS,
        learning_rate=config.AE_LEARNING_RATE,
        batch_size=args.ae_batch_size,
        epochs=args.ae_epochs,
        threshold_percentile=config.AE_THRESHOLD_PERCENTILE
    )
    ae_model.fit(X_train_normal=X_train_normal)
    ae_model.save(config.AUTOENCODER_PATH, config.AE_CONFIG_PATH)

    # Evaluate Autoencoder on test set
    ae_errors = ae_model.compute_reconstruction_error(X_test)
    ae_preds = (ae_errors > ae_model.threshold).astype(int)
    ae_metrics = evaluate_binary_classifier(
        y_true=y_test,
        y_pred=ae_preds,
        y_scores=ae_errors,
        model_name="Deep Autoencoder",
        attack_categories=test_attack_cats
    )
    logger.info(f"Autoencoder Test F1-Score: {ae_metrics['f1_score']:.4f} | Recall: {ae_metrics['recall']:.4f} | Precision: {ae_metrics['precision']:.4f}")

    # 6. Comparative Model Evaluation Table
    logger.info("\n--- STEP 5: Model Comparison & Evaluation Summary ---")
    comp_df = compare_models(rf_metrics, ae_metrics)
    try:
        from tabulate import tabulate
        print("\n" + tabulate(comp_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    except Exception:
        print("\n" + comp_df.to_string(index=False))

    # Print Confusion Matrices
    print("\nConfusion Matrices:")
    print("Random Forest:")
    print(f"  TN: {rf_metrics['confusion_matrix']['tn']} | FP: {rf_metrics['confusion_matrix']['fp']}")
    print(f"  FN: {rf_metrics['confusion_matrix']['fn']} | TP: {rf_metrics['confusion_matrix']['tp']}")
    print("\nDeep Autoencoder:")
    print(f"  TN: {ae_metrics['confusion_matrix']['tn']} | FP: {ae_metrics['confusion_matrix']['fp']}")
    print(f"  FN: {ae_metrics['confusion_matrix']['fn']} | TP: {ae_metrics['confusion_matrix']['tp']}")

    # Save comprehensive metrics to JSON
    all_metrics = {
        "metadata": {
            "mode": mode_label,
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "features_dimension": int(X_train.shape[1]),
            "rf_trees": args.rf_trees,
            "ae_epochs": args.ae_epochs,
            "ae_threshold": float(ae_model.threshold)
        },
        "random_forest": rf_metrics,
        "autoencoder": ae_metrics,
        "rf_top_features": rf_model.get_feature_importances(15)
    }
    save_evaluation_metrics(all_metrics, config.METRICS_PATH)

    # 7. Class Imbalance Explanation
    print("\n" + "=" * 80)
    print(CLASS_IMBALANCE_EXPLANATION)
    print("=" * 80)
    logger.info("Training pipeline finished successfully! Artifacts saved in models/saved/")

if __name__ == "__main__":
    args = parse_args()
    run_training_pipeline(args)
