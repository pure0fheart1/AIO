import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QPushButton, QFileDialog, QMessageBox,
                           QTabWidget, QSplitter, QLineEdit, QComboBox,
                           QCheckBox, QToolBar, QAction, QMenu, QDialog,
                           QGridLayout, QFormLayout, QApplication, QShortcut,
                           QFrame, QSizePolicy, QStatusBar)
from PyQt5.QtGui import (QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
                       QTextCursor, QKeySequence, QIcon, QPalette, QTextDocument, QPainter)
from PyQt5.QtCore import Qt, QRegExp, QSize, pyqtSignal, QTimer

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setTabStopWidth(4 * self.fontMetrics().width(' '))
        
        self.line_number_area = LineNumberArea(self)
        
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.document().contentsChanged.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Set a monospace font
        font = QFont("Courier New", 10)
        self.setFont(font)
        
        # Current file path
        self.current_file_path = None
        
        # Set dark theme colors
        self.apply_editor_style()
        
    def apply_editor_style(self):
        # Editor background and text colors
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #e6e6e6;
                border: 1px solid #3c3c3c;
            }
        """)
        
    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.document().blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
            
        space = 3 + self.fontMetrics().width('9') * digits
        return space
    
    def update_line_number_area_width(self, newBlockCount):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def update_line_number_area(self):
        rect = self.contentsRect()
        self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        
    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2b2b2b")) # Background color

        block = self.document().begin()
        block_number = block.blockNumber()
        # Calculate the top position relative to the viewport
        viewport_top = self.verticalScrollBar().value()
        viewport_bottom = viewport_top + self.viewport().height()

        # Iterate over blocks
        while block.isValid():
            block_pos = self.document().documentLayout().blockBoundingRect(block).topLeft()
            block_height = self.document().documentLayout().blockBoundingRect(block).height()

            # Check if the block is visible within the current viewport area being painted
            if block_pos.y() + block_height >= viewport_top and block_pos.y() <= viewport_bottom:
                # Calculate the y-coordinate to draw the line number within the line number area
                # This coordinate is relative to the line number area widget itself
                paint_y = self.document().documentLayout().blockBoundingRect(block).translated(0, -viewport_top).top()

                # Only draw if the paint_y is within the event's repaint rectangle
                if paint_y >= event.rect().top() and paint_y <= event.rect().bottom():
                    number = str(block_number + 1)
                    painter.setPen(QColor("#7a7a7a")) # Line number color
                    # Use the calculated paint_y for drawing
                    painter.drawText(0, int(paint_y), self.line_number_area.width() - 3, int(block_height),
                                     Qt.AlignRight | Qt.AlignTop, number) # Align top for better consistency

            # Stop if the block is entirely below the viewport
            if block_pos.y() > viewport_bottom:
                break

            block = block.next()
            block_number += 1
        
    def highlight_current_line(self):
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            line_color = QColor("#323232")
            
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)
        
    def keyPressEvent(self, event):
        # Auto-indent: when Enter is pressed, copy the indentation of the current line
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            
            # Extract indentation
            indentation = ""
            for char in text:
                if char.isspace():
                    indentation += char
                else:
                    break
                    
            # Insert new line with the same indentation
            super().keyPressEvent(event)
            self.insertPlainText(indentation)
            return
            
        # Handle tab key
        if event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                # Indent selection
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                
                # Get selected text
                selected_text = cursor.selectedText()
                
                # Add tabs to the beginning of each line
                new_text = ""
                for line in selected_text.split("\u2029"):  # Unicode char for line separator
                    new_text += "    " + line + "\n"
                    
                new_text = new_text[:-1]  # Remove the last newline
                
                cursor.removeSelectedText()
                cursor.insertText(new_text)
            else:
                # Just insert spaces
                self.insertPlainText("    ")
            return
            
        super().keyPressEvent(event)


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]
        
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            self.highlighting_rules.append((pattern, keyword_format))
            
        # Class names
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))
        class_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegExp("\\bclass\\b\\s*(\\w+)"), class_format))
        
        # Function names
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegExp("\\bdef\\b\\s*(\\w+)"), function_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("'.*'"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.highlighting_rules.append((QRegExp("#[^\n]*"), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\b"), number_format))
        
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class JavaScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "break", "case", "catch", "class", "const", "continue", "debugger",
            "default", "delete", "do", "else", "export", "extends", "false",
            "finally", "for", "function", "if", "import", "in", "instanceof",
            "new", "null", "return", "super", "switch", "this", "throw",
            "true", "try", "typeof", "var", "void", "while", "with", "let", "async", "await"
        ]
        
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            self.highlighting_rules.append((pattern, keyword_format))
            
        # Class and function names
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))
        class_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegExp("\\bclass\\b\\s*(\\w+)"), class_format))
        
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegExp("\\bfunction\\b\\s*(\\w+)"), function_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("'.*'"), string_format))
        self.highlighting_rules.append((QRegExp("`.*`"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.highlighting_rules.append((QRegExp("//[^\n]*"), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\b"), number_format))
        
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class HTMLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        
        self.highlighting_rules = []
        
        # Tags
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569cd6"))
        tag_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegExp("<\\/?[a-zA-Z0-9]+"), tag_format))
        self.highlighting_rules.append((QRegExp("\\/>"), tag_format))
        self.highlighting_rules.append((QRegExp(">"), tag_format))
        
        # Attributes
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append((QRegExp("\\b[a-zA-Z0-9_]+="), attribute_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("'.*'"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.highlighting_rules.append((QRegExp("<!--.*-->"), comment_format))
        
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class FindReplaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Find & Replace")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QGridLayout()
        
        # Find
        find_label = QLabel("Find:")
        self.find_input = QLineEdit()
        
        # Replace
        replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit()
        
        # Options
        self.case_sensitive = QCheckBox("Case sensitive")
        self.whole_word = QCheckBox("Whole word")
        
        # Buttons
        self.find_button = QPushButton("Find Next")
        self.find_button.clicked.connect(self.find_next)
        
        self.replace_button = QPushButton("Replace")
        self.replace_button.clicked.connect(self.replace)
        
        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.clicked.connect(self.replace_all)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        # Add widgets to layout
        layout.addWidget(find_label, 0, 0)
        layout.addWidget(self.find_input, 0, 1, 1, 3)
        
        layout.addWidget(replace_label, 1, 0)
        layout.addWidget(self.replace_input, 1, 1, 1, 3)
        
        layout.addWidget(self.case_sensitive, 2, 0, 1, 2)
        layout.addWidget(self.whole_word, 2, 2, 1, 2)
        
        layout.addWidget(self.find_button, 3, 0)
        layout.addWidget(self.replace_button, 3, 1)
        layout.addWidget(self.replace_all_button, 3, 2)
        layout.addWidget(self.close_button, 3, 3)
        
        self.setLayout(layout)
        
    def find_next(self):
        if not self.parent or not hasattr(self.parent, 'current_editor'):
            return
            
        editor = self.parent.current_editor
        text = self.find_input.text()
        
        if not text:
            return
            
        # Get options
        case_sensitive = self.case_sensitive.isChecked()
        whole_word = self.whole_word.isChecked()
        
        # Set search flags
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
            
        # Search for text
        cursor = editor.textCursor()
        if not editor.find(text, flags):
            # If not found from current position, try from beginning
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)
            if not editor.find(text, flags):
                QMessageBox.information(self, "Find", f"Cannot find '{text}'")
                
    def replace(self):
        if not self.parent or not hasattr(self.parent, 'current_editor'):
            return
            
        editor = self.parent.current_editor
        cursor = editor.textCursor()
        
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            
        self.find_next()
        
    def replace_all(self):
        if not self.parent or not hasattr(self.parent, 'current_editor'):
            return
            
        editor = self.parent.current_editor
        text = self.find_input.text()
        replacement = self.replace_input.text()
        
        if not text:
            return
            
        # Save current cursor
        old_cursor = editor.textCursor()
        
        # Start from the beginning
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        editor.setTextCursor(cursor)
        
        # Get options
        case_sensitive = self.case_sensitive.isChecked()
        whole_word = self.whole_word.isChecked()
        
        # Set search flags
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
            
        # Count replacements
        count = 0
        
        # Start an edit block to make it a single undo operation
        editor.document().beginEditBlock()
        
        while True:
            if not editor.find(text, flags):
                break
                
            # Replace text
            cursor = editor.textCursor()
            cursor.insertText(replacement)
            count += 1
            
        editor.document().endEditBlock()
        
        # Restore cursor
        editor.setTextCursor(old_cursor)
        
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrences")


class EditorTab(QWidget):
    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.parent = parent
        self.file_path = file_path
        self.is_modified = False
        self.highlighter = None
        self.setup_ui()
        
        if file_path and os.path.exists(file_path):
            self.load_file(file_path)
            
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Editor
        self.editor = CodeEditor(self)
        self.editor.textChanged.connect(self.on_text_changed)
        
        # Add editor to layout
        layout.addWidget(self.editor)
        
        self.setLayout(layout)
        
    def on_text_changed(self):
        if not self.is_modified:
            self.is_modified = True
            # Update tab title to indicate modification
            self.parent.update_tab_title(self)
        
    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            self.file_path = file_path
            self.editor.setPlainText(content)
            self.is_modified = False
            
            # Apply syntax highlighter based on file extension
            self.apply_highlighter()
            
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")
            return False
            
    def save_file(self, file_path=None):
        path = file_path if file_path else self.file_path
        
        if not path:
            return self.save_file_as()
            
        try:
            with open(path, 'w') as f:
                f.write(self.editor.toPlainText())
                
            self.file_path = path
            self.is_modified = False
            
            # Update tab title
            self.parent.update_tab_title(self)
            
            # Apply syntax highlighter based on saved file extension
            self.apply_highlighter()
            
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
            return False
            
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", "", 
            "Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;HTML Files (*.html);;All Files (*)"
        )
        
        if file_path:
            return self.save_file(file_path)
        return False
        
    def apply_highlighter(self):
        if self.highlighter:
            self.highlighter.setDocument(None)
            self.highlighter = None
            
        if self.file_path:
            ext = os.path.splitext(self.file_path)[1].lower()
            
            if ext == '.py':
                self.highlighter = PythonHighlighter(self.editor.document())
            elif ext in ['.js', '.jsx']:
                self.highlighter = JavaScriptHighlighter(self.editor.document())
            elif ext in ['.html', '.htm', '.xml']:
                self.highlighter = HTMLHighlighter(self.editor.document())


class TextEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tabs = []
        self.current_editor = None
        self.find_replace_dialog = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # New file action
        self.new_action = QAction("New", self)
        self.new_action.triggered.connect(self.new_file)
        toolbar.addAction(self.new_action)
        
        # Open file action
        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.open_file)
        toolbar.addAction(self.open_action)
        
        # Save action
        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save_file)
        toolbar.addAction(self.save_action)
        
        # Save As action
        self.save_as_action = QAction("Save As", self)
        self.save_as_action.triggered.connect(self.save_file_as)
        toolbar.addAction(self.save_as_action)
        
        toolbar.addSeparator()
        
        # Cut action
        self.cut_action = QAction("Cut", self)
        self.cut_action.triggered.connect(self.cut)
        toolbar.addAction(self.cut_action)
        
        # Copy action
        self.copy_action = QAction("Copy", self)
        self.copy_action.triggered.connect(self.copy)
        toolbar.addAction(self.copy_action)
        
        # Paste action
        self.paste_action = QAction("Paste", self)
        self.paste_action.triggered.connect(self.paste)
        toolbar.addAction(self.paste_action)
        
        toolbar.addSeparator()
        
        # Find & Replace action
        self.find_action = QAction("Find", self)
        self.find_action.triggered.connect(self.show_find_replace)
        toolbar.addAction(self.find_action)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Plain Text", "Python", "JavaScript", "HTML"])
        self.language_combo.currentIndexChanged.connect(self.change_language)
        toolbar.addWidget(QLabel("  Syntax: "))
        toolbar.addWidget(self.language_combo)
        
        # Add toolbar to layout
        layout.addWidget(toolbar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.cursor_position_label = QLabel("Line: 1, Column: 1")
        self.status_bar.addPermanentWidget(self.cursor_position_label)
        layout.addWidget(self.status_bar)
        
        self.setLayout(layout)
        
        # Create initial tab
        self.new_file()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        # New file: Ctrl+N
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self.new_file)
        
        # Open file: Ctrl+O
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.open_file)
        
        # Save file: Ctrl+S
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_file)
        
        # Save As: Ctrl+Shift+S
        save_as_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        save_as_shortcut.activated.connect(self.save_file_as)
        
        # Find: Ctrl+F
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_replace)
        
        # Close tab: Ctrl+W
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        
    def new_file(self):
        tab = EditorTab(self)
        self.tabs.append(tab)
        index = self.tab_widget.addTab(tab, "Untitled")
        self.tab_widget.setCurrentIndex(index)
        self.update_ui_state()
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", 
            "Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;HTML Files (*.html);;All Files (*)"
        )
        
        if file_path:
            # Check if file is already open
            for i, tab in enumerate(self.tabs):
                if tab.file_path == file_path:
                    self.tab_widget.setCurrentIndex(i)
                    return
                    
            # Open new tab with file
            tab = EditorTab(self, file_path)
            self.tabs.append(tab)
            file_name = os.path.basename(file_path)
            index = self.tab_widget.addTab(tab, file_name)
            self.tab_widget.setCurrentIndex(index)
            self.update_ui_state()
            
    def save_file(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            current_tab = self.tabs[current_index]
            
            if current_tab.file_path:
                current_tab.save_file()
            else:
                self.save_file_as()
                
    def save_file_as(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            current_tab = self.tabs[current_index]
            saved = current_tab.save_file_as()
            
            if saved and current_tab.file_path:
                file_name = os.path.basename(current_tab.file_path)
                self.tab_widget.setTabText(current_index, file_name)
                
    def close_tab(self, index):
        if index < 0 or index >= len(self.tabs):
            return
            
        tab = self.tabs[index]
        
        if tab.is_modified:
            reply = QMessageBox.question(
                self, "Save Changes", 
                "Do you want to save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if not tab.save_file():
                    # If save failed, don't close the tab
                    return
            elif reply == QMessageBox.Cancel:
                return
                
        # Remove and delete the tab
        self.tab_widget.removeTab(index)
        self.tabs.pop(index)
        
        # Create a new tab if all tabs are closed
        if self.tab_widget.count() == 0:
            self.new_file()
            
    def on_tab_changed(self, index):
        if index >= 0 and index < len(self.tabs):
            self.current_editor = self.tabs[index].editor
            
            # Update language selection
            if self.tabs[index].file_path:
                ext = os.path.splitext(self.tabs[index].file_path)[1].lower()
                
                if ext == '.py':
                    self.language_combo.setCurrentText("Python")
                elif ext in ['.js', '.jsx']:
                    self.language_combo.setCurrentText("JavaScript")
                elif ext in ['.html', '.htm', '.xml']:
                    self.language_combo.setCurrentText("HTML")
                else:
                    self.language_combo.setCurrentText("Plain Text")
                    
            # Connect cursor position signal
            self.current_editor.cursorPositionChanged.connect(self.update_cursor_position)
            self.update_cursor_position()
        else:
            self.current_editor = None
            
    def update_cursor_position(self):
        if self.current_editor:
            cursor = self.current_editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self.cursor_position_label.setText(f"Line: {line}, Column: {column}")
            
    def update_tab_title(self, tab):
        for i, t in enumerate(self.tabs):
            if t == tab:
                title = os.path.basename(tab.file_path) if tab.file_path else "Untitled"
                if tab.is_modified:
                    title += " *"  # Add asterisk to indicate unsaved changes
                self.tab_widget.setTabText(i, title)
                break
                
    def update_ui_state(self):
        has_tabs = len(self.tabs) > 0
        
        self.save_action.setEnabled(has_tabs)
        self.save_as_action.setEnabled(has_tabs)
        self.cut_action.setEnabled(has_tabs)
        self.copy_action.setEnabled(has_tabs)
        self.paste_action.setEnabled(has_tabs)
        self.find_action.setEnabled(has_tabs)
        
    def cut(self):
        if self.current_editor:
            self.current_editor.cut()
            
    def copy(self):
        if self.current_editor:
            self.current_editor.copy()
            
    def paste(self):
        if self.current_editor:
            self.current_editor.paste()
            
    def show_find_replace(self):
        if not self.current_editor:
            return
            
        if not self.find_replace_dialog:
            self.find_replace_dialog = FindReplaceDialog(self)
            
        self.find_replace_dialog.show()
        self.find_replace_dialog.raise_()
        self.find_replace_dialog.activateWindow()
        
        # Pre-fill with selected text if any
        if self.current_editor.textCursor().hasSelection():
            selected_text = self.current_editor.textCursor().selectedText()
            self.find_replace_dialog.find_input.setText(selected_text)
            
    def change_language(self, index):
        if not self.current_editor or index < 0:
            return
            
        current_tab_index = self.tab_widget.currentIndex()
        current_tab = self.tabs[current_tab_index]
        
        # Remove existing highlighter
        if current_tab.highlighter:
            current_tab.highlighter.setDocument(None)
            current_tab.highlighter = None
            
        # Apply new highlighter
        language = self.language_combo.currentText()
        
        if language == "Python":
            current_tab.highlighter = PythonHighlighter(current_tab.editor.document())
        elif language == "JavaScript":
            current_tab.highlighter = JavaScriptHighlighter(current_tab.editor.document())
        elif language == "HTML":
            current_tab.highlighter = HTMLHighlighter(current_tab.editor.document())

# For standalone testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec_()) 