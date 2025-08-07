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
                             QScrollArea, QSlider, QMessageBox, QStackedWidget) # Added QStackedWidget
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
        main_layout = QVBoxLayout(self) # Set layout on self
        
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
        
        # self.setLayout(main_layout) # Set in constructor
        self.setWindowTitle("Audio Recorder and Transcriber") # Window title usually set by main window
        
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
        # Ensure combo boxes exist before accessing them
        if hasattr(self, 'device_combo'):
            self.on_device_changed(self.device_combo.currentIndex()) 
        if hasattr(self, 'language_combo'):
             self.on_language_changed(self.language_combo.currentIndex())
        if hasattr(self, 'engine_combo'):
             self.on_engine_changed(self.engine_combo.currentIndex())
        if hasattr(self, 'buffer_slider'):
             self.on_buffer_size_changed(self.buffer_slider.value())
        
        # Populate the devices dropdown initially
        self.refresh_devices()

    def refresh_devices(self):
        """Refresh the list of available audio devices"""
        self.add_debug_message("Loading audio devices...")
        try:
            devices = sd.query_devices()
            # Convert the DeviceList to a standard Python list before emitting
            # Ensure devices is actually iterable and contains dicts before converting
            if isinstance(devices, (list, tuple)) or hasattr(devices, '__iter__'):
                device_list_for_signal = list(devices) 
            elif isinstance(devices, dict): # Handle case where query_devices might return a single dict for default
                device_list_for_signal = [devices]
            else:
                device_list_for_signal = [] # Fallback
            self.device_list_signal.emit(device_list_for_signal)
        except Exception as e:
            self.add_debug_message(f"Error querying audio devices: {e}")
            traceback.print_exc() # Print full traceback for debugging
            self.device_list_signal.emit([]) # Emit empty list on error
        
    def populate_devices(self, devices):
        """Populate the devices dropdown with available input devices"""
        self.device_combo.clear()
        self.device_combo.addItem("Default Input Device", None) # Add default option first
        
        found_input_devices = 0
        if devices: # Check if devices list is not None or empty
            for i, device_info in enumerate(devices):
                # sd.query_devices() can return dicts or sometimes just device names
                # We need robust checking
                is_input = False
                name = f"Device {i}"
                device_id = i # Default to index if specific ID isn't clear
                channels = 0
                
                if isinstance(device_info, dict):
                    if device_info.get('max_input_channels', 0) > 0:
                        is_input = True
                        name = device_info.get('name', 'Unknown Device')
                        channels = device_info.get('max_input_channels', 0)
                        # Try to get a consistent ID, default to index if not available
                        device_id = device_info.get('index', i) 
                # Add more checks here if query_devices returns other types
                
                if is_input:
                    try:
                        # Add item to combo box
                        self.device_combo.addItem(f"{name} ({channels} ch)", device_id)
                        found_input_devices += 1
                    except Exception as e:
                         self.add_debug_message(f"Error adding device to combo: {device_info} - Error: {e}")
        
        if found_input_devices == 0:
            self.add_debug_message("No active audio input devices found. Check microphone connection and permissions.")
            # Avoid showing QMessageBox from worker thread/signal handler if possible
            # Consider logging or updating status bar instead.
            # QMessageBox.warning(self, "No Input Devices", "No audio input devices found. Please check your microphone.")
        else:
             self.add_debug_message(f"Found {found_input_devices} audio input devices.")
        
        # Automatically select the default device (index 0, data None) or first actual device
        if self.device_combo.count() > 1:
            # Check if default device seems valid (can be tricky to determine programmatically)
            # Heuristic: If default name contains typical system keywords, maybe skip?
            # For now, just select the first *actual* device if available.
            self.device_combo.setCurrentIndex(1) 
        else:
            self.device_combo.setCurrentIndex(0) # Keep Default selected if no others found


    def on_device_changed(self, index):
        """Handle device selection change"""
        if index >= 0:
            device_id = self.device_combo.itemData(index)
            self.input_device_id = device_id # Can be None for default
            self.add_debug_message(f"Selected device: {self.device_combo.currentText()} (ID: {self.input_device_id})")
            if hasattr(self, 'help_text'):
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
            can_change_lang = (engine == "google")
            self.language_combo.setEnabled(can_change_lang)
            
            if engine != "google":
                self.add_debug_message("Note: Sphinx engine primarily supports US English (check installed models)")
                # Automatically switch to English if Sphinx is selected?
                en_us_index = self.language_combo.findData("en-US")
                if en_us_index >= 0:
                    self.language_combo.setCurrentIndex(en_us_index)
                if hasattr(self, 'help_text'):
                    self.help_text.setText("Sphinx is less accurate but works offline. Speak clearly.")
            else:
                 if hasattr(self, 'help_text'):
                     self.help_text.setText("Google provides better recognition but needs internet & API key/limits.")
                
    def on_buffer_size_changed(self, value):
        """Handle buffer size slider change"""
        buffer_size = value / 10.0  # Convert from slider value to seconds
        self.buffer_label.setText(f"{buffer_size:.1f} sec")
        self.buffer_duration_ms = int(buffer_size * 1000)
        
    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            try:
                # Ensure a device is selected (allow default)
                if self.device_combo.currentIndex() < 0: 
                     QMessageBox.warning(self, "No Device", "Please select an audio input device.")
                     return

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
                traceback.print_exc()
                self.is_recording = False
                self.record_button.setText("Start Recording")
                self.device_combo.setEnabled(True)
                self.engine_combo.setEnabled(True)
                self.language_combo.setEnabled(self.recognition_engine == "google")
                self.buffer_slider.setEnabled(True)
                self.help_text.setText(f"ERROR: {str(e)}. Try selecting a different device.")
                QMessageBox.critical(self, "Recording Error", f"Could not start recording: {str(e)}\n\nPlease check the selected device and audio settings.")
        else:
            self.stop_event.set() # Signal threads to stop
            self.is_recording = False
            self.record_button.setText("Start Recording")
            self.status_label.setText("Ready to record")
            
            # Re-enable settings
            self.device_combo.setEnabled(True)
            self.engine_combo.setEnabled(True)
            # Only enable language if google engine is selected
            self.language_combo.setEnabled(self.recognition_engine == "google")
            self.buffer_slider.setEnabled(True)
            self.help_text.setText("Recording stopped. You can start again when ready.")
            
    def _recording_loop(self):
        """Continuously records audio into a queue in a separate thread."""
        block_size_frames = int(self.sample_rate * self.buffer_duration_ms / 1000)
        
        try:
            self.add_debug_message(f"Starting audio stream with device={self.input_device_id}, rate={self.sample_rate}, blocksize={block_size_frames}")
            # Use sd.CallbackFlags() for status checking
            flags = sd.CallbackFlags()
            
            def audio_callback(indata, frames, time, status):
                if status:
                    flags.data = status # Store status flags
                    self.debug_signal.emit(f"Stream status: {status}")
                # Calculate RMS volume from float32 data
                rms = np.sqrt(np.mean(indata**2))
                level_percent = min(100, int(rms * 500)) # Arbitrary scaling
                self.audio_level_signal.emit(level_percent)
                # Put the raw audio chunk (as bytes) into the queue
                self.audio_queue.put(indata.tobytes())

            with sd.InputStream(samplerate=self.sample_rate, 
                               device=self.input_device_id, 
                               channels=self.channels, 
                               dtype='float32', # Use float32 for RMS
                               blocksize=block_size_frames,
                               callback=audio_callback):
                self.add_debug_message("Audio stream started.")
                while not self.stop_event.is_set():
                    sd.sleep(100) # Sleep briefly to yield thread
                    if flags.input_overflow:
                        self.debug_signal.emit("Warning: Input overflowed!")
                        flags.input_overflow = False # Reset flag
                    if flags.input_underflow:
                         self.debug_signal.emit("Warning: Input underflow!")
                         flags.input_underflow = False
                    # Check for other error flags if needed

                    
        except sd.PortAudioError as pae:
             error_msg = f"PortAudioError: {pae}. Try another device or sample rate."
             self.debug_signal.emit(error_msg)
             # Use QTimer to safely update UI from main thread
             QTimer.singleShot(0, lambda: self.status_label.setText(f"Audio Error: {pae}")) 
             QTimer.singleShot(0, self.stop_recording_ui) # Reset UI state safely
        except Exception as e:
            error_msg = f"Error in recording loop: {str(e)}"
            self.debug_signal.emit(error_msg)
            traceback.print_exc()
            QTimer.singleShot(0, lambda: self.status_label.setText(f"Error: {e}")) 
            QTimer.singleShot(0, self.stop_recording_ui)
        finally:
            self.add_debug_message("Recording loop finished.")

    def stop_recording_ui(self):
         """ Safely stops the recording state from the UI thread. """
         if self.is_recording:
              self.toggle_recording() # Call the toggle function to handle state changes

    def _recognition_loop(self):
        """Continuously processes audio from queue for speech recognition."""
        self.add_debug_message("Recognition loop started.")
        # Calculate bytes per sample for AudioData
        bytes_per_sample = np.dtype(np.int16).itemsize # Assuming we want 16-bit for recognition

        while not self.stop_event.is_set() or not self.audio_queue.empty():
            try:
                # Get float32 audio data bytes from the queue
                audio_data_bytes_float32 = self.audio_queue.get(timeout=0.1) 
                
                # Convert float32 numpy array back from bytes
                audio_chunk_float32 = np.frombuffer(audio_data_bytes_float32, dtype=np.float32)
                
                # Convert float32 to int16 for speech_recognition library
                # Scale float32 from [-1.0, 1.0] to int16 [-32768, 32767]
                audio_chunk_int16 = (audio_chunk_float32 * 32767).astype(np.int16)
                audio_data_bytes_int16 = audio_chunk_int16.tobytes()

                # Create AudioData object with int16 data
                audio_data = sr.AudioData(audio_data_bytes_int16, self.sample_rate, bytes_per_sample)
                
                self.debug_signal.emit(f"Processing audio chunk ({len(audio_data_bytes_int16)} bytes) for recognition...")
                
                # Recognize speech using selected engine
                text = None
                if self.recognition_engine == "google":
                    try:
                        text = self.recognizer.recognize_google(audio_data, language=self.language_code)
                        self.debug_signal.emit(f"Google recognized: '{text}'")
                    except sr.UnknownValueError:
                        self.debug_signal.emit("Google Speech Recognition could not understand audio")
                    except sr.RequestError as e:
                        self.debug_signal.emit(f"Google API Error: {e}")
                        # Consider stopping or warning user about API issues
                
                elif self.recognition_engine == "sphinx":
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data) # Sphinx might not use language code directly here
                        self.debug_signal.emit(f"Sphinx recognized: '{text}'")
                    except sr.UnknownValueError:
                        self.debug_signal.emit("Sphinx could not understand audio")
                    except Exception as e_sphinx: 
                        self.debug_signal.emit(f"Sphinx error: {e_sphinx}")
                        if "missing PocketSphinx" in str(e_sphinx).lower():
                           self.debug_signal.emit("ERROR: PocketSphinx is not installed or configured correctly. Install via pip: pip install pocketsphinx")
                           # Stop recording? Disable Sphinx?
                           QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Sphinx Error", "PocketSphinx not found. Please install it."))
                           QTimer.singleShot(0, self.stop_recording_ui)
                           break # Exit recognition loop if Sphinx is fundamentally broken
                
                if text:
                    self.transcription_signal.emit(text)
                           
            except queue.Empty:
                continue 
            except Exception as e:
                self.debug_signal.emit(f"Error in recognition loop: {str(e)}")
                traceback.print_exc()
                # Avoid flooding with errors, maybe add a delay or limit
                time.sleep(0.5) 
                
        self.add_debug_message("Recognition loop finished.")

    def update_transcription(self, text):
        """Update the text display with new transcription"""
        current_text = self.text_display.toPlainText()
        # Add a space if text already exists, unless the new text starts with punctuation
        separator = " " if current_text and text and not text[0] in (' ', '.', '?', '!', ',') else ""
        self.text_display.insertPlainText(separator + text)
        # Ensure cursor is visible
        self.text_display.moveCursor(self.text_display.textCursor().End)
        # self.add_debug_message(f"Transcription: {text}") # Redundant if emitted from loop
        
        # Update help text on successful transcription
        if hasattr(self, 'help_text'):
             self.help_text.setText("Successfully transcribed! Continue speaking or stop recording.")
    
    def update_voice_level(self, level_percent):
        """Update the voice level indicator (expects 0-100)"""
        self.voice_level_bar.setValue(level_percent)
        self.voice_level_indicator.setText(f"{level_percent}%")
        
        # Update help text based on level
        if hasattr(self, 'help_text'):
            if self.is_recording and level_percent > 10:
                self.help_text.setText("Good audio level detected.")
            elif self.is_recording and level_percent < 5 and level_percent > 0:
                self.help_text.setText("Audio level LOW. Speak louder or move closer.")
            
    def show_troubleshooting(self):
        """Show troubleshooting dialog"""
        tips = (
            "<b>Speech Recognition Troubleshooting:</b><br><br>"
            "<b>1. Microphone Issues:</b><br>"
            "• Select a different input device from the dropdown.<br>"
            "• Ensure the mic isn't muted in OS settings.<br>"
            "• Check physical connection.<br>"
            "• Try adjusting Buffer Size slider (0.5-1.5 sec is typical).<br><br>"
            
            "<b>2. Poor Recognition / No Output:</b><br>"
            "• Switch to Sphinx engine (works offline, less accurate).<br>"
            "• Speak slowly and clearly, closer to the mic.<br>"
            "• Use simple words and phrases.<br>"
            "• Reduce background noise.<br>"
            "• If using Google, check internet connection.<br><br>"
            
            "<b>3. Google Errors (e.g., API limits, network):</b><br>"
            "• Switch to Sphinx engine.<br>"
            "• Check internet connection.<br>"
            "• Wait if you suspect API limits were reached.<br><br>"
            
            "<b>4. Sphinx Errors:</b><br>"
            "• Ensure PocketSphinx is installed (`pip install pocketsphinx`).<br>"
            "• Sphinx is less accurate, especially with noise or accents.<br><br>"

            "<b>5. 'Input Overflow/Underflow' Errors:</b><br>"
            "• Try a different microphone device.<br>"
            "• Adjust the buffer size slider.<br>"
            "• Close other apps using the microphone.<br>"
        )
        
        QMessageBox.information(self, "Troubleshooting Tips", tips)
            
    def add_debug_message(self, message):
        """Add a debug message to the log, safely callable from threads."""
        # This method might be called from background threads,
        # but appending to QTextEdit should be thread-safe in Qt.
        # However, checking the checkbox state should ideally happen in the main thread.
        # For simplicity, we risk a minor race condition on the checkbox read.
        if hasattr(self, 'show_debug_check') and not self.show_debug_check.isChecked():
            return
            
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Use QTimer.singleShot to ensure UI updates happen in the main thread
        QTimer.singleShot(0, lambda: self._append_debug_text(formatted_message))

    def _append_debug_text(self, message):
        """Helper method to append text to debug log in main thread."""
        self.debug_text.append(message)
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
        # This might be called if the widget is embedded and the parent closes.
        self.add_debug_message("AudioRecorderWidget close event triggered.")
        if self.is_recording:
            self.stop_event.set() # Signal threads to stop
            # Wait for threads to finish (with a timeout)
            if self.recording_thread and self.recording_thread.is_alive():
                self.add_debug_message("Waiting for recording thread...")
                self.recording_thread.join(timeout=0.5)
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.add_debug_message("Waiting for recognition thread...")
                self.recognition_thread.join(timeout=0.5)
        self.add_debug_message("AudioRecorderWidget cleanup complete.")
        # No event.accept() needed if it's just a QWidget closing
        super().closeEvent(event)

    # --- Registration Method --- 
    def register(self, stack: QStackedWidget):
        """ Placeholder for factory registration method """
        print(f"AudioRecorderWidget register called (Placeholder)")
        pass 