import os
import json
import shutil # Added for directory removal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QSplitter, QTextEdit, QFileSystemModel, QTreeView, QPushButton, QLabel, QTreeWidget, QInputDialog, QMessageBox, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QDir

# Determine the project root based on this file's location
# Assumes this file is in src/ui/ and project root is two levels up.
_PROJECT_PAGE_FILE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(_PROJECT_PAGE_FILE_DIR, '..', '..'))
PROJECTS_BASE_DIR = os.path.join(PROJECT_ROOT, 'data', 'projects')

class ProjectPage(QWidget):
    def __init__(self, parent=None):
        super(ProjectPage, self).__init__(parent)
        # Add a flag to prevent recursive saving triggered by loading
        self._is_loading_checklist = False 
        self.init_ui()

    def init_ui(self):
        # Project list + buttons
        self.project_list = QListWidget()
        self.new_btn = QPushButton("New")
        self.delete_btn = QPushButton("Delete")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(self.new_btn)
        sidebar_layout.addWidget(self.delete_btn)
        sidebar_layout.addWidget(self.project_list)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)

        # Main content widgets (side-by-side)
        self.guide = QTextEdit()
        self.guide.setPlaceholderText("Step-by-step guide...")

        self.checklist = QTreeWidget()
        self.checklist.setHeaderLabels(["Task"])
        # Connect itemChanged signal for auto-saving
        self.checklist.itemChanged.connect(self._on_checklist_item_changed)
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.clicked.connect(self.add_new_task)

        checklist_layout = QVBoxLayout()
        checklist_layout.addWidget(self.checklist)
        checklist_layout.addWidget(self.add_task_btn)
        checklist_widget = QWidget()
        checklist_widget.setLayout(checklist_layout)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Project notes...")

        self.file_model = QFileSystemModel()
        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setHeaderHidden(False) # Make sure header is not hidden

        # Horizontal splitter for 4 columns: Guide | Checklist | Notes | File Browser
        main_content_splitter = QSplitter(Qt.Horizontal)
        main_content_splitter.addWidget(self.guide)
        main_content_splitter.addWidget(checklist_widget)
        main_content_splitter.addWidget(self.notes)
        main_content_splitter.addWidget(self.file_view)

        main_content_splitter.setStretchFactor(0, 2)  # Guide
        main_content_splitter.setStretchFactor(1, 1)  # Checklist
        main_content_splitter.setStretchFactor(2, 1)  # Notes
        main_content_splitter.setStretchFactor(3, 2)  # File viewer

        # Master horizontal splitter: Project list | All panels in a row
        full_splitter = QSplitter(Qt.Horizontal)
        full_splitter.addWidget(sidebar_widget)
        full_splitter.addWidget(main_content_splitter)
        full_splitter.setStretchFactor(0, 1)
        full_splitter.setStretchFactor(1, 4)

        layout = QHBoxLayout(self)
        layout.addWidget(full_splitter)

        # Connect signals and load initial data
        self.project_list.itemClicked.connect(self.load_project_data)
        self.new_btn.clicked.connect(self.create_new_project)
        self.delete_btn.clicked.connect(self.delete_project)

        self.load_projects()
        self.set_project_directory(None) # Initialize file viewer

    def _on_checklist_item_changed(self, item, column):
        """Handles changes to checklist items (text or check state) and triggers save."""
        # Prevent saving if the change was triggered during loading
        if self._is_loading_checklist:
            return
        # Only save if the change is in the first column (text or checkbox)
        if column == 0:
            print(f"Item changed: {item.text(0)}, state: {item.checkState(0)}") # Debug print
            self.save_project_data()

    def add_new_task(self):
        item = QTreeWidgetItem(["New Task"])
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        item.setCheckState(0, Qt.Unchecked)
        self.checklist.addTopLevelItem(item)
        self.checklist.editItem(item, 0) # Start editing immediately
        # No need to save here, itemChanged signal will handle it after edit finishes

    def set_project_directory(self, project_path):
        if project_path and os.path.isdir(project_path):
            root_path = project_path
        else:
            # Default to project root or a sensible default if no project is selected
            # root_path = os.path.join(os.getcwd(), 'data', 'projects') # Or maybe just os.getcwd()
            root_path = PROJECTS_BASE_DIR # Use the consistently defined base directory
        self.file_model.setRootPath(root_path)
        self.file_view.setRootIndex(self.file_model.index(root_path))

    def load_projects(self):
        # projects_dir = os.path.join(os.getcwd(), 'data', 'projects')
        projects_dir = PROJECTS_BASE_DIR # Use the consistently defined base directory
        if not os.path.exists(projects_dir):
            os.makedirs(projects_dir)
        for project_name in os.listdir(projects_dir):
            self.project_list.addItem(project_name)

    def load_project_data(self, item):
        # --- Add loading flag --- 
        self._is_loading_checklist = True 
        try:
            project_name = item.text()
            # project_dir = os.path.join(os.getcwd(), 'data', 'projects', project_name)
            project_dir = os.path.join(PROJECTS_BASE_DIR, project_name) # Use consistent base directory
            guide_path = os.path.join(project_dir, 'guide.txt')
            checklist_path = os.path.join(project_dir, 'checklist.json')
            notes_path = os.path.join(project_dir, 'notes.txt')

            # Load guide
            if os.path.exists(guide_path):
                try:
                    with open(guide_path, 'r', encoding='utf-8') as file:
                        self.guide.setPlainText(file.read())
                except Exception as e:
                    self.guide.setPlainText(f"Error loading guide: {e}")
            else:
                self.guide.clear()

            # Load checklist
            self.checklist.clear()
            if os.path.exists(checklist_path):
                try:
                    with open(checklist_path, 'r', encoding='utf-8') as file:
                        checklist_data = json.load(file)
                        # --- Ensure data is a list --- 
                        if isinstance(checklist_data, list):
                            for task_data in checklist_data:
                                # --- Check if task_data is a dictionary --- 
                                if isinstance(task_data, dict):
                                    # Use 'text' key, fallback to 'label', then default
                                    task_text = task_data.get("text", task_data.get("label", "Unnamed Task")) 
                                    is_checked = task_data.get("checked", False)
                                    
                                    tree_item = QTreeWidgetItem([task_text])
                                    tree_item.setFlags(tree_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                                    tree_item.setCheckState(0, Qt.Checked if is_checked else Qt.Unchecked)
                                    self.checklist.addTopLevelItem(tree_item)
                                else:
                                    print(f"Skipping invalid checklist item (not a dict): {task_data}") # Debug
                        else:
                             QMessageBox.warning(self, "Checklist Load Error", f"Checklist file for '{project_name}' does not contain a valid list.")
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Checklist Load Error", f"Could not parse checklist JSON for '{project_name}'. File might be corrupted or empty.")
                except Exception as e:
                    QMessageBox.critical(self, "Checklist Load Error", f"An unexpected error occurred loading the checklist: {e}")
            # If file doesn't exist, list is already cleared - starting empty.

            # Load notes
            if os.path.exists(notes_path):
                 try:
                    with open(notes_path, 'r', encoding='utf-8') as file:
                        self.notes.setPlainText(file.read())
                 except Exception as e:
                    self.notes.setPlainText(f"Error loading notes: {e}")
            else:
                self.notes.clear()

            # Update file explorer root
            self.set_project_directory(project_dir)
        finally:
             # --- Always reset loading flag --- 
            self._is_loading_checklist = False

    def save_project_data(self):
        current_project_item = self.project_list.currentItem()
        if not current_project_item:
            # Maybe show a status message? For now, just return.
            print("No project selected, cannot save.")
            return

        project_name = current_project_item.text()
        # project_dir = os.path.join(os.getcwd(), 'data', 'projects', project_name)
        project_dir = os.path.join(PROJECTS_BASE_DIR, project_name) # Use consistent base directory
        # Ensure project directory exists before trying to save files
        if not os.path.exists(project_dir):
             QMessageBox.warning(self, "Save Error", f"Project directory for '{project_name}' not found. Cannot save data.")
             return
             
        guide_path = os.path.join(project_dir, 'guide.txt')
        checklist_path = os.path.join(project_dir, 'checklist.json')
        notes_path = os.path.join(project_dir, 'notes.txt')

        # Save guide
        try:
            with open(guide_path, 'w', encoding='utf-8') as file:
                file.write(self.guide.toPlainText())
        except Exception as e:
             QMessageBox.critical(self, "Error Saving Guide", f"Could not save guide: {e}")

        # Save checklist
        checklist_data_to_save = []
        for i in range(self.checklist.topLevelItemCount()):
            item = self.checklist.topLevelItem(i)
            task_text = item.text(0)
            is_checked = item.checkState(0) == Qt.Checked
            # Using 'text' key consistently, as per previous implementation
            checklist_data_to_save.append({"text": task_text, "checked": is_checked})
        try:
            with open(checklist_path, 'w', encoding='utf-8') as file:
                json.dump(checklist_data_to_save, file, indent=4) # Use indent for readability
        except Exception as e:
             QMessageBox.critical(self, "Error Saving Checklist", f"Could not save checklist: {e}")

        # Save notes
        try:
            with open(notes_path, 'w', encoding='utf-8') as file:
                file.write(self.notes.toPlainText())
        except Exception as e:
             QMessageBox.critical(self, "Error Saving Notes", f"Could not save notes: {e}")

    def create_new_project(self):
        project_name, ok = QInputDialog.getText(self, 'New Project', 'Enter project name:')
        if ok and project_name:
            # Sanitize project name (basic example, might need more robust checks)
            project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '_')).rstrip()
            if not project_name:
                QMessageBox.warning(self, 'Invalid Name', 'Project name cannot be empty or only contain invalid characters.')
                return

            # projects_base_dir = os.path.join(os.getcwd(), 'data', 'projects')
            # project_dir = os.path.join(projects_base_dir, project_name)
            project_dir = os.path.join(PROJECTS_BASE_DIR, project_name) # Use consistent base directory

            if os.path.exists(project_dir):
                QMessageBox.warning(self, 'Project Exists', f'Project "{project_name}" already exists.')
            else:
                try:
                    os.makedirs(project_dir)
                    # Create default files with structure for checklist
                    with open(os.path.join(project_dir, 'guide.txt'), 'w') as f:
                        f.write("")
                    with open(os.path.join(project_dir, 'checklist.json'), 'w') as f:
                        json.dump([], f, indent=4) # Start with empty list, formatted
                    with open(os.path.join(project_dir, 'notes.txt'), 'w') as f:
                        f.write("")
                    
                    # Add to list and select
                    self.project_list.addItem(project_name)
                    self.project_list.setCurrentRow(self.project_list.count() - 1) # Select the new item
                    self.load_project_data(self.project_list.currentItem()) # Load the new project's (empty) data

                except Exception as e:
                    QMessageBox.critical(self, 'Error', f'Failed to create project: {e}')

    def delete_project(self):
        current_item = self.project_list.currentItem()
        if not current_item:
            QMessageBox.information(self, 'Delete Project', 'Please select a project to delete.')
            return

        project_name = current_item.text()
        reply = QMessageBox.question(self, 'Delete Project', 
                                   f'Are you sure you want to permanently delete the project "{project_name}"?\nThis action cannot be undone.',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # project_dir = os.path.join(os.getcwd(), 'data', 'projects', project_name)
                project_dir = os.path.join(PROJECTS_BASE_DIR, project_name) # Use consistent base directory
                if os.path.exists(project_dir):
                    shutil.rmtree(project_dir)
                
                # Remove from list
                self.project_list.takeItem(self.project_list.row(current_item))

                # Clear panels or load next/previous project if available
                if self.project_list.count() > 0:
                    next_row = max(0, self.project_list.row(current_item) - 1)
                    self.project_list.setCurrentRow(next_row)
                    self.load_project_data(self.project_list.currentItem())
                else:
                    self.guide.clear()
                    self.checklist.clear()
                    self.notes.clear()
                    self.set_project_directory(None) # Reset file explorer to base project dir

            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to delete project: {e}') 