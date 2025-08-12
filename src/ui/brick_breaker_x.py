from __future__ import annotations

import time
from typing import Optional

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

import pygame

from games.brick_breaker_x import BrickBreakerEngine


class BrickBreakerXWidget(QWidget):
    """Qt wrapper that embeds the Brick Breaker X pygame engine.

    The engine renders into an offscreen pygame.Surface. We convert that into a
    QImage every frame and paint it into the widget so it scales with the app.
    """

    def __init__(self, main_window=None) -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.setObjectName("BrickBreakerXWidget")

        self.engine = BrickBreakerEngine()
        self.last_ts = time.perf_counter()
        self.render_surface: Optional[pygame.Surface] = None

        # Top bar controls (Back + Restart)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        controls = QHBoxLayout()
        controls.setContentsMargins(8, 6, 8, 6)
        controls.setSpacing(8)
        self.back_btn = QPushButton("Back to Main")
        self.back_btn.clicked.connect(self._go_back)
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.clicked.connect(self._restart)
        self.crt_btn = QPushButton("Toggle CRT")
        self.crt_btn.clicked.connect(self._toggle_crt)
        controls.addWidget(self.back_btn)
        controls.addWidget(self.restart_btn)
        controls.addWidget(self.crt_btn)
        controls.addStretch(1)

        outer.addLayout(controls)

        # Canvas placeholder (we draw directly on the widget below controls)
        self.canvas_placeholder = QLabel()
        self.canvas_placeholder.setMinimumSize(QSize(400, 300))
        self.canvas_placeholder.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.canvas_placeholder, 1)

        # Frame timer ~60 FPS
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ------------- control handlers ------------
    def _go_back(self) -> None:
        if self.main_window is not None and hasattr(self.main_window, "nav_list"):
            # Go to first page (YouTube Downloader) as a safe default
            self.main_window.nav_list.setCurrentRow(0)

    def _restart(self) -> None:
        self.engine.restart()

    def _toggle_crt(self) -> None:
        self.engine.toggle_crt()

    # ------------- rendering -------------
    def _ensure_surface(self) -> None:
        w = max(64, self.canvas_placeholder.width())
        h = max(64, self.canvas_placeholder.height())
        if self.render_surface is None or self.render_surface.get_width() != w or self.render_surface.get_height() != h:
            self.render_surface = pygame.Surface((w, h))

    def _tick(self) -> None:
        now = time.perf_counter()
        dt = min(0.05, now - self.last_ts)
        self.last_ts = now
        self.engine.update(dt)
        self._ensure_surface()
        if self.render_surface is None:
            return
        self.engine.render(self.render_surface)

        # Convert to QImage
        raw = pygame.image.tostring(self.render_surface, "RGB")
        w, h = self.render_surface.get_size()
        img = QImage(raw, w, h, w * 3, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self.canvas_placeholder.setPixmap(pix)


