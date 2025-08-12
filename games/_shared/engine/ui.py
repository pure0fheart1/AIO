from __future__ import annotations

import pygame


class Label:
    def __init__(self, text: str, font: pygame.font.Font, color=(255, 255, 255)) -> None:
        self.text = text
        self.font = font
        self.color = color

    def draw(self, surf: pygame.Surface, x: int, y: int) -> None:
        img = self.font.render(self.text, True, self.color)
        surf.blit(img, (x, y))


class Button(Label):
    def __init__(self, text: str, font: pygame.font.Font, color=(255, 255, 255)) -> None:
        super().__init__(text, font, color)
        self.hover = False

    def draw(self, surf: pygame.Surface, x: int, y: int) -> pygame.Rect:
        img = self.font.render(self.text, True, (255, 255, 0) if self.hover else self.color)
        rect = img.get_rect(topleft=(x, y))
        surf.blit(img, rect.topleft)
        return rect


