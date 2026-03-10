import math
import os
import random
import struct
import subprocess

import pygame

from game_config import NAME_AUDIO_DIR, find_existing_asset


class AnimalAssetLibrary:
    def __init__(self):
        self._image_path_cache = {}
        self._popup_image_path_cache = {}
        self._image_cache = {}
        self._popup_image_cache = {}
        self._scaled_image_cache = {}
        self._scaled_popup_image_cache = {}
        self._size_step = 8

    def _normalize_diameter(self, diameter):
        diameter = max(self._size_step, int(diameter))
        return max(self._size_step, (diameter // self._size_step) * self._size_step)

    def image_path_for(self, animal):
        asset_key = animal["asset_key"]
        if asset_key in self._image_path_cache:
            return self._image_path_cache[asset_key]

        path = find_existing_asset(
            f"images_hd/{asset_key}.png",
            f"images_hd/{asset_key}.svg.png",
            f"images/{asset_key}.svg",
            f"images/{asset_key}.png",
            f"images/{asset_key}.jpg",
            f"images/{asset_key}.jpeg",
        )
        self._image_path_cache[asset_key] = path
        return path

    def popup_image_path_for(self, animal):
        asset_key = animal["asset_key"]
        if asset_key in self._popup_image_path_cache:
            return self._popup_image_path_cache[asset_key]

        path = find_existing_asset(
            f"images_hd/{asset_key}.png",
            f"images_hd/{asset_key}.svg.png",
            f"images/{asset_key}.svg",
            f"images/{asset_key}.png",
            f"images/{asset_key}.jpg",
            f"images/{asset_key}.jpeg",
        )
        self._popup_image_path_cache[asset_key] = path
        return path

    def image_for(self, animal):
        asset_key = animal["asset_key"]
        if asset_key in self._image_cache:
            return self._image_cache[asset_key]

        image = None
        path = self.image_path_for(animal)
        if path:
            try:
                image = pygame.image.load(path).convert_alpha()
            except Exception:
                image = None
        self._image_cache[asset_key] = image
        return image

    def popup_image_for(self, animal):
        asset_key = animal["asset_key"]
        if asset_key in self._popup_image_cache:
            return self._popup_image_cache[asset_key]

        image = None
        path = self.popup_image_path_for(animal)
        if path:
            try:
                image = pygame.image.load(path).convert_alpha()
            except Exception:
                image = None
        self._popup_image_cache[asset_key] = image
        return image

    def scaled_image_for(self, animal, diameter):
        normalized_diameter = self._normalize_diameter(diameter)
        cache_key = (animal["asset_key"], normalized_diameter)
        if cache_key in self._scaled_image_cache:
            return self._scaled_image_cache[cache_key]

        image = self.image_for(animal)
        scaled = None
        if image is not None:
            max_w = max(1, int(normalized_diameter * 1.18))
            max_h = max(1, int(normalized_diameter * 1.18))
            scale = min(max_w / image.get_width(), max_h / image.get_height())
            size = (
                max(1, int(image.get_width() * scale)),
                max(1, int(image.get_height() * scale)),
            )
            scaled = pygame.transform.smoothscale(image, size)
        self._scaled_image_cache[cache_key] = scaled
        return scaled

    def scaled_popup_image_for(self, animal, diameter):
        normalized_diameter = self._normalize_diameter(diameter)
        cache_key = (animal["asset_key"], normalized_diameter)
        if cache_key in self._scaled_popup_image_cache:
            return self._scaled_popup_image_cache[cache_key]

        image = self.popup_image_for(animal)
        scaled = None
        if image is not None:
            max_w = max(1, int(normalized_diameter * 1.18))
            max_h = max(1, int(normalized_diameter * 1.18))
            scale = min(max_w / image.get_width(), max_h / image.get_height())
            size = (
                max(1, int(image.get_width() * scale)),
                max(1, int(image.get_height() * scale)),
            )
            scaled = pygame.transform.smoothscale(image, size)
        self._scaled_popup_image_cache[cache_key] = scaled
        return scaled

    def preload(self, animals, diameters, progress_callback=None):
        total = max(1, len(animals) * (1 + len(diameters)))
        completed = 0
        for animal in animals:
            self.image_for(animal)
            completed += 1
            if progress_callback is not None:
                progress_callback(completed, total, f"加载图片 {animal['label']}")
            for diameter in diameters:
                self.scaled_image_for(animal, diameter)
                completed += 1
                if progress_callback is not None:
                    progress_callback(completed, total, f"处理图片尺寸 {animal['label']}")

    def preload_popup_images(self, animals, diameters, progress_callback=None):
        total = max(1, len(animals) * (1 + len(diameters)))
        completed = 0
        for animal in animals:
            self.popup_image_for(animal)
            completed += 1
            if progress_callback is not None:
                progress_callback(completed, total, f"加载弹窗图片 {animal['label']}")
            for diameter in diameters:
                self.scaled_popup_image_for(animal, diameter)
                completed += 1
                if progress_callback is not None:
                    progress_callback(completed, total, f"处理弹窗尺寸 {animal['label']}")


class SoundFactory:
    def __init__(self):
        self.sample_rate = 22050
        self._cache = {}
        self._speech_dir = NAME_AUDIO_DIR
        os.makedirs(self._speech_dir, exist_ok=True)

    def _speech_path(self, animal):
        asset_key = animal["asset_key"]
        existing = find_existing_asset(
            f"name_zh/{asset_key}.wav",
            f"name_zh/{asset_key}.mp3",
            f"name_zh/{asset_key}.aiff",
            f"name_zh/{asset_key}.ogg",
            f"name_zh/{asset_key}_zh.wav",
            f"name_zh/{asset_key}_zh.mp3",
            f"name_zh/{asset_key}_zh.aiff",
            f"name_zh/{asset_key}_zh.ogg",
        )
        if existing:
            return existing
        return os.path.join(self._speech_dir, f"{asset_key}_zh.aiff")

    def _animal_sound_path(self, animal):
        asset_key = animal["asset_key"]
        return find_existing_asset(
            f"animal_sounds/{asset_key}.wav",
            f"animal_sounds/{asset_key}.mp3",
        )

    def _wave_samples(self, freq, duration, wave_type="sine", volume=0.3):
        n_samples = int(self.sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / self.sample_rate
            env = min(1.0, i / (self.sample_rate * 0.01))
            env *= min(1.0, (n_samples - i) / (self.sample_rate * 0.05))

            if wave_type == "sine":
                val = math.sin(2 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == "triangle":
                val = 2.0 * abs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
            else:
                val = math.sin(2 * math.pi * freq * t)

            val *= env * volume
            samples.append(int(val * 32767))
        return samples

    def _sound_from_samples(self, key, samples):
        if key in self._cache:
            return self._cache[key]

        raw = struct.pack(f"<{len(samples)}h", *samples)
        sound = pygame.mixer.Sound(buffer=raw)
        self._cache[key] = sound
        return sound

    def _make_wave(self, freq, duration, wave_type="sine", volume=0.3):
        key = (freq, duration, wave_type, volume)
        samples = self._wave_samples(freq, duration, wave_type, volume)
        return self._sound_from_samples(key, samples)

    def key_sound(self, char_code=None):
        pentatonic = [262, 294, 330, 392, 440, 524, 588, 660, 784, 880]
        if char_code:
            freq = pentatonic[char_code % len(pentatonic)]
        else:
            freq = random.choice(pentatonic)
        wave_type = random.choice(["sine", "triangle"])
        return self._make_wave(freq, 0.25, wave_type, 0.25)

    def click_sound(self):
        freq = random.randint(600, 1200)
        return self._make_wave(freq, 0.15, "sine", 0.2)

    def animal_sound(self, animal):
        key = ("animal", animal["name"])
        if key in self._cache:
            return self._cache[key]

        sound_path = self._animal_sound_path(animal)
        if sound_path:
            try:
                sound = pygame.mixer.Sound(sound_path)
                self._cache[key] = sound
                return sound
            except Exception:
                pass

        accent = animal["accent_color"]
        freq = 220 + (accent[0] % 7) * 45
        alt_freq = freq + 110 + (accent[1] % 5) * 25
        pause = [0] * int(self.sample_rate * 0.03)
        samples = (
            self._wave_samples(freq, 0.18, "triangle", 0.35)
            + pause
            + self._wave_samples(alt_freq, 0.16, "square", 0.28)
        )
        return self._sound_from_samples(key, samples)

    def name_sound(self, animal):
        key = ("name", animal["label"])
        if key in self._cache:
            return self._cache[key]

        speech_path = self._speech_path(animal)
        try:
            if not os.path.exists(speech_path):
                subprocess.run(
                    ["say", "-v", "Ting-Ting", "-o", speech_path, animal["label"]],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            sound = pygame.mixer.Sound(speech_path)
            self._cache[key] = sound
            return sound
        except Exception:
            fallback = self._make_wave(660, 0.18, "triangle", 0.25)
            self._cache[key] = fallback
            return fallback

    def preload(self, animals, progress_callback=None):
        total = max(1, len(animals) * 2)
        completed = 0
        for animal in animals:
            self.name_sound(animal)
            completed += 1
            if progress_callback is not None:
                progress_callback(completed, total, f"准备名字语音 {animal['label']}")
            self.animal_sound(animal)
            completed += 1
            if progress_callback is not None:
                progress_callback(completed, total, f"准备动物音效 {animal['label']}")

    def special_sound(self):
        return self._make_wave(880, 0.4, "triangle", 0.2)
