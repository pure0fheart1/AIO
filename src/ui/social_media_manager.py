from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QPushButton, QLabel, QLineEdit, QTextEdit, 
                             QScrollArea, QGridLayout, QMessageBox, QFrame,
                             QGroupBox, QFormLayout, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWebEngineWidgets import QWebEngineView
import requests
import json
import os
import time
import webbrowser
from pathlib import Path
import urllib.parse

class SocialMediaAuth(QThread):
    """Thread for handling social media authentication processes"""
    auth_completed = pyqtSignal(str, dict)  # Platform, auth info
    auth_failed = pyqtSignal(str, str)  # Platform, error message
    
    def __init__(self, platform, auth_data):
        super().__init__()
        self.platform = platform
        self.auth_data = auth_data
        
    def run(self):
        try:
            if self.platform == "facebook":
                # Facebook authentication happens via OAuth in browser
                # This thread handles token validation once user provides it
                if "token" in self.auth_data:
                    # Validate token
                    if self.validate_facebook_token(self.auth_data["token"]):
                        self.auth_completed.emit(self.platform, self.auth_data)
                    else:
                        self.auth_failed.emit(self.platform, "Invalid Facebook token")
            
            elif self.platform == "instagram":
                # Instagram authentication happens via OAuth in browser
                if "token" in self.auth_data:
                    # Validate token
                    if self.validate_instagram_token(self.auth_data["token"]):
                        self.auth_completed.emit(self.platform, self.auth_data)
                    else:
                        self.auth_failed.emit(self.platform, "Invalid Instagram token")
            
            elif self.platform == "youtube":
                # YouTube authentication happens via OAuth in browser
                if "token" in self.auth_data:
                    # Validate token
                    if self.validate_youtube_token(self.auth_data["token"]):
                        self.auth_completed.emit(self.platform, self.auth_data)
                    else:
                        self.auth_failed.emit(self.platform, "Invalid YouTube token")
        
        except Exception as e:
            self.auth_failed.emit(self.platform, str(e))
    
    def validate_facebook_token(self, token):
        # In a real app, validate token with Facebook API
        # This is a simplified version for demo
        try:
            # Sample validation - in real app, call FB Graph API
            return len(token) > 10  # Simple validation for demo
        except:
            return False
    
    def validate_instagram_token(self, token):
        # In a real app, validate token with Instagram API
        try:
            # Sample validation
            return len(token) > 10
        except:
            return False
    
    def validate_youtube_token(self, token):
        # In a real app, validate token with YouTube Data API
        try:
            # Sample validation
            return len(token) > 10
        except:
            return False

class SocialMediaFeedLoader(QThread):
    """Thread for loading social media feeds"""
    feed_loaded = pyqtSignal(str, list)  # Platform, feed items
    feed_error = pyqtSignal(str, str)  # Platform, error message
    
    def __init__(self, platform, auth_data, max_items=10):
        super().__init__()
        self.platform = platform
        self.auth_data = auth_data
        self.max_items = max_items
        
    def run(self):
        try:
            if self.platform == "facebook":
                feed = self.load_facebook_feed()
                self.feed_loaded.emit(self.platform, feed)
            
            elif self.platform == "instagram":
                feed = self.load_instagram_feed()
                self.feed_loaded.emit(self.platform, feed)
            
            elif self.platform == "youtube":
                feed = self.load_youtube_feed()
                self.feed_loaded.emit(self.platform, feed)
                
        except Exception as e:
            self.feed_error.emit(self.platform, str(e))
    
    def load_facebook_feed(self):
        # In a real app, use Facebook Graph API to load feed
        # This is simulated data for demo purposes
        try:
            feed = []
            # Add demo items
            for i in range(5):
                feed.append({
                    "id": f"post_{i}",
                    "type": "status" if i % 2 == 0 else "photo",
                    "message": f"This is a sample Facebook post #{i}",
                    "created_time": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime(time.time() - i*3600)),
                    "image_url": "https://via.placeholder.com/400x300" if i % 2 == 1 else None
                })
            return feed
        except Exception as e:
            raise Exception(f"Failed to load Facebook feed: {str(e)}")
    
    def load_instagram_feed(self):
        # In a real app, use Instagram Graph API to load feed
        # This is simulated data for demo purposes
        try:
            feed = []
            # Add demo items
            for i in range(5):
                feed.append({
                    "id": f"media_{i}",
                    "type": "image",
                    "caption": f"This is a sample Instagram post #{i}",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime(time.time() - i*3600)),
                    "image_url": "https://via.placeholder.com/400x400",
                    "likes": 10 + i * 5,
                    "comments": i * 2
                })
            return feed
        except Exception as e:
            raise Exception(f"Failed to load Instagram feed: {str(e)}")
    
    def load_youtube_feed(self):
        # In a real app, use YouTube Data API to load feed
        # This is simulated data for demo purposes
        try:
            feed = []
            # Add demo items
            for i in range(5):
                feed.append({
                    "id": f"video_{i}",
                    "title": f"Sample YouTube Video #{i}",
                    "description": f"This is a description for video #{i}",
                    "published_at": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime(time.time() - i*3600)),
                    "thumbnail_url": "https://via.placeholder.com/480x360",
                    "video_url": f"https://www.youtube.com/watch?v=sample_{i}",
                    "views": 1000 + i * 500,
                    "likes": 50 + i * 10
                })
            return feed
        except Exception as e:
            raise Exception(f"Failed to load YouTube feed: {str(e)}")

class PostWidget(QFrame):
    """Widget to display a social media post"""
    
    def __init__(self, platform, post_data, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.post_data = post_data
        self.init_ui()
        
    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            PostWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                margin: 5px;
            }
            QLabel.title {
                font-weight: bold;
                font-size: 14px;
            }
            QLabel.metadata {
                color: #555;
                font-size: 12px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Platform icon/label
        header_layout = QHBoxLayout()
        platform_label = QLabel()
        if self.platform == "facebook":
            platform_label.setText("📘 Facebook")
            platform_label.setStyleSheet("color: #1877f2; font-weight: bold;")
        elif self.platform == "instagram":
            platform_label.setText("📷 Instagram")
            platform_label.setStyleSheet("color: #c32aa3; font-weight: bold;")
        elif self.platform == "youtube":
            platform_label.setText("🎬 YouTube")
            platform_label.setStyleSheet("color: #ff0000; font-weight: bold;")
        
        header_layout.addWidget(platform_label)
        
        # Timestamp
        timestamp_field = "created_time" if self.platform == "facebook" else "timestamp" if self.platform == "instagram" else "published_at"
        if timestamp_field in self.post_data:
            time_str = self.post_data[timestamp_field].split("T")[0]
            timestamp_label = QLabel(time_str)
            timestamp_label.setStyleSheet("color: #666; font-size: 12px;")
            timestamp_label.setAlignment(Qt.AlignRight)
            header_layout.addWidget(timestamp_label)
        
        layout.addLayout(header_layout)
        
        # Content display depends on platform and post type
        if self.platform == "facebook":
            # Message/content
            if "message" in self.post_data:
                content_label = QLabel(self.post_data["message"])
                content_label.setWordWrap(True)
                layout.addWidget(content_label)
            
            # Image if available
            if "image_url" in self.post_data and self.post_data["image_url"]:
                image_label = QLabel()
                image_label.setAlignment(Qt.AlignCenter)
                image_label.setFixedHeight(200)
                # In a real app, you'd load the actual image
                image_label.setText("[Image Placeholder]")
                layout.addWidget(image_label)
                
        elif self.platform == "instagram":
            # Caption
            if "caption" in self.post_data:
                caption_label = QLabel(self.post_data["caption"])
                caption_label.setWordWrap(True)
                layout.addWidget(caption_label)
            
            # Image (always present for Instagram)
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setFixedHeight(200)
            # In a real app, you'd load the actual image
            image_label.setText("[Image Placeholder]")
            layout.addWidget(image_label)
            
            # Engagement metrics
            if "likes" in self.post_data or "comments" in self.post_data:
                metrics_layout = QHBoxLayout()
                if "likes" in self.post_data:
                    likes_label = QLabel(f"❤️ {self.post_data['likes']}")
                    metrics_layout.addWidget(likes_label)
                if "comments" in self.post_data:
                    comments_label = QLabel(f"💬 {self.post_data['comments']}")
                    metrics_layout.addWidget(comments_label)
                metrics_layout.addStretch()
                layout.addLayout(metrics_layout)
                
        elif self.platform == "youtube":
            # Title
            if "title" in self.post_data:
                title_label = QLabel(self.post_data["title"])
                title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                title_label.setWordWrap(True)
                layout.addWidget(title_label)
            
            # Thumbnail
            thumbnail_label = QLabel()
            thumbnail_label.setAlignment(Qt.AlignCenter)
            thumbnail_label.setFixedHeight(180)
            # In a real app, you'd load the actual thumbnail
            thumbnail_label.setText("[Video Thumbnail]")
            layout.addWidget(thumbnail_label)
            
            # Description (truncated)
            if "description" in self.post_data:
                desc = self.post_data["description"]
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                desc_label = QLabel(desc)
                desc_label.setWordWrap(True)
                layout.addWidget(desc_label)
            
            # Metrics and link
            metrics_layout = QHBoxLayout()
            if "views" in self.post_data:
                views_label = QLabel(f"👁️ {self.post_data['views']} views")
                metrics_layout.addWidget(views_label)
            if "likes" in self.post_data:
                likes_label = QLabel(f"👍 {self.post_data['likes']}")
                metrics_layout.addWidget(likes_label)
            metrics_layout.addStretch()
            
            # Watch button
            if "video_url" in self.post_data:
                watch_button = QPushButton("Watch")
                watch_button.setStyleSheet("background-color: #ff0000; color: white;")
                watch_button.clicked.connect(lambda: self.open_video_url(self.post_data["video_url"]))
                metrics_layout.addWidget(watch_button)
            
            layout.addLayout(metrics_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        # Like/Share buttons (these would hook to the real APIs in a full implementation)
        like_button = QPushButton("Like")
        like_button.setStyleSheet("background-color: #eee;")
        actions_layout.addWidget(like_button)
        
        share_button = QPushButton("Share")
        share_button.setStyleSheet("background-color: #eee;")
        actions_layout.addWidget(share_button)
        
        layout.addLayout(actions_layout)
        self.setLayout(layout)
    
    def open_video_url(self, url):
        # Open URL in default browser
        webbrowser.open(url)

class SocialMediaManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # Init auth data storage
        self.auth_data = {
            "facebook": {},
            "instagram": {},
            "youtube": {}
        }
        
        # Load any saved credentials
        self.load_saved_auth()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel("Social Media Integration")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Connect your social media accounts to view and interact with your feeds")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Tabs for different platforms
        self.tabs = QTabWidget()
        
        # Facebook tab
        self.facebook_tab = QWidget()
        self.setup_facebook_tab()
        self.tabs.addTab(self.facebook_tab, "Facebook")
        
        # Instagram tab
        self.instagram_tab = QWidget()
        self.setup_instagram_tab()
        self.tabs.addTab(self.instagram_tab, "Instagram")
        
        # YouTube tab
        self.youtube_tab = QWidget()
        self.setup_youtube_tab()
        self.tabs.addTab(self.youtube_tab, "YouTube")
        
        main_layout.addWidget(self.tabs)
        
        # Settings section
        settings_group = QGroupBox("Display Settings")
        settings_layout = QFormLayout()
        
        # Update frequency
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItem("Manual Refresh Only", 0)
        self.refresh_combo.addItem("Every 5 minutes", 5)
        self.refresh_combo.addItem("Every 15 minutes", 15)
        self.refresh_combo.addItem("Every 30 minutes", 30)
        self.refresh_combo.addItem("Every hour", 60)
        
        settings_layout.addRow("Feed Refresh:", self.refresh_combo)
        
        # Max items to show
        self.max_items_combo = QComboBox()
        for i in range(5, 55, 10):
            self.max_items_combo.addItem(f"{i} posts", i)
        self.max_items_combo.setCurrentIndex(0)  # Default 5
        
        settings_layout.addRow("Max Posts to Show:", self.max_items_combo)
        
        # Auto-open option
        self.auto_open_check = QCheckBox("Open feeds automatically on startup")
        settings_layout.addRow(self.auto_open_check)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Refresh all button
        refresh_all_button = QPushButton("Refresh All Feeds")
        refresh_all_button.clicked.connect(self.refresh_all_feeds)
        main_layout.addWidget(refresh_all_button)
        
        self.setLayout(main_layout)
    
    def setup_facebook_tab(self):
        layout = QVBoxLayout()
        
        # Auth section
        auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout()
        
        self.fb_status_label = QLabel("Not connected")
        auth_layout.addWidget(self.fb_status_label)
        
        self.fb_connect_button = QPushButton("Connect to Facebook")
        self.fb_connect_button.clicked.connect(self.connect_facebook)
        auth_layout.addWidget(self.fb_connect_button)
        
        # Token entry (in a real app, you'd use proper OAuth flow)
        token_layout = QHBoxLayout()
        self.fb_token_input = QLineEdit()
        self.fb_token_input.setPlaceholderText("Enter Facebook access token...")
        self.fb_token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.fb_token_input)
        
        fb_save_token = QPushButton("Save Token")
        fb_save_token.clicked.connect(lambda: self.save_token("facebook"))
        token_layout.addWidget(fb_save_token)
        
        auth_layout.addLayout(token_layout)
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Feed section
        feed_group = QGroupBox("Facebook Feed")
        feed_layout = QVBoxLayout()
        
        # Scroll area for feed
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.fb_feed_container = QWidget()
        self.fb_feed_layout = QVBoxLayout()
        self.fb_feed_layout.addStretch()
        self.fb_feed_container.setLayout(self.fb_feed_layout)
        scroll.setWidget(self.fb_feed_container)
        
        feed_layout.addWidget(scroll)
        
        # Feed control buttons
        buttons_layout = QHBoxLayout()
        
        fb_refresh = QPushButton("Refresh Feed")
        fb_refresh.clicked.connect(lambda: self.load_feed("facebook"))
        buttons_layout.addWidget(fb_refresh)
        
        fb_clear = QPushButton("Clear Feed")
        fb_clear.clicked.connect(lambda: self.clear_feed("facebook"))
        buttons_layout.addWidget(fb_clear)
        
        feed_layout.addLayout(buttons_layout)
        feed_group.setLayout(feed_layout)
        layout.addWidget(feed_group)
        
        self.facebook_tab.setLayout(layout)
    
    def setup_instagram_tab(self):
        layout = QVBoxLayout()
        
        # Auth section
        auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout()
        
        self.ig_status_label = QLabel("Not connected")
        auth_layout.addWidget(self.ig_status_label)
        
        self.ig_connect_button = QPushButton("Connect to Instagram")
        self.ig_connect_button.clicked.connect(self.connect_instagram)
        auth_layout.addWidget(self.ig_connect_button)
        
        # Token entry (in a real app, you'd use proper OAuth flow)
        token_layout = QHBoxLayout()
        self.ig_token_input = QLineEdit()
        self.ig_token_input.setPlaceholderText("Enter Instagram access token...")
        self.ig_token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.ig_token_input)
        
        ig_save_token = QPushButton("Save Token")
        ig_save_token.clicked.connect(lambda: self.save_token("instagram"))
        token_layout.addWidget(ig_save_token)
        
        auth_layout.addLayout(token_layout)
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Feed section
        feed_group = QGroupBox("Instagram Feed")
        feed_layout = QVBoxLayout()
        
        # Grid layout for Instagram posts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.ig_feed_container = QWidget()
        self.ig_feed_layout = QGridLayout()
        self.ig_feed_layout.setSpacing(10)
        self.ig_feed_container.setLayout(self.ig_feed_layout)
        scroll.setWidget(self.ig_feed_container)
        
        feed_layout.addWidget(scroll)
        
        # Feed control buttons
        buttons_layout = QHBoxLayout()
        
        ig_refresh = QPushButton("Refresh Feed")
        ig_refresh.clicked.connect(lambda: self.load_feed("instagram"))
        buttons_layout.addWidget(ig_refresh)
        
        ig_clear = QPushButton("Clear Feed")
        ig_clear.clicked.connect(lambda: self.clear_feed("instagram"))
        buttons_layout.addWidget(ig_clear)
        
        feed_layout.addLayout(buttons_layout)
        feed_group.setLayout(feed_layout)
        layout.addWidget(feed_group)
        
        self.instagram_tab.setLayout(layout)
    
    def setup_youtube_tab(self):
        layout = QVBoxLayout()
        
        # Auth section
        auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout()
        
        self.yt_status_label = QLabel("Not connected")
        auth_layout.addWidget(self.yt_status_label)
        
        self.yt_connect_button = QPushButton("Connect to YouTube")
        self.yt_connect_button.clicked.connect(self.connect_youtube)
        auth_layout.addWidget(self.yt_connect_button)
        
        # Token entry (in a real app, you'd use proper OAuth flow)
        token_layout = QHBoxLayout()
        self.yt_token_input = QLineEdit()
        self.yt_token_input.setPlaceholderText("Enter YouTube API key...")
        self.yt_token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.yt_token_input)
        
        yt_save_token = QPushButton("Save Token")
        yt_save_token.clicked.connect(lambda: self.save_token("youtube"))
        token_layout.addWidget(yt_save_token)
        
        auth_layout.addLayout(token_layout)
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Feed section
        feed_group = QGroupBox("YouTube Feed")
        feed_layout = QVBoxLayout()
        
        # Scroll area for feed
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.yt_feed_container = QWidget()
        self.yt_feed_layout = QVBoxLayout()
        self.yt_feed_layout.addStretch()
        self.yt_feed_container.setLayout(self.yt_feed_layout)
        scroll.setWidget(self.yt_feed_container)
        
        feed_layout.addWidget(scroll)
        
        # Feed control buttons
        buttons_layout = QHBoxLayout()
        
        yt_refresh = QPushButton("Refresh Feed")
        yt_refresh.clicked.connect(lambda: self.load_feed("youtube"))
        buttons_layout.addWidget(yt_refresh)
        
        yt_clear = QPushButton("Clear Feed")
        yt_clear.clicked.connect(lambda: self.clear_feed("youtube"))
        buttons_layout.addWidget(yt_clear)
        
        feed_layout.addLayout(buttons_layout)
        feed_group.setLayout(feed_layout)
        layout.addWidget(feed_group)
        
        self.youtube_tab.setLayout(layout)
    
    def connect_facebook(self):
        """Open Facebook authentication process"""
        # In a real app, this would use proper OAuth flow
        # For demo, just simulating with manual token entry
        token = self.fb_token_input.text()
        if token:
            self.fb_status_label.setText("Connecting...")
            self.auth_data["facebook"]["token"] = token
            
            # Start authentication thread
            self.fb_auth_thread = SocialMediaAuth("facebook", self.auth_data["facebook"])
            self.fb_auth_thread.auth_completed.connect(self.on_auth_completed)
            self.fb_auth_thread.auth_failed.connect(self.on_auth_failed)
            self.fb_auth_thread.start()
        else:
            QMessageBox.warning(self, "Authentication Error", 
                               "Please enter a Facebook access token.")
    
    def connect_instagram(self):
        """Open Instagram authentication process"""
        # In a real app, this would use proper OAuth flow
        token = self.ig_token_input.text()
        if token:
            self.ig_status_label.setText("Connecting...")
            self.auth_data["instagram"]["token"] = token
            
            # Start authentication thread
            self.ig_auth_thread = SocialMediaAuth("instagram", self.auth_data["instagram"])
            self.ig_auth_thread.auth_completed.connect(self.on_auth_completed)
            self.ig_auth_thread.auth_failed.connect(self.on_auth_failed)
            self.ig_auth_thread.start()
        else:
            QMessageBox.warning(self, "Authentication Error", 
                               "Please enter an Instagram access token.")
    
    def connect_youtube(self):
        """Open YouTube authentication process"""
        # In a real app, this would use proper OAuth flow
        token = self.yt_token_input.text()
        if token:
            self.yt_status_label.setText("Connecting...")
            self.auth_data["youtube"]["token"] = token
            
            # Start authentication thread
            self.yt_auth_thread = SocialMediaAuth("youtube", self.auth_data["youtube"])
            self.yt_auth_thread.auth_completed.connect(self.on_auth_completed)
            self.yt_auth_thread.auth_failed.connect(self.on_auth_failed)
            self.yt_auth_thread.start()
        else:
            QMessageBox.warning(self, "Authentication Error", 
                               "Please enter a YouTube API key.")
    
    def on_auth_completed(self, platform, auth_data):
        """Handle successful authentication"""
        self.auth_data[platform] = auth_data
        
        # Update UI
        if platform == "facebook":
            self.fb_status_label.setText("Connected")
            self.fb_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.fb_connect_button.setText("Reconnect")
            # Load feed automatically
            self.load_feed("facebook")
        
        elif platform == "instagram":
            self.ig_status_label.setText("Connected")
            self.ig_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.ig_connect_button.setText("Reconnect")
            # Load feed automatically
            self.load_feed("instagram")
        
        elif platform == "youtube":
            self.yt_status_label.setText("Connected")
            self.yt_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.yt_connect_button.setText("Reconnect")
            # Load feed automatically
            self.load_feed("youtube")
        
        # Save credentials
        self.save_auth_data()
    
    def on_auth_failed(self, platform, error_msg):
        """Handle authentication failure"""
        if platform == "facebook":
            self.fb_status_label.setText("Connection Failed")
            self.fb_status_label.setStyleSheet("color: red;")
        elif platform == "instagram":
            self.ig_status_label.setText("Connection Failed")
            self.ig_status_label.setStyleSheet("color: red;")
        elif platform == "youtube":
            self.yt_status_label.setText("Connection Failed")
            self.yt_status_label.setStyleSheet("color: red;")
        
        QMessageBox.warning(self, "Authentication Error", 
                           f"Failed to connect to {platform.capitalize()}: {error_msg}")
    
    def load_feed(self, platform):
        """Load feed for the specified platform"""
        if not self.auth_data[platform]:
            QMessageBox.warning(self, "Not Authenticated", 
                               f"Please connect to {platform.capitalize()} first.")
            return
        
        # Clear existing feed
        self.clear_feed(platform)
        
        # Update UI to show loading
        if platform == "facebook":
            self.fb_feed_layout.insertWidget(0, QLabel("Loading feed..."))
        elif platform == "instagram":
            self.ig_feed_layout.addWidget(QLabel("Loading feed..."), 0, 0)
        elif platform == "youtube":
            self.yt_feed_layout.insertWidget(0, QLabel("Loading feed..."))
        
        # Get max items setting
        max_items = self.max_items_combo.currentData()
        
        # Start loader thread
        self.feed_loader = SocialMediaFeedLoader(platform, self.auth_data[platform], max_items)
        self.feed_loader.feed_loaded.connect(self.on_feed_loaded)
        self.feed_loader.feed_error.connect(self.on_feed_error)
        self.feed_loader.start()
    
    def on_feed_loaded(self, platform, feed_items):
        """Handle loaded feed data"""
        # Clear any loading indicators
        self.clear_feed(platform)
        
        if platform == "facebook":
            # Add feed items in reverse order (newest first)
            for item in feed_items:
                post_widget = PostWidget(platform, item)
                self.fb_feed_layout.insertWidget(0, post_widget)
        
        elif platform == "instagram":
            # Add feed items in a grid
            for i, item in enumerate(feed_items):
                row = i // 2
                col = i % 2
                post_widget = PostWidget(platform, item)
                self.ig_feed_layout.addWidget(post_widget, row, col)
        
        elif platform == "youtube":
            # Add feed items in reverse order (newest first)
            for item in feed_items:
                post_widget = PostWidget(platform, item)
                self.yt_feed_layout.insertWidget(0, post_widget)
    
    def on_feed_error(self, platform, error_msg):
        """Handle feed loading error"""
        # Clear any loading indicators
        self.clear_feed(platform)
        
        error_label = QLabel(f"Error loading feed: {error_msg}")
        error_label.setStyleSheet("color: red;")
        
        if platform == "facebook":
            self.fb_feed_layout.insertWidget(0, error_label)
        elif platform == "instagram":
            self.ig_feed_layout.addWidget(error_label, 0, 0)
        elif platform == "youtube":
            self.yt_feed_layout.insertWidget(0, error_label)
    
    def clear_feed(self, platform):
        """Clear feed display for the specified platform"""
        if platform == "facebook":
            # Remove all widgets except the stretch at the end
            while self.fb_feed_layout.count() > 1:
                item = self.fb_feed_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        elif platform == "instagram":
            # Clear the grid layout
            while self.ig_feed_layout.count():
                item = self.ig_feed_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        elif platform == "youtube":
            # Remove all widgets except the stretch at the end
            while self.yt_feed_layout.count() > 1:
                item = self.yt_feed_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
    
    def save_token(self, platform):
        """Save entered token"""
        if platform == "facebook":
            token = self.fb_token_input.text()
            if token:
                self.auth_data[platform]["token"] = token
                self.connect_facebook()
        
        elif platform == "instagram":
            token = self.ig_token_input.text()
            if token:
                self.auth_data[platform]["token"] = token
                self.connect_instagram()
        
        elif platform == "youtube":
            token = self.yt_token_input.text()
            if token:
                self.auth_data[platform]["token"] = token
                self.connect_youtube()
    
    def refresh_all_feeds(self):
        """Refresh all connected feeds"""
        for platform in ["facebook", "instagram", "youtube"]:
            if self.is_connected(platform):
                self.load_feed(platform)
    
    def is_connected(self, platform):
        """Check if a platform is connected"""
        return bool(self.auth_data.get(platform, {}).get("token", ""))
    
    def save_auth_data(self):
        """Save authentication data to file"""
        # In a real app, use secure storage for tokens
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Only store minimal data and encrypt in real app
            save_data = {}
            for platform, auth in self.auth_data.items():
                if "token" in auth:
                    # In production, encrypt tokens!
                    save_data[platform] = {"has_token": True}
            
            with open(data_dir / "social_auth.json", "w") as f:
                json.dump(save_data, f)
        except Exception as e:
            print(f"Error saving auth data: {e}")
    
    def load_saved_auth(self):
        """Load saved authentication data"""
        try:
            data_file = Path("data") / "social_auth.json"
            if data_file.exists():
                with open(data_file, "r") as f:
                    saved_data = json.load(f)
                
                # Update UI to reflect saved state
                for platform, data in saved_data.items():
                    if data.get("has_token"):
                        if platform == "facebook":
                            self.fb_status_label.setText("Token saved (reconnect needed)")
                            self.fb_status_label.setStyleSheet("color: orange;")
                        elif platform == "instagram":
                            self.ig_status_label.setText("Token saved (reconnect needed)")
                            self.ig_status_label.setStyleSheet("color: orange;")
                        elif platform == "youtube":
                            self.yt_status_label.setText("Token saved (reconnect needed)")
                            self.yt_status_label.setStyleSheet("color: orange;")
        except Exception as e:
            print(f"Error loading auth data: {e}")

if __name__ == "__main__":
    # For standalone testing
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = SocialMediaManager()
    window.show()
    sys.exit(app.exec_()) 