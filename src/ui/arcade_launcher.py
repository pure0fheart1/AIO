from __future__ import annotations

import os
import subprocess
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout


class ArcadeLauncher(QWidget):
    """Lists games under `games/*/main.py` and launches in a subprocess (simple, reliable)."""

    def __init__(self, project_root: str, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Arcade - Select a game and click Launch"))
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.launch_btn = QPushButton("Launch")
        row.addWidget(self.refresh_btn)
        row.addStretch(1)
        row.addWidget(self.launch_btn)
        layout.addLayout(row)

        self.refresh_btn.clicked.connect(self.refresh)
        self.launch_btn.clicked.connect(self.launch)

        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        games_dir = os.path.join(self.project_root, 'games')
        for name in sorted(os.listdir(games_dir)):
            if name.startswith('_'):
                continue
            main_py = os.path.join(games_dir, name, 'main.py')
            if os.path.isfile(main_py):
                self.list.addItem(name)

    def launch(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        name = item.text()
        main_py = os.path.join(self.project_root, 'games', name, 'main.py')
        if os.path.isfile(main_py):
            # Launch with system Python to isolate from the Qt loop
            subprocess.Popen(['python', main_py], cwd=self.project_root)


