"""
Retro Pong Championship - Embedded Pygame engine for PyQt wrapper.

Key design:
- No pygame window is created. We render onto a pygame.Surface supplied by the
  wrapper which is converted to a QImage for display inside the app.
- Controller + keyboard input are polled each frame using pygame.joystick and
  pygame.key without running a separate SDL event loop.

Adjustments and extension points (search for the tags below):
- [PHYSICS] Change ball speed/accel, spin, bounce angle clamp.
- [MODES]  Add new modes by extending GameMode and swapping in self.mode.
- [BINDINGS] Change controller/keyboard bindings in ControllerState.update().
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Tuple

import pygame


VIRTUAL_W, VIRTUAL_H = 1280, 720


@dataclass
class Settings:
    ball_speed: float = 520.0
    paddle_h: int = 140
    best_of: int = 5  # best-of-X games (odd numbers recommended)
    crt_enabled: bool = True


class ControllerState:
    """Polls 0-2 Xbox controllers. Provides keyboard fallback.

    Player 1 keys: W/S for move, Space=Start, C toggle CRT
    Player 2 keys: Up/Down for move, RightCtrl=Start

    [BINDINGS] Change mappings here safely.
    """

    def __init__(self) -> None:
        pygame.joystick.init()
        self.joys = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self.joys.append(j)
        self.p1 = {"up": False, "down": False, "start": False}
        self.p2 = {"up": False, "down": False, "start": False}
        self.toggle_crt = False

    def update(self) -> None:
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        def map_player(idx: int, up_k: int, down_k: int, start_k: int):
            up = keys[up_k]
            down = keys[down_k]
            start = keys[start_k]
            if idx - 1 < len(self.joys):
                joy = self.joys[idx - 1]
                try:
                    axis_y = joy.get_axis(1)
                    hat = joy.get_hat(0) if joy.get_numhats() > 0 else (0, 0)
                    up = up or axis_y < -0.4 or hat[1] > 0
                    down = down or axis_y > 0.4 or hat[1] < 0
                    start = start or bool(joy.get_button(7))  # START
                except Exception:
                    pass
            return {"up": up, "down": down, "start": start}

        self.p1 = map_player(1, pygame.K_w, pygame.K_s, pygame.K_SPACE)
        self.p2 = map_player(2, pygame.K_UP, pygame.K_DOWN, pygame.K_RCTRL)
        self.toggle_crt = keys[pygame.K_c]


class GameMode:
    """Base mode abstraction to allow future variants. [MODES]
    Extend this to implement power-ups, multi-balls, etc.
    """

    def update_ball(self, game: "RetroPong", dt: float) -> None:
        # Default pong physics
        game.ball_x += game.ball_vx * dt
        game.ball_y += game.ball_vy * dt

        # Top/bottom walls
        if game.ball_y <= 10:
            game.ball_y = 10
            game.ball_vy *= -1
        if game.ball_y >= game.h - 10:
            game.ball_y = game.h - 10
            game.ball_vy *= -1

        # Paddles
        if game.ball_vx < 0 and game.ball_x - 10 <= 50 and abs(game.ball_y - game.p1_y) <= game.paddle_h / 2 + 10:
            game.ball_x = 50 + 10
            self._bounce_from_paddle(game, 1)
        elif game.ball_vx > 0 and game.ball_x + 10 >= game.w - 50 and abs(game.ball_y - game.p2_y) <= game.paddle_h / 2 + 10:
            game.ball_x = game.w - 50 - 10
            self._bounce_from_paddle(game, 2)

    def _bounce_from_paddle(self, game: "RetroPong", paddle_idx: int) -> None:
        # [PHYSICS] Spin & angle control based on impact point
        offset = (game.ball_y - (game.p1_y if paddle_idx == 1 else game.p2_y))
        norm = max(-1.0, min(1.0, offset / (game.paddle_h / 2)))
        angle = norm * math.radians(50)  # clamp bounce angle
        speed = math.hypot(game.ball_vx, game.ball_vy) * 1.05  # small accel
        speed = min(speed, game.settings.ball_speed * 1.7)
        direction = 1 if paddle_idx == 1 else -1
        game.ball_vx = math.cos(angle) * speed * direction
        game.ball_vy = math.sin(angle) * speed


class RetroPong:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        pygame.init()
        pygame.font.init()
        self.settings = settings or Settings()
        self.mode: GameMode = GameMode()
        self.controller = ControllerState()
        self.font = pygame.font.SysFont("Press Start 2P, Consolas, Monospace", 24)
        self.big_font = pygame.font.SysFont("Press Start 2P, Consolas, Monospace", 42)

        self.w, self.h = VIRTUAL_W, VIRTUAL_H
        self.state = "menu"  # menu, playing, game_over
        self.reset_match()

    def reset_match(self) -> None:
        self.score1 = 0
        self.score2 = 0
        self.wins1 = 0
        self.wins2 = 0
        self.start_round()

    def start_round(self) -> None:
        self.paddle_h = self.settings.paddle_h
        self.ball_x, self.ball_y = self.w // 2, self.h // 2
        angle = random.uniform(-0.4, 0.4)
        speed = self.settings.ball_speed
        direction = random.choice([-1, 1])
        self.ball_vx = math.cos(angle) * speed * direction
        self.ball_vy = math.sin(angle) * speed
        self.p1_y = self.h // 2
        self.p2_y = self.h // 2
        self.state = "playing"

    # ---------- Core loop called from Qt wrapper ----------
    def resize(self, w: int, h: int) -> None:
        self.w, self.h = max(640, w), max(360, h)

    def update(self, dt: float) -> None:
        self.controller.update()

        if self.controller.toggle_crt:
            self.settings.crt_enabled = not self.settings.crt_enabled

        if self.state == "menu":
            if self.controller.p1["start"] or self.controller.p2["start"]:
                self.reset_match()
                self.state = "playing"
            return

        if self.state == "game_over":
            if self.controller.p1["start"] or self.controller.p2["start"]:
                self.state = "menu"
            return

        # Playing
        p_speed = 600.0
        if self.controller.p1["up"]:
            self.p1_y -= p_speed * dt
        if self.controller.p1["down"]:
            self.p1_y += p_speed * dt
        if self.controller.p2["up"]:
            self.p2_y -= p_speed * dt
        if self.controller.p2["down"]:
            self.p2_y += p_speed * dt

        self.p1_y = max(self.paddle_h/2, min(self.h - self.paddle_h/2, self.p1_y))
        self.p2_y = max(self.paddle_h/2, min(self.h - self.paddle_h/2, self.p2_y))

        self.mode.update_ball(self, dt)

        # Scoring
        if self.ball_x < -15:
            self.score2 += 1
            self._after_point()
        elif self.ball_x > self.w + 15:
            self.score1 += 1
            self._after_point()

    def _after_point(self) -> None:
        # Win game condition
        target = (self.settings.best_of // 2) + 1
        if self.score1 >= 11 and self.score1 - self.score2 >= 2:
            self.wins1 += 1
            self.score1 = self.score2 = 0
        if self.score2 >= 11 and self.score2 - self.score1 >= 2:
            self.wins2 += 1
            self.score1 = self.score2 = 0

        if self.wins1 >= target or self.wins2 >= target:
            self.state = "game_over"
        else:
            self.start_round()

    def render(self, target: pygame.Surface) -> None:
        # Render to virtual surface then scale to target
        vs = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        vs.fill((12, 12, 16))

        if self.state == "menu":
            self._draw_menu(vs)
        elif self.state == "playing":
            self._draw_playfield(vs)
        elif self.state == "game_over":
            self._draw_game_over(vs)

        if self.settings.crt_enabled:
            self._apply_crt(vs)

        pygame.transform.smoothscale(vs, target.get_size(), target)

    # ---------- Drawing helpers ----------
    def _draw_menu(self, surf: pygame.Surface) -> None:
        title = self.big_font.render("Retro Pong Championship", True, (240, 240, 240))
        hint = self.font.render("Press Start/Space/RightCtrl to Play", True, (200, 200, 200))
        settings = [
            f"Ball Speed: {int(self.settings.ball_speed)}",
            f"Paddle Size: {int(self.settings.paddle_h)}",
            f"Best of: {self.settings.best_of}",
            f"CRT: {'On' if self.settings.crt_enabled else 'Off'} (press C)",
        ]
        surf.blit(title, (VIRTUAL_W//2 - title.get_width()//2, 200))
        surf.blit(hint, (VIRTUAL_W//2 - hint.get_width()//2, 260))
        for i, line in enumerate(settings):
            txt = self.font.render(line, True, (190, 190, 190))
            surf.blit(txt, (VIRTUAL_W//2 - txt.get_width()//2, 320 + i*34))

    def _draw_playfield(self, surf: pygame.Surface) -> None:
        # Middle net
        for y in range(20, VIRTUAL_H, 40):
            pygame.draw.rect(surf, (220, 220, 220), pygame.Rect(VIRTUAL_W//2 - 4, y, 8, 24))

        # Scores and wins
        s1 = self.big_font.render(str(self.score1), True, (230, 230, 230))
        s2 = self.big_font.render(str(self.score2), True, (230, 230, 230))
        surf.blit(s1, (VIRTUAL_W//2 - 80 - s1.get_width(), 20))
        surf.blit(s2, (VIRTUAL_W//2 + 80, 20))
        w1 = self.font.render(f"Wins: {self.wins1}", True, (180, 180, 180))
        w2 = self.font.render(f"Wins: {self.wins2}", True, (180, 180, 180))
        surf.blit(w1, (40, 20))
        surf.blit(w2, (VIRTUAL_W - 40 - w2.get_width(), 20))

        # Paddles & ball
        pygame.draw.rect(surf, (210, 210, 210), pygame.Rect(40, int(self.p1_y - self.paddle_h/2), 20, int(self.paddle_h)))
        pygame.draw.rect(surf, (210, 210, 210), pygame.Rect(VIRTUAL_W-60, int(self.p2_y - self.paddle_h/2), 20, int(self.paddle_h)))
        pygame.draw.circle(surf, (230, 230, 230), (int(self.ball_x * VIRTUAL_W / self.w), int(self.ball_y * VIRTUAL_H / self.h)), 10)

    def _draw_game_over(self, surf: pygame.Surface) -> None:
        winner = "Player 1" if self.wins1 > self.wins2 else "Player 2"
        title = self.big_font.render(f"{winner} Wins!", True, (255, 210, 120))
        hint = self.font.render("Press Start to Return to Menu", True, (200, 200, 200))
        surf.blit(title, (VIRTUAL_W//2 - title.get_width()//2, 260))
        surf.blit(hint, (VIRTUAL_W//2 - hint.get_width()//2, 320))

    def _apply_crt(self, surf: pygame.Surface) -> None:
        # Scanlines
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        for y in range(0, VIRTUAL_H, 2):
            pygame.draw.line(overlay, (0, 0, 0, 40), (0, y), (VIRTUAL_W, y))
        # Vignette
        vign = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        pygame.draw.rect(vign, (0, 0, 0, 140), pygame.Rect(0, 0, VIRTUAL_W, VIRTUAL_H), border_radius=80)
        surf.blit(overlay, (0, 0))
        surf.blit(vign, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    # ---------- Settings API for PyQt wrapper ----------
    def set_ball_speed(self, v: float) -> None:
        self.settings.ball_speed = max(200.0, min(1000.0, float(v)))

    def set_paddle_h(self, v: int) -> None:
        self.settings.paddle_h = max(60, min(260, int(v)))

    def set_best_of(self, v: int) -> None:
        self.settings.best_of = max(1, int(v))

    def set_crt(self, enabled: bool) -> None:
        self.settings.crt_enabled = bool(enabled)


