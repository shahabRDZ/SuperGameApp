"""
Water Sort Puzzle — Premium Edition
Super Game App
"""

import pygame
import sys
import random
import copy
import math
import os

# ══════════════════════════════ INIT ══════════════════════════════

pygame.init()
pygame.mixer.init()

SW, SH = 480, 854  # Mobile aspect ratio (9:16)
FPS = 60
LAYERS = 4

screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Water Sort Puzzle")
clock = pygame.time.Clock()

# ══════════════════════════════ COLORS ══════════════════════════════

COLORS = {
    1:  (239, 83, 80),     # Red
    2:  (66, 165, 245),    # Blue
    3:  (102, 187, 106),   # Green
    4:  (255, 213, 79),    # Yellow
    5:  (255, 138, 101),   # Orange
    6:  (171, 71, 188),    # Purple
    7:  (38, 198, 218),    # Cyan
    8:  (240, 98, 146),    # Pink
    9:  (141, 110, 99),    # Brown
    10: (120, 144, 156),   # Blue Grey
    11: (174, 213, 129),   # Light Green
    12: (255, 183, 77),    # Amber
}

def lighter(c, amt=40):
    return tuple(min(255, x + amt) for x in c)

def darker(c, amt=40):
    return tuple(max(0, x - amt) for x in c)

def alpha_surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)

# ══════════════════════════════ FONTS ══════════════════════════════

def get_font(size, bold=False):
    names = ["SF Pro Display", "Helvetica Neue", "Helvetica", "Arial", "Segoe UI"]
    for name in names:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            return f
        except:
            continue
    return pygame.font.SysFont(None, size, bold=bold)

FONT_HERO = get_font(48, True)
FONT_TITLE = get_font(34, True)
FONT_BIG = get_font(26, True)
FONT_MED = get_font(20, True)
FONT_SM = get_font(16)
FONT_XS = get_font(13)
FONT_XXS = get_font(11)

# ══════════════════════════════ ASSETS (generated) ══════════════════════════════

class Assets:
    """Pre-rendered surfaces for performance."""

    def __init__(self):
        self.bg = self._make_bg()
        self.tube_glass = {}  # cached per state
        self.coin_icon = self._make_coin()
        self.star_on = self._make_star((255, 215, 0), (255, 240, 100))
        self.star_off = self._make_star((60, 63, 80), (80, 83, 100))

    def _make_bg(self):
        s = pygame.Surface((SW, SH))
        # Gradient
        c1 = (15, 18, 40)
        c2 = (8, 10, 28)
        for y in range(SH):
            t = y / SH
            r = int(c1[0] * (1-t) + c2[0] * t)
            g = int(c1[1] * (1-t) + c2[1] * t)
            b = int(c1[2] * (1-t) + c2[2] * t)
            pygame.draw.line(s, (r, g, b), (0, y), (SW, y))

        # Subtle radial vignette from center
        vig = alpha_surf(SW, SH)
        for radius in range(max(SW, SH), 0, -4):
            alpha = max(0, min(30, int((1 - radius / max(SW, SH)) * 50)))
            pygame.draw.circle(vig, (20, 25, 60, alpha), (SW//2, SH//3), radius)
        s.blit(vig, (0, 0))
        return s

    def _make_coin(self):
        s = alpha_surf(28, 28)
        pygame.draw.circle(s, (255, 193, 7), (14, 14), 13)
        pygame.draw.circle(s, (255, 215, 0), (14, 13), 11)
        pygame.draw.circle(s, (255, 235, 59), (12, 11), 6)
        # $ sign
        txt = get_font(12, True).render("$", True, (200, 150, 0))
        s.blit(txt, (14 - txt.get_width()//2, 14 - txt.get_height()//2))
        pygame.draw.circle(s, (200, 160, 0), (14, 14), 13, 2)
        return s

    def _make_star(self, outer_c, inner_c):
        size = 36
        s = alpha_surf(size, size)
        cx, cy = size // 2, size // 2
        r_out, r_in = 16, 7
        pts = []
        for i in range(10):
            a = math.radians(i * 36 - 90)
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pygame.draw.polygon(s, outer_c, pts)
        # Inner glow
        pts2 = []
        for i in range(10):
            a = math.radians(i * 36 - 90)
            r = (r_out - 3) if i % 2 == 0 else (r_in - 1)
            pts2.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pygame.draw.polygon(s, inner_c, pts2)
        return s

assets = Assets()

# ══════════════════════════════ TUBE RENDERER ══════════════════════════════

TW = 52        # tube width
TH = 170       # tube height
TInn = 5       # inner margin
LH = 34        # layer height
TBR = 20       # bottom radius


def render_tube(tube_data, selected=False, complete=False, pour_progress=None):
    """Render a complete tube with liquid to a surface."""
    pad = 14
    w = TW + pad * 2
    h = TH + pad * 2 + 20
    s = alpha_surf(w, h)

    ox, oy = pad, pad + 15  # tube origin within surface

    # ── Selection glow ──
    if selected:
        glow = alpha_surf(w, h)
        for r in range(24, 0, -2):
            a = max(0, min(60, int(60 * (1 - r / 24))))
            rect = pygame.Rect(ox - r, oy - r, TW + r*2, TH + r*2)
            pygame.draw.rect(glow, (255, 200, 60, a), rect, border_radius=TBR + r)
        s.blit(glow, (0, 0))

    # ── Complete glow ──
    if complete:
        glow = alpha_surf(w, h)
        for r in range(18, 0, -2):
            a = max(0, min(40, int(40 * (1 - r / 18))))
            rect = pygame.Rect(ox - r, oy - r, TW + r*2, TH + r*2)
            pygame.draw.rect(glow, (76, 175, 80, a), rect, border_radius=TBR + r)
        s.blit(glow, (0, 0))

    # ── Glass tube shape ──
    # We draw a U-shape: two vertical walls + rounded bottom
    glass = alpha_surf(TW, TH)

    # Fill inside with dark
    pygame.draw.rect(glass, (22, 25, 42, 180), (0, 0, TW, TH), border_radius=TBR)
    # Flatten top
    pygame.draw.rect(glass, (22, 25, 42, 180), (0, 0, TW, 15))

    s.blit(glass, (ox, oy))

    # ── Liquid layers ──
    for i, cid in enumerate(tube_data):
        if cid <= 0:
            continue
        color = COLORS.get(cid, (128, 128, 128))
        lx = ox + TInn
        ly = oy + TH - (i + 1) * LH
        lw = TW - TInn * 2
        lh = LH - 1

        # Bottom layer rounded
        br = (TBR - 6) if i == 0 else 4

        layer = alpha_surf(lw, lh)

        # Gradient fill: lighter at top, base in middle, darker at bottom
        lt = lighter(color, 35)
        dk = darker(color, 25)
        for row in range(lh):
            t = row / max(1, lh - 1)
            if t < 0.3:
                # Top: light to base
                tt = t / 0.3
                r = int(lt[0] * (1-tt) + color[0] * tt)
                g = int(lt[1] * (1-tt) + color[1] * tt)
                b = int(lt[2] * (1-tt) + color[2] * tt)
            else:
                # Base to dark
                tt = (t - 0.3) / 0.7
                r = int(color[0] * (1-tt) + dk[0] * tt)
                g = int(color[1] * (1-tt) + dk[1] * tt)
                b = int(color[2] * (1-tt) + dk[2] * tt)
            pygame.draw.line(layer, (r, g, b, 230), (0, row), (lw, row))

        # Clip to rounded rect
        mask = alpha_surf(lw, lh)
        pygame.draw.rect(mask, (255, 255, 255), (0, 0, lw, lh), border_radius=br)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        s.blit(layer, (lx, ly))

        # Shine strip (left side)
        shine = alpha_surf(6, lh - 4)
        for row in range(shine.get_height()):
            t = row / max(1, shine.get_height())
            a = int(55 * math.sin(t * math.pi))
            pygame.draw.line(shine, (255, 255, 255, a), (0, row), (5, row))
        s.blit(shine, (lx + 3, ly + 2))

        # Bubble dots for filled tubes
        if lh > 10:
            rng = random.Random(cid * 100 + i * 10)
            for _ in range(2):
                bx = rng.randint(4, lw - 4)
                by = rng.randint(4, lh - 4)
                ba = rng.randint(15, 40)
                bs = rng.randint(2, 4)
                pygame.draw.circle(s, (255, 255, 255, ba), (lx + bx, ly + by), bs)

        # Top meniscus for topmost layer
        if i == len(tube_data) - 1:
            men = alpha_surf(lw, 5)
            pygame.draw.ellipse(men, (*lighter(color, 50), 70), (0, 0, lw, 5))
            s.blit(men, (lx, ly - 1))

    # ── Glass walls (on top of liquid) ──
    wall_color = (90, 95, 120) if not selected else (220, 190, 60)
    if complete:
        wall_color = (100, 190, 110)
    wall_alpha = 200

    wall = alpha_surf(TW, TH)

    # Left wall
    pygame.draw.line(wall, (*wall_color, wall_alpha), (1, 0), (1, TH - TBR), 2)
    # Right wall
    pygame.draw.line(wall, (*wall_color, wall_alpha), (TW - 2, 0), (TW - 2, TH - TBR), 2)
    # Bottom arc
    arc_rect = pygame.Rect(0, TH - TBR * 2, TW, TBR * 2)
    pygame.draw.arc(wall, (*wall_color, wall_alpha), arc_rect, math.pi, 2 * math.pi, 2)

    # Glass shine on left
    for row in range(10, TH - 30):
        t = (row - 10) / (TH - 40)
        a = int(22 * math.sin(t * math.pi) * (1 - t * 0.5))
        if a > 0:
            pygame.draw.line(wall, (255, 255, 255, a), (4, row), (8, row))

    # Glass shine on right (subtle)
    for row in range(20, TH - 40):
        t = (row - 20) / (TH - 60)
        a = int(12 * math.sin(t * math.pi))
        if a > 0:
            pygame.draw.line(wall, (255, 255, 255, a), (TW - 8, row), (TW - 5, row))

    s.blit(wall, (ox, oy))

    # ── Completion badge ──
    if complete:
        badge_x = ox + TW // 2
        badge_y = oy - 4
        # Circle
        pygame.draw.circle(s, (76, 175, 80), (badge_x, badge_y), 11)
        pygame.draw.circle(s, (130, 220, 130), (badge_x, badge_y), 9)
        # Checkmark
        pts = [(badge_x - 5, badge_y), (badge_x - 1, badge_y + 4), (badge_x + 6, badge_y - 4)]
        pygame.draw.lines(s, (255, 255, 255), False, pts, 3)

    return s


# ══════════════════════════════ LEVEL GENERATION ══════════════════════════════

def get_difficulty(level):
    if level <= 3:    return 3, 2
    if level <= 8:    return 4, 2
    if level <= 15:   return 5, 2
    if level <= 25:   return 6, 2
    if level <= 40:   return 7, 2
    if level <= 60:   return 8, 2
    if level <= 80:   return 9, 2
    return 10, 2


def generate_level(level_num):
    rng = random.Random(level_num * 31337 + 97)
    colors, empties = get_difficulty(level_num)

    pool = []
    for c in range(1, colors + 1):
        pool.extend([c] * LAYERS)

    for _ in range(200):
        rng.shuffle(pool)
        tubes = [pool[i*LAYERS:(i+1)*LAYERS] for i in range(colors)]
        if not any(len(set(t)) == 1 for t in tubes):
            break

    for _ in range(empties):
        tubes.append([])

    return [list(t) for t in tubes]


# ══════════════════════════════ PARTICLES ══════════════════════════════

class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'decay', 'size', 'color', 'grav', 'shape']

    def __init__(self, x, y, color, vx=None, vy=None, size=None, gravity=True, shape='circle'):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-7, -2)
        self.life = 1.0
        self.decay = random.uniform(0.6, 1.2)
        self.size = size or random.uniform(3, 7)
        self.grav = gravity
        self.shape = shape

    def update(self, dt):
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        if self.grav:
            self.vy += 10 * dt
        self.life -= dt / self.decay
        return self.life > 0

    def draw(self, surf):
        a = max(0, min(255, int(self.life * 255)))
        s = max(1, int(self.size * max(0.3, self.life)))
        if s < 1 or a < 5:
            return
        if self.shape == 'circle':
            temp = alpha_surf(s*2+4, s*2+4)
            pygame.draw.circle(temp, (*self.color, a), (s+2, s+2), s)
            if s > 2:
                pygame.draw.circle(temp, (*self.color, a//4), (s+2, s+2), s+2)
            surf.blit(temp, (int(self.x)-s-2, int(self.y)-s-2))
        elif self.shape == 'star':
            temp = alpha_surf(s*4, s*4)
            cx, cy = s*2, s*2
            pts = []
            rot = self.life * 200
            for i in range(10):
                ang = math.radians(i * 36 - 90 + rot)
                r = s if i % 2 == 0 else s * 0.4
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            pygame.draw.polygon(temp, (*self.color, a), pts)
            surf.blit(temp, (int(self.x)-s*2, int(self.y)-s*2))
        elif self.shape == 'confetti':
            temp = alpha_surf(s*3, s*3)
            angle = self.life * 300
            w = max(1, int(s * abs(math.sin(math.radians(angle)))))
            h = max(1, int(s * 0.6))
            rect = pygame.Rect(s*3//2 - w//2, s*3//2 - h//2, w, h)
            pygame.draw.rect(temp, (*self.color, a), rect, border_radius=2)
            surf.blit(temp, (int(self.x)-s*3//2, int(self.y)-s*3//2))


# ══════════════════════════════ UI COMPONENTS ══════════════════════════════

class PillButton:
    def __init__(self, x, y, w, h, text, color=(50, 55, 80), text_color=(220, 225, 240)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False
        self.press = False
        self.scale = 1.0

    def update(self, mouse, dt):
        self.hover = self.rect.collidepoint(mouse)
        target = 1.06 if self.hover else 1.0
        self.scale += (target - self.scale) * min(1, dt * 14)

    def draw(self, surf):
        w = int(self.rect.w * self.scale)
        h = int(self.rect.h * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        r = h // 2

        # Shadow
        sh = alpha_surf(w + 6, h + 6)
        pygame.draw.rect(sh, (0, 0, 0, 50), (3, 4, w, h), border_radius=r)
        surf.blit(sh, (x - 3, y - 2))

        # Body
        c = lighter(self.color, 18) if self.hover else self.color
        body = alpha_surf(w, h)
        pygame.draw.rect(body, (*c, 230), (0, 0, w, h), border_radius=r)

        # Top highlight
        hl = alpha_surf(w - 8, h // 3)
        pygame.draw.rect(hl, (255, 255, 255, 18), (0, 0, w - 8, h // 3), border_radius=r)
        body.blit(hl, (4, 2))

        surf.blit(body, (x, y))

        # Border
        pygame.draw.rect(surf, (*lighter(c, 30), 120), (x, y, w, h), 1, border_radius=r)

        # Text
        txt = FONT_SM.render(self.text, True, self.text_color)
        surf.blit(txt, (x + w//2 - txt.get_width()//2, y + h//2 - txt.get_height()//2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class BigButton:
    def __init__(self, x, y, w, h, text, color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False
        self.scale = 1.0

    def update(self, mouse, dt):
        self.hover = self.rect.collidepoint(mouse)
        target = 1.05 if self.hover else 1.0
        self.scale += (target - self.scale) * min(1, dt * 14)

    def draw(self, surf):
        w = int(self.rect.w * self.scale)
        h = int(self.rect.h * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        r = 16

        # Shadow
        sh = alpha_surf(w + 8, h + 8)
        pygame.draw.rect(sh, (0, 0, 0, 70), (4, 5, w, h), border_radius=r)
        surf.blit(sh, (x - 4, y - 3))

        c = lighter(self.color, 15) if self.hover else self.color
        # Body gradient
        body = alpha_surf(w, h)
        lt = lighter(c, 20)
        dk = darker(c, 15)
        for row in range(h):
            t = row / max(1, h - 1)
            rr = int(lt[0] * (1-t) + dk[0] * t)
            gg = int(lt[1] * (1-t) + dk[1] * t)
            bb = int(lt[2] * (1-t) + dk[2] * t)
            pygame.draw.line(body, (rr, gg, bb), (0, row), (w, row))
        mask = alpha_surf(w, h)
        pygame.draw.rect(mask, (255, 255, 255), (0, 0, w, h), border_radius=r)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(body, (x, y))

        # Top shine
        shine = alpha_surf(w - 12, h // 3)
        pygame.draw.rect(shine, (255, 255, 255, 30), (0, 0, w - 12, h // 3), border_radius=r)
        surf.blit(shine, (x + 6, y + 3))

        pygame.draw.rect(surf, (*lighter(c, 40), 100), (x, y, w, h), 1, border_radius=r)

        txt = FONT_BIG.render(self.text, True, self.text_color)
        surf.blit(txt, (x + w//2 - txt.get_width()//2, y + h//2 - txt.get_height()//2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


# ══════════════════════════════ POUR ANIMATION ══════════════════════════════

class PourAnim:
    def __init__(self):
        self.active = False
        self.phase = 0
        self.t = 0.0
        self.src = -1
        self.dst = -1
        self.offset = [0.0, 0.0]
        self.done_pour = False
        self.stream_particles = []

    def start(self, src, dst):
        self.active = True
        self.phase = 0
        self.t = 0.0
        self.src = src
        self.dst = dst
        self.offset = [0.0, 0.0]
        self.done_pour = False
        self.stream_particles = []

    def ease(self, t):
        t = max(0, min(1, t))
        return t * t * (3 - 2 * t)

    def update(self, dt, positions, tubes, do_pour_fn):
        if not self.active:
            return False

        speed = 4.0
        self.t += dt * speed
        t = self.ease(min(1, self.t))

        sx, sy = positions[self.src]
        dx, dy = positions[self.dst]

        if self.phase == 0:  # Lift
            self.offset = [0, -60 * t]
            if self.t >= 1:
                self.phase = 1
                self.t = 0

        elif self.phase == 1:  # Slide over
            target_x = (dx - sx) + (28 if dx > sx else -28)
            self.offset = [target_x * t, -60]
            if self.t >= 1:
                self.phase = 2
                self.t = 0

        elif self.phase == 2:  # Tilt + pour
            target_x = (dx - sx) + (28 if dx > sx else -28)
            self.offset = [target_x, -60]
            if not self.done_pour and self.t >= 0.3:
                do_pour_fn()
                self.done_pour = True
                # Stream particles
                px = dx + TW // 2
                py = dy
                if tubes[self.dst]:
                    c = COLORS.get(tubes[self.dst][-1], (200, 200, 200))
                    for _ in range(12):
                        self.stream_particles.append(
                            Particle(px + random.randint(-8, 8), py + random.randint(-5, 15),
                                     c, random.uniform(-1.5, 1.5), random.uniform(-4, -1),
                                     random.uniform(2, 5)))
            if self.t >= 0.8:
                self.phase = 3
                self.t = 0

        elif self.phase == 3:  # Return
            target_x = (dx - sx) + (28 if dx > sx else -28)
            self.offset = [target_x * (1 - t), -60 * (1 - t)]
            if self.t >= 1:
                self.active = False
                self.offset = [0, 0]
                return True  # completed

        # Update stream particles
        self.stream_particles = [p for p in self.stream_particles if p.update(dt)]
        return False

    def draw_particles(self, surf):
        for p in self.stream_particles:
            p.draw(surf)


# ══════════════════════════════ GAME ══════════════════════════════

class Game:
    def __init__(self):
        self.state = "menu"
        self.level = 1
        self.coins = 100
        self.moves = 0
        self.selected = -1
        self.tubes = []
        self.undo_stack = []
        self.positions = []
        self.particles = []
        self.pour = PourAnim()
        self.buttons = {}
        self.win_t = 0
        self.menu_t = 0
        self.tube_cache = {}  # rendered tube cache

    def load_level(self, n):
        self.level = n
        self.tubes = generate_level(n)
        self.moves = 0
        self.selected = -1
        self.undo_stack = []
        self.particles = []
        self.state = "playing"
        self.pour.active = False
        self.win_t = 0
        self.tube_cache = {}
        self._layout()
        self._make_buttons()

    def _layout(self):
        self.positions = []
        n = len(self.tubes)
        per_row = min(n, 5)
        rows = math.ceil(n / per_row)
        spacing = TW + 22

        for i in range(n):
            r = i // per_row
            c = i % per_row
            in_row = min(per_row, n - r * per_row)
            tw = in_row * spacing - 22
            sx = (SW - tw) // 2
            x = sx + c * spacing
            y = 150 + r * (TH + 55)
            self.positions.append((x, y))

    def _make_buttons(self):
        y = SH - 75
        bw, bh = 90, 38
        gap = 10
        total = bw * 4 + gap * 3
        sx = (SW - total) // 2
        self.buttons = {
            'undo': PillButton(sx, y, bw, bh, "Undo"),
            'restart': PillButton(sx + bw + gap, y, bw, bh, "Restart"),
            'hint': PillButton(sx + (bw+gap)*2, y, bw, bh, "Hint", (65, 50, 85)),
            'back': PillButton(sx + (bw+gap)*3, y, bw, bh, "Menu"),
        }

    def _tube_key(self, idx):
        t = self.tubes[idx]
        sel = (idx == self.selected and not self.pour.active)
        comp = len(t) == LAYERS and len(set(t)) == 1 if t else False
        return (tuple(t), sel, comp)

    def get_tube_surf(self, idx):
        key = self._tube_key(idx)
        if key not in self.tube_cache:
            t = self.tubes[idx]
            sel = (idx == self.selected and not self.pour.active)
            comp = len(t) == LAYERS and len(set(t)) == 1 if t else False
            self.tube_cache[key] = render_tube(t, sel, comp)
        return self.tube_cache[key]

    def get_tube_at(self, mx, my):
        for i, (tx, ty) in enumerate(self.positions):
            if pygame.Rect(tx - 10, ty - 20, TW + 20, TH + 40).collidepoint(mx, my):
                return i
        return -1

    def can_pour(self, s, d):
        src, dst = self.tubes[s], self.tubes[d]
        if not src: return False
        if len(dst) >= LAYERS: return False
        if not dst: return True
        return src[-1] == dst[-1]

    def do_pour(self, s, d):
        src, dst = self.tubes[s], self.tubes[d]
        self.undo_stack.append(copy.deepcopy(self.tubes))
        top = src[-1]
        while src and src[-1] == top and len(dst) < LAYERS:
            dst.append(src.pop())
        self.moves += 1
        self.tube_cache = {}

    def undo(self):
        if not self.undo_stack or self.pour.active:
            return
        self.tubes = self.undo_stack.pop()
        self.moves = max(0, self.moves - 1)
        self.selected = -1
        self.tube_cache = {}

    def check_win(self):
        return all(
            (not t) or (len(t) == LAYERS and len(set(t)) == 1)
            for t in self.tubes
        )

    def calc_stars(self):
        c, _ = get_difficulty(self.level)
        opt = c * 2
        if self.moves <= opt: return 3
        if self.moves <= opt * 2: return 2
        return 1

    def spawn_win(self):
        confetti_colors = [(255,107,107), (78,205,196), (255,230,109),
                           (162,155,254), (255,159,243), (69,183,209),
                           (255,177,66), (150,206,180)]
        for _ in range(100):
            c = random.choice(confetti_colors)
            shape = random.choice(['confetti', 'star', 'circle'])
            self.particles.append(Particle(
                random.randint(20, SW-20), random.randint(-50, SH//2),
                c, random.uniform(-3, 3), random.uniform(-5, 2),
                random.uniform(4, 10), shape=shape))

    # ─── DRAWING ───

    def draw_topbar(self):
        # Bar bg
        bar = alpha_surf(SW, 80)
        for y in range(80):
            a = int(220 * (1 - y / 120))
            pygame.draw.line(bar, (15, 18, 38, a), (0, y), (SW, y))
        screen.blit(bar, (0, 0))

        # Level
        colors, _ = get_difficulty(self.level)
        diffs = {3:"Easy",4:"Normal",5:"Medium",6:"Hard",7:"Expert",8:"Master",9:"Insane",10:"Legendary"}
        diff_colors = {3:(130,200,130),4:(130,180,220),5:(220,200,100),6:(230,150,80),
                       7:(220,100,100),8:(200,80,180),9:(180,60,60),10:(255,215,0)}

        lt = FONT_BIG.render(f"Level {self.level}", True, (230, 235, 250))
        screen.blit(lt, (20, 14))

        dc = diff_colors.get(colors, (150,150,150))
        dt_surf = FONT_XS.render(diffs.get(colors, ""), True, dc)
        screen.blit(dt_surf, (20, 46))

        # Moves
        mt = FONT_MED.render(f"Moves: {self.moves}", True, (160, 165, 185))
        screen.blit(mt, (SW//2 - mt.get_width()//2, 28))

        # Coins
        screen.blit(assets.coin_icon, (SW - 110, 22))
        ct = FONT_MED.render(str(self.coins), True, (255, 215, 0))
        screen.blit(ct, (SW - 78, 26))

    def draw_playing(self, dt):
        screen.blit(assets.bg, (0, 0))
        self.draw_topbar()

        # Tubes
        pad = 14
        for i in range(len(self.tubes)):
            tx, ty = self.positions[i]
            ox, oy = 0, 0

            if self.pour.active and self.pour.src == i:
                ox = self.pour.offset[0]
                oy = self.pour.offset[1]
            elif i == self.selected and not self.pour.active:
                oy = -18

            surf = self.get_tube_surf(i)
            screen.blit(surf, (tx - pad + ox, ty - pad - 15 + oy))

        # Pour stream particles
        if self.pour.active:
            self.pour.draw_particles(screen)

        # Particles
        for p in self.particles:
            p.draw(screen)

        # Buttons
        mouse = pygame.mouse.get_pos()
        for b in self.buttons.values():
            b.update(mouse, dt)
            b.draw(screen)

        # Hint
        h = FONT_XXS.render("U=Undo  R=Restart  ESC=Menu", True, (40, 44, 65))
        screen.blit(h, (SW//2 - h.get_width()//2, SH - 28))

    def draw_complete(self, dt):
        self.win_t += dt

        # Overlay
        ov = alpha_surf(SW, SH)
        a = min(180, int(self.win_t * 500))
        ov.fill((0, 0, 0, a))
        screen.blit(ov, (0, 0))

        if self.win_t < 0.25:
            return None, None

        # Panel
        pw, ph = 360, 380
        px = (SW - pw) // 2
        py = (SH - ph) // 2 - 20

        # Panel shadow
        sh = alpha_surf(pw + 10, ph + 10)
        pygame.draw.rect(sh, (0, 0, 0, 90), (5, 7, pw, ph), border_radius=24)
        screen.blit(sh, (px - 5, py - 3))

        # Panel body with gradient
        panel = alpha_surf(pw, ph)
        c1 = (35, 40, 65)
        c2 = (22, 25, 45)
        for row in range(ph):
            t = row / ph
            r = int(c1[0]*(1-t) + c2[0]*t)
            g = int(c1[1]*(1-t) + c2[1]*t)
            b = int(c1[2]*(1-t) + c2[2]*t)
            pygame.draw.line(panel, (r, g, b, 240), (0, row), (pw, row))
        mask = alpha_surf(pw, ph)
        pygame.draw.rect(mask, (255,255,255), (0,0,pw,ph), border_radius=24)
        panel.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(panel, (px, py))

        # Border
        pygame.draw.rect(screen, (60, 65, 90, 180), (px, py, pw, ph), 1, border_radius=24)

        # Inner glow at top
        glow = alpha_surf(pw - 20, 40)
        pygame.draw.rect(glow, (255, 255, 255, 8), (0, 0, pw - 20, 40), border_radius=20)
        screen.blit(glow, (px + 10, py + 5))

        # Title
        title = FONT_TITLE.render("Level Complete!", True, (110, 230, 140))
        screen.blit(title, (SW//2 - title.get_width()//2, py + 30))

        # Stars
        stars = self.calc_stars()
        star_w = 36
        total_sw = star_w * 3 + 16 * 2
        star_sx = SW // 2 - total_sw // 2
        for i in range(3):
            sx = star_sx + i * (star_w + 16)
            sy = py + 90
            # Animate stars appearing
            delay = i * 0.15
            if self.win_t - 0.25 > delay:
                img = assets.star_on if i < stars else assets.star_off
                # Scale bounce
                elapsed = self.win_t - 0.25 - delay
                sc = min(1, elapsed * 5)
                sc = 1 + 0.3 * max(0, 1 - elapsed * 3)  # Bounce
                sw = int(star_w * sc)
                sh_s = int(star_w * sc)
                scaled = pygame.transform.smoothscale(img, (sw, sh_s))
                screen.blit(scaled, (sx + star_w//2 - sw//2, sy + star_w//2 - sh_s//2))

        # Moves
        mt = FONT_MED.render(f"Moves: {self.moves}", True, (190, 195, 215))
        screen.blit(mt, (SW//2 - mt.get_width()//2, py + 150))

        # Reward
        reward = stars * 15
        screen.blit(assets.coin_icon, (SW//2 - 50, py + 185))
        rt = FONT_BIG.render(f"+ {reward}", True, (255, 215, 0))
        screen.blit(rt, (SW//2 - 18, py + 187))

        # Buttons
        mouse = pygame.mouse.get_pos()
        bw, bh = 145, 50
        gap = 14
        bx1 = SW//2 - bw - gap//2
        bx2 = SW//2 + gap//2
        by = py + 270

        next_btn = BigButton(bx1, by, bw, bh, "Next", (60, 175, 95))
        replay_btn = BigButton(bx2, by, bw, bh, "Replay", (50, 60, 90))

        next_btn.update(mouse, dt)
        replay_btn.update(mouse, dt)
        next_btn.draw(screen)
        replay_btn.draw(screen)

        # Double coins button
        dcb_rect = pygame.Rect(SW//2 - 80, by + 65, 160, 36)
        dcb_hover = dcb_rect.collidepoint(mouse)
        dcb_c = (85, 65, 110) if not dcb_hover else (105, 80, 130)
        draw_pill = alpha_surf(160, 36)
        pygame.draw.rect(draw_pill, (*dcb_c, 220), (0, 0, 160, 36), border_radius=18)
        screen.blit(draw_pill, dcb_rect.topleft)
        ad_t = FONT_XS.render("Watch Ad x2", True, (220, 200, 255))
        screen.blit(ad_t, (dcb_rect.centerx - ad_t.get_width()//2,
                           dcb_rect.centery - ad_t.get_height()//2))

        return next_btn.rect, replay_btn.rect

    def draw_menu(self, dt):
        self.menu_t += dt
        screen.blit(assets.bg, (0, 0))

        # Floating bg particles
        if random.random() < 0.08:
            c = random.choice(list(COLORS.values()))
            self.particles.append(Particle(
                random.randint(0, SW), SH + 5, c,
                random.uniform(-0.3, 0.3), random.uniform(-1, -0.4),
                random.uniform(2, 4), gravity=False))

        for p in self.particles:
            p.draw(screen)

        # App badge
        badge = FONT_XS.render("SUPER GAME APP", True, (80, 85, 110))
        screen.blit(badge, (SW//2 - badge.get_width()//2, 120))

        # Title
        t1 = FONT_HERO.render("Water Sort", True, (230, 235, 255))
        screen.blit(t1, (SW//2 - t1.get_width()//2, 145))
        t2 = FONT_TITLE.render("Puzzle", True, (90, 170, 230))
        screen.blit(t2, (SW//2 - t2.get_width()//2, 200))

        # Preview tubes
        preview_tubes = [[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4],[5,5,5,5]]
        ptw = len(preview_tubes) * (TW + 14) - 14
        psx = (SW - ptw) // 2
        for i, pt in enumerate(preview_tubes):
            tx = psx + i * (TW + 14)
            ty = 280 + int(math.sin(self.menu_t * 1.8 + i * 0.9) * 10)
            surf = render_tube(pt, False, True)
            screen.blit(surf, (tx - 14, ty - 29))

        # Play button
        play = BigButton(SW//2 - 110, 520, 220, 60, "P L A Y", (55, 185, 105))
        mouse = pygame.mouse.get_pos()
        play.update(mouse, dt)
        play.draw(screen)

        # Level info
        li = FONT_SM.render(f"Level {self.level}", True, (120, 125, 155))
        screen.blit(li, (SW//2 - li.get_width()//2, 600))

        # Coins
        screen.blit(assets.coin_icon, (SW//2 - 45, 635))
        ci = FONT_MED.render(str(self.coins), True, (255, 215, 0))
        screen.blit(ci, (SW//2 - 13, 638))

        # Footer
        ft = FONT_XXS.render("Tap PLAY to start", True, (50, 54, 75))
        screen.blit(ft, (SW//2 - ft.get_width()//2, SH - 35))

        return play.rect

    # ─── MAIN LOOP ───

    def run(self):
        running = True
        play_btn = None
        next_btn = None
        replay_btn = None

        while running:
            dt = self.clock.tick(FPS) / 1000.0 if hasattr(self, 'clock') else clock.tick(FPS) / 1000.0
            mouse = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if self.state == "playing":
                            self.state = "menu"
                        else:
                            running = False
                    if ev.key == pygame.K_u and self.state == "playing":
                        self.undo()
                    if ev.key == pygame.K_r and self.state == "playing":
                        self.load_level(self.level)

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.state == "menu":
                        if play_btn and play_btn.collidepoint(mouse):
                            self.load_level(self.level)

                    elif self.state == "playing" and not self.pour.active:
                        handled = False
                        for name, btn in self.buttons.items():
                            if btn.clicked(mouse):
                                if name == 'undo': self.undo()
                                elif name == 'restart': self.load_level(self.level)
                                elif name == 'back': self.state = "menu"
                                handled = True
                                break

                        if not handled:
                            ci = self.get_tube_at(*mouse)
                            if ci >= 0:
                                if self.selected == -1:
                                    if self.tubes[ci]:
                                        self.selected = ci
                                        self.tube_cache = {}
                                elif self.selected == ci:
                                    self.selected = -1
                                    self.tube_cache = {}
                                else:
                                    if self.can_pour(self.selected, ci):
                                        src = self.selected
                                        self.selected = -1
                                        self.tube_cache = {}
                                        self.pour.start(src, ci)
                                    elif self.tubes[ci]:
                                        self.selected = ci
                                        self.tube_cache = {}
                                    else:
                                        self.selected = -1
                                        self.tube_cache = {}

                    elif self.state == "complete":
                        if next_btn and next_btn.collidepoint(mouse):
                            self.coins += self.calc_stars() * 15
                            self.load_level(self.level + 1)
                        elif replay_btn and replay_btn.collidepoint(mouse):
                            self.load_level(self.level)

            # ─── UPDATE ───
            if self.pour.active:
                done = self.pour.update(dt, self.positions, self.tubes,
                                        lambda: self.do_pour(self.pour.src, self.pour.dst))
                if done:
                    self.tube_cache = {}
                    if self.check_win():
                        self.state = "complete"
                        self.win_t = 0
                        self.spawn_win()

            self.particles = [p for p in self.particles if p.update(dt)]

            if self.state == "complete" and self.win_t < 4:
                if random.random() < 0.15:
                    cols = [(255,107,107),(78,205,196),(255,230,109),(162,155,254),(255,159,243)]
                    c = random.choice(cols)
                    self.particles.append(Particle(
                        random.randint(30, SW-30), random.randint(-20, SH//3),
                        c, random.uniform(-2, 2), random.uniform(-3, 1),
                        random.uniform(4, 9), shape=random.choice(['confetti','star'])))

            # ─── DRAW ───
            if self.state == "menu":
                play_btn = self.draw_menu(dt)

            elif self.state == "playing":
                self.draw_playing(dt)

            elif self.state == "complete":
                self.draw_playing(dt)
                next_btn, replay_btn = self.draw_complete(dt)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ══════════════════════════════ RUN ══════════════════════════════

if __name__ == "__main__":
    game = Game()
    game.run()
