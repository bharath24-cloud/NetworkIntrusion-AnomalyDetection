"""
Model Evaluation and Class Imbalance Analysis Module.
Computes Precision, Recall, F1-Score, Confusion Matrix, ROC-AUC, PR-AUC,
and per-attack-category detection rates. Explains class imbalance impact.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
    classification_report
)
from src.config import config

logger = logging.getLogger(__name__)

CLASS_IMBALANCE_EXPLANATION = """
### Academic Context: Why Accuracy is Misleading in Network Intrusion Detection

1. **The Accuracy Paradox**: In real-world enterprise network logs, 95% to 99% of flows are benign
   (Normal). A trivial classifier that unconditionally outputs "Normal" achieves 95-99% accuracy,
   yet fails to detect 100% of malicious intrusions—making the system completely useless.
2. **False Alarms vs. Missed Breaches**:
   - **Precision (Positive Predictive Value)**: What proportion of raised intrusion alerts are actual attacks?
     Low precision leads to *SOC Alert Fatigue*, where security analysts ignore alarms due to false positives.
   - **Recall (Detection Rate / Sensitivity)**: What proportion of actual cyber attacks did the system catch?
     Low recall means stealthy cyber intrusions slip past the perimeter (False Negatives).
   - **F1-Score**: Harmonic mean of Precision and Recall. Unlike arithmetic accuracy, F1 penalizes models
     that sacrifice one metric for the other.
3. **Sub-Category Imbalance in UNSW-NB15**:
   While the aggregate UNSW-NB15 binary split has ~55% attack vs 45% normal records, the underlying
   attack categories are severely skewed. Massive volumes belong to 'Generic' or 'Exploits', while
   dangerous attacks like 'Worms', 'Shellcode', and 'Backdoors' constitute less than 1% of flows.
   Evaluating models solely on overall accuracy conceals total blind spots for rare attack classes.
4. **Threshold Invariance (ROC-AUC & PR-AUC)**:
   ROC-AUC evaluates discriminative separation across all decision thresholds. PR-AUC (Average Precision)
   is especially informative on minority positive cases because it does not depend on the large volume
   of True Negatives.
"""

def evaluate_binary_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None,
    model_name: str = "Classifier",
    attack_categories: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Computes a comprehensive evaluation dictionary for binary intrusion detection.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # Core Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    metrics: Dict[str, Any] = {
        "model_name": model_name,
        "accuracy": float(round(acc, 4)),
        "precision": float(round(prec, 4)),
        "recall": float(round(rec, 4)),
        "f1_score": float(round(f1, 4)),
        "specificity": float(round(spec, 4)),
        "false_positive_rate": float(round(fpr, 4)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "matrix": [[int(tn), int(fp)], [int(fn), int(tp)]]
        },
        "sample_counts": {
            "total": int(len(y_true)),
            "actual_normal": int(tn + fp),
            "actual_attack": int(fn + tp),
            "predicted_normal": int(tn + fn),
            "predicted_attack": int(fp + tp)
        }
    }

    # Area Under ROC and PR Curves if continuous anomaly scores or probabilities provided
    if y_scores is not None and len(np.unique(y_true)) > 1:
        try:
            auc = roc_auc_score(y_true, y_scores)
            avg_prec = average_precision_score(y_true, y_scores)
            metrics["roc_auc"] = float(round(auc, 4))
            metrics["pr_auc"] = float(round(avg_prec, 4))

            # Store sampled ROC points for plotting (downsample if very large)
            fpr_arr, tpr_arr, _ = roc_curve(y_true, y_scores)
            step = max(1, len(fpr_arr) // 100)
            metrics["roc_curve"] = {
                "fpr": fpr_arr[::step].tolist(),
                "tpr": tpr_arr[::step].tolist()
            }

            p_arr, r_arr, _ = precision_recall_curve(y_true, y_scores)
            step_pr = max(1, len(p_arr) // 100)
            metrics["pr_curve"] = {
                "precision": p_arr[::step_pr].tolist(),
                "recall": r_arr[::step_pr].tolist()
            }
        except Exception as e:
            logger.warning(f"Could not compute curve metrics: {e}")
            metrics["roc_auc"] = None
            metrics["pr_auc"] = None

    # Granular Per-Attack Category Detection Rates
    if attack_categories is not None:
        category_metrics = {}
        cats = attack_categories.astype(str).str.strip().unique()
        for cat in cats:
            mask = (attack_categories == cat)
            cat_total = int(mask.sum())
            if cat.lower() == "normal":
                # For normal, correct prediction is y_pred == 0
                cat_correct = int((y_pred[mask] == 0).sum())
                rate = cat_correct / cat_total if cat_total > 0 else 0.0
                category_metrics[cat] = {
                    "total": cat_total,
                    "correct": cat_correct,
                    "accuracy_or_recall": float(round(rate, 4)),
                    "type": "Normal (Specificity)"
                }
            else:
                # For attacks, correct detection is y_pred == 1
                cat_detected = int((y_pred[mask] == 1).sum())
                det_rate = cat_detected / cat_total if cat_total > 0 else 0.0
                category_metrics[cat] = {
                    "total": cat_total,
                    "detected": cat_detected,
                    "detection_rate": float(round(det_rate, 4)),
                    "type": "Attack Category"
                }
        metrics["per_category_analysis"] = category_metrics

    return metrics

def compare_models(
    rf_metrics: Dict[str, Any],
    ae_metrics: Dict[str, Any]
) -> pd.DataFrame:
    """
    Creates a side-by-side comparison DataFrame of Random Forest and Autoencoder.
    """
    comparison_data = {
        "Metric": [
            "Model Paradigm",
            "Target Problem",
            "Precision (Alert Reliability)",
            "Recall (Attack Detection)",
            "F1-Score (Harmonic Mean)",
            "Specificity (Benign Traffic Accuracy)",
            "False Positive Rate (FPR)",
            "ROC-AUC Score",
            "PR-AUC (Average Precision)"
        ],
        "Random Forest": [
            "Supervised Learning",
            "Normal vs. Known Attacks",
            f"{rf_metrics.get('precision', 0):.4f}",
            f"{rf_metrics.get('recall', 0):.4f}",
            f"{rf_metrics.get('f1_score', 0):.4f}",
            f"{rf_metrics.get('specificity', 0):.4f}",
            f"{rf_metrics.get('false_positive_rate', 0):.4f}",
            f"{rf_metrics.get('roc_auc', 'N/A')}",
            f"{rf_metrics.get('pr_auc', 'N/A')}"
        ],
        "Deep Autoencoder": [
            "Semi-Supervised / Unsupervised",
            "Anomaly & Novel Attack Detection",
            f"{ae_metrics.get('precision', 0):.4f}",
            f"{ae_metrics.get('recall', 0):.4f}",
            f"{ae_metrics.get('f1_score', 0):.4f}",
            f"{ae_metrics.get('specificity', 0):.4f}",
            f"{ae_metrics.get('false_positive_rate', 0):.4f}",
            f"{ae_metrics.get('roc_auc', 'N/A')}",
            f"{ae_metrics.get('pr_auc', 'N/A')}"
        ]
    }
    return pd.DataFrame(comparison_data)

def save_evaluation_metrics(metrics: Dict[str, Any], filepath: Optional[str] = None):
    """Save metrics to JSON file."""
    path = filepath or config.METRICS_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Evaluation metrics saved to: {path}")

def load_evaluation_metrics(filepath: Optional[str] = None) -> Dict[str, Any]:
    """Load metrics from JSON file."""
    path = filepath or config.METRICS_PATH
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)
