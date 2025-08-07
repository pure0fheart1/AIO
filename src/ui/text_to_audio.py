import sys
import os
import tempfile
import webbrowser
import pyttsx3 # Added for system voices
import shutil # Added for saving

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QComboBox, QFileDialog, QMessageBox, 
    QApplication, QProgressDialog, QSlider, QFormLayout # Added Slider, FormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from gtts import gTTS, gTTSError
from gtts.lang import tts_langs

# --- TTS Generation Thread (gTTS) --- 
class TTSThread(QThread):
    finished_signal = pyqtSignal(bool, str) # success, output_file_path or error_message
    
    def __init__(self, text_to_speak, lang_code, slow=False):
        super().__init__()
        self.text_to_speak = text_to_speak
        self.lang_code = lang_code
        self.slow = slow
        
    def run(self):
        try:
            # Create gTTS object
            tts = gTTS(text=self.text_to_speak, lang=self.lang_code, slow=self.slow)
            
            # Create a temporary file to save the audio
            # Use delete=False so we can open it with webbrowser before cleaning up
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name
                tts.save(temp_filename)
            
            self.finished_signal.emit(True, temp_filename)
            
        except gTTSError as ge:
            self.finished_signal.emit(False, f"gTTS Error: {ge}")
        except Exception as e:
            self.finished_signal.emit(False, f"An unexpected error occurred: {e}")

# --- TTS Generation Thread (pyttsx3) ---
class SystemTTSThread(QThread):
    finished_signal = pyqtSignal(bool, str) # success, output_file_path or error_message
    
    def __init__(self, text_to_speak, voice_id, rate, volume):
        super().__init__()
        self.text_to_speak = text_to_speak
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        
    def run(self):
        engine = None # Ensure engine is defined in the outer scope
        try:
            engine = pyttsx3.init()
            if self.voice_id:
                engine.setProperty('voice', self.voice_id)
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # Create a temporary file to save the audio (use WAV)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
                temp_filename = fp.name
            
            engine.save_to_file(self.text_to_speak, temp_filename)
            engine.runAndWait() # Wait for saving to complete
            engine.stop() # Clean up engine resources
            del engine # Explicitly delete engine instance
            
            # Check if the file was actually created and has size
            if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                self.finished_signal.emit(True, temp_filename)
            else:
                 self.finished_signal.emit(False, "Engine failed to save the audio file.")

        except RuntimeError as rt_err:
             self.finished_signal.emit(False, f"pyttsx3 Runtime Error: {rt_err}. Ensure audio drivers are available.")
             if engine:
                try: 
                   engine.stop()
                   del engine
                except: pass # Ignore errors during cleanup
        except Exception as e:
            self.finished_signal.emit(False, f"An unexpected error occurred with pyttsx3: {e}")
            if engine:
                try: 
                   engine.stop()
                   del engine
                except: pass # Ignore errors during cleanup

# --- Main Widget --- 
class TextToAudioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.last_generated_file = None
        self.last_generated_format = "mp3" # Keep track of format (mp3 or wav)
        self.tts_thread = None
        self.system_voices = []
        self.pyttsx3_engine = None # Keep engine reference for properties
        self._initialize_pyttsx3()
        self.init_ui()

    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 engine and get available voices."""
        try:
            # Initialize temporarily to get voices
            temp_engine = pyttsx3.init()
            self.system_voices = temp_engine.getProperty('voices')
            temp_engine.stop()
            del temp_engine # Clean up temporary engine
            print(f"Found {len(self.system_voices)} system voices.")
        except Exception as e:
            print(f"Could not initialize pyttsx3 or get voices: {e}")
            self.system_voices = []
            QMessageBox.warning(self, "System Voices Error", 
                                "Could not load system voices. pyttsx3 might not be installed correctly or supported.")

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Text to Audio")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Text Input Area
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text here to convert to speech...")
        layout.addWidget(self.text_input, 1) 
        
        # --- Engine Selection --- 
        engine_layout = QHBoxLayout()
        engine_label = QLabel("Engine:")
        self.engine_combo = QComboBox()
        self.engine_combo.addItem("gTTS (Online, MP3)", "gtts")
        # Add system voices option only if voices were found
        if self.system_voices:
            self.engine_combo.addItem("System Voices (Offline, WAV)", "pyttsx3")
        else:
             self.engine_combo.addItem("System Voices (Unavailable)", "pyttsx3")
             self.engine_combo.model().item(1).setEnabled(False)
             
        self.engine_combo.currentIndexChanged.connect(self.on_engine_changed)
        engine_layout.addWidget(engine_label)
        engine_layout.addWidget(self.engine_combo)
        engine_layout.addStretch()
        layout.addLayout(engine_layout)

        # --- Options Box (Visibility toggles based on engine) ---
        self.options_box = QWidget()
        options_form_layout = QFormLayout(self.options_box)
        options_form_layout.setContentsMargins(0, 5, 0, 5)
        options_form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows) # Improve wrapping
        
        # gTTS Options (Language)
        self.gtts_lang_label = QLabel("gTTS Language:")
        self.gtts_lang_combo = QComboBox()
        self.populate_languages()
        options_form_layout.addRow(self.gtts_lang_label, self.gtts_lang_combo)
        
        # System Voices Options (Voice, Rate, Volume)
        self.system_voice_label = QLabel("System Voice:")
        self.system_voice_combo = QComboBox()
        self.populate_system_voices()
        options_form_layout.addRow(self.system_voice_label, self.system_voice_combo)
        
        self.system_rate_label_widget = QLabel("Rate:") # Explicit label widget
        self.system_rate_slider = QSlider(Qt.Horizontal)
        self.system_rate_slider.setRange(50, 400) 
        self.system_rate_slider.setValue(200) 
        self.system_rate_slider.valueChanged.connect(lambda v: self.system_rate_value_label.setText(f"{v} wpm"))
        self.system_rate_value_label = QLabel("200 wpm") # Separate label for value
        rate_widget = QWidget() # Use a container widget for the slider+value
        rate_layout = QHBoxLayout(rate_widget)
        rate_layout.setContentsMargins(0,0,0,0)
        rate_layout.addWidget(self.system_rate_slider)
        rate_layout.addWidget(self.system_rate_value_label)
        options_form_layout.addRow(self.system_rate_label_widget, rate_widget)

        self.system_volume_label_widget = QLabel("Volume:") # Explicit label widget
        self.system_volume_slider = QSlider(Qt.Horizontal)
        self.system_volume_slider.setRange(0, 100) 
        self.system_volume_slider.setValue(100)
        self.system_volume_slider.valueChanged.connect(lambda v: self.system_volume_value_label.setText(f"{v}%"))
        self.system_volume_value_label = QLabel("100%") # Separate label for value
        volume_widget = QWidget() # Use a container widget for the slider+value
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0,0,0,0)
        volume_layout.addWidget(self.system_volume_slider)
        volume_layout.addWidget(self.system_volume_value_label)
        options_form_layout.addRow(self.system_volume_label_widget, volume_widget)
        
        layout.addWidget(self.options_box)
        
        # Initial UI state based on default engine
        self.on_engine_changed() 
        
        # Buttons Layout
        buttons_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Generate Audio")
        self.generate_button.clicked.connect(self.generate_audio)
        
        self.play_button = QPushButton("Play Audio")
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False) # Disabled until audio is generated
        
        self.save_button = QPushButton("Save Audio As...")
        self.save_button.clicked.connect(self.save_audio)
        self.save_button.setEnabled(False) # Disabled until audio is generated
        
        buttons_layout.addWidget(self.generate_button)
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)

    def populate_languages(self):
        """Populate the gTTS language dropdown."""
        self.gtts_lang_combo.clear()
        try:
            supported_langs = tts_langs()
            # Sort languages by name for better usability
            sorted_langs = sorted(supported_langs.items(), key=lambda item: item[1])
            for code, name in sorted_langs:
                self.gtts_lang_combo.addItem(f"{name} ({code})", code)
            # Set default to English if available
            default_index = self.gtts_lang_combo.findData("en")
            if default_index >= 0:
                self.gtts_lang_combo.setCurrentIndex(default_index)
        except Exception as e:
            print(f"Error fetching gTTS languages: {e}")
            QMessageBox.warning(self, "Language Error", "Could not load supported languages.")
            self.gtts_lang_combo.addItem("English (en)", "en") # Fallback

    def populate_system_voices(self):
        """Populate the system voice dropdown."""
        self.system_voice_combo.clear()
        if not self.system_voices:
            self.system_voice_combo.addItem("No Voices Found")
            self.system_voice_combo.setEnabled(False)
            return
            
        for voice in self.system_voices:
            # Attempt to create a descriptive name
            name = voice.name
            lang = getattr(voice, 'lang', '') # lang might not exist on all OS
            gender = getattr(voice, 'gender', '') # gender might not exist
            display_name = f"{name}" 
            if lang: display_name += f" ({lang})"
            if gender: display_name += f" [{gender}]"
            self.system_voice_combo.addItem(display_name, voice.id)
            
        self.system_voice_combo.setEnabled(True)

    def on_engine_changed(self):
        """Show/hide option widgets based on selected TTS engine."""
        selected_engine = self.engine_combo.currentData()
        is_gtts = selected_engine == "gtts"
        is_pyttsx3 = selected_engine == "pyttsx3" and self.system_voices

        # Toggle visibility of widgets associated with each option
        self.gtts_lang_label.setVisible(is_gtts)
        self.gtts_lang_combo.setVisible(is_gtts)
        
        self.system_voice_label.setVisible(is_pyttsx3)
        self.system_voice_combo.setVisible(is_pyttsx3)
        
        self.system_rate_label_widget.setVisible(is_pyttsx3)
        # Find the widget containing the rate slider and label
        rate_container_widget = self.system_rate_slider.parentWidget() 
        if rate_container_widget:
             rate_container_widget.setVisible(is_pyttsx3)
             
        self.system_volume_label_widget.setVisible(is_pyttsx3)
        # Find the widget containing the volume slider and label
        volume_container_widget = self.system_volume_slider.parentWidget()
        if volume_container_widget:
             volume_container_widget.setVisible(is_pyttsx3)

    def generate_audio(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Input Needed", "Please enter some text to convert.")
            return
            
        selected_engine = self.engine_combo.currentData()
        
        # --- Disable UI --- 
        self.generate_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.save_button.setEnabled(False)
        if self.parent and hasattr(self.parent, 'statusBar'):
             self.parent.statusBar().showMessage(f"Generating audio using {selected_engine}...")
        self.cleanup_temp_file()
        
        # --- Generate using Selected Engine --- 
        if selected_engine == "gtts":
            lang_code = self.gtts_lang_combo.currentData()
            if not lang_code:
                QMessageBox.warning(self, "Language Needed", "Please select a gTTS language.")
                self.generate_button.setEnabled(True) # Re-enable
                return
            self.last_generated_format = "mp3"
            self.tts_thread = TTSThread(text, lang_code)
            self.tts_thread.finished_signal.connect(self.on_generation_finished)
            self.tts_thread.start()
            
        elif selected_engine == "pyttsx3":
            if not self.system_voices:
                QMessageBox.critical(self, "Engine Error", "System voices unavailable.")
                self.generate_button.setEnabled(True) # Re-enable
                return
                
            voice_id = self.system_voice_combo.currentData()
            rate = self.system_rate_slider.value()
            volume = self.system_volume_slider.value() / 100.0 # Convert % to 0.0-1.0
            self.last_generated_format = "wav"
            self.tts_thread = SystemTTSThread(text, voice_id, rate, volume)
            self.tts_thread.finished_signal.connect(self.on_generation_finished)
            self.tts_thread.start()
            
        else:
            QMessageBox.critical(self, "Engine Error", "Invalid or unavailable engine selected.")
            self.generate_button.setEnabled(True) # Re-enable

    def on_generation_finished(self, success, result):
        """Handle result from the TTS thread."""
        self.generate_button.setEnabled(True) # Re-enable generate button
        if self.parent and hasattr(self.parent, 'statusBar'):
             self.parent.statusBar().clearMessage()
             
        if success:
            self.last_generated_file = result # Store path to the temp file (mp3 or wav)
            self.play_button.setEnabled(True)
            self.save_button.setEnabled(True)
            if self.parent and hasattr(self.parent, 'statusBar'):
                 self.parent.statusBar().showMessage("Audio generated successfully.", 3000)
            # Optionally auto-play after generation?
            # self.play_audio() 
        else:
            error_message = result
            QMessageBox.critical(self, "Generation Error", f"Failed to generate audio:\n{error_message}")
            self.last_generated_file = None
            self.play_button.setEnabled(False)
            self.save_button.setEnabled(False)
            if self.parent and hasattr(self.parent, 'statusBar'):
                 self.parent.statusBar().showMessage("Audio generation failed.", 3000)
                 
    def play_audio(self):
        if self.last_generated_file and os.path.exists(self.last_generated_file):
            try:
                # Use webbrowser to open the file with the default system player
                webbrowser.open(self.last_generated_file)
                if self.parent and hasattr(self.parent, 'statusBar'):
                     self.parent.statusBar().showMessage("Playing audio...", 2000)
            except Exception as e:
                QMessageBox.critical(self, "Playback Error", f"Could not play audio file: {e}")
        else:
            QMessageBox.warning(self, "No Audio", "No audio file generated or file not found.")

    def save_audio(self):
        if not self.last_generated_file or not os.path.exists(self.last_generated_file):
            QMessageBox.warning(self, "No Audio", "Please generate audio first before saving.")
            return
            
        # Suggest filename based on text and format
        first_words = "_".join(self.text_input.toPlainText().split()[:5])
        file_extension = self.last_generated_format # Use the stored format
        default_filename = f"{first_words}.{file_extension}"
        file_filter = f"{file_extension.upper()} Audio Files (*.{file_extension})"
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Audio As", 
            default_filename,
            file_filter
        )
        
        if save_path:
            try:
                # Ensure the path ends with the correct extension
                if not save_path.lower().endswith(f'.{file_extension}'):
                    save_path += f'.{file_extension}'
                
                shutil.copy2(self.last_generated_file, save_path)
                QMessageBox.information(self, "Save Successful", f"Audio saved to:\n{save_path}")
                if self.parent and hasattr(self.parent, 'statusBar'):
                     self.parent.statusBar().showMessage(f"Audio saved to {save_path}", 4000)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save audio file: {e}")

    def cleanup_temp_file(self):
        """Deletes the previously generated temporary audio file, if it exists."""
        if self.last_generated_file and os.path.exists(self.last_generated_file):
            try:
                os.remove(self.last_generated_file)
                print(f"Cleaned up temp file: {self.last_generated_file}")
                self.last_generated_file = None
            except Exception as e:
                print(f"Warning: Could not delete temp file {self.last_generated_file}: {e}")

    def closeEvent(self, event):
        """Ensure temporary file is deleted when the widget is closed."""
        self.cleanup_temp_file()
        super().closeEvent(event) 