#!/usr/bin/env python3
"""
Download benchmark datasets for DIVA-SQL evaluation

This script downloads the Spider and BIRD datasets for Text-to-SQL benchmarking.
"""

import os
import sys
import argparse
import urllib.request
import zipfile
import json
from pathlib import Path
from tqdm import tqdm

# Set up download directory
BENCHMARK_DIR = Path(__file__).parent.parent / "data" / "benchmarks"

# URLs for datasets
SPIDER_URL = "https://drive.google.com/uc?export=download&id=1iRDVHLr4mX2wQKSgA9J8juoRb2rGX6CS"
BIRD_DEV_URL = "https://bird-bench.github.io/assets/bird/bird-dev.json"
BIRD_TEST_URL = "https://bird-bench.github.io/assets/bird/bird-test.json"

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=output_path.name) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

def download_spider():
    """Download and extract the Spider dataset"""
    spider_dir = BENCHMARK_DIR / "spider"
    spider_zip = BENCHMARK_DIR / "spider.zip"
    
    if spider_dir.exists():
        print(f"Spider dataset already exists at {spider_dir}")
        return
    
    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    
    print("Downloading Spider dataset...")
    try:
        # Alternative direct download URL for Spider
        direct_spider_url = "https://huggingface.co/datasets/spider/resolve/main/spider.zip"
        print(f"Attempting to download from HuggingFace: {direct_spider_url}")
        download_url(direct_spider_url, spider_zip)
    except Exception as e:
        print(f"Error downloading from HuggingFace: {e}")
        print("Attempting alternative download source...")
        try:
            github_url = "https://github.com/taoyds/spider/raw/master/data/spider.zip"
            download_url(github_url, spider_zip)
        except Exception as e2:
            print(f"Error downloading from alternative source: {e2}")
            print("Please download the Spider dataset manually from:")
            print("https://yale-lily.github.io/spider")
            print(f"And place it in {BENCHMARK_DIR}")
            return
    
    print("Extracting Spider dataset...")
    with zipfile.ZipFile(spider_zip, 'r') as zip_ref:
        zip_ref.extractall(BENCHMARK_DIR)
    
    # Clean up the zip file
    os.remove(spider_zip)
    
    # Check if extraction was successful
    if spider_dir.exists():
        print(f"Successfully downloaded and extracted Spider dataset to {spider_dir}")
        # Count the number of databases
        db_count = len(list((spider_dir / "database").glob("*")))
        print(f"Dataset contains {db_count} databases")
    else:
        print("Error: Failed to extract Spider dataset")
        
def download_bird():
    """Download the BIRD dataset"""
    bird_dir = BENCHMARK_DIR / "bird"
    bird_dev = BENCHMARK_DIR / "bird-dev.json"
    bird_test = BENCHMARK_DIR / "bird-test.json"
    
    if bird_dev.exists() and bird_test.exists():
        print(f"BIRD dataset already exists at {BENCHMARK_DIR}")
        return
    
    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    
    print("Downloading BIRD dev set...")
    try:
        download_url(BIRD_DEV_URL, bird_dev)
    except Exception as e:
        print(f"Error downloading BIRD dev set: {e}")
        print("Attempting alternative download source...")
        try:
            alt_url = "https://huggingface.co/datasets/BIRD/resolve/main/bird-dev.json"
            download_url(alt_url, bird_dev)
        except Exception as e2:
            print(f"Error downloading from alternative source: {e2}")
            print("Please download the BIRD dev set manually from:")
            print("https://bird-bench.github.io/")
            print(f"And place it in {BENCHMARK_DIR}")
            return
    
    print("Downloading BIRD test set...")
    try:
        download_url(BIRD_TEST_URL, bird_test)
    except Exception as e:
        print(f"Error downloading BIRD test set: {e}")
        print("Attempting alternative download source...")
        try:
            alt_url = "https://huggingface.co/datasets/BIRD/resolve/main/bird-test.json"
            download_url(alt_url, bird_test)
        except Exception as e2:
            print(f"Error downloading from alternative source: {e2}")
            print("Note: Test set is optional for evaluation. Continuing with dev set only.")
    
    # Check if downloads were successful
    if bird_dev.exists():
        # Create bird directory for databases
        os.makedirs(bird_dir / "databases", exist_ok=True)
        
        # Load the dev set to count examples
        try:
            with open(bird_dev, 'r') as f:
                bird_dev_data = json.load(f)
            
            print(f"Successfully downloaded BIRD dataset to {BENCHMARK_DIR}")
            print(f"Dev set contains {len(bird_dev_data)} examples")
        except Exception as e:
            print(f"Warning: Could not parse BIRD dev set: {e}")
            
        print(f"Warning: BIRD requires additional database files that must be downloaded separately")
        print(f"Please visit https://bird-bench.github.io/ for full database downloads")
    else:
        print("Error: Failed to download BIRD dataset")

def parse_args():
    parser = argparse.ArgumentParser(description='Download benchmark datasets for DIVA-SQL')
    parser.add_argument('--dataset', type=str, choices=['spider', 'bird', 'all'], default='all',
                       help='Which dataset to download')
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.dataset == 'spider' or args.dataset == 'all':
        download_spider()
    
    if args.dataset == 'bird' or args.dataset == 'all':
        download_bird()
    
    print("\nDownload complete!")
    print("To run the benchmarks, use the following commands:")
    print("  python evaluation/benchmark_eval.py --benchmark spider --split dev --limit 10")
    print("  python evaluation/rate_limited_eval.py --benchmark spider --sample 5 --delay 3")

if __name__ == '__main__':
    main()
