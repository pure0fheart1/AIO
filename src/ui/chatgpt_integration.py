import os
import sys
import json
import requests
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTextEdit, QLineEdit, QComboBox, QSplitter, QFrame,
                            QScrollArea, QMessageBox, QFileDialog, QDialog, QFormLayout,
                            QCheckBox, QSpinBox, QGroupBox, QInputDialog)
from PyQt5.QtCore import Qt, QSize, QSettings, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor, QIcon, QPalette

class ChatGPTIntegration(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.api_key = ""
        self.load_api_key()
        self.chat_history = []
        self.current_model = "gpt-3.5-turbo"
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        
        # Header with title and description
        header_layout = QVBoxLayout()
        title_label = QLabel("ChatGPT Integration")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        description_label = QLabel(
            "Interact with ChatGPT directly from the application. "
            "Ask questions, get assistance with tasks, or generate content."
        )
        description_label.setWordWrap(True)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(description_label)
        
        # API key setup
        api_key_layout = QHBoxLayout()
        self.api_status_label = QLabel("API Key: Not Set")
        if self.api_key:
            self.api_status_label.setText("API Key: Configured ✓")
            self.api_status_label.setStyleSheet("color: green;")
        else:
            self.api_status_label.setStyleSheet("color: red;")
        
        api_key_button = QPushButton("Set API Key")
        api_key_button.clicked.connect(self.set_api_key)
        
        api_key_layout.addWidget(self.api_status_label)
        api_key_layout.addStretch()
        api_key_layout.addWidget(api_key_button)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o", "gpt-4-turbo", "gpt-4-0125-preview", "gpt-4", "gpt-3.5-turbo-0125", "gpt-3.5-turbo"])
        self.model_combo.setCurrentText(self.current_model)
        self.model_combo.currentTextChanged.connect(self.change_model)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        # Chat area
        chat_layout = QVBoxLayout()
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(400)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        
        # Add to chat layout
        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_layout)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Chat")
        clear_button.clicked.connect(self.clear_chat)
        
        save_button = QPushButton("Save Conversation")
        save_button.clicked.connect(self.save_conversation)
        
        settings_button = QPushButton("Chat Settings")
        settings_button.clicked.connect(self.show_settings)
        
        actions_layout.addWidget(clear_button)
        actions_layout.addWidget(save_button)
        actions_layout.addStretch()
        actions_layout.addWidget(settings_button)
        
        # Add everything to main layout
        layout.addLayout(header_layout)
        layout.addLayout(api_key_layout)
        layout.addLayout(model_layout)
        layout.addLayout(chat_layout)
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
        
        # Welcome message
        self.display_system_message("Welcome to ChatGPT Integration! Set your API key to get started.")
        
    def load_api_key(self):
        """Load API key from settings"""
        settings = QSettings("VideoDownloader", "ChatGPT")
        self.api_key = settings.value("api_key", "")
        
    def save_api_key(self, key):
        """Save API key to settings"""
        settings = QSettings("VideoDownloader", "ChatGPT")
        settings.setValue("api_key", key)
        self.api_key = key
        
    def set_api_key(self):
        """Set the OpenAI API key"""
        key, ok = QInputDialog.getText(self, "API Key", 
                                     "Enter your OpenAI API key:", 
                                     QLineEdit.Password)
        if ok and key:
            self.save_api_key(key)
            self.api_status_label.setText("API Key: Configured ✓")
            self.api_status_label.setStyleSheet("color: green;")
            self.display_system_message("API key configured successfully. You can now chat with ChatGPT!")
        
    def change_model(self, model):
        """Change the ChatGPT model"""
        self.current_model = model
        self.display_system_message(f"Model changed to {model}")
        
    def send_message(self):
        """Send a message to ChatGPT"""
        message = self.message_input.text().strip()
        if not message:
            return
            
        if not self.api_key:
            QMessageBox.warning(self, "API Key Required", 
                               "Please set your OpenAI API key first.")
            return
            
        # Clear input field
        self.message_input.clear()
        
        # Display user message
        self.display_user_message(message)
        
        # Add to chat history
        self.chat_history.append({"role": "user", "content": message})
        
        # Show typing indicator
        self.display_system_message("ChatGPT is thinking...", temp=True)
        
        # Call the API
        try:
            response = self.call_openai_api(message)
            
            # Remove typing indicator
            self.remove_last_message()
            
            # Display response
            self.display_assistant_message(response)
            
            # Add to chat history
            self.chat_history.append({"role": "assistant", "content": response})
            
        except Exception as e:
            # Remove typing indicator
            self.remove_last_message()
            
            # Display error
            error_msg = str(e)
            self.display_system_message(f"Error: {error_msg}")
            QMessageBox.critical(self, "API Error", f"Error calling ChatGPT API: {error_msg}")
        
    def call_openai_api(self, message):
        """Call the OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.current_model,
            "messages": self.chat_history,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_info = response.json()
            raise Exception(f"API Error ({response.status_code}): {error_info.get('error', {}).get('message', 'Unknown error')}")
        
    def display_user_message(self, message):
        """Display a user message in the chat"""
        self.chat_display.append(f'<div style="text-align: right;"><span style="background-color: #DCF8C6; padding: 5px 10px; border-radius: 10px; display: inline-block; max-width: 70%; margin: 5px;"><b>You:</b><br>{message}</span></div>')
        
    def display_assistant_message(self, message):
        """Display an assistant message in the chat"""
        self.chat_display.append(f'<div style="text-align: left;"><span style="background-color: #E5E5EA; padding: 5px 10px; border-radius: 10px; display: inline-block; max-width: 70%; margin: 5px;"><b>ChatGPT:</b><br>{message}</span></div>')
        
    def display_system_message(self, message, temp=False):
        """Display a system message in the chat"""
        if temp:
            self.chat_display.append(f'<div style="text-align: center; color: #888; margin: 5px;" id="temp_message">{message}</div>')
        else:
            self.chat_display.append(f'<div style="text-align: center; color: #888; margin: 5px;">{message}</div>')
        
    def remove_last_message(self):
        """Remove the last message from the chat display"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove the newline
        
    def clear_chat(self):
        """Clear the chat history"""
        reply = QMessageBox.question(self, "Clear Chat", 
                                    "Are you sure you want to clear the chat history?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.chat_display.clear()
            self.chat_history = []
            self.display_system_message("Chat history cleared.")
        
    def save_conversation(self):
        """Save the conversation to a file"""
        if not self.chat_history:
            QMessageBox.information(self, "No Conversation", 
                                   "There is no conversation to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Conversation", 
                                                 "", "Text Files (*.txt);;JSON Files (*.json)")
        
        if not file_path:
            return
            
        try:
            if file_path.endswith(".json"):
                # Save as JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.chat_history, f, indent=2)
            else:
                # Save as text
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"ChatGPT Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    for msg in self.chat_history:
                        role = "You" if msg["role"] == "user" else "ChatGPT"
                        f.write(f"{role}: {msg['content']}\n\n")
                        
            if self.parent and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Conversation saved to {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving conversation: {str(e)}")
        
    def show_settings(self):
        """Show chat settings dialog"""
        dialog = ChatSettingsDialog(self, self.current_model)
        if dialog.exec_():
            # Apply settings
            self.current_model = dialog.model_combo.currentText()
            self.display_system_message(f"Settings updated. Using model: {self.current_model}")


class ChatSettingsDialog(QDialog):
    def __init__(self, parent=None, current_model="gpt-3.5-turbo"):
        super().__init__(parent)
        self.setWindowTitle("Chat Settings")
        self.setup_ui(current_model)
        
    def setup_ui(self, current_model):
        layout = QVBoxLayout()
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o", "gpt-4-turbo", "gpt-4-0125-preview", "gpt-4", "gpt-3.5-turbo-0125", "gpt-3.5-turbo"])
        self.model_combo.setCurrentText(current_model)
        
        model_layout.addRow("Model:", self.model_combo)
        model_group.setLayout(model_layout)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout()
        
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(1, 10)
        self.temperature_spin.setValue(7)  # Default temperature 0.7
        self.temperature_spin.setToolTip("Controls randomness: 1 is most deterministic, 10 is most creative")
        
        self.stream_checkbox = QCheckBox("Stream responses")
        self.stream_checkbox.setChecked(False)
        self.stream_checkbox.setToolTip("Show responses as they're generated (may not work with all models)")
        
        advanced_layout.addRow("Temperature (÷10):", self.temperature_spin)
        advanced_layout.addRow(self.stream_checkbox)
        advanced_group.setLayout(advanced_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        
        # Add to main layout
        layout.addWidget(model_group)
        layout.addWidget(advanced_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout) 