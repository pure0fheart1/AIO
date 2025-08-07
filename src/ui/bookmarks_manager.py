from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                            QMessageBox, QInputDialog, QFileDialog, QColorDialog, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import json
import os
from datetime import datetime
import traceback

class BookmarkItem(QListWidgetItem):
    def __init__(self, title, url, description="", color=None, parent=None):
        super().__init__(title, parent)
        self.url = url
        self.description = description
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.color = color or "#FFFFFF"
        self.setData(Qt.UserRole, {
            "url": url,
            "description": description,
            "color": self.color,
            "created": self.created_date
        })
        self.updateAppearance()
        
    def updateAppearance(self):
        self.setBackground(QColor(self.color))
        # If color is dark, use white text
        color = QColor(self.color)
        if color.lightness() < 128:
            self.setForeground(QColor(Qt.white))
        else:
            self.setForeground(QColor(Qt.black))

class BookmarksManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Define data file path relative to this script (src/ui/...)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_dir = os.path.join(project_root, 'data')
        self.bookmarks_file = os.path.join(self.data_dir, "bookmarks.json")
        self.bookmarks = []
        self.setup_ui()
        self.load_bookmarks()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        
        # Header with title and new bookmark button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        header_label = QLabel("Bookmarks")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.new_bookmark_button = QPushButton("New Bookmark")
        self.new_bookmark_button.setMaximumWidth(120)
        self.new_bookmark_button.clicked.connect(self.create_new_bookmark)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.new_bookmark_button)
        
        # Splitter for bookmark list and details
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Bookmark list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)
        
        list_header = QLabel("Your Bookmarks")
        list_header.setStyleSheet("font-size: 12px; font-weight: bold;")
        
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemClicked.connect(self.load_bookmark_details)
        self.bookmarks_list.itemDoubleClicked.connect(self.open_bookmark_link)
        self.bookmarks_list.setMinimumWidth(180)
        
        list_layout.addWidget(list_header)
        list_layout.addWidget(self.bookmarks_list)
        
        # Bookmark details area
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(6, 6, 6, 6)
        details_layout.setSpacing(8)
        
        details_header = QLabel("Bookmark Details")
        details_header.setStyleSheet("font-size: 12px; font-weight: bold;")
        details_layout.addWidget(details_header)
        
        # Form layout for fields
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(6)
        
        # Title field
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_label.setFixedWidth(50)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Bookmark Title")
        self.title_edit.textChanged.connect(self.bookmark_modified)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        
        # URL field
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        url_label.setFixedWidth(50)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("URL")
        self.url_edit.textChanged.connect(self.bookmark_modified)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        
        # Description field
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Notes:")
        desc_label.setFixedWidth(50)
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description (optional)")
        self.description_edit.textChanged.connect(self.bookmark_modified)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_edit)
        
        form_layout.addLayout(title_layout)
        form_layout.addLayout(url_layout)
        form_layout.addLayout(desc_layout)
        
        details_layout.addWidget(form_widget)
        
        # Bookmark actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        
        # First row of buttons
        primary_actions = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.setMaximumWidth(100)
        self.save_button.clicked.connect(self.save_current_bookmark)
        self.save_button.setEnabled(False)
        
        self.open_link_button = QPushButton("Open Link")
        self.open_link_button.setMaximumWidth(100)
        self.open_link_button.clicked.connect(self.open_bookmark_link)
        self.open_link_button.setEnabled(False)
        
        primary_actions.addWidget(self.save_button)
        primary_actions.addWidget(self.open_link_button)
        primary_actions.addStretch()
        
        # Second row of buttons
        secondary_actions = QHBoxLayout()
        
        self.rename_button = QPushButton("Rename")
        self.rename_button.setMaximumWidth(100)
        self.rename_button.clicked.connect(self.rename_bookmark)
        self.rename_button.setEnabled(False)
        
        self.change_color_button = QPushButton("Change Color")
        self.change_color_button.setMaximumWidth(100)
        self.change_color_button.clicked.connect(self.change_bookmark_color)
        self.change_color_button.setEnabled(False)
        
        secondary_actions.addWidget(self.rename_button)
        secondary_actions.addWidget(self.change_color_button)
        secondary_actions.addStretch()
        
        # Third row of buttons
        tertiary_actions = QHBoxLayout()
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setMaximumWidth(100)
        self.delete_button.clicked.connect(self.delete_current_bookmark)
        self.delete_button.setEnabled(False)
        
        self.export_button = QPushButton("Export")
        self.export_button.setMaximumWidth(100)
        self.export_button.clicked.connect(self.export_bookmarks)
        self.export_button.setEnabled(False)
        
        tertiary_actions.addWidget(self.delete_button)
        tertiary_actions.addWidget(self.export_button)
        tertiary_actions.addStretch()
        
        button_layout = QVBoxLayout()
        button_layout.setSpacing(4)
        button_layout.addLayout(primary_actions)
        button_layout.addLayout(secondary_actions)
        button_layout.addLayout(tertiary_actions)
        
        actions_layout.addLayout(button_layout)
        
        details_layout.addWidget(actions_widget)
        details_layout.addStretch()
        
        # Add widgets to splitter
        self.splitter.addWidget(list_widget)
        self.splitter.addWidget(details_widget)
        
        # Set splitter size ratio (35% list, 65% details)
        self.splitter.setSizes([35, 65])
        
        # Add everything to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.splitter, 1)
        
        self.setLayout(layout)
        
    def load_bookmarks(self):
        os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            else:
                self.bookmarks = [] # Start empty if file doesn't exist
        except json.JSONDecodeError:
            print(f"Error reading {self.bookmarks_file}. Starting with empty list.")
            self.bookmarks = []
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            QMessageBox.warning(self, "Load Error", f"Could not load bookmarks: {e}")
            self.bookmarks = [] # Fallback to empty list on other errors
            
        self.populate_list()

    def save_bookmarks(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=4)
        except IOError as e:
            print(f"Error saving bookmarks: {e}")
            QMessageBox.critical(self, "Save Error", f"Could not save bookmarks: {e}")
            if self.parent:
                self.parent.statusBar().showMessage(f"Error saving bookmarks: {e}", 5000)
        except Exception as e:
            print(f"Unexpected error saving bookmarks: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred while saving bookmarks: {e}")

    def populate_list(self):
        """Populate the bookmarks list widget from self.bookmarks data."""
        self.bookmarks_list.clear()
        for bookmark in self.bookmarks:
            # Ensure essential keys exist, provide defaults if not
            title = bookmark.get('title', 'Untitled')
            url = bookmark.get('url', '')
            description = bookmark.get('description', '')
            color = bookmark.get('color', "#FFFFFF")
            created = bookmark.get('created', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            item = BookmarkItem(title, url, description, color)
            # Ensure all data is set for the item's UserRole
            item.setData(Qt.UserRole, {
                "url": url,
                "description": description,
                "color": color,
                "created": created
            })
            self.bookmarks_list.addItem(item)

    def create_new_bookmark(self):
        title, ok = QInputDialog.getText(self, "New Bookmark", "Bookmark Title:")
        
        if ok and title:
            url, ok = QInputDialog.getText(self, "New Bookmark", "URL:")
            
            if ok and url:
                # Validate URL format
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                    
                description, ok = QInputDialog.getText(self, "New Bookmark", "Description (optional):")
                
                if ok:
                    # Create bookmark data dictionary
                    bookmark_data = {
                        'title': title,
                        'url': url,
                        'description': description,
                        'color': "#FFFFFF", # Default color
                        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.bookmarks.append(bookmark_data)
                    
                    # Save the updated bookmarks list
                    self.save_bookmarks()
                    
                    # Update UI List
                    item = BookmarkItem(title, url, description)
                    # Set UserRole Data for the new item
                    item.setData(Qt.UserRole, {
                        "url": bookmark_data['url'],
                        "description": bookmark_data['description'],
                        "color": bookmark_data['color'],
                        "created": bookmark_data['created']
                    })
                    self.bookmarks_list.addItem(item)
                    self.bookmarks_list.setCurrentItem(item)
                    self.load_bookmark_details(item)
            
    def load_bookmark_details(self, item):
        if item:
            item_data = item.data(Qt.UserRole)
            
            self.title_edit.setText(item.text())
            self.url_edit.setText(item_data['url'])
            self.description_edit.setText(item_data['description'])
            
            # Enable buttons
            self.save_button.setEnabled(False)  # No changes yet
            self.open_link_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.change_color_button.setEnabled(True)
            self.rename_button.setEnabled(True)
            self.export_button.setEnabled(True)
            
    def bookmark_modified(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            self.save_button.setEnabled(True)
            
    def save_current_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            item_index = self.bookmarks_list.row(current_item)
            if item_index >= 0 and item_index < len(self.bookmarks):
                # Get the corresponding dictionary from our data list
                bookmark_data = self.bookmarks[item_index]
                
                # Update the dictionary
                bookmark_data['title'] = self.title_edit.text()
                bookmark_data['url'] = self.url_edit.text()
                bookmark_data['description'] = self.description_edit.text()
                # color is updated in change_bookmark_color
                
                # Update the list item text if title changed
                if current_item.text() != bookmark_data['title']:
                    current_item.setText(bookmark_data['title'])
                
                # Update the item's UserRole data to match
                current_item.setData(Qt.UserRole, {
                    "url": bookmark_data['url'],
                    "description": bookmark_data['description'],
                    "color": bookmark_data['color'],
                    "created": bookmark_data['created']
                })
                
                self.save_button.setEnabled(False)
                self.save_bookmarks()
                
                if self.parent:
                    self.parent.statusBar().showMessage("Bookmark saved")
            else:
                print(f"Error: Could not find bookmark data for index {item_index}")

    def delete_current_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            reply = QMessageBox.question(self, "Confirm Delete", 
                                        f"Are you sure you want to delete '{current_item.text()}'?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                row = self.bookmarks_list.row(current_item)
                if row >= 0 and row < len(self.bookmarks):
                    # Remove from data list first
                    del self.bookmarks[row]
                    
                    # Remove from UI list
                    self.bookmarks_list.takeItem(row)
                    
                    # Save the updated data
                    self.save_bookmarks()
                    
                    # Clear form and disable buttons
                    self.title_edit.clear()
                    self.url_edit.clear()
                    self.description_edit.clear()
                    
                    self.save_button.setEnabled(False)
                    self.delete_button.setEnabled(False)
                    self.change_color_button.setEnabled(False)
                    self.rename_button.setEnabled(False)
                    self.export_button.setEnabled(False)
                    
                    self.parent.statusBar().showMessage("Bookmark deleted")
                else:
                     print(f"Error: Could not find bookmark data for index {row} to delete")

    def change_bookmark_color(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            item_index = self.bookmarks_list.row(current_item)
            if item_index >= 0 and item_index < len(self.bookmarks):
                item_data = current_item.data(Qt.UserRole)
                current_color = QColor(item_data['color'])
                
                color = QColorDialog.getColor(current_color, self, "Choose Color")
                
                if color.isValid():
                    # Update color
                    item_data['color'] = color.name()
                    current_item.setData(Qt.UserRole, item_data)
                    current_item.color = color.name()
                    current_item.updateAppearance()
                    
                    # Save bookmarks data
                    self.save_bookmarks()
            else:
                print(f"Error: Could not find bookmark data for index {item_index}")

    def rename_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            item_index = self.bookmarks_list.row(current_item)
            if item_index >= 0 and item_index < len(self.bookmarks):
                new_title, ok = QInputDialog.getText(self, "Rename Bookmark", 
                                                   "New Title:", text=current_item.text())
                
                if ok and new_title and new_title != self.bookmarks[item_index]['title']:
                    # Update title
                    self.bookmarks[item_index]['title'] = new_title
                    current_item.setText(new_title)
                    
                    # Save bookmarks data
                    self.save_bookmarks()
            else:
                 print(f"Error: Could not find bookmark data for index {item_index}")

    def export_bookmarks(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Bookmarks", 
            os.path.join(os.path.expanduser("~"), "bookmarks.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Copy the bookmarks data file
                import shutil
                shutil.copy2(self.bookmarks_file, file_path)
                self.parent.statusBar().showMessage(f"Bookmarks exported to {file_path}")
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not export bookmarks: {str(e)}")

    def open_bookmark_link(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            item_data = current_item.data(Qt.UserRole)
            url = item_data['url']
            
            try:
                import webbrowser
                webbrowser.open(url)
                self.parent.statusBar().showMessage(f"Opening {url}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open URL: {str(e)}") 