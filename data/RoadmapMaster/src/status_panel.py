from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTabWidget, QProgressBar, QPushButton)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QPalette

from datetime import datetime, timedelta

class StatusPanel(QWidget):
    """
    Panel for displaying analytics and progress metrics
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Set initial demo data
        self.update_demo_data()
        
    def setup_ui(self):
        # Set up main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        
        # Project progress section
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_title = QLabel("Project Progress")
        progress_title.setStyleSheet("font-weight: bold;")
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(45)
        self.overall_progress_bar.setFormat("%v% Complete")
        
        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(self.overall_progress_bar)
        
        # Timeline metrics section
        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout(timeline_widget)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        
        timeline_title = QLabel("Timeline")
        timeline_title.setStyleSheet("font-weight: bold;")
        
        metrics_layout = QHBoxLayout()
        
        # Start date
        start_date_layout = QVBoxLayout()
        start_date_label = QLabel("Start Date:")
        self.start_date_value = QLabel("Jan 15, 2023")
        self.start_date_value.setStyleSheet("font-weight: bold;")
        start_date_layout.addWidget(start_date_label)
        start_date_layout.addWidget(self.start_date_value)
        
        # End date
        end_date_layout = QVBoxLayout()
        end_date_label = QLabel("End Date:")
        self.end_date_value = QLabel("Dec 31, 2023")
        self.end_date_value.setStyleSheet("font-weight: bold;")
        end_date_layout.addWidget(end_date_label)
        end_date_layout.addWidget(self.end_date_value)
        
        # Days remaining
        days_layout = QVBoxLayout()
        days_label = QLabel("Days Remaining:")
        self.days_value = QLabel("45")
        self.days_value.setStyleSheet("font-weight: bold;")
        days_layout.addWidget(days_label)
        days_layout.addWidget(self.days_value)
        
        metrics_layout.addLayout(start_date_layout)
        metrics_layout.addLayout(end_date_layout)
        metrics_layout.addLayout(days_layout)
        
        timeline_layout.addWidget(timeline_title)
        timeline_layout.addLayout(metrics_layout)
        
        # Task summary section
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        
        tasks_title = QLabel("Tasks")
        tasks_title.setStyleSheet("font-weight: bold;")
        
        task_metrics_layout = QHBoxLayout()
        
        # Total tasks
        total_tasks_layout = QVBoxLayout()
        total_tasks_label = QLabel("Total:")
        self.total_tasks_value = QLabel("24")
        self.total_tasks_value.setStyleSheet("font-weight: bold;")
        total_tasks_layout.addWidget(total_tasks_label)
        total_tasks_layout.addWidget(self.total_tasks_value)
        
        # Completed tasks
        completed_tasks_layout = QVBoxLayout()
        completed_tasks_label = QLabel("Completed:")
        self.completed_tasks_value = QLabel("10")
        self.completed_tasks_value.setStyleSheet("font-weight: bold; color: green;")
        completed_tasks_layout.addWidget(completed_tasks_label)
        completed_tasks_layout.addWidget(self.completed_tasks_value)
        
        # Pending tasks
        pending_tasks_layout = QVBoxLayout()
        pending_tasks_label = QLabel("Pending:")
        self.pending_tasks_value = QLabel("8")
        self.pending_tasks_value.setStyleSheet("font-weight: bold; color: orange;")
        pending_tasks_layout.addWidget(pending_tasks_label)
        pending_tasks_layout.addWidget(self.pending_tasks_value)
        
        # Overdue tasks
        overdue_tasks_layout = QVBoxLayout()
        overdue_tasks_label = QLabel("Overdue:")
        self.overdue_tasks_value = QLabel("2")
        self.overdue_tasks_value.setStyleSheet("font-weight: bold; color: red;")
        overdue_tasks_layout.addWidget(overdue_tasks_label)
        overdue_tasks_layout.addWidget(self.overdue_tasks_value)
        
        task_metrics_layout.addLayout(total_tasks_layout)
        task_metrics_layout.addLayout(completed_tasks_layout)
        task_metrics_layout.addLayout(pending_tasks_layout)
        task_metrics_layout.addLayout(overdue_tasks_layout)
        
        tasks_layout.addWidget(tasks_title)
        tasks_layout.addLayout(task_metrics_layout)
        
        # Add vertical separators between sections
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        
        # Refresh button in a layout to align it to the right
        refresh_layout = QVBoxLayout()
        refresh_layout.addStretch(1)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFixedWidth(80)
        self.refresh_button.clicked.connect(self.update_data)
        
        refresh_layout.addWidget(self.refresh_button)
        
        # Add all sections to main layout
        main_layout.addWidget(progress_widget)
        main_layout.addWidget(separator1)
        main_layout.addWidget(timeline_widget)
        main_layout.addWidget(separator2)
        main_layout.addWidget(tasks_widget)
        main_layout.addStretch(1)
        main_layout.addLayout(refresh_layout)
        
        # Set fixed height
        self.setFixedHeight(100)
        
    def update_data(self):
        """Update the panel with current project data"""
        # In a real application, this would fetch data from the project
        # For now, we'll just simulate changing data
        self.update_demo_data()
        
    def update_demo_data(self):
        """Update the panel with simulated demo data"""
        # Set random-ish values for demonstration
        import random
        
        # Project progress
        progress = random.randint(30, 80)
        self.overall_progress_bar.setValue(progress)
        
        # Timeline dates
        start_date = datetime(2023, 1, 15)
        end_date = datetime(2023, 12, 31)
        self.start_date_value.setText(start_date.strftime("%b %d, %Y"))
        self.end_date_value.setText(end_date.strftime("%b %d, %Y"))
        
        # Calculate days remaining (using current date)
        today = datetime.now()
        remaining = (end_date - today).days
        remaining = max(0, remaining)
        self.days_value.setText(str(remaining))
        
        # Task metrics
        total = random.randint(20, 30)
        completed = random.randint(8, 15)
        overdue = random.randint(1, 4)
        pending = total - completed - overdue
        
        self.total_tasks_value.setText(str(total))
        self.completed_tasks_value.setText(str(completed))
        self.pending_tasks_value.setText(str(pending))
        self.overdue_tasks_value.setText(str(overdue)) 