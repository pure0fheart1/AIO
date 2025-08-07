from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTextEdit, QFrame,
                            QMessageBox, QListWidget, QListWidgetItem, QSplitter)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont
import json
import os
import traceback
import time

class VocabularyLearner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Define data file path relative to this script (src/ui/...)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_dir = os.path.join(project_root, 'data')
        self.vocab_file = os.path.join(self.data_dir, "vocabulary.json")
        self.vocabulary = []
        self.current_index = -1
        self.show_definition = False
        self.setup_ui()
        self.load_vocabulary()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Vocabulary Learner")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont('Arial', 18, QFont.Bold))
        layout.addWidget(header)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Word input and learning area
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Word input section
        input_group = QFrame()
        input_group.setFrameStyle(QFrame.Box | QFrame.Raised)
        input_layout = QVBoxLayout(input_group)
        
        # Word input
        word_layout = QHBoxLayout()
        word_label = QLabel("Word:")
        self.word_input = QLineEdit()
        word_layout.addWidget(word_label)
        word_layout.addWidget(self.word_input)
        
        # Meaning input
        meaning_layout = QVBoxLayout()
        meaning_label = QLabel("Meaning:")
        self.meaning_input = QTextEdit()
        self.meaning_input.setMaximumHeight(100)
        meaning_layout.addWidget(meaning_label)
        meaning_layout.addWidget(self.meaning_input)
        
        # Add word button
        add_button = QPushButton("Add Word")
        add_button.clicked.connect(self.add_word)
        
        input_layout.addLayout(word_layout)
        input_layout.addLayout(meaning_layout)
        input_layout.addWidget(add_button)
        
        # Learning section
        learning_group = QFrame()
        learning_group.setFrameStyle(QFrame.Box | QFrame.Raised)
        learning_layout = QVBoxLayout(learning_group)
        
        # Word display
        self.word_display = QLabel("Click a word to start learning")
        self.word_display.setAlignment(Qt.AlignCenter)
        self.word_display.setFont(QFont('Arial', 24))
        self.word_display.setStyleSheet("padding: 20px;")
        
        # Meaning display
        self.meaning_display = QLabel("")
        self.meaning_display.setAlignment(Qt.AlignCenter)
        self.meaning_display.setWordWrap(True)
        self.meaning_display.setStyleSheet("padding: 10px;")
        
        # Attempt input
        attempt_layout = QHBoxLayout()
        self.attempt_input = QLineEdit()
        self.attempt_input.setPlaceholderText("Type the word here")
        self.attempt_input.returnPressed.connect(self.check_attempt)
        attempt_button = QPushButton("Check")
        attempt_button.clicked.connect(self.check_attempt)
        attempt_layout.addWidget(self.attempt_input)
        attempt_layout.addWidget(attempt_button)
        
        # Stats display
        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignCenter)
        
        learning_layout.addWidget(self.word_display)
        learning_layout.addWidget(self.meaning_display)
        learning_layout.addLayout(attempt_layout)
        learning_layout.addWidget(self.stats_label)
        
        # Add groups to left layout
        left_layout.addWidget(input_group)
        left_layout.addWidget(learning_group)
        
        # Right side - Word lists
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Learning list
        learning_list_group = QFrame()
        learning_list_group.setFrameStyle(QFrame.Box | QFrame.Raised)
        learning_list_layout = QVBoxLayout(learning_list_group)
        
        learning_list_label = QLabel("Words to Learn")
        learning_list_label.setAlignment(Qt.AlignCenter)
        self.learning_list = QListWidget()
        self.learning_list.itemClicked.connect(self.select_word)
        
        learning_list_layout.addWidget(learning_list_label)
        learning_list_layout.addWidget(self.learning_list)
        
        # Learned list
        learned_list_group = QFrame()
        learned_list_group.setFrameStyle(QFrame.Box | QFrame.Raised)
        learned_list_layout = QVBoxLayout(learned_list_group)
        
        learned_list_label = QLabel("Learned Words")
        learned_list_label.setAlignment(Qt.AlignCenter)
        self.learned_list = QListWidget()
        self.learned_list.itemClicked.connect(self.select_word)
        
        learned_list_layout.addWidget(learned_list_label)
        learned_list_layout.addWidget(self.learned_list)
        
        # Add lists to right layout
        right_layout.addWidget(learning_list_group)
        right_layout.addWidget(learned_list_group)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set splitter sizes
        splitter.setSizes([1, 1])
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        
        # Update lists
        self.update_lists()

    def load_vocabulary(self):
        os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists
        loaded_data = None
        try:
            if os.path.exists(self.vocab_file):
                with open(self.vocab_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
            
            # Check if loaded data is a list (new format)
            if isinstance(loaded_data, list):
                # Validate items in the list (simple check)
                self.vocabulary = [
                    item for item in loaded_data 
                    if isinstance(item, dict) and 'word' in item and 'meaning' in item
                ]
                if len(self.vocabulary) != len(loaded_data):
                     self.add_debug_message("Warning: Some invalid items removed from vocabulary.json")
            else:
                # If it's not a list (old format or corrupt), start fresh
                self.add_debug_message("vocabulary.json is not in the expected list format. Starting fresh.")
                self.vocabulary = []

        except json.JSONDecodeError:
            self.add_debug_message(f"Error reading {self.vocab_file}. Starting with empty list.")
            self.vocabulary = []
        except Exception as e:
            self.add_debug_message(f"Error loading vocabulary: {e}")
            QMessageBox.warning(self, "Load Error", f"Could not load vocabulary: {e}")
            self.vocabulary = [] # Fallback to empty list
            
        # Ensure self.vocabulary is always a list before proceeding
        if not isinstance(self.vocabulary, list):
             self.add_debug_message("Critical error: self.vocabulary is not a list after loading attempt. Resetting.")
             self.vocabulary = []
             
        self.current_index = -1 # Reset index after loading
        self.update_lists() # Use update_lists which now calls update_word_count
        self.show_next_word()

    def save_vocabulary(self):
        # Ensure we are saving a list
        if not isinstance(self.vocabulary, list):
            self.add_debug_message("Error: Attempting to save vocabulary but data is not a list. Aborting save.")
            QMessageBox.critical(self, "Save Error", "Internal data error: Vocabulary data is not a list.")
            return
            
        try:
            os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists
            with open(self.vocab_file, 'w', encoding='utf-8') as f:
                # Save the list directly
                json.dump(self.vocabulary, f, indent=4) 
        except IOError as e:
            self.add_debug_message(f"Error saving vocabulary: {e}")
            QMessageBox.critical(self, "Save Error", f"Could not save vocabulary: {e}")
            if self.parent:
                self.parent.statusBar().showMessage(f"Error saving vocabulary: {e}", 5000)
        except Exception as e:
            self.add_debug_message(f"Unexpected error saving vocabulary: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred while saving vocabulary: {e}")

    def add_word(self):
        word = self.word_input.text().strip()
        meaning = self.meaning_input.toPlainText().strip()
        
        if not word or not meaning:
            QMessageBox.warning(self, "Error", "Please enter both word and meaning")
            return
        
        # Check for duplicates
        for item in self.vocabulary:
            if isinstance(item, dict) and item.get('word', '').lower() == word.lower():
                QMessageBox.warning(self, "Duplicate Word", f"The word '{word}' already exists.")
                return
        
        # Add new word dictionary to the list
        self.vocabulary.append({
            "word": word,
            "meaning": meaning,
            "attempts": 0,
            "successes": 0
        })
        
        self.save_vocabulary() # Save the updated list
        self.update_lists() # Update UI lists
        
        # Clear inputs
        self.word_input.clear()
        self.meaning_input.clear()
        
        if self.parent:
            self.parent.statusBar().showMessage(f"Added word: {word}")
        
        # Show the newly added word for learning if it's the only one
        if len(self.vocabulary) == 1:
            self.current_index = -1 # Will become 0 in show_next_word
            self.show_next_word()

    def update_lists(self):
        # Clear lists
        self.learning_list.clear()
        self.learned_list.clear()
        
        # Separate words into learning/learned based on success count
        learning_words = []
        learned_words = []
        for word_data in self.vocabulary:
            if isinstance(word_data, dict) and word_data.get('successes', 0) >= 3:
                learned_words.append(word_data['word'])
            elif isinstance(word_data, dict):
                learning_words.append(word_data['word'])
            else:
                self.add_debug_message(f"Warning: Invalid item in vocabulary data: {word_data}")
        
        # Populate lists
        self.learning_list.addItems(learning_words)
        self.learned_list.addItems(learned_words)
        self.update_word_count() # Update counts after populating

    def select_word(self, item):
        word_text = item.text()
        found_index = -1
        is_learned = False
        
        # Find the dictionary corresponding to the clicked word text
        for index, word_data in enumerate(self.vocabulary):
            if isinstance(word_data, dict) and word_data.get('word') == word_text:
                found_index = index
                is_learned = word_data.get('successes', 0) >= 3
                break
                
        if found_index != -1:
            self.current_index = found_index
            word_data = self.vocabulary[self.current_index]
            
            if is_learned:
                # Show learned word directly
                self.word_display.setText(word_data['word'])
                self.meaning_display.setText(word_data.get('meaning', ''))
                self.attempt_input.setEnabled(False)
                self.attempt_input.clear()
            else:
                # Show asterisks for word being learned
                self.word_display.setText("*" * len(word_data['word']))
                self.meaning_display.setText(word_data.get('meaning', ''))
                self.attempt_input.setEnabled(True)
                self.attempt_input.clear() # Clear previous attempt
                self.attempt_input.setFocus()
                
            self.update_stats()
        else:
            self.add_debug_message(f"Error: Could not find data for selected word '{word_text}'")

    def check_attempt(self):
        # Ensure a valid word is selected and it's not already learned
        if self.current_index < 0 or self.current_index >= len(self.vocabulary):
            self.add_debug_message("Check attempt called with invalid index.")
            return
            
        word_data = self.vocabulary[self.current_index]
        if not isinstance(word_data, dict) or word_data.get('successes', 0) >= 3:
            self.add_debug_message("Check attempt called for a learned word or invalid data.")
            return
        
        attempt = self.attempt_input.text().strip()
        if not attempt:
            return
        
        word_data["attempts"] = word_data.get("attempts", 0) + 1
        correct_word = word_data.get('word', '')
        
        if attempt.lower() == correct_word.lower():
            word_data["successes"] = word_data.get("successes", 0) + 1
            self.attempt_input.clear()
            
            if word_data["successes"] >= 3:
                QMessageBox.information(self, "Success", 
                    f"Congratulations! You've learned '{correct_word}'!")
                # Word automatically moves to learned list on next update_lists call
                # Move to next word automatically or allow user selection?
                # For now, just update lists and show next unlearned word
                self.update_lists() 
                self.show_next_unlearned_word() 
            else:
                needed = 3 - word_data["successes"]
                QMessageBox.information(self, "Success", 
                    f"Correct! {needed} more correct attempt(s) needed.")
                # Potentially show next word after correct attempt?
                # For now, just update stats and wait for next attempt/selection
                self.update_stats()
        else:
            QMessageBox.warning(self, "Incorrect", 
                f"Try again! The correct spelling is '{correct_word}'")
            # Keep focus on input for another try
            self.attempt_input.setFocus()
            self.attempt_input.selectAll()
        
        self.save_vocabulary()
        # Update lists might be redundant if done after success/failure msg
        # self.update_lists() 
        self.update_stats()

    def update_stats(self):
        if self.current_index < 0 or self.current_index >= len(self.vocabulary):
            self.stats_label.setText("")
            return
        
        word_data = self.vocabulary[self.current_index]
        if isinstance(word_data, dict):
            attempts = word_data.get('attempts', 0)
            successes = word_data.get('successes', 0)
            
            if successes >= 3:
                 # Calculate success rate for learned words
                 success_rate = (successes / attempts * 100) if attempts > 0 else 0
                 self.stats_label.setText(
                    f"Learned! | Total Attempts: {attempts} | "
                    f"Success Rate: {success_rate:.1f}%"
                 ) 
            else:
                self.stats_label.setText(
                    f"Attempts: {attempts} | "
                    f"Successes: {successes}/3"
                )
        else:
            self.stats_label.setText("Invalid data")

    def show_next_word(self):
        """Shows the next word in the sequence, regardless of learned status."""
        if not self.vocabulary:
            self.word_display.setText("No words added")
            self.meaning_display.setText("")
            self.attempt_input.setEnabled(False)
            self.attempt_input.clear()
            self.stats_label.setText("")
            self.current_index = -1
            return

        # Cycle through the index
        self.current_index = (self.current_index + 1) % len(self.vocabulary)
        word_data = self.vocabulary[self.current_index]

        # Check if word_data is valid
        if isinstance(word_data, dict) and 'word' in word_data:
            word_text = word_data['word']
            meaning_text = word_data.get('meaning', '')
            is_learned = word_data.get('successes', 0) >= 3

            if is_learned:
                self.word_display.setText(word_text)
                self.meaning_display.setText(meaning_text)
                self.attempt_input.setEnabled(False)
                self.attempt_input.clear()
            else:
                self.word_display.setText("*" * len(word_text))
                self.meaning_display.setText(meaning_text)
                self.attempt_input.setEnabled(True)
                self.attempt_input.clear()
                self.attempt_input.setFocus()
                
            self.update_stats()
        else:
            # Handle invalid data - show error, skip to next?
            self.add_debug_message(f"Invalid vocabulary data at index {self.current_index}: {word_data}")
            self.word_display.setText("[Invalid Data]")
            self.meaning_display.setText("")
            self.attempt_input.setEnabled(False)
            self.attempt_input.clear()
            self.stats_label.setText("Error")
            # Optionally try showing the *next* one immediately
            # self.show_next_word() 

    def show_next_unlearned_word(self):
        """Finds and displays the next word with successes < 3."""
        if not self.vocabulary:
            self.show_next_word() # Show "No words added" message
            return

        start_index = (self.current_index + 1) % len(self.vocabulary)
        idx = start_index

        while True:
            word_data = self.vocabulary[idx]
            if isinstance(word_data, dict) and word_data.get('successes', 0) < 3:
                # Found an unlearned word
                self.current_index = idx
                self.word_display.setText("*" * len(word_data['word']))
                self.meaning_display.setText(word_data.get('meaning', ''))
                self.attempt_input.setEnabled(True)
                self.attempt_input.clear()
                self.attempt_input.setFocus()
                self.update_stats()
                return # Exit after showing the word
            
            # Move to next index and wrap around
            idx = (idx + 1) % len(self.vocabulary)
            # If we wrapped around back to the start, all words are learned
            if idx == start_index:
                QMessageBox.information(self, "All Learned!", "Congratulations! You have learned all the words.")
                self.current_index = -1 # Reset index
                self.word_display.setText("All words learned!")
                self.meaning_display.setText("")
                self.attempt_input.setEnabled(False)
                self.attempt_input.clear()
                self.stats_label.setText("")
                return

    def update_word_count(self):
        learning_count = sum(1 for word_data in self.vocabulary if isinstance(word_data, dict) and word_data.get('successes', 0) < 3)
        learned_count = sum(1 for word_data in self.vocabulary if isinstance(word_data, dict) and word_data.get('successes', 0) >= 3)
        
        # Clear and add items to provide counts, not the words themselves
        self.learning_list.clear()
        self.learning_list.addItem(f"Words to Learn ({learning_count})") 
        # You might want to populate the list with actual words here instead if needed for selection
        # for word_data in self.vocabulary:
        #     if isinstance(word_data, dict) and word_data.get('successes', 0) < 3:
        #         self.learning_list.addItem(word_data['word'])
        
        self.learned_list.clear()
        self.learned_list.addItem(f"Learned Words ({learned_count})")
        # for word_data in self.vocabulary:
        #     if isinstance(word_data, dict) and word_data.get('successes', 0) >= 3:
        #         self.learned_list.addItem(word_data['word'])


    def show_definition(self):
        # This method seems redundant now, select_word handles showing details
        # If intended to reveal the current word being learned:
        if self.current_index >= 0 and self.current_index < len(self.vocabulary):
             word_data = self.vocabulary[self.current_index]
             if isinstance(word_data, dict) and 'word' in word_data:
                 self.word_display.setText(word_data['word']) # Reveal word
                 self.attempt_input.setEnabled(False) # Disable attempts after revealing
                 self.add_debug_message(f"Revealed word: {word_data['word']}")
             else:
                self.add_debug_message("Cannot reveal: No word selected.")
        else:
            self.add_debug_message("Cannot reveal: No word selected.") 

    def add_debug_message(self, message):
        """Placeholder for debug messages. Currently prints to console."""
        # In a more integrated app, this might emit a signal
        # or log to a file or central logging widget.
        timestamp = time.strftime("%H:%M:%S")
        print(f"[VocabLearner DEBUG {timestamp}] {message}") 