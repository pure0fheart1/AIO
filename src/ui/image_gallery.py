import sys
import os
import json
import shutil
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QListWidget, QListWidgetItem, QSplitter, QTreeWidget, 
                            QTreeWidgetItem, QFileDialog, QMessageBox, QInputDialog, 
                            QColorDialog, QMenu, QAction, QComboBox, QApplication, 
                            QStyle, QMainWindow)
from PyQt5.QtCore import Qt, QSize, QDir
from PyQt5.QtGui import QPixmap, QIcon, QColor, QImageReader

GALLERY_ROOT_DIR = "GalleryImages"
METADATA_FILE = os.path.join(GALLERY_ROOT_DIR, "gallery_meta.json")
THUMBNAIL_SIZE = QSize(128, 128) # Increased thumbnail size

class ImageGallery(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_dir = GALLERY_ROOT_DIR
        self.metadata = {} # To store color info, etc.

        # Ensure gallery directory and metadata file exist
        os.makedirs(GALLERY_ROOT_DIR, exist_ok=True)
        self._load_metadata()

        self.setup_ui()
        self.populate_folder_tree()
        self.populate_image_list(self.current_dir)


    def _load_metadata(self):
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r') as f:
                    self.metadata = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode metadata file: {METADATA_FILE}")
                self.metadata = {}
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {} # Initialize if file doesn't exist

    def _save_metadata(self):
        try:
            with open(METADATA_FILE, 'w') as f:
                json.dump(self.metadata, f, indent=4)
        except Exception as e:
            print(f"Error saving metadata: {e}")
            QMessageBox.critical(self, "Metadata Error", f"Could not save gallery metadata: {e}")

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Top Toolbar
        toolbar_layout = QHBoxLayout()
        self.upload_button = QPushButton("Upload Images")
        self.new_folder_button = QPushButton("New Folder")
        self.delete_button = QPushButton("Delete Item")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Grid", "List", "Details"]) # TODO: Implement Details view
        self.color_button = QPushButton("Color Code")
        
        self.upload_button.clicked.connect(self.upload_images)
        self.new_folder_button.clicked.connect(self.create_new_folder)
        self.delete_button.clicked.connect(self.delete_selected_item)
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        self.color_button.clicked.connect(self.color_selected_item)

        toolbar_layout.addWidget(self.upload_button)
        toolbar_layout.addWidget(self.new_folder_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Layout:"))
        toolbar_layout.addWidget(self.layout_combo)
        toolbar_layout.addWidget(self.color_button)
        
        # Main Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: Folder Tree
        folder_panel = QWidget()
        folder_layout = QVBoxLayout(folder_panel)
        folder_layout.addWidget(QLabel("Folders"))
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self.on_folder_selected)
        folder_layout.addWidget(self.folder_tree)
        
        # Right Panel: Image List/Grid
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)
        self.current_path_label = QLabel(f"Current: {self.current_dir}")
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode) # Default to grid
        self.image_list.setIconSize(THUMBNAIL_SIZE)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setMovement(QListWidget.Static) # Prevent dragging
        self.image_list.setSpacing(10) 
        # self.image_list.itemDoubleClicked.connect(self.on_item_double_clicked) # TODO: Open image viewer or navigate folder
        # TODO: Add context menu for items (rename, color, delete)

        image_layout.addWidget(self.current_path_label)
        image_layout.addWidget(self.image_list)

        # Add panels to splitter
        self.splitter.addWidget(folder_panel)
        self.splitter.addWidget(image_panel)
        self.splitter.setSizes([200, 600]) # Initial size ratio

        # Add elements to main layout
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.splitter)

    def populate_folder_tree(self, parent_item=None, dir_path=GALLERY_ROOT_DIR):
        if parent_item is None:
            self.folder_tree.clear()
            parent_item = QTreeWidgetItem(self.folder_tree, [os.path.basename(GALLERY_ROOT_DIR)])
            parent_item.setData(0, Qt.UserRole, GALLERY_ROOT_DIR) # Store full path
            parent_item.setExpanded(True) # Expand root by default
            self.folder_tree.setCurrentItem(parent_item) # Select root initially

        try:
            for entry in os.scandir(dir_path):
                if entry.is_dir():
                    folder_name = entry.name
                    full_path = entry.path
                    child_item = QTreeWidgetItem(parent_item, [folder_name])
                    child_item.setData(0, Qt.UserRole, full_path)
                    child_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon)) # Use standard folder icon
                    # Recursively populate subfolders
                    self.populate_folder_tree(child_item, full_path)
        except OSError as e:
             print(f"Error scanning directory {dir_path}: {e}")


    def populate_image_list(self, dir_path):
        self.image_list.clear()
        self.current_path_label.setText(f"Current: {os.path.relpath(dir_path)}")
        
        supported_formats = QImageReader.supportedImageFormats() # Get supported formats

        try:
            for entry in os.scandir(dir_path):
                if entry.is_file():
                    file_path = entry.path
                    file_ext = os.path.splitext(file_path)[1].lower()[1:] # Get extension without dot

                    if file_ext.encode() in supported_formats: # Check if format is supported
                        item = QListWidgetItem(entry.name)
                        item.setData(Qt.UserRole, file_path) # Store full path

                        # Create thumbnail
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(THUMBNAIL_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setIcon(QIcon(scaled_pixmap))
                            item.setSizeHint(THUMBNAIL_SIZE + QSize(20, 20)) # Add padding
                        else:
                             # Optionally set a default icon for unreadable images
                             pass 

                        # Apply color coding from metadata
                        item_color = self.metadata.get(file_path, {}).get("color")
                        if item_color:
                            item.setBackground(QColor(item_color))
                            # Adjust text color for contrast if needed
                            bg_color = QColor(item_color)
                            item.setForeground(Qt.white if bg_color.lightness() < 128 else Qt.black)
                            
                        self.image_list.addItem(item)

        except OSError as e:
             print(f"Error scanning directory {dir_path}: {e}")
             QMessageBox.warning(self, "Error", f"Could not read directory contents: {e}")


    def on_folder_selected(self, item, column):
        folder_path = item.data(0, Qt.UserRole)
        if folder_path and os.path.isdir(folder_path):
            self.current_dir = folder_path
            self.populate_image_list(self.current_dir)

    def upload_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Images to Upload", 
            QDir.homePath(), # Start in user's home directory
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)" 
        )
        
        if file_paths:
            uploaded_count = 0
            skipped_count = 0
            for src_path in file_paths:
                try:
                    filename = os.path.basename(src_path)
                    dst_path = os.path.join(self.current_dir, filename)
                    
                    # Avoid overwriting existing files (optional: add overwrite confirmation)
                    if os.path.exists(dst_path):
                        # Simple skip for now
                         print(f"Skipping existing file: {filename}")
                         skipped_count += 1
                         continue

                    shutil.copy2(src_path, dst_path) # copy2 preserves metadata
                    uploaded_count += 1
                except Exception as e:
                    print(f"Error copying file {src_path}: {e}")
                    QMessageBox.warning(self, "Upload Error", f"Could not upload {os.path.basename(src_path)}: {e}")
            
            self.populate_image_list(self.current_dir) # Refresh the list
            msg = f"Uploaded {uploaded_count} image(s)."
            if skipped_count > 0:
                msg += f" Skipped {skipped_count} existing file(s)."
            QMessageBox.information(self, "Upload Complete", msg)


    def create_new_folder(self):
         folder_name, ok = QInputDialog.getText(self, "Create New Folder", "Enter folder name:")
         if ok and folder_name:
             # Sanitize folder name (optional, basic example)
             folder_name = folder_name.strip()
             if not folder_name or ("/" in folder_name) or ("\\" in folder_name):
                 QMessageBox.warning(self, "Invalid Name", "Folder name is invalid.")
                 return

             new_folder_path = os.path.join(self.current_dir, folder_name)
             
             if os.path.exists(new_folder_path):
                 QMessageBox.warning(self, "Folder Exists", "A folder with this name already exists.")
                 return
                 
             try:
                 os.makedirs(new_folder_path)
                 self.populate_folder_tree() # Refresh the whole tree to show the new folder
                 # Find and select the parent item in the tree to add the new folder visually
                 # (More complex logic needed here to find the correct parent tree item)
             except OSError as e:
                 QMessageBox.critical(self, "Creation Failed", f"Could not create folder: {e}")

    def delete_selected_item(self):
        selected_image_items = self.image_list.selectedItems()
        selected_folder_item = self.folder_tree.currentItem() 
        item_to_delete = None
        is_folder = False
        item_path = None
        item_name = None

        if selected_image_items:
            item_to_delete = selected_image_items[0]
            item_path = item_to_delete.data(Qt.UserRole)
            item_name = item_to_delete.text()
        elif selected_folder_item and selected_folder_item.data(0, Qt.UserRole) != GALLERY_ROOT_DIR: 
            item_to_delete = selected_folder_item
            item_path = item_to_delete.data(0, Qt.UserRole)
            item_name = item_to_delete.text(0)
            is_folder = True
        else:
            QMessageBox.warning(self, "Selection Error", "Please select an image or a folder (other than the root) to delete.")
            return
        
        # Simplified message text
        confirm_text = f"Delete '{item_name}'? This cannot be undone."
        reply = QMessageBox.question(self, "Confirm Delete", confirm_text,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                if is_folder:
                    shutil.rmtree(item_path)
                    # TODO: Clean up metadata for all items within the deleted folder
                    self.populate_folder_tree() 
                    if self.current_dir.startswith(item_path):
                         self.current_dir = os.path.dirname(item_path)
                         if not os.path.exists(self.current_dir):
                              self.current_dir = GALLERY_ROOT_DIR
                         self.populate_image_list(self.current_dir)

                elif os.path.isfile(item_path):
                    os.remove(item_path)
                    if item_path in self.metadata:
                        del self.metadata[item_path]
                        self._save_metadata()
                    self.populate_image_list(self.current_dir) 
                
            except OSError as e:
                QMessageBox.critical(self, "Deletion Failed", f"Could not delete '{item_name}': {e}")
            except Exception as e: 
                 QMessageBox.critical(self, "Deletion Failed", f"An unexpected error occurred while deleting '{item_name}': {e}")

    def change_layout(self, layout_text):
        if layout_text == "Grid":
            self.image_list.setViewMode(QListWidget.IconMode)
            self.image_list.setIconSize(THUMBNAIL_SIZE)
            self.image_list.setWordWrap(True)
        elif layout_text == "List":
            self.image_list.setViewMode(QListWidget.ListMode)
            self.image_list.setIconSize(QSize(32, 32)) 
            self.image_list.setWordWrap(False)
        # elif layout_text == "Details": 
        #     pass # Requires more complex setup
        self.image_list.updateGeometry()

    def color_selected_item(self):
        selected_items = self.image_list.selectedItems()
        if not selected_items:
             QMessageBox.warning(self, "Selection Error", "Please select an image to color code.")
             return

        item = selected_items[0]
        item_path = item.data(Qt.UserRole)

        current_color_hex = self.metadata.get(item_path, {}).get("color", "#FFFFFF")
        current_color = QColor(current_color_hex)

        color = QColorDialog.getColor(current_color, self, "Choose Color")

        if color.isValid():
            hex_color = color.name()
            if item_path not in self.metadata:
                 self.metadata[item_path] = {}
            self.metadata[item_path]["color"] = hex_color
            self._save_metadata()

            item.setBackground(color)
            item.setForeground(Qt.white if color.lightness() < 128 else Qt.black)

# Example usage (for testing standalone)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = QMainWindow() 
    gallery_widget = ImageGallery()
    main_window.setCentralWidget(gallery_widget)
    main_window.setWindowTitle('Image Gallery Test')
    main_window.setGeometry(100, 100, 900, 600)
    main_window.show()
    sys.exit(app.exec_()) 