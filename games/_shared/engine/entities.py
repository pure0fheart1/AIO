from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pygame


@dataclass
class Entity:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    w: int = 8
    h: int = 8

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf: pygame.Surface, color=(255, 255, 255)) -> None:
        pygame.draw.rect(surf, color, self.rect())


def aabb_overlap(a: Entity, b: Entity) -> bool:
    return a.rect().colliderect(b.rect())


