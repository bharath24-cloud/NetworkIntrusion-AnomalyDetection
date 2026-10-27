# Real-Time Network Intrusion and Anomaly Detection Using Machine Learning and Deep Learning

An end-to-end cybersecurity student project that detects network intrusions and anomalous traffic flows using the **UNSW-NB15** benchmark dataset. The system compares a supervised **Random Forest Classifier** against a semi-supervised **Deep Autoencoder** (trained strictly on benign network traffic) and provides an interactive **Flask Security Operations Center (SOC) Dashboard** featuring dataset-based stream replay simulation.

---

## 📌 Table of Contents
1. [Project Overview](#project-overview)
2. [Dataset: UNSW-NB15](#dataset-unsw-nb15)
3. [Methodology & Architecture](#methodology--architecture)
   - [Strict Data Leakage Prevention](#strict-data-leakage-prevention)
   - [Model 1: Supervised Random Forest Classifier](#model-1-supervised-random-forest-classifier)
   - [Model 2: Deep Learning Autoencoder](#model-2-deep-learning-autoencoder)
4. [Class Imbalance & Evaluation Metrics](#class-imbalance--evaluation-metrics)
5. [Project Directory Structure](#project-directory-structure)
6. [Setup and Installation](#setup-and-installation)
7. [Running the Project](#running-the-project)
   - [1. Dataset Preparation](#1-dataset-preparation)
   - [2. Model Training & Comparison](#2-model-training--comparison)
   - [3. Launching the Streamlit Dashboard](#3-launching-the-streamlit-dashboard)
8. [Streamlit Dashboard Capabilities](#streamlit-dashboard-capabilities)
9. [Experimental Results Summary](#experimental-results-summary)
10. [Academic References](#academic-references)

---

## 📖 Project Overview

Modern enterprise networks face diverse cyber threats—from high-volume denial-of-service (DoS) assaults to stealthy zero-day exploits, reconnaissance scans, and advanced persistent threats (APTs). 

Traditional signature-based Network Intrusion Detection Systems (NIDS) fail against zero-day and morphing attacks. This project implements a **dual-engine detection paradigm**:
1. **Supervised Classification (Random Forest)**: Models known intrusion signatures and behavioral patterns with high precision and recall.
2. **Semi-Supervised Deep Anomaly Detection (PyTorch Autoencoder)**: Trained **exclusively on normal network traffic** to learn the latent representation of benign communication flows. Records that deviate significantly from benign patterns produce high reconstruction error (MSE) and are flagged as anomalous without requiring prior exposure to the attack signature.

---

## 📊 Dataset: UNSW-NB15

The **UNSW-NB15** dataset was created by the Cyber Range Lab of UNSW Canberra using the IXIA PerfectStorm tool to generate realistic normal background traffic and synthetic modern attack behaviors.

- **Total Attributes**: 45 columns (including flow duration, source/destination packet counts, byte volumes, TTL values, TCP window sizes, jitter, and transaction depths).
- **Categorical Features**: `proto` (protocol, e.g., TCP, UDP, ARP, OSPF), `service` (e.g., HTTP, DNS, FTP, SMTP), and `state` (connection state, e.g., FIN, INT, CON, REQ).
- **Binary Target**: `label` (0 = Normal, 1 = Attack).
- **Multi-Class Metadata**: `attack_cat` (Normal, Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoor, Shellcode, Worms).
- **Split Configuration**: Uses the benchmark's pre-divided train and test splits (`UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv`).
- **Student Laptop Sample**: A stratified sample (`sample_training-set.csv` [15,000 records] and `sample_testing-set.csv` [5,000 records]) is automatically generated for quick training and testing on low-resource machines.

---

## 🔬 Methodology & Architecture

### Strict Data Leakage Prevention
In academic and production machine learning, data leakage occurs when information from outside the training dataset is used to train the model. This project strictly prevents leakage:
- **Separation of Concerns**: Non-predictive identifiers (`id`) and target proxy labels (`attack_cat`) are stripped from the feature matrix before model ingestion.
- **Fit on Train Only**: The `DataPreprocessor` fits all imputers (median for numerical), scalers (`StandardScaler`), and categorical encoders (`OneHotEncoder`) **strictly on the training partition**.
- **Transform-Only for Testing & Streaming**: Test records and real-time streaming batches are transformed using frozen training statistics.
- **Unseen Category Handling**: `OneHotEncoder(handle_unknown='ignore')` maps previously unseen protocols or states in the stream to zero vectors without throwing exceptions or leaking future categories.
- **Fixed Random Seed**: `RANDOM_SEED = 42` is fixed across NumPy, PyTorch, and Scikit-Learn for complete reproducibility.

### Model 1: Supervised Random Forest Classifier
- **Algorithm**: Ensemble of 100 decorrelated decision trees with balanced class weighting (`class_weight='balanced'`).
- **Mechanism**: Splits on information gain across feature subsets, generating predicted probabilities:
  $$\hat{y}_{RF} = \mathbb{I}(P(\text{Attack} \mid x) \ge 0.5)$$
- **Output**: Binary classification, confidence score, and feature importance rankings.

### Model 2: Deep Learning Autoencoder
- **Framework**: PyTorch.
- **Architecture**:
  - **Encoder**: $D \to 64 \to 32 \to 16$ (bottleneck latent representation) with LeakyReLU activations and Batch Normalization.
  - **Decoder**: $16 \to 32 \to 64 \to D$ (reconstruction of input features).
- **Training Strategy**: **Trained ONLY on normal traffic ($y = 0$)**. The network optimizes Mean Squared Error (MSE) to reconstruct benign flows:
  $$\mathcal{L}_{MSE} = \frac{1}{D} \sum_{j=1}^D (x_j - \hat{x}_j)^2$$
- **Threshold Calibration**: The anomaly threshold $\tau$ is calibrated as the $95^{\text{th}}$ percentile of reconstruction errors on benign training flows.
- **Inference**: For any incoming connection $x$, if $\text{MSE}(x, \hat{x}) > \tau$, an intrusion alert is raised.

---

## ⚖️ Class Imbalance & Evaluation Metrics

### Why Accuracy Alone is Misleading
In real-world operational networks, 95% to 99% of flows are legitimate. A naive model predicting "Normal" 100% of the time achieves **99% accuracy**, yet allows **100% of cyber attacks to compromise the network**.

Furthermore, within attack traffic, high-volume automated attacks (Generic, Exploits) drown out rare, high-severity attacks (Worms: 0.1%, Backdoors: 0.5%). Evaluating models on accuracy conceals total blind spots for rare threats.

### Metrics Computed
- **Precision (Positive Predictive Value)**: $\frac{TP}{TP + FP}$ — Measures alert reliability. High precision prevents *SOC Alert Fatigue*.
- **Recall (Detection Rate / Sensitivity)**: $\frac{TP}{TP + FN}$ — Measures attack detection coverage. High recall prevents missed breaches.
- **F1-Score**: $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$ — Harmonic mean balancing false alarms and missed attacks.
- **Specificity (True Negative Rate)**: $\frac{TN}{TN + FP}$ — Accuracy on legitimate normal flows.
- **False Positive Rate (FPR)**: $\frac{FP}{FP + TN}$ — Fraction of legitimate flows wrongly flagged.
- **ROC-AUC & PR-AUC**: Area under the Receiver Operating Characteristic and Precision-Recall curves. PR-AUC is especially robust for minority classes.

---

## 📁 Project Directory Structure

```text
NI&AD/
├── data/
│   ├── download_data.py               # Automated dataset downloader & sampler
│   ├── UNSW_NB15_training-set.csv     # Full benchmark training dataset (~32 MB)
│   ├── UNSW_NB15_testing-set.csv      # Full benchmark testing dataset (~15 MB)
│   ├── sample_training-set.csv        # Stratified laptop sample (15,000 rows)
│   └── sample_testing-set.csv         # Stratified laptop sample (5,000 rows)
├── models/
│   └── saved/                         # Serialized weights and preprocessor
│       ├── preprocessor.joblib        # Fitted scaler & encoder pipeline
│       ├── random_forest_model.joblib # Trained Random Forest artifact
│       ├── autoencoder_model.pt       # PyTorch Autoencoder state dictionary
│       ├── autoencoder_config.json    # Autoencoder architecture & threshold metadata
│       └── evaluation_metrics.json    # Complete JSON performance metrics
├── src/
│   ├── __init__.py
│   ├── config.py                      # Global settings, paths, seeds, hyperparameters
│   ├── data_loader.py                 # File loader, NaN/Inf cleaner, dataset inspector
│   ├── preprocessor.py                # Zero-leakage DataPreprocessor class
│   ├── models/
│   │   ├── __init__.py
│   │   ├── random_forest_model.py     # Supervised Random Forest implementation
│   │   └── autoencoder_model.py       # PyTorch Deep Autoencoder implementation
│   ├── evaluation.py                  # Confusion matrices, ROC/PR curves, imbalance metrics
│   └── stream_simulator.py            # Stream replay generator with configurable delays
├── train.py                           # Command-line training & evaluation orchestrator
├── app.py                             # Interactive Streamlit SOC Web Application
├── requirements.txt                   # Pinned Python package dependencies
└── README.md                          # Comprehensive project documentation
```

---

## 🛠️ Setup and Installation

### 1. Prerequisites
- Python 3.9, 3.10, or 3.11 installed.
- Git (optional, for cloning).

### 2. Virtual Environment (Recommended)
```bash
# Navigate to the project root directory
cd NI&AD

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Project

### 1. Dataset Preparation
Download the benchmark datasets and create the stratified laptop sample:
```bash
python data/download_data.py
```
*(If the files are already in `data/`, this script validates their integrity and generates the samples.)*

### 2. Model Training & Comparison
#### Option A: Quick Student Laptop Mode (Default, ~15 seconds)
```bash
python train.py --mode sample --ae-epochs 10
```

#### Option B: Full Benchmark Training (Resource-Intensive)
When running on a machine with greater RAM and compute resources:
```bash
python train.py --mode full --ae-epochs 20
```

#### Option C: Custom Dataset Files
```bash
python train.py --train-path data/my_train.csv --test-path data/my_test.csv
```

### 3. Launching the Flask SOC Dashboard
Launch the web app:
```bash
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 💻 Flask Dashboard Capabilities

The dashboard provides three dedicated views:

1. **📊 Model Metrics & Comparative Evaluation (`/`)**:
   - High-level KPI cards (Accuracy, Precision, Recall, F1, Autoencoder Specificity, False Alarm Rate).
   - Side-by-side comparison table (Random Forest vs. Deep Autoencoder).
   - Interactive 2x2 confusion matrices with color-coded True Negatives, False Positives, False Negatives, and True Positives.
   - Top 10 most important features identified by Random Forest.
   - In-depth academic discussion on the Class Imbalance Paradox.

2. **📂 Batch CSV Prediction (`/predict`)**:
   - Drag-and-drop CSV uploader for scoring network flow captures.
   - "Load 50 Test Flows Demo" button for instant demonstration.
   - Dual-engine scoring with Random Forest attack probability progress bars, Autoencoder reconstruction error, and multi-level Threat Alert tagging (`NORMAL 🟢`, `SUSPICIOUS 🟡`, `CRITICAL INTRUSION 🔴`).
   - Filter buttons (All, Attacks Only, Normal Only) and one-click CSV export.

3. **⚡ Dataset Replay Demo (`/replay`)**:
   - **System Architecture Note**: Replays recorded UNSW-NB15 holdout test flows sequentially at configurable playback speeds (100ms to 2000ms delay) to demonstrate line-rate stream inspection without live packet capture.
   - Real-time rolling counters: Flows Processed, Normal Traffic, Intrusion Alerts, Critical Threats, Attack Detection Rate (%).
   - Dynamic timeline tracking per-flow Autoencoder reconstruction error against the calibrated cutoff threshold line.
   - Live stream table displaying the latest incoming packet flows with color-coded threat badges.
   - One-click CSV export of predictions and anomaly scores.

4. **⚡ Real-Time Stream Replay**:
   - **System Architecture Note**: Replays recorded UNSW-NB15 test flows at configurable playback speeds (0.01s to 0.50s per record) to demonstrate line-rate stream inspection without live packet capture.
   - Real-time rolling packet counter and threat detection rate.
   - Dynamic timeline tracking per-flow Autoencoder reconstruction error against the calibrated cutoff threshold.
   - Live stream table displaying the most recent incoming packet flows with color-coded threat badges.

---

## 📈 Experimental Results Summary

Evaluated on the UNSW-NB15 holdout test partition:

| Metric | Random Forest (Supervised) | Deep Autoencoder (Semi-Supervised) |
| :--- | :---: | :---: |
| **Paradigm** | Supervised (Normal vs. Attack) | Anomaly Detection (Trained on Normal Only) |
| **Precision** | **0.8600** | **0.8350** |
| **Recall (Detection Rate)** | **0.9775** | 0.2445 |
| **F1-Score** | **0.9150** | 0.3782 |
| **Specificity (Benign Flow Accuracy)** | 0.8051 | **0.9408** |
| **False Positive Rate (FPR)** | 0.1949 | **0.0592** |
| **ROC-AUC Score** | **0.9816** | **0.7810** |
| **PR-AUC (Average Precision)** | **0.9860** | **0.7491** |

### Key Academic Findings
1. **Supervised Superiority on Known Classes**: The Random Forest achieves exceptional detection performance ($F_1 = 0.9150$, $\text{ROC-AUC} = 0.9816$) when test traffic matches the distribution of known attack signatures.
2. **Autoencoder Role in Zero-Day Detection**: Because the Autoencoder was trained **strictly on normal traffic**, it does not memorize attack signatures. Instead, it achieves a very low False Positive Rate ($5.92\%$) and high specificity ($94.08\%$), functioning as an effective first-line filter for uncataloged zero-day anomalies.
3. **Defense-in-Depth Consensus**: Combining both models creates a robust defense: flows flagged by both engines represent high-confidence **Critical Intrusions**, flows flagged by one engine represent **Suspicious Anomalies** requiring analyst review, and flows cleared by both represent legitimate normal traffic.

---

## 📚 Academic References
1. Moustafa, Nour, and Jill Slay. *"UNSW-NB15: a comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set)."* 2015 Military Communications and Information Systems Conference (MilCIS). IEEE, 2015.
2. Moustafa, Nour, and Jill Slay. *"The evaluation of Network Anomaly Detection Systems: Statistical analysis of the UNSW-NB15 data set and the comparison with the KDD99 data set."* Information Security Journal: A Global Perspective 25.1-3 (2016): 18-31.
3. Sommer, Robin, and Vern Paxson. *"Outside the closed world: On using machine learning for network intrusion detection."* 2010 IEEE Symposium on Security and Privacy. IEEE, 2010.
#   N e t w o r k I n t r u s i o n - A n o m a l y D e t e c t i o n  
 