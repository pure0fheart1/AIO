from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pygame


@dataclass
class PadState:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False
    start: bool = False


class Input:
    """Keyboard + basic Xbox mapping for two players."""

    def __init__(self) -> None:
        pygame.joystick.init()
        self.joys = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self.joys.append(j)

    def read_player(self, idx: int) -> PadState:
        pygame.event.pump()
        k = pygame.key.get_pressed()
        if idx == 1:
            ps = PadState(
                up=k[pygame.K_w] or k[pygame.K_UP],
                down=k[pygame.K_s] or k[pygame.K_DOWN],
                left=k[pygame.K_a] or k[pygame.K_LEFT],
                right=k[pygame.K_d] or k[pygame.K_RIGHT],
                a=k[pygame.K_SPACE] or k[pygame.K_RETURN],
                b=k[pygame.K_LSHIFT],
                x=k[pygame.K_q],
                y=k[pygame.K_e],
                start=k[pygame.K_RETURN],
            )
        else:
            ps = PadState(
                up=k[pygame.K_i], down=k[pygame.K_k], left=k[pygame.K_j], right=k[pygame.K_l],
                a=k[pygame.K_KP0], b=k[pygame.K_KP1], x=k[pygame.K_KP2], y=k[pygame.K_KP3], start=k[pygame.K_RCTRL]
            )

        # Merge with controller if available
        if idx - 1 < len(self.joys):
            j = self.joys[idx - 1]
            try:
                ax0 = j.get_axis(0)
                ax1 = j.get_axis(1)
                hat = j.get_hat(0) if j.get_numhats() > 0 else (0, 0)
                ps.left = ps.left or ax0 < -0.4 or hat[0] < 0
                ps.right = ps.right or ax0 > 0.4 or hat[0] > 0
                ps.up = ps.up or ax1 < -0.5 or hat[1] > 0
                ps.down = ps.down or ax1 > 0.5 or hat[1] < 0
                ps.a = ps.a or bool(j.get_button(0))
                ps.b = ps.b or bool(j.get_button(1))
                ps.x = ps.x or bool(j.get_button(2))
                ps.y = ps.y or bool(j.get_button(3))
                ps.start = ps.start or bool(j.get_button(7))
            except Exception:
                pass
        return ps


