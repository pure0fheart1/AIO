import sys
import numpy as np
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLineEdit, QLabel, QFormLayout)

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    
    class SimpleMplCanvas(FigureCanvas):
        def __init__(self, parent=None, width=5, height=4, dpi=100):
            fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = fig.add_subplot(111)
            
            super(SimpleMplCanvas, self).__init__(fig)
            self.setParent(parent)
            
            self.plot_example()
            
        def plot_example(self):
            # Generate some example data
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            
            # Plot the data
            self.axes.plot(x, y)
            self.axes.set_title('Sample Sine Wave')
            self.axes.set_xlabel('X axis')
            self.axes.set_ylabel('Y axis')
            self.axes.grid(True)
    
    class GraphWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Simple Graph Viewer")
            self.resize(800, 600)
            
            # Create central widget and layout
            central_widget = QWidget()
            layout = QVBoxLayout(central_widget)
            
            # Add form for data input
            form_layout = QFormLayout()
            self.title_input = QLineEdit("Sample Graph")
            form_layout.addRow("Title:", self.title_input)
            
            # Add button to update graph
            update_btn = QPushButton("Update Graph")
            update_btn.clicked.connect(self.update_graph)
            
            # Create matplotlib canvas
            self.canvas = SimpleMplCanvas(self)
            
            # Add widgets to layout
            layout.addLayout(form_layout)
            layout.addWidget(update_btn)
            layout.addWidget(self.canvas)
            
            # Set central widget
            self.setCentralWidget(central_widget)
        
        def update_graph(self):
            # Clear the axes
            self.canvas.axes.clear()
            
            # Generate new data
            x = np.linspace(0, 10, 100)
            y = np.cos(x)
            
            # Plot the data
            self.canvas.axes.plot(x, y)
            self.canvas.axes.set_title(self.title_input.text())
            self.canvas.axes.set_xlabel('X axis')
            self.canvas.axes.set_ylabel('Y axis')
            self.canvas.axes.grid(True)
            
            # Redraw the canvas
            self.canvas.draw()
    
    # Create the application
    app = QApplication(sys.argv)
    window = GraphWindow()
    window.show()
    
    print("Application started")
    sys.exit(app.exec_())
    
except Exception as e:
    print(f"Error: {str(e)}")
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1) 