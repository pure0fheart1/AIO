from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QFrame, QComboBox, QScrollArea, QPushButton,
                             QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries

from datetime import datetime, timedelta
import random

class AnalyticsPanel(QWidget):
    """
    Panel for displaying advanced analytics and visualizations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setStyleSheet("background-color: #f0f0f0;")
        header_layout = QHBoxLayout(header)
        
        header_label = QLabel("Analytics & Reporting")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.project_combo = QComboBox()
        self.project_combo.addItem("All Projects")
        self.project_combo.addItem("Website Redesign")
        self.project_combo.addItem("Product Launch")
        self.project_combo.currentIndexChanged.connect(self.update_analytics)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_analytics)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch(1)
        header_layout.addWidget(QLabel("Project:"))
        header_layout.addWidget(self.project_combo)
        header_layout.addWidget(refresh_button)
        
        # Tab widget for different analytics views
        self.tabs = QTabWidget()
        
        # Create different analytics tabs
        self.setup_overview_tab()
        self.setup_progress_tab()
        self.setup_timeline_tab()
        self.setup_task_distribution_tab()
        
        # Add widgets to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self.tabs, 1)  # 1 is the stretch factor
        
    def setup_overview_tab(self):
        """Setup the overview dashboard tab"""
        overview_tab = QScrollArea()
        overview_tab.setWidgetResizable(True)
        
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Key metrics section
        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.StyledPanel)
        metrics_layout = QGridLayout(metrics_frame)
        
        # Metric cards
        self.total_tasks_card = self.create_metric_card("Total Tasks", "24")
        self.completed_tasks_card = self.create_metric_card("Completed", "10", "#4CAF50")
        self.in_progress_card = self.create_metric_card("In Progress", "12", "#FFC107")
        self.overdue_card = self.create_metric_card("Overdue", "2", "#F44336")
        self.on_time_card = self.create_metric_card("On Time (%)", "83%", "#2196F3")
        self.avg_completion_card = self.create_metric_card("Avg. Completion", "45%", "#9C27B0")
        
        # Add metric cards to grid
        metrics_layout.addWidget(self.total_tasks_card, 0, 0)
        metrics_layout.addWidget(self.completed_tasks_card, 0, 1)
        metrics_layout.addWidget(self.in_progress_card, 0, 2)
        metrics_layout.addWidget(self.overdue_card, 1, 0)
        metrics_layout.addWidget(self.on_time_card, 1, 1)
        metrics_layout.addWidget(self.avg_completion_card, 1, 2)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Progress by project chart
        progress_chart = self.create_project_progress_chart()
        charts_layout.addWidget(progress_chart)
        
        # Task status chart
        status_chart = self.create_task_status_chart()
        charts_layout.addWidget(status_chart)
        
        # Add all sections to the tab
        overview_layout.addWidget(metrics_frame)
        overview_layout.addLayout(charts_layout)
        overview_layout.addStretch(1)
        
        overview_tab.setWidget(overview_widget)
        self.tabs.addTab(overview_tab, "Overview")
        
    def setup_progress_tab(self):
        """Setup the progress tracking tab"""
        progress_tab = QScrollArea()
        progress_tab.setWidgetResizable(True)
        
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        
        # Detailed progress table
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(5)
        self.progress_table.setHorizontalHeaderLabels(["Task", "Start Date", "End Date", "Progress", "Status"])
        self.progress_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Add sample data
        self.update_progress_table()
        
        # Add table to layout
        progress_layout.addWidget(self.progress_table)
        
        progress_tab.setWidget(progress_widget)
        self.tabs.addTab(progress_tab, "Progress Tracking")
        
    def setup_timeline_tab(self):
        """Setup the timeline analytics tab"""
        timeline_tab = QScrollArea()
        timeline_tab.setWidgetResizable(True)
        
        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout(timeline_widget)
        
        # Timeline distribution chart
        timeline_chart = self.create_timeline_distribution_chart()
        timeline_layout.addWidget(timeline_chart)
        
        # Tasks by month chart
        tasks_by_month_chart = self.create_tasks_by_month_chart()
        timeline_layout.addWidget(tasks_by_month_chart)
        
        timeline_tab.setWidget(timeline_widget)
        self.tabs.addTab(timeline_tab, "Timeline Analysis")
        
    def setup_task_distribution_tab(self):
        """Setup the task distribution tab"""
        distribution_tab = QScrollArea()
        distribution_tab.setWidgetResizable(True)
        
        distribution_widget = QWidget()
        distribution_layout = QVBoxLayout(distribution_widget)
        
        # Task type distribution chart
        type_chart = self.create_task_type_chart()
        distribution_layout.addWidget(type_chart)
        
        # Dependency complexity chart
        dependency_chart = self.create_dependency_complexity_chart()
        distribution_layout.addWidget(dependency_chart)
        
        distribution_tab.setWidget(distribution_widget)
        self.tabs.addTab(distribution_tab, "Task Distribution")
    
    def create_metric_card(self, title, value, color="#333333"):
        """Create a metric card widget"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"background-color: white; border-radius: 5px; padding: 10px;")
        card.setMinimumHeight(100)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666666;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch(1)
        
        return card
    
    def create_project_progress_chart(self):
        """Create a bar chart showing progress by project"""
        # Create chart
        chart = QChart()
        chart.setTitle("Progress by Project")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create bar series
        series = QBarSeries()
        
        # Add data
        website_set = QBarSet("Website Redesign")
        website_set.append([65])
        
        product_set = QBarSet("Product Launch")
        product_set.append([40])
        
        marketing_set = QBarSet("Marketing Campaign")
        marketing_set.append([25])
        
        series.append(website_set)
        series.append(product_set)
        series.append(marketing_set)
        
        chart.addSeries(series)
        
        # Setup axes
        categories = [""]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelFormat("%d%%")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        return chart_view
    
    def create_task_status_chart(self):
        """Create a pie chart showing task status distribution"""
        # Create chart
        chart = QChart()
        chart.setTitle("Task Status Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create pie series
        series = QPieSeries()
        
        # Add slices
        completed = series.append("Completed", 10)
        completed.setBrush(QBrush(QColor("#4CAF50")))
        
        in_progress = series.append("In Progress", 12)
        in_progress.setBrush(QBrush(QColor("#FFC107")))
        
        not_started = series.append("Not Started", 8)
        not_started.setBrush(QBrush(QColor("#2196F3")))
        
        overdue = series.append("Overdue", 2)
        overdue.setBrush(QBrush(QColor("#F44336")))
        
        # Show percentages and labels
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSeries.LabelOutside)
        
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        return chart_view
    
    def create_timeline_distribution_chart(self):
        """Create a bar chart showing task distribution over time"""
        # Create chart
        chart = QChart()
        chart.setTitle("Task Distribution Over Time")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create bar series
        series = QBarSeries()
        
        # Add data
        month1_set = QBarSet("Month 1")
        month1_set.append([5])
        
        month2_set = QBarSet("Month 2")
        month2_set.append([8])
        
        month3_set = QBarSet("Month 3")
        month3_set.append([12])
        
        month4_set = QBarSet("Month 4")
        month4_set.append([7])
        
        month5_set = QBarSet("Month 5")
        month5_set.append([4])
        
        month6_set = QBarSet("Month 6")
        month6_set.append([2])
        
        series.append(month1_set)
        series.append(month2_set)
        series.append(month3_set)
        series.append(month4_set)
        series.append(month5_set)
        series.append(month6_set)
        
        chart.addSeries(series)
        
        # Setup axes
        categories = [""]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 15)
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        return chart_view
    
    def create_tasks_by_month_chart(self):
        """Create a line chart showing tasks by month"""
        # Create chart
        chart = QChart()
        chart.setTitle("Task Deadlines by Month")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create series for each status
        completed_series = QBarSet("Completed")
        completed_series.append([2, 3, 4, 1, 0, 0])
        
        upcoming_series = QBarSet("Upcoming")
        upcoming_series.append([0, 1, 4, 6, 4, 2])
        
        overdue_series = QBarSet("Overdue")
        overdue_series.append([1, 1, 0, 0, 0, 0])
        
        # Add series to a bar series
        series = QBarSeries()
        series.append(completed_series)
        series.append(upcoming_series)
        series.append(overdue_series)
        
        chart.addSeries(series)
        
        # Setup axes
        categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 10)
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        return chart_view
    
    def create_task_type_chart(self):
        """Create a pie chart showing task type distribution"""
        # Create chart
        chart = QChart()
        chart.setTitle("Task Type Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create pie series
        series = QPieSeries()
        
        # Add slices
        design = series.append("Design", 5)
        design.setBrush(QBrush(QColor("#E91E63")))
        
        development = series.append("Development", 8)
        development.setBrush(QBrush(QColor("#2196F3")))
        
        marketing = series.append("Marketing", 6)
        marketing.setBrush(QBrush(QColor("#4CAF50")))
        
        testing = series.append("Testing", 3)
        testing.setBrush(QBrush(QColor("#FFC107")))
        
        planning = series.append("Planning", 2)
        planning.setBrush(QBrush(QColor("#9C27B0")))
        
        # Show percentages
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSeries.LabelOutside)
        
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        return chart_view
    
    def create_dependency_complexity_chart(self):
        """Create a bar chart showing dependency complexity"""
        # Create chart
        chart = QChart()
        chart.setTitle("Task Dependency Complexity")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create bar series
        series = QBarSeries()
        
        # Create data sets
        no_deps = QBarSet("No Dependencies")
        no_deps.append([8])
        
        one_dep = QBarSet("1 Dependency")
        one_dep.append([10])
        
        two_deps = QBarSet("2 Dependencies")
        two_deps.append([4])
        
        three_plus_deps = QBarSet("3+ Dependencies")
        three_plus_deps.append([2])
        
        # Add sets to series
        series.append(no_deps)
        series.append(one_dep)
        series.append(two_deps)
        series.append(three_plus_deps)
        
        chart.addSeries(series)
        
        # Setup axes
        categories = [""]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 12)
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        return chart_view
    
    def update_progress_table(self):
        """Update the progress tracking table with real or sample data"""
        # Clear existing data
        self.progress_table.setRowCount(0)
        
        # Get task data
        tasks = []
        if hasattr(self.parent_app, 'roadmap_canvas'):
            # Get actual task data from the canvas
            tasks = [item for item in self.parent_app.roadmap_canvas.timeline_view.items 
                    if hasattr(item, 'progress')]
        
        if not tasks:
            # Use sample data if no tasks available
            today = datetime.now()
            sample_tasks = [
                {"title": "Wireframes", "start": today - timedelta(days=10), "end": today + timedelta(days=5), "progress": 75},
                {"title": "UI Design", "start": today - timedelta(days=5), "end": today + timedelta(days=15), "progress": 30},
                {"title": "Frontend Dev", "start": today + timedelta(days=10), "end": today + timedelta(days=30), "progress": 0},
                {"title": "Backend Dev", "start": today + timedelta(days=10), "end": today + timedelta(days=35), "progress": 0},
                {"title": "Testing", "start": today + timedelta(days=35), "end": today + timedelta(days=45), "progress": 0},
            ]
            
            # Create tasks
            for task_data in sample_tasks:
                row = self.progress_table.rowCount()
                self.progress_table.insertRow(row)
                
                # Add task data to table
                self.progress_table.setItem(row, 0, QTableWidgetItem(task_data["title"]))
                self.progress_table.setItem(row, 1, QTableWidgetItem(task_data["start"].strftime("%Y-%m-%d")))
                self.progress_table.setItem(row, 2, QTableWidgetItem(task_data["end"].strftime("%Y-%m-%d")))
                self.progress_table.setItem(row, 3, QTableWidgetItem(f"{task_data['progress']}%"))
                
                # Determine status
                status = "Not Started"
                if task_data["progress"] == 100:
                    status = "Completed"
                elif task_data["progress"] > 0:
                    status = "In Progress"
                    
                if task_data["end"] < datetime.now() and task_data["progress"] < 100:
                    status = "Overdue"
                    
                self.progress_table.setItem(row, 4, QTableWidgetItem(status))
        else:
            # Use actual task data
            for task in tasks:
                row = self.progress_table.rowCount()
                self.progress_table.insertRow(row)
                
                # Add task data to table
                self.progress_table.setItem(row, 0, QTableWidgetItem(task.title))
                self.progress_table.setItem(row, 1, QTableWidgetItem(task.start_date.strftime("%Y-%m-%d")))
                self.progress_table.setItem(row, 2, QTableWidgetItem(task.end_date.strftime("%Y-%m-%d")))
                self.progress_table.setItem(row, 3, QTableWidgetItem(f"{task.progress}%"))
                
                # Determine status
                status = "Not Started"
                if task.progress == 100:
                    status = "Completed"
                elif task.progress > 0:
                    status = "In Progress"
                    
                if task.end_date < datetime.now() and task.progress < 100:
                    status = "Overdue"
                    
                self.progress_table.setItem(row, 4, QTableWidgetItem(status))
        
        # Adjust table appearance
        self.progress_table.resizeColumnsToContents()
        self.progress_table.resizeRowsToContents()
    
    def update_analytics(self):
        """Update all analytics based on current data"""
        # Update metric cards with real or sample data
        total_tasks = len([item for item in self.parent_app.roadmap_canvas.timeline_view.items 
                          if hasattr(item, 'progress')]) if hasattr(self.parent_app, 'roadmap_canvas') else 24
        
        completed = sum(1 for item in self.parent_app.roadmap_canvas.timeline_view.items 
                      if hasattr(item, 'progress') and item.progress == 100) if hasattr(self.parent_app, 'roadmap_canvas') else 10
        
        in_progress = sum(1 for item in self.parent_app.roadmap_canvas.timeline_view.items 
                        if hasattr(item, 'progress') and 0 < item.progress < 100) if hasattr(self.parent_app, 'roadmap_canvas') else 12
        
        overdue = sum(1 for item in self.parent_app.roadmap_canvas.timeline_view.items 
                    if hasattr(item, 'progress') and item.progress < 100 and 
                    hasattr(item, 'end_date') and item.end_date < datetime.now()) if hasattr(self.parent_app, 'roadmap_canvas') else 2
        
        on_time_percentage = int(((total_tasks - overdue) / total_tasks) * 100) if total_tasks > 0 else 83
        
        avg_completion = int(sum(item.progress for item in self.parent_app.roadmap_canvas.timeline_view.items 
                               if hasattr(item, 'progress')) / total_tasks) if hasattr(self.parent_app, 'roadmap_canvas') and total_tasks > 0 else 45
        
        # Update metric cards
        self.total_tasks_card.findChild(QLabel, "", Qt.FindDirectChildrenOnly)[1].setText(str(total_tasks))
        self.completed_tasks_card.findChild(QLabel, "", Qt.FindDirectChildrenOnly)[1].setText(str(completed))
        self.in_progress_card.findChild(QLabel, "", Qt.FindDirectChildrenOnly)[1].setText(str(in_progress))
        self.overdue_card.findChild(QLabel, "", Qt.FindDirectChildrenOnly)[1].setText(str(overdue))
        self.on_time_card.findChild(QLabel, "", Qt.FindDirectChildrenOnly)[1].setText(f"{on_time_percentage}%")
        self.avg_completion_card.findChild(QLabel, "", Qt.FindDirectChildrenOnly)[1].setText(f"{avg_completion}%")
        
        # Update the progress table
        self.update_progress_table()
        
        # Note: In a real implementation, we would also update the charts with real data 