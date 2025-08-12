from games._shared.engine.runner import run_game
from games._shared.engine.microgame import create_game
from pathlib import Path


def main():
    base = Path(__file__).parent
    cfg = base / "game" / "data" / "config.json"
    save = base / "save"
    scene = create_game("Neon Runner", str(cfg), str(save))
    run_game(scene, "Neon Runner")


if __name__ == "__main__":
    main()

from games._shared.engine.runner import run_game
from games._shared.engine.microgame import create_game
from pathlib import Path

def main():
    base = Path(__file__).parent
    cfg = base / "game" / "data" / "config.json"
    save = base / "save"
    scene = create_game("Neon Runner", str(cfg), str(save))
    run_game(scene, "Neon Runner")

if __name__ == "__main__":
    main()
