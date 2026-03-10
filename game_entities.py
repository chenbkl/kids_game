import math
import random
import time

import pygame

from game_config import ANIMAL_DATA, COLORS, pick_display_font


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "life", "max_life",
                 "size", "shape", "gravity", "shrink")

    def __init__(self, x, y, color=None, speed=None, size=None, shape=None,
                 life=None, gravity=0.1, shrink=True):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        spd = speed or random.uniform(2, 8)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.color = color or random.choice(COLORS)
        self.max_life = life or random.uniform(30, 80)
        self.life = self.max_life
        self.size = size or random.uniform(4, 12)
        self.shape = shape or random.choice(["circle", "square", "star"])
        self.gravity = gravity
        self.shrink = shrink

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.99
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, self.life / self.max_life)
        sz = self.size * alpha if self.shrink else self.size
        if sz < 1:
            return
        r, g, b = self.color
        color = (min(255, int(r * alpha + 255 * (1 - alpha) * 0.3)),
                 min(255, int(g * alpha + 255 * (1 - alpha) * 0.3)),
                 min(255, int(b * alpha + 255 * (1 - alpha) * 0.3)))

        ix, iy, isz = int(self.x), int(self.y), max(1, int(sz))

        if self.shape == "circle":
            pygame.draw.circle(surface, color, (ix, iy), isz)
        elif self.shape == "square":
            rect = pygame.Rect(ix - isz, iy - isz, isz * 2, isz * 2)
            pygame.draw.rect(surface, color, rect)
        elif self.shape == "star":
            self._draw_star(surface, color, ix, iy, isz)

    @staticmethod
    def _draw_star(surface, color, cx, cy, size):
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            radius = size if i % 2 == 0 else size * 0.4
            points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)


class FloatingChar:
    def __init__(self, char, x, y, font_large, font_small):
        self.char = char
        self.x = x
        self.y = y
        self.font_large = font_large
        self.font_small = font_small
        self.color = random.choice(COLORS)
        self.life = 180
        self.max_life = 180
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-2, -0.5)
        self.angle = 0
        self.angle_speed = random.uniform(-3, 3)
        self.scale = 0.0
        self.max_scale = random.uniform(0.8, 1.2)

    def update(self):
        self.life -= 1
        self.x += self.vx
        self.y += self.vy
        self.angle += self.angle_speed

        progress = 1 - (self.life / self.max_life)
        if progress < 0.15:
            self.scale = (progress / 0.15) * self.max_scale
        elif progress > 0.7:
            self.scale = ((1 - progress) / 0.3) * self.max_scale
        else:
            self.scale = self.max_scale

        return self.life > 0

    def draw(self, surface):
        if self.scale < 0.05:
            return

        size = max(10, int(120 * self.scale))
        try:
            font = pygame.font.SysFont(pick_display_font(), size, bold=True)
        except Exception:
            font = self.font_large

        text_surf = font.render(self.char, True, self.color)
        if abs(self.angle) > 0.5:
            text_surf = pygame.transform.rotate(text_surf, self.angle)

        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surf, rect)


class Airplane:
    def __init__(self, screen_w, screen_h):
        self.x = screen_w // 2
        self.y = screen_h // 2
        self.target_x = self.x
        self.target_y = self.y
        self.angle = 0
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.trail = []
        self.size = 30

    def move_toward(self, tx, ty):
        self.target_x = tx
        self.target_y = ty

    def update(self):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.x += dx * 0.08
        self.y += dy * 0.08
        self.x = max(0, min(self.screen_w, self.x))
        self.y = max(0, min(self.screen_h, self.y))

        if abs(dx) > 1 or abs(dy) > 1:
            self.angle = math.degrees(math.atan2(-dy, dx))

        self.trail.append((int(self.x), int(self.y), random.choice(COLORS)))
        if len(self.trail) > 30:
            self.trail.pop(0)

    def draw(self, surface):
        for i, (tx, ty, tc) in enumerate(self.trail):
            alpha = i / len(self.trail)
            sz = max(1, int(6 * alpha))
            r, g, b = tc
            color = (min(255, int(r * alpha)), min(255, int(g * alpha)),
                     min(255, int(b * alpha)))
            pygame.draw.circle(surface, color, (tx, ty), sz)

        cx, cy = int(self.x), int(self.y)
        rad = math.radians(self.angle)
        size = self.size
        nose = (cx + int(size * math.cos(rad)), cy - int(size * math.sin(rad)))
        left = (cx + int(size * 0.6 * math.cos(rad + 2.5)),
                cy - int(size * 0.6 * math.sin(rad + 2.5)))
        right = (cx + int(size * 0.6 * math.cos(rad - 2.5)),
                 cy - int(size * 0.6 * math.sin(rad - 2.5)))
        tail = (cx - int(size * 0.7 * math.cos(rad)),
                cy + int(size * 0.7 * math.sin(rad)))

        pygame.draw.polygon(surface, (255, 220, 50), [nose, left, tail, right])
        pygame.draw.polygon(surface, (255, 180, 0), [nose, left, tail, right], 2)
        pygame.draw.circle(
            surface,
            (100, 200, 255),
            (cx + int(size * 0.3 * math.cos(rad)), cy - int(size * 0.3 * math.sin(rad))),
            6,
        )


class Bubble:
    def __init__(self, x, y, screen_h, asset_library=None):
        self.x = x
        self.y = y
        self.radius = random.randint(30, 52)
        self.animal = random.choice(ANIMAL_DATA)
        self.color = self.animal["base_color"]
        self.vy = random.uniform(-3, -1)
        self.vx = random.uniform(-0.5, 0.5)
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.02, 0.06)
        self.screen_h = screen_h
        self.asset_library = asset_library
        self.popped = False
        self.pop_particles = []

    def update(self):
        if self.popped:
            alive = []
            for particle in self.pop_particles:
                if particle.update():
                    alive.append(particle)
            self.pop_particles = alive
            return len(self.pop_particles) > 0

        self.y += self.vy
        self.wobble += self.wobble_speed
        self.x += math.sin(self.wobble) * 0.5 + self.vx
        if self.y + self.radius < -50:
            return False
        return True

    def pop(self):
        if not self.popped:
            self.popped = True
            for _ in range(12):
                self.pop_particles.append(
                    Particle(self.x, self.y, self.color, speed=4, life=30)
                )

    def contains(self, mx, my):
        return math.hypot(mx - self.x, my - self.y) <= self.radius

    def draw(self, surface):
        if self.popped:
            for particle in self.pop_particles:
                particle.draw(surface)
            return

        ix, iy = int(self.x), int(self.y)
        r, g, b = self.color
        glow_radius = self.radius + 8
        glow = (min(255, r + 30), min(255, g + 30), min(255, b + 30))
        pygame.draw.circle(surface, glow, (ix, iy), glow_radius)
        pygame.draw.circle(surface, (r, g, b), (ix, iy), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (ix, iy), self.radius, 3)

        animal_image = None
        if self.asset_library is not None:
            animal_image = self.asset_library.scaled_image_for(self.animal, self.radius * 2)

        if animal_image is not None:
            image_rect = animal_image.get_rect(center=(ix, iy + 2))
            surface.blit(animal_image, image_rect)
        else:
            self._draw_label(surface, ix, iy)

        highlight_rect = pygame.Rect(ix - self.radius // 2, iy - self.radius // 2, self.radius, self.radius // 2)
        pygame.draw.ellipse(surface, (255, 255, 255), highlight_rect, 2)
        pygame.draw.circle(surface, (255, 255, 255), (ix, iy), self.radius, 3)

    def _draw_label(self, surface, ix, iy):
        font_size = max(14, int(self.radius * 0.7))
        font = pygame.font.SysFont(pick_display_font(), font_size, bold=True)
        text = font.render(self.animal["label"], True, self.animal["accent_color"])
        surface.blit(text, text.get_rect(center=(ix, iy)))


class CapturedAnimalCelebration:
    def __init__(self, animal, asset_library, font_large, font_medium, screen_w, screen_h):
        self.animal = animal
        self.asset_library = asset_library
        self.font_large = font_large
        self.font_medium = font_medium
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.life = 150
        self.max_life = 150

    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        progress = 1 - (self.life / self.max_life)
        pulse = 1.0 + 0.03 * math.sin(progress * math.pi * 8)

        card_w = min(720, self.screen_w - 120)
        card_h = min(620, self.screen_h - 100)
        card_x = self.screen_w // 2 - card_w // 2
        card_y = self.screen_h // 2 - card_h // 2

        pygame.draw.rect(surface, (255, 248, 226), (card_x, card_y, card_w, card_h), border_radius=32)
        pygame.draw.rect(surface, self.animal["accent_color"], (card_x, card_y, card_w, card_h), 6, border_radius=32)

        banner = self.font_medium.render("抓到啦!", True, self.animal["accent_color"])
        surface.blit(banner, banner.get_rect(center=(self.screen_w // 2, card_y + 50)))

        title = self.font_large.render(self.animal["label"], True, (42, 48, 78))
        surface.blit(title, title.get_rect(center=(self.screen_w // 2, card_y + 132)))

        frame_w = min(320, card_w - 120)
        frame_h = min(260, card_h - 260)
        frame_x = self.screen_w // 2 - frame_w // 2
        frame_y = card_y + 188

        shadow = pygame.Surface((frame_w + 24, frame_h + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (24, 32, 56, 55), (0, 0, frame_w + 24, frame_h + 24), border_radius=34)
        surface.blit(shadow, (frame_x - 12, frame_y + 12))

        pygame.draw.rect(surface, (255, 255, 255), (frame_x, frame_y, frame_w, frame_h), border_radius=28)
        pygame.draw.rect(surface, (245, 229, 184), (frame_x + 8, frame_y + 8, frame_w - 16, frame_h - 16), border_radius=24)
        pygame.draw.rect(surface, self.animal["accent_color"], (frame_x, frame_y, frame_w, frame_h), 4, border_radius=28)

        image = self.asset_library.scaled_popup_image_for(self.animal, int(232 * pulse))
        if image is not None:
            image_rect = image.get_rect(center=(self.screen_w // 2, frame_y + frame_h // 2 + 6))
            surface.blit(image, image_rect)

        subtitle = self.font_medium.render(self.animal["name"], True, (90, 98, 125))
        surface.blit(subtitle, subtitle.get_rect(center=(self.screen_w // 2, card_y + card_h - 52)))


class MouseTrail:
    def __init__(self):
        self.points = []
        self.max_points = 50

    def add(self, x, y):
        self.points.append((x, y, time.time()))
        if len(self.points) > self.max_points:
            self.points.pop(0)

    def draw(self, surface):
        if len(self.points) < 2:
            return
        for i in range(1, len(self.points)):
            alpha = i / len(self.points)
            hue = (i * 12) % 360
            color = self._hue_to_rgb(hue)
            width = max(1, int(6 * alpha))
            p1 = (int(self.points[i-1][0]), int(self.points[i-1][1]))
            p2 = (int(self.points[i][0]), int(self.points[i][1]))
            pygame.draw.line(surface, color, p1, p2, width)

    @staticmethod
    def _hue_to_rgb(hue):
        h = hue / 60.0
        c = 255
        x = int(c * (1 - abs(h % 2 - 1)))
        c = int(c)
        if h < 1:
            return (c, x, 0)
        if h < 2:
            return (x, c, 0)
        if h < 3:
            return (0, c, x)
        if h < 4:
            return (0, x, c)
        if h < 5:
            return (x, 0, c)
        return (c, 0, x)
