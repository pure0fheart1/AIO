import random
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush
import json
import os

# Game states
STATE_HOME = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_HIGH_SCORES_VIEW = 3

# High Score File Path
_GAME_FILE_DIR = os.path.dirname(__file__)
GAME_DATA_DIR = os.path.abspath(os.path.join(_GAME_FILE_DIR, '..', 'data'))
HIGH_SCORE_FILE = os.path.join(GAME_DATA_DIR, 'snake_hs.json')

# Ensure data directory exists
if not os.path.exists(GAME_DATA_DIR):
    try:
        os.makedirs(GAME_DATA_DIR)
    except OSError as e:
        print(f"Error creating data directory for Snake {GAME_DATA_DIR}: {e}")

# Game settings
BOARD_WIDTH = 20  # Number of cells
BOARD_HEIGHT = 15
# CELL_SIZE = 20  # Pixels - This will become dynamic
INITIAL_SPEED = 200  # Milliseconds

class SnakeGame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_manager = parent # Reference to GamesManager if needed for global actions

        # self.setFixedSize(BOARD_WIDTH * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE + 40) # Remove fixed size
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Allow widget to expand

        self.game_state = STATE_HOME
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.player_name = "Player1" # Default player name
        self.high_scores = self.load_high_scores() # Load high scores

        self.init_game_vars()
        self.setup_ui_elements() # For messages like "Press S"

    def init_game_vars(self):
        self.direction = Qt.Key_Right
        self.next_direction = Qt.Key_Right
        self.snake = [QPoint(5, 5), QPoint(4, 5), QPoint(3, 5)]
        self.food = self.generate_food()
        self.score = 0
        self.speed = INITIAL_SPEED
        self.game_over_message = ""

    def setup_ui_elements(self):
        # For displaying messages like "Press S to Start"
        self.message_label = QLabel(self)
        self.message_label.setAlignment(Qt.AlignCenter)
        # self.message_label.setGeometry(0, self.height() // 2 - 50, self.width(), 100) # Geometry will be set in resizeEvent
        self.message_label.setStyleSheet("font-size: 20px; color: white; background-color: rgba(0,0,0,150);")
        self.message_label.hide()

        self.score_label = QLabel(f"Score: {self.score}", self)
        # self.score_label.setGeometry(10, BOARD_HEIGHT * CELL_SIZE + 5, self.width() - 20, 30) # Geometry will be set in resizeEvent
        self.score_label.setStyleSheet("font-size: 16px; color: black;")
        self.score_label.setAlignment(Qt.AlignCenter)

    def get_cell_size(self):
        # Calculate cell size based on widget dimensions, maintaining aspect ratio of the board
        # Subtract space for score label
        game_area_height = self.height() - 40 
        cell_w = self.width() // BOARD_WIDTH
        cell_h = game_area_height // BOARD_HEIGHT
        return min(cell_w, cell_h)

    def get_board_pixel_width(self):
        return BOARD_WIDTH * self.get_cell_size()

    def get_board_pixel_height(self):
        return BOARD_HEIGHT * self.get_cell_size()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cell_size = self.get_cell_size()
        board_pixel_height = self.get_board_pixel_height()

        # Update label geometries
        self.message_label.setGeometry(0, board_pixel_height // 2 - 50, self.width(), 100)
        self.score_label.setGeometry(0, board_pixel_height + 5, self.width(), 30)
        self.update() # Trigger repaint

    def start_game(self):
        if self.game_state == STATE_PLAYING:
            return
        
        name, ok = QInputDialog.getText(self, "Player Name", "Enter your name:", text=self.player_name)
        if ok and name:
            self.player_name = name
        # If cancelled or empty, keeps previous or default self.player_name
            
        self.init_game_vars()
        self.game_state = STATE_PLAYING
        self.timer.start(self.speed)
        self.message_label.hide()
        self.score_label.setText(f"Score: {self.score}")
        self.setFocus()
        self.update()

    def game_loop(self):
        if self.game_state != STATE_PLAYING:
            return

        self.direction = self.next_direction
        head = QPoint(self.snake[0])

        if self.direction == Qt.Key_Left:
            head.setX(head.x() - 1)
        elif self.direction == Qt.Key_Right:
            head.setX(head.x() + 1)
        elif self.direction == Qt.Key_Up:
            head.setY(head.y() - 1)
        elif self.direction == Qt.Key_Down:
            head.setY(head.y() + 1)

        # Check collision with walls
        if not (0 <= head.x() < BOARD_WIDTH and 0 <= head.y() < BOARD_HEIGHT):
            self.end_game("Wall Collision!")
            return

        # Check collision with self
        if head in self.snake[1:]:
            self.end_game("Oops! You hit yourself.")
            return

        self.snake.insert(0, head)

        # Check food
        if head == self.food:
            self.score += 1
            self.food = self.generate_food()
            # Increase speed slightly (optional)
            if self.speed > 50:
                self.speed -= 5
            self.timer.setInterval(self.speed)
            self.score_label.setText(f"Score: {self.score}")
        else:
            self.snake.pop()

        self.update()

    def generate_food(self):
        while True:
            food_pos = QPoint(random.randint(0, BOARD_WIDTH - 1),
                              random.randint(0, BOARD_HEIGHT - 1))
            if food_pos not in self.snake:
                return food_pos

    def end_game(self, reason=""):
        self.game_state = STATE_GAME_OVER
        self.timer.stop()
        self.game_over_message = reason
        self.check_and_add_high_score() # Add score to high scores
        self.message_label.setText(f"Game Over! {reason}\nScore: {self.score}\nPress 'R' to Restart or 'H' for Home/High Scores")
        self.message_label.show()
        self.update()

    def load_high_scores(self):
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r') as f:
                    scores = json.load(f)
                    # Basic validation
                    if isinstance(scores, list) and \
                       all(isinstance(s, dict) and 'name' in s and 'score' in s for s in scores):
                        return sorted(scores, key=lambda x: x['score'], reverse=True)[:10]
                    else:
                        print(f"High score file format error in {HIGH_SCORE_FILE}. Deleting and starting fresh.")
                        os.remove(HIGH_SCORE_FILE) # Remove corrupted file
                        return []
            return []
        except Exception as e:
            print(f"Error loading snake high scores: {e}")
            # If file is corrupted in a way that os.remove fails or other json error
            if os.path.exists(HIGH_SCORE_FILE):
                try:
                    os.remove(HIGH_SCORE_FILE)
                except Exception as e_rem:
                    print(f"Could not remove corrupted high score file {HIGH_SCORE_FILE}: {e_rem}")
            return []

    def save_high_scores(self):
        try:
            # Ensure data directory exists before saving
            if not os.path.exists(GAME_DATA_DIR):
                os.makedirs(GAME_DATA_DIR)
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump(self.high_scores, f, indent=4)
        except Exception as e:
            print(f"Error saving snake high scores: {e}")

    def check_and_add_high_score(self):
        player_name_to_save = self.player_name
        current_score = self.score
        
        # Add current score
        self.high_scores.append({'name': player_name_to_save, 'score': current_score})
        # Sort and keep top 10
        self.high_scores = sorted(self.high_scores, key=lambda x: x['score'], reverse=True)[:10]
        self.save_high_scores()

    def reset_high_scores(self):
        reply = QMessageBox.question(self, 'Reset High Scores',
                                   'Are you sure you want to reset all Snake high scores?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.high_scores = []
            self.save_high_scores()
            if self.game_state == STATE_HIGH_SCORES_VIEW:
                self.update() # Refresh high score screen

    def paintEvent(self, event):
        painter = QPainter(self)
        
        cell_size = self.get_cell_size()
        board_pixel_width = self.get_board_pixel_width()
        board_pixel_height = self.get_board_pixel_height()

        # Draw background (board area)
        # painter.fillRect(0, 0, BOARD_WIDTH * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE, QColor("#333333")) # Dark gray
        painter.fillRect(0, 0, board_pixel_width, board_pixel_height, QColor("#333333"))

        if self.game_state == STATE_HOME:
            painter.fillRect(self.rect(), Qt.black) # Fill entire widget black for home screen
            # Calculate dynamic font size
            font_size = max(10, int(cell_size * 0.8)) # Ensure a minimum font size
            painter.setFont(QFont('Arial', font_size))
            painter.setPen(Qt.white)
            # Adjust text rect to be within the game board area
            text_rect = QRect(0, 0, board_pixel_width, board_pixel_height)
            painter.drawText(text_rect, Qt.AlignCenter, "Snake\n\nPress 'S' to Start")
            return

        if self.game_state == STATE_PLAYING or self.game_state == STATE_GAME_OVER:
            # Draw food
            painter.setBrush(QBrush(QColor("#FF0000"))) # Red
            painter.drawRect(self.food.x() * cell_size, self.food.y() * cell_size,
                             cell_size, cell_size)

            # Draw snake
            painter.setBrush(QBrush(QColor("#00FF00"))) # Green
            for segment in self.snake:
                painter.drawRect(segment.x() * cell_size, segment.y() * cell_size,
                                 cell_size, cell_size)
            
            # Draw grid (optional)
            painter.setPen(QColor("#444444"))
            for i in range(BOARD_WIDTH + 1):
                # painter.drawLine(i * CELL_SIZE, 0, i * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE)
                painter.drawLine(i * cell_size, 0, i * cell_size, board_pixel_height)
            for i in range(BOARD_HEIGHT + 1):
                # painter.drawLine(0, i * CELL_SIZE, BOARD_WIDTH * CELL_SIZE, i * CELL_SIZE)
                painter.drawLine(0, i * cell_size, board_pixel_width, i * cell_size)

        # Score is handled by score_label which is now positioned in resizeEvent
        # Game over message is handled by message_label (shown from end_game) which is now positioned in resizeEvent
        elif self.game_state == STATE_HIGH_SCORES_VIEW:
            self.paint_high_scores_screen(painter)

    def paint_high_scores_screen(self, painter):
        painter.fillRect(self.rect(), Qt.black)
        painter.setPen(Qt.white)
        font_title = QFont("Arial", 24, QFont.Bold)
        font_score = QFont("Arial", 16)
        font_instr = QFont("Arial", 14)

        painter.setFont(font_title)
        painter.drawText(QRect(0, 30, self.width(), 50), Qt.AlignCenter, "High Scores")

        painter.setFont(font_score)
        y_offset = 100
        if not self.high_scores:
            painter.drawText(QRect(0, y_offset, self.width(), 30), Qt.AlignCenter, "No high scores yet!")
        else:
            for i, entry in enumerate(self.high_scores):
                painter.drawText(self.width() // 2 - 120, y_offset + i * 25, f"{i + 1}. {entry['name']} - {entry['score']}")
        
        painter.setFont(font_instr)
        painter.drawText(QRect(0, self.height() - 70, self.width(), 30), Qt.AlignCenter, "[B] Back to Home")
        painter.drawText(QRect(0, self.height() - 40, self.width(), 30), Qt.AlignCenter, "[R] Reset Scores")

    def keyPressEvent(self, event):
        key = event.key()

        if self.game_state == STATE_HOME:
            if key == Qt.Key_S:
                self.start_game()
            elif key == Qt.Key_H: # Added H for High Scores from Home
                self.game_state = STATE_HIGH_SCORES_VIEW
                self.message_label.hide() # Hide home message if any
                self.update()
            return

        if self.game_state == STATE_PLAYING:
            if key == Qt.Key_Left and self.direction != Qt.Key_Right:
                self.next_direction = Qt.Key_Left
            elif key == Qt.Key_Right and self.direction != Qt.Key_Left:
                self.next_direction = Qt.Key_Right
            elif key == Qt.Key_Up and self.direction != Qt.Key_Down:
                self.next_direction = Qt.Key_Up
            elif key == Qt.Key_Down and self.direction != Qt.Key_Up:
                self.next_direction = Qt.Key_Down
            elif key == Qt.Key_P: # Pause
                self.toggle_pause()

        elif self.game_state == STATE_GAME_OVER:
            if key == Qt.Key_R:
                self.start_game()
            elif key == Qt.Key_H:
                self.go_home()
        elif self.game_state == STATE_HIGH_SCORES_VIEW:
            if key == Qt.Key_B:
                self.go_home()
            elif key == Qt.Key_R:
                self.reset_high_scores()
    
    def go_home(self):
        self.game_state = STATE_HOME
        self.timer.stop()
        self.message_label.hide()
        self.score_label.setText(f"Score: 0") # Reset score display or hide
        self.update()

    def toggle_pause(self):
        if self.game_state != STATE_PLAYING:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.message_label.setText("Paused\nPress 'P' to Resume")
            self.message_label.show()
        else:
            self.timer.start(self.speed)
            self.message_label.hide()
        self.update()

    def showEvent(self, event):
        """Called when the widget is shown."""
        super().showEvent(event)
        if self.game_state == STATE_HOME:
            self.update() # Ensure home screen message is painted
            self.setFocus()

    def hideEvent(self, event):
        """Called when the widget is hidden (e.g. tab changed)."""
        super().hideEvent(event)
        if self.timer.isActive():
            self.toggle_pause() # Auto-pause if game is running

# Example usage (for testing SnakeGame standalone)
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    game = SnakeGame()
    game.show()
    sys.exit(app.exec_()) 