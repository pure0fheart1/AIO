from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QDateEdit, QTextEdit,
                             QFormLayout, QComboBox, QFrame, QSlider, QColorDialog,
                             QScrollArea, QGroupBox, QSpinBox, QListWidget,
                             QListWidgetItem, QToolButton, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QFont, QIcon

from datetime import datetime, timedelta

class PropertiesPanel(QWidget):
    """
    Panel for displaying and editing properties of selected roadmap items
    """
    
    # Signals
    item_updated = pyqtSignal(dict)
    dependency_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_item = None
        self.parent_app = parent
        
    def setup_ui(self):
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header section
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setStyleSheet("background-color: #f0f0f0;")
        header_layout = QHBoxLayout(header)
        
        self.header_label = QLabel("Properties")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        header_layout.addWidget(self.header_label)
        header_layout.addStretch(1)
        
        # Scroll area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Container widget for all properties
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_layout.setContentsMargins(10, 10, 10, 10)
        self.properties_layout.setSpacing(10)
        
        # Add scroll area to main layout
        scroll_area.setWidget(self.properties_widget)
        
        # Add the no-selection message
        self.no_selection_label = QLabel("No item selected")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.properties_layout.addWidget(self.no_selection_label)
        
        # Create the property edit forms (initially hidden)
        self.create_milestone_form()
        self.create_task_form()
        
        # Add widgets to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(scroll_area)
        
        # Set a fixed width for the panel
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
    def create_milestone_form(self):
        """Create form for editing milestone properties"""
        self.milestone_form = QGroupBox("Milestone Properties")
        form_layout = QFormLayout(self.milestone_form)
        
        # Title field
        self.milestone_title = QLineEdit()
        self.milestone_title.textChanged.connect(self.on_property_changed)
        form_layout.addRow("Title:", self.milestone_title)
        
        # Date field
        self.milestone_date = QDateEdit()
        self.milestone_date.setCalendarPopup(True)
        self.milestone_date.setDate(QDate.currentDate())
        self.milestone_date.dateChanged.connect(self.on_property_changed)
        form_layout.addRow("Date:", self.milestone_date)
        
        # Description field
        self.milestone_description = QTextEdit()
        self.milestone_description.setMaximumHeight(100)
        self.milestone_description.textChanged.connect(self.on_property_changed)
        form_layout.addRow("Description:", self.milestone_description)
        
        # Color field
        color_layout = QHBoxLayout()
        self.milestone_color_preview = QLabel()
        self.milestone_color_preview.setFixedSize(24, 24)
        self.milestone_color_preview.setStyleSheet("background-color: #4A86E8; border: 1px solid #CCCCCC;")
        
        self.milestone_color_button = QPushButton("Change...")
        self.milestone_color_button.clicked.connect(self.change_milestone_color)
        
        color_layout.addWidget(self.milestone_color_preview)
        color_layout.addWidget(self.milestone_color_button)
        
        form_layout.addRow("Color:", color_layout)
        
        # Add to properties layout but initially hide it
        self.properties_layout.addWidget(self.milestone_form)
        self.milestone_form.hide()
        
    def create_task_form(self):
        """Create form for editing task properties"""
        self.task_form = QGroupBox("Task Properties")
        form_layout = QFormLayout(self.task_form)
        
        # Title field
        self.task_title = QLineEdit()
        self.task_title.textChanged.connect(self.on_property_changed)
        form_layout.addRow("Title:", self.task_title)
        
        # Start date field
        self.task_start_date = QDateEdit()
        self.task_start_date.setCalendarPopup(True)
        self.task_start_date.setDate(QDate.currentDate())
        self.task_start_date.dateChanged.connect(self.on_property_changed)
        form_layout.addRow("Start Date:", self.task_start_date)
        
        # End date field
        self.task_end_date = QDateEdit()
        self.task_end_date.setCalendarPopup(True)
        self.task_end_date.setDate(QDate.currentDate().addDays(7))  # Default to a week later
        self.task_end_date.dateChanged.connect(self.on_property_changed)
        form_layout.addRow("End Date:", self.task_end_date)
        
        # Description field
        self.task_description = QTextEdit()
        self.task_description.setMaximumHeight(100)
        self.task_description.textChanged.connect(self.on_property_changed)
        form_layout.addRow("Description:", self.task_description)
        
        # Progress field
        progress_layout = QHBoxLayout()
        self.task_progress = QSlider(Qt.Horizontal)
        self.task_progress.setRange(0, 100)
        self.task_progress.setValue(0)
        self.task_progress.valueChanged.connect(self.update_progress_label)
        
        self.task_progress_label = QLabel("0%")
        
        progress_layout.addWidget(self.task_progress)
        progress_layout.addWidget(self.task_progress_label)
        
        form_layout.addRow("Progress:", progress_layout)
        
        # Dependencies section
        dependencies_group = QGroupBox("Dependencies")
        dependencies_layout = QVBoxLayout(dependencies_group)
        
        # List of current dependencies
        self.dependencies_list = QListWidget()
        self.dependencies_list.setMaximumHeight(120)
        dependencies_layout.addWidget(self.dependencies_list)
        
        # Add/Remove dependency buttons
        dep_buttons_layout = QHBoxLayout()
        
        self.add_dependency_button = QPushButton("Add...")
        self.add_dependency_button.clicked.connect(self.add_dependency)
        
        self.remove_dependency_button = QPushButton("Remove")
        self.remove_dependency_button.clicked.connect(self.remove_dependency)
        self.remove_dependency_button.setEnabled(False)  # Disabled until selection
        
        self.dependencies_list.itemSelectionChanged.connect(self.dependency_selection_changed)
        
        dep_buttons_layout.addWidget(self.add_dependency_button)
        dep_buttons_layout.addWidget(self.remove_dependency_button)
        dependencies_layout.addLayout(dep_buttons_layout)
        
        form_layout.addRow(dependencies_group)
        
        # Critical path status
        self.critical_path_label = QLabel("No")
        self.critical_path_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("On Critical Path:", self.critical_path_label)
        
        # Color field
        color_layout = QHBoxLayout()
        self.task_color_preview = QLabel()
        self.task_color_preview.setFixedSize(24, 24)
        self.task_color_preview.setStyleSheet("background-color: #4A86E8; border: 1px solid #CCCCCC;")
        
        self.task_color_button = QPushButton("Change...")
        self.task_color_button.clicked.connect(self.change_task_color)
        
        color_layout.addWidget(self.task_color_preview)
        color_layout.addWidget(self.task_color_button)
        
        form_layout.addRow("Color:", color_layout)
        
        # Add to properties layout but initially hide it
        self.properties_layout.addWidget(self.task_form)
        self.task_form.hide()
        
    def update_progress_label(self, value):
        """Update the progress percentage label"""
        self.task_progress_label.setText(f"{value}%")
        self.on_property_changed()
    
    def change_milestone_color(self):
        """Open color picker for milestone color"""
        current_color = QColor(self.milestone_color_preview.styleSheet().split("background-color:")[1].split(";")[0].strip())
        color = QColorDialog.getColor(current_color, self, "Select Milestone Color")
        
        if color.isValid():
            self.milestone_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #CCCCCC;")
            self.on_property_changed()
    
    def change_task_color(self):
        """Open color picker for task color"""
        current_color = QColor(self.task_color_preview.styleSheet().split("background-color:")[1].split(";")[0].strip())
        color = QColorDialog.getColor(current_color, self, "Select Task Color")
        
        if color.isValid():
            self.task_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #CCCCCC;")
            self.on_property_changed()
    
    def dependency_selection_changed(self):
        """Handle selection change in the dependencies list"""
        self.remove_dependency_button.setEnabled(len(self.dependencies_list.selectedItems()) > 0)
    
    def add_dependency(self):
        """Open dialog to add a dependency"""
        if not self.current_item or not hasattr(self.current_item, 'dependencies'):
            return
            
        # Get all available tasks except the current one and its dependents
        available_tasks = []
        if hasattr(self.parent_app, 'roadmap_canvas'):
            all_tasks = [
                item for item in self.parent_app.roadmap_canvas.timeline_view.items
                if hasattr(item, 'dependencies') and item != self.current_item
            ]
            
            # Filter out tasks that would create circular dependencies
            # (current task's dependents and their dependents recursively)
            dependent_ids = self.get_all_dependent_ids(self.current_item)
            available_tasks = [task for task in all_tasks if task.id not in dependent_ids]
        
        # Create and show the dialog
        dialog = DependencySelectionDialog(available_tasks, self)
        if dialog.exec_():
            # Get the selected task
            selected_task = dialog.get_selected_task()
            if selected_task:
                # Add dependency
                self.current_item.add_dependency(selected_task)
                
                # Update the dependencies list
                self.update_dependencies_list()
                
                # Notify that dependencies have changed
                self.dependency_updated.emit()
    
    def get_all_dependent_ids(self, task, visited=None):
        """Get all dependent task IDs recursively to avoid circular dependencies"""
        if visited is None:
            visited = set()
            
        if task.id in visited:
            return visited
        
        visited.add(task.id)
        for dependent in task.dependents:
            self.get_all_dependent_ids(dependent, visited)
            
        return visited
    
    def remove_dependency(self):
        """Remove selected dependency"""
        if not self.current_item or not hasattr(self.current_item, 'dependencies'):
            return
            
        selected_items = self.dependencies_list.selectedItems()
        if not selected_items:
            return
        
        # Get the task ID from the selected item
        task_id = selected_items[0].data(Qt.UserRole)
        
        # Find the corresponding task and remove the dependency
        for dep in self.current_item.dependencies[:]:  # Copy to avoid issues during iteration
            if dep.id == task_id:
                self.current_item.remove_dependency(dep)
                break
        
        # Update the dependencies list
        self.update_dependencies_list()
        
        # Notify that dependencies have changed
        self.dependency_updated.emit()
    
    def update_dependencies_list(self):
        """Update the list of dependencies"""
        self.dependencies_list.clear()
        
        if not self.current_item or not hasattr(self.current_item, 'dependencies'):
            return
            
        for dep in self.current_item.dependencies:
            item = QListWidgetItem(dep.title)
            item.setData(Qt.UserRole, dep.id)
            self.dependencies_list.addItem(item)
    
    def set_item(self, item):
        """Set the item to be edited"""
        self.current_item = item
        
        # Hide all forms first
        self.milestone_form.hide()
        self.task_form.hide()
        self.no_selection_label.hide()
        
        if not item:
            # No item selected
            self.no_selection_label.show()
            return
            
        # Update the header
        if hasattr(item, 'date'):
            # It's a milestone
            self.header_label.setText("Milestone Properties")
            self.update_milestone_form(item)
            self.milestone_form.show()
        elif hasattr(item, 'start_date') and hasattr(item, 'end_date'):
            # It's a task
            self.header_label.setText("Task Properties")
            self.update_task_form(item)
            self.task_form.show()
    
    def update_milestone_form(self, milestone):
        """Update the milestone form with the milestone's properties"""
        # Block signals temporarily to prevent on_property_changed from firing
        self.milestone_title.blockSignals(True)
        self.milestone_date.blockSignals(True)
        self.milestone_description.blockSignals(True)
        
        # Set values
        self.milestone_title.setText(milestone.title)
        self.milestone_date.setDate(QDate(milestone.date.year, milestone.date.month, milestone.date.day))
        self.milestone_description.setText(milestone.description)
        self.milestone_color_preview.setStyleSheet(f"background-color: {milestone.color.name()}; border: 1px solid #CCCCCC;")
        
        # Unblock signals
        self.milestone_title.blockSignals(False)
        self.milestone_date.blockSignals(False)
        self.milestone_description.blockSignals(False)
    
    def update_task_form(self, task):
        """Update the task form with the task's properties"""
        # Block signals temporarily to prevent on_property_changed from firing
        self.task_title.blockSignals(True)
        self.task_start_date.blockSignals(True)
        self.task_end_date.blockSignals(True)
        self.task_description.blockSignals(True)
        self.task_progress.blockSignals(True)
        
        # Set values
        self.task_title.setText(task.title)
        self.task_start_date.setDate(QDate(task.start_date.year, task.start_date.month, task.start_date.day))
        self.task_end_date.setDate(QDate(task.end_date.year, task.end_date.month, task.end_date.day))
        self.task_description.setText(task.description)
        self.task_progress.setValue(task.progress)
        self.task_progress_label.setText(f"{task.progress}%")
        self.task_color_preview.setStyleSheet(f"background-color: {task.color.name()}; border: 1px solid #CCCCCC;")
        
        # Update critical path status
        if task.is_critical:
            self.critical_path_label.setText("Yes")
            self.critical_path_label.setStyleSheet("font-weight: bold; color: #FF5252;")
        else:
            self.critical_path_label.setText("No")
            self.critical_path_label.setStyleSheet("font-weight: bold;")
        
        # Update dependencies list
        self.update_dependencies_list()
        
        # Unblock signals
        self.task_title.blockSignals(False)
        self.task_start_date.blockSignals(False)
        self.task_end_date.blockSignals(False)
        self.task_description.blockSignals(False)
        self.task_progress.blockSignals(False)
    
    def on_property_changed(self):
        """Handle property changes and update the item"""
        if not self.current_item:
            return
            
        # Determine what type of item we're editing
        if hasattr(self.current_item, 'date'):
            # Update milestone properties
            self.current_item.set_title(self.milestone_title.text())
            
            date = self.milestone_date.date().toPyDate()
            self.current_item.set_date(date)
            
            self.current_item.description = self.milestone_description.toPlainText()
            
            color = QColor(self.milestone_color_preview.styleSheet().split("background-color:")[1].split(";")[0].strip())
            self.current_item.set_color(color)
            
        elif hasattr(self.current_item, 'start_date') and hasattr(self.current_item, 'end_date'):
            # Update task properties
            self.current_item.set_title(self.task_title.text())
            
            start_date = self.task_start_date.date().toPyDate()
            end_date = self.task_end_date.date().toPyDate()
            self.current_item.set_dates(start_date, end_date)
            
            self.current_item.description = self.task_description.toPlainText()
            self.current_item.set_progress(self.task_progress.value())
            
            color = QColor(self.task_color_preview.styleSheet().split("background-color:")[1].split(";")[0].strip())
            self.current_item.set_color(color)
            
        # Emit signal to indicate the item was updated
        self.item_updated.emit({
            "id": getattr(self.current_item, "id", "unknown"),
            "type": "milestone" if hasattr(self.current_item, 'date') else "task"
        })


class DependencySelectionDialog(QDialog):
    """Dialog for selecting task dependencies"""
    
    def __init__(self, available_tasks, parent=None):
        super().__init__(parent)
        self.available_tasks = available_tasks
        self.selected_task = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Add Dependency")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Select a task that this task depends on:")
        layout.addWidget(instructions)
        
        # Task list
        self.task_list = QListWidget()
        for task in self.available_tasks:
            item = QListWidgetItem(task.title)
            item.setData(Qt.UserRole, task)
            self.task_list.addItem(item)
        
        layout.addWidget(self.task_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.accept)
        select_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(select_button)
        
        layout.addLayout(button_layout)
        
    def get_selected_task(self):
        """Get the selected task"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return None
            
        # Get the task object from the selected item
        return selected_items[0].data(Qt.UserRole) 