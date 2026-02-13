# Project: 3GPP Standard Crawler
# File: src/main.py
# Copyright (c) 2026 Washington Ruan. All rights reserved.
# Author: Washington Ruan
# Email: washingtonxr@gmail.com
# Date: 2026-02-12 17:00 Beijing time
# This script is designed to download all specification files from the 3GPP website for a specific release (Rel-18 in this case).
# It uses multithreading to speed up the download process and includes error handling to manage potential issues with network requests 
# or file writing. The script also maintains a state file to track downloaded files, allowing it to resume interrupted downloads without 
# duplicating efforts.

import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
from pathlib import Path
import json
from tqdm import tqdm
import queue

# Configuration
BASE_REVERSION = "9"
BASE_URL = f"https://www.3gpp.org/ftp/Specs/latest/Rel-{BASE_REVERSION}/"
DOWNLOAD_DIR = f"data/Rel-{BASE_REVERSION}"
STATE_FILE = f"download_state_rel-{BASE_REVERSION}.json"
MAX_THREADS = 7

# Set a User-Agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Hardcoded list of series directories based on your input
SERIES_DIRS = [
    "21_series/", "22_series/", "23_series/", "24_series/", "25_series/",
    "26_series/", "27_series/", "28_series/", "29_series/", "31_series/",
    "32_series/", "33_series/", "34_series/", "35_series/", "36_series/",
    "37_series/", "38_series/", "41_series/", "42_series/", "43_series/",
    "44_series/", "45_series/", "46_series/", "48_series/", "49_series/",
    "51_series/", "52_series/", "55_series/"
]

def get_all_spec_files():
    """
    Fetches all .zip file links by iterating through a hardcoded list of series directories.
    """
    print(f"Fetching spec files from known Rel-{BASE_REVERSION} series directories...")
    all_spec_files = []
    
    for series_dir in tqdm(SERIES_DIRS, desc="Scanning Series Dirs"):
        series_url = urljoin(BASE_URL, series_dir)
        try:
            response = requests.get(series_url, headers=HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=re.compile(r'\.zip$')):
                all_spec_files.append(urljoin(series_url, link['href']))
                
        except requests.exceptions.RequestException as e:
            print(f"\nCould not fetch {series_url}: {e}")

    return sorted(list(set(all_spec_files)))

def save_state(state):
    """Saves the download state to a file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def load_state():
    """Loads the download state from a file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"downloaded_files": []}

def download_file(url, state):
    """
    Downloads a single file and updates the state.
    """
    filename = url.split('/')[-1]
    series = url.split('/')[-2]
    
    series_dir = Path(DOWNLOAD_DIR) / series
    series_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = series_dir / filename
    
    if str(filepath) in state["downloaded_files"]:
        return

    try:
        response = requests.get(url, stream=True, headers=HEADERS)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        with open(filepath, 'wb') as f, tqdm(
            total=total_size, unit='iB', unit_scale=True, desc=filename, leave=False
        ) as file_pbar:
            for data in response.iter_content(block_size):
                file_pbar.update(len(data))
                f.write(data)

        state["downloaded_files"].append(str(filepath))
        save_state(state)

    except requests.exceptions.RequestException as e:
        print(f"\nError downloading {url}: {e}")
    except IOError as e:
        print(f"\nError writing to file {filepath}: {e}")


def worker(url_queue, state, pbar):
    """Worker thread for downloading files."""
    while True:
        try:
            url = url_queue.get_nowait()
            download_file(url, state)
            url_queue.task_done()
            pbar.update(1)
        except queue.Empty:
            break

def main():
    """
    Main function to orchestrate the download process.
    """
    Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
    state = load_state()

    all_spec_files = get_all_spec_files()

    if not all_spec_files:
        print("No specification files found to download. Exiting.")
        return
        
    url_queue = queue.Queue()
    # Filter out already downloaded files before adding to queue
    files_to_download = [f for f in all_spec_files if str(Path(DOWNLOAD_DIR) / f.split('/')[-2] / f.split('/')[-1]) not in state["downloaded_files"]]
    
    for spec_file in files_to_download:
        url_queue.put(spec_file)

    print(f"Found {len(all_spec_files)} total files, {len(files_to_download)} to download.")

    with tqdm(total=len(files_to_download), desc="Overall Progress") as pbar:
        threads = []
        for _ in range(MAX_THREADS):
            thread = threading.Thread(target=worker, args=(url_queue, state, pbar))
            thread.start()
            threads.append(thread)

        url_queue.join()

    print("All downloads completed.")
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

if __name__ == "__main__":
    main()
