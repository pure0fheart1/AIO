from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Dict, Tuple

import pygame

from .core import Scene, GameContext, INTERNAL_W, INTERNAL_H
from .entities import Entity, aabb_overlap


@dataclass
class MGConfig:
    title: str = "Microgame"
    seed: int = 1337
    player_speed: float = 90.0
    player_size: Tuple[int, int] = (8, 8)
    lives: int = 3
    score_per_second: int = 10
    hazard_speed: float = 50.0
    hazard_spawn_rate: float = 1.0  # per second
    hazard_size: Tuple[int, int] = (8, 8)
    ramp_every_sec: float = 25.0
    ramp_mul: float = 1.15
    palette_bg: Tuple[int, int, int] = (20, 20, 30)
    palette_player: Tuple[int, int, int] = (240, 240, 240)
    palette_hazard: Tuple[int, int, int] = (255, 100, 100)


def load_config(path: str, title: str) -> MGConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Dict = json.load(f)
    except Exception:
        data = {}
    cfg = MGConfig(title=title)
    for k, v in data.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


class MicroGameScene(Scene):
    def __init__(self, title: str, cfg_path: str, save_dir: str) -> None:
        self.title = title
        self.cfg = load_config(cfg_path, title)
        random.seed(self.cfg.seed)
        self.ctx: GameContext | None = None
        w, h = self.cfg.player_size
        self.player = Entity(INTERNAL_W // 2 - w // 2, INTERNAL_H // 2 - h // 2, w=w, h=h)
        self.hazards: list[Entity] = []
        self.spawn_acc = 0.0
        self.score = 0
        self.lives = self.cfg.lives
        self.elapsed = 0.0
        self.state = "title"  # title, play, gameover
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.high_path = os.path.join(save_dir, "highscores.json")
        self.high = self._load_high()

    # --------------- persistence ---------------
    def _load_high(self) -> int:
        try:
            with open(self.high_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return int(data.get("high", 0))
        except Exception:
            return 0

    def _save_high(self) -> None:
        try:
            with open(self.high_path, "w", encoding="utf-8") as f:
                json.dump({"high": int(self.high)}, f)
        except Exception:
            pass

    # --------------- lifecycle ---------------
    def on_enter(self, ctx: GameContext) -> None:
        self.ctx = ctx

    def handle_event(self, evt: pygame.event.Event) -> None:
        if evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            if evt.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.state in ("title", "gameover"):
                    self.reset()
                    self.state = "play"
            if evt.key == pygame.K_r and self.state == "play":
                self.reset()
                self.state = "play"

    def reset(self) -> None:
        self.hazards.clear()
        self.spawn_acc = 0.0
        w, h = self.cfg.player_size
        self.player.x = INTERNAL_W // 2 - w // 2
        self.player.y = INTERNAL_H // 2 - h // 2
        self.player.vx = self.player.vy = 0.0
        self.score = 0
        self.lives = self.cfg.lives
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        if self.state != "play":
            return
        self.elapsed += dt
        # difficulty ramp
        ramp = 1.0 + int(self.elapsed // self.cfg.ramp_every_sec) * (self.cfg.ramp_mul - 1.0)

        # input
        keys = pygame.key.get_pressed()
        sp = self.cfg.player_speed
        self.player.vx = (keys[pygame.K_d] or keys[pygame.K_RIGHT] - (keys[pygame.K_a] or keys[pygame.K_LEFT])) * sp
        self.player.vy = (keys[pygame.K_s] or keys[pygame.K_DOWN] - (keys[pygame.K_w] or keys[pygame.K_UP])) * sp
        self.player.update(dt)
        # clamp
        self.player.x = max(0, min(INTERNAL_W - self.player.w, self.player.x))
        self.player.y = max(0, min(INTERNAL_H - self.player.h, self.player.y))

        # hazards spawn
        self.spawn_acc += dt * self.cfg.hazard_spawn_rate * ramp
        while self.spawn_acc >= 1.0:
            self.spawn_acc -= 1.0
            hw, hh = self.cfg.hazard_size
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                x, y, vx, vy = random.randint(0, INTERNAL_W - hw), -hh, 0, self.cfg.hazard_speed * ramp
            elif side == "bottom":
                x, y, vx, vy = random.randint(0, INTERNAL_W - hw), INTERNAL_H + 1, 0, -self.cfg.hazard_speed * ramp
            elif side == "left":
                x, y, vx, vy = -hw, random.randint(0, INTERNAL_H - hh), self.cfg.hazard_speed * ramp, 0
            else:
                x, y, vx, vy = INTERNAL_W + 1, random.randint(0, INTERNAL_H - hh), -self.cfg.hazard_speed * ramp, 0
            self.hazards.append(Entity(x, y, vx=vx, vy=vy, w=hw, h=hh))

        # hazards update
        for hz in self.hazards:
            hz.update(dt)
        self.hazards = [h for h in self.hazards if -20 <= h.x <= INTERNAL_W + 20 and -20 <= h.y <= INTERNAL_H + 20]

        # collisions
        for hz in self.hazards:
            if aabb_overlap(self.player, hz):
                self.lives -= 1
                self.hazards.remove(hz)
                if self.lives <= 0:
                    self.state = "gameover"
                    if self.score > self.high:
                        self.high = self.score
                        self._save_high()
                break

        # scoring
        self.score += int(self.cfg.score_per_second * dt)

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(self.cfg.palette_bg)
        # player
        self.player.draw(surf, self.cfg.palette_player)
        # hazards
        for hz in self.hazards:
            hz.draw(surf, self.cfg.palette_hazard)

        # HUD
        font = pygame.font.SysFont("Consolas, Monospace", 8)
        hud = font.render(f"{self.title}  Score:{self.score}  Lives:{self.lives}  High:{self.high}", True, (255, 255, 255))
        surf.blit(hud, (4, 4))

        if self.state in ("title", "gameover"):
            big = pygame.font.SysFont("Consolas, Monospace", 16)
            txt = "Press Enter to Start" if self.state == "title" else "Game Over - Press Enter"
            timg = big.render(txt, True, (255, 255, 0))
            surf.blit(timg, (INTERNAL_W // 2 - timg.get_width() // 2, INTERNAL_H // 2 - 8))

    def on_exit(self) -> None:
        pass


def create_game(title: str, cfg_path: str, save_dir: str) -> MicroGameScene:
    return MicroGameScene(title=title, cfg_path=cfg_path, save_dir=save_dir)


