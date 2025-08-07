import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QSlider, QFileDialog, QStyle, QSizePolicy, QMessageBox,
                            QComboBox, QCheckBox, QGroupBox, QFormLayout)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPalette, QColor

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Set background color to black
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        
        # Create media player
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_error)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QPushButton()
        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_pause)
        
        # Stop button
        self.stop_button = QPushButton()
        self.stop_button.setEnabled(False)
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        
        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)  # Default volume
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # Volume label
        self.volume_label = QLabel()
        self.volume_label.setPixmap(self.style().standardPixmap(QStyle.SP_MediaVolume))
        
        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white;")
        self.time_label.setMinimumWidth(100)
        
        # Add controls to layout
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.volume_label)
        controls_layout.addWidget(self.volume_slider)
        
        # File controls
        file_controls_layout = QHBoxLayout()
        
        # Open file button
        self.open_button = QPushButton("Open Video")
        self.open_button.clicked.connect(self.open_file)
        
        # Fullscreen button
        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.is_fullscreen = False
        
        # Add playback speed control
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentIndex(2)  # Default to 1.0x
        self.speed_combo.currentIndexChanged.connect(self.change_playback_speed)
        
        # Add loop checkbox
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setStyleSheet("color: white;")
        self.loop_checkbox.stateChanged.connect(self.toggle_loop)
        
        file_controls_layout.addWidget(self.open_button)
        file_controls_layout.addWidget(QLabel("Speed:"))
        file_controls_layout.addWidget(self.speed_combo)
        file_controls_layout.addWidget(self.loop_checkbox)
        file_controls_layout.addStretch(1)
        file_controls_layout.addWidget(self.fullscreen_button)
        
        # Add codec info section
        codec_info_group = QGroupBox("Codec Information")
        codec_info_group.setStyleSheet("color: white;")
        codec_layout = QVBoxLayout()
        
        self.codec_info_label = QLabel("No media loaded")
        self.codec_info_label.setStyleSheet("color: white;")
        self.codec_info_label.setWordWrap(True)
        
        codec_layout.addWidget(self.codec_info_label)
        codec_info_group.setLayout(codec_layout)
        
        # Add troubleshooting section
        troubleshoot_group = QGroupBox("Troubleshooting")
        troubleshoot_group.setStyleSheet("color: white;")
        troubleshoot_layout = QVBoxLayout()
        
        self.troubleshoot_label = QLabel(
            "If you're having issues playing videos:\n"
            "1. Make sure you have the necessary codecs installed\n"
            "2. Try installing K-Lite Codec Pack (Windows) or VLC (all platforms)\n"
            "3. Some formats may require additional system libraries"
        )
        self.troubleshoot_label.setStyleSheet("color: white;")
        self.troubleshoot_label.setWordWrap(True)
        
        # Alternative player button
        self.alt_player_button = QPushButton("Open in System Player")
        self.alt_player_button.setEnabled(False)
        self.alt_player_button.clicked.connect(self.open_in_system_player)
        
        troubleshoot_layout.addWidget(self.troubleshoot_label)
        troubleshoot_layout.addWidget(self.alt_player_button)
        troubleshoot_group.setLayout(troubleshoot_layout)
        
        # Add widgets to main layout
        layout.addWidget(self.video_widget)
        layout.addLayout(controls_layout)
        layout.addLayout(file_controls_layout)
        layout.addWidget(codec_info_group)
        layout.addWidget(troubleshoot_group)
        
        self.setLayout(layout)
        
        # Set initial volume
        self.media_player.setVolume(70)
        
        # Store the current file path
        self.current_file_path = None
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video", 
                                                 "", "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm)")
        
        if file_path:
            self.current_file_path = file_path
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.alt_player_button.setEnabled(True)
            self.play_pause()  # Start playing automatically
            
            # Update codec info
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            self.codec_info_label.setText(
                f"File: {file_name}\n"
                f"Size: {file_size:.2f} MB\n"
                f"Format: {os.path.splitext(file_path)[1]}"
            )
            
            # Show filename in status bar if parent exists
            if self.parent and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Playing: {file_name}")
    
    def play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def stop(self):
        self.media_player.stop()
    
    def media_state_changed(self, state):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            
        # Handle looping
        if state == QMediaPlayer.StoppedState and self.loop_checkbox.isChecked():
            self.media_player.play()
    
    def position_changed(self, position):
        self.position_slider.setValue(position)
        
        # Update time display
        duration = self.media_player.duration()
        if duration > 0:
            current_time = self.format_time(position)
            total_time = self.format_time(duration)
            self.time_label.setText(f"{current_time} / {total_time}")
    
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
    
    def set_position(self, position):
        self.media_player.setPosition(position)
    
    def set_volume(self, volume):
        self.media_player.setVolume(volume)
    
    def handle_error(self):
        self.play_button.setEnabled(False)
        error_msg = self.media_player.errorString()
        
        # Update the codec info with error details
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            self.codec_info_label.setText(
                f"Error playing: {file_name}\n"
                f"Error message: {error_msg}\n\n"
                f"Try using the 'Open in System Player' button below."
            )
        
        QMessageBox.warning(self, "Media Player Error", 
                           f"Error: {error_msg}\n\n"
                           f"This may be due to missing codecs. Try installing additional codec packs "
                           f"or use an external player like VLC.")
    
    def format_time(self, milliseconds):
        """Convert milliseconds to mm:ss format"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            # Save the normal geometry
            self.normal_geometry = self.geometry()
            
            # Make the video widget fullscreen
            self.video_widget.setFullScreen(True)
            self.is_fullscreen = True
        else:
            # Restore normal view
            self.video_widget.setFullScreen(False)
            self.is_fullscreen = False
    
    def change_playback_speed(self, index):
        """Change the playback speed"""
        speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        if 0 <= index < len(speeds):
            self.media_player.setPlaybackRate(speeds[index])
    
    def toggle_loop(self, state):
        """Toggle looping playback"""
        # The actual looping is handled in media_state_changed
        pass
    
    def open_in_system_player(self):
        """Open the current file in the system's default player"""
        if not self.current_file_path:
            return
            
        try:
            # Different ways to open the file based on the OS
            if sys.platform.startswith('win'):
                os.startfile(self.current_file_path)
            elif sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{self.current_file_path}"')
            else:  # Linux and others
                os.system(f'xdg-open "{self.current_file_path}"')
                
            if self.parent and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Opened in system player: {os.path.basename(self.current_file_path)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open in system player: {str(e)}")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Space:
            self.play_pause()
        elif event.key() == Qt.Key_Right:
            # Skip forward 5 seconds
            self.media_player.setPosition(self.media_player.position() + 5000)
        elif event.key() == Qt.Key_Left:
            # Skip backward 5 seconds
            self.media_player.setPosition(max(0, self.media_player.position() - 5000))
        else:
            super().keyPressEvent(event) 