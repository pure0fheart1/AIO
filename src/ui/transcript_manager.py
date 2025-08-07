from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                            QTextEdit, QSplitter, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import os
import json
from datetime import datetime

class TranscriptItem(QListWidgetItem):
    def __init__(self, title, file_path, date=None, parent=None):
        super().__init__(title, parent)
        self.file_path = file_path
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.setData(Qt.UserRole, {
            "file_path": file_path,
            "date": self.date
        })
        self.updateDisplay()
        
    def updateDisplay(self):
        # Show title and date in the list
        self.setText(f"{self.text()} ({self.date})")

class TranscriptManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.transcripts_directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Transcripts")
        os.makedirs(self.transcripts_directory, exist_ok=True)
        self.setup_ui()
        self.load_transcripts()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header with search
        header_layout = QHBoxLayout()
        header_label = QLabel("Video Transcripts")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search transcripts...")
        self.search_input.textChanged.connect(self.filter_transcripts)
        
        header_layout.addWidget(header_label)
        header_layout.addWidget(self.search_input)
        
        # Splitter for transcript list and content
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Transcript list
        self.transcripts_list = QListWidget()
        self.transcripts_list.itemClicked.connect(self.load_transcript_content)
        self.transcripts_list.setMinimumWidth(300)
        
        # Transcript content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_transcript)
        self.export_button.setEnabled(False)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_transcript)
        self.delete_button.setEnabled(False)
        
        actions_layout.addWidget(self.export_button)
        actions_layout.addWidget(self.delete_button)
        
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.content_display)
        content_layout.addLayout(actions_layout)
        
        # Add widgets to splitter
        self.splitter.addWidget(self.transcripts_list)
        self.splitter.addWidget(content_widget)
        
        # Set splitter size ratio
        self.splitter.setSizes([1, 2])
        
        # Add everything to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.splitter)
        
        self.setLayout(layout)
        
    def load_transcripts(self):
        self.transcripts_list.clear()
        
        if os.path.exists(self.transcripts_directory):
            transcript_files = [f for f in os.listdir(self.transcripts_directory) 
                              if f.endswith('_transcript.docx')]
            
            # Sort files by modification time (newest first)
            transcript_files.sort(key=lambda x: os.path.getmtime(
                os.path.join(self.transcripts_directory, x)), reverse=True)
            
            for file_name in transcript_files:
                file_path = os.path.join(self.transcripts_directory, file_name)
                title = file_name.replace('_transcript.docx', '').replace('_', ' ')
                date = datetime.fromtimestamp(
                    os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                
                item = TranscriptItem(title, file_path, date)
                self.transcripts_list.addItem(item)
                
    def load_transcript_content(self, item):
        if item:
            file_path = item.file_path
            if os.path.exists(file_path):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    
                    # Set title
                    self.title_label.setText(item.text().split(' (')[0])
                    
                    # Extract text from document
                    full_text = []
                    for paragraph in doc.paragraphs:
                        full_text.append(paragraph.text)
                    
                    # Display content
                    self.content_display.setText('\n'.join(full_text))
                    
                    # Enable buttons
                    self.export_button.setEnabled(True)
                    self.delete_button.setEnabled(True)
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not load transcript: {str(e)}")
            else:
                QMessageBox.warning(self, "Error", "Transcript file not found.")
                
    def filter_transcripts(self):
        search_text = self.search_input.text().lower()
        
        for i in range(self.transcripts_list.count()):
            item = self.transcripts_list.item(i)
            item.setHidden(search_text not in item.text().lower())
            
    def export_transcript(self):
        current_item = self.transcripts_list.currentItem()
        if current_item:
            file_name = current_item.text().split(' (')[0]
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Transcript",
                os.path.join(os.path.expanduser("~"), f"{file_name}.txt"),
                "Text Files (*.txt);;Word Documents (*.docx);;All Files (*)"
            )
            
            if file_path:
                try:
                    # If exporting as txt
                    if file_path.lower().endswith('.txt'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(self.content_display.toPlainText())
                    else:
                        # Just copy the original docx file
                        import shutil
                        shutil.copy2(current_item.file_path, file_path)
                        
                    self.parent.statusBar().showMessage(f"Transcript exported to {file_path}")
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not export transcript: {str(e)}")
                    
    def delete_transcript(self):
        current_item = self.transcripts_list.currentItem()
        if current_item:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete '{current_item.text()}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # Delete file
                    os.remove(current_item.file_path)
                    
                    # Remove from list
                    self.transcripts_list.takeItem(self.transcripts_list.row(current_item))
                    
                    # Clear display
                    self.title_label.clear()
                    self.content_display.clear()
                    
                    # Disable buttons
                    self.export_button.setEnabled(False)
                    self.delete_button.setEnabled(False)
                    
                    self.parent.statusBar().showMessage("Transcript deleted")
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not delete transcript: {str(e)}") 