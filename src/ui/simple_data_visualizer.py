import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QSplitter, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt

class SimpleDataVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Create directory for data
        self.data_directory = os.path.join(os.path.expanduser("~/Documents"), "VideoDownloader", "Data")
        os.makedirs(self.data_directory, exist_ok=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = QHBoxLayout()
        title = QLabel("Data Visualizer")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        import_btn = QPushButton("Import Data")
        import_btn.clicked.connect(self.import_data)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(import_btn)
        
        layout.addLayout(header_layout)
        
        # Main content
        info_label = QLabel("This is a simplified version of the Data Visualizer.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px;")
        
        layout.addWidget(info_label)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Stretcher
        layout.addStretch()
    
    def import_data(self):
        """Import data file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.status_label.setText(f"Selected file: {os.path.basename(file_path)}")
            QMessageBox.information(self, "File Selected", f"You selected: {file_path}\n\nIn the full version, this would create visualizations from your data.") 