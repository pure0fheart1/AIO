import sys
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
import queue
import threading
import traceback # For detailed error logging

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QProgressBar, QHBoxLayout,
                             QComboBox, QGroupBox, QFormLayout, QCheckBox,
                             QScrollArea, QSlider, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer # Added QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
import time

class VoiceLevelBar(QProgressBar):
    """Custom progress bar for voice level visualization"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 3px;
                background-color: #f0f0f0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ab80a, stop:0.5 #ffff00, stop:1 #ff0000);
            }
        """)

class AudioRecorderWidget(QWidget):
    # Define signals previously expected from AudioRecorder
    transcription_signal = pyqtSignal(str)
    audio_level_signal = pyqtSignal(int)
    device_list_signal = pyqtSignal(list)
    debug_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Recording State
        self.is_recording = False
        self.input_device_id = None
        self.language_code = "en-US"
        self.recognition_engine = "sphinx" # Default to offline
        self.buffer_duration_ms = 1000 # Milliseconds
        self.sample_rate = 16000 # Common sample rate for speech recognition
        self.channels = 1 # Mono audio
        
        # Threading and Queue
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.recognition_thread = None
        self.stop_event = threading.Event()
        
        # Speech Recognition
        self.recognizer = sr.Recognizer()
        # Adjust energy threshold - may need tweaking
        self.recognizer.energy_threshold = 4000 
        self.recognizer.dynamic_energy_threshold = True
        
        # UI Setup
        self.init_ui() 
        # Moved setup_recorder content here and adapted it
        self.setup_internal_recorder_state()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Settings group
        settings_group = QGroupBox("Audio Settings")
        settings_layout = QFormLayout()
        
        # Device selection
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        refresh_button = QPushButton("Refresh Devices")
        refresh_button.clicked.connect(self.refresh_devices)
        
        device_layout = QHBoxLayout()
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(refresh_button)
        
        # Language selection
        self.language_combo = QComboBox()
        self.populate_languages()
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        # Engine selection
        self.engine_combo = QComboBox()
        self.engine_combo.addItem("Google (Online)", "google")
        self.engine_combo.addItem("Sphinx (Offline)", "sphinx")
        self.engine_combo.setCurrentIndex(1)  # Default to Sphinx to avoid API limits
        self.engine_combo.currentIndexChanged.connect(self.on_engine_changed)
        
        # Buffer size slider
        buffer_layout = QHBoxLayout()
        self.buffer_slider = QSlider(Qt.Horizontal)
        self.buffer_slider.setRange(5, 50)  # 0.5 to 5.0 seconds (x10)
        self.buffer_slider.setValue(10)  # Default 1.0 seconds
        self.buffer_slider.setTickPosition(QSlider.TicksBelow)
        self.buffer_slider.setTickInterval(5)
        self.buffer_slider.valueChanged.connect(self.on_buffer_size_changed)
        
        self.buffer_label = QLabel("1.0 sec")
        buffer_layout.addWidget(self.buffer_slider)
        buffer_layout.addWidget(self.buffer_label)
        
        # Troubleshooting section
        self.troubleshoot_button = QPushButton("Troubleshooting Tips")
        self.troubleshoot_button.clicked.connect(self.show_troubleshooting)
        
        # Show Debug checkbox
        self.show_debug_check = QCheckBox("Show Debug Messages")
        self.show_debug_check.setChecked(True)
        
        settings_layout.addRow("Input Device:", device_layout)
        settings_layout.addRow("Language:", self.language_combo)
        settings_layout.addRow("Recognition Engine:", self.engine_combo)
        settings_layout.addRow("Buffer Size:", buffer_layout)
        settings_layout.addRow(self.troubleshoot_button)
        settings_layout.addRow(self.show_debug_check)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Status and Debug Info
        self.status_label = QLabel("Ready to record")
        self.status_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # Debug log area
        debug_group = QGroupBox("Speech Recognition Log")
        debug_layout = QVBoxLayout()
        
        # Make debug scroll area with text
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMaximumHeight(100)
        self.debug_text.setStyleSheet("font-family: monospace; color: #444; background-color: #f8f8f8;")
        
        # Clear debug button
        self.clear_debug_button = QPushButton("Clear Log")
        self.clear_debug_button.clicked.connect(self.clear_debug)
        
        debug_layout.addWidget(self.debug_text)
        debug_layout.addWidget(self.clear_debug_button)
        debug_group.setLayout(debug_layout)
        main_layout.addWidget(debug_group)
        
        # Voice level indicator
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Voice Level:"))
        self.voice_level_bar = VoiceLevelBar()
        self.voice_level_indicator = QLabel("0%")
        self.voice_level_indicator.setMinimumWidth(40)
        level_layout.addWidget(self.voice_level_bar)
        level_layout.addWidget(self.voice_level_indicator)
        main_layout.addLayout(level_layout)
        
        # Text display area
        text_group = QGroupBox("Transcribed Text")
        text_layout = QVBoxLayout()
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        
        text_layout.addWidget(self.text_display)
        text_group.setLayout(text_layout)
        main_layout.addWidget(text_group)
        
        # Record button
        button_layout = QHBoxLayout()
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setStyleSheet("font-weight: bold; padding: 8px;")
        
        # Clear button
        self.clear_button = QPushButton("Clear Text")
        self.clear_button.clicked.connect(self.clear_text)
        
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        # Help text
        self.help_text = QLabel("Tips: Speak clearly and slowly. Adjust microphone position for better results.")
        self.help_text.setStyleSheet("font-style: italic; color: #666;")
        self.help_text.setWordWrap(True)
        main_layout.addWidget(self.help_text)
        
        self.setLayout(main_layout)
        self.setWindowTitle("Audio Recorder and Transcriber")
        
    def populate_languages(self):
        """Populate language dropdown with common options"""
        languages = [
            ("en-US", "English (US)"),
            ("en-GB", "English (UK)"),
            ("en-AU", "English (Australia)"),
            ("fr-FR", "French"),
            ("de-DE", "German"),
            ("es-ES", "Spanish"),
            ("it-IT", "Italian"),
            ("ja-JP", "Japanese"),
            ("ko-KR", "Korean"),
            ("zh-CN", "Chinese (Simplified)"),
            ("ru-RU", "Russian"),
            ("pt-BR", "Portuguese (Brazil)"),
            ("hi-IN", "Hindi"),
            ("ar-AE", "Arabic")
        ]
        
        for code, name in languages:
            self.language_combo.addItem(name, code)
        
    def setup_internal_recorder_state(self):
        """Initialize internal state, load devices, set defaults."""
        self.transcription_signal.connect(self.update_transcription)
        self.audio_level_signal.connect(self.update_voice_level)
        self.device_list_signal.connect(self.populate_devices)
        self.debug_signal.connect(self.add_debug_message)
        
        # Set initial values from UI elements
        self.on_device_changed(self.device_combo.currentIndex()) # Trigger device set
        self.on_language_changed(self.language_combo.currentIndex())
        self.on_engine_changed(self.engine_combo.currentIndex())
        self.on_buffer_size_changed(self.buffer_slider.value())
        
        # Populate the devices dropdown initially
        self.refresh_devices()

    def refresh_devices(self):
        """Refresh the list of available audio devices"""
        self.add_debug_message("Loading audio devices...")
        try:
            devices = sd.query_devices()
            # Convert the DeviceList to a standard Python list before emitting
            device_list_for_signal = list(devices) 
            self.device_list_signal.emit(device_list_for_signal)
        except Exception as e:
            self.add_debug_message(f"Error querying audio devices: {e}")
            self.device_list_signal.emit([]) # Emit empty list on error
        
    def populate_devices(self, devices):
        """Populate the devices dropdown with available input devices"""
        self.device_combo.clear()
        self.device_combo.addItem("Default Input Device", None) # Add default option first
        
        found_input_devices = 0
        for device_info in devices:
            # Check if it's an input device (has input channels)
            if isinstance(device_info, dict) and device_info.get('max_input_channels', 0) > 0:
                try:
                    device_id = device_info.get('index') # Usually the device ID is the index
                    name = device_info.get('name', 'Unknown Device')
                    channels = device_info.get('max_input_channels', 0)
                    # host_api = device_info.get('hostapi', -1) # Can be useful for debugging
                    
                    # Add item to combo box
                    self.device_combo.addItem(f"{name} ({channels} ch)", device_id)
                    found_input_devices += 1
                except Exception as e:
                     self.add_debug_message(f"Error processing device info: {device_info} - Error: {e}")
            # else: # Optional: Log devices that are not input devices
            #    if isinstance(device_info, dict):
            #       self.add_debug_message(f"Ignoring non-input device: {device_info.get('name')}")
        
        if found_input_devices == 0:
            self.add_debug_message("No active audio input devices found. Check microphone connection and permissions.")
            QMessageBox.warning(self, "No Input Devices", "No audio input devices found. Please check your microphone.")
        else:
             self.add_debug_message(f"Found {found_input_devices} audio input devices.")
        
        # Automatically select the default device if it's available and reasonable
        # Or select the first available non-default device
        if self.device_combo.count() > 1:
             self.device_combo.setCurrentIndex(1) # Select the first actual device
        else:
             self.device_combo.setCurrentIndex(0) # Keep Default selected if no others found

    def on_device_changed(self, index):
        """Handle device selection change"""
        if index >= 0:
            device_id = self.device_combo.itemData(index)
            self.input_device_id = device_id
            self.add_debug_message(f"Selected device: {self.device_combo.currentText()}")
            self.help_text.setText("New device selected. Try recording to test it.")
            
    def on_language_changed(self, index):
        """Handle language selection change"""
        if index >= 0:
            language_code = self.language_combo.itemData(index)
            self.language_code = language_code
            self.add_debug_message(f"Selected language: {self.language_combo.currentText()} ({language_code})")
        
    def on_engine_changed(self, index):
        """Handle recognition engine selection change"""
        if index >= 0:
            engine = self.engine_combo.itemData(index)
            self.recognition_engine = engine
            self.add_debug_message(f"Selected recognition engine: {self.engine_combo.currentText()}")
            
            # Enable/disable language dropdown based on engine
            self.language_combo.setEnabled(engine == "google")
            if engine != "google":
                self.add_debug_message("Note: Sphinx engine only supports US English")
                self.help_text.setText("Sphinx is less accurate but works offline. Speak clearly and use simple phrases.")
            else:
                self.help_text.setText("Google provides better recognition but has API limits. Speak naturally.")
                
    def on_buffer_size_changed(self, value):
        """Handle buffer size slider change"""
        buffer_size = value / 10.0  # Convert from slider value to seconds
        self.buffer_label.setText(f"{buffer_size:.1f} sec")
        self.buffer_duration_ms = int(buffer_size * 1000)
        
    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            try:
                self.stop_event.clear() # Reset stop event
                # Clear the queue
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break
                
                self.is_recording = True
                self.record_button.setText("Stop Recording")
                self.status_label.setText("Recording...")
                
                # Disable settings during recording
                self.device_combo.setEnabled(False)
                self.engine_combo.setEnabled(False)
                self.language_combo.setEnabled(False)
                self.buffer_slider.setEnabled(False)
                self.help_text.setText("Recording active. Speak clearly into the microphone.")
                
                # Start threads
                self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
                self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
                self.recording_thread.start()
                self.recognition_thread.start()
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.add_debug_message(f"Failed to start recording: {str(e)}")
                self.is_recording = False
                self.record_button.setText("Start Recording")
                self.device_combo.setEnabled(True)
                self.engine_combo.setEnabled(True)
                self.language_combo.setEnabled(self.recognition_engine == "google")
                self.buffer_slider.setEnabled(True)
                self.help_text.setText(f"ERROR: {str(e)}. Try selecting a different device.")
        else:
            self.stop_event.set() # Signal threads to stop
            self.is_recording = False
            self.record_button.setText("Start Recording")
            self.status_label.setText("Ready to record")
            
            # Re-enable settings
            self.device_combo.setEnabled(True)
            self.engine_combo.setEnabled(True)
            self.language_combo.setEnabled(self.recognition_engine == "google")
            self.buffer_slider.setEnabled(True)
            self.help_text.setText("Recording stopped. You can start again when ready.")
            
    def _recording_loop(self):
        """Continuously records audio into a queue in a separate thread."""
        block_size_frames = int(self.sample_rate * self.buffer_duration_ms / 1000)
        
        try:
            self.add_debug_message(f"Starting audio stream with device={self.input_device_id}, rate={self.sample_rate}, blocksize={block_size_frames}")
            with sd.InputStream(samplerate=self.sample_rate, 
                               device=self.input_device_id, 
                               channels=self.channels, 
                               dtype='float32', # Use float32 for RMS calculation
                               blocksize=block_size_frames) as stream:
                self.add_debug_message("Audio stream started.")
                while not self.stop_event.is_set():
                    audio_chunk, overflowed = stream.read(block_size_frames)
                    if overflowed:
                        self.debug_signal.emit("Warning: Input overflowed!")
                    
                    # Calculate RMS volume
                    rms = np.sqrt(np.mean(audio_chunk**2))
                    # Convert RMS to a percentage (needs calibration)
                    # This scaling is arbitrary and might need adjustment
                    level_percent = min(100, int(rms * 500)) 
                    self.audio_level_signal.emit(level_percent)
                    
                    # Put the raw audio chunk into the queue for recognition
                    self.audio_queue.put(audio_chunk.tobytes())
                    
        except sd.PortAudioError as pae:
             self.debug_signal.emit(f"PortAudioError: {pae}. Try another device or sample rate.")
             # Attempt to safely stop UI elements from thread
             # This is generally discouraged, using signals is better, but as a fallback:
             # QTimer.singleShot(0, lambda: self.status_label.setText(f"Audio Error: {pae}")) 
             # QTimer.singleShot(0, lambda: self.toggle_recording()) # Attempt to reset UI state
        except Exception as e:
            self.debug_signal.emit(f"Error in recording loop: {str(e)}")
            traceback.print_exc()
        finally:
            self.add_debug_message("Recording loop finished.")
            # Ensure UI state is reset if loop terminates unexpectedly
            if self.is_recording:
                 QTimer.singleShot(0, lambda: self.toggle_recording()) # Use QTimer to call from main thread

    def _recognition_loop(self):
        """Continuously processes audio from queue for speech recognition."""
        self.add_debug_message("Recognition loop started.")
        while not self.stop_event.is_set() or not self.audio_queue.empty():
            try:
                audio_data_bytes = self.audio_queue.get(timeout=0.1) # Timeout to allow checking stop_event
                
                # Create AudioData object
                audio_data = sr.AudioData(audio_data_bytes, self.sample_rate, 2) # Assuming 16-bit samples (2 bytes)
                
                self.debug_signal.emit("Processing audio chunk for recognition...")
                
                # Recognize speech using selected engine
                if self.recognition_engine == "google":
                    try:
                        text = self.recognizer.recognize_google(audio_data, language=self.language_code)
                        self.debug_signal.emit(f"Google recognized: '{text}'")
                        self.transcription_signal.emit(text)
                    except sr.UnknownValueError:
                        self.debug_signal.emit("Google Speech Recognition could not understand audio")
                    except sr.RequestError as e:
                        self.debug_signal.emit(f"Could not request results from Google Speech Recognition service; {e}")
                
                elif self.recognition_engine == "sphinx":
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data, language=self.language_code)
                        self.debug_signal.emit(f"Sphinx recognized: '{text}'")
                        self.transcription_signal.emit(text)
                    except sr.UnknownValueError:
                        self.debug_signal.emit("Sphinx could not understand audio")
                    except Exception as e_sphinx: # Catch broader exceptions for Sphinx
                        self.debug_signal.emit(f"Sphinx error: {e_sphinx}")
                        # Check if pocketsphinx is installed properly
                        if "missing PocketSphinx" in str(e_sphinx).lower():
                           self.debug_signal.emit("ERROR: PocketSphinx is not installed or configured correctly. Install it via pip: pip install pocketsphinx")
                           # Maybe disable Sphinx option or show persistent error
                           
            except queue.Empty:
                # Queue is empty, check stop event again
                continue 
            except Exception as e:
                self.debug_signal.emit(f"Error in recognition loop: {str(e)}")
                traceback.print_exc()
                
        self.add_debug_message("Recognition loop finished.")

    def update_transcription(self, text):
        """Update the text display with new transcription"""
        current_text = self.text_display.toPlainText()
        if current_text:
            self.text_display.append(text)
        else:
            self.text_display.setText(text)
        self.add_debug_message(f"Transcription: {text}")
        
        # Update help text on successful transcription
        self.help_text.setText("Successfully transcribed your speech! Continue speaking.")
    
    def update_voice_level(self, level):
        """Update the voice level indicator"""
        # Convert float level (0.0-1.0) to percent (0-100)
        level_percent = int(level * 100)
        self.voice_level_bar.setValue(level_percent)
        self.voice_level_indicator.setText(f"{level_percent}%")
        
        # Update help text based on level
        if self.is_recording and level > 0.1:
            self.help_text.setText("Good audio level detected! Keep speaking.")
        elif self.is_recording and level < 0.05 and level > 0:
            self.help_text.setText("Audio level is LOW. Speak louder or move closer to the microphone.")
            
    def show_troubleshooting(self):
        """Show troubleshooting dialog"""
        tips = (
            "<b>Speech Recognition Troubleshooting:</b><br><br>"
            "<b>1. Microphone Issues:</b><br>"
            "• Select a different input device from the dropdown<br>"
            "• Make sure your microphone is not muted in Windows settings<br>"
            "• Try reducing the Buffer Size to 0.5-1.0 sec<br><br>"
            
            "<b>2. Recognition Problems:</b><br>"
            "• Switch to the Sphinx engine (works offline, less accurate)<br>"
            "• Speak slowly and clearly with pauses between phrases<br>"
            "• Use simple words and short sentences<br>"
            "• Reduce background noise in your environment<br><br>"
            
            "<b>3. If You See 'API Rate Limit':</b><br>"
            "• Switch to Sphinx engine immediately<br>"
            "• Wait 24 hours for Google quota to reset<br>"
            "• Restart the application<br><br>"
            
            "<b>4. 'Input Overflow' Errors:</b><br>"
            "• Try a different microphone device<br>"
            "• Reduce the buffer size<br>"
            "• Close other applications using the microphone<br>"
        )
        
        QMessageBox.information(self, "Troubleshooting Tips", tips)
            
    def add_debug_message(self, message):
        """Add a debug message to the log"""
        if not self.show_debug_check.isChecked():
            return
            
        # Add timestamp to message
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to debug text
        self.debug_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.debug_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
            
    def clear_text(self):
        """Clear the text display"""
        self.text_display.clear()
        self.add_debug_message("Transcribed text cleared")
        
    def clear_debug(self):
        """Clear the debug log"""
        self.debug_text.clear()
        
    def closeEvent(self, event):
        """Handle cleanup when widget is closed"""
        self.add_debug_message("Close event triggered.")
        if self.is_recording:
            self.stop_event.set() # Signal threads to stop
            # Wait for threads to finish (with a timeout)
            if self.recording_thread and self.recording_thread.is_alive():
                self.add_debug_message("Waiting for recording thread...")
                self.recording_thread.join(timeout=1.0)
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.add_debug_message("Waiting for recognition thread...")
                self.recognition_thread.join(timeout=1.0)
        self.add_debug_message("Cleanup complete.")
        event.accept() 