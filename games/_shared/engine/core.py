from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

import pygame


INTERNAL_W, INTERNAL_H = 320, 180


class Scene(Protocol):
    def on_enter(self, ctx: "GameContext") -> None: ...
    def handle_event(self, evt: pygame.event.Event) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surf: pygame.Surface) -> None: ...
    def on_exit(self) -> None: ...


@dataclass
class GameContext:
    screen: pygame.Surface
    internal: pygame.Surface
    clock: pygame.time.Clock
    scale: int


class SceneStack:
    def __init__(self) -> None:
        self.stack: List[Scene] = []
        self.ctx: Optional[GameContext] = None

    def set_context(self, ctx: GameContext) -> None:
        self.ctx = ctx

    def push(self, scene: Scene) -> None:
        assert self.ctx is not None, "Context not set"
        self.stack.append(scene)
        scene.on_enter(self.ctx)

    def pop(self) -> None:
        if not self.stack:
            return
        scene = self.stack.pop()
        scene.on_exit()

    def top(self) -> Optional[Scene]:
        return self.stack[-1] if self.stack else None


