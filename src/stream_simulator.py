"""
Dataset-Based Stream Replay Simulation Engine.
Simulates real-time network flow inspection by replaying UNSW-NB15 test records
at configurable speeds without sniffing live physical network interfaces.
"""

import time
import datetime
from typing import Generator, Dict, Any, Optional
import numpy as np
import pandas as pd
from src.config import config
from src.preprocessor import DataPreprocessor
from src.models.random_forest_model import RandomForestModel
from src.models.autoencoder_model import DeepAutoencoderModel

class StreamSimulator:
    """
    Simulates high-velocity packet/flow stream ingestion from recorded test data.
    Evaluates both Random Forest and Autoencoder models in real time on incoming flows.
    """

    def __init__(
        self,
        test_df: pd.DataFrame,
        preprocessor: DataPreprocessor,
        rf_model: RandomForestModel,
        ae_model: DeepAutoencoderModel,
        alert_threshold_prob: float = 0.5
    ):
        self.test_df = test_df.reset_index(drop=True)
        self.preprocessor = preprocessor
        self.rf_model = rf_model
        self.ae_model = ae_model
        self.alert_threshold_prob = alert_threshold_prob
        self.total_records = len(test_df)

    def generate_stream(
        self,
        start_idx: int = 0,
        max_records: Optional[int] = None,
        delay_seconds: float = 0.1
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Yields evaluated records sequentially to simulate a real-time detection stream.
        """
        end_idx = self.total_records if max_records is None else min(start_idx + max_records, self.total_records)
        
        for idx in range(start_idx, end_idx):
            row_df = self.test_df.iloc[[idx]].copy()
            
            # Ground truth if available
            ground_truth_label = int(row_df[config.TARGET_COL].values[0]) if config.TARGET_COL in row_df.columns else None
            ground_truth_cat = str(row_df[config.ATTACK_CAT_COL].values[0]) if config.ATTACK_CAT_COL in row_df.columns else "Unknown"

            # Transform single record using fitted preprocessor (zero leakage)
            X_sample = self.preprocessor.transform(row_df)

            # Random Forest prediction & probability
            rf_prob = float(self.rf_model.predict_proba(X_sample)[0])
            rf_pred = int(rf_prob >= self.alert_threshold_prob)

            # Autoencoder anomaly score & threshold decision
            ae_score = float(self.ae_model.compute_reconstruction_error(X_sample)[0])
            ae_pred = int(ae_score > self.ae_model.threshold)

            # Determine composite alert severity
            if rf_pred == 1 and ae_pred == 1:
                alert_level = "CRITICAL INTRUSION"
                alert_color = "red"
                status_icon = "🔴"
            elif rf_pred == 1 or ae_pred == 1:
                alert_level = "SUSPICIOUS / ELEVATED"
                alert_color = "orange"
                status_icon = "🟡"
            else:
                alert_level = "NORMAL TRAFFIC"
                alert_color = "green"
                status_icon = "🟢"

            # Create stream event dictionary
            event = {
                "packet_id": idx + 1,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "mode": "dataset-based stream replay",
                "proto": str(row_df.get("proto", pd.Series(["-"])).values[0]),
                "service": str(row_df.get("service", pd.Series(["-"])).values[0]),
                "state": str(row_df.get("state", pd.Series(["-"])).values[0]),
                "dur": float(row_df.get("dur", pd.Series([0.0])).values[0]),
                "sbytes": int(row_df.get("sbytes", pd.Series([0])).values[0]),
                "dbytes": int(row_df.get("dbytes", pd.Series([0])).values[0]),
                "rate": float(row_df.get("rate", pd.Series([0.0])).values[0]),
                "rf_pred": rf_pred,
                "rf_prob": round(rf_prob, 4),
                "ae_score": round(ae_score, 4),
                "ae_threshold": round(self.ae_model.threshold, 4),
                "ae_pred": ae_pred,
                "alert_level": alert_level,
                "alert_color": alert_color,
                "status_icon": status_icon,
                "ground_truth_label": ground_truth_label,
                "ground_truth_cat": ground_truth_cat,
                "is_correct_rf": (rf_pred == ground_truth_label) if ground_truth_label is not None else None,
                "is_correct_ae": (ae_pred == ground_truth_label) if ground_truth_label is not None else None,
            }

            if delay_seconds > 0:
                time.sleep(delay_seconds)

            yield event
