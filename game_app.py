import math
import os
import random
import sys
import time

import pygame

from game_assets import AnimalAssetLibrary, SoundFactory
from game_config import ANIMAL_DATA, BG_COLOR_CYCLE_SPEED, COLORS, EXIT_HOLD_SECONDS, FPS, pick_display_font
from game_entities import Airplane, Bubble, CapturedAnimalCelebration, FloatingChar, MouseTrail, Particle


class BabyGame:
    def __init__(self):
        os.environ["SDL_VIDEO_CENTERED"] = "1"
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h

        display_flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), display_flags)
        pygame.display.set_caption("Baby Game")

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        if hasattr(pygame.event, "set_keyboard_grab"):
            pygame.event.set_keyboard_grab(True)

        self.display_font_name = pick_display_font()
        self.font_huge = pygame.font.SysFont(self.display_font_name, 160, bold=True)
        self.font_large = pygame.font.SysFont(self.display_font_name, 80, bold=True)
        self.font_medium = pygame.font.SysFont(self.display_font_name, 40, bold=True)
        self.font_small = pygame.font.SysFont(self.display_font_name, 24)
        self.font_tiny = pygame.font.SysFont(self.display_font_name, 18)

        self.sound_factory = SoundFactory()
        self.animal_assets = AnimalAssetLibrary()
        self._warm_up_assets()

        self.particles = []
        self.floating_chars = []
        self.bubbles = []
        self.airplane = Airplane(self.screen_w, self.screen_h)
        self.mouse_trail = MouseTrail()

        self.clock = pygame.time.Clock()
        self.running = True
        self.frame_count = 0
        self.bg_hue = 0
        self.show_airplane = True
        self.captured_overlay = None

        self.exit_combo_start = None
        self.last_exit_combo_name = ""
        self.started_at = time.time()

        self.next_bubble_time = 0
        self.total_interactions = 0
        self.cursor_size = 20
        self.cursor_pulse = 0

        self.stars = []
        for _ in range(60):
            self.stars.append({
                "x": random.randint(0, self.screen_w),
                "y": random.randint(0, self.screen_h),
                "size": random.uniform(1, 3),
                "twinkle": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.02, 0.05),
            })
        for _ in range(6):
            x = random.randint(80, max(81, self.screen_w - 80))
            y = random.randint(self.screen_h // 3, max(self.screen_h // 3 + 1, self.screen_h - 120))
            self.bubbles.append(Bubble(x, y, self.screen_h, self.animal_assets))

    def _warm_up_assets(self):
        common_diameters = [64, 72, 80, 88, 96, 104, 112, 280, 288]
        stages = [
            (
                "准备动物图片",
                lambda progress: self.animal_assets.preload(ANIMAL_DATA, common_diameters, progress),
            ),
            (
                "准备弹窗图片",
                lambda progress: self.animal_assets.preload_popup_images(ANIMAL_DATA, [280, 288, 296, 304, 312], progress),
            ),
            (
                "准备动物声音",
                lambda progress: self.sound_factory.preload(ANIMAL_DATA, progress),
            ),
        ]

        total_stages = len(stages)
        for stage_index, (stage_name, runner) in enumerate(stages, start=1):
            def on_progress(completed, total, detail):
                stage_progress = completed / max(1, total)
                overall_progress = ((stage_index - 1) + stage_progress) / total_stages
                self._draw_loading_screen(stage_name, detail, overall_progress)

            self._draw_loading_screen(stage_name, "开始", (stage_index - 1) / total_stages)
            runner(on_progress)

        self._draw_loading_screen("准备完成", "进入游戏", 1.0)

    def _draw_loading_screen(self, title, detail, progress):
        progress = max(0.0, min(1.0, progress))
        pygame.event.pump()

        self.screen.fill((16, 24, 44))
        for idx, animal in enumerate(ANIMAL_DATA[:6]):
            x = 120 + idx * 150
            y = 110 + int(math.sin(time.time() * 2.5 + idx) * 10)
            pygame.draw.circle(self.screen, animal["base_color"], (x, y), 34)
            image = self.animal_assets.scaled_image_for(animal, 60)
            if image is not None:
                self.screen.blit(image, image.get_rect(center=(x, y)))
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 34, 3)

        title_surf = self.font_large.render("抓动物游戏", True, (255, 244, 215))
        stage_surf = self.font_medium.render(title, True, (235, 243, 255))
        detail_surf = self.font_small.render(detail, True, (205, 218, 236))
        tip_surf = self.font_tiny.render("首次启动会预加载图片和声音，后续点击会更流畅", True, (170, 186, 210))

        card_w = min(920, self.screen_w - 120)
        card_h = 240
        card_x = self.screen_w // 2 - card_w // 2
        card_y = self.screen_h // 2 - card_h // 2 + 60
        pygame.draw.rect(self.screen, (28, 40, 72), (card_x, card_y, card_w, card_h), border_radius=32)
        pygame.draw.rect(self.screen, (255, 215, 110), (card_x, card_y, card_w, card_h), 4, border_radius=32)

        self.screen.blit(title_surf, title_surf.get_rect(center=(self.screen_w // 2, card_y + 52)))
        self.screen.blit(stage_surf, stage_surf.get_rect(center=(self.screen_w // 2, card_y + 112)))
        self.screen.blit(detail_surf, detail_surf.get_rect(center=(self.screen_w // 2, card_y + 152)))
        self.screen.blit(tip_surf, tip_surf.get_rect(center=(self.screen_w // 2, card_y + 210)))

        bar_w = card_w - 120
        bar_h = 20
        bar_x = self.screen_w // 2 - bar_w // 2
        bar_y = card_y + 174
        pygame.draw.rect(self.screen, (74, 88, 128), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
        pygame.draw.rect(self.screen, (255, 204, 86), (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=10)
        pygame.display.flip()

    def _exit_hint(self):
        return "Hold Ctrl+Shift+Esc for 3 seconds"

    def _show_start_overlay(self):
        return self.total_interactions == 0 and (time.time() - self.started_at) < 8

    def _hue_to_rgb(self, hue, saturation=0.15, lightness=0.92):
        h = hue % 360
        s = saturation
        l = lightness
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2

        if h < 60:
            r1, g1, b1 = c, x, 0
        elif h < 120:
            r1, g1, b1 = x, c, 0
        elif h < 180:
            r1, g1, b1 = 0, c, x
        elif h < 240:
            r1, g1, b1 = 0, x, c
        elif h < 300:
            r1, g1, b1 = x, 0, c
        else:
            r1, g1, b1 = c, 0, x

        return (int((r1 + m) * 255), int((g1 + m) * 255), int((b1 + m) * 255))

    def spawn_firework(self, x, y, count=30):
        color = random.choice(COLORS)
        for _ in range(count):
            self.particles.append(Particle(
                x, y, color=color, speed=random.uniform(3, 10), size=random.uniform(4, 14),
                life=random.uniform(40, 90), gravity=0.08
            ))

    def spawn_confetti(self, x, y, count=20):
        for _ in range(count):
            self.particles.append(Particle(
                x, y, speed=random.uniform(2, 6), size=random.uniform(5, 10),
                shape="square", life=random.uniform(50, 100), gravity=0.12
            ))

    @staticmethod
    def _animated_key_char(event):
        char = event.unicode if event.unicode and event.unicode.isprintable() else None
        if char and char.isalnum():
            return char.upper()
        return None

    def handle_key(self, event):
        self.total_interactions += 1
        char = self._animated_key_char(event)
        margin = 150
        x = random.randint(margin, self.screen_w - margin)
        y = random.randint(margin, self.screen_h - margin)

        if char:
            self.floating_chars.append(FloatingChar(char, x, y, self.font_huge, self.font_large))
            self.spawn_firework(x, y, count=15)
            self.sound_factory.key_sound(ord(char)).play()
            return

        if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            speed = 60
            if event.key == pygame.K_UP:
                self.airplane.target_y -= speed
            elif event.key == pygame.K_DOWN:
                self.airplane.target_y += speed
            elif event.key == pygame.K_LEFT:
                self.airplane.target_x -= speed
            elif event.key == pygame.K_RIGHT:
                self.airplane.target_x += speed
            for _ in range(5):
                self.particles.append(Particle(
                    self.airplane.x, self.airplane.y, shape="star", speed=2, size=8, life=40, gravity=0
                ))
        elif event.key == pygame.K_SPACE:
            self.spawn_firework(self.screen_w // 2, self.screen_h // 2, count=50)
            self.spawn_confetti(self.screen_w // 2, self.screen_h // 2, count=30)
            self.sound_factory.special_sound().play()
        else:
            self.sound_factory.key_sound(event.key).play()

    def handle_click(self, pos, button):
        self.total_interactions += 1
        x, y = pos
        popped = False
        for bubble in self.bubbles:
            if not bubble.popped and bubble.contains(x, y):
                bubble.pop()
                popped = True
                name_sound = self.sound_factory.name_sound(bubble.animal)
                animal_sound = self.sound_factory.animal_sound(bubble.animal)
                channel = name_sound.play()
                if channel is not None:
                    channel.queue(animal_sound)
                else:
                    animal_sound.play()
                self.floating_chars.append(FloatingChar(bubble.animal["label"], x, y - 40, self.font_huge, self.font_large))
                self.captured_overlay = CapturedAnimalCelebration(
                    bubble.animal, self.animal_assets, self.font_large, self.font_medium, self.screen_w, self.screen_h
                )
                break

        if not popped:
            self.spawn_firework(x, y, count=25)
            self.sound_factory.click_sound().play()
            if random.random() < 0.3:
                self.floating_chars.append(
                    FloatingChar(random.choice(ANIMAL_DATA)["label"], x, y - 30, self.font_huge, self.font_large)
                )

    def check_exit_combo(self):
        keys = pygame.key.get_pressed()
        ctrl = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        esc = keys[pygame.K_ESCAPE]

        if ctrl and shift and esc:
            if self.last_exit_combo_name != "Ctrl+Shift+Esc":
                self.exit_combo_start = time.time()
                self.last_exit_combo_name = "Ctrl+Shift+Esc"
            if self.exit_combo_start is None:
                self.exit_combo_start = time.time()
            elapsed = time.time() - self.exit_combo_start
            if elapsed >= EXIT_HOLD_SECONDS:
                self.running = False
            return elapsed

        self.exit_combo_start = None
        self.last_exit_combo_name = ""
        return 0

    def draw_exit_indicator(self, elapsed):
        if elapsed <= 0:
            return
        progress = min(1.0, elapsed / EXIT_HOLD_SECONDS)
        bar_w = 200
        bar_h = 8
        bx = self.screen_w // 2 - bar_w // 2
        by = 10
        pygame.draw.rect(self.screen, (100, 100, 100), (bx, by, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, (255, 100, 100), (bx, by, int(bar_w * progress), bar_h), border_radius=4)
        label = self.font_small.render(self.last_exit_combo_name, True, (240, 240, 240))
        self.screen.blit(label, (bx, by + 14))

    def draw_start_overlay(self):
        title = self.font_large.render("抓动物游戏", True, (255, 245, 210))
        subtitle = self.font_medium.render("点击动物气泡, 听名字和叫声", True, (240, 240, 255))
        hint = self.font_small.render("移动小手去抓小动物", True, (215, 228, 242))
        exit_hint = self.font_small.render(self._exit_hint(), True, (210, 220, 235))

        card_w = min(960, self.screen_w - 80)
        card_h = 250
        card_x = self.screen_w // 2 - card_w // 2
        card_y = self.screen_h // 2 - card_h // 2
        pygame.draw.rect(self.screen, (18, 28, 52), (card_x, card_y, card_w, card_h), border_radius=28)
        pygame.draw.rect(self.screen, (255, 220, 120), (card_x, card_y, card_w, card_h), 4, border_radius=28)

        self.screen.blit(title, title.get_rect(center=(self.screen_w // 2, card_y + 52)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.screen_w // 2, card_y + 112)))
        self.screen.blit(hint, hint.get_rect(center=(self.screen_w // 2, card_y + 158)))
        self.screen.blit(exit_hint, exit_hint.get_rect(center=(self.screen_w // 2, card_y + 202)))

        start_x = self.screen_w // 2 - 210
        for idx, animal in enumerate(ANIMAL_DATA[:4]):
            bubble_x = start_x + idx * 140
            bubble_y = card_y - 26
            pygame.draw.circle(self.screen, animal["base_color"], (bubble_x, bubble_y), 34)
            image = self.animal_assets.scaled_image_for(animal, 62)
            if image is not None:
                self.screen.blit(image, image.get_rect(center=(bubble_x, bubble_y)))
            pygame.draw.circle(self.screen, (255, 255, 255), (bubble_x, bubble_y), 34, 3)

    def draw_custom_cursor(self, pos):
        x, y = pos
        self.cursor_pulse += 0.1
        squeeze = math.sin(self.cursor_pulse) * 2
        skin = (255, 224, 189)
        outline = (120, 85, 60)

        palm = pygame.Rect(x - 10, y + 6, 22, 24)
        pygame.draw.ellipse(self.screen, skin, palm)
        pygame.draw.ellipse(self.screen, outline, palm, 2)

        finger_width = 8
        base_y = y - 2
        finger_heights = [28, 33, 30, 22]
        finger_offsets = [-10, -2, 6, 14]
        for offset, height in zip(finger_offsets, finger_heights):
            rect = pygame.Rect(x + offset, base_y - height + int(squeeze), finger_width, height)
            pygame.draw.ellipse(self.screen, skin, rect)
            pygame.draw.ellipse(self.screen, outline, rect, 2)

        thumb = [(x - 6, y + 16), (x - 20, y + 8), (x - 24, y + 16), (x - 12, y + 24)]
        pygame.draw.polygon(self.screen, skin, thumb)
        pygame.draw.polygon(self.screen, outline, thumb, 2)
        pygame.draw.circle(self.screen, (255, 255, 255), (x + 10, y + 2), 4)

    def draw_stars_bg(self):
        for star in self.stars:
            star["twinkle"] += star["speed"]
            brightness = int(150 + 105 * math.sin(star["twinkle"]))
            color = (brightness, brightness, brightness)
            sz = max(1, int(star["size"] * (0.7 + 0.3 * math.sin(star["twinkle"]))))
            pygame.draw.circle(self.screen, color, (int(star["x"]), int(star["y"])), sz)

    def auto_spawn_bubbles(self):
        if self.frame_count >= self.next_bubble_time:
            x = random.randint(50, self.screen_w - 50)
            self.bubbles.append(Bubble(x, self.screen_h + 30, self.screen_h, self.animal_assets))
            self.next_bubble_time = self.frame_count + random.randint(60, 180)

    def draw_interaction_counter(self):
        if self.total_interactions > 0:
            text = self.font_small.render(f"  {self.total_interactions}  ", True, (180, 180, 200))
            star_text = self.font_medium.render("*", True, (255, 220, 50))
            self.screen.blit(star_text, (10, self.screen_h - 50))
            self.screen.blit(text, (35, self.screen_h - 40))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pass
                elif event.type == pygame.KEYDOWN:
                    if event.key not in (pygame.K_ESCAPE, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.handle_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, event.button)
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_trail.add(event.pos[0], event.pos[1])
                    self.airplane.move_toward(event.pos[0], event.pos[1])

            self.frame_count += 1
            self.bg_hue = (self.bg_hue + BG_COLOR_CYCLE_SPEED * 360 / FPS) % 360
            exit_elapsed = self.check_exit_combo()

            self.particles = [particle for particle in self.particles if particle.update()]
            if len(self.particles) > 500:
                self.particles = self.particles[-500:]

            self.floating_chars = [item for item in self.floating_chars if item.update()]
            if len(self.floating_chars) > 20:
                self.floating_chars = self.floating_chars[-20:]

            self.bubbles = [bubble for bubble in self.bubbles if bubble.update()]
            if len(self.bubbles) > 15:
                self.bubbles = self.bubbles[-15:]

            if self.captured_overlay is not None and not self.captured_overlay.update():
                self.captured_overlay = None

            self.airplane.update()
            self.auto_spawn_bubbles()

            bg = self._hue_to_rgb(self.bg_hue, saturation=0.18, lightness=0.22)
            self.screen.fill(bg)
            self.draw_stars_bg()
            self.mouse_trail.draw(self.screen)

            for bubble in self.bubbles:
                bubble.draw(self.screen)
            if self.show_airplane:
                self.airplane.draw(self.screen)
            for particle in self.particles:
                particle.draw(self.screen)
            for floating_char in self.floating_chars:
                floating_char.draw(self.screen)

            self.draw_interaction_counter()
            self.draw_exit_indicator(exit_elapsed)
            if self._show_start_overlay():
                self.draw_start_overlay()
            if self.captured_overlay is not None:
                self.captured_overlay.draw(self.screen)

            self.draw_custom_cursor(pygame.mouse.get_pos())
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.event.set_grab(False)
        if hasattr(pygame.event, "set_keyboard_grab"):
            pygame.event.set_keyboard_grab(False)
        pygame.mouse.set_visible(True)
        pygame.quit()
        sys.exit(0)
