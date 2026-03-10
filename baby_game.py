#!/usr/bin/env python3
"""
Compatibility entrypoint for the baby game.
"""

import time

import pygame

from game_app import BabyGame
from game_assets import AnimalAssetLibrary, SoundFactory
from game_config import (
    ANIMAL_DATA,
    ASSET_DIR,
    BASE_DIR,
    BG_COLOR_CYCLE_SPEED,
    COLORS,
    DISPLAY_FONT_CANDIDATES,
    EXIT_HOLD_SECONDS,
    FPS,
    IMAGE_DIR,
    NAME_AUDIO_DIR,
    ANIMAL_SOUND_DIR,
    _animal_asset_key,
    _build_animal,
    find_existing_asset,
    pick_display_font,
)
from game_entities import (
    Airplane,
    Bubble,
    CapturedAnimalCelebration,
    FloatingChar,
    MouseTrail,
    Particle,
)


if __name__ == "__main__":
    BabyGame().run()
