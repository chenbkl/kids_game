import os

import pygame

FPS = 60
EXIT_HOLD_SECONDS = 3

COLORS = [
    (255, 87, 87),
    (255, 165, 0),
    (255, 230, 0),
    (0, 200, 83),
    (0, 176, 255),
    (156, 39, 176),
    (255, 105, 180),
    (0, 230, 230),
    (255, 200, 100),
    (100, 255, 150),
]

BG_COLOR_CYCLE_SPEED = 0.002
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "cartoon_animals_out")
NAME_AUDIO_DIR = os.path.join(ASSET_DIR, "name_zh")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
IMAGE_HD_DIR = os.path.join(ASSET_DIR, "images_hd")
ANIMAL_SOUND_DIR = os.path.join(ASSET_DIR, "animal_sounds")
DISPLAY_FONT_CANDIDATES = [
    "PingFang SC",
    "Hiragino Sans GB",
    "STHeiti",
    "Heiti SC",
    "Arial Unicode MS",
    "Noto Sans CJK SC",
    "Microsoft YaHei",
    "SimHei",
    "Arial",
]


def _animal_asset_key(name):
    return name.lower().replace(" ", "_")


def _build_animal(name, label, base_color, accent_color):
    return {
        "name": name,
        "label": label,
        "base_color": base_color,
        "accent_color": accent_color,
        "asset_key": _animal_asset_key(name),
    }


ANIMAL_DATA = [
    _build_animal("Cat", "小猫", (255, 190, 120), (255, 150, 90)),
    _build_animal("Dog", "小狗", (195, 145, 105), (120, 80, 60)),
    _build_animal("Duck", "小鸭", (255, 232, 90), (255, 145, 40)),
    _build_animal("Frog", "青蛙", (110, 220, 110), (70, 140, 70)),
    _build_animal("Pig", "小猪", (255, 180, 205), (240, 120, 165)),
    _build_animal("Cow", "奶牛", (240, 240, 240), (60, 60, 60)),
    _build_animal("Sheep", "小羊", (250, 250, 250), (210, 210, 210)),
    _build_animal("Chicken", "小鸡", (255, 230, 120), (255, 145, 60)),
    _build_animal("Horse", "小马", (170, 110, 75), (95, 60, 40)),
    _build_animal("Elephant", "大象", (175, 190, 210), (110, 125, 150)),
    _build_animal("Lion", "狮子", (255, 195, 90), (200, 120, 45)),
    _build_animal("Monkey", "小猴", (190, 135, 90), (120, 80, 55)),
]


def find_existing_asset(*relative_paths):
    for relative_path in relative_paths:
        path = os.path.join(ASSET_DIR, relative_path)
        if os.path.exists(path):
            return path
    return None


def pick_display_font():
    try:
        available_fonts = {name.lower(): name for name in pygame.font.get_fonts()}
    except Exception:
        return DISPLAY_FONT_CANDIDATES[-1]

    for candidate in DISPLAY_FONT_CANDIDATES:
        normalized = candidate.lower().replace(" ", "").replace("-", "")
        if normalized in available_fonts:
            return candidate
    return DISPLAY_FONT_CANDIDATES[-1]
