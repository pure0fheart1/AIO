import os
import json
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QListWidget, QListWidgetItem, QSplitter, 
                            QTextEdit, QGroupBox, QFormLayout, QMessageBox, QInputDialog,
                            QFileDialog, QDialog, QScrollArea, QTreeWidget, QTreeWidgetItem,
                            QMenu, QAction)
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QColor, QDrag, QIcon
import traceback

class InformationLibrary(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Define data file path relative to this script (src/ui/...)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_dir = os.path.join(project_root, 'data')
        self.library_file = os.path.join(self.data_dir, "info_library.json")
        self.library = {"categories": [], "entries": {}}
        self.setup_ui()
        self.load_library()
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        
        # Header with title and description
        header_layout = QVBoxLayout()
        title_label = QLabel("Information Library")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        description_label = QLabel(
            "Store, organize, and search through your knowledge base. "
            "Add articles, links, notes, and references for easy access."
        )
        description_label.setWordWrap(True)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(description_label)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search library...")
        self.search_input.textChanged.connect(self.filter_entries)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.filter_entries)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        
        # Main content area with splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left panel with categories and actions
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Categories list
        category_group = QGroupBox("Categories")
        category_layout = QVBoxLayout()
        
        self.category_list = QListWidget()
        self.category_list.addItems(self.library["categories"])
        self.category_list.currentTextChanged.connect(self.change_category)
        self.category_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_list.customContextMenuRequested.connect(self.show_category_context_menu)
        
        # Category buttons layout
        category_buttons_layout = QHBoxLayout()
        
        add_category_btn = QPushButton("Add Category")
        add_category_btn.clicked.connect(self.add_category)
        
        remove_category_btn = QPushButton("Remove Category")
        remove_category_btn.clicked.connect(self.remove_category)
        
        category_buttons_layout.addWidget(add_category_btn)
        category_buttons_layout.addWidget(remove_category_btn)
        
        category_layout.addWidget(self.category_list)
        category_layout.addLayout(category_buttons_layout)
        category_group.setLayout(category_layout)
        
        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        self.add_entry_btn = QPushButton("Add New Entry")
        self.add_entry_btn.clicked.connect(self.add_entry)
        
        self.add_subpage_btn = QPushButton("Add Subpage")
        self.add_subpage_btn.clicked.connect(self.add_subpage)
        self.add_subpage_btn.setEnabled(False)  # Enabled when an entry is selected
        
        self.import_btn = QPushButton("Import Content")
        self.import_btn.clicked.connect(self.import_content)
        
        self.export_btn = QPushButton("Export Library")
        self.export_btn.clicked.connect(self.export_library)
        
        actions_layout.addWidget(self.add_entry_btn)
        actions_layout.addWidget(self.add_subpage_btn)
        actions_layout.addWidget(self.import_btn)
        actions_layout.addWidget(self.export_btn)
        actions_group.setLayout(actions_layout)
        
        # Add to left panel
        left_layout.addWidget(category_group)
        left_layout.addWidget(actions_group)
        left_layout.addStretch()
        
        # Right panel with entries
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Category header
        self.category_header = QLabel("General")
        self.category_header.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Replace list widget with tree widget for hierarchical structure
        self.entries_tree = QTreeWidget()
        self.entries_tree.setHeaderLabels(["Title"])
        self.entries_tree.setMinimumHeight(300)
        self.entries_tree.itemClicked.connect(self.show_entry_details)
        self.entries_tree.setDragEnabled(True)
        self.entries_tree.setAcceptDrops(True)
        self.entries_tree.setDropIndicatorShown(True)
        self.entries_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.entries_tree.itemChanged.connect(self.on_item_moved)
        self.entries_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entries_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Entry details
        self.entry_details = QGroupBox("Entry Details")
        details_layout = QVBoxLayout()
        
        self.entry_title_label = QLabel("")
        self.entry_title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.entry_meta_label = QLabel("")
        self.entry_meta_label.setStyleSheet("font-size: 12px; color: #666;")
        
        self.entry_content = QTextEdit()
        self.entry_content.setReadOnly(True)
        
        # Entry actions
        entry_actions_layout = QHBoxLayout()
        
        self.edit_entry_btn = QPushButton("Edit")
        self.edit_entry_btn.clicked.connect(self.edit_entry)
        self.edit_entry_btn.setEnabled(False)
        
        self.delete_entry_btn = QPushButton("Delete")
        self.delete_entry_btn.clicked.connect(self.delete_entry)
        self.delete_entry_btn.setEnabled(False)
        
        self.open_url_btn = QPushButton("Open URL")
        self.open_url_btn.clicked.connect(self.open_entry_url)
        self.open_url_btn.setEnabled(False)
        
        entry_actions_layout.addWidget(self.edit_entry_btn)
        entry_actions_layout.addWidget(self.delete_entry_btn)
        entry_actions_layout.addWidget(self.open_url_btn)
        
        # Add to details layout
        details_layout.addWidget(self.entry_title_label)
        details_layout.addWidget(self.entry_meta_label)
        details_layout.addWidget(self.entry_content)
        details_layout.addLayout(entry_actions_layout)
        
        self.entry_details.setLayout(details_layout)
        
        # Add to right panel
        right_layout.addWidget(self.category_header)
        right_layout.addWidget(self.entries_tree)
        right_layout.addWidget(self.entry_details)
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([1, 3])  # Set relative sizes
        
        # Add all elements to main layout
        layout.addLayout(header_layout)
        layout.addLayout(search_layout)
        layout.addWidget(self.splitter, 1)  # 1 is stretch factor
        
        self.setLayout(layout)
    
    def populate_fields(self):
        """Populate fields with existing entry data"""
        if self.entry_data:
            self.title_input.setText(self.entry_data["title"])
            self.tags_input.setText(", ".join(self.entry_data["tags"]))
            self.url_input.setText(self.entry_data["url"])
            self.content_input.setText(self.entry_data["content"])
    
    def get_entry_data(self):
        """Get the entry data from the form"""
        # Process tags - split by comma and strip whitespace
        tags_text = self.tags_input.text()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        return {
            "title": self.title_input.text(),
            "content": self.content_input.toPlainText(),
            "tags": tags,
            "url": self.url_input.text()
        }

    def change_category(self, category_name):
        """Change the current category"""
        if category_name:
            self.current_category = category_name
            self.update_entries_list()
            
            # Clear entry details
            self.clear_entry_details()
    
    def add_category(self):
        """Add a new category"""
        category_name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        
        if ok and category_name:
            if category_name in self.library["categories"]:
                QMessageBox.warning(self, "Duplicate Category", 
                                   f"Category '{category_name}' already exists.")
                return
                
            # Add to categories list
            self.library["categories"].append(category_name)
            self.category_list.addItem(category_name)
            
            # Initialize empty entries list for this category
            self.library["entries"][category_name] = []
            
            # Save the data
            self.save_library()
            
            # Switch to the new category
            self.category_list.setCurrentRow(self.library["categories"].index(category_name))
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Added category: {category_name}")
    
    def add_entry(self):
        """Add a new entry to the current category"""
        dialog = EntryDialog(self)
        
        if dialog.exec_():
            entry_data = dialog.get_entry_data()
            
            # Add metadata
            entry_data["date_added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry_data["date_modified"] = entry_data["date_added"]
            entry_data["id"] = f"{self.current_category[0].lower()}{len(self.library['entries'][self.current_category]) + 1}"
            
            # Add to entries
            self.library["entries"][self.current_category].append(entry_data)
            
            # Update the list
            self.update_entries_list()
            
            # Save the data
            self.save_library()
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Added entry: {entry_data['title']}")
    
    def edit_entry(self):
        """Edit the selected entry"""
        selected_items = self.entries_tree.selectedItems()
        
        if not selected_items:
            return
            
        # Get the selected entry
        entry_data = selected_items[0].data(0, Qt.UserRole)
        
        # Create edit dialog
        dialog = EntryDialog(self, entry_data)
        
        if dialog.exec_():
            updated_data = dialog.get_entry_data()
            
            # Update the entry
            entry_data.update(updated_data)
            entry_data["date_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update the list
            self.update_entries_list()
            
            # Update the details view
            self.show_entry_details(selected_items[0])
            
            # Save the data
            self.save_library()
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Updated entry: {entry_data['title']}")
    
    def delete_entry(self):
        """Delete the selected entry"""
        selected_items = self.entries_tree.selectedItems()
        
        if not selected_items:
            return
            
        # Get the selected entry
        entry_data = selected_items[0].data(0, Qt.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                    f"Are you sure you want to delete '{entry_data['title']}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Remove from entries
            self.library["entries"][self.current_category].remove(entry_data)
            
            # Update the list
            self.update_entries_list()
            
            # Clear the details view
            self.clear_entry_details()
            
            # Save the data
            self.save_library()
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Deleted entry: {entry_data['title']}")
    
    def show_entry_details(self, item):
        """Show details for the selected entry"""
        if not item:
            return
            
        # Get the entry data
        entry_data = item.data(0, Qt.UserRole)
        
        # Update the details view
        self.entry_title_label.setText(entry_data["title"])
        
        # Format metadata
        meta_text = f"Added: {entry_data['date_added']} | Modified: {entry_data['date_modified']}"
        if entry_data["tags"]:
            meta_text += f" | Tags: {', '.join(entry_data['tags'])}"
        self.entry_meta_label.setText(meta_text)
        
        # Set content
        self.entry_content.setText(entry_data["content"])
        
        # Enable buttons
        self.edit_entry_btn.setEnabled(True)
        self.delete_entry_btn.setEnabled(True)
        self.add_subpage_btn.setEnabled(True)
        
        # Enable URL button if URL exists
        if entry_data["url"]:
            self.open_url_btn.setEnabled(True)
        else:
            self.open_url_btn.setEnabled(False)
    
    def clear_entry_details(self):
        """Clear the entry details view"""
        self.entry_title_label.setText("")
        self.entry_meta_label.setText("")
        self.entry_content.setText("")
        
        # Disable buttons
        self.edit_entry_btn.setEnabled(False)
        self.delete_entry_btn.setEnabled(False)
        self.add_subpage_btn.setEnabled(False)
        self.open_url_btn.setEnabled(False)
    
    def open_entry_url(self):
        """Open the URL of the selected entry"""
        selected_items = self.entries_tree.selectedItems()
        
        if not selected_items:
            return
            
        # Get the selected entry
        entry_data = selected_items[0].data(0, Qt.UserRole)
        
        if entry_data["url"]:
            # In a real implementation, this would open the URL in a browser
            # For this demo, just show a message
            QMessageBox.information(self, "Open URL", 
                                   f"Opening URL: {entry_data['url']}\n\n"
                                   "This would normally open in your default web browser.")
    
    def filter_entries(self):
        """Filter entries based on search text"""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            # If search is empty, just show the current category
            self.update_entries_list()
            return
            
        # Clear the list
        self.entries_tree.clear()
        
        # If searching, show results from all categories
        for category, entries in self.library["entries"].items():
            for entry in entries:
                # Search in title, content, and tags
                if (search_text in entry["title"].lower() or 
                    search_text in entry["content"].lower() or 
                    any(search_text in tag.lower() for tag in entry["tags"])):
                    
                    # Create item with category prefix
                    item = QTreeWidgetItem(self.entries_tree, [f"[{category}] {entry['title']}"])
                    item.setData(0, Qt.UserRole, entry)
                    self.entries_tree.addTopLevelItem(item)
        
        # Update header
        self.category_header.setText(f"Search Results: '{search_text}'")
        
        # Clear details
        self.clear_entry_details()
    
    def import_content(self):
        """Import content from various sources"""
        options = ["Text File", "Markdown File", "HTML File", "Website URL"]
        option, ok = QInputDialog.getItem(self, "Import Content", 
                                         "Select import source:", options, 0, False)
        
        if not ok or not option:
            return
            
        if option == "Website URL":
            url, ok = QInputDialog.getText(self, "Import from Website", "Enter URL:")
            if ok and url:
                self.import_from_website(url)
        else:
            # File-based import
            file_types = {
                "Text File": "Text Files (*.txt)",
                "Markdown File": "Markdown Files (*.md *.markdown)",
                "HTML File": "HTML Files (*.html *.htm)"
            }
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"Import from {option}", "", file_types[option]
            )
            
            if file_path:
                self.import_from_file(file_path, option)
    
    def import_from_file(self, file_path, file_type):
        """Import content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Get file name without extension as title
            title = os.path.splitext(os.path.basename(file_path))[0]
            
            # Create entry dialog with pre-filled content
            dialog = EntryDialog(self)
            dialog.title_input.setText(title)
            dialog.content_input.setText(content)
            
            if dialog.exec_():
                entry_data = dialog.get_entry_data()
                
                # Add metadata
                entry_data["date_added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_data["date_modified"] = entry_data["date_added"]
                entry_data["id"] = f"{self.current_category[0].lower()}{len(self.library['entries'][self.current_category]) + 1}"
                
                # Add to entries
                self.library["entries"][self.current_category].append(entry_data)
                
                # Update the list
                self.update_entries_list()
                
                # Save the data
                self.save_library()
                
                if self.parent:
                    self.parent.statusBar().showMessage(f"Imported file: {title}")
                    
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Could not import file: {str(e)}")
    
    def import_from_website(self, url):
        """Import content from a website"""
        try:
            # In a real implementation, this would fetch the website content
            # For this demo, just create a placeholder
            title = url.split("//")[-1].split("/")[0]
            content = f"Content imported from {url}\n\nIn a real implementation, this would extract the main content from the website."
            
            # Create entry dialog with pre-filled content
            dialog = EntryDialog(self)
            dialog.title_input.setText(title)
            dialog.content_input.setText(content)
            dialog.url_input.setText(url)
            
            if dialog.exec_():
                entry_data = dialog.get_entry_data()
                
                # Add metadata
                entry_data["date_added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_data["date_modified"] = entry_data["date_added"]
                entry_data["id"] = f"{self.current_category[0].lower()}{len(self.library['entries'][self.current_category]) + 1}"
                
                # Add to entries
                self.library["entries"][self.current_category].append(entry_data)
                
                # Update the list
                self.update_entries_list()
                
                # Save the data
                self.save_library()
                
                if self.parent:
                    self.parent.statusBar().showMessage(f"Imported website: {title}")
                    
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Could not import website: {str(e)}")
    
    def export_library(self):
        """Export the library to various formats"""
        options = ["JSON", "Markdown", "HTML", "PDF"]
        option, ok = QInputDialog.getItem(self, "Export Library", 
                                         "Select export format:", options, 0, False)
        
        if not ok or not option:
            return
            
        # Get export path
        file_types = {
            "JSON": "JSON Files (*.json)",
            "Markdown": "Markdown Files (*.md)",
            "HTML": "HTML Files (*.html)",
            "PDF": "PDF Files (*.pdf)"
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {option}", "", file_types[option]
        )
        
        if file_path:
            if option == "JSON":
                self.export_as_json(file_path)
            elif option == "Markdown":
                self.export_as_markdown(file_path)
            elif option == "HTML":
                self.export_as_html(file_path)
            elif option == "PDF":
                self.export_as_pdf(file_path)
    
    def export_as_json(self, file_path):
        """Export library as JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.library["entries"], f, indent=2)
                
            if self.parent:
                self.parent.statusBar().showMessage(f"Exported library to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Could not export as JSON: {str(e)}")
    
    def export_as_markdown(self, file_path):
        """Export library as Markdown"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Information Library Export\n\n")
                
                for category in self.library["categories"]:
                    f.write(f"## {category}\n\n")
                    
                    for entry in self.library["entries"].get(category, []):
                        f.write(f"### {entry['title']}\n\n")
                        f.write(f"*Added: {entry['date_added']} | Modified: {entry['date_modified']}*\n\n")
                        
                        if entry['tags']:
                            f.write(f"Tags: {', '.join(entry['tags'])}\n\n")
                            
                        if entry['url']:
                            f.write(f"URL: [{entry['url']}]({entry['url']})\n\n")
                            
                        f.write(f"{entry['content']}\n\n")
                        f.write("---\n\n")
                
            if self.parent:
                self.parent.statusBar().showMessage(f"Exported library to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Could not export as Markdown: {str(e)}")
    
    def export_as_html(self, file_path):
        """Export library as HTML"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write("<title>Information Library Export</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }\n")
                f.write("h1 { color: #2c3e50; }\n")
                f.write("h2 { color: #3498db; border-bottom: 1px solid #3498db; }\n")
                f.write("h3 { color: #2c3e50; }\n")
                f.write(".meta { color: #7f8c8d; font-style: italic; }\n")
                f.write(".tags { color: #16a085; }\n")
                f.write(".entry { margin-bottom: 30px; border-bottom: 1px dashed #bdc3c7; padding-bottom: 20px; }\n")
                f.write("</style>\n</head>\n<body>\n")
                
                f.write("<h1>Information Library Export</h1>\n")
                
                for category in self.library["categories"]:
                    f.write(f"<h2>{category}</h2>\n")
                    
                    for entry in self.library["entries"].get(category, []):
                        f.write("<div class='entry'>\n")
                        f.write(f"<h3>{entry['title']}</h3>\n")
                        f.write(f"<p class='meta'>Added: {entry['date_added']} | Modified: {entry['date_modified']}</p>\n")
                        
                        if entry['tags']:
                            f.write(f"<p class='tags'>Tags: {', '.join(entry['tags'])}</p>\n")
                            
                        if entry['url']:
                            f.write(f"<p>URL: <a href='{entry['url']}' target='_blank'>{entry['url']}</a></p>\n")
                            
                        # Convert content to HTML paragraphs
                        content_html = entry['content'].replace('\n\n', '</p><p>')
                        f.write(f"<p>{content_html}</p>\n")
                        
                        f.write("</div>\n")
                
                f.write("</body>\n</html>")
                
            if self.parent:
                self.parent.statusBar().showMessage(f"Exported library to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Could not export as HTML: {str(e)}")
    
    def export_as_pdf(self, file_path):
        """Export library as PDF"""
        try:
            # For a real implementation, you would use a PDF library like reportlab
            # For this demo, we'll just show a message
            QMessageBox.information(self, "PDF Export", 
                                   "PDF export would normally create a formatted PDF document.\n\n"
                                   "This feature requires the reportlab library.")
            
            if self.parent:
                self.parent.statusBar().showMessage(f"PDF export simulated to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Could not export as PDF: {str(e)}")

    def load_library(self):
        os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists
        try:
            if os.path.exists(self.library_file):
                with open(self.library_file, 'r', encoding='utf-8') as f:
                    self.library = json.load(f)
                    # Ensure basic structure exists if file was empty/corrupted
                    if "categories" not in self.library:
                        self.library["categories"] = []
                    if "entries" not in self.library:
                        self.library["entries"] = {}
            else:
                 self.library = {"categories": [], "entries": {}} # Start fresh
        except json.JSONDecodeError:
            print(f"Error reading {self.library_file}. Starting with empty library.")
            self.library = {"categories": [], "entries": {}}
        except Exception as e:
            print(f"Error loading information library: {e}")
            QMessageBox.warning(self, "Load Error", f"Could not load library: {e}")
            self.library = {"categories": [], "entries": {}} # Fallback
            
        self.update_category_list()
        self.update_entries_list()

    def save_library(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(self.library, f, indent=4)
        except IOError as e:
            print(f"Error saving information library: {e}")
            QMessageBox.critical(self, "Save Error", f"Could not save library: {e}")
            if self.parent:
                self.parent.statusBar().showMessage(f"Error saving library: {e}", 5000)
        except Exception as e:
            print(f"Unexpected error saving library: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred while saving library: {e}")

    def update_entries_list(self):
        """Update the entries tree for the current category"""
        # Clear the tree
        self.entries_tree.clear()
        
        # Update header
        self.category_header.setText(self.current_category)
        
        # Add entries for the current category
        if self.current_category in self.library["entries"]:
            # First, create a map of all entries by ID
            entry_map = {entry["id"]: entry for entry in self.library["entries"][self.current_category]}
            
            # Then, add top-level entries (those without a parent)
            for entry in self.library["entries"][self.current_category]:
                if not entry.get("parent_id"):
                    item = QTreeWidgetItem(self.entries_tree, [entry["title"]])
                    item.setData(0, Qt.UserRole, entry)
                    
                    # Add children recursively
                    if "children" in entry:
                        self.add_child_entries(item, entry["children"], entry_map)
            
            # Expand all items
            self.entries_tree.expandAll()
    
    def add_child_entries(self, parent_item, child_ids, entry_map):
        """Add child entries to a parent item"""
        for child_id in child_ids:
            if child_id in entry_map:
                child_entry = entry_map[child_id]
                child_item = QTreeWidgetItem(parent_item, [child_entry["title"]])
                child_item.setData(0, Qt.UserRole, child_entry)
                
                # Add children recursively
                if "children" in child_entry:
                    self.add_child_entries(child_item, child_entry["children"], entry_map)
    
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        item = self.entries_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_entry())
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_entry())
        
        add_subpage_action = QAction("Add Subpage", self)
        add_subpage_action.triggered.connect(lambda: self.add_subpage())
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(add_subpage_action)
        
        menu.exec_(self.entries_tree.mapToGlobal(position))
    
    def on_item_moved(self, item):
        """Handle item moved in the tree"""
        # This is called after an item is dropped
        # We need to update the parent-child relationships in our data model
        self.update_entry_hierarchy()
        self.save_library()
    
    def update_entry_hierarchy(self):
        """Update the entry hierarchy based on the current tree structure"""
        # This is a complex operation that rebuilds the entry hierarchy
        # based on the current state of the tree widget
        
        # First, create a mapping of all entries by ID
        entry_map = {}
        for category, entries in self.library["entries"].items():
            for entry in entries:
                entry_map[entry["id"]] = entry
                # Reset parent and children
                entry["parent_id"] = None
                if "children" in entry:
                    del entry["children"]
        
        # Now traverse the tree and update parent-child relationships
        root = self.entries_tree.invisibleRootItem()
        for i in range(root.childCount()):
            self.process_tree_item(root.child(i), None, entry_map)
    
    def process_tree_item(self, item, parent_id, entry_map):
        """Process a tree item and update parent-child relationships"""
        entry_id = item.data(0, Qt.UserRole)["id"]
        entry = entry_map.get(entry_id)
        
        if entry:
            # Update parent
            entry["parent_id"] = parent_id
            
            # Process children
            if item.childCount() > 0:
                entry["children"] = []
                for i in range(item.childCount()):
                    child_item = item.child(i)
                    child_id = child_item.data(0, Qt.UserRole)["id"]
                    entry["children"].append(child_id)
                    self.process_tree_item(child_item, entry_id, entry_map)
    
    def add_subpage(self):
        """Add a subpage to the selected entry"""
        selected_items = self.entries_tree.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an entry to add a subpage to.")
            return
            
        parent_item = selected_items[0]
        parent_entry = parent_item.data(0, Qt.UserRole)
        
        dialog = EntryDialog(self)
        
        if dialog.exec_():
            entry_data = dialog.get_entry_data()
            
            # Add metadata
            entry_data["date_added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry_data["date_modified"] = entry_data["date_added"]
            entry_data["id"] = f"{self.current_category[0].lower()}{len(self.library['entries'][self.current_category]) + 1}"
            entry_data["parent_id"] = parent_entry["id"]
            
            # Add to entries
            self.library["entries"][self.current_category].append(entry_data)
            
            # Add to tree
            child_item = QTreeWidgetItem(parent_item, [entry_data["title"]])
            child_item.setData(0, Qt.UserRole, entry_data)
            
            # Expand the parent
            parent_item.setExpanded(True)
            
            # Update parent's children list
            if "children" not in parent_entry:
                parent_entry["children"] = []
            parent_entry["children"].append(entry_data["id"])
            
            # Save the data
            self.save_library()
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Added subpage: {entry_data['title']}")
    
    def show_category_context_menu(self, position):
        """Show context menu for category items"""
        item = self.category_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        rename_action = QAction("Rename Category", self)
        rename_action.triggered.connect(lambda: self.rename_category(item.text()))
        
        remove_action = QAction("Remove Category", self)
        remove_action.triggered.connect(lambda: self.remove_category())
        
        menu.addAction(rename_action)
        menu.addAction(remove_action)
        
        menu.exec_(self.category_list.mapToGlobal(position))
    
    def rename_category(self, category_name):
        """Rename a category"""
        if category_name not in self.library["categories"]:
            return
            
        new_name, ok = QInputDialog.getText(self, "Rename Category", 
                                          "New category name:", 
                                          text=category_name)
        
        if ok and new_name and new_name != category_name:
            if new_name in self.library["categories"]:
                QMessageBox.warning(self, "Duplicate Category", 
                                   f"Category '{new_name}' already exists.")
                return
                
            # Update categories list
            index = self.library["categories"].index(category_name)
            self.library["categories"][index] = new_name
            
            # Update category in entries dictionary
            self.library["entries"][new_name] = self.library["entries"].pop(category_name)
            
            # Update UI
            self.category_list.clear()
            self.category_list.addItems(self.library["categories"])
            self.category_list.setCurrentRow(index)
            
            # Save the data
            self.save_library()
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Renamed category: {category_name} → {new_name}")
    
    def remove_category(self):
        """Remove the selected category"""
        selected_items = self.category_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a category to remove.")
            return
            
        category_name = selected_items[0].text()
        
        # Don't allow removing the last category
        if len(self.library["categories"]) <= 1:
            QMessageBox.warning(self, "Cannot Remove", 
                               "You cannot remove the last category. At least one category must exist.")
            return
            
        # Confirm deletion
        entry_count = len(self.library["entries"].get(category_name, []))
        message = f"Are you sure you want to remove the category '{category_name}'?\n\n"
        
        if entry_count > 0:
            message += f"This will delete {entry_count} entries in this category."
        
        reply = QMessageBox.question(self, "Confirm Removal", message,
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Remove from categories list
            index = self.library["categories"].index(category_name)
            self.library["categories"].remove(category_name)
            
            # Remove from entries dictionary
            if category_name in self.library["entries"]:
                del self.library["entries"][category_name]
            
            # Update UI
            self.category_list.clear()
            self.category_list.addItems(self.library["categories"])
            
            # Select another category
            new_index = min(index, len(self.library["categories"]) - 1)
            self.category_list.setCurrentRow(new_index)
            
            # Save the data
            self.save_library()
            
            if self.parent:
                self.parent.statusBar().showMessage(f"Removed category: {category_name}")

    def update_category_list(self):
        """Update the category list widget from self.library data."""
        self.category_list.clear()
        # Ensure categories exist and is a list
        categories = self.library.get("categories", [])
        if isinstance(categories, list):
            self.category_list.addItems(categories)
            # Select the first category if the list isn't empty
            if categories:
                self.category_list.setCurrentRow(0)
                self.current_category = categories[0]
            else:
                self.current_category = None # No categories available
        else:
            # Handle case where 'categories' is not a list (data corruption?)
            self.library["categories"] = [] # Reset to empty list
            self.current_category = None
            print("Warning: Library categories data was not a list. Resetting.")


class EntryDialog(QDialog):
    """Dialog for adding or editing an entry"""
    def __init__(self, parent=None, entry_data=None):
        super().__init__(parent)
        self.entry_data = entry_data
        self.setup_ui()
        
        if entry_data:
            self.setWindowTitle("Edit Entry")
            self.populate_fields()
        else:
            self.setWindowTitle("Add New Entry")
    
    def setup_ui(self):
        self.setMinimumWidth(500)
        layout = QVBoxLayout()
        
        # Title field
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        
        # Tags field
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Tags:")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Comma-separated tags")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_input)
        
        # URL field
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Optional URL reference")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        # Content field
        content_label = QLabel("Content:")
        self.content_input = QTextEdit()
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        save_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        
        # Add all to main layout
        layout.addLayout(title_layout)
        layout.addLayout(tags_layout)
        layout.addLayout(url_layout)
        layout.addWidget(content_label)
        layout.addWidget(self.content_input)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def populate_fields(self):
        """Populate fields with existing entry data"""
        if self.entry_data:
            self.title_input.setText(self.entry_data["title"])
            self.tags_input.setText(", ".join(self.entry_data["tags"]))
            self.url_input.setText(self.entry_data["url"])
            self.content_input.setText(self.entry_data["content"])
    
    def get_entry_data(self):
        """Get the entry data from the form"""
        # Process tags - split by comma and strip whitespace
        tags_text = self.tags_input.text()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        return {
            "title": self.title_input.text(),
            "content": self.content_input.toPlainText(),
            "tags": tags,
            "url": self.url_input.text()
        } 