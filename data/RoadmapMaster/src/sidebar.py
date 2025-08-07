from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTreeWidget, QTreeWidgetItem, QMenu,
                             QAction, QInputDialog, QMessageBox, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

class Sidebar(QWidget):
    """
    Sidebar widget for project navigation and organization
    """
    
    # Signals
    project_selected = pyqtSignal(str)
    milestone_selected = pyqtSignal(str)
    task_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Set up main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header section with title
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setStyleSheet("background-color: #f0f0f0;")
        header_layout = QHBoxLayout(header)
        
        header_label = QLabel("Projects")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Add buttons in header
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setToolTip("Add new project")
        add_btn.clicked.connect(self.add_project)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch(1)
        header_layout.addWidget(add_btn)
        
        # Search box
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_box)
        
        # Create tree widget for projects
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemClicked.connect(self.item_clicked)
        
        # Add some sample projects
        self.add_sample_projects()
        
        # Add widgets to main layout
        layout.addWidget(header)
        layout.addLayout(search_layout)
        layout.addWidget(self.tree)
        
        # Set some reasonable minimum width
        self.setMinimumWidth(200)
        
    def add_sample_projects(self):
        """Add some sample projects to the tree"""
        # Project 1
        project1 = QTreeWidgetItem(self.tree)
        project1.setText(0, "Website Redesign")
        project1.setData(0, Qt.UserRole, {"type": "project", "id": "p1"})
        
        # Add milestones to Project 1
        milestone1 = QTreeWidgetItem(project1)
        milestone1.setText(0, "Design Approval")
        milestone1.setData(0, Qt.UserRole, {"type": "milestone", "id": "m1", "project_id": "p1"})
        
        milestone2 = QTreeWidgetItem(project1)
        milestone2.setText(0, "Beta Launch")
        milestone2.setData(0, Qt.UserRole, {"type": "milestone", "id": "m2", "project_id": "p1"})
        
        # Add tasks to Project 1
        task1 = QTreeWidgetItem(project1)
        task1.setText(0, "Wireframes")
        task1.setData(0, Qt.UserRole, {"type": "task", "id": "t1", "project_id": "p1"})
        
        task2 = QTreeWidgetItem(project1)
        task2.setText(0, "Frontend Development")
        task2.setData(0, Qt.UserRole, {"type": "task", "id": "t2", "project_id": "p1"})
        
        # Project 2
        project2 = QTreeWidgetItem(self.tree)
        project2.setText(0, "Product Launch")
        project2.setData(0, Qt.UserRole, {"type": "project", "id": "p2"})
        
        # Add milestones to Project 2
        milestone3 = QTreeWidgetItem(project2)
        milestone3.setText(0, "Marketing Campaign Start")
        milestone3.setData(0, Qt.UserRole, {"type": "milestone", "id": "m3", "project_id": "p2"})
        
        # Expand all items
        self.tree.expandAll()
        
    def add_project(self):
        """Add a new project to the tree"""
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        
        if ok and name:
            project = QTreeWidgetItem(self.tree)
            project.setText(0, name)
            project.setData(0, Qt.UserRole, {"type": "project", "id": f"p{self.tree.topLevelItemCount()}"})
            self.tree.setCurrentItem(project)
    
    def add_milestone(self, parent_item):
        """Add a milestone to the selected project"""
        name, ok = QInputDialog.getText(self, "New Milestone", "Milestone name:")
        
        if ok and name:
            parent_data = parent_item.data(0, Qt.UserRole)
            project_id = parent_data["id"] if parent_data["type"] == "project" else parent_data["project_id"]
            
            milestone = QTreeWidgetItem(parent_item if parent_data["type"] == "project" else parent_item.parent())
            milestone.setText(0, name)
            
            # Get count of siblings to generate a unique ID
            parent = parent_item if parent_data["type"] == "project" else parent_item.parent()
            milestone_count = sum(1 for i in range(parent.childCount()) 
                               if parent.child(i).data(0, Qt.UserRole)["type"] == "milestone")
            
            milestone.setData(0, Qt.UserRole, {
                "type": "milestone", 
                "id": f"m{milestone_count + 1}", 
                "project_id": project_id
            })
            
            parent.addChild(milestone)
            parent.setExpanded(True)
    
    def add_task(self, parent_item):
        """Add a task to the selected project"""
        name, ok = QInputDialog.getText(self, "New Task", "Task name:")
        
        if ok and name:
            parent_data = parent_item.data(0, Qt.UserRole)
            project_id = parent_data["id"] if parent_data["type"] == "project" else parent_data["project_id"]
            
            task = QTreeWidgetItem(parent_item if parent_data["type"] == "project" else parent_item.parent())
            task.setText(0, name)
            
            # Get count of siblings to generate a unique ID
            parent = parent_item if parent_data["type"] == "project" else parent_item.parent()
            task_count = sum(1 for i in range(parent.childCount()) 
                          if parent.child(i).data(0, Qt.UserRole)["type"] == "task")
            
            task.setData(0, Qt.UserRole, {
                "type": "task", 
                "id": f"t{task_count + 1}", 
                "project_id": project_id
            })
            
            parent.addChild(task)
            parent.setExpanded(True)
    
    def delete_item(self, item):
        """Delete the selected item"""
        data = item.data(0, Qt.UserRole)
        item_type = data["type"]
        
        message = f"Are you sure you want to delete this {item_type}?"
        if item_type == "project":
            message += "\nThis will also delete all milestones and tasks in the project."
            
        reply = QMessageBox.question(self, "Confirm Delete", message, 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                    
        if reply == QMessageBox.Yes:
            if item_type == "project":
                # Delete a top-level project
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)
            else:
                # Delete a child item
                parent = item.parent()
                index = parent.indexOfChild(item)
                parent.takeChild(index)
    
    def show_context_menu(self, position):
        """Show the context menu for tree items"""
        item = self.tree.itemAt(position)
        
        if item:
            data = item.data(0, Qt.UserRole)
            item_type = data["type"]
            
            menu = QMenu()
            
            if item_type == "project":
                add_milestone_action = QAction("Add Milestone", self)
                add_milestone_action.triggered.connect(lambda: self.add_milestone(item))
                menu.addAction(add_milestone_action)
                
                add_task_action = QAction("Add Task", self)
                add_task_action.triggered.connect(lambda: self.add_task(item))
                menu.addAction(add_task_action)
                
                menu.addSeparator()
                
                rename_action = QAction("Rename", self)
                rename_action.triggered.connect(lambda: self.rename_item(item))
                menu.addAction(rename_action)
                
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(delete_action)
            else:
                rename_action = QAction("Rename", self)
                rename_action.triggered.connect(lambda: self.rename_item(item))
                menu.addAction(rename_action)
                
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(delete_action)
            
            menu.exec_(self.tree.viewport().mapToGlobal(position))
    
    def rename_item(self, item):
        """Rename the selected item"""
        data = item.data(0, Qt.UserRole)
        item_type = data["type"]
        
        current_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, f"Rename {item_type.capitalize()}", 
                                           f"{item_type.capitalize()} name:", 
                                           text=current_name)
        
        if ok and new_name:
            item.setText(0, new_name)
    
    def item_clicked(self, item, column):
        """Handle item click events"""
        data = item.data(0, Qt.UserRole)
        
        if data["type"] == "project":
            self.project_selected.emit(data["id"])
        elif data["type"] == "milestone":
            self.milestone_selected.emit(data["id"])
        elif data["type"] == "task":
            self.task_selected.emit(data["id"])
    
    def filter_items(self, text):
        """Filter tree items based on search text"""
        if not text:
            # If search is empty, show all items
            for i in range(self.tree.topLevelItemCount()):
                top_item = self.tree.topLevelItem(i)
                top_item.setHidden(False)
                
                for j in range(top_item.childCount()):
                    top_item.child(j).setHidden(False)
            return
            
        # Perform the filter
        text = text.lower()
        
        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            top_text = top_item.text(0).lower()
            
            # Check if the top-level item matches
            top_match = text in top_text
            top_item.setHidden(not top_match)
            
            # Also check all children
            child_match = False
            
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                child_text = child_item.text(0).lower()
                
                match = text in child_text
                child_item.setHidden(not match)
                
                if match:
                    child_match = True
            
            # Show the parent if any child matches
            if child_match:
                top_item.setHidden(False)
                top_item.setExpanded(True) 