# 3GPP Standard Crawler

## Project Overview

This script is a multi-threaded download agent designed to crawl and download 3GPP standards for a specific release from the official 3GPP FTP server. It is built to be efficient and resilient, supporting download resumption and providing clear progress indication.

## Features

- **Targeted Release:** Easily configurable to download any specific 3GPP release (e.g., Rel-18, Rel-19).
- **Multi-threaded Downloading:** Utilizes multiple threads to download files concurrently, significantly speeding up the process.
- **Resume on Interrupt:** Maintains a state file (`download_state_rel-XX.json`) to keep track of completed downloads. If the script is stopped and restarted, it will skip already downloaded files and resume where it left off.
- **Progress Bars:** Provides detailed progress bars for both the overall download process and individual file downloads, giving clear visual feedback.
- **Robust Error Handling:** Includes error handling for network issues and file I/O problems.
- **Simple Configuration:** Key parameters like the release number and number of threads are easily configurable at the top of the script.

## Prerequisites

- Python 3.6 or higher
- An active internet connection

## Installation

1.  **Clone the repository or download the source code.**

2.  **Install the required Python packages.** Navigate to the project's root directory in your terminal and run the following command:

    ```bash
    pip install -r requirements.txt
    ```
    This will install `requests`, `beautifulsoup4`, and `tqdm`.

## Usage

To run the script, execute `main.py` from the project's root directory:

```bash
python src/main.py
```

The script will then:
1.  Create a directory named `3gpp_standards_rel-XX` (where XX is the configured release number).
2.  Scan the known series directories for the specified release.
3.  Begin downloading the specification files, showing progress as it goes.

## Configuration

All configuration is done at the top of the `src/main.py` file:

- `BASE_REVERSION`: Set this string to the desired release number (e.g., `"18"`, `"19"`). This determines which release will be downloaded.
- `MAX_THREADS`: Adjust this integer to control the number of concurrent download threads. A higher number can speed up downloads but may also increase network and CPU load. The default is `7`.

Example:
```python
# Configuration
BASE_REVERSION = "18"
BASE_URL = f"https://www.3gpp.org/ftp/Specs/latest/Rel-{BASE_REVERSION}/"
DOWNLOAD_DIR = f"3gpp_standards_rel-{BASE_REVERSION}"
STATE_FILE = f"download_state_rel-{BASE_REVERSION}.json"
MAX_THREADS = 7
```

## How It Works

1.  **Initialization:** The script reads the `BASE_REVERSION` to construct the target URL, download directory, and state file name.
2.  **Link Gathering:** It iterates through a hardcoded list of known series directories (`SERIES_DIRS`). For each directory, it sends an HTTP request to fetch the page content.
3.  **Parsing:** It uses `BeautifulSoup` to parse the HTML of each series page and extracts all links that point to `.zip` files.
4.  **Queueing:** All unique file URLs are added to a queue. The script checks the state file and only queues files that have not been previously downloaded.
5.  **Downloading:** A pool of worker threads is created. Each thread takes a URL from the queue and downloads the corresponding file, showing a progress bar for that specific download.
6.  **State Management:** Upon successful download of a file, its path is recorded in the state file.
7.  **Completion:** Once all files are downloaded, the script cleans up by removing the state file.

## Precautions

- **Network Usage:** This script can download a large number of files, potentially consuming significant bandwidth. Be mindful of your network's data limits.
- **Server Load:** While the script uses a reasonable number of threads by default, setting `MAX_THREADS` to a very high number could place an excessive load on the 3GPP server. Please be considerate.
- **Firewall/Proxy:** If you are behind a corporate firewall or proxy, you may need to configure environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) for the script to access the internet.
- **Website Changes:** The script relies on the current structure of the 3GPP FTP website. If the website's URL scheme or page layout changes significantly, the script may need to be updated.
