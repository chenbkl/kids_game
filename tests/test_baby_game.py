from pathlib import Path
from types import SimpleNamespace
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import baby_game
import game_app
import game_assets


class KeyState:
    def __init__(self, pressed=None):
        self.pressed = set(pressed or [])

    def __getitem__(self, key):
        return key in self.pressed


def make_game():
    game = game_app.BabyGame.__new__(game_app.BabyGame)
    game.exit_combo_start = None
    game.last_exit_combo_name = ""
    game.running = True
    game.captured_overlay = None
    return game


def make_key_game():
    game = make_game()
    game.screen_w = 1280
    game.screen_h = 720
    game.font_huge = object()
    game.font_large = object()
    game.floating_chars = []
    game.particles = []
    game.total_interactions = 0
    game.airplane = SimpleNamespace(x=640, y=360, target_x=640, target_y=360)
    game.spawn_firework = lambda *args, **kwargs: None
    game.spawn_confetti = lambda *args, **kwargs: None
    return game


def test_ctrl_shift_esc_exits_after_hold(monkeypatch):
    game = make_game()
    keys = KeyState({
        baby_game.pygame.K_LCTRL,
        game_app.pygame.K_LSHIFT,
        game_app.pygame.K_ESCAPE,
    })

    monkeypatch.setattr(game_app.pygame.key, "get_pressed", lambda: keys)
    monkeypatch.setattr(game_app.time, "time", lambda: 100.0)

    elapsed = game.check_exit_combo()

    assert elapsed == 0
    assert game.exit_combo_start == 100.0
    assert game.running is True

    monkeypatch.setattr(game_app.time, "time", lambda: 103.1)

    elapsed = game.check_exit_combo()

    assert elapsed >= baby_game.EXIT_HOLD_SECONDS
    assert game.running is False


def test_exit_combo_resets_when_released(monkeypatch):
    game = make_game()
    game.exit_combo_start = 50.0
    game.last_exit_combo_name = "Ctrl+Shift+Esc"

    monkeypatch.setattr(game_app.pygame.key, "get_pressed", lambda: KeyState())

    elapsed = game.check_exit_combo()

    assert elapsed == 0
    assert game.exit_combo_start is None
    assert game.last_exit_combo_name == ""


def test_init_enables_event_and_keyboard_grab(monkeypatch):
    set_mode_calls = []
    grab_calls = []
    keyboard_grab_calls = []

    monkeypatch.setattr(game_app.pygame, "init", lambda: None)
    monkeypatch.setattr(game_app.pygame.mixer, "init", lambda **kwargs: None)
    monkeypatch.setattr(
        game_app.pygame.display,
        "Info",
        lambda: SimpleNamespace(current_w=1280, current_h=720),
    )
    monkeypatch.setattr(
        game_app.pygame.display,
        "set_mode",
        lambda size, flags: set_mode_calls.append((size, flags)) or object(),
    )
    monkeypatch.setattr(game_app.pygame.display, "set_caption", lambda title: None)
    monkeypatch.setattr(game_app.pygame.mouse, "set_visible", lambda visible: None)
    monkeypatch.setattr(
        game_app.pygame.event,
        "set_grab",
        lambda enabled: grab_calls.append(enabled),
    )
    monkeypatch.setattr(
        game_app.pygame.event,
        "set_keyboard_grab",
        lambda enabled: keyboard_grab_calls.append(enabled),
    )
    monkeypatch.setattr(game_app.pygame.font, "SysFont", lambda *args, **kwargs: object())
    monkeypatch.setattr(game_app, "SoundFactory", lambda: object())
    monkeypatch.setattr(game_app, "AnimalAssetLibrary", lambda: object())
    monkeypatch.setattr(game_app, "Airplane", lambda w, h: object())
    monkeypatch.setattr(game_app, "MouseTrail", lambda: object())
    monkeypatch.setattr(game_app, "Bubble", lambda *args, **kwargs: object())
    monkeypatch.setattr(game_app.BabyGame, "_warm_up_assets", lambda self: None)

    game = game_app.BabyGame()

    assert game.screen_w == 1280
    assert game.screen_h == 720
    assert set_mode_calls == [((1280, 720), game_app.pygame.FULLSCREEN | game_app.pygame.HWSURFACE | game_app.pygame.DOUBLEBUF)]
    assert grab_calls == [True]
    assert keyboard_grab_calls == [True]


def test_clicking_bubble_plays_name_then_animal_sound(monkeypatch):
    played = []
    queued = []

    class FakeChannel:
        def queue(self, sound):
            queued.append(sound.name)

    class FakeSound:
        def __init__(self, name):
            self.name = name

        def play(self):
            played.append(self.name)
            if self.name == "name":
                return FakeChannel()
            return None

    class FakeBubble:
        popped = False
        animal = {"label": "Kitty", "name": "Cat"}

        def contains(self, x, y):
            return True

        def pop(self):
            self.popped = True

    game = make_game()
    game.bubbles = [FakeBubble()]
    game.font_huge = object()
    game.font_large = object()
    game.font_medium = object()
    game.floating_chars = []
    game.spawn_firework = lambda *args, **kwargs: None
    game.total_interactions = 0
    game.animal_assets = object()
    game.screen_w = 1280
    game.screen_h = 720
    game.sound_factory = SimpleNamespace(
        name_sound=lambda animal: FakeSound("name"),
        animal_sound=lambda animal: FakeSound("animal"),
        click_sound=lambda: FakeSound("click"),
    )

    monkeypatch.setattr(game_app, "FloatingChar", lambda *args, **kwargs: object())
    monkeypatch.setattr(game_app, "CapturedAnimalCelebration", lambda *args, **kwargs: "overlay")

    game.handle_click((100, 100), 1)

    assert played == ["name"]
    assert queued == ["animal"]
    assert game.captured_overlay == "overlay"


def test_letter_key_shows_large_character_animation(monkeypatch):
    floating_calls = []
    key_sound_calls = []

    class FakeSound:
        def play(self):
            key_sound_calls.append("play")

    game = make_key_game()
    game.sound_factory = SimpleNamespace(
        key_sound=lambda code: key_sound_calls.append(code) or FakeSound(),
    )

    monkeypatch.setattr(game_app, "FloatingChar", lambda *args: floating_calls.append(args) or object())
    monkeypatch.setattr(game_app.random, "randint", lambda start, end: (start + end) // 2)

    event = SimpleNamespace(unicode="k", key=game_app.pygame.K_k)
    game.handle_key(event)

    assert floating_calls
    assert floating_calls[0][0] == "K"
    assert key_sound_calls == [ord("K"), "play"]


def test_symbol_key_does_not_show_character_animation(monkeypatch):
    key_sound_calls = []

    class FakeSound:
        def play(self):
            key_sound_calls.append("play")

    game = make_key_game()
    game.sound_factory = SimpleNamespace(
        key_sound=lambda code: key_sound_calls.append(code) or FakeSound(),
    )

    monkeypatch.setattr(game_app, "FloatingChar", lambda *args: (_ for _ in ()).throw(AssertionError("should not animate")))

    event = SimpleNamespace(unicode=".", key=game_app.pygame.K_PERIOD)
    game.handle_key(event)

    assert game.floating_chars == []
    assert key_sound_calls == [game_app.pygame.K_PERIOD, "play"]


def test_space_key_keeps_effects_without_text_animation(monkeypatch):
    special_sound_calls = []
    firework_calls = []
    confetti_calls = []

    class FakeSound:
        def play(self):
            special_sound_calls.append("play")

    game = make_key_game()
    game.spawn_firework = lambda *args, **kwargs: firework_calls.append((args, kwargs))
    game.spawn_confetti = lambda *args, **kwargs: confetti_calls.append((args, kwargs))
    game.sound_factory = SimpleNamespace(
        special_sound=lambda: FakeSound(),
    )

    monkeypatch.setattr(game_app, "FloatingChar", lambda *args: (_ for _ in ()).throw(AssertionError("should not animate")))

    event = SimpleNamespace(unicode=" ", key=game_app.pygame.K_SPACE)
    game.handle_key(event)

    assert firework_calls
    assert confetti_calls
    assert special_sound_calls == ["play"]
    assert game.floating_chars == []


def test_sound_factory_prefers_local_animal_audio(monkeypatch):
    loaded_paths = []

    monkeypatch.setattr(
        game_assets,
        "find_existing_asset",
        lambda *paths: os.path.join("/tmp", "real_wav", "cat.wav"),
    )
    monkeypatch.setattr(
        game_app.pygame.mixer,
        "Sound",
        lambda path=None, buffer=None: loaded_paths.append(path or buffer) or "sound",
    )

    factory = baby_game.SoundFactory()
    sound = factory.animal_sound(baby_game.ANIMAL_DATA[0])

    assert sound == "sound"
    assert loaded_paths == [os.path.join("/tmp", "real_wav", "cat.wav")]


def test_animal_asset_library_prefers_local_png(monkeypatch):
    convert_calls = []

    class FakeImage:
        def convert_alpha(self):
            convert_calls.append("convert")
            return self

        def get_width(self):
            return 100

        def get_height(self):
            return 50

    monkeypatch.setattr(
        game_assets,
        "find_existing_asset",
        lambda *paths: "/tmp/images_hd/dog.svg.png",
    )
    monkeypatch.setattr(game_app.pygame.image, "load", lambda path: FakeImage())
    monkeypatch.setattr(game_app.pygame.transform, "smoothscale", lambda image, size: (image, size))

    library = baby_game.AnimalAssetLibrary()
    scaled = library.scaled_image_for(baby_game.ANIMAL_DATA[1], 80)

    assert convert_calls == ["convert"]
    assert scaled[1] == (94, 47)


def test_animal_asset_library_prefers_hd_image_for_bubbles(monkeypatch):
    loaded_paths = []

    class FakeImage:
        def convert_alpha(self):
            return self

        def get_width(self):
            return 1024

        def get_height(self):
            return 1024

    monkeypatch.setattr(
        game_assets,
        "find_existing_asset",
        lambda *paths: "/tmp/images_hd/cat.svg.png",
    )
    monkeypatch.setattr(
        game_app.pygame.image,
        "load",
        lambda path: loaded_paths.append(path) or FakeImage(),
    )
    monkeypatch.setattr(game_app.pygame.transform, "smoothscale", lambda image, size: (image, size))

    library = baby_game.AnimalAssetLibrary()
    library.scaled_image_for(baby_game.ANIMAL_DATA[0], 80)

    assert loaded_paths == ["/tmp/images_hd/cat.svg.png"]


def test_animal_asset_library_buckets_scaled_sizes(monkeypatch):
    scale_calls = []

    class FakeImage:
        def convert_alpha(self):
            return self

        def get_width(self):
            return 100

        def get_height(self):
            return 50

    monkeypatch.setattr(
        game_assets,
        "find_existing_asset",
        lambda *paths: "/tmp/images_hd/dog.svg.png",
    )
    monkeypatch.setattr(game_app.pygame.image, "load", lambda path: FakeImage())
    monkeypatch.setattr(
        game_app.pygame.transform,
        "smoothscale",
        lambda image, size: scale_calls.append(size) or (image, size),
    )

    library = baby_game.AnimalAssetLibrary()
    first = library.scaled_image_for(baby_game.ANIMAL_DATA[1], 281)
    second = library.scaled_image_for(baby_game.ANIMAL_DATA[1], 284)

    assert first == second
    assert len(scale_calls) == 1


def test_animal_asset_library_prefers_hd_popup_png(monkeypatch):
    convert_calls = []

    class FakeImage:
        def convert_alpha(self):
            convert_calls.append("convert")
            return self

        def get_width(self):
            return 1024

        def get_height(self):
            return 1024

    monkeypatch.setattr(
        game_assets,
        "find_existing_asset",
        lambda *paths: "/tmp/images_hd/dog.svg.png",
    )
    monkeypatch.setattr(game_app.pygame.image, "load", lambda path: FakeImage())
    monkeypatch.setattr(game_app.pygame.transform, "smoothscale", lambda image, size: (image, size))

    library = baby_game.AnimalAssetLibrary()
    scaled = library.scaled_popup_image_for(baby_game.ANIMAL_DATA[1], 296)

    assert convert_calls == ["convert"]
    assert scaled[1][0] > 0


def test_sound_factory_preload_warms_name_and_animal_sounds(monkeypatch):
    calls = []

    factory = baby_game.SoundFactory()
    monkeypatch.setattr(factory, "name_sound", lambda animal: calls.append(("name", animal["name"])))
    monkeypatch.setattr(factory, "animal_sound", lambda animal: calls.append(("animal", animal["name"])))

    factory.preload(baby_game.ANIMAL_DATA[:2])

    assert calls == [
        ("name", baby_game.ANIMAL_DATA[0]["name"]),
        ("animal", baby_game.ANIMAL_DATA[0]["name"]),
        ("name", baby_game.ANIMAL_DATA[1]["name"]),
        ("animal", baby_game.ANIMAL_DATA[1]["name"]),
    ]


def test_pick_display_font_prefers_chinese_fonts(monkeypatch):
    monkeypatch.setattr(game_app.pygame.font, "get_fonts", lambda: ["arial", "pingfangsc", "hiraginosansgb"])

    assert baby_game.pick_display_font() == "PingFang SC"


def test_warm_up_assets_preloads_images_and_audio():
    preload_calls = []
    game = make_game()
    game.screen = object()
    game.screen_w = 1280
    game.screen_h = 720
    game.font_large = object()
    game.font_medium = object()
    game.font_small = object()
    game.font_tiny = object()
    game.animal_assets = SimpleNamespace(
        scaled_image_for=lambda *args, **kwargs: None,
        preload=lambda animals, diameters, progress=None: preload_calls.append(("image", len(animals), tuple(diameters), callable(progress))),
        preload_popup_images=lambda animals, diameters, progress=None: preload_calls.append(("popup", len(animals), tuple(diameters), callable(progress))),
    )
    game.sound_factory = SimpleNamespace(
        preload=lambda animals, progress=None: preload_calls.append(("sound", len(animals), callable(progress))),
    )
    game._draw_loading_screen = lambda *args, **kwargs: preload_calls.append(("screen", args[0], round(args[2], 2)))

    game_app.BabyGame._warm_up_assets(game)

    assert any(call[0] == "image" and call[1] == len(baby_game.ANIMAL_DATA) and call[3] is True for call in preload_calls)
    assert any(call[0] == "popup" and call[1] == len(baby_game.ANIMAL_DATA) and call[3] is True for call in preload_calls)
    assert any(call[0] == "sound" and call[1] == len(baby_game.ANIMAL_DATA) and call[2] is True for call in preload_calls)
    assert ("screen", "准备完成", 1.0) in preload_calls


def test_captured_animal_celebration_expires():
    celebration = baby_game.CapturedAnimalCelebration(
        baby_game.ANIMAL_DATA[0],
        SimpleNamespace(
            scaled_image_for=lambda *args, **kwargs: None,
            scaled_popup_image_for=lambda *args, **kwargs: None,
        ),
        object(),
        object(),
        1280,
        720,
    )

    for _ in range(149):
        assert celebration.update() is True

    assert celebration.update() is False
