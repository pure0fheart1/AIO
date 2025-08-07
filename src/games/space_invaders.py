import sys
import random
import time # Import the time module
import json # For high scores
import os   # For high scores path
import math # Import math module
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QBasicTimer
from PyQt5.QtGui import QPainter, QColor, QPixmap, QImage, QFont

# Game States
STATE_HOME = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAME_OVER = 3
STATE_VICTORY_WAVE_CLEAR = 4 # For screen between waves
STATE_VICTORY_FINAL = 5      # For final win screen
STATE_HIGH_SCORES_VIEW = 6   # For viewing high scores
# Other states like VICTORY_WAVE_CLEAR, VICTORY_FINAL, HIGH_SCORES_VIEW will be added later.

# High Score File Path (adjust if your data dir is elsewhere)
_GAME_FILE_DIR = os.path.dirname(__file__)
# Assuming space_invaders.py is in src/games/, and you want data in src/data/
GAME_DATA_DIR = os.path.abspath(os.path.join(_GAME_FILE_DIR, '..', 'data'))
HIGH_SCORE_FILE = os.path.join(GAME_DATA_DIR, 'space_invaders_hs.json')

# Ensure data directory exists
if not os.path.exists(GAME_DATA_DIR):
    try:
        os.makedirs(GAME_DATA_DIR)
        print(f"Created data directory: {GAME_DATA_DIR}")
    except OSError as e:
        print(f"Error creating data directory {GAME_DATA_DIR}: {e}")

class Player(QWidget):
    def __init__(self, parent_game):
        super().__init__(parent_game)
        self.game = parent_game
        self.image = QPixmap("src/resources/icons/player_ship.png") # Placeholder path
        if self.image.isNull():
            # Fallback if image not found
            self.image = QPixmap(50, 30)
            self.image.fill(Qt.blue)
            print("Warning: Player ship image not found, using fallback.")
        self.rect = QRect(0, 0, self.image.width(), self.image.height())
        self.speed = 15
        self.set_initial_position()

        # Shield state
        self.has_shield = False
        self.shield_image = QPixmap("src/resources/icons/shield_effect.png") # Placeholder
        if self.shield_image.isNull():
            # Create a simple semi-transparent blue circle as fallback shield visual
            self.shield_image = QPixmap(self.rect.width() + 10, self.rect.height() + 10)
            self.shield_image.fill(Qt.transparent)
            painter = QPainter(self.shield_image)
            painter.setBrush(QColor(0, 0, 255, 70)) # Semi-transparent blue
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.shield_image.rect())
            painter.end()
            print("Warning: Shield effect image not found, using fallback.")

    def set_initial_position(self):
        self.rect.moveTo(self.game.width() // 2 - self.rect.width() // 2,
                           self.game.height() - self.rect.height() - 10)

    def move(self, dx):
        new_x = self.rect.x() + dx * self.speed
        # Boundary checks
        if new_x >= 0 and new_x <= self.game.width() - self.rect.width():
            self.rect.moveTo(new_x, self.rect.y())

    def get_shot_start_position(self):
        return QPoint(self.rect.center().x(), self.rect.top())

    def draw(self, painter):
        painter.drawPixmap(self.rect.topLeft(), self.image)
        if self.has_shield:
            # Draw shield centered on player
            shield_x = self.rect.center().x() - self.shield_image.width() // 2
            shield_y = self.rect.center().y() - self.shield_image.height() // 2
            painter.drawPixmap(shield_x, shield_y, self.shield_image)

class BarrierBlock(QWidget): # Simple barrier block
    def __init__(self, x, y, width, height, parent_game, color=Qt.green):
        super().__init__(parent_game)
        self.rect = QRect(x, y, width, height)
        self.color = color # Could change color based on damage later
        self.alive = True

    def hit(self):
        self.alive = False # For now, one hit destroys it
        # Later, we can add health and change color

    def draw(self, painter):
        if self.alive:
            painter.fillRect(self.rect, self.color)

class Alien(QWidget):
    def __init__(self, x, y, parent_game, image_path="src/resources/icons/alien.png", health=1, points=10, color=Qt.green):
        super().__init__(parent_game)
        self.game = parent_game
        self.image_path = image_path # Store for potential reload or variations
        self.health = health
        self.max_health = health # To show damage indication later if needed
        self.points = points
        self.base_color = color # Base color for fallback

        self.image = QPixmap(image_path)
        if self.image.isNull():
            self.image = QPixmap(35, 25)
            self.image.fill(self.get_current_color()) # Use color based on health
            print(f"Warning: Alien image not found ({image_path}), using fallback color.")
        self.rect = QRect(x, y, self.image.width(), self.image.height())
        
    def get_current_color(self):
        if self.health > 1:
            # Example: slightly darker/different for tougher aliens if no specific image
            return QColor(self.base_color).darker(120) if self.health == 2 else QColor(self.base_color).darker(150)
        return self.base_color

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            return True # Alien destroyed
        else:
            # Update visual to show damage (e.g., change color or use different sprite if available)
            if self.image.isNull(): # Only change color if using fallback
                self.image.fill(self.get_current_color())
            print(f"Alien hit, health: {self.health}") # Debug
            return False # Alien still alive

    def move(self, dx, dy):
        self.rect.translate(dx, dy)

    def draw(self, painter):
        painter.drawPixmap(self.rect.topLeft(), self.image)

class Bullet(QWidget):
    def __init__(self, x, y, dy, parent_game, color=Qt.yellow):
        super().__init__(parent_game)
        self.game = parent_game
        self.rect = QRect(x - 2, y, 4, 10) # Simple rectangular bullet
        self.speed = dy
        self.color = color

    def move(self):
        self.rect.translate(0, self.speed)

    def draw(self, painter):
        painter.fillRect(self.rect, self.color)

class MotherShip(QWidget):
    def __init__(self, parent_game, image_path="src/resources/icons/mothership.png"):
        super().__init__(parent_game)
        self.game = parent_game
        self.image = QPixmap(image_path)
        if self.image.isNull():
            self.image = QPixmap(60, 25) # Wider, shorter than player
            self.image.fill(Qt.magenta) # Distinct color
            print(f"Warning: Mothership image not found ({image_path}), using fallback.")
        self.rect = QRect(0, 0, self.image.width(), self.image.height())
        self.speed = 3 # Moves horizontally
        self.direction = 1 # 1 for right, -1 for left
        self.points = 100 # Bonus points
        self.active = False
        self.spawn_y_position = 30 # Appears near the top

    def spawn(self):
        self.active = True
        # Alternate starting side
        if random.choice([True, False]):
            self.direction = 1
            self.rect.moveTo(-self.rect.width(), self.spawn_y_position)
        else:
            self.direction = -1
            self.rect.moveTo(self.game.width(), self.spawn_y_position)

    def move(self):
        if not self.active: return
        self.rect.translate(self.speed * self.direction, 0)
        # Deactivate if it goes off-screen
        if (self.direction == 1 and self.rect.left() > self.game.width()) or \
           (self.direction == -1 and self.rect.right() < 0):
            self.active = False

    def draw(self, painter):
        if self.active:
            painter.drawPixmap(self.rect.topLeft(), self.image)

class PowerUp(QWidget):
    def __init__(self, x, y, power_type, parent_game, image_path=None):
        super().__init__(parent_game)
        self.game = parent_game
        self.power_type = power_type # e.g., "rapid_fire"
        self.image = None
        if image_path:
            self.image = QPixmap(image_path)
        
        if self.image is None or self.image.isNull():
            self.image = QPixmap(20, 20) # Default size
            if self.power_type == "rapid_fire":
                self.image.fill(Qt.cyan) # Cyan for rapid fire
            elif self.power_type == "shield":
                self.image.fill(QColor(0, 200, 0, 200)) # Semi-transparent Green for shield PU
            else:
                self.image.fill(Qt.yellow) # Generic power-up color
            print(f"Warning: PowerUp image not found ({image_path}), using fallback for {self.power_type}.")
            
        self.rect = QRect(x, y, self.image.width(), self.image.height())
        self.speed_y = 2 # Falls downwards
        self.active = True
        self.duration = 5000 # milliseconds (5 seconds for rapid fire)

    def move(self):
        if not self.active: return
        self.rect.translate(0, self.speed_y)
        if self.rect.top() > self.game.height():
            self.active = False # Deactivate if it goes off-screen

    def draw(self, painter):
        if self.active:
            painter.drawPixmap(self.rect.topLeft(), self.image)

class Explosion(QWidget):
    def __init__(self, x, y, parent_game, size=30, duration=300, color=QColor(255,165,0,200)):
        super().__init__(parent_game) # Parent for drawing context
        self.game = parent_game
        self.x = x
        self.y = y
        self.max_size = size
        self.current_size = 0
        self.duration_ms = duration
        self.color = color
        self.creation_time = int(time.monotonic() * 1000)
        self.active = True
        self.particles = [] # For a more complex explosion
        self.num_particles = 15

        for _ in range(self.num_particles):
            angle = random.uniform(0, 2 * math.pi) # Use math.pi
            speed = random.uniform(0.5, 2.5) 
            radius = random.uniform(2, 5) 
            p_color = QColor(random.randint(200,255), random.randint(100,200), 0, 200) 
            self.particles.append({'x': 0, 'y': 0, 'vx': speed * math.cos(angle), 'vy': speed * math.sin(angle), 'radius': radius, 'color': p_color, 'life': duration})

    def update(self):
        if not self.active: return
        elapsed_time = int(time.monotonic() * 1000) - self.creation_time
        if elapsed_time > self.duration_ms:
            self.active = False
            return
        
        progress = elapsed_time / self.duration_ms
        self.current_size = self.max_size * progress

        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= self.game.GameSpeed # Approx ms per frame
            if p['life'] <=0:
                 # Mark for removal or just stop drawing - for now, they fade with main explosion
                 pass 

    def draw(self, painter):
        if not self.active: return
        
        current_alpha = self.color.alpha() * (1 - ( (int(time.monotonic()*1000) - self.creation_time) / self.duration_ms) )
        if current_alpha < 0: current_alpha = 0

        for p in self.particles:
            if p['life'] > 0:
                particle_alpha_ratio = max(0, p['life'] / self.duration_ms)
                p_color_with_alpha = QColor(p['color'])
                p_color_with_alpha.setAlpha(int(current_alpha * particle_alpha_ratio))
                painter.setBrush(p_color_with_alpha)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(int(self.x + p['x']), int(self.y + p['y'])), int(p['radius']), int(p['radius']))

class SpaceInvadersGame(QWidget):
    GameSpeed = 20 # Timer interval in ms
    PlayerShotCooldown = 300 # Milliseconds
    AlienShotCooldown = 1000 # Milliseconds
    AlienMoveInterval = 750 # Milliseconds for horizontal move
    # Define spawn intervals as class constants or move to instance variables if they can change
    MOTHERSHIP_SPAWN_INTERVAL_DEFAULT = 15000 # milliseconds (15 seconds)
    POWERUP_SPAWN_INTERVAL_DEFAULT = 20000  # e.g., every 20 seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        print("[SI DEBUG] __init__ called")
        self.game_state = STATE_HOME
        self.player_name = "Player1" # Default
        self.high_scores = self.load_high_scores()

        self.init_ui_elements() # Renamed from init_ui to avoid confusion with full game reset
        
        # Defer full game logic/object initialization until game starts
        QTimer.singleShot(0, self.update) # Ensure initial paint for home screen
        # Objects like self.player, self.aliens will be created in self.reset_and_init_game_entities()
        print("[SI DEBUG] __init__ finished")

    def init_ui_elements(self): # Sets up focus, size, and timers
        print("[SI DEBUG] init_ui_elements called")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(800, 600)
        
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.game_loop)
        self.alien_move_timer = QTimer(self)
        self.alien_move_timer.timeout.connect(self.trigger_alien_move)
        # Note: No self.status_label here anymore
        print("[SI DEBUG] init_ui_elements finished")

    def init_game_state(self): # Called when a game session starts (from home or after game over)
        """Resets all game-specific variables for a new play session."""
        self.player = Player(self)
        self.aliens = []
        self.player_bullets = []
        self.alien_bullets = []
        self.barriers = [] 
        self.mother_ship = MotherShip(self) 
        self.power_ups = [] 
        self.explosions = [] # List to hold active explosions

        self.score = 0
        self.lives = 3
        self.wave = 1

        # self.game_running = True # This is implicit with STATE_PLAYING
        # self.game_paused = False # Implicit with STATE_PLAYING/STATE_PAUSED
        # self.game_over_flag = False 
        # self.victory_flag = False

        self.alien_direction = 1 
        self.alien_move_down_next = False
        
        self.last_player_shot_time = 0
        self.last_alien_shot_time = 0
        self.last_mothership_spawn_time = int(time.monotonic() * 1000) # Initialize to current time to avoid immediate spawn
        self.last_powerup_spawn_time = int(time.monotonic() * 1000)

        # Define instance variables for spawn intervals
        self.mothership_spawn_interval = self.MOTHERSHIP_SPAWN_INTERVAL_DEFAULT
        self.powerup_spawn_interval = self.POWERUP_SPAWN_INTERVAL_DEFAULT
        self.original_player_shot_cooldown = self.PlayerShotCooldown # Store original for rapid fire

        self.is_rapid_fire_active = False
        self.rapid_fire_end_time = 0
        self.player.has_shield = False

        self.create_barriers()
        self.create_aliens()
        self.player.set_initial_position()
        # No QTimer.start here, done by the method that transitions to STATE_PLAYING

    def start_new_game_session(self):
        print("[SI DEBUG] start_new_game_session called")
        name, ok = QInputDialog.getText(self, "Player Name", "Enter your name:", text=self.player_name)
        if ok:
            self.player_name = name if name else "Player1"
        # If user cancels, self.player_name remains unchanged.

        self.reset_and_init_game_entities() # Prepare all game objects and score/lives etc.
        self.game_state = STATE_PLAYING
        self.game_timer.start(SpaceInvadersGame.GameSpeed)
        self.alien_move_timer.start(SpaceInvadersGame.AlienMoveInterval)
        self.update()
        print("[SI DEBUG] start_new_game_session finished, game_state:", self.game_state)

    def pause_game(self):
        print("[SI DEBUG] pause_game called")
        if self.game_state == STATE_PLAYING:
            self.game_state = STATE_PAUSED
            self.game_timer.stop()
            self.alien_move_timer.stop()
            self.update()

    def resume_game(self):
        print("[SI DEBUG] resume_game called")
        if self.game_state == STATE_PAUSED:
            self.game_state = STATE_PLAYING
            self.game_timer.start(SpaceInvadersGame.GameSpeed)
            self.alien_move_timer.start(SpaceInvadersGame.AlienMoveInterval)
            self.update()

    def game_loop(self):
        # Minimal print to avoid flooding, but confirms it's running
        # print("[SI DEBUG] game_loop, state:", self.game_state) 
        if self.game_state != STATE_PLAYING:
            return
        # ... (rest of game_loop logic from before, ensure it doesn't rely on old flags)
        current_time_monotonic_ms = int(time.monotonic() * 1000)
        if hasattr(self, 'mother_ship') and self.mother_ship.active:
            self.mother_ship.move()
        elif hasattr(self, 'mother_ship') and current_time_monotonic_ms - self.last_mothership_spawn_time > self.mothership_spawn_interval:
            if random.random() < 0.4:
                self.mother_ship.spawn()
            self.last_mothership_spawn_time = current_time_monotonic_ms
        if hasattr(self, 'power_ups'):
            if not self.is_rapid_fire_active and \
               current_time_monotonic_ms - self.last_powerup_spawn_time > self.powerup_spawn_interval:
                if random.random() < 0.3:
                    self.spawn_power_up()
                self.last_powerup_spawn_time = current_time_monotonic_ms
            for pu in self.power_ups[:]:
                if pu.active: pu.move()
                else: self.power_ups.remove(pu)
        if self.is_rapid_fire_active and current_time_monotonic_ms > self.rapid_fire_end_time:
            self.deactivate_rapid_fire()
        for bullet in self.player_bullets[:]:
            bullet.move()
            if bullet.rect.bottom() < 0: self.player_bullets.remove(bullet)
        for bullet in self.alien_bullets[:]:
            bullet.move()
            if bullet.rect.top() > self.height(): self.alien_bullets.remove(bullet)
        if hasattr(self, 'last_alien_shot_time') and current_time_monotonic_ms - self.last_alien_shot_time > SpaceInvadersGame.AlienShotCooldown:
            self.aliens_shoot()
            self.last_alien_shot_time = current_time_monotonic_ms
        self.check_collisions()
        if not self.aliens and self.game_state == STATE_PLAYING: # Check if all aliens are cleared
            self.wave_cleared()
        self.update()

    def trigger_alien_move(self):
        # print("[SI DEBUG] trigger_alien_move, state:", self.game_state)
        if self.game_state == STATE_PLAYING:
            self.move_aliens()

    def game_over(self, message="Game Over"):
        print(f"[SI DEBUG] game_over called: {message}")
        self.game_timer.stop()
        self.alien_move_timer.stop()
        self.game_state = STATE_GAME_OVER
        if hasattr(self.player, 'has_shield'): self.player.has_shield = False
        self.deactivate_rapid_fire()
        if hasattr(self, 'power_ups'): self.power_ups.clear()
        self.check_and_add_high_score()
        self.update()

    # --- Paint Methods --- (Simplified for this step)
    def paint_home_screen(self, painter):
        # print("[SI DEBUG] paint_home_screen")
        painter.setPen(Qt.white)
        font_title = QFont("Arial", 36, QFont.Bold)
        font_options = QFont("Arial", 20)
        font_name = QFont("Arial", 14)

        painter.setFont(font_title)
        title_rect = QRect(0, self.height() // 4 - 40, self.width(), 80)
        painter.drawText(title_rect, Qt.AlignCenter, "Space Invaders")

        painter.setFont(font_name)
        name_display = f"Player: {self.player_name}" if hasattr(self, 'player_name') else "Player: Player1"
        painter.drawText(20, self.height() - 30, name_display)

        options_y_start = self.height() // 2
        painter.setFont(font_options)
        painter.drawText(QRect(0, options_y_start, self.width(), 40), Qt.AlignCenter, "[S] Start Game")
        painter.drawText(QRect(0, options_y_start + 50, self.width(), 40), Qt.AlignCenter, "[H] High Scores")
        painter.drawText(QRect(0, options_y_start + 100, self.width(), 40), Qt.AlignCenter, "[Q] Quit to Menu")

    def paint_playing_screen(self, painter):
        # print("[SI DEBUG] paint_playing_screen")
        # HUD
        painter.setPen(Qt.white)
        font_hud = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font_hud)
        score = self.score if hasattr(self, 'score') else 0
        lives = self.lives if hasattr(self, 'lives') else 0
        wave = self.wave if hasattr(self, 'wave') else 0
        painter.drawText(15, 30, f"Score: {score}")
        painter.drawText(self.width() - 130, 30, f"Lives: {lives}")
        painter.drawText(self.width() // 2 - 50, 30, f"Wave: {wave}")
        
        # Game Elements
        if hasattr(self, 'player') and self.player: self.player.draw(painter)
        if hasattr(self, 'aliens'):
            for alien in self.aliens: alien.draw(painter)
        if hasattr(self, 'barriers'):
            for block in self.barriers: block.draw(painter)
        if hasattr(self, 'mother_ship') and self.mother_ship.active: self.mother_ship.draw(painter)
        if hasattr(self, 'power_ups'):
            for pu in self.power_ups: pu.draw(painter)
        if hasattr(self, 'player_bullets'):
            for bullet in self.player_bullets: bullet.draw(painter)
        if hasattr(self, 'alien_bullets'):
            for bullet in self.alien_bullets: bullet.draw(painter)

        if self.game_state == STATE_PAUSED:
            font_message = QFont("Arial", 24, QFont.Bold)
            painter.setFont(font_message)
            painter.setPen(Qt.yellow)
            # Optional: semi-transparent overlay
            # painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "Paused\nPress 'P' to Resume")

    def paint_game_over_screen(self, painter):
        # print("[SI DEBUG] paint_game_over_screen")
        font_large = QFont("Arial", 32, QFont.Bold)
        font_medium = QFont("Arial", 20)
        painter.setPen(Qt.red)
        painter.setFont(font_large)
        score_val = self.score if hasattr(self, 'score') else 0
        main_text_rect = QRect(0, self.height() // 3, self.width(), 100)
        painter.drawText(main_text_rect, Qt.AlignCenter, f"GAME OVER\nFinal Score: {score_val}")
        
        painter.setPen(Qt.white)
        painter.setFont(font_medium)
        options_y = main_text_rect.bottom() + 50
        painter.drawText(QRect(0, options_y, self.width(), 40), Qt.AlignCenter, "[S] Play Again")
        painter.drawText(QRect(0, options_y + 50, self.width(), 40), Qt.AlignCenter, "[H] High Scores")
        painter.drawText(QRect(0, options_y + 100, self.width(), 40), Qt.AlignCenter, "[Q] Quit to Menu")

    def paint_wave_clear_screen(self, painter):
        # print("[SI DEBUG] paint_wave_clear_screen")
        font_large = QFont("Arial", 32, QFont.Bold)
        font_medium = QFont("Arial", 20)
        painter.setPen(QColor(100, 255, 100)) # Light Green
        painter.setFont(font_large)
        wave_val = self.wave if hasattr(self, 'wave') else 0
        score_val = self.score if hasattr(self, 'score') else 0
        main_text_rect = QRect(0, self.height() // 3, self.width(), 100)
        painter.drawText(main_text_rect, Qt.AlignCenter, f"Wave {wave_val} Cleared!")

        painter.setPen(Qt.white)
        painter.setFont(font_medium)
        options_y = main_text_rect.bottom() + 40
        painter.drawText(QRect(0, options_y, self.width(), 40), Qt.AlignCenter, f"Score: {score_val}")
        painter.drawText(QRect(0, options_y + 50, self.width(), 40), Qt.AlignCenter, "[N] Next Wave")
        painter.drawText(QRect(0, options_y + 100, self.width(), 40), Qt.AlignCenter, "[Q] Quit to Menu")

    def paint_final_victory_screen(self, painter):
        # print("[SI DEBUG] paint_final_victory_screen")
        font_large = QFont("Arial", 32, QFont.Bold)
        font_medium = QFont("Arial", 20)
        painter.setPen(QColor(255, 215, 0)) # Gold
        painter.setFont(font_large)
        score_val = self.score if hasattr(self, 'score') else 0
        main_text_rect = QRect(0, self.height() // 3 - 20, self.width(), 120)
        painter.drawText(main_text_rect, Qt.AlignCenter, f"CONGRATULATIONS!\nYou saved the Earth!\nFinal Score: {score_val}")

        painter.setPen(Qt.white)
        painter.setFont(font_medium)
        options_y = main_text_rect.bottom() + 60
        painter.drawText(QRect(0, options_y, self.width(), 40), Qt.AlignCenter, "[S] Play Again")
        painter.drawText(QRect(0, options_y + 50, self.width(), 40), Qt.AlignCenter, "[H] High Scores")
        painter.drawText(QRect(0, options_y + 100, self.width(), 40), Qt.AlignCenter, "[Q] Quit to Menu")
        
    def paint_high_scores_screen(self, painter): # Placeholder for now
        # print("[SI DEBUG] paint_high_scores_screen")
        painter.setPen(Qt.white)
        font_title = QFont("Arial", 24, QFont.Bold)
        font_score = QFont("Arial", 16)
        font_instr = QFont("Arial", 14)

        painter.setFont(font_title)
        painter.drawText(QRect(0, 50, self.width(), 50), Qt.AlignCenter, "High Scores")

        painter.setFont(font_score)
        y_offset = 120
        scores_to_display = self.high_scores if hasattr(self, 'high_scores') else []
        if not scores_to_display:
            painter.drawText(QRect(0, y_offset, self.width(), 30), Qt.AlignCenter, "No high scores yet!")
        else:
            for i, entry in enumerate(scores_to_display[:10]): # Display top 10
                painter.drawText(self.width()//2 - 150, y_offset + i * 30, f"{i+1}. {entry.get('name', 'N/A')} - {entry.get('score', 0)}")
        
        painter.setFont(font_instr)
        painter.drawText(QRect(0, self.height() - 70, self.width(), 30), Qt.AlignCenter, "[B] Back to Home")
        painter.drawText(QRect(0, self.height() - 40, self.width(), 30), Qt.AlignCenter, "[R] Reset Scores (If Implemented)")

    def paintEvent(self, event):
        # print("[SI DEBUG] paintEvent, state:", self.game_state)
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)

        if self.game_state == STATE_HOME:
            self.paint_home_screen(painter)
        elif self.game_state == STATE_PLAYING or self.game_state == STATE_PAUSED:
            self.paint_playing_screen(painter) # PAUSED will draw over this
        elif self.game_state == STATE_GAME_OVER:
            self.paint_game_over_screen(painter)
        elif self.game_state == STATE_VICTORY_WAVE_CLEAR:
            self.paint_wave_clear_screen(painter)
        elif self.game_state == STATE_VICTORY_FINAL:
            self.paint_final_victory_screen(painter)
        elif self.game_state == STATE_HIGH_SCORES_VIEW:
            self.paint_high_scores_screen(painter)
        
        # Draw explosions
        if hasattr(self, 'explosions'): 
            for exp in self.explosions:
                if exp.active:
                    exp.draw(painter)
        
        painter.end()

    def keyPressEvent(self, event):
        key = event.key()
        # print(f"[SI DEBUG] keyPressEvent: {key}, state: {self.game_state}")
        current_game_state = self.game_state # Cache for clarity

        if current_game_state == STATE_HOME:
            if key == Qt.Key_S:
                self.start_new_game_session()
            elif key == Qt.Key_H:
                self.game_state = STATE_HIGH_SCORES_VIEW
            elif key == Qt.Key_Q:
                self.quit_game_to_main_menu() # Implement this if needed
        elif current_game_state == STATE_PLAYING:
            if key == Qt.Key_P:
                self.pause_game()
            elif key == Qt.Key_Left or key == Qt.Key_A:
                if hasattr(self, 'player'): self.player.move(-1)
            elif key == Qt.Key_Right or key == Qt.Key_D:
                if hasattr(self, 'player'): self.player.move(1)
            elif key == Qt.Key_Space:
                self.player_shoot() # player_shoot itself checks if player exists
        elif current_game_state == STATE_PAUSED:
            if key == Qt.Key_P:
                self.resume_game()
        elif current_game_state == STATE_GAME_OVER or current_game_state == STATE_VICTORY_FINAL:
            if key == Qt.Key_S:
                self.start_new_game_session()
            elif key == Qt.Key_H:
                self.game_state = STATE_HIGH_SCORES_VIEW
            elif key == Qt.Key_Q:
                self.quit_game_to_main_menu()
        elif current_game_state == STATE_VICTORY_WAVE_CLEAR:
            if key == Qt.Key_N:
                self.next_wave()
            elif key == Qt.Key_Q:
                self.quit_game_to_main_menu()
        elif current_game_state == STATE_HIGH_SCORES_VIEW:
            if key == Qt.Key_B: # Back to Home
                self.game_state = STATE_HOME
            elif key == Qt.Key_R: # Reset High Scores
                self.reset_high_scores()
        
        self.update() # Request repaint

    # ... (Keep other methods like create_aliens, move_aliens, player_shoot, check_collisions, etc.)
    # ... (Ensure they check for existence of attributes like self.player if they can be called before full init_game_state)
    # Placeholder for methods that were defined in the full change but are not part of this minimal step yet:
    def create_barriers(self): self.barriers = [] # Minimal
    # def create_aliens(self): self.aliens = [] # Minimal, will be filled by init_game_state
    def spawn_power_up(self): pass
    def activate_power_up(self, pu): pass
    def deactivate_rapid_fire(self): self.is_rapid_fire_active = False
    def load_high_scores(self):
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r') as f:
                    scores = json.load(f)
                    if isinstance(scores, list) and \
                       all(isinstance(s, dict) and 'name' in s and 'score' in s for s in scores):
                        return sorted(scores, key=lambda x: x['score'], reverse=True)[:10]
                    else:
                        print(f"High score file format error in {HIGH_SCORE_FILE}")
                        os.remove(HIGH_SCORE_FILE) # Remove corrupted file
                        return []
            return []
        except Exception as e:
            print(f"Error loading high scores: {e}")
            return []
    def save_high_scores(self):
        try:
            # Ensure data directory exists before saving
            if not os.path.exists(GAME_DATA_DIR):
                os.makedirs(GAME_DATA_DIR)
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump(self.high_scores, f, indent=4)
        except Exception as e:
            print(f"Error saving high scores: {e}")
    def check_and_add_high_score(self):
        player_name_to_save = self.player_name if hasattr(self, 'player_name') and self.player_name else "Player1"
        current_score = self.score if hasattr(self, 'score') else 0
        
        self.high_scores.append({'name': player_name_to_save, 'score': current_score})
        self.high_scores = sorted(self.high_scores, key=lambda x: x['score'], reverse=True)[:10]
        self.save_high_scores()
    def reset_high_scores(self):
        reply = QMessageBox.question(self, 'Reset High Scores',
                                   'Are you sure you want to reset all high scores?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.high_scores = []
            self.save_high_scores()
            self.update() # Refresh high score screen if currently viewing
    def quit_game_to_main_menu(self):
        # This method should ideally signal the GamesManager to switch tabs or handle visibility.
        # For now, just revert to home state of this game.
        print("Action: Quit to game's home screen / main menu.")
        self.game_timer.stop()
        self.alien_move_timer.stop()
        # self.game_running = False # Not needed if using game_state
        self.game_state = STATE_HOME
        self.update()
        # If part of a larger app and want to switch tabs in GamesManager:
        # if self.parent() and hasattr(self.parent(), 'go_to_first_game_tab'): # Example
        #     self.parent().go_to_first_game_tab()

    def create_aliens(self):
        self.aliens.clear() 
        if not hasattr(self, 'wave'): self.wave = 1 # Ensure wave attribute
        alien_rows = 3 + self.wave 
        alien_cols = 8
        spacing_x = 45
        spacing_y = 35
        start_x = (self.width() - (alien_cols * spacing_x)) // 2
        if start_x < 0: start_x = 10 # Ensure aliens don't start off-screen if window too small
        start_y = 50
        for r in range(min(alien_rows, 5)):
            for c in range(alien_cols):
                x = start_x + c * spacing_x
                y = start_y + r * spacing_y
                is_tough = self.wave > 1 and random.random() < 0.2
                img_path = "src/resources/icons/alien_tough.png" if is_tough else "src/resources/icons/alien.png"
                health = 2 if is_tough else 1
                points = 25 if is_tough else 10
                color = Qt.red if is_tough else Qt.green
                self.aliens.append(Alien(x, y, self, image_path=img_path, health=health, points=points, color=color))
        self.alien_direction = 1 
        self.alien_move_down_next = False

    def move_aliens(self):
        if not self.aliens: return
        move_dx = self.alien_direction * 10
        move_dy = 0
        if self.alien_move_down_next:
            move_dy = 20
            self.alien_direction *= -1
            self.alien_move_down_next = False
            move_dx = 0
        at_boundary = False
        for alien in self.aliens:
            if not self.alien_move_down_next:
                if (alien.rect.right() + move_dx > self.width() and self.alien_direction > 0) or \
                   (alien.rect.left() + move_dx < 0 and self.alien_direction < 0):
                    at_boundary = True
                    break 
        if at_boundary and not self.alien_move_down_next:
            self.alien_move_down_next = True 
            move_dx = 0
        for alien in self.aliens:
            alien.move(move_dx, move_dy)
            if hasattr(self, 'player') and self.player and alien.rect.bottom() >= self.player.rect.top():
                self.game_state = STATE_GAME_OVER
                self.game_over("Aliens reached the bottom!")
                return

    def aliens_shoot(self):
        if not self.aliens or random.random() < 0.6: return
        potential_shooters = []
        columns_with_aliens = sorted(list(set(alien.rect.x() // 40 for alien in self.aliens)))
        for col_idx_approx in columns_with_aliens:
            aliens_in_col = [a for a in self.aliens if abs(a.rect.x() // 40 - col_idx_approx) < 1]
            if aliens_in_col:
                potential_shooters.append(max(aliens_in_col, key=lambda a: a.rect.bottom()))
        if potential_shooters:
            shooter_alien = random.choice(potential_shooters)
            self.alien_bullets.append(Bullet(shooter_alien.rect.center().x(), shooter_alien.rect.bottom(), 5, self, Qt.red))

    def player_shoot(self):
        if not hasattr(self, 'player'): return
        current_time_monotonic_ms = int(time.monotonic() * 1000)
        current_shot_cooldown = self.original_player_shot_cooldown # Use the instance variable
        if self.is_rapid_fire_active:
            current_shot_cooldown = self.original_player_shot_cooldown // 3
        if current_time_monotonic_ms - self.last_player_shot_time > current_shot_cooldown:
            pos = self.player.get_shot_start_position()
            self.player_bullets.append(Bullet(pos.x(), pos.y(), -7, self, Qt.cyan))
            self.last_player_shot_time = current_time_monotonic_ms

    def check_collisions(self):
        if not hasattr(self, 'player'): return
        for bullet in self.player_bullets[:]:
            for alien in self.aliens[:]:
                if bullet.rect.intersects(alien.rect):
                    if bullet in self.player_bullets: self.player_bullets.remove(bullet)
                    if alien.hit(): 
                        self.score += alien.points
                        self.explosions.append(Explosion(alien.rect.center().x(), alien.rect.center().y(), self))
                        self.aliens.remove(alien)
                    break 
            if bullet not in self.player_bullets: continue
            if hasattr(self, 'mother_ship') and self.mother_ship.active and bullet.rect.intersects(self.mother_ship.rect):
                self.score += self.mother_ship.points
                self.mother_ship.active = False
                self.explosions.append(Explosion(self.mother_ship.rect.center().x(), self.mother_ship.rect.center().y(), self, size=50, color=QColor(255,0,255,200)))
                if bullet in self.player_bullets: self.player_bullets.remove(bullet)
                continue
            for barrier_block in self.barriers[:]:
                if barrier_block.alive and bullet.rect.intersects(barrier_block.rect):
                    barrier_block.hit()
                    self.explosions.append(Explosion(barrier_block.rect.center().x(), barrier_block.rect.center().y(), self, size=10, duration=150, color=QColor(0,255,0,150)))
                    if bullet in self.player_bullets: self.player_bullets.remove(bullet)
                    break
        for bullet in self.alien_bullets[:]:
            if bullet.rect.intersects(self.player.rect):
                if bullet in self.alien_bullets: self.alien_bullets.remove(bullet)
                if self.player.has_shield:
                    self.player.has_shield = False
                    self.explosions.append(Explosion(self.player.rect.center().x(), self.player.rect.center().y(), self, size=40, color=QColor(0,0,255,100))) # Shield hit effect
                else:
                    self.lives -= 1
                    self.explosions.append(Explosion(self.player.rect.center().x(), self.player.rect.center().y(), self, size=60, color=QColor(255,0,0,220))) # Player destroyed
                    if self.lives <= 0:
                        self.game_state = STATE_GAME_OVER
                        self.game_over("Player destroyed!")
                break
            if bullet not in self.alien_bullets: continue
            for barrier_block in self.barriers[:]:
                if barrier_block.alive and bullet.rect.intersects(barrier_block.rect):
                    barrier_block.hit()
                    self.explosions.append(Explosion(barrier_block.rect.center().x(), barrier_block.rect.center().y(), self, size=10, duration=150, color=QColor(0,255,0,150)))
                    if bullet in self.alien_bullets: self.alien_bullets.remove(bullet)
                    break
        for alien in self.aliens:
            if alien.rect.intersects(self.player.rect):
                self.explosions.append(Explosion(self.player.rect.center().x(), self.player.rect.center().y(), self, size=60, color=QColor(255,0,0,220)))
                self.game_state = STATE_GAME_OVER
                self.game_over("Alien collision!")
                return
        if hasattr(self, 'power_ups'):
            for pu in self.power_ups[:]:
                if pu.active and self.player.rect.intersects(pu.rect):
                    self.activate_power_up(pu)
                    pu.active = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'player') and self.player:
             if self.game_state == STATE_HOME or not self.game_state == STATE_PLAYING : # Keep player at bottom if not playing
                  self.player.set_initial_position()
        self.update()

    def reset_and_init_game_entities(self):
        print("[SI DEBUG] reset_and_init_game_entities called")
        self.player = Player(self)
        print(f"[SI DEBUG] Player initialized: {self.player}")
        self.aliens = []
        self.player_bullets = []
        self.alien_bullets = []
        self.barriers = []
        self.mother_ship = MotherShip(self)
        self.power_ups = []
        self.explosions = [] # Ensure this is initialized once here

        self.score = 0
        self.lives = 3
        self.wave = 1

        self.alien_direction = 1
        self.alien_move_down_next = False
        
        current_time_ms = int(time.monotonic() * 1000)
        self.last_player_shot_time = 0 
        self.last_alien_shot_time = current_time_ms
        self.last_mothership_spawn_time = current_time_ms
        self.last_powerup_spawn_time = current_time_ms
        
        # Define instance variables for spawn intervals and original cooldown
        self.mothership_spawn_interval = self.MOTHERSHIP_SPAWN_INTERVAL_DEFAULT
        self.powerup_spawn_interval = self.POWERUP_SPAWN_INTERVAL_DEFAULT
        self.original_player_shot_cooldown = self.PlayerShotCooldown 

        self.is_rapid_fire_active = False
        self.rapid_fire_end_time = 0
        if hasattr(self.player, 'has_shield'): 
            self.player.has_shield = False

        self.create_barriers()
        self.create_aliens() 
        if hasattr(self.player, 'set_initial_position'):
            self.player.set_initial_position()
        print("[SI DEBUG] reset_and_init_game_entities finished")

    def wave_cleared(self):
        # Stop alien movement and game logic, but not player controls for "Next Wave" screen
        self.game_timer.stop() 
        self.alien_move_timer.stop()
        
        if hasattr(self.player, 'has_shield'): self.player.has_shield = False
        self.deactivate_rapid_fire()
        if hasattr(self, 'power_ups'): self.power_ups.clear()

        if self.wave >= 3: # Assuming 3 waves for a full victory
            self.final_victory()
        else:
            self.game_state = STATE_VICTORY_WAVE_CLEAR
        self.update()

    def final_victory(self):
        self.game_state = STATE_VICTORY_FINAL
        # Ensure timers are stopped from wave_cleared or stop them here again just in case
        self.game_timer.stop()
        self.alien_move_timer.stop()
        self.check_and_add_high_score()
        self.update()

    def next_wave(self):
        if self.game_state != STATE_VICTORY_WAVE_CLEAR:
            return
        self.wave += 1
        
        # Minimal reset for next wave, keep score and lives
        self.player_bullets.clear()
        self.alien_bullets.clear()
        # self.barriers.clear() # Optionally regenerate barriers per wave or keep damaged ones
        # self.create_barriers()
        self.mother_ship = MotherShip(self) # Reset mothership
        self.power_ups.clear()

        self.create_aliens()
        if hasattr(self.player, 'set_initial_position'):
            self.player.set_initial_position()
        if hasattr(self.player, 'has_shield'): # Reset shield for new wave
            self.player.has_shield = False
        self.deactivate_rapid_fire() # Reset rapid fire

        self.game_state = STATE_PLAYING
        self.game_timer.start(SpaceInvadersGame.GameSpeed)
        self.alien_move_timer.start(SpaceInvadersGame.AlienMoveInterval)
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = SpaceInvadersGame()
    game.setWindowTitle('Simple Space Invaders Test')
    game.show() 
    # Game starts by pressing 'S'
    sys.exit(app.exec_()) 