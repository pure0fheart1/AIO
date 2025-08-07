import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QSplitter, QInputDialog, QMessageBox, QFileDialog,
                            QAbstractItemView, QStackedWidget) # Added QStackedWidget for register hint
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
        # Determine project root based on this file's location (widgets/pages/)
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(script_dir, '..', '..')) # Up two levels
        except NameError:
            # Fallback if __file__ is not defined
            project_root = os.path.abspath(os.path.join(os.getcwd()))

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
        # This requires checking if itemDelegate() is valid first
        delegate = self.items_list.itemDelegate()
        if delegate:
             delegate.commitData.connect(self.on_item_edited)
        else:
             print("Warning: Could not connect commitData signal for ChecklistManager item editing.")

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
        # Ensure the directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        if os.path.exists(self.checklists_file):
            try:
                with open(self.checklists_file, 'r') as f:
                    self.checklists = json.load(f)
            except json.JSONDecodeError:
                print("Error reading checklists.json, starting with empty list.")
                self.checklists = [] # Start fresh if file is corrupt
            except Exception as e:
                 print(f"Error loading checklists: {e}")
                 self.checklists = []
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
            # Ensure directory exists before writing
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.checklists_file, 'w') as f:
                json.dump(self.checklists, f, indent=4)
        except IOError as e:
            print(f"Error saving checklists: {e}")
            if self.parent and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Error saving checklists: {e}", 5000)
        except Exception as e:
             print(f"Unexpected error saving checklists: {e}")

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
            
    def add_item_to_current_list(self, item_text):
        """Public method to add an item from external sources (like AutoOrganise)"""
        if self.current_checklist_index < 0:
            # If no checklist is selected, try creating a default one or adding to the first one
            if not self.checklists:
                # Try creating a default checklist named 'Tasks'
                default_name = "Tasks"
                checklist = {"name": default_name, "items": []}
                self.checklists.append(checklist)
                self.save_checklists()
                self.update_checklist_list()
                self.checklist_list.setCurrentRow(len(self.checklists) - 1)
                # Check if creation was successful and a list is now selected
                if self.current_checklist_index < 0:
                    print("Could not add item: Failed to create default checklist.")
                    return
            else:
                # Select the first checklist if none is selected
                if self.checklist_list.currentRow() < 0:
                    self.checklist_list.setCurrentRow(0)
                # Update current index based on selection
                self.current_checklist_index = self.checklist_list.currentRow()
                if self.current_checklist_index < 0: # Check again if selection worked
                    print("Could not add item: Could not select the first checklist.")
                    return

        # Now add the item to the selected list
        item_data = {"text": item_text, "checked": False}
        try:
            self.checklists[self.current_checklist_index]["items"].append(item_data)
            self.save_checklists()
            # Add using the custom item
            self.items_list.blockSignals(True)
            list_item = ChecklistItem(item_data)
            self.items_list.addItem(list_item)
            self.items_list.blockSignals(False) 
            print(f"Added task '{item_text}' to checklist '{self.checklists[self.current_checklist_index]['name']}'")
        except IndexError:
             print(f"Error adding item: current_checklist_index ({self.current_checklist_index}) is out of bounds.")
        except Exception as e:
             print(f"Unexpected error adding item to checklist: {e}")

    def on_items_reordered(self):
        """Update the internal data order after drag-and-drop."""
        if self.current_checklist_index < 0:
            return
            
        new_items_order = []
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            if isinstance(item, ChecklistItem):
                new_items_order.append(item.item_data)
                
        try:
            self.checklists[self.current_checklist_index]["items"] = new_items_order
            self.save_checklists()
        except IndexError:
            print(f"Error reordering items: current_checklist_index ({self.current_checklist_index}) is out of bounds.")
        except Exception as e:
             print(f"Unexpected error reordering items: {e}")

    def on_item_check_changed(self, row, is_checked):
        """Handle check state changes from the ChecklistItemsWidget."""
        if self.current_checklist_index < 0:
             print("Warning: Item check changed but no checklist selected.")
             return
        try:
            # Data should already be updated in the ChecklistItem instance by ChecklistItemsWidget
            # Just save the checklists state
            self.save_checklists()
        except IndexError:
             print(f"Error saving check state: current_checklist_index ({self.current_checklist_index}) or row ({row}) out of bounds.")
        except Exception as e:
             print(f"Unexpected error saving item check state: {e}")


    def on_item_edited(self, editor):
        """Handle finished editing an item's text."""
        # The editor's model index should correspond to the item
        index = self.items_list.indexAt(editor.pos())
        if not index.isValid():
            return # Should not happen if triggered by commitData
            
        row = index.row()
        item = self.items_list.item(row)
        if not isinstance(item, ChecklistItem) or self.current_checklist_index < 0:
            return

        new_text = item.text() # The item's text is already updated by the delegate
        # Update the data store
        try:
            item.item_data["text"] = new_text # Update internal data just in case
            self.checklists[self.current_checklist_index]["items"][row]["text"] = new_text
            self.save_checklists()
        except IndexError:
             print(f"Error saving edited item: current_checklist_index ({self.current_checklist_index}) or row ({row}) out of bounds.")
        except Exception as e:
             print(f"Unexpected error saving edited item: {e}")

    def remove_item(self):
        current_item_row = self.items_list.currentRow()
        if self.current_checklist_index < 0 or current_item_row < 0:
            return
            
        try:
            checklist = self.checklists[self.current_checklist_index]
            checklist["items"].pop(current_item_row)
            self.save_checklists()
            # Take item removes it visually
            self.items_list.takeItem(current_item_row)
            self.update_button_states() # Update buttons as selected item is gone
        except IndexError:
             print(f"Error removing item: current_checklist_index ({self.current_checklist_index}) or row ({current_item_row}) out of bounds.")
        except Exception as e:
             print(f"Unexpected error removing item: {e}")


    def rename_checklist(self):
        if self.current_checklist_index < 0:
            return
            
        try:
            current_name = self.checklists[self.current_checklist_index]["name"]
            new_name, ok = QInputDialog.getText(self, "Rename Checklist", "Enter new name:", text=current_name)
            if ok and new_name and new_name != current_name:
                self.checklists[self.current_checklist_index]["name"] = new_name
                self.save_checklists()
                # Update visual list
                self.checklist_list.item(self.current_checklist_index).setText(new_name)
        except IndexError:
             print(f"Error renaming checklist: current_checklist_index ({self.current_checklist_index}) is out of bounds.")
        except Exception as e:
             print(f"Unexpected error renaming checklist: {e}")


    def delete_checklist(self):
        if self.current_checklist_index < 0:
            return
            
        reply = QMessageBox.question(self, "Delete Checklist",
                                   "Are you sure you want to delete this checklist?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.checklists.pop(self.current_checklist_index)
                # Take item visually removes it
                self.checklist_list.takeItem(self.current_checklist_index)
                # Reset index and clear items list
                self.current_checklist_index = -1 
                self.items_list.clear()
                self.save_checklists()
                self.update_button_states()
            except IndexError:
                 print(f"Error deleting checklist: current_checklist_index was likely already invalid.")
                 # Try to reset state anyway
                 self.current_checklist_index = -1
                 self.update_checklist_list()
                 self.items_list.clear()
                 self.update_button_states()
            except Exception as e:
                 print(f"Unexpected error deleting checklist: {e}")


    def export_checklist(self):
        if self.current_checklist_index < 0:
            return
            
        try:
            checklist = self.checklists[self.current_checklist_index]
            default_filename = f"{checklist['name']}.txt"
            # Ensure data directory exists for default save location (optional)
            os.makedirs(self.data_dir, exist_ok=True)
            save_dir = self.data_dir 
            default_path = os.path.join(save_dir, default_filename)

            file_path, _ = QFileDialog.getSaveFileName(self, "Export Checklist",
                                                     default_path, "Text Files (*.txt);;All Files (*)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Checklist: {checklist['name']}\n\n")
                    for item in checklist["items"]:
                        status = "[X]" if item["checked"] else "[ ]"
                        f.write(f"{status} {item['text']}\n")
                if self.parent and hasattr(self.parent, 'statusBar'):
                    self.parent.statusBar().showMessage(f"Checklist exported to {file_path}", 5000)

        except IndexError:
            print(f"Error exporting checklist: current_checklist_index ({self.current_checklist_index}) is out of bounds.")
        except IOError as e:
            QMessageBox.warning(self, "Export Error", f"Could not export checklist: {e}")
        except Exception as e:
            print(f"Unexpected error exporting checklist: {e}")

    def clear_completed_items(self):
        """Remove all checked items from the current checklist."""
        if self.current_checklist_index < 0:
            return
        
        try:    
            checklist = self.checklists[self.current_checklist_index]
            initial_count = len(checklist['items'])
            # Create a new list containing only the unchecked items
            checklist['items'] = [item for item in checklist['items'] if not item['checked']]
            removed_count = initial_count - len(checklist['items'])
            
            if removed_count > 0:
                self.save_checklists()
                self.update_items_list() # Refresh UI
                if self.parent and hasattr(self.parent, 'statusBar'):
                    self.parent.statusBar().showMessage(f"Removed {removed_count} completed items.", 3000)
            else:
                 if self.parent and hasattr(self.parent, 'statusBar'):
                    self.parent.statusBar().showMessage("No completed items to remove.", 3000)

        except IndexError:
             print(f"Error clearing completed items: current_checklist_index ({self.current_checklist_index}) is out of bounds.")
        except Exception as e:
             print(f"Unexpected error clearing completed items: {e}")

    def update_button_states(self):
        has_checklist = self.current_checklist_index >= 0
        # Check if there's a currently selected item in the items list
        has_selected_item = self.items_list.currentRow() >= 0
        
        self.rename_btn.setEnabled(has_checklist)
        self.delete_btn.setEnabled(has_checklist)
        self.export_btn.setEnabled(has_checklist)
        self.add_item_btn.setEnabled(has_checklist)
        self.remove_item_btn.setEnabled(has_selected_item and has_checklist) # Need item and list
        self.clear_completed_btn.setEnabled(has_checklist)

    # --- Registration Method --- 
    def register(self, stack: QStackedWidget):
        """ Placeholder for factory registration method """
        print(f"ChecklistManager register called (Placeholder)")
        pass 