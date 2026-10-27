import sys
sys.path.insert(0, '.')
import time
import pandas as pd
from src.config import config
from src.preprocessor import DataPreprocessor
from src.models.random_forest_model import RandomForestModel
from src.models.autoencoder_model import DeepAutoencoderModel

t0 = time.time()
print("Loading preprocessor and models...")
prep = DataPreprocessor.load(config.PREPROCESSOR_PATH)
rf = RandomForestModel.load(config.RF_MODEL_PATH)
ae = DeepAutoencoderModel.load(config.AUTOENCODER_PATH, config.AE_CONFIG_PATH)
print(f"Loaded models in {time.time()-t0:.2f}s")

t0 = time.time()
df = pd.read_csv('data/UNSW_NB15_testing-set.csv', low_memory=False)
print(f"Read CSV ({len(df)} rows) in {time.time()-t0:.2f}s")

t0 = time.time()
X_trans = prep.transform(df)
print(f"Transformed features {X_trans.shape} in {time.time()-t0:.2f}s")

t0 = time.time()
rf_probs = rf.predict_proba(X_trans)
print(f"RF predict_proba in {time.time()-t0:.2f}s")

t0 = time.time()
ae_scores = ae.compute_reconstruction_error(X_trans)
print(f"AE reconstruction in {time.time()-t0:.2f}s")
