import sys
import random # Added for piece generation
import json
import os
from PyQt5.QtWidgets import QWidget, QApplication, QFrame, QMessageBox, QLabel, QInputDialog
from PyQt5.QtCore import Qt, QTimer, QBasicTimer, pyqtSignal, QRect # Added QRect for text drawing
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont # Added QFont

# Game States
STATE_HOME = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAME_OVER = 3
STATE_HIGH_SCORES_VIEW = 4

# High Score File Path
_GAME_FILE_DIR = os.path.dirname(__file__)
GAME_DATA_DIR = os.path.abspath(os.path.join(_GAME_FILE_DIR, '..', 'data')) # Assumes tetris.py in src/games, data in src/data
HIGH_SCORE_FILE = os.path.join(GAME_DATA_DIR, 'tetris_hs.json')

if not os.path.exists(GAME_DATA_DIR):
    try:
        os.makedirs(GAME_DATA_DIR)
    except OSError as e:
        print(f"Error creating data directory for Tetris {GAME_DATA_DIR}: {e}")

class Shape:
    """Represents a Tetris piece (Tetromino)."""
    class Tetrominoe:
        NoShape = 0
        ZShape = 1
        SShape = 2
        LineShape = 3
        TShape = 4
        SquareShape = 5
        LShape = 6
        MirroredLShape = 7

    COORDS_TABLE = (
        ((0, 0),     (0, 0),     (0, 0),     (0, 0)),    # NoShape
        ((0, -1),    (0, 0),     (-1, 0),    (-1, 1)),   # ZShape
        ((0, -1),    (0, 0),     (1, 0),     (1, 1)),    # SShape
        ((0, -1),    (0, 0),     (0, 1),     (0, 2)),    # LineShape
        ((-1, 0),    (0, 0),     (1, 0),     (0, 1)),    # TShape
        ((0, 0),     (1, 0),     (0, 1),     (1, 1)),    # SquareShape
        ((-1, -1),   (0, -1),    (0, 0),     (0, 1)),    # LShape
        ((1, -1),    (0, -1),    (0, 0),     (0, 1))     # MirroredLShape
    )

    def __init__(self):
        self.coords = [[0,0] for _ in range(4)]
        self.piece_shape = Shape.Tetrominoe.NoShape # Default to NoShape
        self.set_shape(Shape.Tetrominoe.NoShape)

    def shape(self):
        return self.piece_shape

    def set_shape(self, shape_type):
        table = Shape.COORDS_TABLE[shape_type]
        for i in range(4):
            for j in range(2):
                self.coords[i][j] = table[i][j]
        self.piece_shape = shape_type

    def set_random_shape(self):
        self.set_shape(random.randint(1, 7)) # 1 to 7 are actual shapes

    def x(self, index):
        return self.coords[index][0]

    def y(self, index):
        return self.coords[index][1]

    def set_x(self, index, x_val):
        self.coords[index][0] = x_val

    def set_y(self, index, y_val):
        self.coords[index][1] = y_val

    def min_x(self):
        m = self.coords[0][0]
        for i in range(4):
            m = min(m, self.coords[i][0])
        return m

    def max_x(self):
        m = self.coords[0][0]
        for i in range(4):
            m = max(m, self.coords[i][0])
        return m

    def min_y(self):
        m = self.coords[0][1]
        for i in range(4):
            m = min(m, self.coords[i][1])
        return m

    def max_y(self):
        m = self.coords[0][1]
        for i in range(4):
            m = max(m, self.coords[i][1])
        return m

    def rotated_left(self):
        if self.piece_shape == Shape.Tetrominoe.SquareShape:
            return self # Square does not rotate
        
        result = Shape()
        result.piece_shape = self.piece_shape
        for i in range(4):
            result.set_x(i, self.y(i))
            result.set_y(i, -self.x(i))
        return result

    def rotated_right(self):
        if self.piece_shape == Shape.Tetrominoe.SquareShape:
            return self
        
        result = Shape()
        result.piece_shape = self.piece_shape
        for i in range(4):
            result.set_x(i, -self.y(i))
            result.set_y(i, self.x(i))
        return result

class TetrisGame(QWidget):
    BoardWidth = 10
    BoardHeight = 22
    Speed = 300 # Milliseconds for piece to drop one line
    LevelUpLines = 10 # Lines to clear for next level
    NextPieceAreaWidth = 4 # In terms of blocks
    NextPieceAreaHeight = 4 # In terms of blocks

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_state = STATE_HOME
        self.player_name = "Player1"
        self.high_scores = self.load_high_scores()
        
        self.init_ui_elements() # Basic UI setup like focus and timers
        self.reset_and_init_game_elements() # Initialize game elements
        # Game elements (board, pieces, score) initialized by reset_and_init_game_elements()
        QTimer.singleShot(0, self.update) # Initial paint for home screen

    def init_ui_elements(self):
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QBasicTimer() # Game timer for pieces falling
        # Removed status_bar_label

    def reset_and_init_game_elements(self):
        """Resets board, score, pieces, level for a new game."""
        self.board = [Shape.Tetrominoe.NoShape] * (TetrisGame.BoardWidth * TetrisGame.BoardHeight)
        self.is_paused = False # Internal pause flag for PLAYING state
        # self.is_game_over = False # Replaced by game_state
        # self.is_started = False # Replaced by game_state
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.current_speed = TetrisGame.Speed

        self.cur_x = 0
        self.cur_y = 0
        self.current_piece = Shape()
        self.next_piece = Shape() # For displaying next piece (visual improvement later)
        self.next_piece.set_random_shape()
        
        self.clear_board() # Ensure board is visually empty (though array is new)
        self.new_piece() # Get the first piece

    def start_new_game_session(self):
        name, ok = QInputDialog.getText(self, "Player Name", "Enter your name:", text=self.player_name)
        if ok:
            self.player_name = name if name else "Player1"
        # If cancelled, keep current name

        self.reset_and_init_game_elements()
        self.game_state = STATE_PLAYING
        self.timer.start(self.current_speed, self)
        self.update()

    def shape_at(self, x, y):
        return self.board[(y * TetrisGame.BoardWidth) + x]

    def set_shape_at(self, x, y, shape_type):
        self.board[(y * TetrisGame.BoardWidth) + x] = shape_type

    def square_width(self):
        return self.contentsRect().width() // TetrisGame.BoardWidth

    def square_height(self):
        return self.contentsRect().height() // TetrisGame.BoardHeight

    def pause_game(self): # Renamed from pause for clarity
        if self.game_state != STATE_PLAYING:
            return
        self.is_paused = not self.is_paused # Toggle internal pause for PLAYING state
        if self.is_paused:
            self.timer.stop()
            self.game_state = STATE_PAUSED # Set main game state
        else:
            # This case should be handled by resume_game
            # self.timer.start(self.current_speed, self)
            # self.game_state = STATE_PLAYING 
            pass # Should not happen here, resume is explicit
        self.update()

    def resume_game(self):
        if self.game_state != STATE_PAUSED:
            return
        self.is_paused = False
        self.game_state = STATE_PLAYING
        self.timer.start(self.current_speed, self)
        self.update()

    # def update_status_bar(self): # Removed
    #     pass

    # --- Paint Methods for different states ---
    def paint_home_screen(self, painter):
        painter.setPen(Qt.white)
        font_title = QFont("Arial", 28, QFont.Bold)
        font_options = QFont("Arial", 18)
        painter.setFont(font_title)
        painter.drawText(self.rect(), Qt.AlignCenter, "Tetris\n\n[S] Start Game\n[H] High Scores")
        painter.setFont(font_options)
        current_player_text = f"Player: {self.player_name}"
        painter.drawText(20, self.height() - 30, current_player_text)

    def paint_playing_screen(self, painter):
        rect = self.contentsRect()
        
        # Calculate main board dimensions and position
        board_pixel_height = TetrisGame.BoardHeight * self.square_height()
        board_pixel_width = TetrisGame.BoardWidth * self.square_width()
        board_top = rect.bottom() - board_pixel_height
        # Try to center the board horizontally if there's extra space for HUD elements
        # For now, assume HUD is on left, board starts after HUD width or is primary focus
        hud_width = 100 # Approximate width for score/level/lines text area
        board_left = hud_width + 10 # Start board after HUD
        if rect.width() < board_pixel_width + hud_width + 20: # If not enough space, prioritize board
            board_left = (rect.width() - board_pixel_width) // 2 # Center board
            if board_left < 0: board_left = 0

        # Draw landed pieces on the main board
        for i in range(TetrisGame.BoardHeight):
            for j in range(TetrisGame.BoardWidth):
                shape = self.shape_at(j, TetrisGame.BoardHeight - 1 - i)
                if shape != Shape.Tetrominoe.NoShape:
                    self.draw_square(painter, board_left + j * self.square_width(),
                                     board_top + i * self.square_height(), shape, self.square_width(), self.square_height())
        
        # Draw current falling piece on the main board
        if self.current_piece.shape() != Shape.Tetrominoe.NoShape:
            for i in range(4):
                x = self.cur_x + self.current_piece.x(i)
                y = self.cur_y - self.current_piece.y(i)
                self.draw_square(painter, board_left + x * self.square_width(),
                                 board_top + (TetrisGame.BoardHeight - 1 - y) * self.square_height(),
                                 self.current_piece.shape(), self.square_width(), self.square_height())
        
        # Draw HUD (Score, Lines, Level) - positioned to the left of the board usually
        painter.setPen(Qt.white)
        font_hud = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font_hud)
        hud_text_x = 15
        painter.drawText(hud_text_x, board_top + 20, f"Score: {self.score}")
        painter.drawText(hud_text_x, board_top + 45, f"Lines: {self.lines_cleared_total}")
        painter.drawText(hud_text_x, board_top + 70, f"Level: {self.level}")

        # Draw "Next Piece" area and the next piece
        # Position it to the right of the HUD, or above it if space is tight.
        next_piece_display_x = hud_text_x 
        next_piece_display_y = board_top + 100 
        next_piece_box_size = self.square_width() * self.NextPieceAreaWidth + 10 # Small box for next piece

        painter.drawText(next_piece_display_x, next_piece_display_y - 5, "Next:")
        # Simple border for next piece area
        painter.setPen(QColor(100,100,100))
        painter.drawRect(next_piece_display_x - 2, next_piece_display_y + 5, 
                         self.square_width() * self.NextPieceAreaWidth + 4,
                         self.square_height() * self.NextPieceAreaHeight + 4)
        painter.setPen(Qt.white) # Reset pen

        if self.next_piece.shape() != Shape.Tetrominoe.NoShape:
            # Calculate offset to center the piece within the NextPieceArea
            # Based on the piece's own coordinate system (min_x, max_x, etc.)
            piece_width_blocks = self.next_piece.max_x() - self.next_piece.min_x() + 1
            piece_height_blocks = self.next_piece.max_y() - self.next_piece.min_y() + 1
            
            offset_x_blocks = (self.NextPieceAreaWidth - piece_width_blocks) / 2.0 - self.next_piece.min_x()
            offset_y_blocks = (self.NextPieceAreaHeight - piece_height_blocks) / 2.0 - self.next_piece.min_y()

            for i in range(4):
                x = self.next_piece.x(i) + offset_x_blocks
                y = self.next_piece.y(i) + offset_y_blocks # Y is not typically inverted for next display
                self.draw_square(painter, 
                                 int(next_piece_display_x + x * self.square_width()),
                                 int(next_piece_display_y + 10 + y * self.square_height()), 
                                 self.next_piece.shape(),
                                 self.square_width(), self.square_height(), is_next_piece=True)

    def paint_paused_screen(self, painter):
        self.paint_playing_screen(painter) # Draw game state underneath
        painter.setPen(QColor(255, 255, 0)) # Yellow text for pause
        font_pause = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font_pause)
        painter.fillRect(self.rect(), QColor(0,0,0,150)) # Semi-transparent overlay
        painter.drawText(self.rect(), Qt.AlignCenter, "Paused\n[P] Resume")

    def paint_game_over_screen(self, painter):
        painter.setPen(Qt.red)
        font_large = QFont("Arial", 28, QFont.Bold)
        font_medium = QFont("Arial", 18)
        painter.setFont(font_large)
        painter.drawText(self.rect(), Qt.AlignCenter, f"GAME OVER\nFinal Score: {self.score}")
        painter.setFont(font_medium)
        painter.setPen(Qt.white)
        options_y = self.rect().center().y() + 60
        painter.drawText(QRect(0, options_y, self.width(), 30), Qt.AlignCenter, "[S] Play Again")
        painter.drawText(QRect(0, options_y + 35, self.width(), 30), Qt.AlignCenter, "[H] High Scores")

    def paint_high_scores_screen(self, painter):
        painter.setPen(Qt.white)
        font_title = QFont("Arial", 24, QFont.Bold)
        font_score = QFont("Arial", 16)
        painter.setFont(font_title)
        painter.drawText(QRect(0, 30, self.width(), 50), Qt.AlignCenter, "High Scores")
        painter.setFont(font_score)
        y_offset = 100
        if not self.high_scores:
            painter.drawText(QRect(0, y_offset, self.width(), 30), Qt.AlignCenter, "No high scores yet!")
        else:
            for i, entry in enumerate(self.high_scores[:10]):
                painter.drawText(self.width()//2 - 100, y_offset + i * 25, f"{i+1}. {entry['name']} - {entry['score']}")
        painter.setFont(QFont("Arial", 14))
        painter.drawText(QRect(0, self.height() - 70, self.width(), 30), Qt.AlignCenter, "[B] Back to Home")
        painter.drawText(QRect(0, self.height() - 40, self.width(), 30), Qt.AlignCenter, "[R] Reset Scores")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black) # Background for all states

        if self.game_state == STATE_HOME:
            self.paint_home_screen(painter)
        elif self.game_state == STATE_PLAYING:
            self.paint_playing_screen(painter)
        elif self.game_state == STATE_PAUSED:
            self.paint_paused_screen(painter)
        elif self.game_state == STATE_GAME_OVER:
            self.paint_game_over_screen(painter)
        elif self.game_state == STATE_HIGH_SCORES_VIEW:
            self.paint_high_scores_screen(painter)
        
        painter.end()

    # def draw_game_over_message(self, painter, rect): # Replaced by paint_game_over_screen
    #     pass
        
    # def draw_pause_message(self, painter, rect): # Replaced by paint_paused_screen
    #     pass

    def keyPressEvent(self, event):
        key = event.key()

        if self.game_state == STATE_HOME:
            if key == Qt.Key_S:
                self.start_new_game_session()
            elif key == Qt.Key_H:
                self.game_state = STATE_HIGH_SCORES_VIEW
        elif self.game_state == STATE_PLAYING:
            if key == Qt.Key_P:
                self.pause_game()
            elif key == Qt.Key_Left or key == Qt.Key_A:
                self.try_move(self.current_piece, self.cur_x - 1, self.cur_y)
            elif key == Qt.Key_Right or key == Qt.Key_D:
                self.try_move(self.current_piece, self.cur_x + 1, self.cur_y)
            elif key == Qt.Key_Down or key == Qt.Key_S:
                self.one_line_down()
            elif key == Qt.Key_Up or key == Qt.Key_W: # Rotate
                self.try_move(self.current_piece.rotated_left(), self.cur_x, self.cur_y)
            elif key == Qt.Key_Space:
                self.drop_down()
            else:
                super().keyPressEvent(event)
        elif self.game_state == STATE_PAUSED:
            if key == Qt.Key_P:
                self.resume_game()
        elif self.game_state == STATE_GAME_OVER:
            if key == Qt.Key_S:
                self.start_new_game_session()
            elif key == Qt.Key_H:
                self.game_state = STATE_HIGH_SCORES_VIEW
        elif self.game_state == STATE_HIGH_SCORES_VIEW:
            if key == Qt.Key_B: # Back
                self.game_state = STATE_HOME
            elif key == Qt.Key_R: # Reset
                self.reset_high_scores()
        else:
            super().keyPressEvent(event)
        self.update() # Trigger repaint after key press

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.game_state == STATE_PLAYING and not self.is_paused: # is_paused check might be redundant with STATE_PAUSED
                self.one_line_down()
            # else: # Game not playing or is paused, timer should be stopped
            #     self.timer.stop()
        else:
            super().timerEvent(event)

    def clear_board(self):
        for i in range(TetrisGame.BoardHeight * TetrisGame.BoardWidth):
            self.board[i] = Shape.Tetrominoe.NoShape
        # self.is_game_over = False # Handled by game_state

    def new_piece(self):
        self.current_piece.set_shape(self.next_piece.shape()) # Use the stored next_piece
        self.next_piece.set_random_shape() # Generate a new next_piece
        # Calculate starting position based on the current_piece
        self.cur_x = TetrisGame.BoardWidth // 2 - (self.current_piece.max_x() + self.current_piece.min_x()) // 2 - self.current_piece.min_x()
        self.cur_y = TetrisGame.BoardHeight - 1 + self.current_piece.min_y()

        if not self.try_move(self.current_piece, self.cur_x, self.cur_y):
            self.current_piece.set_shape(Shape.Tetrominoe.NoShape)
            self.timer.stop()
            # self.is_started = False
            # self.is_game_over = True
            self.game_state = STATE_GAME_OVER
            self.check_and_add_high_score()
            # self.update_status_bar() # Removed
            self.update()

    def try_move(self, new_piece, new_x, new_y):
        for i in range(4): # Tetrominos have 4 blocks
            x = new_x + new_piece.x(i)
            y = new_y - new_piece.y(i) # Y is inverted in piece coords

            if x < 0 or x >= TetrisGame.BoardWidth or y < 0 or y >= TetrisGame.BoardHeight:
                return False 
            if self.shape_at(x, y) != Shape.Tetrominoe.NoShape: # Collision with landed piece
                return False

        self.current_piece = new_piece
        self.cur_x = new_x
        self.cur_y = new_y
        self.update()
        return True

    def one_line_down(self):
        if not self.try_move(self.current_piece, self.cur_x, self.cur_y - 1):
            self.piece_dropped()

    def drop_down(self):
        new_y = self.cur_y
        while new_y > 0:
            if not self.try_move(self.current_piece, self.cur_x, new_y - 1):
                break
            new_y -= 1
        self.piece_dropped()

    def piece_dropped(self):
        for i in range(4):
            x = self.cur_x + self.current_piece.x(i)
            y = self.cur_y - self.current_piece.y(i)
            self.set_shape_at(x, y, self.current_piece.shape())

        self.remove_full_lines()

        if not self.is_paused: # If remove_full_lines didn't end the game
            self.new_piece()

    def remove_full_lines(self):
        num_full_lines = 0
        rows_to_remove = []

        for i in range(TetrisGame.BoardHeight): # Iterate from bottom up
            is_line_full = True
            for j in range(TetrisGame.BoardWidth):
                if self.shape_at(j, i) == Shape.Tetrominoe.NoShape:
                    is_line_full = False
                    break
            
            if is_line_full:
                rows_to_remove.append(i)
        
        rows_to_remove.sort(reverse=True) # Remove from top to avoid index shifting issues

        for row in rows_to_remove:
            num_full_lines +=1
            for k in range(row, TetrisGame.BoardHeight - 1): # Shift lines down
                for j in range(TetrisGame.BoardWidth):
                    self.set_shape_at(j, k, self.shape_at(j, k + 1))
            
            # Clear the top line
            for j in range(TetrisGame.BoardWidth):
                 self.set_shape_at(j, TetrisGame.BoardHeight -1, Shape.Tetrominoe.NoShape)

        if num_full_lines > 0:
            self.score += (num_full_lines * num_full_lines * 100) * self.level # Score bonus by level
            self.lines_cleared_total += num_full_lines
            # self.update_status_bar() # Removed
            self.update()
            
            # Level up logic
            if self.lines_cleared_total // TetrisGame.LevelUpLines >= self.level:
                self.level += 1
                new_speed = self.current_speed - (self.level * 20) # Speed up
                self.current_speed = max(50, new_speed) # Don't let speed get too fast (50ms min)
                if self.timer.isActive(): # Only restart if it was running
                    self.timer.start(self.current_speed, self)
                print(f"Level Up! Level: {self.level}, Speed: {self.current_speed}")
            
        # After removing lines, check if the new piece causes game over immediately
        # This is handled in new_piece()

    def draw_square(self, painter, x, y, shape, square_width, square_height, is_next_piece=False):
        color_table = [
            0x000000, 0xCC6666, 0x66CC66, 0x6666CC, # NoShape, Z, S, Line
            0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00  # T, Square, L, MirroredL
        ]
        # More distinct classic Tetris colors (approximate)
        classic_color_table = [
            QColor(0,0,0),      # NoShape (black/transparent)
            QColor(255,0,0),    # ZShape (red)
            QColor(0,255,0),    # SShape (green)
            QColor(0,255,255),  # LineShape (cyan)
            QColor(128,0,128),  # TShape (purple)
            QColor(255,255,0),  # SquareShape (yellow)
            QColor(255,165,0),  # LShape (orange)
            QColor(0,0,255)     # MirroredLShape (blue)
        ]

        color = classic_color_table[shape]

        # Draw main block color
        painter.fillRect(x + 1, y + 1, square_width - 2, square_height - 2, color)

        # Draw Bevel effect
        # Lighter top and left edges
        painter.setPen(color.lighter(130))
        painter.drawLine(x, y + square_height - 1, x, y) # Left vertical
        painter.drawLine(x, y, x + square_width - 1, y) # Top horizontal

        # Darker bottom and right edges
        painter.setPen(color.darker(130))
        painter.drawLine(x + 1, y + square_height - 1, 
                         x + square_width - 1, y + square_height - 1) # Bottom horizontal
        painter.drawLine(x + square_width - 1, 
                         y + square_height - 1, x + square_width - 1, y + 1) # Right vertical

        # Optional: Inner highlight/shadow for more depth if desired (can be complex)

# --- High Score Methods ---
    def load_high_scores(self):
        try:
            if not os.path.exists(GAME_DATA_DIR):
                 os.makedirs(GAME_DATA_DIR)
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r') as f:
                    scores = json.load(f)
                    if isinstance(scores, list) and \
                       all(isinstance(s, dict) and 'name' in s and 'score' in s for s in scores):
                        return sorted(scores, key=lambda x: x['score'], reverse=True)[:10]
                    else:
                        print(f"Tetris high score file format error in {HIGH_SCORE_FILE}")
                        os.remove(HIGH_SCORE_FILE)
                        return []
            return []
        except Exception as e:
            print(f"Error loading Tetris high scores: {e}")
            return []

    def save_high_scores(self):
        try:
            if not os.path.exists(GAME_DATA_DIR):
                os.makedirs(GAME_DATA_DIR)
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump(self.high_scores, f, indent=4)
        except Exception as e:
            print(f"Error saving Tetris high scores: {e}")

    def check_and_add_high_score(self):
        player_name_to_save = self.player_name if hasattr(self, 'player_name') and self.player_name else "Player1"
        current_score = self.score if hasattr(self, 'score') else 0
        
        self.high_scores.append({'name': player_name_to_save, 'score': current_score})
        self.high_scores = sorted(self.high_scores, key=lambda x: x['score'], reverse=True)[:10]
        self.save_high_scores()

    def reset_high_scores(self):
        reply = QMessageBox.question(self, 'Reset Tetris High Scores',
                                   'Are you sure you want to reset all Tetris high scores?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.high_scores = []
            self.save_high_scores()
            if self.game_state == STATE_HIGH_SCORES_VIEW: # Refresh if viewing
                self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = TetrisGame()
    # game.resize(300, 660) # Old size, HUD might need more width
    game.resize(450, 660) # Adjust size to accommodate HUD/Next piece area
    game.setWindowTitle('Simple Tetris - Phase 1 Refactor')
    # Game starts on home screen, press S to play
    # game.start_new_game_session() # Optionally start game directly for testing
    game.show()
    sys.exit(app.exec_()) 