from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QDateTime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                          QPushButton, QListWidget, QListWidgetItem, QLineEdit,
                          QTextEdit, QComboBox, QTabWidget, QWidget,
                          QTableWidget, QTableWidgetItem, QHeaderView,
                          QGroupBox, QFormLayout, QMessageBox, QInputDialog)
from PyQt5.QtGui import QColor, QIcon, QPixmap

import uuid
import json
import time
from datetime import datetime, timedelta
import random

class CollaborationManager(QObject):
    """
    Manages collaboration features like comments, sharing, and realtime updates
    """
    
    # Signals
    comment_added = pyqtSignal(dict)
    user_connected = pyqtSignal(str)
    user_disconnected = pyqtSignal(str)
    item_updated = pyqtSignal(dict)
    sync_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        
        # Initialize collaboration data
        self.connected_users = []
        self.comments = []
        self.shared_projects = []
        self.change_history = []
        self.current_user = {"id": str(uuid.uuid4()), "name": "Current User", "color": "#4CAF50"}
        
        # Add some mock users for demo purposes
        self.users = [
            {"id": "user1", "name": "Alex Johnson", "color": "#2196F3", "online": True},
            {"id": "user2", "name": "Sam Taylor", "color": "#9C27B0", "online": False},
            {"id": "user3", "name": "Casey Smith", "color": "#FF9800", "online": True}
        ]
        
        # Setup simulated online/offline status change timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.simulate_user_status_change)
        self.status_timer.start(20000)  # 20 seconds
        
        # Add connected users
        for user in self.users:
            if user["online"]:
                self.connected_users.append(user)
        
        # Add some demo comments
        self.add_demo_comments()
        
    def add_demo_comments(self):
        """Add some demo comments for testing"""
        self.comments = [
            {
                "id": "c1",
                "user_id": "user1",
                "item_id": "task_0",  # Assuming this matches a task ID in the timeline
                "content": "We should start this task earlier to avoid delays.",
                "timestamp": datetime.now() - timedelta(days=2, hours=3),
                "resolved": False
            },
            {
                "id": "c2",
                "user_id": "user3",
                "item_id": "task_2",
                "content": "I'll help with this task, let's coordinate.",
                "timestamp": datetime.now() - timedelta(days=1, hours=5),
                "resolved": False
            },
            {
                "id": "c3",
                "user_id": "user2",
                "item_id": "task_1",
                "content": "This task is completed ahead of schedule.",
                "timestamp": datetime.now() - timedelta(hours=7),
                "resolved": True
            }
        ]
        
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        if user_id == self.current_user["id"]:
            return self.current_user
            
        for user in self.users:
            if user["id"] == user_id:
                return user
                
        return None
    
    def simulate_user_status_change(self):
        """Simulate users coming online/offline for demo purposes"""
        if not self.users:
            return
            
        # Randomly select a user to change status
        user = random.choice(self.users)
        was_online = user["online"]
        
        # Change status
        user["online"] = not was_online
        
        # Update connected users list
        if user["online"]:
            self.connected_users.append(user)
            self.user_connected.emit(user["name"])
        else:
            self.connected_users = [u for u in self.connected_users if u["id"] != user["id"]]
            self.user_disconnected.emit(user["name"])
    
    def add_comment(self, item_id, content):
        """Add a comment to an item"""
        comment = {
            "id": f"c{len(self.comments) + 1}",
            "user_id": self.current_user["id"],
            "item_id": item_id,
            "content": content,
            "timestamp": datetime.now(),
            "resolved": False
        }
        
        self.comments.append(comment)
        self.comment_added.emit(comment)
        
        return comment
    
    def get_comments_for_item(self, item_id):
        """Get all comments for a specific item"""
        return [comment for comment in self.comments if comment["item_id"] == item_id]
    
    def resolve_comment(self, comment_id):
        """Mark a comment as resolved"""
        for comment in self.comments:
            if comment["id"] == comment_id:
                comment["resolved"] = True
                break
    
    def share_project(self, project_id, user_ids, permission="read"):
        """Share a project with other users"""
        share_info = {
            "project_id": project_id,
            "shared_by": self.current_user["id"],
            "shared_with": user_ids,
            "permission": permission,
            "timestamp": datetime.now()
        }
        
        self.shared_projects.append(share_info)
        
        # In a real app, this would notify the users
        return share_info
    
    def is_project_shared_with_user(self, project_id, user_id):
        """Check if a project is shared with a specific user"""
        for share in self.shared_projects:
            if share["project_id"] == project_id and user_id in share["shared_with"]:
                return True
                
        return False
    
    def record_change(self, item_id, change_type, details=None):
        """Record a change for synchronization"""
        change = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "user_id": self.current_user["id"],
            "timestamp": datetime.now(),
            "type": change_type,
            "details": details or {}
        }
        
        self.change_history.append(change)
        self.item_updated.emit(change)
        
        return change
    
    def get_recent_changes(self, count=20):
        """Get the most recent changes"""
        # Sort by timestamp (most recent first) and return the specified number
        sorted_changes = sorted(
            self.change_history, 
            key=lambda x: x["timestamp"] if isinstance(x["timestamp"], datetime) else datetime.now(),
            reverse=True
        )
        
        return sorted_changes[:count]
    
    def simulate_incoming_change(self):
        """Simulate an incoming change from another user (for demo purposes)"""
        if not self.users or not self.connected_users:
            return
            
        # Select a random online user
        online_users = [user for user in self.users if user["online"]]
        if not online_users:
            return
            
        user = random.choice(online_users)
        
        # Create a random change
        change_types = ["add_task", "update_task", "add_comment", "resolve_comment"]
        change_type = random.choice(change_types)
        
        # Generate random task ID
        task_id = f"task_{random.randint(0, 5)}"
        
        # Create change details based on type
        if change_type == "add_task":
            details = {
                "title": f"New Task by {user['name']}",
                "start_date": datetime.now() + timedelta(days=random.randint(1, 30)),
                "end_date": datetime.now() + timedelta(days=random.randint(31, 60))
            }
        elif change_type == "update_task":
            details = {
                "progress": random.randint(10, 100)
            }
        elif change_type == "add_comment":
            details = {
                "content": f"Comment from {user['name']}: This looks good!"
            }
        else:  # resolve_comment
            details = {
                "comment_id": f"c{random.randint(1, len(self.comments))}"
            }
        
        change = {
            "id": str(uuid.uuid4()),
            "item_id": task_id,
            "user_id": user["id"],
            "timestamp": datetime.now(),
            "type": change_type,
            "details": details
        }
        
        # Add to history and notify
        self.change_history.append(change)
        self.item_updated.emit(change)
        
        return change
    
    def sync_with_server(self):
        """Simulate syncing with server (for demo purposes)"""
        # In a real app, this would communicate with a server
        # For the demo, we'll just simulate a successful sync
        
        # Simulate a delay
        time.sleep(0.5)
        
        # Emit signal to indicate sync is complete
        self.sync_completed.emit()
        
        return True


class CommentsPanel(QWidget):
    """
    Panel for displaying and managing comments
    """
    
    def __init__(self, collaboration_manager, parent=None):
        super().__init__(parent)
        self.collab_manager = collaboration_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Comments section
        comments_group = QGroupBox("Comments")
        comments_layout = QVBoxLayout(comments_group)
        
        # Comments list
        self.comments_list = QListWidget()
        self.comments_list.setSelectionMode(QListWidget.SingleSelection)
        self.comments_list.setMinimumHeight(200)
        
        # Add comment section
        comment_input_layout = QHBoxLayout()
        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Add a comment...")
        
        self.add_comment_btn = QPushButton("Add")
        self.add_comment_btn.clicked.connect(self.add_comment)
        
        comment_input_layout.addWidget(self.comment_input)
        comment_input_layout.addWidget(self.add_comment_btn)
        
        # Add to comments layout
        comments_layout.addWidget(self.comments_list)
        comments_layout.addLayout(comment_input_layout)
        
        # Add to main layout
        layout.addWidget(comments_group)
        
    def set_item(self, item):
        """Set the current item and load its comments"""
        self.current_item = item
        self.refresh_comments()
        
    def refresh_comments(self):
        """Refresh the comments list for the current item"""
        self.comments_list.clear()
        
        if not hasattr(self, 'current_item') or not self.current_item or not hasattr(self.current_item, 'id'):
            return
            
        # Get comments for this item
        comments = self.collab_manager.get_comments_for_item(self.current_item.id)
        
        # Add to list
        for comment in comments:
            # Get user details
            user = self.collab_manager.get_user_by_id(comment["user_id"])
            user_name = user["name"] if user else "Unknown User"
            
            # Create list item
            item = QListWidgetItem()
            item.setData(Qt.UserRole, comment)
            
            # Format the timestamp
            timestamp = comment["timestamp"]
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
            else:
                timestamp_str = "Unknown Time"
            
            # Set item text
            status = " (Resolved)" if comment["resolved"] else ""
            item.setText(f"{user_name} - {timestamp_str}{status}\n{comment['content']}")
            
            # Add to list
            self.comments_list.addItem(item)
            
    def add_comment(self):
        """Add a new comment to the current item"""
        if not hasattr(self, 'current_item') or not self.current_item or not hasattr(self.current_item, 'id'):
            return
            
        comment_text = self.comment_input.text().strip()
        if not comment_text:
            return
            
        # Add comment
        self.collab_manager.add_comment(self.current_item.id, comment_text)
        
        # Clear input
        self.comment_input.clear()
        
        # Refresh list
        self.refresh_comments()


class SharingDialog(QDialog):
    """
    Dialog for sharing projects with other users
    """
    
    def __init__(self, collaboration_manager, project_id, project_name, parent=None):
        super().__init__(parent)
        self.collab_manager = collaboration_manager
        self.project_id = project_id
        self.project_name = project_name
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Share Project: {self.project_name}")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Select users to share this project with:")
        layout.addWidget(instructions)
        
        # User list
        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Add users to list
        for user in self.collab_manager.users:
            item = QListWidgetItem(user["name"])
            item.setData(Qt.UserRole, user["id"])
            
            # Check if already shared
            if self.collab_manager.is_project_shared_with_user(self.project_id, user["id"]):
                item.setSelected(True)
                
            self.user_list.addItem(item)
            
        layout.addWidget(self.user_list)
        
        # Permission selector
        permission_layout = QHBoxLayout()
        permission_layout.addWidget(QLabel("Permission:"))
        
        self.permission_combo = QComboBox()
        self.permission_combo.addItems(["View Only", "Edit", "Full Access"])
        permission_layout.addWidget(self.permission_combo)
        
        layout.addLayout(permission_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        share_btn = QPushButton("Share")
        share_btn.clicked.connect(self.share_project)
        share_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(share_btn)
        
        layout.addLayout(button_layout)
        
    def share_project(self):
        """Share the project with selected users"""
        # Get selected users
        selected_users = []
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            if item.isSelected():
                user_id = item.data(Qt.UserRole)
                selected_users.append(user_id)
        
        # Get permission
        permission_map = {
            0: "view",
            1: "edit",
            2: "full"
        }
        permission = permission_map[self.permission_combo.currentIndex()]
        
        # Share project
        if selected_users:
            self.collab_manager.share_project(self.project_id, selected_users, permission)
            
        # Close dialog
        self.accept()


class ActivityPanel(QWidget):
    """
    Panel for displaying recent activity and collaboration features
    """
    
    def __init__(self, collaboration_manager, parent=None):
        super().__init__(parent)
        self.collab_manager = collaboration_manager
        self.setup_ui()
        
        # Connect signals
        self.collab_manager.user_connected.connect(self.handle_user_connected)
        self.collab_manager.user_disconnected.connect(self.handle_user_disconnected)
        self.collab_manager.item_updated.connect(self.handle_item_updated)
        
        # Periodically simulate incoming changes for demo purposes
        self.change_timer = QTimer(self)
        self.change_timer.timeout.connect(self.simulate_incoming_change)
        self.change_timer.start(30000)  # 30 seconds
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create the activity tab
        self.setup_activity_tab()
        
        # Create the users tab
        self.setup_users_tab()
        
        # Create the sharing tab
        self.setup_sharing_tab()
        
        # Add tabs to widget
        layout.addWidget(self.tabs)
        
        # Add sync status at bottom
        status_layout = QHBoxLayout()
        
        self.sync_status = QLabel("Last synced: Never")
        
        sync_btn = QPushButton("Sync Now")
        sync_btn.clicked.connect(self.sync_with_server)
        
        status_layout.addWidget(self.sync_status)
        status_layout.addStretch()
        status_layout.addWidget(sync_btn)
        
        layout.addLayout(status_layout)
        
    def setup_activity_tab(self):
        """Set up the activity feed tab"""
        activity_tab = QWidget()
        activity_layout = QVBoxLayout(activity_tab)
        
        # Activity list
        self.activity_list = QListWidget()
        
        # Populate with recent changes
        self.refresh_activity_list()
        
        activity_layout.addWidget(self.activity_list)
        
        self.tabs.addTab(activity_tab, "Activity")
        
    def setup_users_tab(self):
        """Set up the connected users tab"""
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        
        # Connected users list
        self.users_list = QListWidget()
        
        # Populate with connected users
        self.refresh_users_list()
        
        users_layout.addWidget(self.users_list)
        
        self.tabs.addTab(users_tab, "Users")
        
    def setup_sharing_tab(self):
        """Set up the sharing tab"""
        sharing_tab = QWidget()
        sharing_layout = QVBoxLayout(sharing_tab)
        
        # Shared projects table
        self.sharing_table = QTableWidget()
        self.sharing_table.setColumnCount(3)
        self.sharing_table.setHorizontalHeaderLabels(["Project", "Shared With", "Permission"])
        self.sharing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Populate with shared projects
        self.refresh_sharing_table()
        
        # Share project button
        share_btn = QPushButton("Share Project...")
        share_btn.clicked.connect(self.show_share_dialog)
        
        sharing_layout.addWidget(self.sharing_table)
        sharing_layout.addWidget(share_btn)
        
        self.tabs.addTab(sharing_tab, "Sharing")
        
    def refresh_activity_list(self):
        """Refresh the activity list"""
        self.activity_list.clear()
        
        # Get recent changes
        changes = self.collab_manager.get_recent_changes()
        
        # Add to list
        for change in changes:
            # Get user details
            user = self.collab_manager.get_user_by_id(change["user_id"])
            user_name = user["name"] if user else "Unknown User"
            
            # Format the timestamp
            timestamp = change["timestamp"]
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
            else:
                timestamp_str = "Unknown Time"
            
            # Format the action description
            if change["type"] == "add_task":
                action = f"added task '{change['details'].get('title', 'Unnamed Task')}'"
            elif change["type"] == "update_task":
                action = f"updated task {change['item_id']}"
                if "progress" in change["details"]:
                    action += f" progress to {change['details']['progress']}%"
            elif change["type"] == "add_comment":
                action = f"commented on {change['item_id']}"
            elif change["type"] == "resolve_comment":
                action = f"resolved a comment on {change['item_id']}"
            else:
                action = f"performed action {change['type']} on {change['item_id']}"
            
            # Create list item
            item = QListWidgetItem()
            item.setText(f"{user_name} {action} - {timestamp_str}")
            
            # Add to list
            self.activity_list.addItem(item)
            
    def refresh_users_list(self):
        """Refresh the connected users list"""
        self.users_list.clear()
        
        # Add current user (always shown as online)
        item = QListWidgetItem(f"{self.collab_manager.current_user['name']} (You)")
        item.setData(Qt.UserRole, self.collab_manager.current_user["id"])
        self.users_list.addItem(item)
        
        # Add other connected users
        for user in self.collab_manager.connected_users:
            if user["id"] != self.collab_manager.current_user["id"]:
                item = QListWidgetItem(f"{user['name']} (Online)")
                item.setData(Qt.UserRole, user["id"])
                self.users_list.addItem(item)
        
        # Add offline users
        for user in self.collab_manager.users:
            if not user["online"]:
                item = QListWidgetItem(f"{user['name']} (Offline)")
                item.setData(Qt.UserRole, user["id"])
                self.users_list.addItem(item)
                
    def refresh_sharing_table(self):
        """Refresh the shared projects table"""
        self.sharing_table.setRowCount(0)
        
        # Add shared projects
        for i, share in enumerate(self.collab_manager.shared_projects):
            self.sharing_table.insertRow(i)
            
            # Project name (in a real app, this would be fetched from the project list)
            project_name = f"Project {share['project_id']}"
            self.sharing_table.setItem(i, 0, QTableWidgetItem(project_name))
            
            # Shared with (list of users)
            shared_with_names = []
            for user_id in share["shared_with"]:
                user = self.collab_manager.get_user_by_id(user_id)
                if user:
                    shared_with_names.append(user["name"])
            
            shared_with_text = ", ".join(shared_with_names)
            self.sharing_table.setItem(i, 1, QTableWidgetItem(shared_with_text))
            
            # Permission
            permission_map = {
                "view": "View Only",
                "edit": "Edit",
                "full": "Full Access"
            }
            permission_text = permission_map.get(share["permission"], share["permission"])
            self.sharing_table.setItem(i, 2, QTableWidgetItem(permission_text))
            
    def show_share_dialog(self):
        """Show the share project dialog"""
        # In a real app, this would get the actual project ID and name
        project_id = "project1"
        project_name = "Website Redesign"
        
        dialog = SharingDialog(self.collab_manager, project_id, project_name, self)
        if dialog.exec_():
            # Refresh the sharing table
            self.refresh_sharing_table()
            
    def handle_user_connected(self, user_name):
        """Handle a user connecting"""
        # Update the users list
        self.refresh_users_list()
        
        # Add to activity feed
        item = QListWidgetItem(f"{user_name} connected - {datetime.now().strftime('%H:%M')}")
        self.activity_list.insertItem(0, item)
        
    def handle_user_disconnected(self, user_name):
        """Handle a user disconnecting"""
        # Update the users list
        self.refresh_users_list()
        
        # Add to activity feed
        item = QListWidgetItem(f"{user_name} disconnected - {datetime.now().strftime('%H:%M')}")
        self.activity_list.insertItem(0, item)
        
    def handle_item_updated(self, change):
        """Handle an item update"""
        # Refresh the activity list
        self.refresh_activity_list()
        
    def simulate_incoming_change(self):
        """Simulate an incoming change for demo purposes"""
        self.collab_manager.simulate_incoming_change()
        
    def sync_with_server(self):
        """Sync with server"""
        # Show syncing status
        self.sync_status.setText("Syncing...")
        
        # Perform sync
        self.collab_manager.sync_with_server()
        
        # Update sync status
        self.sync_status.setText(f"Last synced: {datetime.now().strftime('%H:%M:%S')}")
        
        # Refresh lists
        self.refresh_activity_list()
        self.refresh_users_list()
        self.refresh_sharing_table() 