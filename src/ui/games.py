import os
import sys
import random # Import random for AI (placeholder)
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, QSizePolicy, QTabWidget, QMessageBox,
    QDialog, QComboBox, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, 
    QSpacerItem, QGroupBox, QFormLayout, QApplication # Added QRadioButton, QButtonGroup, QSpacerItem, QGroupBox, QFormLayout, QApplication
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont

# --- Import Tetris Game --- #
from games.tetris import TetrisGame, STATE_HOME # Assuming tetris.py is in a 'games' subdirectory relative to this file or in sys.path
# --- Import Space Invaders Game --- #
from games.space_invaders import SpaceInvadersGame
# --- Import Snake Game --- #
from games.snake import SnakeGame, STATE_HOME as SNAKE_STATE_HOME
# --- Import Solitaire Game --- #
from games.solitaire import SolitaireGame, SOLITAIRE_STATE_HOME # Assuming solitaire.py is in games subdirectory

# --- Try importing python-chess --- #
try:
    import chess
    import chess.engine
    CHESS_AVAILABLE = True
except ImportError:
    CHESS_AVAILABLE = False
    # Define dummy classes/variables if chess is not installed
    # This allows the rest of the UI to load without crashing
    class chess:
        Board = lambda: None
        WHITE = True
        BLACK = False
        PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(1, 7)
        SQUARES = range(64)
        square_name = lambda i: "a1"
        Move = lambda from_sq, to_sq: None
        engine = None # Will prevent AI logic from running

# Define the path to the Stockfish engine executable
# User might need to change this depending on their system and where they place Stockfish
# We can make this configurable later in settings.
STOCKFISH_PATH = r"C:\Users\jamie\Desktop\stockfish-windows-x86-64-avx2\stockfish-windows-x86-64-avx2.exe"
# STOCKFISH_PATH = "/usr/games/stockfish" # Example path for Linux
# STOCKFISH_PATH = "/opt/homebrew/bin/stockfish" # Example path for macOS (Homebrew)

# Game States for Chess
CHESS_STATE_HOME = 0
CHESS_STATE_PLAYING = 1
CHESS_STATE_GAME_OVER = 2 # Can be Checkmate or Draw

class GamesManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        
        # Header with title and description
        header_layout = QVBoxLayout()
        title_label = QLabel("Games")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        description_label = QLabel(
            "Take a break and enjoy some classic games. "
            "Challenge yourself or play against a friend."
        )
        description_label.setWordWrap(True)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(description_label)
        
        # Games tab widget
        self.games_tabs = QTabWidget()
        
        # Add chess game
        if CHESS_AVAILABLE:
            self.chess_game = ChessGame(self)
            self.games_tabs.addTab(self.chess_game, "Chess")
        else:
            chess_unavailable_label = QLabel("Chess game requires the 'python-chess' library to be installed.\nPlease install it (pip install python-chess) and ensure Stockfish engine is accessible.")
            chess_unavailable_label.setAlignment(Qt.AlignCenter)
            chess_unavailable_label.setWordWrap(True)
            self.games_tabs.addTab(chess_unavailable_label, "Chess")
            self.games_tabs.setTabEnabled(self.games_tabs.count() - 1, False)
        
        # --- Add Tetris Game --- #
        self.tetris_game = TetrisGame(self)
        self.games_tabs.addTab(self.tetris_game, "Tetris")
        # Connect a signal to start Tetris when its tab is selected
        self.games_tabs.currentChanged.connect(self.handle_tab_changed)
        
        # --- Add Space Invaders Game --- # 
        self.space_invaders_game = SpaceInvadersGame(self)
        self.games_tabs.addTab(self.space_invaders_game, "Space Invaders")
        
        # --- Add Snake Game --- #
        self.snake_game = SnakeGame(self)
        self.games_tabs.addTab(self.snake_game, "Snake")
        
        # --- Add Solitaire Game --- #
        self.solitaire_game = SolitaireGame(self)
        self.games_tabs.addTab(self.solitaire_game, "Solitaire")
        
        # Add more games here in the future
        
        # Add everything to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.games_tabs)
        
        self.setLayout(layout)

    def handle_tab_changed(self, index):
        current_widget = self.games_tabs.widget(index)
        if isinstance(current_widget, TetrisGame):
            # Ensure the game has focus to receive key presses
            current_widget.setFocus()
            # Optionally, auto-start the game if it's not already started
            # or provide a start button within the TetrisGame widget itself.
            # For now, just focusing. The user can press 'S' to start as per TetrisGame.keyPressEvent
            if current_widget.game_state == STATE_HOME:
                # To make it user-friendly, we can call start() or inform the user.
                # Let's try to start it if it makes sense, or it could be confusing.
                # current_widget.start() # Auto-start might not be desired if they switch back and forth
                pass # User presses 'S' to start
        elif isinstance(current_widget, ChessGame):
             current_widget.update_board_display() # Refresh chess board if switched to
        elif isinstance(current_widget, SpaceInvadersGame):
            current_widget.setFocus() # Ensure focus for key presses
            # Similar to Tetris, user presses 'S' to start Space Invaders
            # Game state is managed internally by SpaceInvadersGame including initial message
            pass
        elif isinstance(current_widget, SnakeGame):
            current_widget.setFocus()
            if current_widget.game_state == SNAKE_STATE_HOME:
                pass # User presses 'S' to start
        elif isinstance(current_widget, SolitaireGame):
            current_widget.setFocus()
            if current_widget.game_state == SOLITAIRE_STATE_HOME:
                pass # User presses 'S' to start

class ChessGame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Game state using python-chess
        self.board = chess.Board()
        self.current_player_is_human = True # Assume human starts as white initially
        self.ai_player_active = False # Flag if AI opponent is active
        self.human_player_color = chess.WHITE # Player is initially White
        self.ai_skill_level = 8 # Default Standard (0-20 for Stockfish)
        self.ai_think_time = 0.5 # Default Standard
        
        self.selected_square = None # Store the selected square index (0-63)
        self.valid_moves = [] # Store valid chess.Move objects
        self.last_move_ai = None # Store the last AI move for undo purposes
        
        self.game_state = CHESS_STATE_HOME # Initialize game state
        
        # AI Engine
        self.engine = None
        self._init_stockfish()

        # Load piece images (map python-chess pieces to display text)
        self.piece_images = self.load_piece_images()
        
        self.setup_ui()
        self.update_board_display()
        
    def _init_stockfish(self):
        if not CHESS_AVAILABLE or self.engine:
            return
        try:
            # Check if the specified Stockfish path exists and is executable
            if os.path.exists(STOCKFISH_PATH) and os.access(STOCKFISH_PATH, os.X_OK):
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
                print("Stockfish engine initialized successfully.")
                # Optionally: Configure initial engine parameters if needed
                # self.engine.configure({"Skill Level": self.ai_skill_level}) 
            else:
                print(f"Stockfish engine not found or not executable at: {STOCKFISH_PATH}")
                QMessageBox.warning(self, "Stockfish Error",
                                  f"Stockfish engine not found or not executable at the specified path:\n{STOCKFISH_PATH}\n\nAI opponent will be disabled. Please install Stockfish and configure the path if needed.")
                if hasattr(self, 'opponent_combo'): # Check if UI is built
                    self.opponent_combo.setEnabled(False)
                    self.difficulty_combo.setEnabled(False)
        except Exception as e:
            print(f"Error initializing Stockfish engine: {e}")
            QMessageBox.critical(self, "Stockfish Error", f"Failed to initialize Stockfish engine: {e}")
            # Optionally disable AI controls
            if hasattr(self, 'opponent_combo'):
                 self.opponent_combo.setEnabled(False)
                 self.difficulty_combo.setEnabled(False)

    def setup_ui(self):
        # Main layout (Horizontal: Options | Board + Info)
        main_layout = QHBoxLayout(self)

        # --- Left side: Options --- #
        options_layout = QVBoxLayout()
        options_group = QGroupBox("Game Options")
        options_form_layout = QFormLayout() # Use QFormLayout for labels+controls

        # Opponent Selection
        self.opponent_combo = QComboBox()
        self.opponent_combo.addItems(["Human", "AI Computer"])
        self.opponent_combo.currentIndexChanged.connect(self.on_opponent_changed)
        # Disable AI if engine failed to load
        if not self.engine:
            self.opponent_combo.model().item(1).setEnabled(False)
            self.opponent_combo.setToolTip("AI requires a functional Stockfish engine.")
        options_form_layout.addRow("Opponent:", self.opponent_combo)
        options_group.setLayout(options_form_layout)

        # Player Color Selection (only relevant for AI opponent)
        self.player_color_group = QGroupBox("Your Color (vs AI):")
        player_color_layout = QHBoxLayout()
        self.white_radio = QRadioButton("White")
        self.black_radio = QRadioButton("Black")
        self.white_radio.setChecked(True)
        self.player_color_group.setLayout(player_color_layout)
        player_color_layout.addWidget(self.white_radio)
        player_color_layout.addWidget(self.black_radio)
        self.white_radio.toggled.connect(self.on_player_color_changed)
        self.player_color_group.setVisible(False) # Hide initially

        # AI Difficulty Selection
        self.difficulty_group = QGroupBox("AI Difficulty:")
        difficulty_layout = QVBoxLayout()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy (Lvl 1, 0.1s)", "Standard (Lvl 8, 0.5s)", "Hard (Lvl 15, 1.5s)"])
        self.difficulty_combo.setCurrentIndex(1) # Default to Standard
        self.difficulty_combo.currentIndexChanged.connect(self.on_difficulty_changed)
        self.difficulty_group.setLayout(difficulty_layout)
        difficulty_layout.addWidget(self.difficulty_combo)
        self.difficulty_group.setVisible(False) # Hide initially

        # New Game Button
        new_game_btn = QPushButton("New Game")
        new_game_btn.clicked.connect(self.new_game)

        # Undo Move Button (Might need disabling for AI turns)
        self.undo_move_btn = QPushButton("Undo Move")
        self.undo_move_btn.clicked.connect(self.undo_move)

        options_layout.addWidget(options_group)
        options_layout.addWidget(self.player_color_group)
        options_layout.addWidget(self.difficulty_group)
        options_layout.addWidget(new_game_btn)
        options_layout.addWidget(self.undo_move_btn)
        options_layout.addStretch() # Push controls to the top

        options_widget = QWidget()
        options_widget.setLayout(options_layout)
        options_widget.setFixedWidth(220) # Give options a fixed width

        # --- Right side: Board + Info --- #
        right_pane_layout = QVBoxLayout()

        # Game info
        info_layout = QHBoxLayout()
        self.player_label = QLabel(f"Turn: White")
        self.player_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.status_label = QLabel("Select a piece to move")
        info_layout.addWidget(self.player_label)
        info_layout.addStretch()
        info_layout.addWidget(self.status_label)
        right_pane_layout.addLayout(info_layout)

        # Chess board
        board_widget = QWidget() # Container for the grid
        board_layout = QGridLayout(board_widget)
        board_layout.setSpacing(0)
        board_layout.setContentsMargins(0,0,0,0)
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for f in range(8):
                square_index = chess.square(f, 7 - r) # Map grid (0,0 top-left) to chess square index (a1=0)
                square = ChessSquare(square_index, self)
                board_layout.addWidget(square, r, f)
                self.squares[r][f] = square
        right_pane_layout.addWidget(board_widget)

        # --- Add panes to main layout --- #
        main_layout.addWidget(options_widget)
        main_layout.addLayout(right_pane_layout)

        # Initial UI state based on defaults
        self.on_opponent_changed(0) # Set initial state based on Human opponent
        self.on_difficulty_changed(1) # Set initial difficulty

        # Hide board and info if on home screen initially
        self.toggle_game_elements_visibility(False)

    def toggle_game_elements_visibility(self, show_elements):
        """Shows or hides game board and related info labels."""
        # Assuming board_widget and info_layout are accessible
        # Need to find these elements in the layout or store references
        if hasattr(self, 'board_widget_container') and self.board_widget_container:
            self.board_widget_container.setVisible(show_elements)
        if hasattr(self, 'info_layout_widget') and self.info_layout_widget: # Assuming info_layout is in a QWidget wrapper
            self.info_layout_widget.setVisible(show_elements)
        
        # Options are always visible, but their relevance changes
        # self.options_widget.setVisible(True) 

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black) # Changed to Qt.black

        if self.game_state == CHESS_STATE_HOME:
            self.paint_home_screen(painter)
            # Ensure game elements are hidden when on home screen
            if hasattr(self, 'board_widget_container') and self.board_widget_container.isVisible():
                 self.toggle_game_elements_visibility(False)
        else:
            # Ensure game elements are visible when not on home screen
            if hasattr(self, 'board_widget_container') and not self.board_widget_container.isVisible():
                 self.toggle_game_elements_visibility(True)
            # The actual board drawing is handled by ChessSquare widgets, no need to call update_board_display here explicitly for paint
            # It's called when game logic changes.

    def paint_home_screen(self, painter):
        painter.setPen(Qt.white)
        font_title = QFont("Arial", 28, QFont.Bold)
        font_options = QFont("Arial", 18)
        painter.setFont(font_title)
        painter.drawText(self.rect(), Qt.AlignCenter, "Chess Master\n\n[S] Start Game")
        # Add more options if needed, e.g., settings

    def on_opponent_changed(self, index):
        opponent_type = self.opponent_combo.itemText(index)
        is_ai = (opponent_type == "AI Computer" and self.engine is not None)
        self.ai_player_active = is_ai
        
        self.player_color_group.setVisible(is_ai and self.game_state != CHESS_STATE_HOME)
        self.difficulty_group.setVisible(is_ai and self.game_state != CHESS_STATE_HOME)
        self.undo_move_btn.setEnabled(not is_ai and self.game_state == CHESS_STATE_PLAYING) 

        # Start a new game when opponent changes, but only if not on home screen
        if self.game_state != CHESS_STATE_HOME:
            self.new_game() 
        else:
            # If on home screen, just update visibility of AI options if AI is selected
            # This allows pre-configuration before starting.
            is_ai_selected = self.opponent_combo.itemText(self.opponent_combo.currentIndex()) == "AI Computer" and self.engine is not None
            self.player_color_group.setVisible(is_ai_selected)
            self.difficulty_group.setVisible(is_ai_selected)

    def on_player_color_changed(self):
        # Start a new game if the player color changes while AI is active and game is not on home
        if self.ai_player_active and self.game_state != CHESS_STATE_HOME:
            self.new_game()
            
    def on_difficulty_changed(self, index):
        if index == 0: # Easy
            self.ai_skill_level = 1
            self.ai_think_time = 0.1
        elif index == 1: # Standard
            self.ai_skill_level = 8
            self.ai_think_time = 0.5
        elif index == 2: # Hard
            self.ai_skill_level = 15
            self.ai_think_time = 1.5
        print(f"AI Difficulty set to: {self.difficulty_combo.itemText(index)}")
        # Configure engine immediately if it exists
        if self.engine:
            try:
                self.engine.configure({"Skill Level": self.ai_skill_level})
            except Exception as e:
                 print(f"Could not configure engine skill level: {e}")
                 # Skill Level might not be supported by all UCI engines or versions
        # Optionally restart game when difficulty changes?
        # self.new_game() 
    
    def create_initial_board(self):
        # This method is redundant
        pass 
    
    def load_piece_images(self):
        """Map python-chess piece types/colors to display characters."""
        return {
            (chess.PAWN, chess.WHITE):   '♙',
            (chess.ROOK, chess.WHITE):   '♖',
            (chess.KNIGHT, chess.WHITE): '♘',
            (chess.BISHOP, chess.WHITE): '♗',
            (chess.QUEEN, chess.WHITE):  '♕',
            (chess.KING, chess.WHITE):   '♔',
            (chess.PAWN, chess.BLACK):   '♟',
            (chess.ROOK, chess.BLACK):   '♜',
            (chess.KNIGHT, chess.BLACK): '♞',
            (chess.BISHOP, chess.BLACK): '♝',
            (chess.QUEEN, chess.BLACK):  '♛',
            (chess.KING, chess.BLACK):   '♚'
        }
    
    def update_board_display(self):
        """Update the visual display based on the chess.Board state."""
        if self.game_state == CHESS_STATE_HOME:
             self.toggle_game_elements_visibility(False) # Ensure board is hidden on home screen
             return
        else:
             self.toggle_game_elements_visibility(True)

        # Map chess.SQUARE index (0-63) back to grid row/col (0-7)
        # Remember square 0 (a1) is bottom-left, grid (7,0) is bottom-left
        for sq_index in chess.SQUARES:
            row = 7 - chess.square_rank(sq_index) 
            col = chess.square_file(sq_index)
            square_widget = self.squares[row][col]

            piece = self.board.piece_at(sq_index)
            
            # Set piece character
            if piece:
                piece_key = (piece.piece_type, piece.color)
                square_widget.set_piece(self.piece_images.get(piece_key, '?'))
            else:
                square_widget.set_piece(None)
            
            # Highlight selected square
            if self.selected_square == sq_index:
                square_widget.set_selected(True)
            else:
                square_widget.set_selected(False)
            
            # Highlight valid moves
            is_valid_dest = False
            if self.selected_square is not None:
                for move in self.valid_moves:
                    if move.to_square == sq_index:
                        is_valid_dest = True
                        break
            square_widget.set_valid_move(is_valid_dest)
        
        # Update player turn label
        turn_color = "White" if self.board.turn == chess.WHITE else "Black"
        self.player_label.setText(f"Turn: {turn_color}")
        
        # Update status label (basic)
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.status_label.setText(f"Checkmate! {winner} wins.")
        elif self.board.is_stalemate():
            self.status_label.setText("Stalemate! Draw.")
        elif self.board.is_insufficient_material():
            self.status_label.setText("Draw by insufficient material.")
        elif self.board.is_seventyfive_moves():
             self.status_label.setText("Draw by 75-move rule.")
        elif self.board.is_fivefold_repetition():
             self.status_label.setText("Draw by fivefold repetition.")
        elif self.board.is_check():
            self.status_label.setText(f"{turn_color} is in check!")
        else:
            # Reset status if no special condition
            if self.selected_square is None:
                 self.status_label.setText(f"Select a {turn_color} piece to move")
            # Keep status about selection if a piece is selected

    def square_clicked(self, square_index):
        """Handle a chess square being clicked, using chess.Board logic."""
        if self.game_state != CHESS_STATE_PLAYING: # Only allow clicks if playing
            return

        if self.board.is_game_over():
            return

        # Check if it's the human player's turn
        if not self.current_player_is_human:
            print("Not human player's turn") # Debug
            return

        piece = self.board.piece_at(square_index)

        # If no square is selected yet
        if self.selected_square is None:
            # Can only select your own pieces
            if piece and piece.color == self.board.turn:
                self.selected_square = square_index
                # Get valid moves from the chess library
                self.valid_moves = [move for move in self.board.legal_moves if move.from_square == square_index]
                if self.valid_moves:
                    piece_name = chess.piece_name(piece.piece_type).capitalize()
                    self.status_label.setText(f"Selected {piece_name}. Choose destination.")
                else:
                     self.status_label.setText("Selected piece has no legal moves.")
                     self.selected_square = None # Deselect if no moves
            else:
                # Clear selection state if clicking empty or opponent piece
                self.selected_square = None
                self.valid_moves = []
                turn_color = "White" if self.board.turn == chess.WHITE else "Black"
                self.status_label.setText(f"Select a {turn_color} piece to move")
        
        # If a square is already selected
        else:
            move = None
            # Check if the clicked square is a valid destination
            for valid_move in self.valid_moves:
                if valid_move.to_square == square_index:
                    # Handle pawn promotion - simplistic: auto-promote to Queen
                    if self.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                         rank = chess.square_rank(square_index)
                         if (self.board.turn == chess.WHITE and rank == 7) or \
                            (self.board.turn == chess.BLACK and rank == 0):
                             # Set promotion type on the move object
                             valid_move.promotion = chess.QUEEN 
                    move = valid_move
                    break
            
            if move:
                # Make the move
                self.make_move(move)
                # AI opponent's turn?
                if self.ai_player_active and not self.board.is_game_over():
                    self.current_player_is_human = False # Block human input
                    self.status_label.setText("AI is thinking...")
                    # Ensure UI updates before potentially blocking for AI
                    QApplication.processEvents() 
                    # Use QTimer to delay AI move slightly to allow UI update and prevent freezing
                    QTimer.singleShot(50, self.make_ai_move) # Reduced delay slightly
            else:
                # Clicked somewhere else - maybe select a different piece?
                # If clicking another piece of the same color, select it instead
                if piece and piece.color == self.board.turn:
                    self.selected_square = None # Deselect first
                    self.valid_moves = []
                    # Re-trigger click logic to select the new square 
                    self.square_clicked(square_index) 
                    return # Avoid double update if re-selecting
                else:
                     # Clicked an invalid square or opponent piece, just deselect
                    self.selected_square = None 
                    self.valid_moves = []
                    turn_color = "White" if self.board.turn == chess.WHITE else "Black"
                    self.status_label.setText(f"Select a {turn_color} piece to move")
        
        # Update the board display after any action
        self.update_board_display()
    
    def make_move(self, move):
        """Applies a move to the board and updates the state."""
        if self.game_state != CHESS_STATE_PLAYING: return

        self.board.push(move)
        self.selected_square = None
        self.valid_moves = []
        self.last_move_ai = None # Clear last AI move if human made a move
        
        # Check for game over 
        self.check_game_over()

    def make_ai_move(self):
        """Calculates and makes the AI's move."""
        if self.game_state != CHESS_STATE_PLAYING: return
        if not self.engine or self.board.is_game_over():
            self.current_player_is_human = True # Allow human input again
            return
        
        try:
            # Configure engine difficulty based on selection (already set in on_difficulty_changed)
            # Use time limit for control
            limit = chess.engine.Limit(time=self.ai_think_time)
            
            # Get best move
            result = self.engine.play(self.board, limit)
            best_move = result.move
            
            if best_move:
                self.last_move_ai = best_move # Store AI move for potential undo
                print(f"AI plays: {best_move}") # Debug
                self.board.push(best_move)
                self.check_game_over() # Check game state after AI move
                self.update_board_display()
            else:
                 self.status_label.setText("AI could not find a move.") # Should not happen in normal chess
        except Exception as e:
            print(f"AI move error: {e}")
            self.status_label.setText(f"AI Error: {e}")
            # Handle engine crashes? Maybe try restarting engine?

        self.current_player_is_human = True # AI finished, allow human input
        # Update status after AI move (if not game over)
        if not self.board.is_game_over():
             turn_color = "White" if self.board.turn == chess.WHITE else "Black"
             self.status_label.setText(f"Select a {turn_color} piece to move")
             # Also re-update the board display here ensure highlights are correct
             self.update_board_display()

    def get_valid_moves(self, row, col, piece):
        # This method is redundant
        pass
    
    def move_piece(self, from_pos, to_pos):
        # This method is redundant
        pass
    
    def undo_move(self):
        """Undo the last move using board.pop(). Only allows undoing human moves if against AI."""
        if self.game_state != CHESS_STATE_PLAYING: return

        if self.board.move_stack:
            # If against AI, undo is disabled via the button state
            # This check is redundant but safe
            if self.ai_player_active:
                 QMessageBox.information(self, "Undo", "Undo is disabled when playing against the AI.")
                 return
                 
            try:
                self.board.pop() # Undo the last move on the board
                self.selected_square = None
                self.valid_moves = []
                self.update_board_display() # Refresh the display
                turn_color = "White" if self.board.turn == chess.WHITE else "Black"
                self.status_label.setText(f"Move undone. {turn_color}'s turn.")
            except IndexError:
                self.status_label.setText("No moves to undo.")
        else:
            self.status_label.setText("No moves to undo.")
    
    def new_game(self):
        """Start a new game, considering AI settings."""
        # If called from home screen, game_state is already CHESS_STATE_PLAYING via start_game_action
        # If called otherwise (e.g. opponent change), ensure state is PLAYING
        if self.game_state == CHESS_STATE_HOME: # Should not happen if start_game_action is used
            print("Warning: new_game called while on home screen without start_game_action")
            self.game_state = CHESS_STATE_PLAYING 
            self.toggle_game_elements_visibility(True)

        self.board.reset()
        self.selected_square = None
        self.valid_moves = []
        self.last_move_ai = None
        
        # Determine who plays first based on settings
        if self.ai_player_active:
            # AI Opponent
            if self.black_radio.isChecked(): # Human chose Black
                self.human_player_color = chess.BLACK
                self.current_player_is_human = False # AI (White) moves first
                self.status_label.setText("New Game: AI (White) is thinking...")
                # Use QTimer to delay AI's first move
                QTimer.singleShot(100, self.make_ai_move) 
            else: # Human chose White
                self.human_player_color = chess.WHITE
                self.current_player_is_human = True # Human (White) moves first
                self.status_label.setText("New Game: White (Human) to move.")
        else: # Human vs Human
            self.human_player_color = chess.WHITE # Default doesn't matter as much here
            self.current_player_is_human = True
            self.status_label.setText("New Game: White to move.")
            
        self.update_board_display()
    
    def check_game_over(self):
        """Check game over conditions using python-chess and update status."""
        if self.game_state != CHESS_STATE_PLAYING: return False # Only check if playing

        if self.board.is_game_over():
            outcome = self.board.outcome()
            self.game_state = CHESS_STATE_GAME_OVER # Set game over state
            if outcome:
                if outcome.winner == chess.WHITE:
                    msg = "Checkmate! White wins."
                elif outcome.winner == chess.BLACK:
                    msg = "Checkmate! Black wins."
                else:
                    # Handle draws
                    termination_reason = str(outcome.termination).split('.')[-1].replace('_', ' ').title()
                    msg = f"Draw by {termination_reason}."
                self.status_label.setText(msg)
                QMessageBox.information(self, "Game Over", msg)
            # Also handle cases where outcome might be None but game is over (e.g., variants)
            elif self.board.is_stalemate(): msg = "Stalemate! Draw."
            elif self.board.is_insufficient_material(): msg = "Draw by insufficient material."
            elif self.board.is_seventyfive_moves(): msg = "Draw by 75-move rule."
            elif self.board.is_fivefold_repetition(): msg = "Draw by fivefold repetition."
            else: msg = "Game Over - Unknown Reason"
            self.status_label.setText(msg)
            # Don't show message box again if outcome was None but handled
            if outcome:
                 QMessageBox.information(self, "Game Over", msg)
            return True
        return False

    def closeEvent(self, event):
        # Clean up the engine process when the widget is closed
        print("ChessGame closeEvent called")
        if self.engine:
            print("Quitting Stockfish engine...")
            self.engine.quit()
            print("Engine quit command sent.")
            self.engine = None
        # super().closeEvent(event) # QWidget doesn't have closeEvent by default
        
    def __del__(self):
        # Ensure engine is closed if the object is deleted
        print("ChessGame __del__ called")
        if self.engine:
            print("Quitting Stockfish engine from __del__...")
            try:
                self.engine.quit()
                print("Engine quit command sent from __del__.")
            except Exception as e:
                print(f"Error quitting engine on delete: {e}")
            self.engine = None

    def start_game_action(self): # New method to handle starting the game
        self.game_state = CHESS_STATE_PLAYING
        self.toggle_game_elements_visibility(True)
        self.new_game() # This will set up the board and AI if active
        # Update visibility of AI options based on current selection
        is_ai = self.opponent_combo.itemText(self.opponent_combo.currentIndex()) == "AI Computer" and self.engine is not None
        self.player_color_group.setVisible(is_ai)
        self.difficulty_group.setVisible(is_ai)
        self.undo_move_btn.setEnabled(not is_ai)

    def keyPressEvent(self, event):
        key = event.key()
        if self.game_state == CHESS_STATE_HOME:
            if key == Qt.Key_S:
                self.start_game_action()
            return # Don't process other keys on home screen
        
        # Existing key press logic for CHESS_STATE_PLAYING etc.
        # This part remains unchanged, ensure it's inside an else or checked after HOME state
        if self.game_state == CHESS_STATE_PLAYING:
            if not self.current_player_is_human: # Prevent keyboard input during AI turn
                super().keyPressEvent(event)
                return
            # ... existing chess key press logic (none specific in original code beyond square clicks) ...
        super().keyPressEvent(event) # Pass to parent if not handled

class ChessSquare(QFrame):
    def __init__(self, square_index, parent_game):
        super().__init__(parent_game)
        self.square_index = square_index
        self.parent_game = parent_game # Renamed from 'parent' to avoid clash
        self.piece_text = None
        self.selected = False
        self.valid_move = False
        
        self.setup_ui()
    
    def setup_ui(self):
        self.setMinimumSize(60, 60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFrameShape(QFrame.Box)
        
        # Set the background color based on square index
        is_light_square = (chess.square_rank(self.square_index) + chess.square_file(self.square_index)) % 2 != 0
        if is_light_square:
            self.setStyleSheet("background-color: #f0d9b5;")  # Light wood
        else:
            self.setStyleSheet("background-color: #b58863;")  # Dark wood
    
    def set_piece(self, piece_text):
        if self.piece_text != piece_text:
            self.piece_text = piece_text
            self.update() # Trigger repaint only if changed
    
    def set_selected(self, selected):
        if self.selected != selected:
            self.selected = selected
            self.update()
    
    def set_valid_move(self, valid_move):
        if self.valid_move != valid_move:
            self.valid_move = valid_move
            self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw selection highlight
        if self.selected:
            painter.fillRect(self.rect(), QColor(0, 255, 0, 70)) # Semi-transparent green
        
        # Draw valid move indicator (small circle)
        if self.valid_move:
            radius = self.width() * 0.15
            center = self.rect().center()
            painter.setBrush(QBrush(QColor(0, 0, 0, 90))) # Semi-transparent dark circle
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
        
        # Draw the piece character
        if self.piece_text:
            # Use a font size relative to square size
            font_size = int(self.height() * 0.6)
            painter.setFont(QFont('DejaVu Sans', font_size)) # Use a font known to have chess glyphs
            
            # Set color based on piece (assuming dark pieces are 'black' in piece_text)
            if self.piece_text in ['♟', '♜', '♞', '♝', '♛', '♚']:
                painter.setPen(QColor(Qt.black))
            else:
                painter.setPen(QColor(Qt.white))
                
            painter.drawText(self.rect(), Qt.AlignCenter, self.piece_text)
    
    def mousePressEvent(self, event):
        if self.parent_game:
            self.parent_game.square_clicked(self.square_index) 