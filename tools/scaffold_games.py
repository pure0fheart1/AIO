import json
from pathlib import Path

GAMES = [
    "neon_runner","pixel_pirates","astro_salvage","turbo_tunnelers","sky_squadron",
    "dungeon_dash","metro_brawler","robo_foundry","hyper_hopper","boomerang_blade",
    "volcano_climber","ghost_grid","synthwave_surfer","laser_lasso","space_janitor",
    "comet_courier","rocket_rodeo","byte_breaker","circuit_serpent","tailgun_ace",
    "hover_heist","gumball_gobbler","abyss_diver","time_loop_arena","nano_ninja",
    "meteor_miner","cosmic_cab","pinball_dungeon","street_skater","magnet_mayhem",
    "jetpack_juggler","bubble_blitz","tower_topple","retro_rally","sentry_shift",
    "submarine_sos","pixel_chef","rail_runners","thunder_bots","jungle_joust",
    "quantum_quarry","solar_sailors","mutant_market","rooftop_rumble","circuit_courier",
    "glacier_glide","rocket_rescuers","city_defender","rhythm_rumble","haunted_arcade",
]

ROOT = Path(__file__).resolve().parents[1] / "games"

README_TEMPLATE = """# {TITLE}

- Elevator: {ELEVATOR}
- Core Loop:
  - Dodge hazards, survive, score increases over time
  - Difficulty ramps periodically
- Controls: Arrow/WASD move, Enter/Space start, R restart, Esc quit
- Win/Lose: Survive as long as possible; 0 lives = game over
- Scoring: +{SCORE} per second; high score saved
- Difficulty: ramp every {RAMP}s by x{MUL}
- Entities: Player square, moving hazards
- Level: Single arena (procedural spawns)
- HUD: Title, score, lives, high score
- Audio: placeholder bleeps, retro palette
- Config: see `game/data/config.json`
- MVP:
  - [x] Move player, spawn hazards, collisions
  - [x] Scoring and high score
  - [x] Pause/Restart
- Stretch: power-ups, enemy types, patterns
- Acceptance:
  - Starts <3s; 60 FPS
  - Playable 5 min without exceptions
  - Score increments, game over reachable, restart works
  - High score persists to `save/highscores.json`
"""

MAIN_TEMPLATE = """from games._shared.engine.runner import run_game
from games._shared.engine.microgame import create_game
from pathlib import Path

def main():
    base = Path(__file__).parent
    cfg = base / "game" / "data" / "config.json"
    save = base / "save"
    scene = create_game("{TITLE}", str(cfg), str(save))
    run_game(scene, "{TITLE}")

if __name__ == "__main__":
    main()
"""

TEST_TEMPLATE = """import pygame
from games._shared.engine.microgame import create_game

def test_smoke_120_frames(tmp_path):
    scene = create_game("{TITLE}", str(tmp_path / "config.json"), str(tmp_path))
    (tmp_path / "config.json").write_text("{{}}")
    pygame.init()
    class DummyCtx:
        def __init__(self):
            self.screen = pygame.Surface((320, 180))
            self.internal = pygame.Surface((320, 180))
            self.clock = pygame.time.Clock()
            self.scale = 1
    ctx = DummyCtx()
    scene.on_enter(ctx)
    for _ in range(120):
        scene.update(1/60)
        scene.draw(ctx.internal)
    pygame.quit()
"""

CONFIG_DEFAULT = {
    "player_speed": 95.0,
    "hazard_speed": 55.0,
    "hazard_spawn_rate": 1.2,
    "palette_bg": [18, 18, 28],
    "palette_player": [240, 240, 240],
    "palette_hazard": [255, 120, 120],
}

ELEVATORS = {
    "neon_runner": "Dash through synth alleys dodging neon hazards.",
    "pixel_pirates": "Sail a pixel sea, dodge cannonballs and collect loot.",
    "astro_salvage": "Jet around a derelict station, avoid debris, grab parts.",
    "turbo_tunnelers": "Drift in narrow tunnels as walls collapse.",
    "sky_squadron": "Dogfight silhouettes above the clouds.",
}

FIRST5_TUNING = {
    "neon_runner": {"hazard_spawn_rate": 1.6, "palette_bg": [10, 10, 22]},
    "pixel_pirates": {"hazard_speed": 45.0, "palette_bg": [12, 20, 28]},
    "astro_salvage": {"player_speed": 110.0, "hazard_spawn_rate": 1.0},
    "turbo_tunnelers": {"hazard_speed": 70.0, "hazard_spawn_rate": 1.4},
    "sky_squadron": {"hazard_speed": 60.0, "palette_hazard": [255, 255, 120]},
}


def ensure_game(name: str):
    base = ROOT / name
    (base / "game" / "data").mkdir(parents=True, exist_ok=True)
    (base / "assets" / "sprites").mkdir(parents=True, exist_ok=True)
    (base / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
    (base / "save").mkdir(parents=True, exist_ok=True)

    title = " ".join([w.capitalize() for w in name.split("_")])

    readme = README_TEMPLATE.format(
        TITLE=title,
        ELEVATOR=ELEVATORS.get(name, f"Arcade microgame: survive and score in {title}."),
        SCORE=10,
        RAMP=25,
        MUL=1.15,
    )
    (base / "README.md").write_text(readme, encoding="utf-8")

    (base / "main.py").write_text(MAIN_TEMPLATE.format(TITLE=title), encoding="utf-8")

    cfg = CONFIG_DEFAULT.copy()
    cfg.update(FIRST5_TUNING.get(name, {}))
    (base / "game" / "data" / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    if name in FIRST5_TUNING:
        (base / "tests").mkdir(exist_ok=True)
        (base / "tests" / "test_smoke.py").write_text(TEST_TEMPLATE.format(TITLE=title), encoding="utf-8")


def main():
    for g in GAMES:
        ensure_game(g)
    print(f"Scaffolded {len(GAMES)} games under games/.")


if __name__ == "__main__":
    main()


