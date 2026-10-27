"""
Streamlit Web Application: Real-Time Network Intrusion and Anomaly Detection
Uses Machine Learning (Random Forest) and Deep Learning (PyTorch Autoencoder) on UNSW-NB15.
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.config import config
from src.data_loader import load_dataset, inspect_dataset
from src.preprocessor import DataPreprocessor
from src.models.random_forest_model import RandomForestModel
from src.models.autoencoder_model import DeepAutoencoderModel
from src.evaluation import load_evaluation_metrics, CLASS_IMBALANCE_EXPLANATION

# Page configuration
st.set_page_config(
    page_title="Network Intrusion & Anomaly Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern SOC Theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .badge-normal {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-attack {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .disclaimer-banner {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        color: #1E40AF;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions to load models and data with caching
@st.cache_resource(show_spinner="Loading models and preprocessor...")
def load_saved_pipeline():
    """Loads fitted preprocessor, Random Forest, and PyTorch Autoencoder."""
    if not (os.path.exists(config.PREPROCESSOR_PATH) and
            os.path.exists(config.RF_MODEL_PATH) and
            os.path.exists(config.AUTOENCODER_PATH)):
        return None, None, None

    try:
        preprocessor = DataPreprocessor.load(config.PREPROCESSOR_PATH)
        rf_model = RandomForestModel.load(config.RF_MODEL_PATH)
        ae_model = DeepAutoencoderModel.load(config.AUTOENCODER_PATH, config.AE_CONFIG_PATH)
        return preprocessor, rf_model, ae_model
    except Exception as e:
        st.error(f"Error loading pipeline: {e}")
        return None, None, None

@st.cache_data(show_spinner="Loading test dataset...")
def load_test_records():
    """Loads test dataset for exploration and stream replay."""
    path = config.SAMPLE_TEST_PATH if os.path.exists(config.SAMPLE_TEST_PATH) else config.DEFAULT_TEST_PATH
    if os.path.exists(path):
        return pd.read_csv(path, encoding="utf-8-sig")
    return None

@st.cache_data(show_spinner="Loading train dataset...")
def load_train_records():
    path = config.SAMPLE_TRAIN_PATH if os.path.exists(config.SAMPLE_TRAIN_PATH) else config.DEFAULT_TRAIN_PATH
    if os.path.exists(path):
        return pd.read_csv(path, encoding="utf-8-sig")
    return None

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=64)
st.sidebar.title("🛡️ NIDS Control Center")
st.sidebar.markdown("**Dual-Engine Cyber Intrusion Detection**")
st.sidebar.markdown("*Random Forest & Deep Autoencoder*")
st.sidebar.markdown("---")

# Navigation
selected_page = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Dataset & System Analytics",
        "⚖️ Model Performance & Comparison",
        "📂 Batch File Prediction",
        "⚡ Real-Time Stream Replay"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("System Configuration")
st.sidebar.info(f"**Random Seed**: `{config.RANDOM_SEED}`\n\n**Dataset**: `UNSW-NB15`\n\n**Frameworks**: `PyTorch`, `Scikit-Learn`")

# Load Pipeline
preprocessor, rf_model, ae_model = load_saved_pipeline()
metrics_dict = load_evaluation_metrics(config.METRICS_PATH)

if preprocessor is None or rf_model is None or ae_model is None:
    st.warning("⚠️ **Trained models not found!** Please execute `python train.py --mode sample` first to generate model weights and metrics.")
    st.stop()

# ==============================================================================
# TAB 1: DATASET & SYSTEM ANALYTICS
# ==============================================================================
if selected_page == "📊 Dataset & System Analytics":
    st.markdown('<div class="main-header">Real-Time Network Intrusion & Anomaly Detection</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">UNSW-NB15 Dataset Exploration & Feature Characterization</div>', unsafe_allow_html=True)

    train_df = load_train_records()
    test_df = load_test_records()

    if train_df is None or test_df is None:
        st.error("Dataset files missing. Run 'python data/download_data.py'.")
        st.stop()

    # Top KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Training Records", f"{len(train_df):,}", "UNSW-NB15 Sample")
    with col2:
        st.metric("Total Testing Records", f"{len(test_df):,}", "Holdout Benchmark")
    with col3:
        attack_count = int(train_df["label"].sum())
        st.metric("Training Attacks", f"{attack_count:,}", f"{(attack_count/len(train_df)*100):.1f}% of train")
    with col4:
        normal_count = int((train_df["label"] == 0).sum())
        st.metric("Training Normal Traffic", f"{normal_count:,}", f"{(normal_count/len(train_df)*100):.1f}% of train")

    st.markdown("---")

    tab_overview, tab_features, tab_data = st.tabs(["Class & Attack Distribution", "Protocol & Service Profile", "Data Sample Viewer"])

    with tab_overview:
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Binary Class Distribution (Train vs. Test)")
            class_data = pd.DataFrame({
                "Dataset": ["Train Normal", "Train Attack", "Test Normal", "Test Attack"],
                "Count": [
                    (train_df["label"] == 0).sum(),
                    (train_df["label"] == 1).sum(),
                    (test_df["label"] == 0).sum(),
                    (test_df["label"] == 1).sum()
                ],
                "Type": ["Normal", "Attack", "Normal", "Attack"]
            })
            fig_bar = px.bar(
                class_data,
                x="Dataset",
                y="Count",
                color="Type",
                color_discrete_map={"Normal": "#10B981", "Attack": "#EF4444"},
                text_auto=True,
                title="Normal vs. Attack Records Across Benchmark Splits"
            )
            fig_bar.update_layout(showlegend=True, height=380)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            st.subheader("Attack Category Breakdown (Training Set)")
            if "attack_cat" in train_df.columns:
                cat_counts = train_df["attack_cat"].value_counts().reset_index()
                cat_counts.columns = ["Attack Category", "Count"]
                fig_pie = px.pie(
                    cat_counts,
                    names="Attack Category",
                    values="Count",
                    hole=0.45,
                    title="Distribution of Intrusion Categories",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_pie.update_layout(height=380)
                st.plotly_chart(fig_pie, use_container_width=True)

        st.info("""
        💡 **Dataset Insight**: Notice how **Generic** and **Exploits** dominate the attack traffic, while categories like **Worms**, **Backdoors**, and **Shellcode** comprise a tiny fraction. This highlights why overall accuracy alone is inadequate—high accuracy can be achieved while failing on rare, high-consequence attacks.
        """)

    with tab_features:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.subheader("Top Network Protocols")
            top_proto = train_df["proto"].value_counts().head(8).reset_index()
            top_proto.columns = ["Protocol", "Flow Count"]
            fig_proto = px.bar(top_proto, x="Protocol", y="Flow Count", color="Flow Count", color_continuous_scale="Viridis")
            fig_proto.update_layout(height=360)
            st.plotly_chart(fig_proto, use_container_width=True)

        with col_p2:
            st.subheader("Top Network Services")
            top_srv = train_df["service"].replace("-", "none/direct").value_counts().head(8).reset_index()
            top_srv.columns = ["Service", "Flow Count"]
            fig_srv = px.bar(top_srv, x="Service", y="Flow Count", color="Flow Count", color_continuous_scale="Plasma")
            fig_srv.update_layout(height=360)
            st.plotly_chart(fig_srv, use_container_width=True)

    with tab_data:
        st.subheader("Raw UNSW-NB15 Records Preview")
        st.dataframe(train_df.head(50), use_container_width=True)

# ==============================================================================
# TAB 2: MODEL PERFORMANCE & COMPARISON
# ==============================================================================
elif selected_page == "⚖️ Model Performance & Comparison":
    st.markdown('<div class="main-header">Comparative Model Performance & Class Imbalance Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating Supervised Random Forest vs. Semi-Supervised Deep Autoencoder</div>', unsafe_allow_html=True)

    rf_m = metrics_dict.get("random_forest", {})
    ae_m = metrics_dict.get("autoencoder", {})

    # Top KPI Metrics Side-by-Side
    col_rf1, col_rf2, col_ae1, col_ae2 = st.columns(4)
    with col_rf1:
        st.metric("RF Precision", f"{rf_m.get('precision', 0):.4f}", "Supervised")
    with col_rf2:
        st.metric("RF Recall", f"{rf_m.get('recall', 0):.4f}", f"F1: {rf_m.get('f1_score', 0):.4f}")
    with col_ae1:
        st.metric("Autoencoder Specificity", f"{ae_m.get('specificity', 0):.4f}", "Normal traffic retention")
    with col_ae2:
        st.metric("Autoencoder Precision", f"{ae_m.get('precision', 0):.4f}", f"Threshold: {metrics_dict.get('metadata', {}).get('ae_threshold', 0):.4f}")

    st.markdown("---")

    # Side-by-side Table
    st.subheader("Detailed Model Comparison Matrix")
    metrics_table = pd.DataFrame({
        "Evaluation Dimension": [
            "Learning Paradigm",
            "Detection Objective",
            "Precision (Alert Reliability)",
            "Recall (Attack Detection Rate)",
            "F1-Score (Harmonic Mean)",
            "Specificity (Benign Flow Accuracy)",
            "False Positive Rate (FPR)",
            "ROC-AUC Score",
            "PR-AUC (Average Precision)"
        ],
        "Random Forest": [
            "Supervised (Labels 0 & 1)",
            "Identifies Known Attack Patterns",
            f"{rf_m.get('precision', 0):.4f}",
            f"{rf_m.get('recall', 0):.4f}",
            f"{rf_m.get('f1_score', 0):.4f}",
            f"{rf_m.get('specificity', 0):.4f}",
            f"{rf_m.get('false_positive_rate', 0):.4f}",
            f"{rf_m.get('roc_auc', 'N/A')}",
            f"{rf_m.get('pr_auc', 'N/A')}"
        ],
        "Deep Autoencoder": [
            "Semi-Supervised (Trained ONLY on Normal)",
            "Detects Statistical Anomalies & Novel Attacks",
            f"{ae_m.get('precision', 0):.4f}",
            f"{ae_m.get('recall', 0):.4f}",
            f"{ae_m.get('f1_score', 0):.4f}",
            f"{ae_m.get('specificity', 0):.4f}",
            f"{ae_m.get('false_positive_rate', 0):.4f}",
            f"{ae_m.get('roc_auc', 'N/A')}",
            f"{ae_m.get('pr_auc', 'N/A')}"
        ]
    })
    st.table(metrics_table)

    col_cm1, col_cm2 = st.columns(2)
    with col_cm1:
        st.subheader("Random Forest Confusion Matrix")
        rf_mat = rf_m.get("confusion_matrix", {}).get("matrix", [[0, 0], [0, 0]])
        fig_rf_cm = px.imshow(
            rf_mat,
            labels=dict(x="Predicted Class", y="Actual Class", color="Count"),
            x=["Normal (0)", "Attack (1)"],
            y=["Normal (0)", "Attack (1)"],
            text_auto=True,
            color_continuous_scale="Blues"
        )
        fig_rf_cm.update_layout(height=340)
        st.plotly_chart(fig_rf_cm, use_container_width=True)

    with col_cm2:
        st.subheader("Deep Autoencoder Confusion Matrix")
        ae_mat = ae_m.get("confusion_matrix", {}).get("matrix", [[0, 0], [0, 0]])
        fig_ae_cm = px.imshow(
            ae_mat,
            labels=dict(x="Predicted Class", y="Actual Class", color="Count"),
            x=["Normal (0)", "Attack (1)"],
            y=["Normal (0)", "Attack (1)"],
            text_auto=True,
            color_continuous_scale="Oranges"
        )
        fig_ae_cm.update_layout(height=340)
        st.plotly_chart(fig_ae_cm, use_container_width=True)

    # ROC Curves Comparison
    col_roc, col_feat = st.columns(2)
    with col_roc:
        st.subheader("ROC Curves Comparison")
        fig_roc = go.Figure()
        if "roc_curve" in rf_m:
            fig_roc.add_trace(go.Scatter(
                x=rf_m["roc_curve"]["fpr"],
                y=rf_m["roc_curve"]["tpr"],
                mode="lines",
                name=f"Random Forest (AUC = {rf_m.get('roc_auc', 0):.3f})",
                line=dict(color="#2563EB", width=2)
            ))
        if "roc_curve" in ae_m:
            fig_roc.add_trace(go.Scatter(
                x=ae_m["roc_curve"]["fpr"],
                y=ae_m["roc_curve"]["tpr"],
                mode="lines",
                name=f"Deep Autoencoder (AUC = {ae_m.get('roc_auc', 0):.3f})",
                line=dict(color="#EA580C", width=2)
            ))
        fig_roc.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1],
            mode="lines",
            name="Random Guess",
            line=dict(color="grey", dash="dash")
        ))
        fig_roc.update_layout(
            xaxis_title="False Positive Rate (1 - Specificity)",
            yaxis_title="True Positive Rate (Recall)",
            height=380,
            legend=dict(x=0.4, y=0.1)
        )
        st.plotly_chart(fig_roc, use_container_width=True)

    with col_feat:
        st.subheader("Top Predictive Features (Random Forest)")
        top_features = metrics_dict.get("rf_top_features", [])
        if top_features:
            feat_df = pd.DataFrame(top_features, columns=["Feature", "Importance"]).sort_values("Importance", ascending=True)
            fig_feat = px.bar(
                feat_df,
                x="Importance",
                y="Feature",
                orientation="h",
                color="Importance",
                color_continuous_scale="Teal"
            )
            fig_feat.update_layout(height=380)
            st.plotly_chart(fig_feat, use_container_width=True)

    # Academic explanation of class imbalance
    st.markdown("---")
    st.subheader("🎓 In-Depth Analysis: Why Accuracy Alone is Misleading")
    st.markdown(CLASS_IMBALANCE_EXPLANATION)

# ==============================================================================
# TAB 3: BATCH CSV PREDICTION
# ==============================================================================
elif selected_page == "📂 Batch File Prediction":
    st.markdown('<div class="main-header">Batch File Prediction & Anomaly Scoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload a Network Flow CSV for Dual-Engine Classification</div>', unsafe_allow_html=True)

    col_upload, col_sample = st.columns([3, 1])
    with col_upload:
        uploaded_file = st.file_uploader("Upload Network Traffic CSV", type=["csv"])
    with col_sample:
        st.markdown("<br>", unsafe_allow_html=True)
        use_sample = st.button("🧪 Load Sample Test Batch", use_container_width=True)

    data_to_predict = None

    if uploaded_file is not None:
        try:
            data_to_predict = pd.read_csv(uploaded_file, encoding="utf-8-sig")
            st.success(f"Successfully loaded {len(data_to_predict):,} records from uploaded CSV.")
        except Exception as e:
            st.error(f"Error reading uploaded CSV: {e}")
    elif use_sample:
        test_df = load_test_records()
        if test_df is not None:
            data_to_predict = test_df.sample(min(200, len(test_df)), random_state=42).reset_index(drop=True)
            st.info(f"Loaded {len(data_to_predict)} records from the UNSW-NB15 holdout test set.")

    if data_to_predict is not None:
        with st.spinner("Executing Dual-Engine Predictions..."):
            # Transform features using fitted preprocessor
            X_trans = preprocessor.transform(data_to_predict)

            # Random Forest predictions
            rf_probs = rf_model.predict_proba(X_trans)
            rf_preds = (rf_probs >= 0.5).astype(int)

            # Autoencoder predictions
            ae_scores = ae_model.compute_reconstruction_error(X_trans)
            ae_preds = (ae_scores > ae_model.threshold).astype(int)

            # Build result DataFrame
            results_df = data_to_predict.copy()
            results_df["RF_Attack_Probability"] = np.round(rf_probs, 4)
            results_df["RF_Prediction"] = np.where(rf_preds == 1, "Attack", "Normal")
            results_df["AE_Reconstruction_Error"] = np.round(ae_scores, 4)
            results_df["AE_Anomaly_Alert"] = np.where(ae_preds == 1, "Anomaly Flagged", "Normal Pattern")

            # Composite Threat Level
            conditions = [
                (rf_preds == 1) & (ae_preds == 1),
                (rf_preds == 1) | (ae_preds == 1)
            ]
            choices = ["CRITICAL INTRUSION 🔴", "SUSPICIOUS / ELEVATED 🟡"]
            results_df["Threat_Level"] = np.select(conditions, choices, default="NORMAL 🟢")

        # Metrics for the batch
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Batch Records", f"{len(results_df):,}")
        with c2:
            rf_att = int((rf_preds == 1).sum())
            st.metric("RF Attacks Flagged", f"{rf_att:,}", f"{(rf_att/len(results_df)*100):.1f}%")
        with c3:
            ae_anom = int((ae_preds == 1).sum())
            st.metric("Autoencoder Anomalies", f"{ae_anom:,}", f"{(ae_anom/len(results_df)*100):.1f}%")
        with c4:
            crit = int(((rf_preds == 1) & (ae_preds == 1)).sum())
            st.metric("Critical Consensus Alerts", f"{crit:,}", "Both Engines Agreed")

        # Filtering
        st.subheader("Predicted Records Table")
        threat_filter = st.multiselect(
            "Filter by Threat Level",
            options=["ALL", "CRITICAL INTRUSION 🔴", "SUSPICIOUS / ELEVATED 🟡", "NORMAL 🟢"],
            default=["ALL"]
        )

        filtered_df = results_df
        if "ALL" not in threat_filter and len(threat_filter) > 0:
            filtered_df = results_df[results_df["Threat_Level"].isin(threat_filter)]

        # Display key columns
        display_cols = [
            "Threat_Level", "RF_Prediction", "RF_Attack_Probability",
            "AE_Anomaly_Alert", "AE_Reconstruction_Error",
            "proto", "service", "state", "dur", "sbytes", "dbytes"
        ]
        if "attack_cat" in filtered_df.columns:
            display_cols.append("attack_cat")

        present_cols = [c for c in display_cols if c in filtered_df.columns]
        st.dataframe(filtered_df[present_cols], use_container_width=True)

        # Download button
        csv_data = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Full Predictions CSV",
            data=csv_data,
            file_name="nids_dual_engine_predictions.csv",
            mime="text/csv"
        )
    else:
        st.info("👆 Upload a CSV file or click 'Load Sample Test Batch' to generate predictions.")

# ==============================================================================
# TAB 4: REAL-TIME STREAM REPLAY SIMULATION
# ==============================================================================
elif selected_page == "⚡ Real-Time Stream Replay":
    st.markdown('<div class="main-header">Real-Time Stream Replay Simulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Replaying UNSW-NB15 Test Flows to Demonstrate Line-Rate Anomaly Detection</div>', unsafe_allow_html=True)

    # Required Student Disclaimer
    st.markdown("""
    <div class="disclaimer-banner">
        ℹ️ <strong>System Architecture Note</strong>: This demonstration is a <strong>dataset-based stream replay simulation</strong>. 
        It streams holdout test records sequentially from the benchmark dataset at configurable millisecond intervals, feeding them 
        into our zero-leakage preprocessing pipeline and dual-model inference engines. It does not perform live physical packet sniffing.
    </div>
    """, unsafe_allow_html=True)

    test_df = load_test_records()
    if test_df is None:
        st.error("Holdout test records not available.")
        st.stop()

    # Replay Controls
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    with col_ctrl1:
        playback_delay = st.slider(
            "⏱️ Stream Latency / Interval per Record (seconds)",
            min_value=0.01,
            max_value=0.50,
            value=0.08,
            step=0.01,
            help="Simulates incoming network flow ingestion frequency."
        )
    with col_ctrl2:
        num_stream_packets = st.slider(
            "📦 Batch Stream Size",
            min_value=20,
            max_value=300,
            value=60,
            step=10
        )
    with col_ctrl3:
        st.markdown("<br>", unsafe_allow_html=True)
        start_replay = st.button("▶️ Start Stream Replay", use_container_width=True, type="primary")

    if start_replay:
        # Sample packets to stream
        stream_subset = test_df.sample(num_stream_packets, random_state=int(time.time()) % 1000).reset_index(drop=True)

        # Placeholders for live updates
        kpi_placeholder = st.empty()
        chart_placeholder = st.empty()
        feed_placeholder = st.empty()

        # Streaming state variables
        history = []
        ae_threshold = float(ae_model.threshold)

        for i in range(len(stream_subset)):
            row = stream_subset.iloc[[i]].copy()
            
            # Extract ground truth if present
            gt_label = int(row["label"].values[0]) if "label" in row.columns else None
            gt_cat = str(row["attack_cat"].values[0]) if "attack_cat" in row.columns else "Unknown"

            # Transform row
            X_row = preprocessor.transform(row)

            # Inference
            rf_prob = float(rf_model.predict_proba(X_row)[0])
            rf_pred = int(rf_prob >= 0.5)

            ae_err = float(ae_model.compute_reconstruction_error(X_row)[0])
            ae_pred = int(ae_err > ae_threshold)

            # Alert status
            if rf_pred == 1 and ae_pred == 1:
                status_icon = "🔴"
                threat = "CRITICAL INTRUSION"
            elif rf_pred == 1 or ae_pred == 1:
                status_icon = "🟡"
                threat = "SUSPICIOUS"
            else:
                status_icon = "🟢"
                threat = "NORMAL"

            record_info = {
                "Flow #": i + 1,
                "Time": time.strftime("%H:%M:%S"),
                "Proto": str(row.get("proto", pd.Series(["-"])).values[0]),
                "Service": str(row.get("service", pd.Series(["-"])).values[0]),
                "Bytes": int(row.get("sbytes", pd.Series([0])).values[0]),
                "RF Attack Prob": round(rf_prob, 3),
                "AE Recon MSE": round(ae_err, 4),
                "Threat Level": f"{status_icon} {threat}",
                "Ground Truth": f"{'Attack' if gt_label == 1 else 'Normal'} ({gt_cat})" if gt_label is not None else "N/A"
            }
            history.append(record_info)

            # Update Live KPIs
            with kpi_placeholder.container():
                c1, c2, c3, c4 = st.columns(4)
                attacks_detected = sum(1 for r in history if "CRITICAL" in r["Threat_Level"] or "SUSPICIOUS" in r["Threat_Level"])
                c1.metric("Packets Processed", f"{i + 1} / {num_stream_packets}")
                c2.metric("Intrusions Flagged", f"{attacks_detected}", f"{(attacks_detected/(i+1)*100):.1f}% Rate")
                c3.metric("Current Autoencoder MSE", f"{ae_err:.4f}", f"Threshold: {ae_threshold:.4f}")
                c4.metric("Last Flow Threat", f"{status_icon} {threat}")

            # Update Chart every 3 packets for smooth UI
            if (i + 1) % 3 == 0 or (i + 1) == len(stream_subset):
                with chart_placeholder.container():
                    chart_df = pd.DataFrame(history)
                    fig_timeline = go.Figure()
                    fig_timeline.add_trace(go.Scatter(
                        x=chart_df["Flow #"],
                        y=chart_df["AE Recon MSE"],
                        mode="lines+markers",
                        name="Flow Reconstruction Error (MSE)",
                        line=dict(color="#2563EB", width=2),
                        marker=dict(size=5)
                    ))
                    fig_timeline.add_hline(
                        y=ae_threshold,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Anomaly Cutoff Threshold ({ae_threshold:.4f})",
                        annotation_position="top left"
                    )
                    fig_timeline.update_layout(
                        title="Real-Time Network Flow Anomaly Score Timeline",
                        xaxis_title="Packet Sequence",
                        yaxis_title="Reconstruction MSE",
                        height=280,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)

            # Update Feed Table (latest 10 records)
            with feed_placeholder.container():
                st.subheader("Live Packet Stream Feed (Latest 10 Packets)")
                feed_df = pd.DataFrame(history).tail(10)
                st.dataframe(feed_df, use_container_width=True)

            time.sleep(playback_delay)

        st.success(f"✅ Stream replay simulation complete! Evaluated {num_stream_packets} incoming network flows.")
    else:
        st.info("Click **'▶️ Start Stream Replay'** to initiate live network traffic simulation.")
