from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QColorDialog, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPathItem, QSizePolicy, QFileDialog, QMessageBox
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QIcon, QImage, QPixmap
from PyQt5.QtCore import Qt, QPointF, QRectF
import traceback # Import traceback for detailed error logging

class WhiteboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WhiteboardPage")
        self.drawing = False
        self.last_point = QPointF()
        self.pen_color = Qt.black
        self.pen_width = 3  # Default pen width

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Toolbar for drawing tools
        toolbar_layout = QHBoxLayout()

        self.pen_color_button = QPushButton("Pen Color")
        self.pen_color_button.setIcon(QIcon.fromTheme("applications-graphics")) # Placeholder icon
        self.pen_color_button.clicked.connect(self.select_pen_color)
        toolbar_layout.addWidget(self.pen_color_button)

        self.eraser_button = QPushButton("Eraser")
        self.eraser_button.setIcon(QIcon.fromTheme("edit-clear")) # Placeholder icon
        self.eraser_button.clicked.connect(self.select_eraser)
        toolbar_layout.addWidget(self.eraser_button)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setIcon(QIcon.fromTheme("document-new")) # Placeholder icon
        self.clear_button.clicked.connect(self.clear_canvas)
        toolbar_layout.addWidget(self.clear_button)

        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.setIcon(QIcon.fromTheme("zoom-in"))
        self.zoom_in_button.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.setIcon(QIcon.fromTheme("zoom-out"))
        self.zoom_out_button.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(self.zoom_out_button)

        self.save_button = QPushButton("Save")
        self.save_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_button.clicked.connect(self.save_canvas)
        toolbar_layout.addWidget(self.save_button)

        toolbar_layout.addStretch() # Pushes buttons to the left

        # Graphics Scene and View for drawing
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.white) # White background

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.NoDrag) # Important for drawing
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Install event filter on the view to capture mouse events for drawing
        self.view.viewport().installEventFilter(self)

        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.view)

        self.setLayout(main_layout)

    def select_pen_color(self):
        color = QColorDialog.getColor(self.pen_color, self, "Select Pen Color")
        if color.isValid():
            self.pen_color = color
            # Potentially update pen width if we add a width selector
            # For now, eraser sets width to a larger value. Reset if not eraser.
            if self.pen_color != self.scene.backgroundBrush().color(): # If not eraser color
                 self.pen_width = 3


    def select_eraser(self):
        # Eraser is just drawing with the background color
        self.pen_color = self.scene.backgroundBrush().color()
        self.pen_width = 20 # Make eraser thicker


    def clear_canvas(self):
        self.scene.clear()
        # Re-set background if needed, though clear() usually doesn't remove it
        self.scene.setBackgroundBrush(Qt.white)

    def zoom_in(self):
        self.view.scale(1.2, 1.2)

    def zoom_out(self):
        self.view.scale(1 / 1.2, 1 / 1.2)

    def save_canvas(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Whiteboard",
            "",  # Default directory (user's last used or OS default)
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;Bitmap Image (*.bmp)" # Standard filter names
        )

        if not file_path:
            return  # User cancelled

        try:
            scene_rect = self.scene.itemsBoundingRect()
            target_width = 0
            target_height = 0
            render_source_rect = QRectF() # The part of the scene to render

            if scene_rect.isEmpty():
                # For an empty scene, use the viewport's current size or a default
                vp_size = self.view.viewport().size()
                target_width = vp_size.width() if vp_size.width() > 0 else 800
                target_height = vp_size.height() if vp_size.height() > 0 else 600
                # For an empty scene, the source rect for rendering is just a blank area of this size
                render_source_rect = QRectF(0, 0, target_width, target_height)
            else:
                # For non-empty scene, use itemsBoundingRect with padding
                padded_scene_rect = scene_rect.adjusted(-20, -20, 20, 20)
                target_width = int(padded_scene_rect.width())
                target_height = int(padded_scene_rect.height())
                render_source_rect = padded_scene_rect

            if target_width <= 0 or target_height <= 0:
                QMessageBox.warning(self, "Save Failed", f"Cannot save an image with invalid dimensions: {target_width}x{target_height}.")
                return

            image = QImage(target_width, target_height, QImage.Format_ARGB32_Premultiplied)
            if image.isNull():
                QMessageBox.critical(self, "Save Error", "Failed to create image for saving (low memory or invalid size).")
                return

            # Fill image with the scene's background color.
            # self.scene.setBackgroundBrush(Qt.white) is called in setup_ui and clear_canvas
            image.fill(self.scene.backgroundBrush().color()) # Should be white
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Render the scene content.
            # The target area on the image is the entire image.
            # The source area from the scene is render_source_rect.
            self.scene.render(painter, QRectF(0, 0, target_width, target_height), render_source_rect)
            painter.end()

            if image.save(file_path):
                QMessageBox.information(self, "Save Successful", f"Whiteboard saved to {file_path}")
            else:
                QMessageBox.warning(self, "Save Failed", f"Could not save the whiteboard image to '{file_path}'.\nCheck file permissions, path, and ensure sufficient disk space.")
        
        except Exception as e:
            error_str = traceback.format_exc()
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred while saving:\n{str(e)}\n\nDetails:\n{error_str}")
            print(f"Error saving whiteboard: {e}\n{error_str}")

    def eventFilter(self, source, event):
        if source == self.view.viewport():
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.drawing = True
                    self.last_point = self.view.mapToScene(event.pos())
                    # Create a new path item for this stroke
                    self.current_path_item = QGraphicsPathItem()
                    pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    self.current_path_item.setPen(pen)
                    self.scene.addItem(self.current_path_item)
                    
                    # Start the path at the current point
                    path = QPainterPath(self.last_point)
                    self.current_path_item.setPath(path)
                    return True
            elif event.type() == event.MouseMove:
                if self.drawing and event.buttons() & Qt.LeftButton:
                    current_point = self.view.mapToScene(event.pos())
                    if self.current_path_item:
                        path = self.current_path_item.path()
                        path.lineTo(current_point)
                        self.current_path_item.setPath(path)
                    self.last_point = current_point
                    return True
            elif event.type() == event.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self.drawing:
                    self.drawing = False
                    self.current_path_item = None # Finalize current path item
                    return True
        return super().eventFilter(source, event)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    whiteboard = WhiteboardPage()
    layout.addWidget(whiteboard)
    window.resize(800, 600)
    window.setWindowTitle("Whiteboard Page Test")
    window.show()
    sys.exit(app.exec_()) 