from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QStyleOptionGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from datetime import datetime

class TaskItem(QGraphicsItem):
    """
    A graphics item representing a task with start and end date on the timeline
    """
    
    def __init__(self, title, start_date, end_date, description="", color=None, parent=None):
        super().__init__(parent)
        
        # Task properties
        self.title = title
        self.start_date = start_date if isinstance(start_date, datetime) else datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = end_date if isinstance(end_date, datetime) else datetime.strptime(end_date, "%Y-%m-%d")
        self.description = description
        self.color = QColor(color) if color else QColor("#4A86E8")  # Default to blue
        
        # Dependency tracking
        self.dependencies = []  # Tasks that this task depends on
        self.dependents = []    # Tasks that depend on this task
        self.is_critical = False  # Whether this task is on the critical path
        
        # Visual properties
        self.height = 30
        self.width = 100  # Will be calculated based on date range
        self.rounded_radius = 5
        
        # Progress
        self.progress = 0  # 0-100
        
        # Task identification
        self.id = None  # Will be set when added to the timeline
        
        # State
        self.is_selected = False
        self.is_hovered = False
        
        # Enable flags
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
    def boundingRect(self):
        """Define the bounding rectangle of the item"""
        return QRectF(0, -self.height/2, self.width, self.height)
    
    def shape(self):
        """Define the shape for hit detection"""
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), self.rounded_radius, self.rounded_radius)
        return path
    
    def paint(self, painter, option, widget=None):
        """Paint the task item"""
        # Save the current painter state
        painter.save()
        
        # Use antialiasing for smoother drawing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get the task rectangle
        rect = self.boundingRect()
        
        # Determine colors based on state
        if self.is_critical:
            # Critical path tasks get a special highlight
            border_color = QColor("#FF5252")  # Red
            border_width = 2
            bg_color = self.color.lighter(110)
        elif self.is_selected:
            border_color = QColor("#FF9900")
            border_width = 2
            bg_color = self.color.lighter(120)
        elif self.is_hovered:
            border_color = self.color.darker(110)
            border_width = 1
            bg_color = self.color.lighter(110)
        else:
            border_color = self.color.darker(110)
            border_width = 1
            bg_color = self.color
        
        # Draw the background
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, self.rounded_radius, self.rounded_radius)
        
        # Draw progress bar if progress > 0
        if self.progress > 0:
            progress_width = (self.progress / 100.0) * rect.width()
            progress_rect = QRectF(rect.left(), rect.top(), progress_width, rect.height())
            
            # Create a slightly darker color for progress
            progress_color = self.color.darker(120)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(progress_color))
            
            # Draw a rounded rect for the progress, but ensure it fits within the main rect
            if progress_width >= rect.width():
                # If 100%, just use the same rounded rect as the main one
                painter.drawRoundedRect(rect, self.rounded_radius, self.rounded_radius)
            else:
                # Otherwise, only round the left side
                progress_path = QPainterPath()
                progress_path.setFillRule(Qt.WindingFill)
                progress_path.addRoundedRect(
                    QRectF(rect.left(), rect.top(), progress_width * 2, rect.height()),
                    self.rounded_radius, self.rounded_radius
                )
                progress_path.addRect(
                    QRectF(rect.left() + progress_width, rect.top(), progress_width, rect.height())
                )
                painter.setClipRect(rect)
                painter.drawPath(progress_path)
        
        # Draw dependency indicator if this task has dependencies
        if self.dependencies:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#555555")))
            painter.drawEllipse(QPointF(5, -self.height/2 - 5), 3, 3)
        
        # Draw dependent indicator if other tasks depend on this
        if self.dependents:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#555555")))
            painter.drawEllipse(QPointF(rect.width() - 5, -self.height/2 - 5), 3, 3)
        
        # Draw critical path indicator if on critical path
        if self.is_critical:
            # Add a small critical path icon
            critical_path_icon_rect = QRectF(rect.right() - 15, rect.top() - 15, 10, 10)
            painter.setPen(QPen(QColor("#FF5252"), 1))
            painter.setBrush(QBrush(QColor("#FF5252")))
            painter.drawEllipse(critical_path_icon_rect)
                
        # Draw title text
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        
        # Determine text color - use white if background is dark, black if light
        luminance = (0.299 * self.color.red() + 0.587 * self.color.green() + 0.114 * self.color.blue()) / 255
        if luminance < 0.5:
            text_color = QColor(255, 255, 255)  # White text for dark background
        else:
            text_color = QColor(0, 0, 0)  # Black text for light background
            
        painter.setPen(QPen(text_color))
        
        # Draw text with a small margin
        text_rect = QRectF(rect.left() + 5, rect.top(), rect.width() - 10, rect.height())
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.title)
        
        # Restore the painter state
        painter.restore()
    
    def hoverEnterEvent(self, event):
        """Handle hover enter events"""
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave events"""
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        self.is_selected = True
        self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        super().mouseReleaseEvent(event)
        
    def itemChange(self, change, value):
        """Handle item changes, such as selection state"""
        if change == QGraphicsItem.ItemSelectedChange:
            self.is_selected = bool(value)
            self.update()
        
        return super().itemChange(change, value)
    
    def set_position(self, pos):
        """Set the position of the task"""
        self.setPos(pos)
    
    def set_width(self, width):
        """Set the width of the task based on date range"""
        self.width = max(width, 50)  # Ensure minimum width
        self.update()
    
    def set_title(self, title):
        """Set the title of the task"""
        self.title = title
        self.update()
    
    def set_dates(self, start_date, end_date):
        """Set the start and end dates of the task"""
        self.start_date = start_date if isinstance(start_date, datetime) else datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = end_date if isinstance(end_date, datetime) else datetime.strptime(end_date, "%Y-%m-%d")
        self.update()
    
    def set_color(self, color):
        """Set the color of the task"""
        self.color = QColor(color)
        self.update()
    
    def set_progress(self, progress):
        """Set the progress of the task (0-100)"""
        self.progress = max(0, min(100, progress))  # Clamp between 0-100
        self.update()
        
    def add_dependency(self, task):
        """Add a task that this task depends on"""
        if task not in self.dependencies and task != self:
            self.dependencies.append(task)
            task.dependents.append(self)
            self.update()
            
    def remove_dependency(self, task):
        """Remove a dependency"""
        if task in self.dependencies:
            self.dependencies.remove(task)
            if self in task.dependents:
                task.dependents.remove(self)
            self.update()
    
    def clear_dependencies(self):
        """Clear all dependencies"""
        for dep in self.dependencies[:]:
            self.remove_dependency(dep)
    
    def get_dependencies(self):
        """Get all dependencies of this task"""
        return self.dependencies
    
    def get_dependents(self):
        """Get all tasks that depend on this task"""
        return self.dependents
    
    def get_earliest_start(self):
        """Calculate the earliest start date based on dependencies"""
        if not self.dependencies:
            return self.start_date
        
        # Find the latest end date among dependencies
        latest_end = max(dep.end_date for dep in self.dependencies)
        
        # Determine if our start date needs to be adjusted
        if latest_end > self.start_date:
            return latest_end
        
        return self.start_date
    
    def get_duration_days(self):
        """Get the duration of the task in days"""
        return (self.end_date - self.start_date).days + 1  # Include both start and end days
    
    def set_critical(self, is_critical):
        """Set whether this task is on the critical path"""
        self.is_critical = is_critical
        self.update()
    
    def is_on_critical_path(self):
        """Check if this task is on the critical path"""
        return self.is_critical 