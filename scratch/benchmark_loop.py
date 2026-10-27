import sys
sys.path.insert(0, '.')
import time
import numpy as np
import pandas as pd
from app import app, safe_float, safe_int, safe_label

df = pd.read_csv('data/UNSW_NB15_testing-set.csv', low_memory=False)
rf_probs = np.random.rand(len(df))
rf_preds = (rf_probs >= 0.5).astype(int)
ae_scores = np.random.rand(len(df))
ae_threshold = 0.0865
ae_preds = (ae_scores > ae_threshold).astype(int)

print(f"Testing dictionary building for {len(df)} rows...")
t0 = time.time()
results = []
has_ground_truth = "label" in df.columns

for i in range(len(df)):
    rf_p = int(rf_preds[i])
    ae_p = int(ae_preds[i])
    
    if rf_p == 1 and ae_p == 1:
        threat = "CRITICAL INTRUSION"
    elif rf_p == 1 or ae_p == 1:
        threat = "SUSPICIOUS"
    else:
        threat = "NORMAL"

    item = {
        "id": i + 1,
        "proto": str(df.get("proto", pd.Series(["-"])).iloc[i]),
        "service": str(df.get("service", pd.Series(["-"])).iloc[i]),
        "state": str(df.get("state", pd.Series(["-"])).iloc[i]),
        "dur": safe_float(df.get("dur", pd.Series([0.0])).iloc[i]),
        "sbytes": safe_int(df.get("sbytes", pd.Series([0])).iloc[i]),
        "rf_pred": rf_p,
        "rf_prob": float(rf_probs[i]),
        "ae_score": float(ae_scores[i]),
        "threat_level": threat,
        "ground_truth": safe_label(df["label"].iloc[i]) if has_ground_truth else None,
        "attack_cat": str(df["attack_cat"].iloc[i]) if "attack_cat" in df.columns and not pd.isna(df["attack_cat"].iloc[i]) else None
    }
    results.append(item)

print(f"Dictionary building took {time.time()-t0:.2f}s")

print("Now testing Jinja2 rendering of predict.html with 82k rows...")
t0 = time.time()
with app.app_context():
    from flask import render_template
    summary = {
        "total": len(results),
        "rf_attacks": 100,
        "ae_anomalies": 100,
        "critical_count": 50,
        "attack_rate": 50.0
    }
    html = render_template(
        "predict.html",
        active_page="predict",
        results=results,
        summary=summary,
        has_ground_truth=has_ground_truth,
        ae_threshold=ae_threshold
    )
print(f"Jinja2 rendering took {time.time()-t0:.2f}s, output HTML size = {len(html)/1024/1024:.2f} MB")
