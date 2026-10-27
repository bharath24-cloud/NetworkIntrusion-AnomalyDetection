"""
Flask Web Application: Real-Time Network Intrusion and Anomaly Detection
Uses pre-trained Random Forest and Deep PyTorch Autoencoder models on the UNSW-NB15 dataset.
"""

import os
import io
import sys
import time
import json
import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_file,
    session
)

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.config import config
from src.preprocessor import DataPreprocessor
from src.models.random_forest_model import RandomForestModel
from src.models.autoencoder_model import DeepAutoencoderModel
from src.evaluation import load_evaluation_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FlaskNIDS")

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "nids-cybersecurity-secret-key-2026"
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload (supports full UNSW-NB15 CSVs)

# Global Storage for Loaded Pipeline Artifacts (Loaded ONCE at startup)
pipeline_state = {
    "is_loaded": False,
    "preprocessor": None,
    "rf_model": None,
    "ae_model": None,
    "metrics": {},
    "test_data": None,
    "error_message": None
}

# Temporary in-memory cache for batch predictions export
last_prediction_results = []

def load_models_at_startup():
    """
    Loads pre-trained model artifacts from disk when the Flask app starts.
    STRICT RULE: Only loads existing saved models; NEVER retrains at startup.
    """
    logger.info("Initializing Flask app: loading pre-trained models and preprocessors from disk...")
    required_files = [
        config.PREPROCESSOR_PATH,
        config.RF_MODEL_PATH,
        config.AUTOENCODER_PATH,
        config.AE_CONFIG_PATH,
        config.METRICS_PATH
    ]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        msg = f"Missing required model artifacts: {', '.join([os.path.basename(m) for m in missing])}. Run 'python train.py --mode sample' first."
        logger.error(msg)
        pipeline_state["is_loaded"] = False
        pipeline_state["error_message"] = msg
        return

    try:
        pipeline_state["preprocessor"] = DataPreprocessor.load(config.PREPROCESSOR_PATH)
        pipeline_state["rf_model"] = RandomForestModel.load(config.RF_MODEL_PATH)
        pipeline_state["ae_model"] = DeepAutoencoderModel.load(config.AUTOENCODER_PATH, config.AE_CONFIG_PATH)
        pipeline_state["metrics"] = load_evaluation_metrics(config.METRICS_PATH)
        
        # Load test dataset in memory for the replay demo
        test_path = config.SAMPLE_TEST_PATH if os.path.exists(config.SAMPLE_TEST_PATH) else config.DEFAULT_TEST_PATH
        if os.path.exists(test_path):
            pipeline_state["test_data"] = pd.read_csv(test_path, encoding="utf-8-sig", low_memory=False)
            logger.info(f"Loaded holdout test dataset for replay demo: {len(pipeline_state['test_data']):,} rows.")
        else:
            logger.warning(f"Holdout test CSV not found at {test_path}.")

        pipeline_state["is_loaded"] = True
        logger.info("Successfully loaded all models and preprocessors into Flask memory!")
    except Exception as e:
        logger.exception("Failed to load model artifacts:")
        pipeline_state["is_loaded"] = False
        pipeline_state["error_message"] = f"Error loading models: {str(e)}"

# Execute loading
load_models_at_startup()

def safe_float(val, default=0.0):
    try:
        if pd.isna(val):
            return default
        return float(val)
    except Exception:
        return default

def safe_int(val, default=0):
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except Exception:
        return default

def safe_label(val):
    if pd.isna(val):
        return None
    try:
        return int(float(val))
    except Exception:
        return None

def validate_uploaded_csv(df: pd.DataFrame) -> Optional[str]:
    """
    Validates uploaded CSV file structure.
    Returns error message if invalid, or None if acceptable.
    """
    if df.empty:
        return "The uploaded CSV file is completely empty. Please upload a file containing network flow records."

    if len(df.columns) < 3:
        return f"The uploaded CSV only contains {len(df.columns)} column(s). UNSW-NB15 flow datasets require standard network attributes."

    if len(df) > 200000:
        return f"The uploaded CSV contains {len(df):,} rows, which exceeds the maximum in-memory limit (200,000 rows). Please upload a smaller slice or use the 5,000-row sample test dataset."

    # Check for presence of at least some common network flow columns (case-insensitive)
    expected_sample = {"proto", "service", "state", "dur", "sbytes", "dbytes", "rate", "spkts", "dpkts", "sttl"}
    clean_cols = set(c.strip().lower() for c in df.columns)
    overlap = expected_sample.intersection(clean_cols)
    if len(overlap) == 0:
        return (
            "The uploaded CSV headers do not match network flow telemetry. "
            "Expected UNSW-NB15 attributes such as 'proto', 'service', 'state', 'sbytes', 'dbytes', etc. "
            f"Found columns: {list(df.columns[:8])}..."
        )

    return None

# ==============================================================================
# ROUTES
# ==============================================================================

@app.route("/")
def index():
    """Dashboard view displaying saved evaluation metrics and confusion matrices."""
    if not pipeline_state["is_loaded"]:
        flash(pipeline_state.get("error_message", "Models not loaded. Run 'python train.py' to generate artifacts."), "danger")
        return render_template(
            "index.html",
            active_page="dashboard",
            rf={},
            ae={},
            metadata={},
            top_features=[]
        )

    metrics = pipeline_state["metrics"]
    rf = metrics.get("random_forest", {})
    ae = metrics.get("autoencoder", {})
    metadata = metrics.get("metadata", {})
    top_features = metrics.get("rf_top_features", [])

    return render_template(
        "index.html",
        active_page="dashboard",
        rf=rf,
        ae=ae,
        metadata=metadata,
        top_features=top_features
    )

@app.route("/predict", methods=["GET", "POST"])
def predict():
    """CSV upload and prediction interface."""
    global last_prediction_results

    if not pipeline_state["is_loaded"]:
        flash("Models are not loaded. Run 'python train.py --mode sample' first.", "danger")
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template(
            "predict.html",
            active_page="predict",
            results=None,
            summary=None
        )

    # Handle file upload POST
    if "file" not in request.files:
        flash("No file part found in upload request. Please select a valid CSV file.", "warning")
        return redirect(url_for("predict"))

    file = request.files["file"]
    if not file or file.filename == "":
        flash("No file selected. Please choose a CSV file before clicking 'Preprocess & Run Predictions'.", "warning")
        return redirect(url_for("predict"))

    if not file.filename.lower().endswith(".csv"):
        flash(f"Invalid file format '{file.filename}'. Please upload a file with a .csv extension.", "danger")
        return redirect(url_for("predict"))

    try:
        # Read CSV into pandas DataFrame with low_memory=False to support large files
        df = pd.read_csv(file, encoding="utf-8-sig", low_memory=False)
        df.columns = df.columns.str.strip()
    except Exception as e:
        logger.error(f"Failed to parse uploaded CSV: {e}")
        flash(f"Failed to parse CSV file: {str(e)}", "danger")
        return redirect(url_for("predict"))

    # Validate CSV schema
    err = validate_uploaded_csv(df)
    if err:
        flash(err, "danger")
        return redirect(url_for("predict"))

    return process_and_render_predictions(df, source_filename=file.filename)

@app.route("/predict/sample", methods=["POST"])
def predict_sample():
    """Quick demo: loads 50 records from holdout test set and scores them."""
    if not pipeline_state["is_loaded"] or pipeline_state["test_data"] is None:
        flash("Test dataset is unavailable. Run 'python data/download_data.py' first.", "danger")
        return redirect(url_for("predict"))

    test_df = pipeline_state["test_data"]
    sample_df = test_df.sample(min(50, len(test_df)), random_state=int(time.time()) % 1000).reset_index(drop=True)
    flash(f"Successfully loaded {len(sample_df)} test flow records from the holdout benchmark.", "success")
    return process_and_render_predictions(sample_df, source_filename="Holdout Benchmark Sample (50 flows)")

def process_and_render_predictions(df: pd.DataFrame, source_filename: str = "Uploaded CSV"):
    """
    Executes preprocessor and dual-model inference on a DataFrame.
    Optimized with vectorized NumPy/Pandas operations to score 80,000+ rows in ~1-2 seconds.
    Ensures target columns ('attack_cat', 'label') and identifiers ('id') are NEVER passed as features.
    """
    global last_prediction_results
    t_start = time.time()

    preprocessor = pipeline_state["preprocessor"]
    rf_model = pipeline_state["rf_model"]
    ae_model = pipeline_state["ae_model"]
    ae_threshold = float(ae_model.threshold)

    # 1. Isolate and preserve ground truth targets & identifiers WITHOUT passing them as features
    target_cols = [c for c in df.columns if c.strip().lower() in ("label", "target", "class")]
    attack_cat_cols = [c for c in df.columns if c.strip().lower() in ("attack_cat", "attack_category", "category")]
    id_cols = [c for c in df.columns if c.strip().lower() in ("id", "packet_id", "flow_id")]

    has_ground_truth = len(target_cols) > 0
    ground_truth_series = df[target_cols[0]] if has_ground_truth else None
    attack_cat_series = df[attack_cat_cols[0]] if len(attack_cat_cols) > 0 else None

    # Drop target and identifier columns from feature matrix so they NEVER enter the models
    cols_to_drop = list(set(target_cols + attack_cat_cols + id_cols))
    features_df = df.drop(columns=cols_to_drop, errors="ignore")

    # Check for missing expected feature columns and inform user
    missing_cols = [c for c in preprocessor.num_cols + preprocessor.cat_cols if c not in features_df.columns]
    if missing_cols and len(missing_cols) < 25:
        flash(
            f"Notice: {len(missing_cols)} expected feature columns were missing ({', '.join(missing_cols[:4])}...). "
            "Missing values were automatically imputed using training statistics.",
            "info"
        )

    # 2. Vectorized Feature Transformation (strictly using pre-fitted transformers)
    try:
        X_trans = preprocessor.transform(features_df)
    except Exception as e:
        logger.error(f"Feature transformation error: {e}")
        flash(f"Error during feature preprocessing: {str(e)}", "danger")
        return redirect(url_for("predict"))

    # 3. Vectorized Model Inference
    # Random Forest: probability & prediction
    rf_probs = rf_model.predict_proba(X_trans)
    rf_preds = (rf_probs >= 0.5).astype(int)

    # Deep Autoencoder: reconstruction error & thresholding
    ae_scores = ae_model.compute_reconstruction_error(X_trans)
    ae_preds = (ae_scores > ae_threshold).astype(int)

    # 4. Dual-Engine Threat Consensus (Vectorized)
    threat_levels = np.where(
        (rf_preds == 1) & (ae_preds == 1), "CRITICAL INTRUSION",
        np.where((rf_preds == 1) | (ae_preds == 1), "SUSPICIOUS", "NORMAL")
    )

    # 5. Full Batch Summary Statistics
    total_records = len(df)
    rf_attacks = int(np.sum(rf_preds == 1))
    ae_anomalies = int(np.sum(ae_preds == 1))
    critical_count = int(np.sum(threat_levels == "CRITICAL INTRUSION"))
    normal_count = int(np.sum(threat_levels == "NORMAL"))
    attack_rate = (rf_attacks / total_records * 100.0) if total_records > 0 else 0.0

    # Ground truth accuracy / agreement if ground truth label is available
    gt_stats = None
    if has_ground_truth and ground_truth_series is not None:
        try:
            gt_arr = pd.to_numeric(ground_truth_series, errors="coerce").fillna(0).astype(int).values
            correct_rf = int(np.sum(rf_preds == gt_arr))
            gt_acc = (correct_rf / total_records * 100.0) if total_records > 0 else 0.0
            actual_attacks = int(np.sum(gt_arr == 1))
            actual_normal = int(np.sum(gt_arr == 0))
            gt_stats = {
                "accuracy": round(gt_acc, 2),
                "actual_attacks": actual_attacks,
                "actual_normal": actual_normal,
                "matches": correct_rf
            }
        except Exception:
            gt_stats = None

    elapsed_time = round(time.time() - t_start, 2)

    # 6. Build Complete Export DataFrame for CSV Download
    export_df = pd.DataFrame({
        "id": np.arange(1, total_records + 1),
        "proto": df["proto"].astype(str) if "proto" in df.columns else "-",
        "service": df["service"].astype(str) if "service" in df.columns else "-",
        "state": df["state"].astype(str) if "state" in df.columns else "-",
        "dur": pd.to_numeric(df["dur"], errors="coerce").fillna(0.0) if "dur" in df.columns else 0.0,
        "sbytes": pd.to_numeric(df["sbytes"], errors="coerce").fillna(0).astype(int) if "sbytes" in df.columns else 0,
        "rf_prediction": np.where(rf_preds == 1, "Attack", "Normal"),
        "rf_attack_prob": np.round(rf_probs, 4),
        "ae_reconstruction_error": np.round(ae_scores, 4),
        "ae_is_anomaly": np.where(ae_preds == 1, "Anomaly", "Normal"),
        "threat_consensus": threat_levels
    })
    if has_ground_truth and ground_truth_series is not None:
        export_df["ground_truth_label"] = ground_truth_series.values
    if attack_cat_series is not None:
        export_df["attack_category"] = attack_cat_series.values

    # Cache complete DataFrame for download route
    last_prediction_results = export_df

    # 7. Fast Preview Generation for Browser Display (First 200 records to prevent DOM freezing)
    preview_limit = min(200, total_records)
    preview_records = []

    proto_list = export_df["proto"].iloc[:preview_limit].tolist()
    service_list = export_df["service"].iloc[:preview_limit].tolist()
    state_list = export_df["state"].iloc[:preview_limit].tolist()
    dur_list = export_df["dur"].iloc[:preview_limit].tolist()
    sbytes_list = export_df["sbytes"].iloc[:preview_limit].tolist()
    rf_prob_list = export_df["rf_attack_prob"].iloc[:preview_limit].tolist()
    ae_score_list = export_df["ae_reconstruction_error"].iloc[:preview_limit].tolist()
    threat_list = export_df["threat_consensus"].iloc[:preview_limit].tolist()
    gt_list = ground_truth_series.iloc[:preview_limit].tolist() if (has_ground_truth and ground_truth_series is not None) else None
    cat_list = attack_cat_series.iloc[:preview_limit].tolist() if attack_cat_series is not None else None

    for i in range(preview_limit):
        preview_records.append({
            "id": i + 1,
            "proto": proto_list[i],
            "service": service_list[i],
            "state": state_list[i],
            "dur": float(dur_list[i]),
            "sbytes": int(sbytes_list[i]),
            "rf_pred": int(rf_preds[i]),
            "rf_prob": float(rf_prob_list[i]),
            "ae_score": float(ae_score_list[i]),
            "threat_level": threat_list[i],
            "ground_truth": safe_label(gt_list[i]) if gt_list is not None else None,
            "attack_cat": str(cat_list[i]) if cat_list is not None and not pd.isna(cat_list[i]) else None
        })

    summary = {
        "source_filename": source_filename,
        "total": total_records,
        "rf_attacks": rf_attacks,
        "ae_anomalies": ae_anomalies,
        "critical_count": critical_count,
        "normal_count": normal_count,
        "attack_rate": round(attack_rate, 2),
        "elapsed_time": elapsed_time,
        "gt_stats": gt_stats,
        "display_limit": preview_limit,
        "is_truncated": (total_records > preview_limit)
    }

    flash(
        f"Successfully processed {total_records:,} records in {elapsed_time}s! "
        f"Detected {rf_attacks:,} attacks ({round(attack_rate, 1)}%) and {critical_count:,} critical threats.",
        "success"
    )

    return render_template(
        "predict.html",
        active_page="predict",
        results=preview_records,
        summary=summary,
        has_ground_truth=has_ground_truth,
        ae_threshold=ae_threshold
    )

@app.route("/download-predictions")
def download_predictions():
    """Exports prediction results to downloadable CSV."""
    global last_prediction_results
    if last_prediction_results is None or (isinstance(last_prediction_results, list) and not last_prediction_results) or (isinstance(last_prediction_results, pd.DataFrame) and last_prediction_results.empty):
        flash("No prediction results available to download. Please run predictions first.", "warning")
        return redirect(url_for("predict"))

    if isinstance(last_prediction_results, pd.DataFrame):
        out_df = last_prediction_results
    else:
        out_df = pd.DataFrame(last_prediction_results)

    csv_buffer = io.StringIO()
    out_df.to_csv(csv_buffer, index=False)
    csv_bytes = io.BytesIO(csv_buffer.getvalue().encode("utf-8"))

    return send_file(
        csv_bytes,
        mimetype="text/csv",
        as_attachment=True,
        download_name="nids_dual_engine_predictions.csv"
    )

@app.route("/replay")
def replay():
    """Renders the Dataset-Based Stream Replay Simulation interface."""
    if not pipeline_state["is_loaded"]:
        flash("Models are not loaded. Run 'python train.py --mode sample' first.", "danger")
        return redirect(url_for("index"))

    ae_threshold = float(pipeline_state["ae_model"].threshold)
    return render_template(
        "replay.html",
        active_page="replay",
        ae_threshold=ae_threshold
    )

@app.route("/api/replay/next", methods=["POST"])
def api_replay_next():
    """
    API endpoint for dataset stream replay demo.
    Returns the next batch of evaluated records from the holdout test set.
    """
    if not pipeline_state["is_loaded"] or pipeline_state["test_data"] is None:
        return jsonify({"error": "Test dataset or models not loaded"}), 500

    data = request.get_json() or {}
    current_index = int(data.get("current_index", 0))
    batch_size = max(1, min(int(data.get("batch_size", 1)), 50))

    test_df = pipeline_state["test_data"]
    total_records = len(test_df)

    if current_index >= total_records:
        return jsonify({
            "records": [],
            "next_index": current_index,
            "is_end": True
        })

    end_index = min(current_index + batch_size, total_records)
    batch_df = test_df.iloc[current_index:end_index].copy()

    preprocessor = pipeline_state["preprocessor"]
    rf_model = pipeline_state["rf_model"]
    ae_model = pipeline_state["ae_model"]
    ae_threshold = float(ae_model.threshold)

    # Zero-leakage transform
    X_trans = preprocessor.transform(batch_df)
    rf_probs = rf_model.predict_proba(X_trans)
    rf_preds = (rf_probs >= 0.5).astype(int)
    ae_scores = ae_model.compute_reconstruction_error(X_trans)
    ae_preds = (ae_scores > ae_threshold).astype(int)

    records = []
    has_ground_truth = "label" in batch_df.columns

    for idx, (original_idx, row) in enumerate(batch_df.iterrows()):
        rf_p = int(rf_preds[idx])
        ae_p = int(ae_preds[idx])
        
        if rf_p == 1 and ae_p == 1:
            threat = "CRITICAL INTRUSION"
        elif rf_p == 1 or ae_p == 1:
            threat = "SUSPICIOUS"
        else:
            threat = "NORMAL"

        record = {
            "packet_id": current_index + idx + 1,
            "timestamp": time.strftime("%H:%M:%S"),
            "proto": str(row.get("proto", "-")),
            "service": str(row.get("service", "-")),
            "state": str(row.get("state", "-")),
            "sbytes": safe_int(row.get("sbytes", 0)),
            "rf_pred": rf_p,
            "rf_prob": float(round(rf_probs[idx], 4)),
            "ae_score": float(round(ae_scores[idx], 4)),
            "ae_pred": ae_p,
            "threat_level": threat,
            "ground_truth_label": safe_label(row["label"]) if has_ground_truth else None,
            "ground_truth_cat": str(row.get("attack_cat", "Unknown")) if not pd.isna(row.get("attack_cat", None)) else "Unknown"
        }
        records.append(record)

    return jsonify({
        "records": records,
        "next_index": end_index,
        "is_end": (end_index >= total_records)
    })

# Error Handlers
@app.errorhandler(400)
def bad_request(e):
    logger.warning(f"HTTP 400 Bad Request caught: {e}")
    flash(
        "Upload request was interrupted or invalid. If you are uploading a large CSV file, "
        "please ensure the file is selected and wait for the upload to complete without clicking multiple times.",
        "warning"
    )
    return redirect(url_for("predict"))

@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning(f"HTTP 413 Payload Too Large: {e}")
    flash(
        "The uploaded CSV exceeds the maximum allowable file size (64 MB). "
        "Please upload a smaller file or use the built-in 5,000-flow sample test dataset.",
        "danger"
    )
    return redirect(url_for("predict"))

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", active_page="", content="<div class='alert alert-warning'>Page not found (404).</div>"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("base.html", active_page="", content="<div class='alert alert-danger'>Internal server error (500).</div>"), 500

if __name__ == "__main__":
    # Runs the Flask application on port 5000
    print("=" * 70)
    print("  🛡️  Network Intrusion & Anomaly Detection - Flask Dashboard")
    print("  Local URL: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True)
