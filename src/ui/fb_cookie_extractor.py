import os
import sys
import json
import sqlite3
import shutil
import browser_cookie3
import tempfile
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog,
                            QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class CookieExtractorThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, str)  # success, message, output_path
    
    def __init__(self, browser_name, output_path):
        super().__init__()
        self.browser_name = browser_name
        self.output_path = output_path
        
    def run(self):
        try:
            self.progress.emit(10, "Starting cookie extraction...")
            
            # Extract cookies based on browser selection
            if self.browser_name == "chrome":
                self.progress.emit(30, "Extracting from Chrome...")
                cookies = browser_cookie3.chrome(domain_name=".facebook.com")
            elif self.browser_name == "firefox":
                self.progress.emit(30, "Extracting from Firefox...")
                cookies = browser_cookie3.firefox(domain_name=".facebook.com")
            elif self.browser_name == "edge":
                self.progress.emit(30, "Extracting from Edge...")
                cookies = browser_cookie3.edge(domain_name=".facebook.com")
            elif self.browser_name == "safari":
                self.progress.emit(30, "Extracting from Safari...")
                cookies = browser_cookie3.safari(domain_name=".facebook.com")
            elif self.browser_name == "opera":
                self.progress.emit(30, "Extracting from Opera...")
                cookies = browser_cookie3.opera(domain_name=".facebook.com")
            elif self.browser_name == "brave":
                self.progress.emit(30, "Extracting from Brave...")
                cookies = browser_cookie3.brave(domain_name=".facebook.com")
            else:
                raise ValueError(f"Unsupported browser: {self.browser_name}")
            
            self.progress.emit(50, "Processing cookies...")
            
            # Format cookies for yt-dlp
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie.name] = cookie.value
                
            # Check if we found any Facebook cookies
            if not cookie_dict:
                self.finished.emit(False, "No Facebook cookies found. Are you logged in to Facebook in this browser?", "")
                return
                
            self.progress.emit(70, f"Found {len(cookie_dict)} Facebook cookies")
            
            # Create netscape format cookies file
            with open(self.output_path, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for cookie in cookies:
                    if cookie.domain.endswith(".facebook.com") or cookie.domain == ".facebook.com":
                        secure = "TRUE" if cookie.secure else "FALSE"
                        http_only = "TRUE" if cookie.has_nonstandard_attr("HttpOnly") else "FALSE"
                        expires = int(cookie.expires) if cookie.expires else 0
                        
                        f.write(f"{cookie.domain}\t"
                                f"{'TRUE'}\t"  # domain_specified
                                f"{cookie.path}\t"
                                f"{secure}\t"
                                f"{expires}\t"
                                f"{cookie.name}\t"
                                f"{cookie.value}\n")
            
            self.progress.emit(100, "Cookies exported successfully!")
            self.finished.emit(True, f"Successfully exported {len(cookie_dict)} Facebook cookies", self.output_path)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f"Error extracting cookies: {str(e)}", "")

class FacebookCookieExtractor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Facebook Cookie Extractor")
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Explanation
        info_label = QLabel(
            "This tool extracts your Facebook cookies from your browser to allow downloading Facebook videos.\n\n"
            "You must be logged in to Facebook in your browser for this to work.\n"
            "Your cookies will be saved to a file that you can select in the Universal Downloader."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Browser selection
        browser_layout = QHBoxLayout()
        browser_layout.addWidget(QLabel("Select Browser:"))
        
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge", "Safari", "Opera", "Brave"])
        browser_layout.addWidget(self.browser_combo)
        
        layout.addLayout(browser_layout)
        
        # Output file selection
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Save to:"))
        
        self.output_path = QLineEdit()
        default_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "facebook_cookies.txt")
        self.output_path.setText(default_path)
        output_layout.addWidget(self.output_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_output_location)
        output_layout.addWidget(browse_btn)
        
        layout.addLayout(output_layout)
        
        # Progress info
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.extract_btn = QPushButton("Extract Cookies")
        self.extract_btn.clicked.connect(self.extract_cookies)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.extract_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def browse_output_location(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Cookies File",
            self.output_path.text(),
            "Text Files (*.txt)"
        )
        if file_path:
            self.output_path.setText(file_path)
            
    def extract_cookies(self):
        browser_name = self.browser_combo.currentText().lower()
        output_path = self.output_path.text()
        
        if not output_path:
            QMessageBox.warning(self, "Error", "Please specify an output file location")
            return
            
        # Disable UI during extraction
        self.extract_btn.setEnabled(False)
        self.browser_combo.setEnabled(False)
        self.output_path.setEnabled(False)
        
        # Start extraction thread
        self.extractor = CookieExtractorThread(browser_name, output_path)
        self.extractor.progress.connect(self.update_progress)
        self.extractor.finished.connect(self.on_extraction_finished)
        self.extractor.start()
        
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def on_extraction_finished(self, success, message, output_path):
        # Re-enable UI
        self.extract_btn.setEnabled(True)
        self.browser_combo.setEnabled(True)
        self.output_path.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, 
                "Success", 
                f"{message}\n\nCookies saved to: {output_path}\n\nYou can now use this file in the Universal Downloader"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    window = FacebookCookieExtractor()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 