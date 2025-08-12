from __future__ import annotations

import importlib
import json
import os
from typing import List

from games._shared.engine.runner import run_game
from games._shared.engine.template_game import TemplateGame


ROOT = os.path.dirname(os.path.dirname(__file__))


def list_games() -> List[str]:
    entries = []
    for name in os.listdir(os.path.join(ROOT)):
        if name.startswith('_'):
            continue
        path = os.path.join(ROOT, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, 'main.py')):
            entries.append(name)
    return sorted(entries)


def main() -> None:
    games = list_games()
    print("Retro Microgames Launcher\n---------------------------")
    for i, g in enumerate(games, 1):
        print(f"{i}. {g}")
    try:
        choice = int(input("Select game (number), or 0 for template: "))
    except Exception:
        choice = 0
    if choice <= 0 or choice > len(games):
        run_game(TemplateGame(), "Template Game")
        return
    mod_name = f"games.{games[choice-1]}.main"
    mod = importlib.import_module(mod_name)
    mod.main()


if __name__ == "__main__":
    main()


