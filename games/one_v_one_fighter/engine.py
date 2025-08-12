"""
Lightweight 1v1 fighting game engine rendered with pygame surfaces.

Design goals
- No pygame display/window is created. Rendering is done to a pygame.Surface
  which the Qt wrapper converts to a QImage for on-screen display. This avoids
  SDL window embedding issues and keeps the main Qt event loop responsive.

Controls (Xbox controller + Keyboard fallbacks)
- Player 1: Left stick/D-Pad to move, A=Light, X=Heavy, B=Special, RB=Block, Start=Pause
  Keyboard fallback: A/D=Left/Right, W=Jump, S=Crouch, J=Light, K=Heavy, L=Special, I=Block, Enter=Pause
- Player 2: Right stick/D-Pad on second controller, A/X/B/RB, Start
  Keyboard fallback: Left/Right=Left/Right, Up=Jump, Down=Crouch,
                     Num1=Light, Num2=Heavy, Num3=Special, Num5=Block, RightCtrl=Pause

How to extend
- To add a new move, create a MoveSpec and add it in PlayerController._handle_attack.
- To change button bindings, edit ControllerState.update() mappings.
- To change characters/backgrounds, modify SpriteFactory to load custom assets
  (or generated placeholders) and update Player initialization in FightScene.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import pygame


# ---------------------- Data structures ----------------------

@dataclass
class MoveSpec:
    name: str
    startup_frames: int
    active_frames: int
    recovery_frames: int
    damage: int
    knockback: Tuple[float, float]
    hitbox: pygame.Rect  # Hitbox relative to player origin


@dataclass
class PlayerState:
    health: int = 100
    stock_rounds_won: int = 0
    facing: int = 1  # 1 right, -1 left
    on_ground: bool = True
    is_blocking: bool = False
    is_crouching: bool = False
    is_jumping: bool = False
    vx: float = 0.0
    vy: float = 0.0
    combo_counter: int = 0
    hitstun_frames: int = 0
    ko: bool = False
    current_move: Optional[MoveSpec] = None
    move_frame: int = 0


class ControllerState:
    """Polls keyboard and up to two Xbox controllers via pygame.joystick.

    This component intentionally uses polling (not event queue) to avoid
    impacting the Qt event loop with window events from pygame.
    """

    def __init__(self) -> None:
        pygame.joystick.init()
        self.joys: List[pygame.joystick.Joystick] = []
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self.joys.append(joy)

        # Cached per-player input snapshot
        self.players: Dict[int, Dict[str, bool | float]] = {1: {}, 2: {}}

    def update(self) -> None:
        pygame.event.pump()  # Required to refresh joystick state
        keys = pygame.key.get_pressed()

        def map_player(idx: int, keymap: Dict[str, int]) -> Dict[str, bool | float]:
            joy: Optional[pygame.joystick.Joystick] = None
            if idx - 1 < len(self.joys):
                joy = self.joys[idx - 1]

            axis_x = 0.0
            axis_y = 0.0
            btn_a = btn_b = btn_x = btn_rb = btn_start = False
            dpad_left = dpad_right = dpad_up = dpad_down = False

            if joy is not None:
                try:
                    axis_x = joy.get_axis(0)
                    axis_y = joy.get_axis(1)
                    btn_a = bool(joy.get_button(0))
                    btn_b = bool(joy.get_button(1))
                    btn_x = bool(joy.get_button(2))
                    btn_rb = bool(joy.get_button(5))
                    btn_start = bool(joy.get_button(7))
                    hat = joy.get_hat(0) if joy.get_numhats() > 0 else (0, 0)
                    dpad_left = hat[0] < 0
                    dpad_right = hat[0] > 0
                    dpad_up = hat[1] > 0
                    dpad_down = hat[1] < 0
                except Exception:
                    pass

            left = axis_x < -0.4 or keys[keymap['left']] or dpad_left
            right = axis_x > 0.4 or keys[keymap['right']] or dpad_right
            up = axis_y < -0.5 or keys[keymap['up']] or dpad_up
            down = axis_y > 0.5 or keys[keymap['down']] or dpad_down

            light = btn_a or keys[keymap['light']]
            heavy = btn_x or keys[keymap['heavy']]
            special = btn_b or keys[keymap['special']]
            block = btn_rb or keys[keymap['block']]
            pause = btn_start or keys[keymap['pause']]

            return {
                'left': left, 'right': right, 'up': up, 'down': down,
                'light': light, 'heavy': heavy, 'special': special,
                'block': block, 'pause': pause,
            }

        p1 = map_player(1, {
            'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w, 'down': pygame.K_s,
            'light': pygame.K_j, 'heavy': pygame.K_k, 'special': pygame.K_l,
            'block': pygame.K_i, 'pause': pygame.K_RETURN,
        })
        p2 = map_player(2, {
            'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP, 'down': pygame.K_DOWN,
            'light': pygame.K_KP1, 'heavy': pygame.K_KP2, 'special': pygame.K_KP3,
            'block': pygame.K_KP5, 'pause': pygame.K_RCTRL,
        })
        self.players[1] = p1
        self.players[2] = p2

    def get_player(self, idx: int) -> Dict[str, bool | float]:
        return self.players[idx]


class SpriteFactory:
    """Creates placeholder sprites and backgrounds at runtime.

    Replace these with loaded images if you add real assets later. The aspect
    ratio is kept consistent with the internal virtual resolution.
    """

    def __init__(self) -> None:
        self.font = pygame.font.SysFont('Consolas', 20)

    def player_sprite(self, color: Tuple[int, int, int]) -> pygame.Surface:
        surf = pygame.Surface((80, 120), pygame.SRCALPHA)
        pygame.draw.rect(surf, color, pygame.Rect(0, 20, 80, 100), border_radius=6)
        pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(20, 0, 40, 30), border_radius=6)
        return surf

    def background(self, size: Tuple[int, int]) -> pygame.Surface:
        w, h = size
        surf = pygame.Surface((w, h))
        surf.fill((30, 36, 48))
        for i in range(0, w, 40):
            pygame.draw.line(surf, (40, 46, 60), (i, 0), (i, h))
        for j in range(0, h, 40):
            pygame.draw.line(surf, (40, 46, 60), (0, j), (w, j))
        title = self.font.render('1v1 Fighter (placeholder art)', True, (200, 200, 200))
        surf.blit(title, (10, 10))
        return surf

    def text(self, s: str, color=(230, 230, 230)) -> pygame.Surface:
        return self.font.render(s, True, color)


class Player:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        self.state = PlayerState()
        self.x = x
        self.y = y
        self.width = 60
        self.height = 110
        self.color = color
        self.sprite_factory = SpriteFactory()
        self.sprite = self.sprite_factory.player_sprite(color)

        # Define core moves with simple rectangle hitboxes
        self.moves: Dict[str, MoveSpec] = {
            'light': MoveSpec('light', 4, 6, 10, 6, (4.0, -1.0), pygame.Rect(50, 20, 40, 30)),
            'heavy': MoveSpec('heavy', 8, 6, 16, 12, (8.0, -3.0), pygame.Rect(55, 10, 55, 40)),
            'special': MoveSpec('special', 10, 10, 18, 18, (11.0, -5.0), pygame.Rect(60, -5, 60, 50)),
        }

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y) - self.height, self.width, self.height)

    def get_world_hitbox(self) -> Optional[pygame.Rect]:
        if not self.state.current_move:
            return None
        hb = self.state.current_move.hitbox.copy()
        # Mirror hitbox when facing left
        if self.state.facing == -1:
            hb.x = -hb.x - hb.width
        hb.x += int(self.x + (self.width // 2))
        hb.y += int(self.y) - self.height
        return hb


class FightScene:
    VIRTUAL_W = 1280
    VIRTUAL_H = 720
    GROUND_Y = 620

    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.controller = ControllerState()
        self.sprites = SpriteFactory()
        self.bg = self.sprites.background((self.VIRTUAL_W, self.VIRTUAL_H))
        self.clock = pygame.time.Clock()
        self.round_time = 60  # seconds per round
        self.time_left = self.round_time
        self.round_over = False
        self.best_of = 3
        self.winner_text: Optional[str] = None
        self.paused = False

        self.player1 = Player(400, self.GROUND_Y, (50, 160, 255))
        self.player2 = Player(880, self.GROUND_Y, (255, 110, 80))
        self.player2.state.facing = -1

    # --------------- Core loop interface used by Qt wrapper ---------------
    def update(self, dt: float) -> None:
        if self.paused:
            self.controller.update()
            if self.controller.get_player(1)['pause'] or self.controller.get_player(2)['pause']:
                self.paused = False
            return

        self.clock.tick()  # maintain internal tick for joystick stability
        self.controller.update()
        self._update_timer(dt)
        self._apply_inputs(self.player1, self.controller.get_player(1))
        self._apply_inputs(self.player2, self.controller.get_player(2))
        self._apply_physics(self.player1, dt)
        self._apply_physics(self.player2, dt)
        self._handle_facing()
        self._handle_attacks_and_hitstun()

    def render(self, surface: pygame.Surface) -> None:
        # Draw to an internal virtual surface then scale to target for crispness
        vsurf = pygame.Surface((self.VIRTUAL_W, self.VIRTUAL_H))
        vsurf.blit(self.bg, (0, 0))
        self._draw_hud(vsurf)
        self._draw_player(vsurf, self.player1)
        self._draw_player(vsurf, self.player2)

        if self.round_over and self.winner_text:
            banner = self.sprites.text(self.winner_text, (255, 200, 100))
            vsurf.blit(banner, (self.VIRTUAL_W // 2 - banner.get_width() // 2, 200))

        if self.paused:
            shade = pygame.Surface((self.VIRTUAL_W, self.VIRTUAL_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            vsurf.blit(shade, (0, 0))
            vsurf.blit(self.sprites.text("Paused - Start/Enter to Resume", (240, 240, 240)), (440, 320))
            vsurf.blit(self.sprites.text("R: Restart  |  Esc: Back to App", (240, 240, 240)), (440, 360))

        pygame.transform.smoothscale(vsurf, surface.get_size(), surface)

    # --------------- Input / Physics / Combat ----------------
    def _apply_inputs(self, player: Player, inp: Dict[str, bool | float]) -> None:
        if player.state.ko:
            return

        # Pause
        if inp['pause']:
            self.paused = True

        # Movement
        speed = 320.0
        if player.state.hitstun_frames > 0 or player.state.current_move is not None:
            move_x = 0.0
        else:
            move_x = (-1.0 if inp['left'] else 0.0) + (1.0 if inp['right'] else 0.0)
        player.state.vx = move_x * speed

        # Jump / crouch
        if inp['up'] and player.state.on_ground and not player.state.is_jumping:
            player.state.vy = -650.0
            player.state.on_ground = False
            player.state.is_jumping = True
        player.state.is_crouching = bool(inp['down'] and player.state.on_ground)

        # Block
        player.state.is_blocking = bool(inp['block'] and player.state.on_ground and player.state.current_move is None)

        # Attacks
        if player.state.current_move is None and player.state.hitstun_frames == 0 and not player.state.is_blocking:
            if inp['light']:
                player.state.current_move = player.moves['light']
                player.state.move_frame = 0
            elif inp['heavy']:
                player.state.current_move = player.moves['heavy']
                player.state.move_frame = 0
            elif inp['special']:
                # Simple combo: if combo_counter >= 2, special gets +5 damage
                base = player.moves['special']
                dmg = base.damage + (5 if player.state.combo_counter >= 2 else 0)
                player.state.current_move = MoveSpec(base.name, base.startup_frames, base.active_frames,
                                                    base.recovery_frames, dmg, base.knockback, base.hitbox)
                player.state.move_frame = 0

    def _apply_physics(self, player: Player, dt: float) -> None:
        # Gravity
        if not player.state.on_ground:
            player.state.vy += 1800.0 * dt
        # Integrate
        player.x += player.state.vx * dt
        player.y += player.state.vy * dt

        # Ground collision
        if player.y >= self.GROUND_Y:
            player.y = self.GROUND_Y
            player.state.on_ground = True
            player.state.is_jumping = False
            player.state.vy = 0.0

        # Side bounds
        player.x = max(60, min(self.VIRTUAL_W - 120, player.x))

        # Update move timing
        if player.state.current_move is not None:
            player.state.move_frame += 1
            total_frames = (player.state.current_move.startup_frames +
                            player.state.current_move.active_frames +
                            player.state.current_move.recovery_frames)
            if player.state.move_frame >= total_frames:
                player.state.current_move = None
                player.state.move_frame = 0

        # Hitstun countdown
        if player.state.hitstun_frames > 0:
            player.state.hitstun_frames -= 1

    def _handle_facing(self) -> None:
        if self.player1.x < self.player2.x:
            self.player1.state.facing = 1
            self.player2.state.facing = -1
        else:
            self.player1.state.facing = -1
            self.player2.state.facing = 1

    def _handle_attacks_and_hitstun(self) -> None:
        if self.round_over:
            return

        for atk_player, def_player in ((self.player1, self.player2), (self.player2, self.player1)):
            move = atk_player.state.current_move
            if move is None:
                continue
            frame = atk_player.state.move_frame
            if frame < move.startup_frames:
                continue
            if frame >= move.startup_frames + move.active_frames:
                continue

            hb = atk_player.get_world_hitbox()
            if hb is None:
                continue
            if hb.colliderect(def_player.rect):
                # Simple block check
                blocked = def_player.state.is_blocking and def_player.state.on_ground
                damage = max(1, move.damage // (3 if blocked else 1))
                def_player.state.health -= damage
                def_player.state.combo_counter = (def_player.state.combo_counter + 1) if not blocked else 0
                kb_x, kb_y = move.knockback
                if blocked:
                    kb_x *= 0.2
                    kb_y *= 0.2
                def_player.state.vx = kb_x * atk_player.state.facing
                def_player.state.vy = kb_y
                def_player.state.on_ground = False
                def_player.state.hitstun_frames = 10 if blocked else 18
                # Prevent multi-hit in the same active frame window
                atk_player.state.move_frame = move.startup_frames + move.active_frames

                if def_player.state.health <= 0:
                    def_player.state.ko = True
                    self.round_over = True
                    self.winner_text = 'KO! Player 1 Wins' if def_player is self.player2 else 'KO! Player 2 Wins'

    def _update_timer(self, dt: float) -> None:
        if self.round_over or self.paused:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.round_over = True
            if self.player1.state.health == self.player2.state.health:
                self.winner_text = 'Time! Draw'
            elif self.player1.state.health > self.player2.state.health:
                self.winner_text = 'Time! Player 1 Wins'
            else:
                self.winner_text = 'Time! Player 2 Wins'

    # --------------- Drawing helpers ----------------
    def _draw_player(self, surf: pygame.Surface, p: Player) -> None:
        # Shadow
        shadow = pygame.Surface((p.width, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 120), shadow.get_rect())
        surf.blit(shadow, (int(p.x) - p.width // 2, self.GROUND_Y - 8))

        # Character
        sprite = pygame.transform.flip(p.sprite, p.state.facing == -1, False)
        surf.blit(sprite, (int(p.x) - 40, int(p.y) - 120))

        # Active hitbox debug (toggle-able if needed)
        if p.state.current_move is not None:
            hb = p.get_world_hitbox()
            if hb:
                pygame.draw.rect(surf, (255, 80, 80), hb, 2)

    def _draw_hud(self, surf: pygame.Surface) -> None:
        # Health bars
        def draw_bar(x: int, y: int, hp: int, color: Tuple[int, int, int]):
            pygame.draw.rect(surf, (60, 60, 60), pygame.Rect(x, y, 460, 28), border_radius=6)
            w = max(0, int(460 * (hp / 100.0)))
            pygame.draw.rect(surf, color, pygame.Rect(x + 2, y + 2, w - 4 if w >= 4 else 0, 24), border_radius=6)

        draw_bar(40, 30, self.player1.state.health, (80, 180, 255))
        draw_bar(self.VIRTUAL_W - 500, 30, self.player2.state.health, (255, 140, 120))

        # Timer
        timer_txt = self.sprites.text(f"{int(max(0, self.time_left))}")
        surf.blit(timer_txt, (self.VIRTUAL_W // 2 - timer_txt.get_width() // 2, 26))

    # --------------- Round / Scene controls --------------
    def restart_round(self) -> None:
        self.player1 = Player(400, self.GROUND_Y, (50, 160, 255))
        self.player2 = Player(880, self.GROUND_Y, (255, 110, 80))
        self.player2.state.facing = -1
        self.time_left = self.round_time
        self.round_over = False
        self.paused = False
        self.winner_text = None


