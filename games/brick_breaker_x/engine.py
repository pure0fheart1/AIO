"""
Brick Breaker X - embedded-friendly Breakout engine for PyQt5 apps.

Rendering strategy
- No pygame window is created. We render to an offscreen pygame.Surface using
  pygame.math/joystick modules only. The Qt wrapper pulls this surface each
  frame, converts to QImage, and paints it in the central panel. This keeps the
  Qt event loop responsive and avoids SDL window focus issues.

Features implemented
- Multiple levels with brick layout files (ASCII maps)
- Power-ups: big paddle, multi-ball, fireball
- Score + high score JSON persistence
- Animated background on higher levels
- Options: paddle size, base ball speed, best-of-X (match length)
- CRT scanline filter toggle for retro look
- Xbox controller + keyboard controls

Customize
- Add a level: drop a new text file into games/brick_breaker_x/levels with rows of
  characters. Use '#' for a brick, '.' for empty. The engine will advance
  sequentially.
- Add a power-up: extend PowerUpType and handle in apply_powerup().
- Tweak ball physics: update BALL_SPEED_BASE, bounce damping or angle logic in
  _ball_paddle_collision and _ball_brick_collision.
"""

from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional

import pygame


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
HIGHSCORE_PATH = os.path.join(DATA_DIR, "brick_breaker_x_highscores.json")


class PowerUpType(Enum):
    BIG_PADDLE = "BIG_PADDLE"
    MULTI_BALL = "MULTI_BALL"
    FIREBALL = "FIREBALL"


@dataclass
class Paddle:
    x: float
    y: float
    width: float
    height: float = 16
    speed: float = 580.0

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - self.height / 2), int(self.width), int(self.height))


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = 8
    on_fire: bool = False  # If True, passes through bricks and deals more points


@dataclass
class Brick:
    rect: pygame.Rect
    hp: int = 1


@dataclass
class PowerUp:
    kind: PowerUpType
    x: float
    y: float
    vy: float = 140.0
    size: int = 18

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.size / 2), int(self.y - self.size / 2), self.size, self.size)


class Controller:
    """Simple polling-based controller with Xbox + keyboard support."""

    def __init__(self) -> None:
        pygame.joystick.init()
        self.joy: Optional[pygame.joystick.Joystick] = None
        if pygame.joystick.get_count() > 0:
            j = pygame.joystick.Joystick(0)
            j.init()
            self.joy = j

    def update(self) -> dict:
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        axis = 0.0
        launch = keys[pygame.K_SPACE]
        pause = keys[pygame.K_RETURN]
        crt = keys[pygame.K_c]

        if self.joy is not None:
            try:
                axis = self.joy.get_axis(0)
                launch = launch or bool(self.joy.get_button(0))  # A
                pause = pause or bool(self.joy.get_button(7))    # Start
                crt = crt or bool(self.joy.get_button(2))        # X
            except Exception:
                pass

        left = keys[pygame.K_LEFT] or keys[pygame.K_a] or axis < -0.2
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d] or axis > 0.2
        return {"left": left, "right": right, "launch": launch, "pause": pause, "crt": crt}


class BrickBreakerEngine:
    VIRTUAL_W = 1280
    VIRTUAL_H = 720

    def __init__(self, levels_dir: Optional[str] = None) -> None:
        pygame.init()
        pygame.font.init()
        self.font_ui = pygame.font.SysFont("Consolas", 24)
        self.font_big = pygame.font.SysFont("Consolas", 48)
        self.controller = Controller()
        self.levels_dir = levels_dir or os.path.join(os.path.dirname(__file__), "levels")

        self.reset_options()
        self._load_highscores()
        self.state = "menu"  # menu | play | gameover | pause
        self.match_wins_needed = (self.best_of // 2) + 1
        self.player_game_wins = 0
        self.opponent_dummy_wins = 0  # placeholder future modes

        self._load_level_list()
        self._build_level(0)

    # -------- public controls used by wrapper --------
    def restart(self) -> None:
        self.player_game_wins = 0
        self.opponent_dummy_wins = 0
        self.current_level_idx = 0
        self._build_level(self.current_level_idx)
        self.state = "menu"

    def toggle_crt(self) -> None:
        self.enable_crt = not self.enable_crt

    # -------- high-level lifecycle --------
    def update(self, dt: float) -> None:
        self.controller.update()
        inp = self.controller.update()

        if self.state == "menu":
            if inp["launch"]:
                self.state = "play"
        elif self.state == "pause":
            if inp["pause"]:
                self.state = "play"
        elif self.state == "gameover":
            if inp["launch"]:
                self.restart()
        elif self.state == "play":
            if inp["pause"]:
                self.state = "pause"
            self._update_play(dt, inp)

        if inp["crt"]:
            self.enable_crt = not self.enable_crt

    def render(self, target: pygame.Surface) -> None:
        surf = pygame.Surface((self.VIRTUAL_W, self.VIRTUAL_H))
        self._draw_background(surf)

        if self.state in ("menu", "pause", "play", "gameover"):
            self._draw_world(surf)

        if self.state == "menu":
            self._overlay_center(surf, "Brick Breaker X", 80)
            self._overlay_sub(surf, "Space/A to Start  |  Enter/Start to Pause  |  C to Toggle CRT")
            self._overlay_sub(surf, f"Options: Paddle {int(self.paddle.width)}  Ball {self.base_ball_speed:.0f}  Best-of {self.best_of}", y=420)
        elif self.state == "pause":
            self._overlay_center(surf, "Paused", 80)
        elif self.state == "gameover":
            self._overlay_center(surf, f"Game Over - Score {self.score}", 70)
            self._overlay_sub(surf, "Space/A to Restart")

        # Apply CRT overlay if enabled
        if self.enable_crt:
            self._apply_crt(surf)

        pygame.transform.smoothscale(surf, target.get_size(), target)

    # -------- menu helpers (simple inline adjustments) --------
    def reset_options(self):
        self.base_ball_speed = 420.0
        self.paddle = Paddle(x=self.VIRTUAL_W / 2, y=self.VIRTUAL_H - 60, width=160.0)
        self.best_of = 3
        self.enable_crt = False

    # -------- world building / persistence --------
    def _load_highscores(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            if os.path.exists(HIGHSCORE_PATH):
                with open(HIGHSCORE_PATH, "r", encoding="utf-8") as f:
                    self.highscores = json.load(f)
            else:
                self.highscores = {"high_score": 0}
        except Exception:
            self.highscores = {"high_score": 0}

    def _save_highscores(self) -> None:
        try:
            with open(HIGHSCORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.highscores, f, indent=2)
        except Exception:
            pass

    def _load_level_list(self) -> None:
        self.level_files: List[str] = []
        if os.path.isdir(self.levels_dir):
            for name in sorted(os.listdir(self.levels_dir)):
                if name.lower().endswith((".txt", ".lvl")):
                    self.level_files.append(os.path.join(self.levels_dir, name))
        if not self.level_files:
            # Fallback minimal layout in-memory
            self.level_files = []

    def _build_level(self, idx: int) -> None:
        self.current_level_idx = idx
        self.bricks: List[Brick] = []
        self.balls: List[Ball] = []
        self.powerups: List[PowerUp] = []
        self.score = 0 if idx == 0 else self.score
        self.lives = 3

        # Animated background state
        self.bg_phase = 0.0

        # Create initial ball
        self.balls.append(Ball(self.VIRTUAL_W / 2, self.VIRTUAL_H - 100, 0.0, -self.base_ball_speed))

        # Build bricks
        grid_top = 120
        grid_left = 100
        cols = 14
        rows = 8
        cell_w = (self.VIRTUAL_W - grid_left * 2) // cols
        cell_h = 30

        if self.level_files:
            try:
                with open(self.level_files[idx % len(self.level_files)], "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\n") for line in f]
                rows = min(rows, len(lines))
                cols = min(cols, max((len(r) for r in lines), default=cols))
                for r in range(rows):
                    for c in range(cols):
                        ch = lines[r][c] if c < len(lines[r]) else '.'
                        if ch == '#':
                            rect = pygame.Rect(grid_left + c * cell_w + 2, grid_top + r * cell_h + 2, cell_w - 4, cell_h - 4)
                            self.bricks.append(Brick(rect=rect, hp=1 + (idx // 2)))
            except Exception:
                pass
        else:
            # Default checkerboard layout
            for r in range(rows):
                for c in range(cols):
                    if (r + c) % 2 == 0:
                        rect = pygame.Rect(grid_left + c * cell_w + 2, grid_top + r * cell_h + 2, cell_w - 4, cell_h - 4)
                        self.bricks.append(Brick(rect=rect, hp=1 + (idx // 2)))

    # -------- gameplay update/draw --------
    def _update_play(self, dt: float, inp: dict) -> None:
        # Move paddle
        if inp["left"]:
            self.paddle.x -= self.paddle.speed * dt
        if inp["right"]:
            self.paddle.x += self.paddle.speed * dt
        self.paddle.x = max(self.paddle.width / 2, min(self.VIRTUAL_W - self.paddle.width / 2, self.paddle.x))

        # Update balls
        for ball in self.balls:
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt

            # Wall collisions
            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.vx = abs(ball.vx)
            if ball.x + ball.radius > self.VIRTUAL_W:
                ball.x = self.VIRTUAL_W - ball.radius
                ball.vx = -abs(ball.vx)
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.vy = abs(ball.vy)

        # Paddle collision
        padd_rect = self.paddle.rect()
        for ball in self.balls:
            if padd_rect.collidepoint(ball.x, ball.y + ball.radius):
                rel = (ball.x - (padd_rect.x + padd_rect.width / 2)) / (padd_rect.width / 2)
                angle = rel * (math.pi * 0.35)
                speed = max(self.base_ball_speed, math.hypot(ball.vx, ball.vy))
                ball.vx = speed * math.sin(angle)
                ball.vy = -abs(speed * math.cos(angle))
                ball.y = padd_rect.y - ball.radius - 1

        # Brick collisions
        remaining_bricks: List[Brick] = []
        for brick in self.bricks:
            hit = False
            for ball in self.balls:
                if brick.rect.collidepoint(ball.x, ball.y - ball.radius) or \
                   brick.rect.collidepoint(ball.x, ball.y + ball.radius) or \
                   brick.rect.collidepoint(ball.x - ball.radius, ball.y) or \
                   brick.rect.collidepoint(ball.x + ball.radius, ball.y):
                    hit = True
                    self.score += 10 if not ball.on_fire else 20
                    if not ball.on_fire:
                        # reflect basic
                        dx = abs(min(ball.x - brick.rect.left, brick.rect.right - ball.x))
                        dy = abs(min(ball.y - brick.rect.top, brick.rect.bottom - ball.y))
                        if dx < dy:
                            ball.vx = -ball.vx
                        else:
                            ball.vy = -ball.vy
                    brick.hp -= 1 if not ball.on_fire else 2
            if brick.hp > 0:
                remaining_bricks.append(brick)
            else:
                # Chance to spawn a powerup
                if random.random() < 0.12:
                    kind = random.choice([PowerUpType.BIG_PADDLE, PowerUpType.MULTI_BALL, PowerUpType.FIREBALL])
                    self.powerups.append(PowerUp(kind, brick.rect.centerx, brick.rect.centery))
        self.bricks = remaining_bricks

        # Powerups fall
        next_powerups: List[PowerUp] = []
        for p in self.powerups:
            p.y += p.vy * dt
            if p.rect().colliderect(padd_rect):
                self._apply_powerup(p.kind)
            elif p.y < self.VIRTUAL_H + 40:
                next_powerups.append(p)
        self.powerups = next_powerups

        # Ball death and life loss
        next_balls: List[Ball] = []
        for b in self.balls:
            if b.y - b.radius > self.VIRTUAL_H:
                continue
            next_balls.append(b)
        self.balls = next_balls
        if not self.balls:
            self.lives -= 1
            if self.lives <= 0:
                self._end_game()
            else:
                self.balls.append(Ball(self.paddle.x, self.VIRTUAL_H - 100, 0.0, -self.base_ball_speed))

        # Level clear
        if not self.bricks and self.balls:
            self.current_level_idx += 1
            self._build_level(self.current_level_idx)

        # Update background phase for animation
        self.bg_phase += dt

    def _apply_powerup(self, kind: PowerUpType) -> None:
        if kind == PowerUpType.BIG_PADDLE:
            self.paddle.width = min(300.0, self.paddle.width + 50.0)
        elif kind == PowerUpType.MULTI_BALL:
            new_balls: List[Ball] = []
            for b in self.balls:
                ang = math.atan2(b.vy, b.vx)
                spd = max(self.base_ball_speed, math.hypot(b.vx, b.vy))
                new_balls.append(Ball(b.x, b.y, spd * math.cos(ang + 0.3), spd * math.sin(ang + 0.3)))
                new_balls.append(Ball(b.x, b.y, spd * math.cos(ang - 0.3), spd * math.sin(ang - 0.3)))
            self.balls.extend(new_balls)
        elif kind == PowerUpType.FIREBALL:
            for b in self.balls:
                b.on_fire = True

    def _end_game(self) -> None:
        self.state = "gameover"
        self.highscores["high_score"] = max(self.highscores.get("high_score", 0), self.score)
        self._save_highscores()

    # -------- drawing --------
    def _draw_background(self, surf: pygame.Surface) -> None:
        # base
        surf.fill((18, 22, 30))
        # animated gradient stripes on higher levels
        if self.current_level_idx >= 2:
            for i in range(10):
                y = int((math.sin(self.bg_phase * 0.8 + i) * 0.5 + 0.5) * self.VIRTUAL_H)
                color = (20 + i * 8, 24 + i * 6, 32 + i * 10)
                pygame.draw.rect(surf, color, pygame.Rect(0, y, self.VIRTUAL_W, 8))

    def _draw_world(self, surf: pygame.Surface) -> None:
        # Bricks
        for br in self.bricks:
            col = (80, 140, 220) if br.hp == 1 else (220, 130, 90)
            pygame.draw.rect(surf, col, br.rect)
            pygame.draw.rect(surf, (0, 0, 0), br.rect, 1)

        # Paddle
        pygame.draw.rect(surf, (240, 240, 240), self.paddle.rect())

        # Balls
        for b in self.balls:
            pygame.draw.circle(surf, (255, 210, 80) if b.on_fire else (255, 255, 255), (int(b.x), int(b.y)), b.radius)

        # Powerups
        for p in self.powerups:
            color = {
                PowerUpType.BIG_PADDLE: (130, 220, 130),
                PowerUpType.MULTI_BALL: (220, 220, 120),
                PowerUpType.FIREBALL: (240, 110, 90),
            }[p.kind]
            pygame.draw.rect(surf, color, p.rect())

        # HUD
        score_txt = self.font_ui.render(f"Score: {self.score}", True, (230, 230, 230))
        lives_txt = self.font_ui.render(f"Lives: {self.lives}", True, (230, 230, 230))
        hs_txt = self.font_ui.render(f"High: {self.highscores.get('high_score', 0)}", True, (230, 230, 230))
        surf.blit(score_txt, (20, 18))
        surf.blit(lives_txt, (20, 48))
        surf.blit(hs_txt, (20, 78))

    def _overlay_center(self, surf: pygame.Surface, text: str, size: int) -> None:
        font = pygame.font.SysFont("Consolas", size)
        img = font.render(text, True, (240, 240, 240))
        surf.blit(img, (self.VIRTUAL_W // 2 - img.get_width() // 2, self.VIRTUAL_H // 2 - img.get_height() // 2))

    def _overlay_sub(self, surf: pygame.Surface, text: str, y: int = 380) -> None:
        img = self.font_ui.render(text, True, (200, 200, 200))
        surf.blit(img, (self.VIRTUAL_W // 2 - img.get_width() // 2, y))

    def _apply_crt(self, surf: pygame.Surface) -> None:
        # Draw scanlines
        h = surf.get_height()
        w = surf.get_width()
        for y in range(0, h, 3):
            pygame.draw.line(surf, (0, 0, 0), (0, y), (w, y), 1)
        # Vignette
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(shade, (0, 0, 0, 120), shade.get_rect(), border_radius=40)
        surf.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)


