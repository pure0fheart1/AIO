from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QLabel, QFrame, QGraphicsView, QGraphicsScene,
                             QGraphicsItem, QSlider, QPushButton, QComboBox,
                             QToolButton, QMessageBox)
from PyQt5.QtCore import Qt, QRectF, QPointF, QDate, QDateTime, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QIcon

from datetime import datetime, timedelta
import uuid

from timeline_view import TimelineView
from milestone_item import MilestoneItem
from task_item import TaskItem

class RoadmapCanvas(QWidget):
    """Main canvas for displaying and interacting with roadmap elements"""
    
    # Signals
    item_selected = pyqtSignal(object)
    item_moved = pyqtSignal(object, QPointF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_view = "timeline"
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar at the top
        control_bar = QFrame()
        control_bar.setFrameShape(QFrame.StyledPanel)
        control_bar_layout = QHBoxLayout(control_bar)
        
        # Zoom control
        zoom_label = QLabel("Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        
        # Time scale selector
        scale_label = QLabel("Scale:")
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Days", "Weeks", "Months", "Quarters", "Years"])
        self.scale_combo.setCurrentIndex(2)  # Default to Months
        self.scale_combo.currentIndexChanged.connect(self.scale_changed)
        
        # Add to control bar
        control_bar_layout.addWidget(zoom_label)
        control_bar_layout.addWidget(self.zoom_slider)
        control_bar_layout.addSpacing(20)
        control_bar_layout.addWidget(scale_label)
        control_bar_layout.addWidget(self.scale_combo)
        control_bar_layout.addStretch(1)
        
        # Task Dependency Controls
        dependency_label = QLabel("Dependencies:")
        self.create_dependency_btn = QToolButton()
        self.create_dependency_btn.setText("Create")
        self.create_dependency_btn.setCheckable(True)
        self.create_dependency_btn.clicked.connect(self.toggle_dependency_mode)
        
        self.show_critical_path_btn = QPushButton("Show Critical Path")
        self.show_critical_path_btn.setCheckable(True)
        self.show_critical_path_btn.clicked.connect(self.toggle_critical_path)
        
        control_bar_layout.addWidget(dependency_label)
        control_bar_layout.addWidget(self.create_dependency_btn)
        control_bar_layout.addWidget(self.show_critical_path_btn)
        control_bar_layout.addSpacing(20)
        
        # Switch view buttons
        self.timeline_btn = QPushButton("Timeline")
        self.timeline_btn.setCheckable(True)
        self.timeline_btn.setChecked(True)
        self.timeline_btn.clicked.connect(lambda: self.switch_view("timeline"))
        
        self.gantt_btn = QPushButton("Gantt Chart")
        self.gantt_btn.setCheckable(True)
        self.gantt_btn.clicked.connect(lambda: self.switch_view("gantt"))
        
        self.mindmap_btn = QPushButton("Mind Map")
        self.mindmap_btn.setCheckable(True)
        self.mindmap_btn.clicked.connect(lambda: self.switch_view("mindmap"))
        
        control_bar_layout.addWidget(self.timeline_btn)
        control_bar_layout.addWidget(self.gantt_btn)
        control_bar_layout.addWidget(self.mindmap_btn)
        
        # Timeline view (the default view)
        self.timeline_view = TimelineView()
        
        # Connect signals
        self.timeline_view.item_selected.connect(self.handle_item_selected)
        
        # Scroll area to contain the view
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.timeline_view)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Add widgets to main layout
        layout.addWidget(control_bar)
        layout.addWidget(self.scroll_area)
        
        # Setup drag and drop
        self.setAcceptDrops(True)
        
    def zoom_changed(self, value):
        """Handle zoom slider value change"""
        zoom_factor = value / 100.0
        self.timeline_view.set_zoom(zoom_factor)
        
    def scale_changed(self, index):
        """Handle time scale change"""
        scales = ["day", "week", "month", "quarter", "year"]
        if index >= 0 and index < len(scales):
            self.timeline_view.set_time_scale(scales[index])
            
    def switch_view(self, view_type):
        """Switch between different visualization types"""
        if view_type == self.current_view:
            return
            
        self.current_view = view_type
        
        # Update button states
        self.timeline_btn.setChecked(view_type == "timeline")
        self.gantt_btn.setChecked(view_type == "gantt")
        self.mindmap_btn.setChecked(view_type == "mindmap")
        
        # Replace the view in the scroll area
        if view_type == "timeline":
            self.scroll_area.setWidget(self.timeline_view)
        elif view_type == "gantt":
            # In a real implementation, this would be a separate GanttView class
            placeholder = QLabel("Gantt Chart View (Coming Soon)")
            placeholder.setAlignment(Qt.AlignCenter)
            self.scroll_area.setWidget(placeholder)
        elif view_type == "mindmap":
            # In a real implementation, this would be a separate MindMapView class
            placeholder = QLabel("Mind Map View (Coming Soon)")
            placeholder.setAlignment(Qt.AlignCenter)
            self.scroll_area.setWidget(placeholder)
    
    def add_milestone(self, title, date, description="", color=None):
        """Add a milestone to the timeline"""
        milestone = MilestoneItem(title, date, description, color)
        self.timeline_view.add_item(milestone)
        return milestone
        
    def add_task(self, title, start_date, end_date, description="", color=None):
        """Add a task to the timeline"""
        task = TaskItem(title, start_date, end_date, description, color)
        self.timeline_view.add_item(task)
        return task
        
    def clear(self):
        """Clear all items from the canvas"""
        self.timeline_view.clear()
    
    def toggle_dependency_mode(self, checked):
        """Toggle dependency creation mode"""
        if self.current_view == "timeline":
            self.timeline_view.enable_dependency_mode(checked)
            if checked:
                dependency_help = (
                    "Dependency Creation Mode Active\n\n"
                    "Click on a source task, then click on a target task to create a dependency. "
                    "The target task will depend on the source task.\n\n"
                    "Click again on the Create button or press Esc to exit dependency mode."
                )
                QMessageBox.information(self, "Dependency Mode", dependency_help)
        else:
            self.create_dependency_btn.setChecked(False)
            QMessageBox.warning(self, "Not Available", 
                             "Dependency creation is only available in Timeline view.")
    
    def toggle_critical_path(self, checked):
        """Toggle critical path display"""
        if self.current_view == "timeline":
            if checked:
                # Run critical path analysis
                self.timeline_view.analyze_critical_path()
            else:
                # Reset critical path highlighting
                for item in self.timeline_view.items:
                    if hasattr(item, 'set_critical'):
                        item.set_critical(False)
                # Redraw the timeline
                self.timeline_view.initialize_timeline()
        else:
            self.show_critical_path_btn.setChecked(False)
            QMessageBox.warning(self, "Not Available", 
                             "Critical path analysis is only available in Timeline view.")
    
    def handle_item_selected(self, item):
        """Handle item selection from the timeline view"""
        self.item_selected.emit(item)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-roadmapitem"):
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-roadmapitem"):
            item_data = event.mimeData().data("application/x-roadmapitem")
            # In a real implementation, deserialize the item data and add it
            event.acceptProposedAction() 