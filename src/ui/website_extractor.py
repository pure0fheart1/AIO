from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTextEdit, QProgressBar,
                            QCheckBox, QGroupBox, QFileDialog, QMessageBox,
                            QListWidget, QComboBox, QTabWidget, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QFont
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class ExtractorThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, url, options):
        super().__init__()
        self.url = url
        self.options = options
        self.save_dir = options.get('save_dir', '')
        self.extract_images = options.get('extract_images', True)
        self.extract_text = options.get('extract_text', True)
        self.extract_links = options.get('extract_links', True)
        self.extract_videos = options.get('extract_videos', True)
        self.extract_files = options.get('extract_files', True)
        self.download_content = options.get('download_content', False)
        self.max_depth = options.get('max_depth', 0)
        
    def run(self):
        try:
            self.results = {
                'images': [],
                'videos': [],
                'links': [],
                'files': [],
                'text': '',
                'title': ''
            }
            
            self.visited = set()
            self.extract_from_url(self.url, 0)
            
            self.finished_signal.emit(self.results)
        except Exception as e:
            self.error_signal.emit(f"Extraction error: {str(e)}")
    
    def extract_from_url(self, url, depth):
        if url in self.visited or (self.max_depth > 0 and depth > self.max_depth):
            return
        
        self.visited.add(url)
        self.progress_signal.emit(0, f"Processing {url}")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                self.progress_signal.emit(0, f"Failed to access {url}: {response.status_code}")
                return
            
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                # Not HTML, may be a file
                if self.extract_files and self.download_content:
                    filename = os.path.basename(urlparse(url).path) or 'unnamed_file'
                    file_path = os.path.join(self.save_dir, filename)
                    self.save_file(response.content, file_path)
                    self.results['files'].append({'url': url, 'path': file_path})
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            if soup.title:
                self.results['title'] = soup.title.text.strip()
            
            # Extract text
            if self.extract_text:
                self.progress_signal.emit(20, "Extracting text...")
                all_text = soup.get_text(separator=' ', strip=True)
                self.results['text'] += all_text + "\n\n"
            
            # Extract images
            if self.extract_images:
                self.progress_signal.emit(40, "Extracting images...")
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src:
                        img_url = urljoin(url, src)
                        if img_url not in [i['url'] for i in self.results['images']]:
                            img_data = {'url': img_url, 'alt': img.get('alt', ''), 'path': ''}
                            if self.download_content:
                                try:
                                    img_response = requests.get(img_url, timeout=5)
                                    if img_response.status_code == 200:
                                        filename = os.path.basename(urlparse(img_url).path) or f'image_{len(self.results["images"])}.jpg'
                                        file_path = os.path.join(self.save_dir, 'images', filename)
                                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                        self.save_file(img_response.content, file_path)
                                        img_data['path'] = file_path
                                except Exception as e:
                                    self.progress_signal.emit(0, f"Error downloading image {img_url}: {str(e)}")
                            self.results['images'].append(img_data)
            
            # Extract videos
            if self.extract_videos:
                self.progress_signal.emit(60, "Extracting videos...")
                # Find video tags
                for video in soup.find_all('video'):
                    src = video.get('src')
                    if src:
                        video_url = urljoin(url, src)
                        if video_url not in [v['url'] for v in self.results['videos']]:
                            self.results['videos'].append({
                                'url': video_url,
                                'type': 'html5',
                                'path': ''
                            })
                
                # Find YouTube embeds
                youtube_patterns = [
                    r'(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+',
                    r'(https?:\/\/)?(www\.)?vimeo\.com\/.+'
                ]
                
                for iframe in soup.find_all('iframe'):
                    src = iframe.get('src', '')
                    for pattern in youtube_patterns:
                        if re.match(pattern, src):
                            if src not in [v['url'] for v in self.results['videos']]:
                                self.results['videos'].append({
                                    'url': src,
                                    'type': 'embed',
                                    'path': ''
                                })
            
            # Extract links and potentially follow them
            if self.extract_links:
                self.progress_signal.emit(80, "Extracting links...")
                for a_tag in soup.find_all('a'):
                    href = a_tag.get('href')
                    if href:
                        link_url = urljoin(url, href)
                        if link_url not in [l['url'] for l in self.results['links']]:
                            parsed_url = urlparse(link_url)
                            if parsed_url.scheme in ('http', 'https'):
                                self.results['links'].append({
                                    'url': link_url,
                                    'text': a_tag.get_text(strip=True),
                                    'title': a_tag.get('title', '')
                                })
                                
                                # For document/file links
                                ext = os.path.splitext(parsed_url.path)[1].lower()
                                if self.extract_files and ext in ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar'):
                                    if link_url not in [f['url'] for f in self.results['files']]:
                                        file_data = {'url': link_url, 'type': ext[1:], 'path': ''}
                                        if self.download_content:
                                            try:
                                                file_response = requests.get(link_url, timeout=10)
                                                if file_response.status_code == 200:
                                                    filename = os.path.basename(parsed_url.path) or f'file_{len(self.results["files"])}{ext}'
                                                    file_path = os.path.join(self.save_dir, 'files', filename)
                                                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                                    self.save_file(file_response.content, file_path)
                                                    file_data['path'] = file_path
                                            except Exception as e:
                                                self.progress_signal.emit(0, f"Error downloading file {link_url}: {str(e)}")
                                        self.results['files'].append(file_data)
                                
                                # Follow link if recursion is enabled
                                if self.max_depth > 0 and depth < self.max_depth:
                                    # Only follow links within the same domain
                                    if urlparse(link_url).netloc == urlparse(self.url).netloc:
                                        self.extract_from_url(link_url, depth + 1)
            
            self.progress_signal.emit(100, "Extraction completed")
            
        except Exception as e:
            self.progress_signal.emit(0, f"Error processing {url}: {str(e)}")
    
    def save_file(self, content, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)

class WebsiteExtractor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.save_directory = os.path.expanduser("~/Downloads/WebsiteExtractor")
        self.extracted_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Website Extractor")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(header)
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Options group
        options_group = QGroupBox("Extraction Options")
        options_layout = QVBoxLayout(options_group)
        
        # Checkboxes for different content types
        self.extract_images_cb = QCheckBox("Extract Images")
        self.extract_images_cb.setChecked(True)
        
        self.extract_text_cb = QCheckBox("Extract Text")
        self.extract_text_cb.setChecked(True)
        
        self.extract_links_cb = QCheckBox("Extract Links")
        self.extract_links_cb.setChecked(True)
        
        self.extract_videos_cb = QCheckBox("Extract Videos")
        self.extract_videos_cb.setChecked(True)
        
        self.extract_files_cb = QCheckBox("Extract Files")
        self.extract_files_cb.setChecked(True)
        
        self.download_content_cb = QCheckBox("Download Content")
        self.download_content_cb.setChecked(False)
        
        options_layout.addWidget(self.extract_images_cb)
        options_layout.addWidget(self.extract_text_cb)
        options_layout.addWidget(self.extract_links_cb)
        options_layout.addWidget(self.extract_videos_cb)
        options_layout.addWidget(self.extract_files_cb)
        options_layout.addWidget(self.download_content_cb)
        
        # Recursion depth
        depth_layout = QHBoxLayout()
        depth_label = QLabel("Recursion Depth:")
        self.depth_spinner = QSpinBox()
        self.depth_spinner.setMinimum(0)
        self.depth_spinner.setMaximum(3)  # Limit to prevent excessive crawling
        self.depth_spinner.setValue(0)
        self.depth_spinner.setToolTip("0 = Only extract from the URL\n1 = Follow links one level deep\n2+ = Follow links deeper")
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_spinner)
        options_layout.addLayout(depth_layout)
        
        # Save directory selection
        save_dir_layout = QHBoxLayout()
        save_dir_label = QLabel("Save Directory:")
        self.save_dir_input = QLineEdit(self.save_directory)
        self.save_dir_input.setReadOnly(True)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.select_save_directory)
        save_dir_layout.addWidget(save_dir_label)
        save_dir_layout.addWidget(self.save_dir_input)
        save_dir_layout.addWidget(browse_button)
        options_layout.addLayout(save_dir_layout)
        
        layout.addWidget(options_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.extract_button = QPushButton("Extract Content")
        self.extract_button.clicked.connect(self.start_extraction)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_extraction)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        
        # Text results
        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.results_tabs.addTab(self.text_result, "Text")
        
        # Image results
        self.images_list = QListWidget()
        self.results_tabs.addTab(self.images_list, "Images")
        
        # Video results
        self.videos_list = QListWidget()
        self.results_tabs.addTab(self.videos_list, "Videos")
        
        # Link results
        self.links_list = QListWidget()
        self.results_tabs.addTab(self.links_list, "Links")
        
        # File results
        self.files_list = QListWidget()
        self.results_tabs.addTab(self.files_list, "Files")
        
        layout.addWidget(self.results_tabs)
        
    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.save_directory,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.save_directory = directory
            self.save_dir_input.setText(directory)
            
    def start_extraction(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
            
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_input.setText(url)
        
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                QMessageBox.warning(self, "Error", "Invalid URL")
                return
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid URL")
            return
            
        # Clear previous results
        self.text_result.clear()
        self.images_list.clear()
        self.videos_list.clear()
        self.links_list.clear()
        self.files_list.clear()
        self.extracted_data = {}
        
        # Get options
        options = {
            'save_dir': self.save_directory,
            'extract_images': self.extract_images_cb.isChecked(),
            'extract_text': self.extract_text_cb.isChecked(),
            'extract_links': self.extract_links_cb.isChecked(),
            'extract_videos': self.extract_videos_cb.isChecked(),
            'extract_files': self.extract_files_cb.isChecked(),
            'download_content': self.download_content_cb.isChecked(),
            'max_depth': self.depth_spinner.value()
        }
        
        # Create directory if downloading content
        if options['download_content']:
            os.makedirs(self.save_directory, exist_ok=True)
            os.makedirs(os.path.join(self.save_directory, 'images'), exist_ok=True)
            os.makedirs(os.path.join(self.save_directory, 'files'), exist_ok=True)
        
        # Start extraction thread
        self.extractor_thread = ExtractorThread(url, options)
        self.extractor_thread.progress_signal.connect(self.update_progress)
        self.extractor_thread.finished_signal.connect(self.extraction_finished)
        self.extractor_thread.error_signal.connect(self.extraction_error)
        
        self.extractor_thread.start()
        
        # Update UI
        self.extract_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("Extracting content...")
        
    def cancel_extraction(self):
        if hasattr(self, 'extractor_thread') and self.extractor_thread.isRunning():
            self.extractor_thread.terminate()
            self.status_label.setText("Extraction cancelled")
            self.progress_bar.setValue(0)
            self.extract_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def extraction_finished(self, results):
        self.extracted_data = results
        self.display_results()
        
        self.extract_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Extraction completed")
        
        if self.parent:
            self.parent.statusBar().showMessage("Website extraction completed", 3000)
            
    def extraction_error(self, error_message):
        QMessageBox.warning(self, "Extraction Error", error_message)
        self.status_label.setText("Extraction failed")
        self.progress_bar.setValue(0)
        self.extract_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
    def display_results(self):
        # Display text
        if self.extracted_data.get('title'):
            self.text_result.setPlainText(f"Title: {self.extracted_data['title']}\n\n")
        self.text_result.append(self.extracted_data.get('text', ''))
        
        # Display images
        for img in self.extracted_data.get('images', []):
            item_text = f"{img['url']}"
            if img['alt']:
                item_text += f" (Alt: {img['alt']})"
            if img['path']:
                item_text += f" [Saved to: {img['path']}]"
            self.images_list.addItem(item_text)
            
        # Display videos
        for video in self.extracted_data.get('videos', []):
            item_text = f"{video['url']} (Type: {video['type']})"
            if video['path']:
                item_text += f" [Saved to: {video['path']}]"
            self.videos_list.addItem(item_text)
            
        # Display links
        for link in self.extracted_data.get('links', []):
            item_text = f"{link['url']}"
            if link['text']:
                item_text += f" (Text: {link['text']})"
            if link['title']:
                item_text += f" [Title: {link['title']}]"
            self.links_list.addItem(item_text)
            
        # Display files
        for file in self.extracted_data.get('files', []):
            item_text = f"{file['url']}"
            if 'type' in file:
                item_text += f" (Type: {file['type']})"
            if file['path']:
                item_text += f" [Saved to: {file['path']}]"
            self.files_list.addItem(item_text)
            
        # Update tab counts
        self.results_tabs.setTabText(0, f"Text ({len(self.extracted_data.get('text', '').split())} words)")
        self.results_tabs.setTabText(1, f"Images ({len(self.extracted_data.get('images', []))})")
        self.results_tabs.setTabText(2, f"Videos ({len(self.extracted_data.get('videos', []))})")
        self.results_tabs.setTabText(3, f"Links ({len(self.extracted_data.get('links', []))})")
        self.results_tabs.setTabText(4, f"Files ({len(self.extracted_data.get('files', []))})") 