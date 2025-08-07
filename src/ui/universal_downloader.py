from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QProgressBar, QComboBox,
                            QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
                            QSpinBox, QCheckBox, QGroupBox, QFormLayout, QTabWidget,
                            QPlainTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
import os
import time
import re
from datetime import datetime

class DownloadWorker(QThread):
    progress = pyqtSignal(float, str)
    finished = pyqtSignal(bool, str)
    info_updated = pyqtSignal(dict)
    log_message = pyqtSignal(str)

    def __init__(self, url, save_path, format_id="best", extract_audio=False, cookies=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.format_id = format_id
        self.extract_audio = extract_audio
        self.is_cancelled = False
        self.cookies = cookies

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Calculate progress
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
            
            # Emit progress with speed
            speed = d.get('speed', 0)
            if speed:
                speed_str = f"{speed/1024/1024:.1f} MB/s"
            else:
                speed_str = "-- MB/s"
            
            self.progress.emit(percent, speed_str)
            
    def debug_hook(self, message):
        self.log_message.emit(message)

    def run(self):
        try:
            # Options for yt-dlp
            ydl_opts = {
                'format': self.format_id if not self.extract_audio else 'bestaudio/best',
                'progress_hooks': [self.progress_hook],
                'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'verbose': True,
                'logger': self
            }

            # Add options for audio extraction
            if self.extract_audio:
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
                
            # Handle cookies for sites requiring authentication
            if self.cookies:
                self.log_message.emit("Using provided cookies for authentication")
                ydl_opts['cookiesfrombrowser'] = ('chrome',)
                
            # Special handling for Facebook URLs
            if 'facebook.com' in self.url:
                self.log_message.emit("Facebook URL detected, applying special handling")
                ydl_opts.update({
                    'allow_unplayable_formats': True,
                    'skip_download': False,
                    'cookiefile': self.cookies if self.cookies else None,
                    'ignoreerrors': True,
                    'no_warnings': False,
                    'verbose': True,
                    'hls_prefer_native': True,
                    'extract_flat': False,
                    'skip_unavailable_fragments': True,
                    'socket_timeout': 60,
                    'retries': 10,
                    'fragment_retries': 10,
                    'force_generic_extractor': False
                })
                
                # Handle Facebook saved videos page specifically
                if 'saved' in self.url or 'referrer' in self.url:
                    self.log_message.emit("Detected Facebook saved videos page, attempting to extract")
                    # Ensure we're properly handling the URL format
                    new_url = self.url.split('?')[0]  # Remove query parameters that might cause issues
                    self.url = new_url
                    self.log_message.emit(f"Simplified URL to: {self.url}")
                    
                # Try to clean the URL if it contains a login redirect
                if 'login.php' in self.url:
                    self.log_message.emit("Detected Facebook login redirect, attempting to clean URL")
                    # Try to extract the actual URL from redirect parameters
                    if 'next=' in self.url:
                        try:
                            import urllib.parse
                            redirect_part = self.url.split('next=')[1].split('&')[0]
                            actual_url = urllib.parse.unquote(redirect_part)
                            self.url = actual_url
                            self.log_message.emit(f"Extracted actual URL from redirect: {self.url}")
                        except Exception as e:
                            self.log_message.emit(f"Failed to extract URL from redirect: {str(e)}")

            # First get video info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.log_message.emit(f"Extracting info from: {self.url}")
                info = ydl.extract_info(self.url, download=False)
                self.info_updated.emit(info)

                if not self.is_cancelled:
                    # Then download
                    self.log_message.emit("Starting download...")
                    ydl.download([self.url])
                    self.finished.emit(True, "Download completed successfully")
                else:
                    self.finished.emit(False, "Download cancelled")

        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}")
            self.finished.emit(False, str(e))
            
    def debug(self, msg):
        """Log debug messages from yt-dlp"""
        if msg:
            self.log_message.emit(f"DEBUG: {msg}")
            
    def info(self, msg):
        """Log info messages from yt-dlp"""
        if msg:
            self.log_message.emit(f"INFO: {msg}")
            
    def warning(self, msg):
        """Log warning messages from yt-dlp"""
        if msg:
            self.log_message.emit(f"WARNING: {msg}")
            
    def error(self, msg):
        """Log error messages from yt-dlp"""
        if msg:
            self.log_message.emit(f"ERROR: {msg}")

    def cancel(self):
        self.is_cancelled = True

class UniversalDownloader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create tabs
        self.tab_widget = QTabWidget()
        self.main_tab = QWidget()
        self.advanced_tab = QWidget()
        self.log_tab = QWidget()
        
        self.tab_widget.addTab(self.main_tab, "Main")
        self.tab_widget.addTab(self.advanced_tab, "Advanced Options")
        self.tab_widget.addTab(self.log_tab, "Log")
        
        layout.addWidget(self.tab_widget)
        
        # Setup main tab
        self.setup_main_tab()
        
        # Setup advanced tab
        self.setup_advanced_tab()
        
        # Setup log tab
        self.setup_log_tab()

    def setup_main_tab(self):
        layout = QVBoxLayout(self.main_tab)

        # URL input section
        url_group = QGroupBox("Video URL")
        url_layout = QVBoxLayout()

        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL...")
        self.fetch_btn = QPushButton("Fetch Info")
        self.fetch_btn.clicked.connect(self.fetch_video_info)
        
        url_input_layout.addWidget(self.url_input)
        url_input_layout.addWidget(self.fetch_btn)
        url_layout.addLayout(url_input_layout)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # Video info section
        info_group = QGroupBox("Video Information")
        info_layout = QFormLayout()

        self.title_label = QLabel("No video loaded")
        self.duration_label = QLabel("")
        self.format_combo = QComboBox()
        self.format_combo.setEnabled(False)

        info_layout.addRow("Title:", self.title_label)
        info_layout.addRow("Duration:", self.duration_label)
        info_layout.addRow("Format:", self.format_combo)

        # Audio extraction option
        self.audio_only_check = QCheckBox("Extract audio only (MP3)")
        info_layout.addRow(self.audio_only_check)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Download section
        download_group = QGroupBox("Download")
        download_layout = QVBoxLayout()

        # Save location
        save_layout = QHBoxLayout()
        self.save_path_input = QLineEdit()
        self.save_path_input.setReadOnly(True)
        self.save_path_input.setText(os.path.expanduser("~/Downloads"))
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_save_location)
        
        save_layout.addWidget(QLabel("Save to:"))
        save_layout.addWidget(self.save_path_input)
        save_layout.addWidget(browse_btn)
        download_layout.addLayout(save_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        download_layout.addWidget(self.progress_bar)

        # Speed label
        self.speed_label = QLabel("")
        download_layout.addWidget(self.speed_label)

        # Download button
        button_layout = QHBoxLayout()
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.cancel_btn)
        download_layout.addLayout(button_layout)

        download_group.setLayout(download_layout)
        layout.addWidget(download_group)

        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Add stretch to bottom
        layout.addStretch()
        
    def setup_advanced_tab(self):
        layout = QVBoxLayout(self.advanced_tab)
        
        # Facebook authentication section
        fb_group = QGroupBox("Facebook Authentication")
        fb_layout = QVBoxLayout()
        
        fb_info_label = QLabel("For Facebook videos, you may need to provide authentication cookies.")
        fb_info_label.setWordWrap(True)
        fb_layout.addWidget(fb_info_label)
        
        # Cookie file
        cookie_layout = QHBoxLayout()
        self.cookie_path_input = QLineEdit()
        self.cookie_path_input.setPlaceholderText("Path to cookies file (optional)")
        self.cookie_browse_btn = QPushButton("Browse")
        self.cookie_browse_btn.clicked.connect(self.browse_cookies_file)
        
        cookie_layout.addWidget(QLabel("Cookies:"))
        cookie_layout.addWidget(self.cookie_path_input)
        cookie_layout.addWidget(self.cookie_browse_btn)
        fb_layout.addLayout(cookie_layout)
        
        # Button to extract a Facebook saved videos page
        fb_batch_layout = QHBoxLayout()
        self.fb_url_input = QLineEdit()
        self.fb_url_input.setPlaceholderText("Enter Facebook saved videos URL")
        self.fb_extract_btn = QPushButton("Extract All Videos")
        self.fb_extract_btn.clicked.connect(self.extract_facebook_videos)
        
        fb_batch_layout.addWidget(QLabel("Saved Videos URL:"))
        fb_batch_layout.addWidget(self.fb_url_input)
        fb_batch_layout.addWidget(self.fb_extract_btn)
        fb_layout.addLayout(fb_batch_layout)
        
        fb_group.setLayout(fb_layout)
        layout.addWidget(fb_group)
        
        # General advanced options
        adv_group = QGroupBox("Other Options")
        adv_layout = QVBoxLayout()
        
        # Format options
        self.format_options_input = QLineEdit()
        self.format_options_input.setPlaceholderText("Custom format options (advanced)")
        adv_layout.addWidget(QLabel("Custom Format:"))
        adv_layout.addWidget(self.format_options_input)
        
        # Add more advanced options as needed
        
        adv_group.setLayout(adv_layout)
        layout.addWidget(adv_group)
        
        # Help text
        help_text = QLabel(
            "Tips:\n"
            "- For Facebook videos, you need to be logged in to download some content\n"
            "- To download a whole page of saved videos, use the Saved Videos URL field\n"
            "- Make sure to have ffmpeg installed for audio conversion\n"
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        layout.addStretch()
        
    def setup_log_tab(self):
        layout = QVBoxLayout(self.log_tab)
        
        # Log text area
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Clear log button
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        layout.addWidget(self.log_text)
        layout.addWidget(self.clear_log_btn)
        
    def clear_log(self):
        self.log_text.clear()
        
    def log(self, message):
        self.log_text.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def browse_cookies_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookies File",
            os.path.expanduser("~"),
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookie_path_input.setText(file_path)
            self.log(f"Cookies file selected: {file_path}")

    def browse_save_location(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Save Location",
            self.save_path_input.text(),
            QFileDialog.ShowDirsOnly
        )
        if dir_path:
            self.save_path_input.setText(dir_path)
            self.log(f"Save location set to: {dir_path}")

    def fetch_video_info(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a video URL")
            return

        self.fetch_btn.setEnabled(False)
        self.status_label.setText("Fetching video information...")
        self.log(f"Fetching information for: {url}")
        
        # Create worker for fetching info
        self.current_worker = DownloadWorker(
            url, 
            self.save_path_input.text(), 
            cookies=self.cookie_path_input.text() if self.cookie_path_input.text() else None
        )
        self.current_worker.info_updated.connect(self.update_video_info)
        self.current_worker.finished.connect(self.on_fetch_finished)
        self.current_worker.log_message.connect(self.log)
        self.current_worker.start()
        
        # Switch to log tab
        self.tab_widget.setCurrentIndex(2)  # Index of log tab

    def update_video_info(self, info):
        # Update title and duration
        self.title_label.setText(info.get('title', 'Unknown'))
        duration = info.get('duration')
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            self.duration_label.setText(f"{minutes}:{seconds:02d}")

        # Update available formats
        self.format_combo.clear()
        
        # Add default best quality option
        self.format_combo.addItem("Best Quality (automatic)", "best")
        
        formats = info.get('formats', [])
        if formats:
            self.log(f"Found {len(formats)} available formats")
            
            # Add video+audio formats
            for f in formats:
                if f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none':
                    format_str = f"{f.get('format_note', 'unknown')} - {f.get('ext', 'unknown')}"
                    if f.get('filesize'):
                        format_str += f" ({f['filesize']/1024/1024:.1f} MB)"
                    self.format_combo.addItem(format_str, f['format_id'])
        else:
            self.log("No detailed format information available")

        self.format_combo.setEnabled(True)
        self.download_btn.setEnabled(True)
        
        # Switch back to main tab
        self.tab_widget.setCurrentIndex(0)

    def on_fetch_finished(self, success, message):
        self.fetch_btn.setEnabled(True)
        if not success:
            self.log(f"Error: {message}")
            QMessageBox.warning(self, "Error", f"Could not fetch video info: {message}")
            self.status_label.setText("Error fetching video information")
        else:
            self.status_label.setText("Ready to download")
            self.log("Video information fetched successfully")

    def start_download(self):
        url = self.url_input.text().strip()
        save_path = self.save_path_input.text()
        
        # Use custom format if provided, otherwise use selected format
        if self.format_options_input.text():
            format_id = self.format_options_input.text()
            self.log(f"Using custom format: {format_id}")
        else:
            format_id = self.format_combo.currentData()
            self.log(f"Using format: {format_id}")

        self.current_worker = DownloadWorker(
            url, save_path, format_id, 
            extract_audio=self.audio_only_check.isChecked(),
            cookies=self.cookie_path_input.text() if self.cookie_path_input.text() else None
        )
        self.current_worker.progress.connect(self.update_progress)
        self.current_worker.finished.connect(self.on_download_finished)
        self.current_worker.log_message.connect(self.log)
        self.current_worker.start()

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Downloading...")
        self.log("Download started")
        
        # Switch to log tab
        self.tab_widget.setCurrentIndex(2)

    def update_progress(self, percent, speed):
        self.progress_bar.setValue(int(percent))
        self.speed_label.setText(f"Download speed: {speed}")

    def on_download_finished(self, success, message):
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.speed_label.setText("")

        if success:
            self.log("Download completed successfully")
            self.status_label.setText("Download completed successfully")
            if self.parent:
                self.parent.statusBar().showMessage("Download completed successfully")
        else:
            self.log(f"Download failed: {message}")
            self.status_label.setText(f"Download failed: {message}")
            QMessageBox.warning(self, "Error", f"Download failed: {message}")

    def cancel_download(self):
        if self.current_worker:
            self.current_worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status_label.setText("Cancelling download...")
            self.log("Download cancelled by user")
            
    def extract_facebook_videos(self):
        url = self.fb_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a Facebook saved videos URL")
            return
            
        if not url.startswith("https://www.facebook.com"):
            QMessageBox.warning(self, "Error", "Please enter a valid Facebook URL")
            return
            
        if not self.cookie_path_input.text():
            reply = QMessageBox.question(
                self, 
                "Authentication Required",
                "Facebook usually requires authentication to access saved videos. Continue without cookies?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # Set the URL in the main input and start fetch
        self.url_input.setText(url)
        self.fetch_video_info()
        self.log("Attempting to extract all videos from Facebook page") 