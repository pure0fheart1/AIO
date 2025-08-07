from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsTextItem, QStyleOptionGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from datetime import datetime

class MilestoneItem(QGraphicsItem):
    """
    A graphics item representing a milestone on the timeline
    """
    
    def __init__(self, title, date, description="", color=None, parent=None):
        super().__init__(parent)
        
        # Milestone properties
        self.title = title
        self.date = date if isinstance(date, datetime) else datetime.strptime(date, "%Y-%m-%d")
        self.description = description
        self.color = QColor(color) if color else QColor("#4A86E8")  # Default to blue
        
        # Visual properties
        self.radius = 10
        self.width = 150
        self.height = 50
        self.text_padding = 5
        
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
        return QRectF(-self.radius, -self.radius, 
                     self.width + (2 * self.radius), self.height + (2 * self.radius))
    
    def shape(self):
        """Define the shape for hit detection"""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    def paint(self, painter, option, widget=None):
        """Paint the milestone item"""
        # Save the current painter state
        painter.save()
        
        # Use antialiasing for smoother drawing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the milestone marker (circle)
        if self.is_selected:
            # Draw a selection highlight
            painter.setPen(QPen(QColor("#FF9900"), 2))
            painter.setBrush(QBrush(self.color.lighter(110)))
            painter.drawEllipse(QPointF(0, 0), self.radius + 2, self.radius + 2)
        else:
            # Standard or hover state
            pen_color = self.color.darker(110)
            brush_color = self.color.lighter(110) if self.is_hovered else self.color
            
            painter.setPen(QPen(pen_color, 1))
            painter.setBrush(QBrush(brush_color))
            painter.drawEllipse(QPointF(0, 0), self.radius, self.radius)
        
        # Draw the milestone label
        text_rect = QRectF(self.radius + self.text_padding, -self.height/2,
                         self.width - (self.radius + self.text_padding), self.height)
        
        # Draw text background
        if self.is_selected or self.is_hovered:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(245, 245, 245, 200)))
            painter.drawRoundedRect(text_rect, 5, 5)
        
        # Set up font
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        # Draw title
        painter.setPen(QPen(QColor("#333333")))
        title_rect = QRectF(text_rect.left(), text_rect.top(), 
                         text_rect.width(), text_rect.height() / 2)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, self.title)
        
        # Draw date
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#666666")))
        date_rect = QRectF(text_rect.left(), text_rect.top() + text_rect.height() / 2, 
                          text_rect.width(), text_rect.height() / 2)
        date_str = self.date.strftime("%d %b %Y")
        painter.drawText(date_rect, Qt.AlignLeft | Qt.AlignTop, date_str)
        
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
        """Set the position of the milestone"""
        self.setPos(pos)
    
    def set_title(self, title):
        """Set the title of the milestone"""
        self.title = title
        self.update()
    
    def set_date(self, date):
        """Set the date of the milestone"""
        self.date = date if isinstance(date, datetime) else datetime.strptime(date, "%Y-%m-%d")
        self.update()
    
    def set_color(self, color):
        """Set the color of the milestone"""
        self.color = QColor(color)
        self.update() 