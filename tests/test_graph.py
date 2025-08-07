import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow
try:
    from graph_manager import DataGraphWidget
    print("Import successful")
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    graph_widget = DataGraphWidget()
    window.setCentralWidget(graph_widget)
    window.setWindowTitle("Graph Test")
    window.resize(800, 600)
    window.show()
    
    print("Application started")
    sys.exit(app.exec_())
except Exception as e:
    print(f"Error: {str(e)}")
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1) 