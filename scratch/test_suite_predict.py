import sys
sys.path.insert(0, '.')
import io
import time
from app import app

client = app.test_client()

print("=" * 60)
print("TEST 1: Submitting with NO file selected")
resp = client.post('/predict', data={}, content_type='multipart/form-data', follow_redirects=True)
print("Status code:", resp.status_code)
assert resp.status_code == 200
assert b"No file" in resp.data
print("PASSED TEST 1")

print("=" * 60)
print("TEST 2: Submitting an empty filename")
resp = client.post('/predict', data={'file': (io.BytesIO(b""), "")}, content_type='multipart/form-data', follow_redirects=True)
print("Status code:", resp.status_code)
assert resp.status_code == 200
assert b"No file selected" in resp.data
print("PASSED TEST 2")

print("=" * 60)
print("TEST 3: Submitting a non-CSV file (.txt)")
resp = client.post('/predict', data={'file': (io.BytesIO(b"hello world"), "test.txt")}, content_type='multipart/form-data', follow_redirects=True)
print("Status code:", resp.status_code)
assert resp.status_code == 200
assert b"Invalid file format" in resp.data
print("PASSED TEST 3")

print("=" * 60)
print("TEST 4: Submitting an invalid CSV (wrong headers)")
resp = client.post('/predict', data={'file': (io.BytesIO(b"colA,colB,colC\n1,2,3"), "test.csv")}, content_type='multipart/form-data', follow_redirects=True)
print("Status code:", resp.status_code)
assert resp.status_code == 200
assert b"do not match network flow telemetry" in resp.data
print("PASSED TEST 4")

print("=" * 60)
print("TEST 5: Submitting sample_testing-set.csv (5,000 rows)")
t0 = time.time()
with open('data/sample_testing-set.csv', 'rb') as f:
    resp = client.post('/predict', data={'file': (f, 'sample_testing-set.csv')}, content_type='multipart/form-data', follow_redirects=True)
print(f"Sample test took {time.time()-t0:.2f}s, status code: {resp.status_code}")
assert resp.status_code == 200
assert b"5,000" in resp.data
assert b"Random Forest Attacks" in resp.data
print("PASSED TEST 5")

print("=" * 60)
print("TEST 6: Submitting full UNSW_NB15_testing-set.csv (82,332 rows, 15.4 MB)")
t0 = time.time()
with open('data/UNSW_NB15_testing-set.csv', 'rb') as f:
    resp = client.post('/predict', data={'file': (f, 'UNSW_NB15_testing-set.csv')}, content_type='multipart/form-data', follow_redirects=True)
elapsed = time.time() - t0
print(f"Full benchmark upload took {elapsed:.2f}s, status code: {resp.status_code}")
assert resp.status_code == 200
assert b"82,332" in resp.data
assert b"Random Forest Attacks" in resp.data
assert b"Top 200 Preview" in resp.data
print("PASSED TEST 6")

print("=" * 60)
print("TEST 7: Downloading full CSV predictions for 82,332 rows")
t0 = time.time()
resp_dl = client.get('/download-predictions')
print(f"Download took {time.time()-t0:.2f}s, status: {resp_dl.status_code}, size: {len(resp_dl.data)/1024/1024:.2f} MB")
assert resp_dl.status_code == 200
assert resp_dl.headers["Content-Type"].startswith("text/csv")
lines_count = resp_dl.data.count(b"\n")
print(f"CSV has {lines_count:,} lines (header + 82,332 rows)!")
assert lines_count >= 82332
print("PASSED TEST 7")

print("=" * 60)
print("TEST 8: One-Click 50 Flows Demo (/predict/sample)")
resp_sample = client.post('/predict/sample', follow_redirects=True)
print("Sample demo status:", resp_sample.status_code)
assert resp_sample.status_code == 200
assert b"50" in resp_sample.data
print("PASSED TEST 8")

print("\nALL 8 INTEGRATION TESTS PASSED SUCCESSFULLY!")
