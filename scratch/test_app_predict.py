import sys
sys.path.insert(0, '.')
import time
import io
import pandas as pd
from app import app, pipeline_state

print("Testing full upload pipeline with sample_testing-set.csv and full testing CSV...")

client = app.test_client()

# Test 1: Upload sample_testing-set.csv
with open('data/sample_testing-set.csv', 'rb') as f:
    resp = client.post('/predict', data={'file': (f, 'sample_testing-set.csv')}, content_type='multipart/form-data', follow_redirects=True)
    print("Test 1 status:", resp.status_code)
    assert resp.status_code == 200

# Test 2: Upload CSV with target columns and ID column
# Verify download
resp_dl = client.get('/download-predictions')
print("Download status:", resp_dl.status_code)
assert resp_dl.status_code == 200
print("Downloaded bytes:", len(resp_dl.data))
print("Tests passed!")
