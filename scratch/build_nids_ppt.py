# -*- coding: utf-8 -*-
import os
import shutil
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def update_text_frame(tf, paragraphs_data, default_font_size=18, default_font_name=None, align=None, space_after=6):
    """
    Updates a text frame with clean paragraphs and runs while preserving layout.
    paragraphs_data: list of items. An item can be:
      - str: plain paragraph
      - tuple (bold_prefix, normal_body)
      - dict: {'text': str, 'bold': bool, 'size': int, 'align': PP_ALIGN, 'space_after': int}
    """
    p0 = tf.paragraphs[0]
    p0.text = ""
    
    # Remove extra paragraphs
    p_elements = list(tf._txBody.p_lst)
    for p_elem in p_elements[1:]:
        tf._txBody.remove(p_elem)
        
    for idx, item in enumerate(paragraphs_data):
        if idx == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
            
        if align is not None:
            p.alignment = align
            
        if isinstance(item, tuple):
            bold_prefix, normal_body = item
            r1 = p.add_run()
            r1.text = bold_prefix
            r1.font.bold = True
            if default_font_name:
                r1.font.name = default_font_name
            if default_font_size:
                r1.font.size = Pt(default_font_size)
                
            r2 = p.add_run()
            r2.text = normal_body
            r2.font.bold = False
            if default_font_name:
                r2.font.name = default_font_name
            if default_font_size:
                r2.font.size = Pt(default_font_size)
                
            p.space_after = Pt(space_after)
        elif isinstance(item, dict):
            r = p.add_run()
            r.text = item.get('text', '')
            r.font.bold = item.get('bold', False)
            if default_font_name:
                r.font.name = default_font_name
            size = item.get('size', default_font_size)
            if size:
                r.font.size = Pt(size)
            if 'align' in item:
                p.alignment = item['align']
            p.space_after = Pt(item.get('space_after', space_after))
        else:
            r = p.add_run()
            r.text = str(item)
            if default_font_name:
                r.font.name = default_font_name
            if default_font_size:
                r.font.size = Pt(default_font_size)
            p.space_after = Pt(space_after)

def build_presentation():
    src_path = 'doc/NEXUS_Project_PPT_backup.pptx'
    if not os.path.exists(src_path):
        src_path = 'doc/NEXUS_Project_PPT.pptx'

    prs = pptx.Presentation(src_path)

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides[0]
    for shape in s1.shapes:
        if shape.name == 'Title 1':
            update_text_frame(shape.text_frame, [
                {'text': "DATA MINING LABORATORY - ADA23CL302", 'bold': True, 'size': 26, 'align': PP_ALIGN.CENTER, 'space_after': 4},
                {'text': "Final Assessment Project", 'bold': False, 'size': 20, 'align': PP_ALIGN.CENTER, 'space_after': 0}
            ])
        elif shape.name == 'Value Project Type / Domain:':
            update_text_frame(shape.text_frame, [
                "Internal / Cybersecurity & Machine Learning"
            ], default_font_size=20)
        elif shape.name == 'Value Project Title:':
            update_text_frame(shape.text_frame, [
                "Real-Time Network Intrusion and Anomaly Detection Using Machine Learning and Deep Learning"
            ], default_font_size=21)
        elif shape.name == 'Value Presented By:':
            update_text_frame(shape.text_frame, [
                "Bharathram K (Reg. No: E0324006)"
            ], default_font_size=20)
        elif shape.name == 'Value Guided by:':
            update_text_frame(shape.text_frame, [
                "Prof. P. Deepika, Assistant Professor"
            ], default_font_size=20)

    # =========================================================================
    # SLIDE 2: Contents
    # =========================================================================
    s2 = prs.slides[1]
    for shape in s2.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                "1. Introduction (Threat Landscape & NIDS)",
                "2. Problem Statement (Imbalance & Zero-Days)",
                "3. Literature Survey (Benchmark Research)",
                "4. Objectives (Dual-Engine Framework)",
                "5. Workflow Diagram (Pipeline Architecture)",
                "6. Methodology (KDD & Preprocessing)",
                "7. Tools and Techniques (ML, DL & Flask Stack)"
            ], default_font_size=18, space_after=10)
        elif shape.name == 'Content Placeholder 3':
            update_text_frame(shape.text_frame, [
                "8. Implementation (Architecture & Setup)",
                "9. Environment Setup (Hardware & Execution)",
                "10. Evaluation Metrics (Validation Metrics)",
                "11. Result Analysis (Empirical Metrics)",
                "12. Conclusion (Key Findings & Impact)",
                "13. Future Scope (Live NIC Sniffing)",
                "14. References (Academic & IEEE Citations)"
            ], default_font_size=18, space_after=10)

    # =========================================================================
    # SLIDE 3: Introduction
    # =========================================================================
    s3 = prs.slides[2]
    for shape in s3.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                "Modern enterprise networks face an unprecedented volume of sophisticated cyber threats, ranging from polymorphic exploits to high-velocity volumetric denial-of-service attacks. Traditional signature-based Network Intrusion Detection Systems (NIDS) rely on rigid rule tables that fail completely against novel zero-day attacks and evasive techniques.",
                "Supervised machine learning improves known attack classification, but struggles with extreme real-world class imbalance, concept drift, and severe Security Operations Center (SOC) alert fatigue. To bridge this gap, this project develops an end-to-end data mining and machine learning framework using the UNSW-NB15 benchmark dataset (45 flow attributes). It introduces a complementary dual-engine detection architecture combining a supervised Random Forest classifier for high-precision known attack classification with a semi-supervised PyTorch Deep Autoencoder trained strictly on normal traffic to detect out-of-distribution zero-day anomalies."
            ], default_font_size=19, space_after=14)

    # =========================================================================
    # SLIDE 4: Problem Statement
    # =========================================================================
    s4 = prs.slides[3]
    for shape in s4.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                "Conventional network intrusion detection systems suffer from four critical operational bottlenecks:",
                ("1. Class Imbalance & Alert Fatigue: ", "Normal network flows vastly outnumber rare attacks in real networks. Naive models achieve deceptive 90%+ accuracy while generating thousands of false alarms, paralyzing security teams (the Accuracy Paradox)."),
                ("2. Inability to Detect Zero-Day Exploits: ", "Purely supervised classifiers rely entirely on historical training labels and fail to detect novel attack variants or uncataloged vulnerabilities."),
                ("3. Data Leakage & Evaluation Bias: ", "Preprocessing encoders and scalers fitted across entire datasets leak test distribution statistics, producing artificially inflated research metrics that collapse in production."),
                ("4. Operational Deployment Void: ", "Most academic research remains static offline scripts lacking real-time stream replay, multi-model consensus arbitration, or actionable SOC dashboard interfaces.")
            ], default_font_size=17, space_after=10)

    # =========================================================================
    # SLIDE 5: Literature Survey (Table 4x5)
    # =========================================================================
    s5 = prs.slides[4]
    for shape in s5.shapes:
        if shape.has_table:
            tbl = shape.table
            lit_data = [
                ['Research Paper Title and Year', 'Author Name and Publication', 'Methodology', 'Advantages', 'Limitations'],
                [
                    'UNSW-NB15: A Comprehensive Data Set for NIDS (2015)',
                    'N. Moustafa & J. Slay, MilCIS / IEEE',
                    'Synthesized realistic modern attacks & normal flows using IXIA PerfectStorm across 45 features.',
                    'Realistic modern attack vectors; diverse protocols; overcomes legacy KDD99/NSL-KDD flaws.',
                    'Complex feature space & severe class imbalance require zero-leakage preprocessing.'
                ],
                [
                    'Random Forests for Network Intrusion Detection (2003)',
                    'J. Zhang, M. Zulkernine et al., IEEE',
                    'Ensemble of 100 decorrelated decision trees with Gini split criteria and out-of-bag validation.',
                    'High precision and recall on known attacks; provides feature importance ranking.',
                    'Supervised paradigm fails against uncataloged zero-day attacks absent from training.'
                ],
                [
                    'Kitsune: Ensemble of Autoencoders for Online NIDS (2018)',
                    'Y. Mirsky et al., NDSS / IEEE S&P',
                    'Neural bottleneck autoencoders trained on benign traffic to detect reconstruction anomalies.',
                    'Detects novel zero-day attacks without prior attack signatures or labels.',
                    'Higher false positive rate on complex normal flows; requires careful threshold tuning.'
                ]
            ]
            for r_idx, row in enumerate(tbl.rows):
                for c_idx, cell in enumerate(row.cells):
                    cell.text = lit_data[r_idx][c_idx]
                    p = cell.text_frame.paragraphs[0]
                    p.font.size = Pt(11 if r_idx > 0 else 12)
                    p.font.name = "Calibri"
                    if r_idx == 0:
                        p.font.bold = True

    # =========================================================================
    # SLIDE 6: Objective
    # =========================================================================
    s6 = prs.slides[5]
    for shape in s6.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                ("1. Stratified Benchmark Ingestion: ", "Ingest and profile the UNSW-NB15 dataset (257k full / 20k stratified laptop sample) with strict zero-leakage pipeline design."),
                ("2. Supervised Pattern Classification: ", "Train and optimize a 100-tree Supervised Random Forest Classifier with balanced class weighting to maximize detection recall on known attack patterns."),
                ("3. Semi-Supervised Anomaly Detection: ", "Engineer a deep PyTorch Autoencoder (42-D -> 64 -> 32 -> 16 -> 32 -> 64 -> 42-D) trained strictly on benign traffic to establish an out-of-distribution reconstruction cutoff."),
                ("4. Comprehensive Multi-Metric Evaluation: ", "Evaluate detection performance across Precision, Recall, F1-Score, False Positive Rate (FPR), ROC-AUC, and PR-AUC, resolving the Accuracy Paradox."),
                ("5. Interactive Flask SOC Deployment: ", "Deploy an interactive Flask SOC web dashboard featuring batch CSV prediction, dual-engine threat consensus alerting (NORMAL, SUSPICIOUS, CRITICAL), and dataset-based stream replay simulation.")
            ], default_font_size=17, space_after=10)

    # =========================================================================
    # SLIDE 7: Workflow Diagram (Serpentine Flow RR7-14 + RR22, 23)
    # =========================================================================
    s7 = prs.slides[6]
    workflow_box_texts = {
        'Rounded Rectangle 7': [
            {'text': "1. Telemetry Ingestion", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "UNSW-NB15 flow data\n& packet features (45-D)", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 8': [
            {'text': "2. Preprocess & Clean", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "Median imputation & missing\nvalue sanitation", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 9': [
            {'text': "3. Zero-Leakage Pipeline", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "StandardScaler & OneHot\nEncoder (187-D space)", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 10': [
            {'text': "4. Supervised RF Classifier", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "100 decorrelated trees for\nknown attack signatures", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 11': [
            {'text': "5. PyTorch Autoencoder", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "Bottleneck neural manifold\ntrained on benign flows", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 12': [
            {'text': "6. MSE Loss Thresholding", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "Calibrated 95th percentile\ncutoff score (0.0865)", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 13': [
            {'text': "7. Threat Consensus Arbiter", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "Hierarchical classification:\nNormal, Suspicious, Critical", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 14': [
            {'text': "8. Flask SOC Dashboard", 'bold': True, 'size': 14, 'align': PP_ALIGN.CENTER, 'space_after': 3},
            {'text': "Batch CSV prediction,\nstream replay & alerts", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.CENTER, 'space_after': 0}
        ],
        'Rounded Rectangle 22': [
            {'text': "Cross-Cutting: Integrity & Leakage Prevention", 'bold': True, 'size': 13.5, 'align': PP_ALIGN.LEFT, 'space_after': 4},
            {'text': "- Strict fit-on-train preprocessor isolation (preprocessor.joblib)", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.LEFT, 'space_after': 2},
            {'text': "- Target & ID attributes ('label', 'attack_cat', 'id') strictly excluded", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.LEFT, 'space_after': 2},
            {'text': "- Fixed random seed (42) for deterministic reproduction across runs", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.LEFT, 'space_after': 0}
        ],
        'Rounded Rectangle 23': [
            {'text': "Cross-Cutting: Operational SOC Usability", 'bold': True, 'size': 13.5, 'align': PP_ALIGN.LEFT, 'space_after': 4},
            {'text': "- Dual-engine consensus eliminates single-model alert fatigue", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.LEFT, 'space_after': 2},
            {'text': "- Vectorized batch scoring: 82,332 test records in 1.84 s (< 25 us/flow)", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.LEFT, 'space_after': 2},
            {'text': "- Configurable dataset-based replay simulation with delay controls", 'bold': False, 'size': 11.5, 'align': PP_ALIGN.LEFT, 'space_after': 0}
        ]
    }
    for shape in s7.shapes:
        if shape.name in workflow_box_texts:
            update_text_frame(shape.text_frame, workflow_box_texts[shape.name])

    # =========================================================================
    # SLIDE 8: Methodology (Part 1 - Data Selection & Preprocessing)
    # =========================================================================
    s8 = prs.slides[7]
    for shape in s8.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                ("KDD Data Selection & Ingestion: ", "Ingest UNSW-NB15 flow telemetry spanning 45 attributes across basic packet, content, temporal, and generated traffic metrics. Standard training (175,341 flows) and testing (82,332 flows) partitions are preserved alongside a stratified laptop research sample (15,000 train / 5,000 test)."),
                ("Data Cleaning & Target Isolation: ", "Replace infinite values (+/- inf) with NaN; impute numerical missing values with feature medians; impute categorical gaps with constant '-'. Database IDs ('id') and diagnostic labels ('attack_cat') are explicitly excluded from feature matrices to eliminate target leakage."),
                ("Categorical Encoding & Normalization: ", "Apply OneHotEncoder(handle_unknown='ignore') to nominal attributes ('proto', 'service', 'state'), producing 145 binary indicators. Standardize all numerical features using StandardScaler fitted exclusively on training records, establishing a 187-dimensional normalized feature space.")
            ], default_font_size=18, space_after=12)

    # =========================================================================
    # SLIDE 9: Methodology (Part 2 - Models & Consensus Arbiter)
    # =========================================================================
    s9 = prs.slides[8]
    for shape in s9.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                ("Supervised Random Forest Classifier: ", "Configure 100 decorrelated decision trees (max_depth=15, class_weight='balanced') using Gini impurity. Subsamples features at each split node to capture complex non-linear attack boundaries and compute feature importance scores for known intrusion vectors."),
                ("Semi-Supervised Deep Autoencoder (PyTorch): ", "Construct a symmetric bottleneck neural network (D -> 64 -> 32 -> 16 -> 32 -> 64 -> D) with ReLU activations and Adam optimization (lr=0.001, batch_size=128, 20 epochs). Trained exclusively on normal benign network flows (label = 0) to compress normal communication manifolds."),
                ("Anomaly Thresholding & Threat Consensus: ", "Calculate Mean Squared Error (MSE) reconstruction loss: L(x) = (1/D) * sum((x_i - x_hat_i)^2). Calibrate the anomaly decision cutoff at the 95th percentile of normal errors (0.0865). Combine outputs into a 3-tier threat consensus: NORMAL (both cleared), SUSPICIOUS (single engine flag), and CRITICAL INTRUSION (both triggered).")
            ], default_font_size=18, space_after=12)

    # =========================================================================
    # SLIDE 10: Tools
    # =========================================================================
    s10 = prs.slides[9]
    for shape in s10.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                ("Programming & Runtime: ", "Python 3.11 64-bit, PowerShell, Virtual Environment (.venv)"),
                ("Data Manipulation & Linear Algebra: ", "NumPy, Pandas, SciPy"),
                ("Machine Learning Engine: ", "Scikit-Learn (RandomForestClassifier, StandardScaler, OneHotEncoder)"),
                ("Deep Learning & Neural Networks: ", "PyTorch (Bottleneck Autoencoder, MSELoss, Adam Optimizer)"),
                ("Pipeline Persistence: ", "Joblib (serialization of fitted preprocessor and models)"),
                ("Web Application & REST API: ", "Flask 3.0, Jinja2 Templates, Werkzeug WSGI"),
                ("Frontend & Visualization: ", "HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Chart.js"),
                ("Diagnostic Plotting: ", "Matplotlib, Seaborn (ROC Curves, Confusion Matrices, Loss Curves)")
            ], default_font_size=17, space_after=8)

    # =========================================================================
    # SLIDE 11: Techniques
    # =========================================================================
    s11 = prs.slides[10]
    for shape in s11.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                ("KDD Data Mining Methodology: ", "Structured execution of Data Selection, Cleaning, Transformation, Modeling, and Diagnostic Evaluation."),
                ("Zero-Leakage Pipeline Architecture: ", "Strict fit-on-train design ensuring scalers and encoders never observe test distributions or streaming data in advance."),
                ("Ensemble Decision Tree Bagging: ", "Random feature subsampling and bootstrap aggregation to provide variance reduction and high recall on rare attack vectors."),
                ("Bottleneck Neural Manifold Learning: ", "Low-dimensional latent feature compression for unsupervised out-of-distribution zero-day anomaly detection."),
                ("Dual-Engine Threat Consensus: ", "Multi-tier decision arbitration balancing supervised precision with unsupervised anomaly sensitivity to eliminate alert fatigue."),
                ("Dataset-Based Stream Replay Simulation: ", "Time-delayed client-server batch simulation demonstrating streaming detection without invasive live packet capture.")
            ], default_font_size=17, space_after=9)

    # =========================================================================
    # SLIDE 12: Implementation
    # =========================================================================
    s12 = prs.slides[11]
    for shape in s12.shapes:
        if shape.name == 'Dataset Description':
            update_text_frame(shape.text_frame, [
                {'text': "System Architecture & Pipeline Setup", 'bold': True, 'size': 20, 'space_after': 4},
                {'text': "The system implements a defense-in-depth architecture combining a Supervised Random Forest Classifier (100 trees, balanced weighting) for signature matching with a Semi-Supervised PyTorch Deep Autoencoder (42-D -> 64 -> 32 -> 16 -> 32 -> 64 -> 42-D) trained exclusively on benign traffic to flag zero-day anomalies.", 'bold': False, 'size': 16, 'space_after': 12},
                {'text': "Telemetry & Pipeline Setup", 'bold': True, 'size': 20, 'space_after': 4},
                ("Dataset Attributes: ", "45 total flow features (3 nominal protocols, 39 packet/flow metrics)."),
                ("Transformed Dimension: ", "187-dimensional one-hot encoded and standardized vector space."),
                ("Anomaly Cutoff: ", "MSE reconstruction threshold calibrated at 0.0865 (95th percentile of normal flows)."),
                ("Serialized Artifacts: ", "preprocessor.joblib, random_forest_model.joblib, autoencoder_model.pt, evaluation_metrics.json.")
            ], default_font_size=16, space_after=6)

    # =========================================================================
    # SLIDE 13: Environment Setup
    # =========================================================================
    s13 = prs.slides[12]
    for shape in s13.shapes:
        if shape.name == 'Language & Platform':
            update_text_frame(shape.text_frame, [
                ("Language & Platform: ", "Python 3.11 64-bit on Windows 11 desktop, CPU-optimized execution ensuring seamless reproducibility on standard student laptops."),
                ("Libraries & Frameworks: ", "Scikit-Learn, PyTorch, NumPy, Pandas, SciPy, Joblib, Flask 3.0, Bootstrap 5.3, Chart.js."),
                ("Models & Algorithms: ", "Supervised Random Forest (Gini criterion, balanced class weighting), Deep Neural Autoencoder (MSELoss, Adam optimizer, lr=0.001, batch_size=128, 20 epochs), and 3-Tier Threat Consensus Arbiter."),
                ("Operational Performance: ", "Model training executes in under 15 seconds; vectorized web prediction scores all 82,332 test records in 1.84 seconds (< 25 us per flow).")
            ], default_font_size=17, space_after=12)

    # =========================================================================
    # SLIDE 14: Evaluation Metrics
    # =========================================================================
    s14 = prs.slides[13]
    for shape in s14.shapes:
        if shape.name == 'Key Performance Indicators':
            update_text_frame(shape.text_frame, [
                {'text': "Key Performance Indicators", 'bold': True, 'size': 22, 'space_after': 0}
            ])
        elif shape.name == 'Metrics':
            update_text_frame(shape.text_frame, [
                {'text': "Evaluation Dimensions", 'bold': True, 'size': 17, 'space_after': 4},
                ("Precision & Recall: ", "Quantifies attack detection accuracy and completeness of threat coverage."),
                ("F1-Score: ", "Harmonic mean providing a balanced evaluation metric under severe class imbalance."),
                ("Specificity & False Positive Rate: ", "Measures benign flow preservation and analyst alert fatigue."),
                ("Reconstruction MSE Cutoff: ", "Calibrated at 95th percentile (0.0865) for zero-day out-of-distribution detection.")
            ], default_font_size=14.5, space_after=4)
        elif shape.has_table:
            tbl = shape.table
            metrics_rows = [
                ['Model Metric (Holdout Benchmark)', 'Empirical Result'],
                ['Random Forest Attack Recall (Detection Rate)', '97.75% (2,691 / 2,753 attacks)'],
                ['Random Forest F1-Score / Precision', '0.9150 / 86.00% (ROC-AUC: 0.9816)'],
                ['Autoencoder Normal Specificity / FPR', '94.08% / 5.92% (Low Alert Fatigue)'],
                ['Dual-Engine Vectorized Batch Latency', '1.84 s for 82,332 records (< 25 us/flow)']
            ]
            for r_idx, row in enumerate(tbl.rows):
                for c_idx, cell in enumerate(row.cells):
                    cell.text = metrics_rows[r_idx][c_idx]
                    p = cell.text_frame.paragraphs[0]
                    p.font.size = Pt(11)
                    p.font.name = "Calibri"
                    if r_idx == 0:
                        p.font.bold = True

    # =========================================================================
    # SLIDE 15: Result Analysis
    # =========================================================================
    s15 = prs.slides[14]
    for shape in s15.shapes:
        if shape.name == 'TextBox 12':
            update_text_frame(shape.text_frame, [
                {'text': "Key Findings & Benefits", 'bold': True, 'size': 20, 'space_after': 0}
            ])
        elif shape.name == 'Benefits':
            update_text_frame(shape.text_frame, [
                ("Exceptional Known Attack Detection: ", "Random Forest delivers 97.75% recall and 0.9150 F1-score on holdout test attacks, successfully flagging 2,691 out of 2,753 malicious flows."),
                ("Complementary Zero-Day Filter: ", "Deep Autoencoder achieves 94.08% specificity with only 5.92% FPR, detecting novel out-of-distribution attacks without prior signature knowledge."),
                ("Resolution of Accuracy Paradox: ", "Proves that raw 90%+ accuracy is deceptive in security operations; balances Precision, Recall, and False Alarm rates."),
                ("Threat Consensus Hierarchy: ", "Combines outputs into Normal (both clear), Suspicious (single flag), and Critical Intrusion (both triggered) to eliminate single-point blind spots."),
                ("Production-Ready Flask SOC: ", "Offers sub-2-second batch CSV scoring for 82,000+ flows, interactive threshold tuning, and realistic dataset stream replay.")
            ], default_font_size=16, space_after=8)

    # =========================================================================
    # SLIDE 16: Conclusion
    # =========================================================================
    s16 = prs.slides[15]
    for shape in s16.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                "Successfully designed and evaluated an end-to-end data mining and machine learning framework for network intrusion and anomaly detection on the UNSW-NB15 benchmark.",
                "Proved that pairing supervised tree ensembles (Random Forest) with unsupervised bottleneck neural networks (Deep Autoencoder) creates a resilient defense-in-depth architecture.",
                "Enforced zero data leakage through strict fit-on-train preprocessor isolation, ensuring realistic and uncompromised evaluation metrics.",
                "Operationalized research models into an interactive, student-friendly Flask SOC dashboard with batch CSV scoring, stream replay simulation, and multi-tier threat consensus alerting.",
                "Resolved core academic challenges around class imbalance, alert fatigue, and real-time execution constraints on standard student hardware."
            ], default_font_size=17, space_after=10)

    # =========================================================================
    # SLIDE 17: Future Scope
    # =========================================================================
    s17 = prs.slides[16]
    for shape in s17.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                ("Live Raw Packet Sniffing Engine: ", "Integrate Scapy or DPDK with raw network socket listeners to extract UNSW-NB15 flow features directly from live Ethernet/Wi-Fi NIC interfaces in real time."),
                ("Granular Multi-Class Intrusion Classification: ", "Expand the supervised engine from binary detection to 9-class attack categorization (Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoor, Shellcode, Worms)."),
                ("Dynamic Anomaly Threshold Adaptation: ", "Implement adaptive sliding-window Kalman filtering or reinforcement learning to continuously tune the Autoencoder reconstruction cutoff against diurnal traffic shifts."),
                ("Deep Sequential & Temporal Modeling: ", "Incorporate Temporal Convolutional Networks (TCN) or LSTM Autoencoders to capture sequential packet dependencies across consecutive flow windows."),
                ("Enterprise SIEM Platform Integration: ", "Forward alert telemetry via Syslog (CEF / JSON format) and webhooks into enterprise SIEM tools such as Splunk, Elastic Security, and Microsoft Sentinel.")
            ], default_font_size=17, space_after=10)

    # =========================================================================
    # SLIDE 18: References (Min. 10 References) - Part 1
    # =========================================================================
    s18 = prs.slides[17]
    for shape in s18.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                "1. N. Moustafa and J. Slay, 'UNSW-NB15: A comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set),' in Proc. Military Communications and Information Systems Conference (MilCIS), 2015, pp. 1-6.",
                "2. L. Breiman, 'Random Forests,' Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.",
                "3. V. Chandola, A. Banerjee, and V. Kumar, 'Anomaly detection: A survey,' ACM Computing Surveys (CSUR), vol. 41, no. 3, pp. 1-58, 2009.",
                "4. Y. Mirsky, T. Doitshman, Y. Elovici, and A. Shabtai, 'Kitsune: An ensemble of autoencoders for online network intrusion detection,' in Proc. Network and Distributed System Security Symposium (NDSS), 2018.",
                "5. M. Ring, S. Wunderlich, D. Scheuring, D. Landes, and A. Hotho, 'A survey of network-based intrusion detection data sets,' Computers & Security, vol. 86, pp. 147-167, 2019."
            ], default_font_size=14, space_after=8)

    # =========================================================================
    # SLIDE 19: References (Contd.) - Part 2
    # =========================================================================
    s19 = prs.slides[18]
    for shape in s19.shapes:
        if shape.name == 'Content Placeholder 2':
            update_text_frame(shape.text_frame, [
                "6. N. Moustafa and J. Slay, 'The evaluation of Network Anomaly Detection Systems: Statistical analysis of the UNSW-NB15 data set and the comparison with the KDD99 data set,' Information Security Journal: A Global Perspective, vol. 25, no. 1-3, pp. 18-31, 2016.",
                "7. F. E. Febro and N. Moustafa, 'Co-design of edge-AI and cloud computing for cyber threat detection in smart grids,' IEEE Transactions on Industrial Informatics, vol. 18, no. 11, pp. 8056-8066, 2022.",
                "8. R. Sommer and V. Paxson, 'Outside the closed world: On using machine learning for network intrusion detection,' in Proc. IEEE Symposium on Security and Privacy (SP), 2010, pp. 305-316.",
                "9. A. L. Buczak and E. Guven, 'A survey of data mining and machine learning methods for cyber security intrusion detection,' IEEE Communications Surveys & Tutorials, vol. 18, no. 2, pp. 1153-1176, 2016.",
                "10. U. M. Fayyad, G. Piatetsky-Shapiro, and P. Smyth, 'The KDD process for extracting useful knowledge from volumes of data,' Communications of the ACM, vol. 39, no. 11, pp. 27-34, 1996."
            ], default_font_size=14, space_after=8)

    # =========================================================================
    # SLIDE 20: Thank you!
    # =========================================================================
    s20 = prs.slides[19]
    for shape in s20.shapes:
        if shape.name == 'Title 1':
            update_text_frame(shape.text_frame, [
                {'text': "Thank you!", 'bold': True, 'size': 44, 'align': PP_ALIGN.CENTER, 'space_after': 10},
                {'text': "Questions & Discussion", 'bold': False, 'size': 24, 'align': PP_ALIGN.CENTER, 'space_after': 14},
                {'text': "Bharathram K (Reg. No: E0324006) | Guided by: Prof. P. Deepika\nDepartment of Computer Science & Engineering (AI & DA)\nSri Ramachandra Institute of Higher Education and Research (SRIHER)", 'bold': False, 'size': 16, 'align': PP_ALIGN.CENTER, 'space_after': 0}
            ])

    # Save presentation
    output_path = 'doc/NEXUS_Project_PPT.pptx'
    final_copy_path = 'doc/Network_Intrusion_Detection_Presentation.pptx'
    
    prs.save(output_path)
    print(f"Successfully saved updated presentation to {output_path}")
    prs.save(final_copy_path)
    print(f"Successfully saved copy to {final_copy_path}")

if __name__ == '__main__':
    build_presentation()
