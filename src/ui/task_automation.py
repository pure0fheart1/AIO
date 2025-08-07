import os
import json
import time
import datetime
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTextEdit, QLineEdit, QListWidget, QSplitter, QFrame,
                            QScrollArea, QMessageBox, QFileDialog, QDialog, QFormLayout,
                            QCheckBox, QSpinBox, QGroupBox, QInputDialog, QListWidgetItem,
                            QTabWidget, QComboBox, QRadioButton, QButtonGroup, QMenu, QSlider)
from PyQt5.QtCore import Qt, QSize, QSettings, pyqtSignal, QTimer, QEvent, QPoint
from PyQt5.QtGui import QFont, QColor, QTextCursor, QIcon, QPalette, QCursor
from PyQt5.QtWidgets import qApp

class TaskRecord:
    """Class to represent a recorded task"""
    def __init__(self, name="New Task"):
        self.name = name
        self.creation_date = datetime.datetime.now()
        self.actions = []
        self.last_executed = None
        self.execution_count = 0
        self.notes = ""
        
    def add_action(self, action_type, params=None):
        """Add an action to the task"""
        if params is None:
            params = {}
            
        self.actions.append({
            "type": action_type,
            "params": params,
            "timestamp": time.time()
        })
        
    def clear_actions(self):
        """Clear all actions in this task"""
        self.actions = []
        
    def to_dict(self):
        """Convert to dictionary for saving"""
        try:
            creation_date_str = self.creation_date.strftime("%Y-%m-%d %H:%M:%S") if self.creation_date else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            last_executed_str = self.last_executed.strftime("%Y-%m-%d %H:%M:%S") if self.last_executed else None
            
            return {
                "name": self.name,
                "creation_date": creation_date_str,
                "actions": self.actions,
                "last_executed": last_executed_str,
                "execution_count": self.execution_count,
                "notes": self.notes
            }
        except Exception as e:
            print(f"Error in to_dict: {str(e)}")
            # Return safe values
            return {
                "name": self.name,
                "creation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "actions": self.actions,
                "last_executed": None,
                "execution_count": self.execution_count,
                "notes": self.notes
            }
        
    @classmethod
    def from_dict(cls, data):
        """Create from saved dictionary"""
        try:
            task = cls(name=data["name"])
            
            # Handle creation date
            try:
                if isinstance(data["creation_date"], str):
                    if "T" in data["creation_date"]:  # ISO format
                        task.creation_date = datetime.datetime.fromisoformat(data["creation_date"].replace("Z", "+00:00"))
                    else:
                        task.creation_date = datetime.datetime.strptime(data["creation_date"], "%Y-%m-%d %H:%M:%S")
                else:
                    task.creation_date = datetime.datetime.now()
            except (ValueError, TypeError):
                task.creation_date = datetime.datetime.now()
                
            # Handle actions
            task.actions = data.get("actions", [])
            
            # Handle last executed
            try:
                last_executed = data.get("last_executed")
                if last_executed:
                    if isinstance(last_executed, str):
                        if "T" in last_executed:  # ISO format
                            task.last_executed = datetime.datetime.fromisoformat(last_executed.replace("Z", "+00:00"))
                        else:
                            task.last_executed = datetime.datetime.strptime(last_executed, "%Y-%m-%d %H:%M:%S")
                    else:
                        task.last_executed = None
                else:
                    task.last_executed = None
            except (ValueError, TypeError):
                task.last_executed = None
                
            task.execution_count = data.get("execution_count", 0)
            task.notes = data.get("notes", "")
            
            return task
        except Exception as e:
            print(f"Error creating task from dictionary: {str(e)}")
            # Return a safe default task
            return cls(name=data.get("name", "Recovered Task"))


class TaskAutomation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tasks = []
        self.current_task = None
        self.is_recording = False
        self.is_learning_mode = False
        self.pattern_database = {}
        self.action_templates = {
            "click": {"description": "Click at position", "params": ["x", "y"]},
            "text_input": {"description": "Type text", "params": ["text"]},
            "select": {"description": "Select option", "params": ["option"]},
            "delay": {"description": "Wait for time", "params": ["seconds"]},
            "conditional": {"description": "If condition", "params": ["condition", "true_action", "false_action"]},
            "loop": {"description": "Repeat actions", "params": ["count", "actions"]},
            "api_call": {"description": "Call API", "params": ["url", "method", "data"]},
            "file_operation": {"description": "File operation", "params": ["operation", "path"]}
        }
        
        # Load saved tasks
        self.tasks_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks")
        os.makedirs(self.tasks_directory, exist_ok=True)
        self.load_tasks()
        
        # Setup UI
        self.setup_ui()
        
        # Check for pyautogui
        self.check_pyautogui()
        
    def check_pyautogui(self):
        """Check if pyautogui is installed, and if not, try to install it"""
        try:
            # First check for pyautogui
            try:
                import pyautogui
                print("PyAutoGUI is available for task automation")
            except ImportError:
                print("PyAutoGUI is not installed")
                self.install_package("pyautogui")
                
            # On Windows, also check for pywin32
            if os.name == 'nt':
                try:
                    import win32api
                    import win32con
                    print("pywin32 is available for Windows task automation")
                except ImportError:
                    print("pywin32 is not installed")
                    self.install_package("pywin32")
                    
            return True
        except Exception as e:
            print(f"Error checking packages: {str(e)}")
            return False
            
    def install_package(self, package_name):
        """Install a Python package"""
        message = (
            f"The {package_name} library is not installed, which is needed for better task automation.\n\n"
            "Would you like to install it now? This will improve task playback."
        )
        reply = QMessageBox.question(self, f"Install {package_name}?", message, 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                                   
        if reply == QMessageBox.Yes:
            try:
                import subprocess
                self.status_label.setText(f"Installing {package_name}...")
                
                # Install package
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    self.status_label.setText(f"{package_name} installed successfully. Restart may be required.")
                    QMessageBox.information(self, "Success", 
                                         f"{package_name} was installed successfully. You may need to restart the application.")
                    return True
                else:
                    error = stderr.decode('utf-8')
                    print(f"Error installing {package_name}: {error}")
                    self.status_label.setText(f"Error installing {package_name}.")
                    QMessageBox.warning(self, "Installation Failed", 
                                       f"Could not install {package_name}: {error}")
                    return False
            except Exception as e:
                print(f"Error during installation: {str(e)}")
                self.status_label.setText(f"Error installing {package_name}.")
                QMessageBox.warning(self, "Installation Error", 
                                   f"Error during installation: {str(e)}")
                return False
        else:
            self.status_label.setText(f"{package_name} not installed. Task playback may be limited.")
            return False
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QVBoxLayout()
        title_label = QLabel("Task Automation")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        description = QLabel("Record, automate, and learn from repetitive tasks.")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(description)
        
        # Create splitter for task list and action details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - task list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        task_list_label = QLabel("Available Tasks:")
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.load_task)
        
        # Task list buttons
        task_buttons_layout = QHBoxLayout()
        self.new_task_btn = QPushButton("New Task")
        self.new_task_btn.clicked.connect(self.create_new_task)
        
        self.delete_task_btn = QPushButton("Delete")
        self.delete_task_btn.clicked.connect(self.delete_task)
        self.delete_task_btn.setEnabled(False)
        
        task_buttons_layout.addWidget(self.new_task_btn)
        task_buttons_layout.addWidget(self.delete_task_btn)
        
        left_layout.addWidget(task_list_label)
        left_layout.addWidget(self.task_list)
        left_layout.addLayout(task_buttons_layout)
        
        # Right panel - action details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Task name and description
        task_details_layout = QFormLayout()
        self.task_name_edit = QLineEdit()
        self.task_name_edit.setPlaceholderText("Task name")
        self.task_name_edit.textChanged.connect(self.update_task_name)
        
        self.task_desc_edit = QTextEdit()
        self.task_desc_edit.setPlaceholderText("Task description/notes")
        self.task_desc_edit.setMaximumHeight(80)
        self.task_desc_edit.textChanged.connect(self.update_task_notes)
        
        task_details_layout.addRow("Name:", self.task_name_edit)
        task_details_layout.addRow("Notes:", self.task_desc_edit)
        
        # Recorded actions list
        actions_label = QLabel("Recorded Actions:")
        self.actions_list = QListWidget()
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        self.add_action_btn = QPushButton("Add Action")
        self.add_action_btn.clicked.connect(self.add_action_manually)
        
        self.delete_action_btn = QPushButton("Delete Selected")
        self.delete_action_btn.clicked.connect(self.delete_selected_actions)
        
        action_buttons_layout.addWidget(self.add_action_btn)
        action_buttons_layout.addWidget(self.delete_action_btn)
        
        # Add to right layout
        right_layout.addLayout(task_details_layout)
        right_layout.addWidget(actions_label)
        right_layout.addWidget(self.actions_list)
        right_layout.addLayout(action_buttons_layout)
        
        # Playback speed control
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Playback Speed:")
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)  # Slowest
        self.speed_slider.setMaximum(10) # Fastest
        self.speed_slider.setValue(5)    # Default moderate speed
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        
        self.speed_value_label = QLabel("5x")
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider, 1)
        speed_layout.addWidget(self.speed_value_label)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("▶ Record")
        self.record_btn.setCheckable(True)
        self.record_btn.toggled.connect(self.toggle_recording)
        
        self.run_btn = QPushButton("▶ Run Task")
        self.run_btn.clicked.connect(self.run_task)
        self.run_btn.setEnabled(False)
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_current_task)
        self.save_btn.setEnabled(False)
        
        control_layout.addWidget(self.record_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.run_btn)
        control_layout.addWidget(self.save_btn)
        
        # Status label
        self.status_label = QLabel("Ready. Create a new task or select an existing one.")
        
        # Add everything to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(splitter, 1)  # Give the splitter stretch
        main_layout.addLayout(speed_layout)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.status_label)
        
        # Initialize UI state
        self.refresh_task_list()
        self.update_ui_state()
        
        # Set up the event filter for global event monitoring
        qApp.installEventFilter(self)
        
        # Set up timer for periodic events
        self.action_timer = QTimer()
        self.action_timer.timeout.connect(self.check_periodic_events)
        
    def update_ui_state(self):
        """Update UI based on current state"""
        has_task = self.current_task is not None
        self.task_name_edit.setEnabled(has_task)
        self.task_desc_edit.setEnabled(has_task)
        self.add_action_btn.setEnabled(has_task)
        self.delete_task_btn.setEnabled(has_task)
        self.delete_action_btn.setEnabled(has_task and self.actions_list.selectedItems())
        self.save_btn.setEnabled(has_task and (self.current_task.actions or self.current_task.notes))
        
        if has_task and self.current_task.actions:
            self.run_btn.setEnabled(True)
        else:
            self.run_btn.setEnabled(False)
    
    def load_task(self, item):
        """Load a task when selected in the list"""
        if not item:
            return
            
        try:
            self.current_task = item.data(Qt.UserRole)
            
            if not self.current_task:
                print("Warning: Selected task item has no associated data")
                return
                
            # Update UI with task details
            self.task_name_edit.setText(self.current_task.name)
            self.task_desc_edit.setText(self.current_task.notes or "")
            
            # Refresh actions list
            self.refresh_actions_list()
            
            # Update UI state
            self.update_ui_state()
            self.status_label.setText(f"Loaded task: {self.current_task.name}")
        except Exception as e:
            error_msg = f"Error loading task: {str(e)}"
            print(error_msg)
            self.status_label.setText(error_msg)
            QMessageBox.warning(self, "Load Error", error_msg)

    def refresh_actions_list(self):
        """Refresh the actions list"""
        self.actions_list.clear()
        
        if not self.current_task:
            return
            
        for i, action in enumerate(self.current_task.actions):
            # Create descriptive text for the action
            description = self.format_action_description(action)
            item = QListWidgetItem(description)
            item.setData(Qt.UserRole, action)
            self.actions_list.addItem(item)
    
    def format_action_description(self, action):
        """Format an action into a readable description"""
        action_type = action["type"]
        params = action["params"]
        
        if action_type == "click":
            return f"Click at position ({params.get('x', '?')}, {params.get('y', '?')})"
        elif action_type == "text_input":
            text = params.get('text', '')
            if len(text) > 20:
                text = text[:20] + "..."
            return f"Type text: \"{text}\""
        elif action_type == "delay":
            return f"Wait for {params.get('seconds', '?')} seconds"
        elif action_type == "select":
            return f"Select option: {params.get('option', '?')}"
        elif action_type == "file_operation":
            return f"File operation: {params.get('operation', '?')} - {params.get('path', '?')}"
        elif action_type == "key_press":
            return f"Press key: {params.get('key', '?')}"
        elif action_type == "mouse_move":
            return f"Move mouse to ({params.get('x', '?')}, {params.get('y', '?')})"
        else:
            return f"Action: {action_type} {str(params)}"
    
    def update_task_name(self):
        """Update the name of the current task"""
        if not self.current_task:
            return
            
        self.current_task.name = self.task_name_edit.text()
        self.save_btn.setEnabled(True)
    
    def update_task_notes(self):
        """Update the notes of the current task"""
        if not self.current_task:
            return
            
        self.current_task.notes = self.task_desc_edit.toPlainText()
        self.save_btn.setEnabled(True)
        
    def toggle_recording(self, recording):
        """Toggle recording mode"""
        self.is_recording = recording
        
        if recording:
            # Start recording
            if not self.current_task:
                # Create a new task if none is selected
                self.create_new_task()
                if not self.current_task:  # User cancelled
                    self.record_btn.setChecked(False)
                    return
            
            # Set UI for recording
            self.record_btn.setText("⏹ Stop Recording")
            self.status_label.setText("Recording actions... Perform the task you want to automate.")
            
            # Record initial state
            self.last_mouse_pos = None
            self.last_key_pressed = None
            self.last_action_time = time.time()
            
            # Start monitoring periodic events
            self.action_timer.start(500)  # Check every 500ms
        else:
            # Stop recording
            self.record_btn.setText("▶ Record")
            self.status_label.setText("Recording stopped.")
            self.action_timer.stop()
            
            # Update UI
            if self.current_task and self.current_task.actions:
                self.run_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                
            # Save the task
            self.save_current_task()
    
    def eventFilter(self, obj, event):
        """Filter events to capture user actions when recording"""
        if not self.is_recording:
            return super().eventFilter(obj, event)
            
        # Handle mouse events
        if event.type() == QEvent.MouseButtonPress:
            pos = event.globalPos()
            self.record_mouse_click(pos.x(), pos.y())
        elif event.type() == QEvent.MouseMove:
            # Only record significant mouse movements
            pos = event.globalPos()
            if self.last_mouse_pos:
                dx = pos.x() - self.last_mouse_pos.x()
                dy = pos.y() - self.last_mouse_pos.y()
                if dx*dx + dy*dy > 100:  # Minimum distance squared
                    self.record_mouse_move(pos.x(), pos.y())
                    self.last_mouse_pos = pos
            else:
                self.last_mouse_pos = pos
                
        # Handle key events
        elif event.type() == QEvent.KeyPress:
            key = event.key()
            if key != self.last_key_pressed:
                self.record_key_press(key)
                self.last_key_pressed = key
                
        return super().eventFilter(obj, event)
    
    def check_periodic_events(self):
        """Check for time-based events"""
        current_time = time.time()
        elapsed = current_time - self.last_action_time
        
        # If significant time has passed, record a delay
        if elapsed > 2.0:  # More than 2 seconds
            self.record_delay(round(elapsed, 1))
            self.last_action_time = current_time
    
    def record_mouse_click(self, x, y):
        """Record a mouse click action"""
        if not self.current_task:
            return
            
        self.current_task.add_action("click", {"x": x, "y": y})
        self.refresh_actions_list()
        self.last_action_time = time.time()
    
    def record_mouse_move(self, x, y):
        """Record a mouse movement action"""
        if not self.current_task:
            return
            
        self.current_task.add_action("mouse_move", {"x": x, "y": y})
        self.refresh_actions_list()
        self.last_action_time = time.time()
    
    def record_key_press(self, key):
        """Record a key press action"""
        if not self.current_task:
            return
            
        self.current_task.add_action("key_press", {"key": key})
        self.refresh_actions_list()
        self.last_action_time = time.time()
    
    def record_text_input(self, text):
        """Record a text input action"""
        if not self.current_task or not text:
            return
            
        self.current_task.add_action("text_input", {"text": text})
        self.refresh_actions_list()
        self.last_action_time = time.time()
    
    def record_delay(self, seconds):
        """Record a delay action"""
        if not self.current_task:
            return
            
        self.current_task.add_action("delay", {"seconds": seconds})
        self.refresh_actions_list()
    
    def add_action_manually(self):
        """Add an action manually"""
        if not self.current_task:
            return
            
        # Get action type
        action_types = ["click", "text_input", "delay", "key_press", "select", "file_operation"]
        action_type, ok = QInputDialog.getItem(self, "Action Type", 
                                            "Select the type of action:", 
                                            action_types, 0, False)
        if not ok:
            return
            
        # Get action parameters
        params = {}
        
        if action_type == "click":
            x, ok1 = QInputDialog.getInt(self, "X Coordinate", "Enter X coordinate:", 500, 0, 3000)
            if not ok1:
                return
                
            y, ok2 = QInputDialog.getInt(self, "Y Coordinate", "Enter Y coordinate:", 500, 0, 2000)
            if not ok2:
                return
                
            params = {"x": x, "y": y}
            
        elif action_type == "text_input":
            text, ok = QInputDialog.getText(self, "Text Input", "Enter text to type:")
            if not ok:
                return
                
            params = {"text": text}
            
        elif action_type == "delay":
            seconds, ok = QInputDialog.getDouble(self, "Delay", 
                                             "Enter delay in seconds:", 1.0, 0.1, 60.0, 1)
            if not ok:
                return
                
            params = {"seconds": seconds}
            
        elif action_type == "key_press":
            key, ok = QInputDialog.getInt(self, "Key Code", 
                                       "Enter key code (e.g., 16777220 for Enter):", 0, 0, 99999999)
            if not ok:
                return
                
            params = {"key": key}
            
        elif action_type == "select":
            option, ok = QInputDialog.getText(self, "Select Option", "Enter option to select:")
            if not ok:
                return
                
            params = {"option": option}
            
        elif action_type == "file_operation":
            operation, ok1 = QInputDialog.getItem(self, "File Operation", 
                                             "Select operation type:", 
                                             ["open", "save", "delete"], 0, False)
            if not ok1:
                return
                
            path, ok2 = QInputDialog.getText(self, "File Path", "Enter file path:")
            if not ok2:
                return
                
            params = {"operation": operation, "path": path}
        
        # Add the action
        self.current_task.add_action(action_type, params)
        self.refresh_actions_list()
        self.run_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
    
    def delete_selected_actions(self):
        """Delete selected actions"""
        if not self.current_task:
            return
            
        selected_items = self.actions_list.selectedItems()
        if not selected_items:
            return
            
        reply = QMessageBox.question(self, "Delete Actions", 
                                  f"Delete {len(selected_items)} selected action(s)?",
                                  QMessageBox.Yes | QMessageBox.No)
                                  
        if reply != QMessageBox.Yes:
            return
            
        # Get indices to remove (in reverse order)
        indices = sorted([self.actions_list.row(item) for item in selected_items], reverse=True)
        
        # Remove the actions
        for index in indices:
            if 0 <= index < len(self.current_task.actions):
                del self.current_task.actions[index]
                
        # Update UI
        self.refresh_actions_list()
        self.save_btn.setEnabled(True)
        self.run_btn.setEnabled(len(self.current_task.actions) > 0)
    
    def delete_task(self):
        """Delete the current task"""
        if not self.current_task:
            return
            
        reply = QMessageBox.question(self, "Delete Task", 
                                  f"Delete task '{self.current_task.name}'?",
                                  QMessageBox.Yes | QMessageBox.No)
                                  
        if reply != QMessageBox.Yes:
            return
            
        # Remove task file if it exists
        task_filename = os.path.join(self.tasks_directory, 
                                   f"{self.current_task.name.replace(' ', '_')}.json")
        if os.path.exists(task_filename):
            try:
                os.remove(task_filename)
            except Exception as e:
                print(f"Error deleting task file: {e}")
        
        # Remove from tasks list
        self.tasks.remove(self.current_task)
        self.current_task = None
        
        # Update UI
        self.refresh_task_list()
        self.actions_list.clear()
        self.task_name_edit.clear()
        self.task_desc_edit.clear()
        self.update_ui_state()
        self.status_label.setText("Task deleted.")
    
    def save_current_task(self):
        """Save the current task"""
        if not self.current_task:
            return
            
        try:
            # Create safe filename
            safe_name = self.current_task.name.replace(' ', '_')
            if not safe_name:
                safe_name = "unnamed_task"
                
            # Make sure the tasks directory exists
            os.makedirs(self.tasks_directory, exist_ok=True)
                
            # Save to file
            filename = os.path.join(self.tasks_directory, f"{safe_name}.json")
            
            # Get task data with error handling
            try:
                task_data = self.current_task.to_dict()
            except Exception as e:
                print(f"Error converting task to dictionary: {str(e)}")
                self.status_label.setText(f"Error saving task: {str(e)}")
                QMessageBox.warning(self, "Save Error", f"Error preparing task data: {str(e)}")
                return
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2)
                
            self.status_label.setText(f"Task '{self.current_task.name}' saved.")
            self.save_btn.setEnabled(False)
            
            # Refresh list to ensure task appears with correct name
            self.refresh_task_list()
            
            # Select the current task in the list
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                task = item.data(Qt.UserRole)
                if task and task.name == self.current_task.name:
                    self.task_list.setCurrentItem(item)
                    break
        except Exception as e:
            error_msg = f"Error saving task: {str(e)}"
            print(error_msg)
            self.status_label.setText(error_msg)
            QMessageBox.warning(self, "Save Error", error_msg)
    
    def run_task(self):
        """Execute the current task"""
        if not self.current_task or not self.current_task.actions:
            return
            
        # Update execution stats
        self.current_task.execution_count += 1
        self.current_task.last_executed = datetime.datetime.now()
        
        # Start executing actions
        self.status_label.setText(f"Executing task '{self.current_task.name}'...")
        
        # Disable UI during execution
        self.setEnabled(False)
        
        # Execute each action with proper timing
        QTimer.singleShot(100, lambda: self.execute_actions(0))
    
    def execute_actions(self, index):
        """Execute actions recursively with proper timing"""
        if not self.current_task or index >= len(self.current_task.actions):
            # All actions completed
            self.setEnabled(True)
            self.status_label.setText(f"Task '{self.current_task.name}' executed successfully.")
            return
            
        # Get current action
        action = self.current_task.actions[index]
        action_type = action["type"]
        params = action["params"]
        
        # Execute based on action type
        if action_type == "delay":
            # For delay actions, wait the specified time
            seconds = float(params.get("seconds", 1.0))
            adjusted_time = self.get_delay_time(seconds * 1000)  # Convert to ms then adjust by speed
            self.status_label.setText(f"Waiting for {seconds} seconds (adjusted: {adjusted_time/1000:.1f}s)...")
            QTimer.singleShot(adjusted_time, lambda: self.execute_actions(index + 1))
            
        elif action_type == "click":
            # For click actions, simulate a mouse click
            try:
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                self.status_label.setText(f"Clicking at position ({x}, {y})...")
                
                # Use system-level click simulation
                self.execute_system_mouse_click(x, y)
            except Exception as e:
                print(f"Error simulating click: {str(e)}")
            
            # Move to next action after a short delay
            QTimer.singleShot(self.get_delay_time(100), lambda: self.execute_actions(index + 1))
            
        elif action_type == "text_input":
            # For text input, simulate keyboard input
            try:
                text = str(params.get("text", ""))
                self.status_label.setText(f"Typing text: {text}")
                
                # Try to use pyautogui for typing if available
                try:
                    import pyautogui
                    # Adjust interval between keystrokes based on speed setting
                    interval = max(0.01, 0.1 / self.speed_slider.value())
                    pyautogui.write(text, interval=interval)
                except ImportError:
                    # Fallback to clipboard and paste
                    clipboard = qApp.clipboard()
                    clipboard.setText(text)
                    
                    # Try to send Ctrl+V
                    widget = qApp.focusWidget()
                    if widget:
                        from PyQt5.QtGui import QKeyEvent
                        from PyQt5.QtCore import QEvent
                        
                        # Create key event for Ctrl+V
                        ctrl_down = QKeyEvent(QEvent.KeyPress, Qt.Key_Control, Qt.ControlModifier)
                        v_down = QKeyEvent(QEvent.KeyPress, Qt.Key_V, Qt.ControlModifier)
                        v_up = QKeyEvent(QEvent.KeyRelease, Qt.Key_V, Qt.ControlModifier)
                        ctrl_up = QKeyEvent(QEvent.KeyRelease, Qt.Key_Control, Qt.NoModifier)
                        
                        # Send events
                        qApp.sendEvent(widget, ctrl_down)
                        qApp.sendEvent(widget, v_down)
                        qApp.sendEvent(widget, v_up)
                        qApp.sendEvent(widget, ctrl_up)
            except Exception as e:
                print(f"Error simulating text input: {str(e)}")
            
            # Move to next action
            QTimer.singleShot(self.get_delay_time(200), lambda: self.execute_actions(index + 1))
            
        elif action_type == "key_press":
            # For key press, simulate key press
            try:
                key = int(params.get("key", 0))
                self.status_label.setText(f"Pressing key: {key}")
                
                # Find focused widget
                widget = qApp.focusWidget()
                if widget:
                    from PyQt5.QtGui import QKeyEvent
                    from PyQt5.QtCore import QEvent
                    
                    # Create key events
                    key_down = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
                    key_up = QKeyEvent(QEvent.KeyRelease, key, Qt.NoModifier)
                    
                    # Send events
                    qApp.sendEvent(widget, key_down)
                    qApp.sendEvent(widget, key_up)
                else:
                    # Try to use pyautogui
                    try:
                        import pyautogui
                        # Convert Qt key code to pyautogui key
                        # This is a basic mapping and would need to be expanded
                        key_mapping = {
                            16777220: 'enter',  # Enter key
                            16777216: 'esc',    # Escape key
                            16777219: 'backspace',  # Backspace
                            16777217: 'tab',    # Tab key
                            16777223: 'delete', # Delete key
                            16777248: 'shift',  # Shift key
                            16777249: 'ctrl',   # Ctrl key
                            16777251: 'alt',    # Alt key
                        }
                        pykey = key_mapping.get(key)
                        if pykey:
                            pyautogui.press(pykey)
                        else:
                            print(f"No mapping found for key code {key}")
                    except ImportError:
                        print("pyautogui not available for key simulation")
            except Exception as e:
                print(f"Error simulating key press: {str(e)}")
            
            # Move to next action
            QTimer.singleShot(self.get_delay_time(100), lambda: self.execute_actions(index + 1))
            
        elif action_type == "mouse_move":
            # For mouse move, just move cursor
            try:
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                self.status_label.setText(f"Moving mouse to ({x}, {y})...")
                QCursor.setPos(x, y)
            except Exception as e:
                print(f"Error moving mouse: {str(e)}")
                
            # Move to next action
            QTimer.singleShot(self.get_delay_time(50), lambda: self.execute_actions(index + 1))
            
        else:
            # For other actions, just log and continue
            self.status_label.setText(f"Executing action: {action_type}")
            QTimer.singleShot(self.get_delay_time(50), lambda: self.execute_actions(index + 1))
    
    def create_new_task(self):
        """Create a new task"""
        try:
            name, ok = QInputDialog.getText(self, "New Task", "Enter task name:")
            
            if not ok:
                return
                
            name = name.strip()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Task name cannot be empty.")
                return
                
            # Check for duplicate names
            for task in self.tasks:
                if task.name == name:
                    QMessageBox.warning(self, "Duplicate Name", 
                                       f"A task named '{name}' already exists. Please choose a different name.")
                    return
            
            # Create new task with error handling
            try:
                new_task = TaskRecord(name=name)
                self.tasks.append(new_task)
                self.current_task = new_task
            except Exception as e:
                error_msg = f"Error creating task: {str(e)}"
                print(error_msg)
                QMessageBox.critical(self, "Error", error_msg)
                return
            
            # Update UI safely
            try:
                self.refresh_task_list()
                self.task_name_edit.setText(name)
                self.task_desc_edit.clear()
                self.actions_list.clear()
                self.update_ui_state()
                
                # Try to select the new task in the list
                for i in range(self.task_list.count()):
                    item = self.task_list.item(i)
                    if item and item.text() == name:
                        self.task_list.setCurrentItem(item)
                        break
                
                self.status_label.setText(f"Created new task: {name}")
                self.task_desc_edit.setFocus()
                
                # Save the new task immediately
                self.save_current_task()
            except Exception as e:
                error_msg = f"Error updating UI after task creation: {str(e)}"
                print(error_msg)
                self.status_label.setText(error_msg)
                
        except Exception as e:
            error_msg = f"Unexpected error creating task: {str(e)}"
            print(error_msg)
            self.status_label.setText(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def load_tasks(self):
        """Load saved tasks from disk"""
        self.tasks = []
        
        try:
            for file_name in os.listdir(self.tasks_directory):
                if file_name.endswith(".json"):
                    task_path = os.path.join(self.tasks_directory, file_name)
                    try:
                        with open(task_path, 'r', encoding='utf-8') as f:
                            task_data = json.load(f)
                            task = TaskRecord.from_dict(task_data)
                            self.tasks.append(task)
                    except Exception as e:
                        print(f"Error loading task {file_name}: {str(e)}")
                        
            # Sort tasks by name
            self.tasks.sort(key=lambda x: x.name.lower())
            
        except Exception as e:
            print(f"Error loading tasks: {str(e)}")
            if self.parent and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Error loading tasks: {str(e)}")
                
    def refresh_task_list(self):
        """Refresh the task list widget"""
        self.task_list.clear()
        
        for task in self.tasks:
            item = QListWidgetItem(task.name)
            item.setData(Qt.UserRole, task)
            self.task_list.addItem(item)

    def execute_system_mouse_click(self, x, y):
        """Execute a system-level mouse click for more reliability"""
        try:
            # Try pyautogui first (most reliable cross-platform)
            try:
                import pyautogui
                pyautogui.click(x, y)
                return True
            except ImportError:
                pass
                
            # For Windows systems
            if os.name == 'nt':
                try:
                    import ctypes
                    import win32api
                    import win32con
                    
                    # Move cursor
                    win32api.SetCursorPos((x, y))
                    
                    # Left mouse button down
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                    
                    # Small delay
                    time.sleep(0.1)
                    
                    # Left mouse button up
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
                    
                    return True
                except (ImportError, Exception) as e:
                    print(f"Windows mouse click simulation failed: {str(e)}")
            
            # For Linux systems
            elif os.name == 'posix':
                try:
                    import subprocess
                    # Use xdotool if available
                    subprocess.call(f'xdotool mousemove {x} {y} click 1', shell=True)
                    return True
                except Exception as e:
                    print(f"Linux mouse click simulation failed: {str(e)}")
            
            # Fallback to PyQt method
            cursor_pos = QCursor.pos()  # Save current position
            QCursor.setPos(x, y)
            
            # Try to find widget at position
            widget = qApp.widgetAt(x, y)
            if widget:
                local_pos = widget.mapFromGlobal(QPoint(x, y))
                
                # Create and send mouse events
                from PyQt5.QtGui import QMouseEvent
                from PyQt5.QtCore import QEvent, QPoint
                
                press_event = QMouseEvent(
                    QEvent.MouseButtonPress,
                    local_pos,
                    Qt.LeftButton,
                    Qt.LeftButton,
                    Qt.NoModifier
                )
                
                release_event = QMouseEvent(
                    QEvent.MouseButtonRelease,
                    local_pos,
                    Qt.LeftButton,
                    Qt.LeftButton,
                    Qt.NoModifier
                )
                
                qApp.sendEvent(widget, press_event)
                qApp.sendEvent(widget, release_event)
                
                # Restore cursor position if needed
                # QCursor.setPos(cursor_pos)
                return True
                
            return False
        except Exception as e:
            print(f"Mouse click simulation error: {str(e)}")
            return False

    def update_speed_label(self, value):
        """Update the speed label when slider value changes"""
        self.speed_value_label.setText(f"{value}x")
        
    def get_delay_time(self, base_time):
        """Calculate delay time based on speed setting"""
        speed_factor = self.speed_slider.value()
        return int(base_time / speed_factor) 