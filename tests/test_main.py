# Project: 3GPP Standard Crawler
# File: tests/test_main.py
# Copyright (c) 2026 Washington Ruan. All rights reserved.
# Author: Washington Ruan
# Email: washingtonxr@gmail.com
# Date: 2026-02-12 17:00 Beijing time
# This script is designed to download all specification files from the 3GPP website for a specific release (Rel-18 in this case).
# It uses multithreading to speed up the download process and includes error handling to manage potential issues with network requests 
# or file writing. The script also maintains a state file to track downloaded files, allowing it to resume interrupted downloads without 
# duplicating efforts.

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path to allow importing the main script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import get_latest_specs_links, get_spec_files_from_series, download_file, save_state, load_state

class Test3gppDownloader(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.base_url = "https://www.3gpp.org/ftp/Specs/latest"
        self.download_dir = "test_downloads"
        self.state_file = "test_state.json"
        
        # Override constants in main module
        self.patcher_download_dir = patch('src.main.DOWNLOAD_DIR', self.download_dir)
        self.patcher_state_file = patch('src.main.STATE_FILE', self.state_file)
        self.mock_download_dir = self.patcher_download_dir.start()
        self.mock_state_file = self.patcher_state_file.start()

        Path(self.download_dir).mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.download_dir):
            for series_dir in os.listdir(self.download_dir):
                series_path = os.path.join(self.download_dir, series_dir)
                for f in os.listdir(series_path):
                    os.remove(os.path.join(series_path, f))
                os.rmdir(series_path)
            os.rmdir(self.download_dir)
        
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
            
        self.patcher_download_dir.stop()
        self.patcher_state_file.stop()

    @patch('src.main.requests.get')
    def test_get_latest_specs_links(self, mock_get):
        """Test fetching latest spec links."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
            <a href="21-series/">21-series/</a>
            <a href="22-series/">22-series/</a>
            <a href="invalid/">invalid/</a>
        </body></html>
        """
        mock_get.return_value = mock_response

        links = get_latest_specs_links()
        self.assertEqual(len(links), 2)
        self.assertIn(f"{self.base_url}/21-series/", links)
        self.assertIn(f"{self.base_url}/22-series/", links)

    @patch('src.main.requests.get')
    def test_get_spec_files_from_series(self, mock_get):
        """Test fetching spec files from a series page."""
        series_url = f"{self.base_url}/21-series/"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
            <a href="21101-g00.zip">21101-g00.zip</a>
            <a href="21905-g00.zip">21905-g00.zip</a>
            <a href="not_a_zip.txt">not_a_zip.txt</a>
        </body></html>
        """
        mock_get.return_value = mock_response

        files = get_spec_files_from_series(series_url)
        self.assertEqual(len(files), 2)
        self.assertIn(f"{series_url}21101-g00.zip", files)
        self.assertIn(f"{series_url}21905-g00.zip", files)

    @patch('src.main.requests.get')
    def test_download_file(self, mock_get):
        """Test downloading a single file."""
        file_url = f"{self.base_url}/21-series/21101-g00.zip"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'file content']
        mock_get.return_value = mock_response

        state = {"downloaded_files": []}
        download_file(file_url, state)

        series_dir = Path(self.download_dir) / "21-series"
        filepath = series_dir / "21101-g00.zip"
        
        self.assertTrue(filepath.exists())
        with open(filepath, 'rb') as f:
            self.assertEqual(f.read(), b'file content')
        
        self.assertIn(str(filepath), state["downloaded_files"])

    def test_save_and_load_state(self):
        """Test saving and loading the download state."""
        state = {"downloaded_files": ["path/to/file1.zip", "path/to/file2.zip"]}
        save_state(state)
        
        loaded_state = load_state()
        self.assertEqual(state, loaded_state)

if __name__ == '__main__':
    unittest.main()
