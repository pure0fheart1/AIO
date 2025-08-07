from PyQt5.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem,
                             QGraphicsTextItem, QStyleOptionGraphicsItem)
from PyQt5.QtCore import Qt, QRectF, QPointF, QDate, QDateTime, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from datetime import datetime, timedelta
from dependency_connector import DependencyConnector

class TimelineView(QGraphicsView):
    """
    A custom view widget for displaying roadmap items on a timeline
    """
    
    # Signals
    item_selected = pyqtSignal(object)
    item_moved = pyqtSignal(object, QPointF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create a scene to hold the graphics items
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Default settings
        self.zoom_factor = 1.0
        self.time_scale = "month"  # day, week, month, quarter, year
        
        # Visual parameters
        self.timeline_height = 50
        self.header_height = 60
        self.row_height = 80
        self.horizontal_padding = 50
        
        # Date range (start with a default 1-year range)
        self.start_date = datetime.now().replace(day=1)  # Start on the first of the current month
        self.end_date = self.start_date + timedelta(days=365)  # Default to one year
        
        # Item tracking
        self.items = []
        self.dependency_connectors = []
        
        # Performance optimizations
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.setCacheMode(QGraphicsView.CacheBackground)
        
        # Initialize the timeline
        self.initialize_timeline()
        
        # Setup view properties
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # Dependency creation mode
        self.dependency_mode = False
        self.source_task = None
        
    def initialize_timeline(self):
        """Initialize the timeline with grid lines and markers"""
        self.scene.clear()
        
        # Calculate timeline dimensions
        timeline_width = self.calculate_timeline_width()
        total_height = self.header_height + (len(self.items) * self.row_height) + 100
        
        # Set the scene rectangle
        self.scene.setSceneRect(0, 0, timeline_width, total_height)
        
        # Draw timeline header background
        header_rect = QGraphicsRectItem(0, 0, timeline_width, self.header_height)
        header_rect.setBrush(QBrush(QColor("#f5f5f5")))
        header_rect.setPen(QPen(QColor("#dddddd")))
        self.scene.addItem(header_rect)
        
        # Draw timeline header with date markers
        self.draw_timeline_header()
        
        # Draw grid lines
        self.draw_grid_lines(timeline_width, total_height)
        
        # Reset dependency connectors list
        self.dependency_connectors = []
        
        # Draw roadmap items
        self.draw_items()
        
        # Draw dependencies between tasks
        self.draw_dependencies()
    
    def calculate_timeline_width(self):
        """Calculate the width of the timeline based on date range and zoom"""
        date_range_days = (self.end_date - self.start_date).days
        
        # Base width calculation depends on the time scale
        if self.time_scale == "day":
            base_width = date_range_days * 30  # 30 pixels per day
        elif self.time_scale == "week":
            base_width = (date_range_days / 7) * 100  # 100 pixels per week
        elif self.time_scale == "month":
            base_width = (date_range_days / 30) * 150  # 150 pixels per month
        elif self.time_scale == "quarter":
            base_width = (date_range_days / 90) * 200  # 200 pixels per quarter
        elif self.time_scale == "year":
            base_width = (date_range_days / 365) * 400  # 400 pixels per year
        else:
            base_width = date_range_days * 2  # Fallback
        
        # Apply zoom factor
        return base_width * self.zoom_factor + (2 * self.horizontal_padding)
    
    def draw_timeline_header(self):
        """Draw the timeline header with date markers"""
        # The specific implementation depends on the time scale
        if self.time_scale == "day":
            self.draw_daily_timeline_header()
        elif self.time_scale == "week":
            self.draw_weekly_timeline_header()
        elif self.time_scale == "month":
            self.draw_monthly_timeline_header()
        elif self.time_scale == "quarter":
            self.draw_quarterly_timeline_header()
        elif self.time_scale == "year":
            self.draw_yearly_timeline_header()
    
    def draw_monthly_timeline_header(self):
        """Draw timeline header with month markers"""
        # Start at the first day of the month for the start date
        current_date = self.start_date.replace(day=1)
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw month label
            month_label = current_date.strftime("%b %Y")
            text_item = QGraphicsTextItem(month_label)
            text_item.setPos(x_pos, 10)
            self.scene.addItem(text_item)
            
            # Draw marker line
            line_item = QGraphicsLineItem(x_pos, self.header_height - 5, x_pos, self.header_height)
            line_item.setPen(QPen(QColor("#666666")))
            self.scene.addItem(line_item)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def draw_daily_timeline_header(self):
        """Draw timeline header with day markers"""
        # Simplified implementation - in a real app this would show appropriate day markers
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Every 5 days, draw a more prominent marker
            if current_date.day % 5 == 0:
                date_label = current_date.strftime("%d")
                text_item = QGraphicsTextItem(date_label)
                text_item.setPos(x_pos, 10)
                self.scene.addItem(text_item)
                
                line_item = QGraphicsLineItem(x_pos, self.header_height - 10, x_pos, self.header_height)
                line_item.setPen(QPen(QColor("#666666")))
                self.scene.addItem(line_item)
            
            # Move to next day
            current_date += timedelta(days=1)
    
    def draw_weekly_timeline_header(self):
        """Draw timeline header with week markers"""
        # Start at the first day of the week for the start date
        current_date = self.start_date - timedelta(days=self.start_date.weekday())
        
        week_num = 1
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw week label
            week_label = f"Week {week_num}"
            text_item = QGraphicsTextItem(week_label)
            text_item.setPos(x_pos, 10)
            
            # Add date range for the week
            week_range = f"{current_date.strftime('%d %b')} - {(current_date + timedelta(days=6)).strftime('%d %b')}"
            date_item = QGraphicsTextItem(week_range)
            date_item.setPos(x_pos, 30)
            
            self.scene.addItem(text_item)
            self.scene.addItem(date_item)
            
            # Draw marker line
            line_item = QGraphicsLineItem(x_pos, self.header_height - 5, x_pos, self.header_height)
            line_item.setPen(QPen(QColor("#666666")))
            self.scene.addItem(line_item)
            
            # Move to next week
            current_date += timedelta(days=7)
            week_num += 1
    
    def draw_quarterly_timeline_header(self):
        """Draw timeline header with quarter markers"""
        # Start at the first day of the quarter for the start date
        month = ((self.start_date.month - 1) // 3) * 3 + 1
        current_date = self.start_date.replace(day=1, month=month)
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw quarter label
            quarter = (current_date.month - 1) // 3 + 1
            quarter_label = f"Q{quarter} {current_date.year}"
            text_item = QGraphicsTextItem(quarter_label)
            text_item.setPos(x_pos, 10)
            self.scene.addItem(text_item)
            
            # Draw marker line
            line_item = QGraphicsLineItem(x_pos, self.header_height - 5, x_pos, self.header_height)
            line_item.setPen(QPen(QColor("#666666")))
            self.scene.addItem(line_item)
            
            # Move to next quarter
            month = current_date.month
            if month >= 10:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=month + 3)
    
    def draw_yearly_timeline_header(self):
        """Draw timeline header with year markers"""
        # Start at January 1 of the start year
        current_date = self.start_date.replace(day=1, month=1)
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw year label
            year_label = str(current_date.year)
            text_item = QGraphicsTextItem(year_label)
            text_item.setPos(x_pos, 10)
            self.scene.addItem(text_item)
            
            # Draw marker line
            line_item = QGraphicsLineItem(x_pos, self.header_height - 5, x_pos, self.header_height)
            line_item.setPen(QPen(QColor("#666666")))
            self.scene.addItem(line_item)
            
            # Move to next year
            current_date = current_date.replace(year=current_date.year + 1)
    
    def draw_grid_lines(self, width, height):
        """Draw horizontal and vertical grid lines"""
        # Draw horizontal grid lines
        y = self.header_height
        
        # Add horizontal line at the top of the items area
        line_item = QGraphicsLineItem(0, y, width, y)
        line_item.setPen(QPen(QColor("#dddddd")))
        self.scene.addItem(line_item)
        
        # Add horizontal lines for each row
        for i in range(len(self.items) + 1):
            y += self.row_height
            line_item = QGraphicsLineItem(0, y, width, y)
            line_item.setPen(QPen(QColor("#eeeeee")))
            self.scene.addItem(line_item)
        
        # Draw vertical grid lines based on the time scale
        if self.time_scale == "day":
            self.draw_daily_grid_lines(height)
        elif self.time_scale == "week":
            self.draw_weekly_grid_lines(height)
        elif self.time_scale == "month":
            self.draw_monthly_grid_lines(height)
        elif self.time_scale == "quarter":
            self.draw_quarterly_grid_lines(height)
        elif self.time_scale == "year":
            self.draw_yearly_grid_lines(height)
    
    def draw_monthly_grid_lines(self, height):
        """Draw vertical grid lines for months"""
        current_date = self.start_date.replace(day=1)
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw grid line
            line_item = QGraphicsLineItem(x_pos, self.header_height, x_pos, height)
            line_item.setPen(QPen(QColor("#eeeeee")))
            self.scene.addItem(line_item)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def draw_daily_grid_lines(self, height):
        """Draw vertical grid lines for days"""
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw grid line (make every Sunday/first of month more visible)
            line_item = QGraphicsLineItem(x_pos, self.header_height, x_pos, height)
            
            if current_date.weekday() == 6 or current_date.day == 1:  # Sunday or first of month
                line_item.setPen(QPen(QColor("#dddddd")))
            else:
                line_item.setPen(QPen(QColor("#f5f5f5")))
                
            self.scene.addItem(line_item)
            
            # Move to next day
            current_date += timedelta(days=1)
    
    def draw_weekly_grid_lines(self, height):
        """Draw vertical grid lines for weeks"""
        # Start at the first day of the week for the start date
        current_date = self.start_date - timedelta(days=self.start_date.weekday())
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw grid line
            line_item = QGraphicsLineItem(x_pos, self.header_height, x_pos, height)
            
            # First of month gets a more visible line
            if current_date.day <= 7 and current_date.weekday() == 0:
                line_item.setPen(QPen(QColor("#dddddd")))
            else:
                line_item.setPen(QPen(QColor("#eeeeee")))
                
            self.scene.addItem(line_item)
            
            # Move to next week
            current_date += timedelta(days=7)
    
    def draw_quarterly_grid_lines(self, height):
        """Draw vertical grid lines for quarters"""
        # Start at the first day of the quarter for the start date
        month = ((self.start_date.month - 1) // 3) * 3 + 1
        current_date = self.start_date.replace(day=1, month=month)
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw grid line
            line_item = QGraphicsLineItem(x_pos, self.header_height, x_pos, height)
            line_item.setPen(QPen(QColor("#dddddd")))
            self.scene.addItem(line_item)
            
            # Also add month grid lines within the quarter
            for i in range(1, 3):
                month_date = current_date.replace(month=current_date.month + i) if current_date.month + i <= 12 else \
                             current_date.replace(year=current_date.year + 1, month=(current_date.month + i) % 12)
                
                if month_date <= self.end_date:
                    month_x = self.date_to_x_position(month_date)
                    month_line = QGraphicsLineItem(month_x, self.header_height, month_x, height)
                    month_line.setPen(QPen(QColor("#eeeeee")))
                    self.scene.addItem(month_line)
            
            # Move to next quarter
            month = current_date.month
            if month >= 10:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=month + 3)
    
    def draw_yearly_grid_lines(self, height):
        """Draw vertical grid lines for years"""
        # Start at January 1 of the start year
        current_date = self.start_date.replace(day=1, month=1)
        
        while current_date <= self.end_date:
            # Calculate x position
            x_pos = self.date_to_x_position(current_date)
            
            # Draw grid line
            line_item = QGraphicsLineItem(x_pos, self.header_height, x_pos, height)
            line_item.setPen(QPen(QColor("#dddddd")))
            self.scene.addItem(line_item)
            
            # Also add quarter grid lines
            for quarter in range(1, 4):
                quarter_date = current_date.replace(month=quarter * 3 + 1)
                if quarter_date <= self.end_date:
                    quarter_x = self.date_to_x_position(quarter_date)
                    quarter_line = QGraphicsLineItem(quarter_x, self.header_height, quarter_x, height)
                    quarter_line.setPen(QPen(QColor("#eeeeee")))
                    self.scene.addItem(quarter_line)
            
            # Move to next year
            current_date = current_date.replace(year=current_date.year + 1)
    
    def draw_items(self):
        """Draw all roadmap items on the timeline"""
        # Clear any task IDs before redrawing
        task_index = 0
        
        for i, item in enumerate(self.items):
            y = self.header_height + (i * self.row_height)
            
            # Adjust item position based on its date
            if hasattr(item, 'date'):
                # Milestone-type item with a single date
                x = self.date_to_x_position(item.date)
                item.set_position(QPointF(x, y + self.row_height // 2))
            elif hasattr(item, 'start_date') and hasattr(item, 'end_date'):
                # Task-type item with start and end dates
                # Set ID if it doesn't have one
                if item.id is None:
                    item.id = f"task_{task_index}"
                    task_index += 1
                
                # For tasks with dependencies, use the earliest possible start date
                if hasattr(item, 'get_earliest_start') and item.dependencies:
                    earliest_start = item.get_earliest_start()
                    duration = item.get_duration_days()
                    end_date = earliest_start + timedelta(days=duration - 1)
                    item.set_dates(earliest_start, end_date)
                
                x1 = self.date_to_x_position(item.start_date)
                x2 = self.date_to_x_position(item.end_date)
                item.set_position(QPointF(x1, y + self.row_height // 2))
                item.set_width(x2 - x1)
            
            # Add the item to the scene
            self.scene.addItem(item)
            
    def draw_dependencies(self):
        """Draw dependency arrows between tasks"""
        for item in self.items:
            # Skip items that don't have dependencies
            if not hasattr(item, 'dependencies') or not item.dependencies:
                continue
                
            # Create connectors for each dependency
            for dep in item.dependencies:
                connector = DependencyConnector(dep, item)
                self.scene.addItem(connector)
                self.dependency_connectors.append(connector)
                
    def date_to_x_position(self, date):
        """Convert a date to an x-coordinate on the timeline"""
        if isinstance(date, str):
            # Parse date string to datetime object
            date = datetime.strptime(date, "%Y-%m-%d")
        
        # Calculate days from start date
        delta_days = (date - self.start_date).days
        
        # Calculate position based on time scale and zoom
        if self.time_scale == "day":
            x = delta_days * 30 * self.zoom_factor  # 30 pixels per day
        elif self.time_scale == "week":
            x = (delta_days / 7) * 100 * self.zoom_factor  # 100 pixels per week
        elif self.time_scale == "month":
            x = (delta_days / 30) * 150 * self.zoom_factor  # 150 pixels per month
        elif self.time_scale == "quarter":
            x = (delta_days / 90) * 200 * self.zoom_factor  # 200 pixels per quarter
        elif self.time_scale == "year":
            x = (delta_days / 365) * 400 * self.zoom_factor  # 400 pixels per year
        else:
            x = delta_days * 2 * self.zoom_factor  # Fallback
        
        # Add horizontal padding
        return x + self.horizontal_padding
                
    def add_item(self, item):
        """Add a roadmap item to the timeline"""
        self.items.append(item)
        self.initialize_timeline()
        return item
    
    def remove_item(self, item):
        """Remove a roadmap item from the timeline"""
        if item in self.items:
            # Clear dependencies if it's a task
            if hasattr(item, 'clear_dependencies'):
                # Remove dependencies to this task
                for other_item in self.items:
                    if hasattr(other_item, 'remove_dependency'):
                        if item in other_item.dependencies:
                            other_item.remove_dependency(item)
                
                # Clear this task's dependencies
                item.clear_dependencies()
            
            self.items.remove(item)
            self.initialize_timeline()
    
    def clear(self):
        """Clear all items from the timeline"""
        self.items.clear()
        self.dependency_connectors.clear()
        self.initialize_timeline()
    
    def set_zoom(self, factor):
        """Set the zoom level of the timeline"""
        self.zoom_factor = factor
        self.initialize_timeline()
    
    def set_time_scale(self, scale):
        """Set the time scale of the timeline"""
        self.time_scale = scale
        self.initialize_timeline()
    
    def set_date_range(self, start_date, end_date):
        """Set the date range of the timeline"""
        self.start_date = start_date
        self.end_date = end_date
        self.initialize_timeline()
    
    def enable_dependency_mode(self, enabled):
        """Enable or disable dependency creation mode"""
        self.dependency_mode = enabled
        self.source_task = None
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)
    
    def is_dependency_mode_enabled(self):
        """Check if dependency mode is enabled"""
        return self.dependency_mode
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if self.dependency_mode and event.button() == Qt.LeftButton:
            # Get the item under the mouse
            pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(pos, self.transform())
            
            # Check if it's a task
            if item and hasattr(item, 'dependencies'):
                if not self.source_task:
                    # First click - select source task
                    self.source_task = item
                    self.source_task.is_selected = True
                    self.source_task.update()
                else:
                    # Second click - select target task and create dependency
                    target_task = item
                    
                    # Don't allow self-dependencies or duplicates
                    if target_task != self.source_task and target_task not in self.source_task.dependents:
                        target_task.add_dependency(self.source_task)
                        
                        # Redraw the timeline to show the new dependency
                        self.initialize_timeline()
                        
                        # Run critical path analysis after adding a dependency
                        self.analyze_critical_path()
                    
                    # Reset for next dependency
                    self.source_task.is_selected = False
                    self.source_task.update()
                    self.source_task = None
            else:
                # Clicked on empty space or non-task item
                if self.source_task:
                    self.source_task.is_selected = False
                    self.source_task.update()
                    self.source_task = None
        else:
            # Normal mouse handling
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if not self.dependency_mode:
            # Normal mouse handling
            super().mouseReleaseEvent(event)
            
            # Run critical path analysis after item movement
            self.analyze_critical_path()
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Save the scene pos
        old_pos = self.mapToScene(event.pos())
        
        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        # Apply zoom to the view
        self.scale(zoom_factor, zoom_factor)
        
        # Get the new position
        new_pos = self.mapToScene(event.pos())
        
        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
    def analyze_critical_path(self):
        """Calculate and visualize the critical path"""
        # First, reset critical status for all tasks
        for item in self.items:
            if hasattr(item, 'set_critical'):
                item.set_critical(False)
        
        # Get all tasks (skip milestones)
        tasks = [item for item in self.items if hasattr(item, 'dependencies')]
        if not tasks:
            return
            
        # Find tasks with no dependents (end tasks)
        end_tasks = [task for task in tasks if not task.dependents]
        if not end_tasks:
            # If no end tasks, use the task with the latest end date
            end_tasks = [max(tasks, key=lambda t: t.end_date)]
            
        # Find tasks with no dependencies (start tasks)
        start_tasks = [task for task in tasks if not task.dependencies]
        if not start_tasks:
            # If no start tasks, use the task with the earliest start date
            start_tasks = [min(tasks, key=lambda t: t.start_date)]
        
        # Calculate earliest start and finish times for each task
        earliest_start = {}
        earliest_finish = {}
        
        # Forward pass
        for task in tasks:
            if not task.dependencies:
                earliest_start[task.id] = task.start_date
            else:
                # Task's earliest start is the maximum of predecessor finish times
                predecessor_finish_times = [earliest_finish[dep.id] for dep in task.dependencies 
                                         if dep.id in earliest_finish]
                if predecessor_finish_times:
                    earliest_start[task.id] = max(predecessor_finish_times)
                else:
                    earliest_start[task.id] = task.start_date
            
            # Earliest finish = earliest start + duration
            duration = task.get_duration_days()
            earliest_finish[task.id] = earliest_start[task.id] + timedelta(days=duration - 1)
        
        # Calculate latest start and finish times
        latest_start = {}
        latest_finish = {}
        
        # Set the project end time as the latest finish of end tasks
        project_end = max(earliest_finish[task.id] for task in end_tasks)
        
        # Backward pass
        for task in reversed(tasks):
            if not task.dependents:
                latest_finish[task.id] = project_end
            else:
                # Task's latest finish is the minimum of successor start times
                successor_start_times = [latest_start[succ.id] for succ in task.dependents
                                      if succ.id in latest_start]
                if successor_start_times:
                    latest_finish[task.id] = min(successor_start_times)
                else:
                    latest_finish[task.id] = project_end
            
            # Latest start = latest finish - duration
            duration = task.get_duration_days()
            latest_start[task.id] = latest_finish[task.id] - timedelta(days=duration - 1)
        
        # Calculate slack time for each task
        slack = {}
        for task in tasks:
            slack[task.id] = (latest_start[task.id] - earliest_start[task.id]).days
        
        # Identify critical path (tasks with zero slack)
        for task in tasks:
            if slack[task.id] == 0:
                task.set_critical(True) 