"""
Water Sort Puzzle - Playable Demo
Part of SuperGameApp project
Built with Pygame for desktop testing
"""

import pygame
import sys
import random
import copy
import math
import colorsys

# ─────────────────────────── CONFIG ───────────────────────────

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 750
FPS = 60
LAYERS_PER_TUBE = 4

# Theme
BG_TOP = (18, 18, 35)
BG_BOTTOM = (8, 8, 18)

LIQUID_COLORS = {
    1: (231, 76, 60),     # Red
    2: (52, 152, 219),    # Blue
    3: (46, 204, 113),    # Green
    4: (241, 196, 15),    # Yellow
    5: (230, 126, 34),    # Orange
    6: (155, 89, 182),    # Purple
    7: (26, 188, 156),    # Teal
    8: (233, 30, 99),     # Pink
    9: (121, 85, 72),     # Brown
    10: (100, 181, 246),  # Light Blue
}

LIQUID_HIGHLIGHTS = {}
LIQUID_SHADOWS = {}
for k, (r, g, b) in LIQUID_COLORS.items():
    LIQUID_HIGHLIGHTS[k] = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
    LIQUID_SHADOWS[k] = (max(0, r - 40), max(0, g - 40), max(0, b - 40))


# ─────────────────────────── LEVEL GENERATOR ───────────────────────────

def get_difficulty(level):
    """Returns (num_colors, num_empties) based on level."""
    if level <= 3:    return 3, 2
    if level <= 8:    return 4, 2
    if level <= 15:   return 5, 2
    if level <= 25:   return 6, 2
    if level <= 40:   return 7, 2
    if level <= 60:   return 8, 2
    if level <= 80:   return 9, 2
    return 10, 2


def generate_level(level_num):
    """
    Generate a solvable level by creating a flat pool of colors,
    shuffling them, then distributing into tubes.
    This guarantees the puzzle is solvable (since it came from a solved state).
    """
    rng = random.Random(level_num * 31337 + 97)
    colors, empties = get_difficulty(level_num)

    # Create pool: each color appears LAYERS_PER_TUBE times
    pool = []
    for c in range(1, colors + 1):
        pool.extend([c] * LAYERS_PER_TUBE)

    # Shuffle until no tube is already solved
    for attempt in range(100):
        rng.shuffle(pool)

        tubes = []
        for i in range(colors):
            start = i * LAYERS_PER_TUBE
            tube = pool[start:start + LAYERS_PER_TUBE]
            tubes.append(tube)

        # Check no tube is already single-color
        any_solved = any(len(set(t)) == 1 for t in tubes)
        if not any_solved:
            break

    # Add empty tubes
    for _ in range(empties):
        tubes.append([])

    return tubes


def is_tube_complete(tube):
    return len(tube) == LAYERS_PER_TUBE and len(set(tube)) == 1


def check_win(tubes):
    for tube in tubes:
        if tube and not is_tube_complete(tube):
            return False
    return True


# ─────────────────────────── DRAWING HELPERS ───────────────────────────

def draw_gradient_rect(surface, rect, color_top, color_bottom):
    """Draw a vertical gradient filled rectangle."""
    x, y, w, h = rect
    for row in range(h):
        t = row / max(1, h - 1)
        r = int(color_top[0] * (1 - t) + color_bottom[0] * t)
        g = int(color_top[1] * (1 - t) + color_bottom[1] * t)
        b = int(color_top[2] * (1 - t) + color_bottom[2] * t)
        pygame.draw.line(surface, (r, g, b), (x, y + row), (x + w - 1, y + row))


def draw_rounded_rect(surface, color, rect, radius, alpha=255):
    """Draw a rounded rectangle with optional alpha."""
    if alpha < 255:
        temp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(temp, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surface.blit(temp, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_star(surface, cx, cy, outer_r, inner_r, color, rotation=0):
    """Draw a 5-pointed star."""
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90 + rotation)
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(surface, color, points)
    # Lighter outline
    pygame.draw.polygon(surface, tuple(min(255, c + 30) for c in color), points, 2)


# ─────────────────────────── PARTICLE SYSTEM ───────────────────────────

class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, size=None, gravity=True):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-4, 4)
        self.vy = vy if vy is not None else random.uniform(-8, -2)
        self.life = 1.0
        self.max_life = random.uniform(0.8, 1.5)
        self.size = size if size is not None else random.uniform(3, 8)
        self.gravity = gravity
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-200, 200)

    def update(self, dt):
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        if self.gravity:
            self.vy += 12 * dt
        self.life -= dt / self.max_life
        self.rotation += self.rot_speed * dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(self.life * 255)))
        s = max(1, int(self.size * self.life))
        if s < 1:
            return
        temp = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*self.color[:3], alpha), (s + 1, s + 1), s)
        # Glow
        if s > 2:
            pygame.draw.circle(temp, (*self.color[:3], alpha // 3), (s + 1, s + 1), s + 1)
        surface.blit(temp, (int(self.x) - s - 1, int(self.y) - s - 1))


# ─────────────────────────── BUTTON ───────────────────────────

class Button:
    def __init__(self, x, y, w, h, text, font, color=(50, 55, 75), icon_text=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.base_color = color
        self.hover_color = tuple(min(255, c + 25) for c in color)
        self.press_color = tuple(max(0, c - 10) for c in color)
        self.icon_text = icon_text
        self.hovered = False
        self.scale = 1.0
        self.target_scale = 1.0

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.target_scale = 1.05 if self.hovered else 1.0
        self.scale += (self.target_scale - self.scale) * min(1, dt * 12)

    def draw(self, surface):
        # Scaled rect
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        r = pygame.Rect(x, y, w, h)

        color = self.hover_color if self.hovered else self.base_color

        # Shadow
        shadow = pygame.Rect(x + 2, y + 3, w, h)
        draw_rounded_rect(surface, (0, 0, 0), shadow, 10, 60)

        # Button body
        draw_rounded_rect(surface, color, r, 10)

        # Top highlight
        highlight = pygame.Rect(x + 2, y + 2, w - 4, h // 3)
        draw_rounded_rect(surface, (255, 255, 255), highlight, 8, 15)

        # Border
        pygame.draw.rect(surface, tuple(min(255, c + 40) for c in color), r, 1, border_radius=10)

        # Text
        txt = self.font.render(self.text, True, (230, 232, 240))
        tx = r.centerx - txt.get_width() // 2
        ty = r.centery - txt.get_height() // 2
        if self.icon_text:
            icon = self.font.render(self.icon_text, True, (230, 232, 240))
            total_w = icon.get_width() + 6 + txt.get_width()
            tx = r.centerx - total_w // 2 + icon.get_width() + 6
            surface.blit(icon, (r.centerx - total_w // 2, ty))
        surface.blit(txt, (tx, ty))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


# ─────────────────────────── TUBE DRAWING ───────────────────────────

TUBE_WIDTH = 56
TUBE_HEIGHT = 175
TUBE_INNER = 6
LAYER_H = 36
TUBE_BOTTOM_RADIUS = 14
TUBE_GLASS_COLOR = (45, 50, 70)
TUBE_GLASS_BORDER = (75, 80, 105)
TUBE_GLASS_SHINE = (255, 255, 255, 20)


def draw_tube_glass(surface, x, y, selected=False, complete=False):
    """Draw the glass tube with shine effect."""
    rect = pygame.Rect(x, y, TUBE_WIDTH, TUBE_HEIGHT)

    # Glow for selected
    if selected:
        glow = pygame.Surface((TUBE_WIDTH + 20, TUBE_HEIGHT + 30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 220, 80, 35), (0, 0, TUBE_WIDTH + 20, TUBE_HEIGHT + 30),
                         border_radius=TUBE_BOTTOM_RADIUS + 6)
        surface.blit(glow, (x - 10, y - 10))

    # Complete glow
    if complete:
        glow = pygame.Surface((TUBE_WIDTH + 16, TUBE_HEIGHT + 26), pygame.SRCALPHA)
        pygame.draw.rect(glow, (80, 200, 120, 30), (0, 0, TUBE_WIDTH + 16, TUBE_HEIGHT + 26),
                         border_radius=TUBE_BOTTOM_RADIUS + 4)
        surface.blit(glow, (x - 8, y - 8))

    # Glass body
    glass = pygame.Surface((TUBE_WIDTH, TUBE_HEIGHT), pygame.SRCALPHA)

    # Main body
    pygame.draw.rect(glass, (*TUBE_GLASS_COLOR, 200), (0, 0, TUBE_WIDTH, TUBE_HEIGHT),
                     border_radius=TUBE_BOTTOM_RADIUS)
    # Open top - draw rect to flatten top corners
    pygame.draw.rect(glass, (*TUBE_GLASS_COLOR, 200), (0, 0, TUBE_WIDTH, 20))

    # Border
    border_color = (255, 220, 80) if selected else ((120, 220, 150) if complete else TUBE_GLASS_BORDER)
    # Left wall
    pygame.draw.line(glass, (*border_color, 220), (0, 0), (0, TUBE_HEIGHT - TUBE_BOTTOM_RADIUS), 2)
    # Right wall
    pygame.draw.line(glass, (*border_color, 220), (TUBE_WIDTH - 1, 0),
                     (TUBE_WIDTH - 1, TUBE_HEIGHT - TUBE_BOTTOM_RADIUS), 2)
    # Bottom arc
    pygame.draw.arc(glass, (*border_color, 220),
                    (0, TUBE_HEIGHT - TUBE_BOTTOM_RADIUS * 2, TUBE_WIDTH, TUBE_BOTTOM_RADIUS * 2),
                    math.pi, 2 * math.pi, 2)

    # Shine on left side
    shine = pygame.Surface((8, TUBE_HEIGHT - 30), pygame.SRCALPHA)
    for row in range(shine.get_height()):
        t = row / shine.get_height()
        a = int(25 * (1 - abs(t - 0.3) * 2))
        if a > 0:
            pygame.draw.line(shine, (255, 255, 255, a), (0, row), (7, row))
    glass.blit(shine, (4, 10))

    surface.blit(glass, (x, y))


def draw_liquid_layer(surface, x, y, tube_x, tube_y, color_idx, layer_idx, total_layers):
    """Draw a single liquid layer with gradient and shine."""
    color = LIQUID_COLORS.get(color_idx, (128, 128, 128))
    highlight = LIQUID_HIGHLIGHTS.get(color_idx, color)
    shadow = LIQUID_SHADOWS.get(color_idx, color)

    lx = tube_x + TUBE_INNER
    ly = tube_y + TUBE_HEIGHT - (layer_idx + 1) * LAYER_H
    lw = TUBE_WIDTH - TUBE_INNER * 2
    lh = LAYER_H - 1

    # Bottom layer gets rounded bottom
    radius = TUBE_BOTTOM_RADIUS - 4 if layer_idx == 0 else 3

    layer_surf = pygame.Surface((lw, lh), pygame.SRCALPHA)

    # Main fill with gradient
    for row in range(lh):
        t = row / max(1, lh - 1)
        r = int(highlight[0] * (1 - t) * 0.3 + color[0] * (0.7 + t * 0.3))
        g = int(highlight[1] * (1 - t) * 0.3 + color[1] * (0.7 + t * 0.3))
        b = int(highlight[2] * (1 - t) * 0.3 + color[2] * (0.7 + t * 0.3))
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        pygame.draw.line(layer_surf, (r, g, b, 240), (0, row), (lw - 1, row))

    # Apply rounded rect mask
    mask = pygame.Surface((lw, lh), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, lw, lh), border_radius=radius)

    # Combine
    final = pygame.Surface((lw, lh), pygame.SRCALPHA)
    final.blit(layer_surf, (0, 0))
    # Use mask
    for px in range(lw):
        for py in range(lh):
            if mask.get_at((px, py))[3] == 0:
                final.set_at((px, py), (0, 0, 0, 0))

    surface.blit(final, (lx, ly))

    # Shine strip
    shine_surf = pygame.Surface((lw // 4, lh - 4), pygame.SRCALPHA)
    pygame.draw.rect(shine_surf, (255, 255, 255, 40), (0, 0, lw // 4, lh - 4), border_radius=2)
    surface.blit(shine_surf, (lx + 3, ly + 2))

    # Top surface wave effect for topmost layer
    if layer_idx == total_layers - 1:
        wave_surf = pygame.Surface((lw, 4), pygame.SRCALPHA)
        pygame.draw.rect(wave_surf, (*highlight, 80), (0, 0, lw, 4), border_radius=2)
        surface.blit(wave_surf, (lx, ly))


# ─────────────────────────── MAIN GAME CLASS ───────────────────────────

class WaterSortGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Super Game App — Water Sort Puzzle")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Helvetica", 42, bold=True)
        self.font_large = pygame.font.SysFont("Helvetica", 32, bold=True)
        self.font_medium = pygame.font.SysFont("Helvetica", 22, bold=True)
        self.font_small = pygame.font.SysFont("Helvetica", 17)
        self.font_tiny = pygame.font.SysFont("Helvetica", 13)

        # Pre-render background
        self.bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(self.bg_surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Game state
        self.state = "menu"  # menu, playing, complete
        self.level = 1
        self.coins = 100
        self.moves = 0
        self.selected = -1
        self.tubes = []
        self.undo_stack = []
        self.tube_positions = []
        self.particles = []
        self.buttons = {}
        self.selected_offset_y = 0.0
        self.target_offset_y = 0.0
        self.win_timer = 0
        self.menu_anim = 0

        # Pour animation
        self.pouring = False
        self.pour_from = -1
        self.pour_to = -1
        self.pour_phase = 0
        self.pour_t = 0.0
        self.pour_source_offset = [0.0, 0.0]
        self.pour_data = []

    def load_level(self, level_num):
        self.level = level_num
        self.tubes = generate_level(level_num)
        self.moves = 0
        self.selected = -1
        self.undo_stack = []
        self.particles = []
        self.state = "playing"
        self.pouring = False
        self.win_timer = 0
        self.calculate_positions()
        self.create_buttons()

    def calculate_positions(self):
        self.tube_positions = []
        n = len(self.tubes)
        max_per_row = min(n, 6)
        rows = math.ceil(n / max_per_row)

        base_y = 160

        for i in range(n):
            row = i // max_per_row
            col = i % max_per_row
            tubes_in_row = min(max_per_row, n - row * max_per_row)

            spacing = TUBE_WIDTH + 28
            total_w = tubes_in_row * spacing - 28
            start_x = (SCREEN_WIDTH - total_w) // 2

            x = start_x + col * spacing
            y = base_y + row * (TUBE_HEIGHT + 55)
            self.tube_positions.append([x, y])

    def create_buttons(self):
        btn_y = SCREEN_HEIGHT - 75
        btn_w = 120
        btn_h = 44
        gap = 16
        total = btn_w * 4 + gap * 3
        sx = (SCREEN_WIDTH - total) // 2

        self.buttons = {
            "undo": Button(sx, btn_y, btn_w, btn_h, "Undo", self.font_small, (55, 60, 85)),
            "restart": Button(sx + (btn_w + gap), btn_y, btn_w, btn_h, "Restart", self.font_small, (55, 60, 85)),
            "hint": Button(sx + (btn_w + gap) * 2, btn_y, btn_w, btn_h, "Hint", self.font_small, (70, 55, 85)),
            "menu": Button(sx + (btn_w + gap) * 3, btn_y, btn_w, btn_h, "Menu", self.font_small, (55, 60, 85)),
        }

    def get_tube_at(self, mx, my):
        for i, (tx, ty) in enumerate(self.tube_positions):
            r = pygame.Rect(tx - 8, ty - 15, TUBE_WIDTH + 16, TUBE_HEIGHT + 30)
            if r.collidepoint(mx, my):
                return i
        return -1

    def can_pour(self, source_idx, target_idx):
        source = self.tubes[source_idx]
        target = self.tubes[target_idx]
        if not source:
            return False
        if len(target) >= LAYERS_PER_TUBE:
            return False
        if not target:
            return True
        return source[-1] == target[-1]

    def do_pour(self, source_idx, target_idx):
        source = self.tubes[source_idx]
        target = self.tubes[target_idx]

        self.undo_stack.append(copy.deepcopy(self.tubes))

        top_color = source[-1]
        moved = 0
        while source and source[-1] == top_color and len(target) < LAYERS_PER_TUBE:
            target.append(source.pop())
            moved += 1

        self.moves += 1
        return moved

    def start_pour_animation(self, from_idx, to_idx):
        self.pouring = True
        self.pour_from = from_idx
        self.pour_to = to_idx
        self.pour_phase = 0  # 0=lift, 1=move, 2=pour+transfer, 3=return
        self.pour_t = 0.0
        self.pour_source_offset = [0.0, 0.0]

    def update_pour(self, dt):
        if not self.pouring:
            return

        speed = 4.5
        self.pour_t += dt * speed

        sx, sy = self.tube_positions[self.pour_from]
        tx, ty = self.tube_positions[self.pour_to]

        t = min(1.0, self.pour_t)
        t = t * t * (3 - 2 * t)  # smoothstep

        if self.pour_phase == 0:  # Lift
            self.pour_source_offset = [0, -55 * t]
            if self.pour_t >= 1.0:
                self.pour_phase = 1
                self.pour_t = 0.0

        elif self.pour_phase == 1:  # Move horizontally
            dx = (tx - sx) + (25 if tx > sx else -25)
            self.pour_source_offset = [dx * t, -55]
            if self.pour_t >= 1.0:
                self.pour_phase = 2
                self.pour_t = 0.0
                # Do the actual pour
                self.do_pour(self.pour_from, self.pour_to)
                # Spawn pour particles
                px = tx + TUBE_WIDTH // 2
                py = ty
                color = LIQUID_COLORS.get(self.tubes[self.pour_to][-1], (200, 200, 200))
                for _ in range(8):
                    self.particles.append(Particle(px + random.randint(-10, 10), py,
                                                   color, random.uniform(-1, 1),
                                                   random.uniform(-3, 0), random.uniform(2, 5)))

        elif self.pour_phase == 2:  # Wait a beat
            dx = (tx - sx) + (25 if tx > sx else -25)
            self.pour_source_offset = [dx, -55]
            if self.pour_t >= 0.5:
                self.pour_phase = 3
                self.pour_t = 0.0

        elif self.pour_phase == 3:  # Return
            dx = (tx - sx) + (25 if tx > sx else -25)
            self.pour_source_offset = [dx * (1 - t), -55 * (1 - t)]
            if self.pour_t >= 1.0:
                self.pouring = False
                self.pour_source_offset = [0, 0]
                # Check win
                if check_win(self.tubes):
                    self.state = "complete"
                    self.win_timer = 0
                    self.spawn_win_particles()

    def undo(self):
        if not self.undo_stack or self.pouring:
            return
        self.tubes = self.undo_stack.pop()
        self.moves = max(0, self.moves - 1)
        self.selected = -1

    def spawn_win_particles(self):
        for _ in range(80):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            c = random.choice(list(LIQUID_COLORS.values()))
            self.particles.append(Particle(x, y, c,
                                           random.uniform(-5, 5),
                                           random.uniform(-10, -3),
                                           random.uniform(4, 10)))

    def calculate_stars(self):
        colors, _ = get_difficulty(self.level)
        optimal = colors * 2
        if self.moves <= optimal:
            return 3
        if self.moves <= optimal * 2:
            return 2
        return 1

    # ─── DRAW METHODS ───

    def draw_bg(self):
        self.screen.blit(self.bg_surface, (0, 0))

    def draw_top_bar(self):
        # Bar background
        bar = pygame.Surface((SCREEN_WIDTH, 75), pygame.SRCALPHA)
        bar.fill((20, 22, 40, 230))
        self.screen.blit(bar, (0, 0))
        pygame.draw.line(self.screen, (50, 55, 75), (0, 75), (SCREEN_WIDTH, 75), 1)

        # Level
        colors, _ = get_difficulty(self.level)
        diff_map = {3: "Easy", 4: "Normal", 5: "Medium", 6: "Hard", 7: "Expert",
                    8: "Master", 9: "Insane", 10: "Legendary"}
        diff = diff_map.get(colors, "")

        level_text = self.font_large.render(f"Level {self.level}", True, (230, 232, 245))
        self.screen.blit(level_text, (30, 12))

        diff_text = self.font_tiny.render(diff, True, (140, 145, 170))
        self.screen.blit(diff_text, (30, 48))

        # Moves
        moves_text = self.font_medium.render(f"Moves: {self.moves}", True, (180, 185, 200))
        mx = SCREEN_WIDTH // 2 - moves_text.get_width() // 2
        self.screen.blit(moves_text, (mx, 25))

        # Coins
        coin_x = SCREEN_WIDTH - 130
        pygame.draw.circle(self.screen, (255, 215, 0), (coin_x, 38), 14)
        pygame.draw.circle(self.screen, (200, 170, 0), (coin_x, 38), 14, 2)
        # $ symbol
        dollar = self.font_tiny.render("$", True, (180, 150, 0))
        self.screen.blit(dollar, (coin_x - dollar.get_width() // 2, 31))

        coin_text = self.font_medium.render(str(self.coins), True, (255, 215, 0))
        self.screen.blit(coin_text, (coin_x + 20, 24))

    def draw_tubes(self, dt):
        for i, tube in enumerate(self.tubes):
            tx, ty = self.tube_positions[i]

            # Apply pour offset
            offset_x, offset_y = 0, 0
            if self.pouring and self.pour_from == i:
                offset_x = self.pour_source_offset[0]
                offset_y = self.pour_source_offset[1]

            # Selection bounce
            if i == self.selected and not self.pouring:
                offset_y = -22

            dx = tx + offset_x
            dy = ty + offset_y

            complete = is_tube_complete(tube)
            selected = (i == self.selected and not self.pouring)

            # Draw glass
            draw_tube_glass(self.screen, int(dx), int(dy), selected, complete)

            # Draw liquid layers
            for li, color_idx in enumerate(tube):
                draw_liquid_layer(self.screen, 0, 0, int(dx), int(dy), color_idx, li, len(tube))

            # Complete checkmark
            if complete:
                cx = int(dx) + TUBE_WIDTH // 2
                cy = int(dy) - 12
                pygame.draw.circle(self.screen, (80, 200, 120), (cx, cy), 11)
                pygame.draw.circle(self.screen, (60, 170, 100), (cx, cy), 11, 2)
                check = self.font_tiny.render("✓", True, (255, 255, 255))
                self.screen.blit(check, (cx - check.get_width() // 2, cy - check.get_height() // 2))

    def draw_complete_screen(self, dt):
        self.win_timer += dt

        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = min(170, int(self.win_timer * 400))
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        if self.win_timer < 0.3:
            return None, None

        # Panel
        pw, ph = 420, 370
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2

        # Panel shadow
        draw_rounded_rect(self.screen, (0, 0, 0), (px + 4, py + 6, pw, ph), 20, 100)

        # Panel body
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        draw_gradient_rect(panel, (0, 0, pw, ph), (40, 45, 70), (25, 28, 48))
        # Round the corners
        mask = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), (0, 0, pw, ph), border_radius=20)
        final_panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        final_panel.blit(panel, (0, 0))
        for x_p in range(pw):
            for y_p in range(ph):
                if mask.get_at((x_p, y_p))[3] == 0:
                    final_panel.set_at((x_p, y_p), (0, 0, 0, 0))
        self.screen.blit(final_panel, (px, py))
        pygame.draw.rect(self.screen, (70, 75, 100), (px, py, pw, ph), 2, border_radius=20)

        # Title
        title = self.font_large.render("Level Complete!", True, (80, 220, 130))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, py + 30))

        # Stars
        stars = self.calculate_stars()
        star_y = py + 95
        for i in range(3):
            star_x = SCREEN_WIDTH // 2 - 65 + i * 55
            if i < stars:
                draw_star(self.screen, star_x, star_y, 22, 9, (255, 210, 50))
            else:
                draw_star(self.screen, star_x, star_y, 22, 9, (50, 55, 70))

        # Stats
        moves_t = self.font_medium.render(f"Moves: {self.moves}", True, (200, 205, 220))
        self.screen.blit(moves_t, (SCREEN_WIDTH // 2 - moves_t.get_width() // 2, py + 140))

        reward = stars * 10
        reward_t = self.font_medium.render(f"+ {reward} coins", True, (255, 215, 0))
        self.screen.blit(reward_t, (SCREEN_WIDTH // 2 - reward_t.get_width() // 2, py + 175))

        # Buttons
        btn_w, btn_h = 160, 48
        gap = 20
        bx1 = SCREEN_WIDTH // 2 - btn_w - gap // 2
        bx2 = SCREEN_WIDTH // 2 + gap // 2
        by = py + 255

        mouse = pygame.mouse.get_pos()

        next_rect = pygame.Rect(bx1, by, btn_w, btn_h)
        replay_rect = pygame.Rect(bx2, by, btn_w, btn_h)

        for rect, text, base_c in [(next_rect, "Next Level", (60, 180, 100)),
                                    (replay_rect, "Replay", (55, 65, 95))]:
            hovered = rect.collidepoint(mouse)
            c = tuple(min(255, x + 20) for x in base_c) if hovered else base_c

            draw_rounded_rect(self.screen, (0, 0, 0), (rect.x + 2, rect.y + 3, btn_w, btn_h), 12, 60)
            draw_rounded_rect(self.screen, c, rect, 12)
            pygame.draw.rect(self.screen, tuple(min(255, x + 30) for x in c), rect, 1, border_radius=12)

            t = self.font_medium.render(text, True, (240, 242, 250))
            self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

        return next_rect, replay_rect

    def draw_menu(self, dt):
        self.draw_bg()
        self.menu_anim += dt

        # Floating particles in background
        if random.random() < 0.1:
            c = random.choice(list(LIQUID_COLORS.values()))
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 10,
                c, random.uniform(-0.5, 0.5), random.uniform(-1.5, -0.5),
                random.uniform(2, 5), gravity=False
            ))

        # Title
        title = self.font_title.render("Water Sort", True, (230, 235, 250))
        subtitle = self.font_large.render("Puzzle", True, (100, 180, 230))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 130))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        # Animated preview tubes
        preview_colors = [1, 2, 3, 4, 5]
        for i, ci in enumerate(preview_colors):
            tx = 160 + i * 120
            ty = 270 + int(math.sin(self.menu_anim * 2 + i * 0.8) * 8)
            draw_tube_glass(self.screen, tx, ty, False, False)
            c = LIQUID_COLORS[ci]
            for j in range(LAYERS_PER_TUBE):
                draw_liquid_layer(self.screen, 0, 0, tx, ty, ci, j, LAYERS_PER_TUBE)

        # Super Game App badge
        badge = self.font_tiny.render("SUPER GAME APP", True, (100, 105, 130))
        self.screen.blit(badge, (SCREEN_WIDTH // 2 - badge.get_width() // 2, 245))

        # Play button
        play_rect = pygame.Rect(SCREEN_WIDTH // 2 - 110, 510, 220, 60)
        mouse = pygame.mouse.get_pos()
        hovered = play_rect.collidepoint(mouse)
        scale = 1.05 if hovered else 1.0
        pw = int(220 * scale)
        ph = int(60 * scale)
        pr = pygame.Rect(SCREEN_WIDTH // 2 - pw // 2, 510 + 30 - ph // 2, pw, ph)

        draw_rounded_rect(self.screen, (0, 0, 0), (pr.x + 3, pr.y + 4, pw, ph), 14, 80)
        base_green = (65, 190, 110) if not hovered else (85, 210, 130)
        draw_rounded_rect(self.screen, base_green, pr, 14)
        pygame.draw.rect(self.screen, (100, 230, 150), pr, 1, border_radius=14)

        play_text = self.font_large.render("PLAY", True, (255, 255, 255))
        self.screen.blit(play_text, (pr.centerx - play_text.get_width() // 2,
                                     pr.centery - play_text.get_height() // 2))

        # Level indicator
        lvl_text = self.font_small.render(f"Level {self.level}", True, (140, 145, 170))
        self.screen.blit(lvl_text, (SCREEN_WIDTH // 2 - lvl_text.get_width() // 2, 590))

        # Coins
        coin_text = self.font_small.render(f"Coins: {self.coins}", True, (255, 215, 0))
        self.screen.blit(coin_text, (SCREEN_WIDTH // 2 - coin_text.get_width() // 2, 620))

        # Footer
        footer = self.font_tiny.render("Built with Python + Pygame", True, (50, 55, 75))
        self.screen.blit(footer, (SCREEN_WIDTH // 2 - footer.get_width() // 2, SCREEN_HEIGHT - 30))

        # Particles
        for p in self.particles:
            p.draw(self.screen)

        return play_rect

    # ─── MAIN LOOP ───

    def run(self):
        running = True
        next_btn = None
        replay_btn = None
        play_btn = None

        while running:
            dt = self.clock.tick(FPS) / 1000.0
            mouse = pygame.mouse.get_pos()

            # ─── EVENTS ───
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "playing":
                            self.state = "menu"
                        elif self.state == "menu":
                            running = False
                    if event.key == pygame.K_u and self.state == "playing":
                        self.undo()
                    if event.key == pygame.K_r and self.state == "playing":
                        self.load_level(self.level)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "menu":
                        if play_btn and play_btn.collidepoint(mouse):
                            self.load_level(self.level)

                    elif self.state == "playing" and not self.pouring:
                        handled = False
                        for name, btn in self.buttons.items():
                            if btn.clicked(mouse):
                                if name == "undo":
                                    self.undo()
                                elif name == "restart":
                                    self.load_level(self.level)
                                elif name == "hint":
                                    pass  # TODO: hint system
                                elif name == "menu":
                                    self.state = "menu"
                                handled = True
                                break

                        if not handled:
                            clicked = self.get_tube_at(*mouse)
                            if clicked >= 0:
                                if self.selected == -1:
                                    # Select if tube has liquid
                                    if self.tubes[clicked]:
                                        self.selected = clicked
                                elif self.selected == clicked:
                                    # Deselect
                                    self.selected = -1
                                else:
                                    # Try pour
                                    if self.can_pour(self.selected, clicked):
                                        self.start_pour_animation(self.selected, clicked)
                                        self.selected = -1
                                    else:
                                        # Select new tube if it has liquid
                                        if self.tubes[clicked]:
                                            self.selected = clicked
                                        else:
                                            self.selected = -1

                    elif self.state == "complete":
                        if next_btn and next_btn.collidepoint(mouse):
                            self.coins += self.calculate_stars() * 10
                            self.load_level(self.level + 1)
                        elif replay_btn and replay_btn.collidepoint(mouse):
                            self.load_level(self.level)

            # ─── UPDATE ───
            self.update_pour(dt)
            self.particles = [p for p in self.particles if p.update(dt)]

            if self.state == "playing":
                for btn in self.buttons.values():
                    btn.update(mouse, dt)

            # Spawn win particles continuously
            if self.state == "complete" and self.win_timer < 3:
                if random.random() < 0.3:
                    c = random.choice(list(LIQUID_COLORS.values()))
                    self.particles.append(Particle(
                        random.randint(100, SCREEN_WIDTH - 100),
                        random.randint(100, SCREEN_HEIGHT - 200),
                        c))

            # ─── DRAW ───
            if self.state == "menu":
                play_btn = self.draw_menu(dt)

            elif self.state in ("playing", "complete"):
                self.draw_bg()
                self.draw_top_bar()

                # Difficulty label
                colors, _ = get_difficulty(self.level)
                diff_map = {3: "Easy", 4: "Normal", 5: "Medium", 6: "Hard",
                            7: "Expert", 8: "Master", 9: "Insane", 10: "Legendary"}
                diff = diff_map.get(colors, "")
                diff_t = self.font_tiny.render(diff, True, (120, 125, 150))
                self.screen.blit(diff_t, (SCREEN_WIDTH // 2 - diff_t.get_width() // 2, 88))

                self.draw_tubes(dt)

                for btn in self.buttons.values():
                    btn.draw(self.screen)

                # Controls hint
                hint = self.font_tiny.render("U = Undo  |  R = Restart  |  ESC = Menu",
                                             True, (45, 48, 65))
                self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 22))

                # Particles
                for p in self.particles:
                    p.draw(self.screen)

                if self.state == "complete":
                    next_btn, replay_btn = self.draw_complete_screen(dt)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ─────────────────────────── ENTRY POINT ───────────────────────────

if __name__ == "__main__":
    game = WaterSortGame()
    game.run()
