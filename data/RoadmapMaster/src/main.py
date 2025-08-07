import sys
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSplitter, QFrame, QTabWidget,
                            QToolBar, QStatusBar, QAction, QMenu, QMenuBar,
                            QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
                            QDateEdit, QColorDialog, QMessageBox, QDockWidget,
                            QSplashScreen, QPainter, QFont)
from PyQt5.QtCore import Qt, QSize, QDate, QTimer
from PyQt5.QtGui import QIcon, QColor, QPixmap

# Import local modules
from roadmap_canvas import RoadmapCanvas
from sidebar import Sidebar
from properties_panel import PropertiesPanel
from status_panel import StatusPanel
from task_item import TaskItem
from milestone_item import MilestoneItem
from analytics_panel import AnalyticsPanel
from collaboration_manager import CollaborationManager, CommentsPanel, ActivityPanel
from export_manager import ExportManager, ExportDialog, ImportDialog

class RoadmapMaster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Roadmap Master")
        self.setMinimumSize(1200, 800)
        
        # Initialize collaboration manager
        self.collaboration_manager = CollaborationManager(self)
        
        # Initialize export manager
        self.export_manager = ExportManager(self)
        
        # Set up the main layout
        self.setup_ui()
        self.setup_menubar()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Connect signals between components
        self.connect_signals()
        
        # Apply initial styles
        self.apply_styles()
        
        # Add some sample data
        self.add_sample_data()
        
    def setup_ui(self):
        # Create central widget with main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Left sidebar for project navigation
        self.sidebar = Sidebar()
        
        # Center area with roadmap canvas
        self.roadmap_canvas = RoadmapCanvas()
        
        # Right panel for properties and details
        self.properties_panel = PropertiesPanel(self)
        
        # Add panels to the main splitter
        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(self.roadmap_canvas)
        self.main_splitter.addWidget(self.properties_panel)
        
        # Set the initial sizes of the splitter panels
        self.main_splitter.setSizes([200, 800, 250])  # Left, Center, Right
        
        # Bottom status panel
        self.status_panel = StatusPanel()
        
        # Add widgets to main layout
        main_layout.addWidget(self.main_splitter, 1)  # 1 is the stretch factor
        main_layout.addWidget(self.status_panel)
        
        # Set the central widget
        self.setCentralWidget(central_widget)
        
        # Create analytics panel as a dock widget (initially hidden)
        self.setup_analytics_panel()
        
        # Create collaboration panels as dock widgets
        self.setup_collaboration_panels()
        
    def setup_analytics_panel(self):
        """Set up the analytics panel as a dock widget"""
        # Create analytics panel
        self.analytics_panel = AnalyticsPanel(self)
        
        # Create dock widget to contain the analytics panel
        self.analytics_dock = QDockWidget("Analytics & Reporting", self)
        self.analytics_dock.setWidget(self.analytics_panel)
        self.analytics_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.analytics_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        
        # Add dock widget to main window
        self.addDockWidget(Qt.RightDockWidgetArea, self.analytics_dock)
        
        # Initially hide the analytics panel
        self.analytics_dock.hide()
        
    def setup_collaboration_panels(self):
        """Set up the collaboration panels as dock widgets"""
        # Create comments panel
        self.comments_panel = CommentsPanel(self.collaboration_manager, self)
        
        # Create comments dock widget
        self.comments_dock = QDockWidget("Comments", self)
        self.comments_dock.setWidget(self.comments_panel)
        self.comments_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.comments_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        
        # Add comments dock widget to main window
        self.addDockWidget(Qt.BottomDockWidgetArea, self.comments_dock)
        
        # Create activity panel
        self.activity_panel = ActivityPanel(self.collaboration_manager, self)
        
        # Create activity dock widget
        self.activity_dock = QDockWidget("Activity", self)
        self.activity_dock.setWidget(self.activity_panel)
        self.activity_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.activity_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        
        # Add activity dock widget to main window
        self.addDockWidget(Qt.RightDockWidgetArea, self.activity_dock)
        
        # Initially hide the collaboration panels
        self.comments_dock.hide()
        self.activity_dock.hide()
        
    def connect_signals(self):
        # Connect signals between components
        
        # Item selection on canvas updates the properties panel
        self.roadmap_canvas.item_selected.connect(self.properties_panel.set_item)
        
        # When properties are updated, update the canvas
        self.properties_panel.item_updated.connect(self.update_timeline)
        
        # When dependencies are updated, refresh the canvas
        self.properties_panel.dependency_updated.connect(self.update_timeline)
        
        # Connect sidebar project selection to filter items in canvas
        self.sidebar.project_selected.connect(self.filter_by_project)
        self.sidebar.milestone_selected.connect(self.select_milestone)
        self.sidebar.task_selected.connect(self.select_task)
        
        # Connect item selection to comments panel
        self.roadmap_canvas.item_selected.connect(self.comments_panel.set_item)
        
        # Connect collaboration signals
        self.collaboration_manager.user_connected.connect(self.handle_user_connected)
        self.collaboration_manager.user_disconnected.connect(self.handle_user_disconnected)
        self.collaboration_manager.item_updated.connect(self.handle_item_updated)
        self.collaboration_manager.sync_completed.connect(self.handle_sync_completed)
        
        # Connect export signals
        self.export_manager.export_started.connect(lambda: self.statusBar().showMessage("Export started..."))
        self.export_manager.export_completed.connect(lambda path: self.statusBar().showMessage(f"Export completed: {path}", 5000))
        self.export_manager.export_error.connect(lambda error: self.statusBar().showMessage(f"Export error: {error}", 5000))
        
    def update_timeline(self, *args):
        """Update the timeline view to reflect changes"""
        # Refresh the canvas
        self.roadmap_canvas.timeline_view.initialize_timeline()
        
        # Run critical path analysis if it's enabled
        if hasattr(self.roadmap_canvas, 'show_critical_path_btn') and self.roadmap_canvas.show_critical_path_btn.isChecked():
            self.roadmap_canvas.timeline_view.analyze_critical_path()
            
        # Update the status panel with progress information
        self.update_status_panel()
    
    def update_status_panel(self):
        """Update the status panel with current project data"""
        # Get all tasks from the timeline
        tasks = [item for item in self.roadmap_canvas.timeline_view.items 
                if hasattr(item, 'progress')]
        
        if not tasks:
            return
            
        # Calculate overall progress
        total_progress = sum(task.progress for task in tasks)
        avg_progress = total_progress / len(tasks) if tasks else 0
        
        # Update the progress bar in the status panel
        self.status_panel.overall_progress_bar.setValue(int(avg_progress))
        
        # Get date range
        start_dates = [task.start_date for task in tasks if hasattr(task, 'start_date')]
        end_dates = [task.end_date for task in tasks if hasattr(task, 'end_date')]
        milestone_dates = [item.date for item in self.roadmap_canvas.timeline_view.items 
                         if hasattr(item, 'date')]
        
        all_dates = start_dates + end_dates + milestone_dates
        if all_dates:
            start_date = min(all_dates).strftime("%b %d, %Y")
            end_date = max(all_dates).strftime("%b %d, %Y")
            
            # Update dates in the status panel
            self.status_panel.start_date_value.setText(start_date)
            self.status_panel.end_date_value.setText(end_date)
            
        # Count tasks by status
        total = len(tasks)
        completed = sum(1 for task in tasks if task.progress == 100)
        overdue = sum(1 for task in tasks if task.end_date < datetime.now() and task.progress < 100)
        pending = total - completed - overdue
        
        # Update task counts in the status panel
        self.status_panel.total_tasks_value.setText(str(total))
        self.status_panel.completed_tasks_value.setText(str(completed))
        self.status_panel.pending_tasks_value.setText(str(pending))
        self.status_panel.overdue_tasks_value.setText(str(overdue))
    
    def filter_by_project(self, project_id):
        """Filter timeline items by project"""
        # This would filter the timeline to show only items from the selected project
        # In a real implementation, this would query a data model
        # For now, we'll just show a status message
        self.statusBar().showMessage(f"Selected project: {project_id}")
    
    def select_milestone(self, milestone_id):
        """Select a milestone in the timeline"""
        # This would find and select the milestone with the given ID
        # In a real implementation, this would query a data model
        self.statusBar().showMessage(f"Selected milestone: {milestone_id}")
    
    def select_task(self, task_id):
        """Select a task in the timeline"""
        # This would find and select the task with the given ID
        # In a real implementation, this would query a data model
        self.statusBar().showMessage(f"Selected task: {task_id}")
        
    def setup_menubar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Roadmap", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_roadmap)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Roadmap", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export...", self)
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)
        
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        edit_menu.addAction(paste_action)
        
        # Task menu
        task_menu = menubar.addMenu("Task")
        
        add_task_action = QAction("Add Task", self)
        add_task_action.triggered.connect(self.show_add_task_dialog)
        task_menu.addAction(add_task_action)
        
        add_milestone_action = QAction("Add Milestone", self)
        add_milestone_action.triggered.connect(self.show_add_milestone_dialog)
        task_menu.addAction(add_milestone_action)
        
        task_menu.addSeparator()
        
        create_dependency_action = QAction("Create Dependency", self)
        create_dependency_action.setCheckable(True)
        create_dependency_action.triggered.connect(self.toggle_dependency_mode)
        task_menu.addAction(create_dependency_action)
        
        analyze_critical_path_action = QAction("Show Critical Path", self)
        analyze_critical_path_action.setCheckable(True)
        analyze_critical_path_action.triggered.connect(self.toggle_critical_path)
        task_menu.addAction(analyze_critical_path_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        view_menu.addSeparator()
        
        gantt_view_action = QAction("Gantt Chart View", self)
        gantt_view_action.triggered.connect(lambda: self.roadmap_canvas.switch_view("gantt"))
        view_menu.addAction(gantt_view_action)
        
        mindmap_view_action = QAction("Mind Map View", self)
        mindmap_view_action.triggered.connect(lambda: self.roadmap_canvas.switch_view("mindmap"))
        view_menu.addAction(mindmap_view_action)
        
        timeline_view_action = QAction("Timeline View", self)
        timeline_view_action.triggered.connect(lambda: self.roadmap_canvas.switch_view("timeline"))
        view_menu.addAction(timeline_view_action)
        
        # Analytics menu
        analytics_menu = menubar.addMenu("Analytics")
        
        show_analytics_action = QAction("Show Analytics Panel", self)
        show_analytics_action.setCheckable(True)
        show_analytics_action.triggered.connect(self.toggle_analytics_panel)
        analytics_menu.addAction(show_analytics_action)
        
        analytics_menu.addSeparator()
        
        project_progress_action = QAction("Project Progress Report", self)
        project_progress_action.triggered.connect(lambda: self.show_analytics_tab(0))  # 0 = Overview tab
        analytics_menu.addAction(project_progress_action)
        
        task_progress_action = QAction("Task Progress Report", self)
        task_progress_action.triggered.connect(lambda: self.show_analytics_tab(1))  # 1 = Progress tab
        analytics_menu.addAction(task_progress_action)
        
        timeline_analysis_action = QAction("Timeline Analysis", self)
        timeline_analysis_action.triggered.connect(lambda: self.show_analytics_tab(2))  # 2 = Timeline tab
        analytics_menu.addAction(timeline_analysis_action)
        
        task_distribution_action = QAction("Task Distribution Analysis", self)
        task_distribution_action.triggered.connect(lambda: self.show_analytics_tab(3))  # 3 = Distribution tab
        analytics_menu.addAction(task_distribution_action)
        
        analytics_menu.addSeparator()
        
        refresh_analytics_action = QAction("Refresh Analytics", self)
        refresh_analytics_action.triggered.connect(self.refresh_analytics)
        analytics_menu.addAction(refresh_analytics_action)
        
        # Collaboration menu
        collab_menu = menubar.addMenu("Collaboration")
        
        show_comments_action = QAction("Show Comments Panel", self)
        show_comments_action.setCheckable(True)
        show_comments_action.triggered.connect(self.toggle_comments_panel)
        collab_menu.addAction(show_comments_action)
        
        show_activity_action = QAction("Show Activity Panel", self)
        show_activity_action.setCheckable(True)
        show_activity_action.triggered.connect(self.toggle_activity_panel)
        collab_menu.addAction(show_activity_action)
        
        collab_menu.addSeparator()
        
        share_project_action = QAction("Share Project...", self)
        share_project_action.triggered.connect(self.show_share_project_dialog)
        collab_menu.addAction(share_project_action)
        
        collab_menu.addSeparator()
        
        sync_action = QAction("Sync with Server", self)
        sync_action.triggered.connect(self.sync_with_server)
        collab_menu.addAction(sync_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        analyze_action = QAction("Analyze Dependencies", self)
        tools_menu.addAction(analyze_action)
        
        critical_path_action = QAction("Show Critical Path", self)
        critical_path_action.triggered.connect(lambda: self.roadmap_canvas.toggle_critical_path(True))
        tools_menu.addAction(critical_path_action)
        
        calendar_sync_action = QAction("Sync with Calendar", self)
        tools_menu.addAction(calendar_sync_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        docs_action = QAction("Documentation", self)
        help_menu.addAction(docs_action)
        
        shortcuts_action = QAction("Keyboard Shortcuts", self)
        help_menu.addAction(shortcuts_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # New roadmap action
        new_action = QAction("New", self)
        new_action.setStatusTip("Create a new roadmap")
        new_action.triggered.connect(self.new_roadmap)
        toolbar.addAction(new_action)
        
        # Open roadmap action
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open an existing roadmap")
        toolbar.addAction(open_action)
        
        # Save action
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save current roadmap")
        toolbar.addAction(save_action)
        
        # Export action
        export_action = QAction("Export", self)
        export_action.setStatusTip("Export roadmap to file or service")
        export_action.triggered.connect(self.show_export_dialog)
        toolbar.addAction(export_action)
        
        # Import action
        import_action = QAction("Import", self)
        import_action.setStatusTip("Import roadmap from file")
        import_action.triggered.connect(self.show_import_dialog)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        # Add milestone action
        add_milestone_action = QAction("Add Milestone", self)
        add_milestone_action.setStatusTip("Add a new milestone")
        add_milestone_action.triggered.connect(self.show_add_milestone_dialog)
        toolbar.addAction(add_milestone_action)
        
        # Add task action
        add_task_action = QAction("Add Task", self)
        add_task_action.setStatusTip("Add a new task")
        add_task_action.triggered.connect(self.show_add_task_dialog)
        toolbar.addAction(add_task_action)
        
        # Link items action
        link_action = QAction("Link Items", self)
        link_action.setStatusTip("Create a dependency link between items")
        link_action.setCheckable(True)
        link_action.triggered.connect(self.toggle_dependency_mode)
        toolbar.addAction(link_action)
        
        toolbar.addSeparator()
        
        # Show critical path action
        critical_path_action = QAction("Show Critical Path", self)
        critical_path_action.setStatusTip("Highlight the critical path in the project")
        critical_path_action.setCheckable(True)
        critical_path_action.triggered.connect(self.toggle_critical_path)
        toolbar.addAction(critical_path_action)
        
        # Show analytics action
        analytics_action = QAction("Analytics", self)
        analytics_action.setStatusTip("Show analytics and reporting panel")
        analytics_action.setCheckable(True)
        analytics_action.triggered.connect(self.toggle_analytics_panel)
        toolbar.addAction(analytics_action)
        
        # Show collaboration action
        collab_action = QAction("Collaboration", self)
        collab_action.setStatusTip("Show collaboration and activity panels")
        collab_action.setCheckable(True)
        collab_action.triggered.connect(self.toggle_collaboration)
        toolbar.addAction(collab_action)
        
        toolbar.addSeparator()
        
        # View mode actions
        timeline_action = QAction("Timeline", self)
        timeline_action.setStatusTip("Switch to timeline view")
        timeline_action.triggered.connect(lambda: self.roadmap_canvas.switch_view("timeline"))
        toolbar.addAction(timeline_action)
        
        gantt_action = QAction("Gantt", self)
        gantt_action.setStatusTip("Switch to Gantt chart view")
        gantt_action.triggered.connect(lambda: self.roadmap_canvas.switch_view("gantt"))
        toolbar.addAction(gantt_action)
        
        mindmap_action = QAction("Mind Map", self)
        mindmap_action.setStatusTip("Switch to mind map view")
        mindmap_action.triggered.connect(lambda: self.roadmap_canvas.switch_view("mindmap"))
        toolbar.addAction(mindmap_action)
        
    def setup_statusbar(self):
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)
        
    def apply_styles(self):
        # Set application-wide stylesheet
        stylesheet = """
            /* Global styles */
            QMainWindow, QDialog {
                background-color: #f8f9fa;
                color: #343a40;
            }
            
            /* Menu and toolbar styles */
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 2px;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }
            
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 0px;
            }
            
            QMenu::item {
                padding: 6px 20px 6px 20px;
                border-radius: 2px;
            }
            
            QMenu::item:selected {
                background-color: #e9ecef;
            }
            
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 5px;
                padding: 2px;
            }
            
            QToolBar QToolButton {
                background-color: transparent;
                border-radius: 4px;
                padding: 4px;
            }
            
            QToolBar QToolButton:hover {
                background-color: #e9ecef;
            }
            
            QToolBar QToolButton:pressed {
                background-color: #dee2e6;
            }
            
            /* Panel and widget styles */
            QSplitter::handle {
                background-color: #dee2e6;
            }
            
            QSplitter::handle:horizontal {
                width: 1px;
            }
            
            QSplitter::handle:vertical {
                height: 1px;
            }
            
            QDockWidget {
                border: 1px solid #dee2e6;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(undock.png);
            }
            
            QDockWidget::title {
                background-color: #f8f9fa;
                padding-left: 5px;
                padding-top: 2px;
                border-bottom: 1px solid #dee2e6;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                top: -1px;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom-color: #dee2e6;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 5px 10px;
            }
            
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #ffffff;
            }
            
            QTabBar::tab:selected {
                border-bottom-color: #ffffff;
            }
            
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 3px;
            }
            
            /* Form control styles */
            QLineEdit, QTextEdit, QDateEdit, QComboBox, QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
                selection-background-color: #007bff;
            }
            
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #80bdff;
                outline: 0;
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
            }
            
            QPushButton {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: #f8f9fa;
                padding: 5px 10px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #dee2e6;
            }
            
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            
            QPushButton:checked {
                background-color: #e9ecef;
                border-color: #dee2e6;
            }
            
            /* StatusBar styles */
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
            }
            
            /* ScrollBar styles */
            QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #adb5bd;
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f8f9fa;
                height: 12px;
                margin: 0px 0px 0px 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #adb5bd;
                min-width: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Table styles */
            QTableView, QTreeView, QListView {
                border: 1px solid #dee2e6;
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
            }
            
            QTableView::item, QTreeView::item, QListView::item {
                padding: 4px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {
                background-color: #007bff;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #dee2e6;
                border-left: 0px;
                border-top: 0px;
                font-weight: bold;
                color: #495057;
            }
            
            /* Progress bar styles */
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                background-color: #f8f9fa;
            }
            
            QProgressBar::chunk {
                background-color: #007bff;
                width: 10px;
                margin: 0.5px;
            }
        """
        QApplication.instance().setStyleSheet(stylesheet)
    
    def new_roadmap(self):
        """Create a new empty roadmap"""
        reply = QMessageBox.question(self, "Confirm New Roadmap", 
                                   "This will clear all current items. Continue?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.roadmap_canvas.clear()
            self.statusBar().showMessage("Created new roadmap")
    
    def show_add_task_dialog(self):
        """Show dialog to add a new task"""
        dialog = AddTaskDialog(self)
        if dialog.exec_():
            # Get the task details from the dialog
            title = dialog.title_edit.text()
            start_date = dialog.start_date.date().toPyDate()
            end_date = dialog.end_date.date().toPyDate()
            color = dialog.color
            
            # Create and add the task
            task = self.roadmap_canvas.add_task(title, start_date, end_date, "", color)
            
            # Update the timeline
            self.update_timeline()
            
            # Show confirmation
            self.statusBar().showMessage(f"Added task: {title}")
    
    def show_add_milestone_dialog(self):
        """Show dialog to add a new milestone"""
        dialog = AddMilestoneDialog(self)
        if dialog.exec_():
            # Get the milestone details from the dialog
            title = dialog.title_edit.text()
            date = dialog.date_edit.date().toPyDate()
            color = dialog.color
            
            # Create and add the milestone
            milestone = self.roadmap_canvas.add_milestone(title, date, "", color)
            
            # Update the timeline
            self.update_timeline()
            
            # Show confirmation
            self.statusBar().showMessage(f"Added milestone: {title}")
    
    def toggle_dependency_mode(self, checked):
        """Toggle dependency creation mode"""
        self.roadmap_canvas.toggle_dependency_mode(checked)
    
    def toggle_critical_path(self, checked):
        """Toggle critical path display"""
        self.roadmap_canvas.toggle_critical_path(checked)
    
    def zoom_in(self):
        """Zoom in on the timeline"""
        current_value = self.roadmap_canvas.zoom_slider.value()
        new_value = min(current_value + 10, 200)
        self.roadmap_canvas.zoom_slider.setValue(new_value)
    
    def zoom_out(self):
        """Zoom out on the timeline"""
        current_value = self.roadmap_canvas.zoom_slider.value()
        new_value = max(current_value - 10, 50)
        self.roadmap_canvas.zoom_slider.setValue(new_value)
    
    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About Roadmap Master",
                        "<h3>Roadmap Master</h3>"
                        "<p>Version 1.0</p>"
                        "<p>A comprehensive application for creating and managing project roadmaps.</p>"
                        "<p>Features include:</p>"
                        "<ul>"
                        "<li>Interactive timeline visualization</li>"
                        "<li>Task dependency tracking</li>"
                        "<li>Critical path analysis</li>"
                        "<li>Multiple visualization modes</li>"
                        "</ul>")
    
    def add_sample_data(self):
        """Add some sample data to the roadmap"""
        # Start with today's date
        today = datetime.now()
        
        # Project 1: Website Redesign
        # Add milestones
        design_approval = self.roadmap_canvas.add_milestone(
            "Design Approval", 
            today + timedelta(days=15),
            "All design mockups approved by stakeholders",
            "#E91E63"  # Pink
        )
        
        beta_launch = self.roadmap_canvas.add_milestone(
            "Beta Launch", 
            today + timedelta(days=60),
            "Launch beta version to test users",
            "#E91E63"  # Pink
        )
        
        # Add tasks
        wireframes = self.roadmap_canvas.add_task(
            "Wireframes", 
            today + timedelta(days=2),
            today + timedelta(days=10),
            "Create wireframes for all pages",
            "#F06292"  # Light pink
        )
        wireframes.set_progress(100)  # Completed
        
        design = self.roadmap_canvas.add_task(
            "UI Design", 
            today + timedelta(days=11),
            today + timedelta(days=25),
            "Create visual designs based on wireframes",
            "#F06292"  # Light pink
        )
        design.set_progress(50)  # In progress
        
        frontend = self.roadmap_canvas.add_task(
            "Frontend Development", 
            today + timedelta(days=26),
            today + timedelta(days=45),
            "Implement the frontend based on approved designs",
            "#F06292"  # Light pink
        )
        
        backend = self.roadmap_canvas.add_task(
            "Backend Development", 
            today + timedelta(days=26),
            today + timedelta(days=50),
            "Implement backend APIs and database",
            "#F06292"  # Light pink
        )
        
        testing = self.roadmap_canvas.add_task(
            "QA Testing", 
            today + timedelta(days=51),
            today + timedelta(days=59),
            "Test the website for bugs and issues",
            "#F06292"  # Light pink
        )
        
        # Project 2: Product Launch
        # Add milestones
        marketing_start = self.roadmap_canvas.add_milestone(
            "Marketing Campaign Start", 
            today + timedelta(days=40),
            "Begin marketing campaign for the product",
            "#4CAF50"  # Green
        )
        
        product_launch = self.roadmap_canvas.add_milestone(
            "Product Launch", 
            today + timedelta(days=90),
            "Official launch of the product",
            "#4CAF50"  # Green
        )
        
        # Add tasks
        market_research = self.roadmap_canvas.add_task(
            "Market Research", 
            today + timedelta(days=5),
            today + timedelta(days=20),
            "Research market trends and competition",
            "#81C784"  # Light green
        )
        market_research.set_progress(75)  # Mostly done
        
        marketing_materials = self.roadmap_canvas.add_task(
            "Marketing Materials", 
            today + timedelta(days=21),
            today + timedelta(days=39),
            "Create marketing materials and copy",
            "#81C784"  # Light green
        )
        
        pr_outreach = self.roadmap_canvas.add_task(
            "PR Outreach", 
            today + timedelta(days=41),
            today + timedelta(days=75),
            "Contact media outlets and influencers",
            "#81C784"  # Light green
        )
        
        launch_event = self.roadmap_canvas.add_task(
            "Launch Event", 
            today + timedelta(days=76),
            today + timedelta(days=90),
            "Plan and execute the launch event",
            "#81C784"  # Light green
        )
        
        # Setup dependencies
        design.add_dependency(wireframes)
        frontend.add_dependency(design)
        backend.add_dependency(design)
        testing.add_dependency(frontend)
        testing.add_dependency(backend)
        
        marketing_materials.add_dependency(market_research)
        pr_outreach.add_dependency(marketing_materials)
        launch_event.add_dependency(pr_outreach)
        
        # Update the timeline to reflect dependencies
        self.update_timeline()
    
    def toggle_analytics_panel(self, checked):
        """Toggle the visibility of the analytics panel"""
        if checked:
            self.analytics_dock.show()
            # Refresh analytics data when showing the panel
            self.refresh_analytics()
        else:
            self.analytics_dock.hide()
    
    def show_analytics_tab(self, tab_index):
        """Show the analytics panel and select the specified tab"""
        # Show the analytics panel if it's hidden
        self.analytics_dock.show()
        
        # Make sure the Analytics menu item is checked
        self.menuBar().actions()[4].menu().actions()[0].setChecked(True)
        
        # Select the specified tab
        self.analytics_panel.tabs.setCurrentIndex(tab_index)
        
        # Refresh analytics data
        self.refresh_analytics()
    
    def refresh_analytics(self):
        """Refresh all analytics data"""
        if hasattr(self, 'analytics_panel'):
            self.analytics_panel.update_analytics()
            self.statusBar().showMessage("Analytics data refreshed", 3000)
    
    def handle_user_connected(self, user_name):
        """Handle a user connecting to the collaboration session"""
        self.statusBar().showMessage(f"{user_name} connected", 5000)
        
    def handle_user_disconnected(self, user_name):
        """Handle a user disconnecting from the collaboration session"""
        self.statusBar().showMessage(f"{user_name} disconnected", 5000)
        
    def handle_item_updated(self, change):
        """Handle an item being updated by another user"""
        # Update the timeline if needed
        if change["type"] in ["add_task", "update_task"]:
            self.update_timeline()
            
        # Show a status message
        user = self.collaboration_manager.get_user_by_id(change["user_id"])
        user_name = user["name"] if user else "Unknown user"
        
        if change["type"] == "add_task":
            task_title = change["details"].get("title", "unknown task")
            self.statusBar().showMessage(f"{user_name} added task '{task_title}'", 5000)
        elif change["type"] == "update_task":
            self.statusBar().showMessage(f"{user_name} updated task {change['item_id']}", 5000)
        elif change["type"] == "add_comment":
            self.statusBar().showMessage(f"{user_name} commented on {change['item_id']}", 5000)
            
    def handle_sync_completed(self):
        """Handle completion of sync with server"""
        self.statusBar().showMessage("Sync completed", 3000)
    
    def toggle_comments_panel(self, checked):
        """Toggle the visibility of the comments panel"""
        if checked:
            self.comments_dock.show()
        else:
            self.comments_dock.hide()
    
    def toggle_activity_panel(self, checked):
        """Toggle the visibility of the activity panel"""
        if checked:
            self.activity_dock.show()
        else:
            self.activity_dock.hide()
    
    def toggle_collaboration(self, checked):
        """Toggle the visibility of all collaboration panels"""
        # Get the actions from the Collaboration menu
        collab_menu = self.menuBar().actions()[5].menu()  # Collaboration is 6th menu (index 5)
        comments_action = collab_menu.actions()[0]  # First action is "Show Comments Panel"
        activity_action = collab_menu.actions()[1]  # Second action is "Show Activity Panel"
        
        if checked:
            # Show both panels
            self.comments_dock.show()
            self.activity_dock.show()
            
            # Update menu actions
            comments_action.setChecked(True)
            activity_action.setChecked(True)
        else:
            # Hide both panels
            self.comments_dock.hide()
            self.activity_dock.hide()
            
            # Update menu actions
            comments_action.setChecked(False)
            activity_action.setChecked(False)
    
    def show_share_project_dialog(self):
        """Show dialog to share a project"""
        # In a real app, we would get the current project ID
        project_id = "project1"
        project_name = "Website Redesign"
        
        from collaboration_manager import SharingDialog
        dialog = SharingDialog(self.collaboration_manager, project_id, project_name, self)
        dialog.exec_()
    
    def sync_with_server(self):
        """Sync changes with the server"""
        # Show a syncing message
        self.statusBar().showMessage("Syncing with server...", 1000)
        
        # Call the collaboration manager to sync
        self.collaboration_manager.sync_with_server()

    def show_export_dialog(self):
        """Show export dialog"""
        dialog = ExportDialog(self.export_manager, self)
        dialog.exec_()
    
    def show_import_dialog(self):
        """Show import dialog"""
        dialog = ImportDialog(self.export_manager, self)
        dialog.exec_()


class AddTaskDialog(QDialog):
    """Dialog for adding a new task"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Task")
        self.color = "#4A86E8"  # Default color
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Task title
        self.title_edit = QLineEdit()
        form_layout.addRow("Title:", self.title_edit)
        
        # Start date
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date)
        
        # End date
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(7))  # Default to a week later
        self.end_date.setCalendarPopup(True)
        form_layout.addRow("End Date:", self.end_date)
        
        # Color selector
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(f"background-color: {self.color}; border: 1px solid #CCCCCC;")
        
        color_button = QPushButton("Select Color...")
        color_button.clicked.connect(self.select_color)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(color_button)
        
        form_layout.addRow("Color:", color_layout)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_color(self):
        """Open color dialog and select a color"""
        color = QColorDialog.getColor(QColor(self.color), self, "Select Task Color")
        if color.isValid():
            self.color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.color}; border: 1px solid #CCCCCC;")


class AddMilestoneDialog(QDialog):
    """Dialog for adding a new milestone"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Milestone")
        self.color = "#4A86E8"  # Default color
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Milestone title
        self.title_edit = QLineEdit()
        form_layout.addRow("Title:", self.title_edit)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_edit)
        
        # Color selector
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(f"background-color: {self.color}; border: 1px solid #CCCCCC;")
        
        color_button = QPushButton("Select Color...")
        color_button.clicked.connect(self.select_color)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(color_button)
        
        form_layout.addRow("Color:", color_layout)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_color(self):
        """Open color dialog and select a color"""
        color = QColorDialog.getColor(QColor(self.color), self, "Select Milestone Color")
        if color.isValid():
            self.color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.color}; border: 1px solid #CCCCCC;")


if __name__ == "__main__":
    import sys
    import os
    import ctypes
    from PyQt5.QtWidgets import QSplashScreen
    from PyQt5.QtCore import QTimer
    
    # Performance optimization for Windows
    if os.name == 'nt':
        # Set process priority to high
        try:
            process_handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(process_handle, 0x00008000)  # HIGH_PRIORITY_CLASS
        except:
            pass
    
    # Performance optimization for Qt
    # This attribute must be set before QApplication is created
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
    
    # Use software rendering if hardware acceleration causes issues
    # os.environ["QT_OPENGL"] = "software"
    
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application details
    app.setApplicationName("Roadmap Master")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("RoadmapMaster")
    app.setOrganizationDomain("roadmapmaster.com")
    
    # Create a splash screen
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(QColor("#f8f9fa"))
    
    # Create a painter to draw on the pixmap
    painter = QPainter(splash_pix)
    
    # Draw logo text
    font = QFont("Arial", 24, QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#007bff"))
    painter.drawText(splash_pix.rect(), Qt.AlignCenter, "Roadmap Master")
    
    # Draw version
    font = QFont("Arial", 10)
    painter.setFont(font)
    painter.setPen(QColor("#6c757d"))
    painter.drawText(splash_pix.rect().adjusted(0, 100, 0, 0), Qt.AlignCenter, "Version 1.0")
    
    # Add loading text
    font = QFont("Arial", 10)
    painter.setFont(font)
    painter.setPen(QColor("#6c757d"))
    painter.drawText(splash_pix.rect().adjusted(0, 150, 0, 0), Qt.AlignCenter, "Loading...")
    
    # End painting
    painter.end()
    
    # Create and show the splash screen
    splash = QSplashScreen(splash_pix)
    splash.show()
    
    # Process events to ensure splash screen is displayed
    app.processEvents()
    
    # Create the main window (this will be loaded asynchronously)
    window = None
    
    def load_app():
        """Load the application asynchronously"""
        nonlocal window
        # Create the main window
        window = RoadmapMaster()
        # Show the window
        window.show()
        # Close the splash screen
        splash.finish(window)
    
    # Use a timer to delay the loading of the main window
    # This allows the splash screen to be shown immediately
    QTimer.singleShot(1000, load_app)
    
    # Start the application event loop
    sys.exit(app.exec_()) 