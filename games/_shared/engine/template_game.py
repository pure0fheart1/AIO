from __future__ import annotations

import pygame
from .core import Scene, GameContext
from .entities import Entity


class TemplateGame(Scene):
    def __init__(self) -> None:
        self.ctx: GameContext | None = None
        self.player = Entity(150, 90, w=8, h=8)
        self.paused = False

    def on_enter(self, ctx: GameContext) -> None:
        self.ctx = ctx

    def handle_event(self, evt: pygame.event.Event) -> None:
        if evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            if evt.key == pygame.K_p:
                self.paused = not self.paused

    def update(self, dt: float) -> None:
        if self.paused:
            return
        keys = pygame.key.get_pressed()
        speed = 80
        self.player.vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed
        self.player.vy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed
        self.player.update(dt)

    def draw(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(surf, (20, 20, 40), surf.get_rect())
        self.player.draw(surf)
        # HUD
        pygame.draw.rect(surf, (255, 255, 255), pygame.Rect(2, 2, 100, 10), 1)

    def on_exit(self) -> None:
        pass


