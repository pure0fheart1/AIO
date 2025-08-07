import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QSplitter, QInputDialog, QMessageBox, QFileDialog,
                            QAbstractItemView)
from PyQt5.QtCore import Qt, QDir, pyqtSignal
from PyQt5.QtGui import QFont

class ChecklistItem(QListWidgetItem):
    """Custom QListWidgetItem to store original data."""
    def __init__(self, item_data):
        super().__init__(item_data["text"])
        self.item_data = item_data
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
        self.setCheckState(Qt.Checked if item_data["checked"] else Qt.Unchecked)
        self.update_font()

    def update_font(self):
        font = self.font()
        font.setStrikeOut(self.item_data["checked"])
        self.setFont(font)

    def setChecked(self, checked):
        self.item_data["checked"] = checked
        self.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.update_font()

    def setText(self, text):
        self.item_data["text"] = text
        super().setText(text)

class ChecklistItemsWidget(QListWidget):
    """Subclass QListWidget to handle drag and drop and item changes."""
    items_reordered = pyqtSignal()
    item_text_changed = pyqtSignal(int, str) # row, new_text
    item_check_changed = pyqtSignal(int, bool) # row, is_checked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.itemChanged.connect(self._on_internal_item_changed)
        self.itemDoubleClicked.connect(self.edit_item) # Edit on double-click

    def dropEvent(self, event):
        super().dropEvent(event)
        self.items_reordered.emit()

    def _on_internal_item_changed(self, item):
        """Handle changes from checkbox clicks or edits."""
        if not isinstance(item, ChecklistItem):
            return
            
        row = self.row(item)
        is_checked = item.checkState() == Qt.Checked
        new_text = item.text()

        # Check if state actually changed to avoid loops
        if item.item_data["checked"] != is_checked:
            item.item_data["checked"] = is_checked
            item.update_font()
            self.item_check_changed.emit(row, is_checked)

        # Text doesn't trigger itemChanged directly for edits, handled via editor
        # We rely on the main manager saving changes after editing finishes
        
    def edit_item(self, item):
        """Start editing the item on double click."""
        if isinstance(item, ChecklistItem):
            self.editItem(item)

class ChecklistManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent # Store parent reference
        self.checklists = []
        self.current_checklist_index = -1
        # Store data in the project's data directory
        # Go up one level from src/ui/ (__file__) to src/, then up to project root, then into data/
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_dir = os.path.join(project_root, 'data')
        self.checklists_file = os.path.join(self.data_dir, "checklists.json")
        self.setup_ui()
        self.load_checklists()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Checklists")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        new_checklist_btn = QPushButton("New Checklist")
        new_checklist_btn.clicked.connect(self.create_checklist)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(new_checklist_btn)
        layout.addLayout(header)
        
        # Main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Checklist list
        checklist_list_widget = QWidget()
        checklist_list_layout = QVBoxLayout(checklist_list_widget)
        
        self.checklist_list = QListWidget()
        self.checklist_list.currentItemChanged.connect(self.on_checklist_selected)
        checklist_list_layout.addWidget(self.checklist_list)
        
        # Checklist actions
        checklist_actions = QHBoxLayout()
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_checklist)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_checklist)
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_checklist)
        
        checklist_actions.addWidget(self.rename_btn)
        checklist_actions.addWidget(self.delete_btn)
        checklist_actions.addWidget(self.export_btn)
        checklist_list_layout.addLayout(checklist_actions)
        
        # Checklist content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Use the new ChecklistItemsWidget
        self.items_list = ChecklistItemsWidget(self)
        self.items_list.items_reordered.connect(self.on_items_reordered)
        self.items_list.item_check_changed.connect(self.on_item_check_changed)
        # Connect editingFinished signal from the item delegate
        self.items_list.itemDelegate().commitData.connect(self.on_item_edited)
        content_layout.addWidget(self.items_list)
        
        # Item actions
        item_actions = QHBoxLayout()
        self.add_item_btn = QPushButton("Add Item")
        self.add_item_btn.clicked.connect(self.add_item)
        self.remove_item_btn = QPushButton("Remove Item")
        self.remove_item_btn.clicked.connect(self.remove_item)
        self.clear_completed_btn = QPushButton("Clear Completed") # New button
        self.clear_completed_btn.clicked.connect(self.clear_completed_items) # Connect signal
        
        item_actions.addWidget(self.add_item_btn)
        item_actions.addWidget(self.remove_item_btn)
        item_actions.addWidget(self.clear_completed_btn) # Add button to layout
        content_layout.addLayout(item_actions)
        
        # Add widgets to splitter
        splitter.addWidget(checklist_list_widget)
        splitter.addWidget(content_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Initialize button states
        self.update_button_states()

    def load_checklists(self):
        # Ensure the directory exists (though it should as it's the script's dir)
        os.makedirs(self.data_dir, exist_ok=True)
        
        if os.path.exists(self.checklists_file):
            try:
                with open(self.checklists_file, 'r') as f:
                    self.checklists = json.load(f)
            except json.JSONDecodeError:
                print("Error reading checklists.json, starting with empty list.")
                self.checklists = [] # Start fresh if file is corrupt
        else:
            self.checklists = [] # Start with empty list if file doesn't exist
        
        self.update_checklist_list()
        # Select first checklist if available
        if self.checklists:
            self.checklist_list.setCurrentRow(0)
        else:
            self.update_items_list() # Ensure items list is cleared if no checklists

    def save_checklists(self):
        try:
            with open(self.checklists_file, 'w') as f:
                json.dump(self.checklists, f, indent=4)
        except IOError as e:
            print(f"Error saving checklists: {e}")
            if self.parent: # Show error in status bar if possible
                self.parent.statusBar().showMessage(f"Error saving checklists: {e}", 5000)

    def create_checklist(self):
        name, ok = QInputDialog.getText(self, "New Checklist", "Enter checklist name:")
        if ok and name:
            checklist = {
                "name": name,
                "items": []
            }
            self.checklists.append(checklist)
            self.save_checklists()
            self.update_checklist_list()
            self.checklist_list.setCurrentRow(len(self.checklists) - 1)

    def update_checklist_list(self):
        self.checklist_list.clear()
        for checklist in self.checklists:
            self.checklist_list.addItem(checklist["name"])

    def on_checklist_selected(self, current, previous):
        if current: 
            self.current_checklist_index = self.checklist_list.row(current)
        else:
            self.current_checklist_index = -1
        self.update_items_list()
        self.update_button_states()

    def update_items_list(self):
        self.items_list.blockSignals(True)
        self.items_list.clear()
        if self.current_checklist_index >= 0 and self.current_checklist_index < len(self.checklists):
            checklist = self.checklists[self.current_checklist_index]
            for item_data in checklist["items"]:
                # Use the custom ChecklistItem
                list_item = ChecklistItem(item_data)
                self.items_list.addItem(list_item)
        self.items_list.blockSignals(False)

    def add_item(self):
        if self.current_checklist_index < 0:
            return
            
        text, ok = QInputDialog.getText(self, "Add Item", "Enter item text:")
        if ok and text:
            item_data = {"text": text, "checked": False}
            self.checklists[self.current_checklist_index]["items"].append(item_data)
            self.save_checklists()
            # Add using the custom item
            self.items_list.blockSignals(True)
            list_item = ChecklistItem(item_data)
            self.items_list.addItem(list_item)
            self.items_list.blockSignals(False)

    def on_items_reordered(self):
        """Update the internal data order after drag-and-drop."""
        if self.current_checklist_index < 0:
            return
            
        new_items_order = []
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            if isinstance(item, ChecklistItem):
                new_items_order.append(item.item_data)
                
        self.checklists[self.current_checklist_index]["items"] = new_items_order
        self.save_checklists()

    def on_item_check_changed(self, row, is_checked):
        """Handle check state changes from the ChecklistItemsWidget."""
        if self.current_checklist_index < 0 or row >= len(self.checklists[self.current_checklist_index]["items"]):
            return
        # Data was already updated by the signal handler in ChecklistItemsWidget
        # Just save the checklists
        self.save_checklists()

    def on_item_edited(self, editor):
        """Handle finished editing an item's text."""
        row = self.items_list.currentRow()
        item = self.items_list.item(row)
        if not isinstance(item, ChecklistItem) or self.current_checklist_index < 0:
            return

        new_text = item.text() # The item's text is already updated by the delegate
        # Update the data store
        self.checklists[self.current_checklist_index]["items"][row]["text"] = new_text
        self.save_checklists()

    def remove_item(self):
        current_item_row = self.items_list.currentRow()
        if self.current_checklist_index < 0 or current_item_row < 0:
            return
            
        checklist = self.checklists[self.current_checklist_index]
        checklist["items"].pop(current_item_row)
        self.save_checklists()
        self.update_items_list()
        self.update_button_states() # Update buttons as selected item is gone

    def rename_checklist(self):
        if self.current_checklist_index < 0:
            return
            
        current_name = self.checklists[self.current_checklist_index]["name"]
        new_name, ok = QInputDialog.getText(self, "Rename Checklist", "Enter new name:", text=current_name)
        if ok and new_name:
            self.checklists[self.current_checklist_index]["name"] = new_name
            self.save_checklists()
            self.update_checklist_list()
            self.checklist_list.setCurrentRow(self.current_checklist_index) # Re-select the renamed item

    def delete_checklist(self):
        if self.current_checklist_index < 0:
            return
            
        reply = QMessageBox.question(self, "Delete Checklist",
                                   "Are you sure you want to delete this checklist?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.checklists.pop(self.current_checklist_index)
            self.current_checklist_index = -1 # Reset index
            self.save_checklists()
            self.update_checklist_list()
            self.update_items_list() # Clear items list
            self.update_button_states()

    def export_checklist(self):
        if self.current_checklist_index < 0:
            return
            
        checklist = self.checklists[self.current_checklist_index]
        default_filename = f"{checklist['name']}.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Checklist",
                                                 default_filename, "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(f"Checklist: {checklist['name']}\n\n")
                    for item in checklist["items"]:
                        status = "[X]" if item["checked"] else "[ ]"
                        f.write(f"{status} {item['text']}\n")
                if self.parent:
                    self.parent.statusBar().showMessage(f"Checklist exported to {file_path}", 5000)
            except IOError as e:
                QMessageBox.warning(self, "Export Error", f"Could not export checklist: {e}")

    def clear_completed_items(self):
        """Remove all checked items from the current checklist."""
        if self.current_checklist_index < 0:
            return
            
        checklist = self.checklists[self.current_checklist_index]
        # Create a new list containing only the unchecked items
        checklist['items'] = [item for item in checklist['items'] if not item['checked']]
        
        self.save_checklists()
        self.update_items_list() # Refresh UI
        self.update_button_states()

    def update_button_states(self):
        has_checklist = self.current_checklist_index >= 0
        # Check if there's a currently selected item in the items list
        has_selected_item = self.items_list.currentRow() >= 0
        
        self.rename_btn.setEnabled(has_checklist)
        self.delete_btn.setEnabled(has_checklist)
        self.export_btn.setEnabled(has_checklist)
        self.add_item_btn.setEnabled(has_checklist)
        self.remove_item_btn.setEnabled(has_selected_item) # Enable only if an item is selected
        self.clear_completed_btn.setEnabled(has_checklist) # Enable if a checklist is selected

    def add_item_to_current_list(self, item_text):
        """Public method to add an item from external sources (like AutoOrganise)"""
        if self.current_checklist_index < 0:
            # If no checklist is selected, try creating a default one or adding to the first one
            if not self.checklists:
                self.create_checklist() # Create a default checklist if none exist
                # Check if creation was successful and a list is now selected
                if self.current_checklist_index < 0:
                    print("Could not add item: No checklist selected or created.")
                    return
            else:
                # Select the first checklist if none is selected
                self.checklist_list.setCurrentRow(0)
                if self.current_checklist_index < 0: # Check again if selection worked
                    print("Could not add item: Could not select the first checklist.")
                    return

        item_data = {"text": item_text, "checked": False}
        self.checklists[self.current_checklist_index]["items"].append(item_data)
        self.save_checklists()
        # Add using the custom item
        self.items_list.blockSignals(True)
        list_item = ChecklistItem(item_data)
        self.items_list.addItem(list_item)
        self.items_list.blockSignals(False) 