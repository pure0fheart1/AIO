from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath, QPen, QColor

class DependencyConnector(QGraphicsPathItem):
    """
    A graphics item representing a dependency relationship between two tasks
    """
    
    def __init__(self, source_task, target_task, parent=None):
        super().__init__(parent)
        self.source_task = source_task
        self.target_task = target_task
        
        # Set up visual style
        self.setPen(QPen(QColor("#777777"), 1.5, Qt.DashLine))
        self.setZValue(-1)  # Make sure connections appear behind tasks
        
        # Update the path
        self.update_path()
    
    def update_path(self):
        """Update the connector path based on task positions"""
        if not self.source_task or not self.target_task:
            return
            
        # Get source and target positions
        source_pos = self.source_task.scenePos()
        target_pos = self.target_task.scenePos()
        
        # Calculate endpoint coordinates
        source_rect = self.source_task.boundingRect()
        target_rect = self.target_task.boundingRect()
        
        # Source point is at the right edge of the source task
        source_point = QPointF(source_pos.x() + source_rect.width(), 
                             source_pos.y())
        
        # Target point is at the left edge of the target task
        target_point = QPointF(target_pos.x(), 
                             target_pos.y())
        
        # Create a path for the connection
        path = QPainterPath()
        path.moveTo(source_point)
        
        # Calculate control points for a curved path
        ctrl1_x = source_point.x() + (target_point.x() - source_point.x()) * 0.4
        ctrl1_y = source_point.y()
        ctrl2_x = source_point.x() + (target_point.x() - source_point.x()) * 0.6
        ctrl2_y = target_point.y()
        
        # Add a cubic curve to the path
        path.cubicTo(
            QPointF(ctrl1_x, ctrl1_y),
            QPointF(ctrl2_x, ctrl2_y),
            target_point
        )
        
        # Add an arrowhead
        self.add_arrow_head(path, target_point, source_point)
        
        # Set the path
        self.setPath(path)
    
    def add_arrow_head(self, path, tip_point, source_point):
        """Add an arrowhead to the path"""
        # Calculate the direction vector
        dx = tip_point.x() - source_point.x()
        dy = tip_point.y() - source_point.y()
        
        # Normalize vector length
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            return
            
        dx /= length
        dy /= length
        
        # Calculate perpendicular vector for arrow wings
        perpx = -dy
        perpy = dx
        
        # Arrow head size
        size = 8
        
        # Calculate arrow points
        arrow_p1 = QPointF(tip_point.x() - dx * size - perpx * size/2,
                         tip_point.y() - dy * size - perpy * size/2)
        arrow_p2 = QPointF(tip_point.x() - dx * size + perpx * size/2,
                         tip_point.y() - dy * size + perpy * size/2)
        
        # Draw arrowhead
        path.moveTo(tip_point)
        path.lineTo(arrow_p1)
        path.moveTo(tip_point)
        path.lineTo(arrow_p2)
        
    def source_moved(self):
        """Handle source task movement"""
        self.update_path()
        
    def target_moved(self):
        """Handle target task movement"""
        self.update_path()
        
    def get_source_task(self):
        """Get the source task"""
        return self.source_task
    
    def get_target_task(self):
        """Get the target task"""
        return self.target_task 