import sys
import random # For shuffling deck
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QFont

# Game States
SOLITAIRE_STATE_HOME = 0
SOLITAIRE_STATE_PLAYING = 1
# SOLITAIRE_STATE_GAME_OVER_WON = 2
# SOLITAIRE_STATE_GAME_OVER_STUCK = 3 # Or just one GAME_OVER state

# Card Constants
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Approximate Card dimensions (can be dynamic later)
CARD_WIDTH = 70
CARD_HEIGHT = 100
CARD_OVERLAP_Y = 20 # Overlap for tableau cards
CARD_OVERLAP_X = 15 # Horizontal overlap for fanned piles if needed

# Layout Constants (can be adjusted based on widget size later)
TOP_MARGIN = 20
LEFT_MARGIN = 20
PILE_SPACING = 10 # Spacing between piles

class Card:
    def __init__(self, suit, rank):
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        self.suit = suit
        self.rank = rank
        self.face_up = False
        # self.image = None # Could load QPixmap here or in game class

    def __str__(self):
        return f"{self.rank}{self.suit[0]}" # e.g., "AH", "10S"

    def __repr__(self):
        return f"Card('{self.suit}', '{self.rank}')"

    def color(self):
        if self.suit in ["Hearts", "Diamonds"]:
            return "Red"
        else:
            return "Black"

    def value(self):
        """Returns the numerical value of the card for comparison (Ace=1, King=13)."""
        if self.rank == "A": return 1
        if self.rank == "K": return 13
        if self.rank == "Q": return 12
        if self.rank == "J": return 11
        return int(self.rank)

class SolitaireGame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_state = SOLITAIRE_STATE_HOME
        self.init_ui()

        # Game elements - initialized here, setup in setup_game or start_game
        self.deck = []
        self.stock_pile = []
        self.waste_pile = []
        self.foundation_piles = [[] for _ in range(4)] # 4 foundation piles
        self.tableau_piles = [[] for _ in range(7)]    # 7 tableau piles

        self.dragging = False
        self.dragged_cards = []
        self.drag_start_pos = None
        self.drag_source_pile_info = None # (pile_type, pile_index, card_index_in_pile)
        # pile_type can be 'tableau', 'waste', 'foundation'

        if self.game_state == SOLITAIRE_STATE_PLAYING: # Should ideally be called by start_game
            self.setup_game()

    def init_ui(self):
        self.setFocusPolicy(Qt.StrongFocus)
        self.message_label = QLabel("Solitaire\n\n[S] Start Game", self)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 24px; color: white;")
        self.message_label.hide() # Will be shown/hidden based on game_state

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ensure the message label covers the widget area if shown
        self.message_label.setGeometry(self.rect())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black) # Black background

        if self.game_state == SOLITAIRE_STATE_HOME:
            # Use the QLabel for home screen message
            self.message_label.setText("Solitaire\n\n[S] Start Game")
            if not self.message_label.isVisible():
                self.message_label.show()
        elif self.game_state == SOLITAIRE_STATE_PLAYING:
            if self.message_label.isVisible():
                self.message_label.hide()
            # TODO: Draw the actual Solitaire game board
            # painter.setPen(Qt.white)
            # painter.setFont(QFont("Arial", 18))
            # painter.drawText(self.rect(), Qt.AlignCenter, "Solitaire Game Area\n(Work in Progress)")
            self.draw_game_board(painter) # New method to draw all game elements

        # Draw dragged cards on top if any
        if self.dragging and self.dragged_cards:
            # For simplicity, draw at current mouse position offset by start click relative to card top-left
            # A more robust way would involve calculating current_pos based on self.drag_start_pos and mouse move event
            # This is a placeholder for dragging visuals
            current_mouse_pos = self.mapFromGlobal(self.cursor().pos()) # Get mouse pos relative to widget
            if self.drag_start_pos: # Ensure drag_start_pos is set
                dx = current_mouse_pos.x() - self.drag_start_pos.x()
                dy = current_mouse_pos.y() - self.drag_start_pos.y()
                
                # Need original rect of the first dragged card to calculate its new position
                # This part is complex without knowing the exact original card rect. Placeholder:
                start_x_render = current_mouse_pos.x() - CARD_WIDTH // 2 # Approximate centering
                start_y_render = current_mouse_pos.y() - CARD_HEIGHT // 2

                for i, card_obj in enumerate(self.dragged_cards):
                    # Simple stacked drawing for dragged cards
                    card_rect = QRect(start_x_render, start_y_render + i * CARD_OVERLAP_Y, CARD_WIDTH, CARD_HEIGHT)
                    self.draw_card(painter, card_obj, card_rect)

        # Add other states like GAME_OVER later
        
        # Important to end painter if started
        painter.end()

    def draw_game_board(self, painter):
        """Draws all piles: stock, waste, foundations, tableau."""
        # Define starting positions for piles (can be made dynamic with widget size)
        stock_x = LEFT_MARGIN
        stock_y = TOP_MARGIN
        waste_x = stock_x + CARD_WIDTH + PILE_SPACING
        waste_y = TOP_MARGIN

        # Draw Stock Pile
        stock_rect = QRect(stock_x, stock_y, CARD_WIDTH, CARD_HEIGHT)
        if self.stock_pile:
            # Draw top card of stock (or a representation like back of card)
            self.draw_card(painter, self.stock_pile[-1], stock_rect, face_down_override=True)
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(stock_rect.adjusted(0,0,0, -CARD_HEIGHT + 12), Qt.AlignCenter, f"{len(self.stock_pile)}")
        else:
            painter.setPen(QColor(80,80,80))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(stock_rect, 5, 5)
            painter.drawText(stock_rect, Qt.AlignCenter, "Empty")

        # Draw Waste Pile
        if self.waste_pile:
            # Show top 3 cards, or fewer if less than 3, slightly fanned or just top one
            # For now, just draw the top card
            waste_rect = QRect(waste_x, waste_y, CARD_WIDTH, CARD_HEIGHT)
            self.draw_card(painter, self.waste_pile[-1], waste_rect)
        else:
            waste_rect_empty = QRect(waste_x, waste_y, CARD_WIDTH, CARD_HEIGHT)
            painter.setPen(QColor(80,80,80))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(waste_rect_empty, 5, 5)

        # Draw Foundation Piles
        foundation_start_x = waste_x + CARD_WIDTH + PILE_SPACING * 3 # More spacing before foundations
        for i, pile in enumerate(self.foundation_piles):
            pile_x = foundation_start_x + i * (CARD_WIDTH + PILE_SPACING)
            pile_rect = QRect(pile_x, TOP_MARGIN, CARD_WIDTH, CARD_HEIGHT)
            if pile:
                self.draw_card(painter, pile[-1], pile_rect)
            else:
                painter.setPen(QColor(80,80,80))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(pile_rect, 5, 5)
                # Optionally draw an Ace symbol or suit placeholder
                painter.setFont(QFont("Arial", 20, QFont.Bold))
                painter.drawText(pile_rect, Qt.AlignCenter, "A")
        
        # Draw Tableau Piles
        tableau_y_start = TOP_MARGIN + CARD_HEIGHT + PILE_SPACING * 2
        for i, pile in enumerate(self.tableau_piles):
            pile_x = LEFT_MARGIN + i * (CARD_WIDTH + PILE_SPACING)
            if not pile:
                empty_tableau_rect = QRect(pile_x, tableau_y_start, CARD_WIDTH, CARD_HEIGHT)
                painter.setPen(QColor(80,80,80))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(empty_tableau_rect, 5, 5)
            else:
                for card_idx, card_obj in enumerate(pile):
                    card_y = tableau_y_start + card_idx * CARD_OVERLAP_Y
                    card_rect = QRect(pile_x, card_y, CARD_WIDTH, CARD_HEIGHT)
                    self.draw_card(painter, card_obj, card_rect)

    def draw_card(self, painter, card_obj, rect, face_down_override=None):
        """Draws a single card at the given QRect."""
        painter.setPen(Qt.black)
        is_face_up = card_obj.face_up
        if face_down_override is not None:
            is_face_up = not face_down_override

        if is_face_up:
            painter.setBrush(QColor(Qt.white))
            painter.drawRect(rect)
            
            font = QFont("Arial", 12, QFont.Bold)
            painter.setFont(font)
            
            text_color = QColor(Qt.red) if card_obj.color() == "Red" else QColor(Qt.black)
            painter.setPen(text_color)
            
            # Draw rank and suit symbol (simplified)
            rank_text = card_obj.rank
            suit_char = ''
            if card_obj.suit == "Hearts": suit_char = '♥'
            elif card_obj.suit == "Diamonds": suit_char = '♦'
            elif card_obj.suit == "Clubs": suit_char = '♣'
            elif card_obj.suit == "Spades": suit_char = '♠'
            
            # Top-left rank and suit
            painter.drawText(rect.adjusted(5, 5, 0, 0), Qt.AlignLeft | Qt.AlignTop, rank_text)
            painter.drawText(rect.adjusted(5, 20, 0, 0), Qt.AlignLeft | Qt.AlignTop, suit_char)
            
            # Bottom-right rank and suit (optional, requires rotation or careful placement)
            # For simplicity, let's draw a larger central suit symbol
            big_suit_font = QFont("Arial", 28, QFont.Bold)
            painter.setFont(big_suit_font)
            painter.drawText(rect, Qt.AlignCenter, suit_char)

        else: # Face down
            painter.setBrush(QColor(70, 100, 180)) # Blue card back
            painter.drawRect(rect)
            # Optionally draw a pattern on the card back
            painter.setPen(QColor(100, 150, 220))
            for i in range(1, 5):
                painter.drawLine(rect.left() + i*5, rect.top(), rect.right() - i*5, rect.bottom())
                painter.drawLine(rect.left(), rect.top() + i*5, rect.right(), rect.bottom() - i*5)

    def setup_game(self):
        """Initializes and shuffles the deck, then deals cards to the tableau."""
        self.deck = [Card(s, r) for s in SUITS for r in RANKS]
        random.shuffle(self.deck)

        # Reset piles
        self.stock_pile = []
        self.waste_pile = []
        self.foundation_piles = [[] for _ in range(4)]
        self.tableau_piles = [[] for _ in range(7)]

        # Deal to tableau
        for i in range(7):
            for j in range(i, 7):
                if self.deck:
                    card = self.deck.pop()
                    if i == j: # Last card in each tableau pile is face up
                        card.face_up = True
                    self.tableau_piles[j].append(card)
                else:
                    print("Error: Deck ran out during tableau setup.") # Should not happen
                    break
        
        # Remaining cards go to stock pile
        self.stock_pile = self.deck
        self.deck = [] # Deck is now conceptually empty, cards are in stock or tableau

        self.update() # Refresh display

    def start_game(self):
        self.game_state = SOLITAIRE_STATE_PLAYING
        self.setup_game() # Setup the game board
        if self.message_label.isVisible():
            self.message_label.hide()
        self.update() # Trigger repaint
        self.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        if self.game_state == SOLITAIRE_STATE_HOME:
            if key == Qt.Key_S:
                self.start_game()
        elif self.game_state == SOLITAIRE_STATE_PLAYING:
            # TODO: Handle in-game key presses if any (e.g., new deal, undo)
            pass
        super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self.game_state == SOLITAIRE_STATE_HOME:
            # Ensure message_label is correctly sized and shown
            self.message_label.setGeometry(self.rect())
            self.message_label.show()
        self.update() # Ensure repaint when widget is shown
        self.setFocus()

    def hideEvent(self, event):
        super().hideEvent(event)
        # Optional: auto-pause if game is running and has pause functionality
        # if self.game_state == SOLITAIRE_STATE_PLAYING and hasattr(self, 'timer') and self.timer.isActive():
        #     self.pause_game() # Assuming a pause_game method

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = SolitaireGame()
    game.setWindowTitle('Solitaire Game Test')
    game.resize(800,600)
    game.show()
    sys.exit(app.exec_()) 