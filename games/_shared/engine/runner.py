from __future__ import annotations

import pygame
from .core import INTERNAL_W, INTERNAL_H, Scene, SceneStack, GameContext


def run_game(initial_scene: Scene, window_title: str = "Microgame") -> None:
    pygame.init()
    pygame.display.set_caption(window_title)
    clock = pygame.time.Clock()

    # Integer scale for pixel-perfect
    scale = 4
    screen = pygame.display.set_mode((INTERNAL_W * scale, INTERNAL_H * scale))
    internal = pygame.Surface((INTERNAL_W, INTERNAL_H))

    ctx = GameContext(screen=screen, internal=internal, clock=clock, scale=scale)
    stack = SceneStack()
    stack.set_context(ctx)
    stack.push(initial_scene)

    # Fixed timestep
    target_dt = 1.0 / 60.0
    accumulator = 0.0
    last = pygame.time.get_ticks() / 1000.0

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0
        frame = now - last
        last = now
        accumulator += frame

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
            else:
                top = stack.top()
                if top:
                    top.handle_event(evt)

        top = stack.top()
        while accumulator >= target_dt:
            if top:
                top.update(target_dt)
            accumulator -= target_dt

        if top:
            internal.fill((0, 0, 0))
            top.draw(internal)
        pygame.transform.scale(internal, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


