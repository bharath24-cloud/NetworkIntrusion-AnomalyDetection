import sys
sys.path.insert(0, '.')
import time
import numpy as np
import pandas as pd
from src.config import config
from src.preprocessor import DataPreprocessor
from src.models.random_forest_model import RandomForestModel
from src.models.autoencoder_model import DeepAutoencoderModel

print("Loading models...")
prep = DataPreprocessor.load(config.PREPROCESSOR_PATH)
rf = RandomForestModel.load(config.RF_MODEL_PATH)
ae = DeepAutoencoderModel.load(config.AUTOENCODER_PATH, config.AE_CONFIG_PATH)

df = pd.read_csv('data/UNSW_NB15_testing-set.csv', low_memory=False)
print(f"Loaded {len(df)} rows.")

t0 = time.time()
# 1. Separate targets and features
drop_cols = [c for c in df.columns if c.lower() in ("id", "label", "attack_cat", "target", "class")]
features_df = df.drop(columns=drop_cols, errors="ignore")

# 2. Transform features
X_trans = prep.transform(features_df)

# 3. Model predictions
rf_probs = rf.predict_proba(X_trans)
rf_preds = (rf_probs >= 0.5).astype(int)
ae_scores = ae.compute_reconstruction_error(X_trans)
ae_threshold = float(ae.threshold)
ae_preds = (ae_scores > ae_threshold).astype(int)

# 4. Vectorized threat consensus
threat_levels = np.where((rf_preds == 1) & (ae_preds == 1), "CRITICAL INTRUSION",
                np.where((rf_preds == 1) | (ae_preds == 1), "SUSPICIOUS", "NORMAL"))

# 5. Summary statistics
total = len(df)
rf_attacks = int(np.sum(rf_preds == 1))
ae_anomalies = int(np.sum(ae_preds == 1))
critical_count = int(np.sum(threat_levels == "CRITICAL INTRUSION"))

print(f"Full batch vectorized inference took: {time.time()-t0:.2f} seconds!")
print(f"Summary: Total={total}, RF Attacks={rf_attacks}, AE Anomalies={ae_anomalies}, Critical={critical_count}")

# 6. Fast preview table building (first 200 rows)
t0 = time.time()
preview_limit = 200
preview_df = df.iloc[:preview_limit]
has_ground_truth = "label" in df.columns
has_attack_cat = "attack_cat" in df.columns

proto_vals = preview_df["proto"].astype(str).tolist() if "proto" in preview_df.columns else ["-"] * preview_limit
service_vals = preview_df["service"].astype(str).tolist() if "service" in preview_df.columns else ["-"] * preview_limit
state_vals = preview_df["state"].astype(str).tolist() if "state" in preview_df.columns else ["-"] * preview_limit
dur_vals = preview_df["dur"].fillna(0.0).astype(float).tolist() if "dur" in preview_df.columns else [0.0] * preview_limit
sbytes_vals = preview_df["sbytes"].fillna(0).astype(int).tolist() if "sbytes" in preview_df.columns else [0] * preview_limit
gt_vals = preview_df["label"].tolist() if has_ground_truth else [None] * preview_limit
cat_vals = preview_df["attack_cat"].fillna("").astype(str).tolist() if has_attack_cat else [None] * preview_limit

preview_results = []
for i in range(preview_limit):
    preview_results.append({
        "id": i + 1,
        "proto": proto_vals[i],
        "service": service_vals[i],
        "state": state_vals[i],
        "dur": dur_vals[i],
        "sbytes": sbytes_vals[i],
        "rf_pred": int(rf_preds[i]),
        "rf_prob": float(round(rf_probs[i], 4)),
        "ae_score": float(round(ae_scores[i], 4)),
        "threat_level": threat_levels[i],
        "ground_truth": gt_vals[i],
        "attack_cat": cat_vals[i] if cat_vals[i] != "" else None
    })

print(f"Preview dict building (200 rows) took: {time.time()-t0:.3f} seconds!")
