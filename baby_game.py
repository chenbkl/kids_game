#!/usr/bin/env python3
"""
Compatibility entrypoint for the baby game.
"""

import argparse
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Baby Game")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode with a windowed display and normal window controls.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    BabyGame(debug_mode=args.debug).run()
