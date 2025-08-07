import os
import sys
import time
import json
import re
import tempfile
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QLineEdit, QProgressBar, 
                            QCheckBox, QMessageBox, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class FacebookVideoExtractorThread(QThread):
    """Thread to extract Facebook video URLs using browser automation"""
    
    progress = pyqtSignal(int, str)
    video_found = pyqtSignal(str, str)  # url, title
    log_message = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, url, cookie_file=None, max_videos=10):
        super().__init__()
        self.url = url
        self.cookie_file = cookie_file
        self.max_videos = max_videos
        self.driver = None
        self.abort = False
        
    def run(self):
        try:
            self.log_message.emit("Starting Facebook video extraction process")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            
            # Install and setup Chrome driver
            self.log_message.emit("Setting up Chrome driver")
            self.progress.emit(10, "Setting up browser...")
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Load cookies if available
            if self.cookie_file and os.path.exists(self.cookie_file):
                self.log_message.emit(f"Loading cookies from {self.cookie_file}")
                self.driver.get("https://www.facebook.com")
                
                # Parse and add cookies
                self._add_cookies_to_driver()
                self.log_message.emit("Cookies loaded")
            
            # Navigate to the URL
            self.log_message.emit(f"Navigating to {self.url}")
            self.progress.emit(20, "Accessing Facebook...")
            self.driver.get(self.url)
            time.sleep(3)  # Wait for page to load
            
            # Check if redirected to login page
            if "login" in self.driver.current_url:
                self.log_message.emit("Redirected to login page. Please ensure your cookies are valid")
                self.finished.emit(False, "Login required. Please use the Facebook Cookie Extractor first")
                self.driver.quit()
                return
                
            # Wait for content to load
            self.log_message.emit("Waiting for content to load")
            self.progress.emit(30, "Waiting for content...")
            time.sleep(2)
            
            # Extract videos
            self.log_message.emit("Extracting video information")
            video_count = self._extract_videos()
            
            if video_count == 0:
                self.log_message.emit("No videos found on the page")
                self.finished.emit(False, "No videos found on the page")
            else:
                self.log_message.emit(f"Successfully extracted {video_count} videos")
                self.finished.emit(True, f"Found {video_count} videos")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log_message.emit(f"Error during extraction: {str(e)}")
            self.finished.emit(False, f"Error: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                
    def _add_cookies_to_driver(self):
        """Add cookies from the cookie file to the WebDriver"""
        try:
            # Read Netscape format cookies file
            with open(self.cookie_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if line.startswith('#') or not line.strip():
                    continue
                    
                try:
                    fields = line.strip().split('\t')
                    if len(fields) >= 7:
                        domain, _, path, secure, expires, name, value = fields[:7]
                        
                        cookie = {
                            'domain': domain,
                            'path': path,
                            'secure': secure.lower() == 'true',
                            'expiry': int(expires) if expires != '0' else None,
                            'name': name,
                            'value': value
                        }
                        
                        self.driver.add_cookie(cookie)
                except Exception as e:
                    self.log_message.emit(f"Error adding cookie: {str(e)}")
                    
        except Exception as e:
            self.log_message.emit(f"Error loading cookies: {str(e)}")
    
    def _extract_videos(self):
        """Extract videos from the Facebook page"""
        video_count = 0
        
        try:
            # Scroll down to load more content
            self.log_message.emit("Scrolling to load more content")
            self.progress.emit(40, "Loading videos...")
            
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_attempts = 5  # Limit scrolling to prevent infinite loops
            
            while scroll_attempts < max_attempts and video_count < self.max_videos:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                # Check if we've reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
                
                # Extract current videos
                current_videos = self._find_videos_in_page()
                video_count = len(current_videos)
                
                self.progress.emit(40 + (scroll_attempts * 10), f"Found {video_count} videos...")
                
                # Check if we've found enough videos
                if video_count >= self.max_videos:
                    break
                
            # Final extraction after scrolling
            videos = self._find_videos_in_page()
            video_count = len(videos)
            
            self.progress.emit(90, f"Processing {video_count} videos...")
            self.log_message.emit(f"Found {video_count} videos")
            
            # Emit each video URL
            for idx, (url, title) in enumerate(videos):
                if self.abort:
                    break
                    
                self.video_found.emit(url, title)
                self.progress.emit(90 + (idx * 10 // video_count), f"Processed {idx+1}/{video_count} videos")
                
            return video_count
            
        except Exception as e:
            self.log_message.emit(f"Error during video extraction: {str(e)}")
            return video_count
            
    def _find_videos_in_page(self):
        """Find video elements in the current page"""
        videos = []
        
        try:
            # Get page source and parse with BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for video links - this will need to be adjusted based on Facebook's structure
            # Find video containers
            video_elements = soup.find_all('a', href=re.compile(r'facebook\.com\/.*\/videos\/'))
            
            for elem in video_elements:
                try:
                    url = elem.get('href')
                    # Make sure it's an absolute URL
                    if url and not url.startswith('http'):
                        url = f"https://www.facebook.com{url}"
                        
                    # Try to find a title
                    title_elem = elem.find('span', {'class': lambda x: x and 'ytreact' in x})
                    title = title_elem.text if title_elem else f"Facebook Video {len(videos) + 1}"
                    
                    # Only add if we don't already have this URL
                    if url and (url, title) not in videos:
                        videos.append((url, title))
                        self.log_message.emit(f"Found video: {title}")
                except Exception as e:
                    self.log_message.emit(f"Error processing video element: {str(e)}")
                    
            # Also look for standard video elements
            direct_videos = soup.find_all('div', {'data-pagelet': re.compile(r'VideoChatHome.*')})
            for video_div in direct_videos:
                try:
                    # Try to find the URL
                    link = video_div.find('a', href=re.compile(r'\/videos\/'))
                    if link and link.get('href'):
                        url = link.get('href')
                        if not url.startswith('http'):
                            url = f"https://www.facebook.com{url}"
                            
                        # Try to find title
                        title_elem = video_div.find('span', {'class': 'x193iq5w'})
                        title = title_elem.text if title_elem else f"Facebook Video {len(videos) + 1}"
                        
                        if url and (url, title) not in videos:
                            videos.append((url, title))
                            self.log_message.emit(f"Found video: {title}")
                except Exception as e:
                    self.log_message.emit(f"Error processing direct video: {str(e)}")
                    
            # Deduplicate videos
            unique_videos = []
            seen_urls = set()
            
            for url, title in videos:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_videos.append((url, title))
                    
            return unique_videos
                    
        except Exception as e:
            self.log_message.emit(f"Error finding videos: {str(e)}")
            return []
            
    def stop(self):
        """Stop the extraction process"""
        self.abort = True
        self.log_message.emit("Stopping extraction...")

class FacebookVideoExtractor(QDialog):
    """Dialog to extract Facebook videos using browser automation"""
    
    videos_extracted = pyqtSignal(list)  # List of (url, title) tuples
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Facebook Video Extractor")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.extractor_thread = None
        self.extracted_videos = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Description
        description = QLabel(
            "This tool extracts videos from Facebook using browser automation.\n"
            "You must provide cookies from a logged-in Facebook session.\n"
            "The extractor will navigate to the URL and extract all videos it can find."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Facebook URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.facebook.com/saved/...")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Cookie file selection
        cookie_layout = QHBoxLayout()
        cookie_layout.addWidget(QLabel("Cookie File:"))
        self.cookie_path = QLineEdit()
        self.cookie_path.setReadOnly(True)
        self.cookie_path.setPlaceholderText("No cookie file selected")
        cookie_layout.addWidget(self.cookie_path)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_cookie_file)
        cookie_layout.addWidget(self.browse_button)
        
        layout.addLayout(cookie_layout)
        
        # Maximum videos
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Videos:"))
        
        self.max_videos = QComboBox()
        self.max_videos.addItems(["10", "20", "50", "100", "All"])
        max_layout.addWidget(self.max_videos)
        
        layout.addLayout(max_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Log viewer
        layout.addWidget(QLabel("Log:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.NoWrap)
        self.log_view.setMinimumHeight(200)
        layout.addWidget(self.log_view)
        
        # Extracted videos count
        self.videos_label = QLabel("No videos extracted yet")
        layout.addWidget(self.videos_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.extract_button = QPushButton("Extract Videos")
        self.extract_button.clicked.connect(self.start_extraction)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_extraction)
        self.stop_button.setEnabled(False)
        
        self.import_button = QPushButton("Import Selected")
        self.import_button.clicked.connect(self.import_videos)
        self.import_button.setEnabled(False)
        
        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.import_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def browse_cookie_file(self):
        """Open a file dialog to select the cookie file"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookie File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.cookie_path.setText(file_path)
            self.log(f"Selected cookie file: {file_path}")
            
    def log(self, message):
        """Add a message to the log view"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{timestamp}] {message}")
        # Scroll to the bottom
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )
        
    def start_extraction(self):
        """Start the video extraction process"""
        url = self.url_input.text().strip()
        cookie_file = self.cookie_path.text()
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a Facebook URL")
            return
            
        if not url.startswith("https://www.facebook.com"):
            QMessageBox.warning(self, "Error", "Please enter a valid Facebook URL")
            return
            
        if not cookie_file:
            reply = QMessageBox.question(
                self,
                "No Cookies",
                "You haven't selected a cookie file. Facebook login will likely be required.\nContinue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # Get max videos
        max_videos_text = self.max_videos.currentText()
        if max_videos_text == "All":
            max_videos = 999999
        else:
            max_videos = int(max_videos_text)
            
        # Clear previous results
        self.extracted_videos = []
        self.videos_label.setText("No videos extracted yet")
        self.import_button.setEnabled(False)
        
        # Update UI
        self.extract_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Extracting videos...")
        
        # Start extraction thread
        self.log(f"Starting extraction from: {url}")
        self.extractor_thread = FacebookVideoExtractorThread(url, cookie_file, max_videos)
        self.extractor_thread.progress.connect(self.update_progress)
        self.extractor_thread.log_message.connect(self.log)
        self.extractor_thread.video_found.connect(self.add_video)
        self.extractor_thread.finished.connect(self.extraction_finished)
        self.extractor_thread.start()
        
    def stop_extraction(self):
        """Stop the extraction process"""
        if self.extractor_thread and self.extractor_thread.isRunning():
            self.extractor_thread.stop()
            self.log("Stopping extraction process...")
            self.status_label.setText("Stopping...")
            
    def update_progress(self, value, message):
        """Update the progress bar and status message"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def add_video(self, url, title):
        """Add an extracted video to the list"""
        self.extracted_videos.append((url, title))
        self.videos_label.setText(f"Found {len(self.extracted_videos)} videos")
        
    def extraction_finished(self, success, message):
        """Handle completion of the extraction process"""
        # Update UI
        self.extract_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if success:
            self.status_label.setText(f"Extraction complete: {message}")
            if self.extracted_videos:
                self.import_button.setEnabled(True)
            self.log(f"Extraction completed successfully: {len(self.extracted_videos)} videos found")
        else:
            self.status_label.setText(f"Extraction failed: {message}")
            self.log(f"Extraction failed: {message}")
            
    def import_videos(self):
        """Import the extracted videos to the main application"""
        if not self.extracted_videos:
            QMessageBox.information(self, "No Videos", "No videos to import")
            return
            
        # Emit the signal with the extracted videos
        self.videos_extracted.emit(self.extracted_videos)
        self.log(f"Imported {len(self.extracted_videos)} videos to downloader")
        
        # Close the dialog
        self.accept()
            
def main():
    app = QApplication(sys.argv)
    window = FacebookVideoExtractor()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main() 