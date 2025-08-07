from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt

class ScriptPromptPage(QWidget):
    """
    A widget page with three resizable text panels for script writing and prompt generation.
    """
    def __init__(self, parent=None):
        super(ScriptPromptPage, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface components and layout.
        """
        # Overall layout for the widget
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Use full space

        # Horizontal splitter for the three panels
        splitter = QSplitter(Qt.Horizontal)

        # 1. Script Panel
        self.script_panel = QTextEdit()
        self.script_panel.setPlaceholderText("SCRIPT")

        # 2. Image Generation Prompt Panel
        self.image_gen_prompt_panel = QTextEdit()
        self.image_gen_prompt_panel.setPlaceholderText("PROMPT FOR IMAGE GENERATION")

        # 3. Image to Video Prompt Panel
        self.image_to_video_prompt_panel = QTextEdit()
        self.image_to_video_prompt_panel.setPlaceholderText("PROMPT FOR IMAGE TO VIDEO ANIMATION")

        # Add panels to the splitter
        splitter.addWidget(self.script_panel)
        splitter.addWidget(self.image_gen_prompt_panel)
        splitter.addWidget(self.image_to_video_prompt_panel)

        # Set stretch factors for resizability (equal stretching initially)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)

        # Add the splitter to the main layout
        layout.addWidget(splitter)

        # Set the layout for the ScriptPromptPage widget
        self.setLayout(layout) 