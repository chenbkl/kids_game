# Kid Game Structure

This project is split by responsibility so the main game loop stays small and maintainable.

## Modules

- `baby_game.py`: compatibility entrypoint and public import surface.
- `game_app.py`: the `BabyGame` application class and main loop.
- `game_config.py`: constants, asset paths, animal metadata, and font selection.
- `game_assets.py`: image caching, sound loading, and preload logic.
- `game_entities.py`: render/update classes such as bubbles, particles, airplane, overlays, and trail.

## Assets

Assets live under `cartoon_animals_out/`.

- `images/`: animal images used by the game. Prefer `svg`.
- `animal_sounds/`: animal sound effects used when catching animals.
- `name_zh/`: Chinese name voice clips. The game prefers these local files first.
- `tools/`: helper scripts for asset preparation.

## Run

```bash
python3 baby_game.py
```
