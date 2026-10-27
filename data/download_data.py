"""
Dataset Download Utility for UNSW-NB15
Downloads the official training and testing sets from reliable mirrors
and creates lightweight student samples for quick laptop experimentation.
"""

import os
import sys
import ssl
import shutil
import urllib.request
import pandas as pd
from sklearn.model_selection import train_test_split

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DATA_DIR)
LOCAL_CSV_DIR = os.path.join(BASE_DIR, "CSV Files", "Training and Testing Sets")

URLS = {
    "UNSW_NB15_training-set.csv": "https://raw.githubusercontent.com/princee1/UNSW_NB15-Data-analysis/master/UNSW_NB15_training-set.csv",
    "UNSW_NB15_testing-set.csv": "https://raw.githubusercontent.com/princee1/UNSW_NB15-Data-analysis/master/UNSW_NB15_testing-set.csv"
}

def download_file(url: str, dest_path: str):
    """Download a file with progress reporting and SSL fallback, checking local fallback first."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000000:
        print(f"[+] Already downloaded: {os.path.basename(dest_path)} ({os.path.getsize(dest_path):,} bytes)")
        return

    # Check if file exists in CSV Files folder first
    filename = os.path.basename(dest_path)
    local_source = os.path.join(LOCAL_CSV_DIR, filename)
    if os.path.exists(local_source) and os.path.getsize(local_source) > 10000000:
        print(f"[+] Found existing local file in '{LOCAL_CSV_DIR}'. Copying to data/...")
        shutil.copy2(local_source, dest_path)
        print(f"[+] Copied to {dest_path}")
        return

    print(f"[~] Downloading {os.path.basename(dest_path)} from {url}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as response, open(dest_path, 'wb') as out_file:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 64
        downloaded = 0
        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            if total_size > 0:
                percent = downloaded / total_size * 100
                sys.stdout.write(f"\r    -> {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB ({percent:.1f}%)")
                sys.stdout.flush()
    print(f"\n[+] Saved to {dest_path}")

def create_sample_datasets(train_path: str, test_path: str, train_sample_size: int = 15000, test_sample_size: int = 5000):
    """Create stratified sample CSVs for fast execution on student laptops."""
    sample_train_path = os.path.join(DATA_DIR, "sample_training-set.csv")
    sample_test_path = os.path.join(DATA_DIR, "sample_testing-set.csv")

    print("\n[~] Generating lightweight student sample datasets for rapid experimentation...")
    train_df = pd.read_csv(train_path, encoding='utf-8-sig')
    test_df = pd.read_csv(test_path, encoding='utf-8-sig')

    train_df.columns = train_df.columns.str.strip()
    test_df.columns = test_df.columns.str.strip()

    # Stratified sampling on 'label'
    if 'label' in train_df.columns:
        train_sample, _ = train_test_split(
            train_df,
            train_size=min(train_sample_size, len(train_df)),
            stratify=train_df['label'],
            random_state=42
        )
    else:
        train_sample = train_df.sample(min(len(train_df), train_sample_size), random_state=42)

    if 'label' in test_df.columns:
        test_sample, _ = train_test_split(
            test_df,
            train_size=min(test_sample_size, len(test_df)),
            stratify=test_df['label'],
            random_state=42
        )
    else:
        test_sample = test_df.sample(min(len(test_df), test_sample_size), random_state=42)

    train_sample.to_csv(sample_train_path, index=False)
    test_sample.to_csv(sample_test_path, index=False)
    print(f"[+] Saved sample train ({len(train_sample):,} rows, {len(train_sample.columns)} cols) to: {sample_train_path}")
    print(f"[+] Saved sample test ({len(test_sample):,} rows, {len(test_sample.columns)} cols) to: {sample_test_path}")

if __name__ == "__main__":
    for fname, url in URLS.items():
        dest = os.path.join(DATA_DIR, fname)
        download_file(url, dest)

    train_file = os.path.join(DATA_DIR, "UNSW_NB15_training-set.csv")
    test_file = os.path.join(DATA_DIR, "UNSW_NB15_testing-set.csv")
    if os.path.exists(train_file) and os.path.exists(test_file):
        create_sample_datasets(train_file, test_file)
    print("\n[+] Dataset preparation complete!")
