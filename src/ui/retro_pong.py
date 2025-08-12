from __future__ import annotations

import time
from typing import Optional

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox

import pygame

from games.retro_pong_championship import RetroPong, Settings


class CanvasWidget(QWidget):
    """Dedicated canvas that owns its paintEvent to draw the pygame surface safely."""
    def __init__(self, game: RetroPong, parent=None):
        super().__init__(parent)
        self.game = game
        self.surface = pygame.Surface((1280, 720))

    def paintEvent(self, event):
        painter = QPainter(self)
        # Ensure surface matches current widget size
        if self.surface.get_width() != self.width() or self.surface.get_height() != self.height():
            self.surface = pygame.Surface((max(1, self.width()), max(1, self.height())))
        self.game.render(self.surface)
        raw = pygame.image.tostring(self.surface, 'RGB')
        img = QImage(raw, self.surface.get_width(), self.surface.get_height(), QImage.Format_RGB888)
        painter.drawImage(0, 0, img)


class RetroPongWidget(QWidget):
    """Qt wrapper hosting a pygame-rendered surface inside the app.

    - Renders into an offscreen pygame.Surface and blits to QWidget via QImage
    - Provides minimal settings controls and back button
    - Resizes with the main window and throttles at ~60 FPS using QTimer
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setMouseTracking(True)

        self.game = RetroPong(Settings())
        self.last_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)  # ~60 FPS

        # UI controls bar
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(200, 1000)
        self.speed_slider.setValue(int(self.game.settings.ball_speed))
        self.speed_slider.valueChanged.connect(lambda v: self.game.set_ball_speed(v))

        self.paddle_slider = QSlider(Qt.Horizontal)
        self.paddle_slider.setRange(60, 260)
        self.paddle_slider.setValue(int(self.game.settings.paddle_h))
        self.paddle_slider.valueChanged.connect(lambda v: self.game.set_paddle_h(v))

        self.bestof_slider = QSlider(Qt.Horizontal)
        self.bestof_slider.setRange(1, 9)
        self.bestof_slider.setValue(int(self.game.settings.best_of))
        self.bestof_slider.valueChanged.connect(lambda v: self.game.set_best_of(v))

        self.crt_toggle = QCheckBox("CRT")
        self.crt_toggle.setChecked(self.game.settings.crt_enabled)
        self.crt_toggle.stateChanged.connect(lambda s: self.game.set_crt(s == Qt.Checked))

        self.back_btn = QPushButton("Back to Main Menu")
        self.back_btn.clicked.connect(self._back)

        top = QHBoxLayout()
        top.addWidget(QLabel("Ball Speed"))
        top.addWidget(self.speed_slider)
        top.addWidget(QLabel("Paddle"))
        top.addWidget(self.paddle_slider)
        top.addWidget(QLabel("Best Of"))
        top.addWidget(self.bestof_slider)
        top.addWidget(self.crt_toggle)
        top.addStretch(1)
        top.addWidget(self.back_btn)

        self.canvas = CanvasWidget(self.game, self)
        self.canvas.setMinimumSize(QSize(640, 360))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addWidget(self.canvas, 1)

    # ----- control handlers -----
    def _back(self):
        # Signal parent main window to switch away (assumes parent has switch_to_page)
        parent = self.parent()
        if parent and hasattr(parent, 'switch_to_page') and hasattr(parent, 'downloader_tab'):
            parent.switch_to_page(parent.downloader_tab)

    # ----- rendering -----
    def _tick(self):
        now = time.time()
        dt = min(0.05, now - self.last_time)
        self.last_time = now
        self.game.resize(max(100, self.canvas.width()), max(100, self.canvas.height()))
        self.game.update(dt)
        self.update()  # triggers paintEvent

    def paintEvent(self, event):
        # No painting here; the CanvasWidget handles its own painting.
        super().paintEvent(event)


