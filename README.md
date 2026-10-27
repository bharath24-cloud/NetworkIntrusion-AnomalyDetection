# Real-Time Network Intrusion and Anomaly Detection

A student project that analyzes network-flow records from the UNSW-NB15 dataset. It compares a supervised Random Forest classifier with a deep autoencoder trained on normal traffic, and presents results in a Flask dashboard.

The dashboard supports CSV predictions and dataset replay. Replay processes saved test records to demonstrate the workflow; it does not monitor live network traffic.

## Features

- Clean and preprocess UNSW-NB15 network-flow data.
- Train and evaluate a Random Forest classifier for normal-versus-attack classification.
- Train a PyTorch autoencoder on normal training records and use reconstruction error to flag unusual flows.
- Compare models with precision, recall, F1-score, specificity, false-positive rate, ROC-AUC, and PR-AUC.
- View metrics, upload CSV files for prediction, and replay test records in the Flask dashboard.

## Dataset

UNSW-NB15 contains labeled network-flow records. Each row describes a connection using features such as protocol, service, connection state, duration, packet and byte counts, traffic rates, and timing statistics.

- `label`: `0` for normal traffic, `1` for attack traffic.
- `attack_cat`: attack category metadata.
- `proto`, `service`, `state`: categorical network-flow features.

The models must not receive target columns such as `label` or `attack_cat` as input features. The complete dataset is not included in this repository. Obtain it from the [official UNSW-NB15 dataset page](https://research.unsw.edu.au/projects/unsw-nb15-dataset) and place the prepared CSV files in `data/`. Small sample CSVs may be used for a lightweight demo.

## Method

### Preprocessing

The pipeline cleans missing and infinite values, imputes missing values, scales numerical features, and one-hot encodes categorical features. Preprocessing is fitted on training data only, then reused for testing and prediction to avoid data leakage.

### Random Forest

The Random Forest learns from labeled training records and predicts whether a flow is normal or an attack. It also provides an attack probability.

### Deep Autoencoder

The autoencoder learns to reconstruct normal traffic. It calculates the mean squared reconstruction error for each flow:

\[
\text{MSE}(x,\hat{x}) = \frac{1}{D}\sum_{j=1}^{D}(x_j-\hat{x}_j)^2
\]

An error above the configured threshold is flagged as anomalous. This is an anomaly-detection experiment; the project does not establish that it detects real-world zero-day attacks.

## Results

The following results are from the sample run using 15,000 training rows and 5,000 test rows. Results may differ when training on the full dataset.

| Metric | Random Forest | Deep Autoencoder |
|---|---:|---:|
| Precision | 0.8600 | 0.8350 |
| Recall | 0.9775 | 0.2445 |
| F1-score | 0.9150 | 0.3782 |
| Specificity | 0.8051 | 0.9408 |
| False-positive rate | 0.1949 | 0.0592 |
| ROC-AUC | 0.9816 | 0.7810 |
| PR-AUC | 0.9860 | 0.7491 |

In this sample run, the Random Forest detected more attacks. The autoencoder had higher specificity but low attack recall, so it missed many attacks at the selected threshold.

## Project Structure

```text
NI&AD/
├── app.py
├── train.py
├── requirements.txt
├── data/
│   ├── download_data.py
│   ├── sample_training-set.csv
│   └── sample_testing-set.csv
├── models/
│   └── saved/
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── evaluation.py
│   ├── preprocessor.py
│   ├── stream_simulator.py
│   └── models/
├── static/
├── templates/
└── doc/
```

## Setup on Windows

Open PowerShell in the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, allow it for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Prepare Data and Train

If you need to download or prepare the dataset, follow the instructions in `data/download_data.py`. For a quick student-laptop run with the sample files:

```powershell
python train.py --mode sample --ae-epochs 10
```

For full training, when your computer has enough memory and processing capacity:

```powershell
python train.py --mode full --ae-epochs 20
```

Training saves the preprocessor, models, and evaluation metrics under `models/saved/`.

## Run the Flask Dashboard

With the virtual environment active:

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. Keep the terminal running while using the dashboard.

The dashboard includes:

- **Model Metrics:** model comparison and evaluation results.
- **CSV Prediction:** upload a compatible network-flow CSV and view predictions and anomaly scores.
- **Dataset Replay:** process saved test flows in sequence as a demonstration.

## Notes

- The project is an educational benchmark prototype, not a production security system.
- Dataset replay is simulated from saved CSV records; there is no live packet capture.
- Do not upload the full dataset, virtual environment, secrets, or temporary files to GitHub.
- Cite the dataset and research papers if you use this project in an academic report.

## References

1. Moustafa, N. and Slay, J. “UNSW-NB15: a comprehensive data set for network intrusion detection systems.” *Military Communications and Information Systems Conference*, 2015.
2. Moustafa, N. and Slay, J. “The evaluation of Network Anomaly Detection Systems.” *Information Security Journal: A Global Perspective*, 2016.
3. Sommer, R. and Paxson, V. “Outside the Closed World: On Using Machine Learning for Network Intrusion Detection.” *IEEE Symposium on Security and Privacy*, 2010.
