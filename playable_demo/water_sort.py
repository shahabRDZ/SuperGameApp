"""
Water Sort Puzzle — Production Quality
All weaknesses fixed: realistic tubes, liquid, pour animation, sounds, hints
"""

import pygame
import pygame.gfxdraw
import sys
import random
import copy
import math
import struct
import array
import io
import colorsys

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)

# ════════════════════════════════════════════════════════════════
#  SCREEN
# ════════════════════════════════════════════════════════════════
SW, SH = 440, 800
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Water Sort Puzzle")
clock = pygame.time.Clock()
FPS = 60
LAYERS = 4

def S(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)

# ════════════════════════════════════════════════════════════════
#  SOUND GENERATOR
# ════════════════════════════════════════════════════════════════

def gen_sound(freq, dur, vol=0.3, wave='sine', fade_out=True):
    sr = 44100
    n = int(sr * dur)
    buf = array.array('h')
    for i in range(n):
        t = i / sr
        if wave == 'sine':
            v = math.sin(2 * math.pi * freq * t)
        elif wave == 'tri':
            v = 2 * abs(2 * (freq * t - math.floor(freq * t + 0.5))) - 1
        else:
            v = v if 'v' in dir() else 0
        # Fade
        env = 1.0
        if fade_out:
            env = max(0, 1 - i / n)
        if i < 200:
            env *= i / 200
        buf.append(int(v * vol * 32767 * env))
    snd = pygame.mixer.Sound(buffer=buf)
    return snd

def gen_pour_sound():
    sr = 44100
    dur = 0.4
    n = int(sr * dur)
    buf = array.array('h')
    rng = random.Random(42)
    for i in range(n):
        t = i / sr
        env = max(0, 1 - i/n) * min(1, i / 800)
        # Bubbling noise + low freq
        v = math.sin(2 * math.pi * 180 * t + 3 * math.sin(2 * math.pi * 40 * t))
        v += rng.uniform(-0.3, 0.3)  # noise
        v *= 0.25
        buf.append(int(v * env * 32767))
    return pygame.mixer.Sound(buffer=buf)

def gen_complete_sound():
    sr = 44100
    notes = [523, 659, 784]  # C5, E5, G5
    dur_each = 0.12
    buf = array.array('h')
    for note in notes:
        n = int(sr * dur_each)
        for i in range(n):
            t = i / sr
            env = max(0, 1 - i/n * 0.7) * min(1, i / 100)
            v = math.sin(2 * math.pi * note * t) * 0.3
            v += math.sin(2 * math.pi * note * 2 * t) * 0.1
            buf.append(int(v * env * 32767))
    return pygame.mixer.Sound(buffer=buf)

def gen_win_sound():
    sr = 44100
    notes = [523, 587, 659, 784, 1047]
    dur_each = 0.1
    buf = array.array('h')
    for note in notes:
        n = int(sr * dur_each)
        for i in range(n):
            t = i / sr
            env = max(0, 1 - i/n * 0.5) * min(1, i / 80)
            v = math.sin(2 * math.pi * note * t) * 0.3
            v += math.sin(2 * math.pi * note * 1.5 * t) * 0.1
            buf.append(int(v * env * 32767))
    return pygame.mixer.Sound(buffer=buf)

SND_TAP = gen_sound(800, 0.05, 0.15)
SND_POUR = gen_pour_sound()
SND_DROP = gen_sound(400, 0.1, 0.2, 'sine')
SND_COMPLETE = gen_complete_sound()
SND_WIN = gen_win_sound()
SND_UNDO = gen_sound(300, 0.08, 0.12)

# ════════════════════════════════════════════════════════════════
#  COLORS - Bright, vibrant, pastel-ish
# ════════════════════════════════════════════════════════════════

WATER = {
    1:  (235, 87, 87),     # Red
    2:  (86, 156, 230),    # Blue
    3:  (111, 207, 115),   # Green
    4:  (250, 215, 75),    # Yellow
    5:  (245, 145, 65),    # Orange
    6:  (175, 115, 220),   # Purple
    7:  (72, 210, 200),    # Teal
    8:  (240, 120, 170),   # Pink
    9:  (180, 140, 110),   # Brown
    10: (130, 190, 240),   # Sky Blue
    11: (195, 225, 95),    # Lime
    12: (220, 175, 95),    # Gold
}

def brighter(c, n=40): return tuple(min(255, x+n) for x in c)
def dimmer(c, n=35): return tuple(max(0, x-n) for x in c)
def lerpc(a, b, t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

# Background colors (calming, light)
BG_TOP = (220, 230, 245)      # Light lavender
BG_BOT = (190, 205, 230)      # Soft blue
BG_DARK_TOP = (25, 28, 48)    # Dark mode
BG_DARK_BOT = (15, 18, 35)

# ════════════════════════════════════════════════════════════════
#  FONTS
# ════════════════════════════════════════════════════════════════

def MF(sz, bold=False):
    for n in ["Avenir Next","Avenir","SF Pro Rounded","SF Pro Display","Helvetica Neue","Helvetica","Arial"]:
        try: return pygame.font.SysFont(n, sz, bold)
        except: pass
    return pygame.font.SysFont(None, sz, bold)

f48=MF(46,True); f32=MF(30,True); f24=MF(22,True); f20=MF(18,True)
f16=MF(15); f14=MF(13); f12=MF(12); f11=MF(11); f10=MF(10)

# ════════════════════════════════════════════════════════════════
#  BACKGROUND
# ════════════════════════════════════════════════════════════════

def make_bg(dark=False):
    s = pygame.Surface((SW, SH))
    t1 = BG_DARK_TOP if dark else BG_TOP
    t2 = BG_DARK_BOT if dark else BG_BOT
    for y in range(SH):
        t = y / SH
        r = int(t1[0]*(1-t)+t2[0]*t)
        g = int(t1[1]*(1-t)+t2[1]*t)
        b = int(t1[2]*(1-t)+t2[2]*t)
        pygame.draw.line(s, (r,g,b), (0,y), (SW,y))
    return s

BG_LIGHT = make_bg(False)
BG_DARK = make_bg(True)

# ════════════════════════════════════════════════════════════════
#  TUBE GEOMETRY
# ════════════════════════════════════════════════════════════════

TW = 50
TH = 160
WALL = 3
IW = TW - WALL * 2
BOT_CURVE = 22  # bottom semicircle height
INNER_H = TH - WALL - BOT_CURVE // 2
LH = INNER_H // LAYERS

# ════════════════════════════════════════════════════════════════
#  TUBE RENDERER — 3D Cylindrical Glass
# ════════════════════════════════════════════════════════════════

def render_tube_glass(selected=False, complete=False):
    """Pre-render glass tube with 3D cylindrical shading."""
    pad = 18
    w = TW + pad * 2
    h = TH + pad * 2 + 20
    surf = S(w, h)

    ox, oy = pad, pad + 12

    # ── Glow ──
    if selected:
        for r in range(22, 0, -2):
            a = int(40 * (1 - r/22))
            pygame.draw.rect(surf, (255, 200, 50, a),
                           (ox-r, oy-r, TW+r*2, TH+r*2), border_radius=BOT_CURVE+r)
    elif complete:
        for r in range(16, 0, -2):
            a = int(30 * (1 - r/16))
            pygame.draw.rect(surf, (80, 210, 120, a),
                           (ox-r, oy-r, TW+r*2, TH+r*2), border_radius=BOT_CURVE+r)

    # ── Inner dark area (inside of tube) ──
    inner = S(TW, TH)
    inner_color = (235, 240, 248) if not False else (18, 20, 35)
    # Rect part
    pygame.draw.rect(inner, (*inner_color, 120), (WALL, 0, IW, TH - BOT_CURVE))
    # Bottom curve
    pygame.draw.ellipse(inner, (*inner_color, 120),
                       (WALL, TH - BOT_CURVE * 2, IW, BOT_CURVE * 2))
    surf.blit(inner, (ox, oy))

    # ── Cylindrical 3D shading on glass walls ──
    glass = S(TW, TH)

    # Create cylindrical gradient across tube width
    for col in range(TW):
        # Distance from center normalized to [-1, 1]
        t = (col - TW/2) / (TW/2)
        # Cylindrical shading: bright in center-left, dark at edges
        brightness = math.exp(-(t + 0.3)**2 / 0.15) * 0.7 + 0.15

        # Only draw on walls (left and right edges)
        if col < WALL + 2 or col > TW - WALL - 3:
            alpha = int(180 * (1 - abs(t) * 0.3))
            gc = (160, 175, 200) if not selected else (240, 210, 100)
            if complete: gc = (130, 210, 150)
            r = int(gc[0] * brightness)
            g = int(gc[1] * brightness)
            b = int(gc[2] * brightness)
            for row in range(TH - BOT_CURVE):
                pygame.draw.line(glass, (r, g, b, alpha), (col, row), (col, row))

    # ── Glass reflections ──
    # Main left reflection (bright, narrow)
    for row in range(5, TH - BOT_CURVE - 5):
        t = (row - 5) / max(1, TH - BOT_CURVE - 10)
        intensity = math.exp(-((t - 0.2)**2) / 0.02) * 60 + \
                    math.exp(-((t - 0.6)**2) / 0.08) * 25
        if intensity > 3:
            pygame.draw.line(glass, (255, 255, 255, int(intensity)),
                           (WALL + 1, row), (WALL + 5, row))

    # Secondary right reflection (dimmer)
    for row in range(12, TH - BOT_CURVE - 12):
        t = (row - 12) / max(1, TH - BOT_CURVE - 24)
        intensity = math.exp(-((t - 0.35)**2) / 0.04) * 25
        if intensity > 3:
            pygame.draw.line(glass, (255, 255, 255, int(intensity)),
                           (TW - WALL - 4, row), (TW - WALL - 1, row))

    surf.blit(glass, (ox, oy))

    # ── Bottom arc ──
    arc_color = (140, 155, 180) if not selected else (220, 195, 80)
    if complete: arc_color = (110, 195, 135)

    # Draw bottom curve with slight 3D
    for i in range(3):
        a = max(20, 120 - i * 40)
        arc_rect = (ox + WALL - i, oy + TH - BOT_CURVE * 2 + i,
                    IW + i * 2, BOT_CURVE * 2)
        pygame.draw.arc(surf, (*arc_color, a), arc_rect, math.pi, 2 * math.pi, 1)

    # ── Side walls ──
    wall_c = (130, 145, 175) if not selected else (220, 195, 80)
    if complete: wall_c = (110, 195, 135)

    # Left wall (slightly brighter = light source from left)
    pygame.draw.line(surf, (*brighter(wall_c, 20), 160), (ox, oy), (ox, oy + TH - BOT_CURVE), 2)
    # Right wall
    pygame.draw.line(surf, (*wall_c, 140), (ox + TW - 1, oy), (ox + TW - 1, oy + TH - BOT_CURVE), 2)

    # ── Top rim (open top, subtle) ──
    rim_c = brighter(wall_c, 30)
    pygame.draw.line(surf, (*rim_c, 100), (ox, oy), (ox + WALL + 1, oy))
    pygame.draw.line(surf, (*rim_c, 100), (ox + TW - WALL - 2, oy), (ox + TW - 1, oy))

    return surf


# Pre-render tube states
TUBE_NORMAL = render_tube_glass(False, False)
TUBE_SELECTED = render_tube_glass(True, False)
TUBE_COMPLETE = render_tube_glass(False, True)
TUBE_PAD = 18

def draw_liquid_in_tube(surf, tx, ty, tube_data, anim_fill=None):
    """Draw gel-like liquid inside tube. No divisions between same-pour layers."""
    if not tube_data:
        return

    ox = tx + WALL + 1
    ow = IW - 2
    base_bottom = ty + TH - WALL

    # Group consecutive same-color layers into segments
    segments = []
    i = 0
    while i < len(tube_data):
        color_id = tube_data[i]
        count = 1
        while i + count < len(tube_data) and tube_data[i + count] == color_id:
            count += 1
        segments.append((color_id, i, count))
        i += count

    for color_id, start_layer, count in segments:
        base = WATER.get(color_id, (150, 150, 150))
        light = brighter(base, 55)
        dark = dimmer(base, 30)

        total_h = count * LH
        seg_top = base_bottom - (start_layer + count) * LH
        seg_bot = base_bottom - start_layer * LH

        # ── Draw filled region ──
        layer_surf = S(ow, total_h + (BOT_CURVE if start_layer == 0 else 0))

        for row in range(total_h):
            t = row / max(1, total_h - 1)
            # Smooth gel gradient: light at top, base in middle, slightly dark at bottom
            if t < 0.08:
                c = lerpc(light, base, t / 0.08)
            elif t < 0.85:
                c = base
            else:
                c = lerpc(base, dark, (t - 0.85) / 0.15)
            pygame.draw.line(layer_surf, (*c, 230), (0, row), (ow, row))

        # Bottom layer fills into curve
        if start_layer == 0:
            for row in range(BOT_CURVE):
                t = row / max(1, BOT_CURVE - 1)
                # Semicircle width at this depth
                r = BOT_CURVE
                dy = r - row
                if dy > r: continue
                half_w = math.sqrt(max(0, r * r - dy * dy)) * (ow / 2) / r
                cx = ow // 2
                x1 = max(0, int(cx - half_w))
                x2 = min(ow, int(cx + half_w))
                c = lerpc(dark, dimmer(dark, 15), t)
                pygame.draw.line(layer_surf, (*c, 230), (x1, total_h + row), (x2, total_h + row))

        surf.blit(layer_surf, (ox, seg_top))

        # ── Gel shine (left highlight strip) ──
        shine_h = total_h - 4
        if shine_h > 4:
            shine = S(7, shine_h)
            for row in range(shine_h):
                t = row / max(1, shine_h)
                a = int(45 * math.sin(t * math.pi) * (1 - t * 0.3))
                if a > 2:
                    pygame.draw.line(shine, (255, 255, 255, a), (0, row), (5, row))
            surf.blit(shine, (ox + 3, seg_top + 2))

        # ── Top meniscus (curved surface) ──
        if start_layer + count == len(tube_data):
            men = S(ow, 6)
            # Concave meniscus shape
            for col in range(ow):
                t = (col - ow/2) / (ow/2)
                curve_h = int(2 * (1 - t*t))  # parabolic curve
                a = int(70 * (1 - abs(t) * 0.5))
                mc = brighter(base, 65)
                for row in range(curve_h):
                    men.set_at((col, row), (*mc, a - row * 15))
            surf.blit(men, (ox, seg_top))

    # ── Cylindrical liquid shading (subtle dark edges) ──
    edge_shade = S(ow, TH)
    for col in range(ow):
        t = abs((col - ow/2) / (ow/2))
        if t > 0.7:
            a = int(25 * ((t - 0.7) / 0.3))
            for row in range(TH):
                edge_shade.set_at((col, row), (0, 0, 0, a))
    # Only apply where there's liquid
    surf.blit(edge_shade, (ox, ty))


# ════════════════════════════════════════════════════════════════
#  PARTICLES
# ════════════════════════════════════════════════════════════════

class Particle:
    __slots__ = ['x','y','vx','vy','life','sz','c','gv','shape','decay']
    def __init__(s, x, y, c, vx=None, vy=None, sz=None, gv=True, shape=0):
        s.x=x; s.y=y; s.c=c
        s.vx = vx if vx is not None else random.uniform(-3,3)
        s.vy = vy if vy is not None else random.uniform(-6,-2)
        s.sz = sz or random.uniform(3,7)
        s.life = 1.0; s.gv = gv; s.shape = shape
        s.decay = random.uniform(0.7, 1.4)
    def update(s, dt):
        s.x += s.vx * 60 * dt
        s.y += s.vy * 60 * dt
        if s.gv: s.vy += 10 * dt
        s.life -= dt / s.decay
        return s.life > 0
    def draw(s, sf):
        a = max(0, min(255, int(s.life * 255)))
        sz = max(1, int(s.sz * max(0.2, s.life)))
        if a < 5 or sz < 1: return
        t = S(sz*2+2, sz*2+2)
        if s.shape == 0:  # circle
            pygame.draw.circle(t, (*s.c, a), (sz+1,sz+1), sz)
            if sz > 2:
                pygame.draw.circle(t, (*s.c, a//3), (sz+1,sz+1), sz+1)
        elif s.shape == 1:  # confetti
            w = max(1, int(sz * abs(math.sin(s.life * 10))))
            h = max(1, int(sz * 0.5))
            pygame.draw.rect(t, (*s.c, a), (sz+1-w//2, sz+1-h//2, w, h), border_radius=1)
        elif s.shape == 2:  # star
            cx, cy = sz+1, sz+1
            pts = []
            for i in range(10):
                ag = math.radians(i*36 - 90 + s.life*200)
                r = sz if i%2==0 else sz*0.4
                pts.append((cx+r*math.cos(ag), cy+r*math.sin(ag)))
            if len(pts) >= 3:
                pygame.draw.polygon(t, (*s.c, a), pts)
        sf.blit(t, (int(s.x)-sz-1, int(s.y)-sz-1))

# ════════════════════════════════════════════════════════════════
#  LEVEL GENERATION
# ════════════════════════════════════════════════════════════════

def get_diff(lv):
    if lv <= 3:  return 3, 2
    if lv <= 8:  return 4, 2
    if lv <= 15: return 5, 2
    if lv <= 25: return 6, 2
    if lv <= 40: return 7, 2
    if lv <= 60: return 8, 2
    return 9, 2

def gen_level(lv):
    rng = random.Random(lv * 31337 + 97)
    nc, ne = get_diff(lv)
    pool = []
    for c in range(1, nc+1):
        pool.extend([c]*LAYERS)
    for _ in range(300):
        rng.shuffle(pool)
        tubes = [pool[i*LAYERS:(i+1)*LAYERS] for i in range(nc)]
        if not any(len(set(t))==1 for t in tubes):
            break
    for _ in range(ne):
        tubes.append([])
    return [list(t) for t in tubes]

def is_done(t): return len(t)==LAYERS and len(set(t))==1
def all_done(tubes): return all((not t) or is_done(t) for t in tubes)

# ════════════════════════════════════════════════════════════════
#  HINT SOLVER (BFS)
# ════════════════════════════════════════════════════════════════

def find_hint(tubes):
    """Find the best next move using BFS."""
    def state_key(ts):
        return tuple(tuple(t) for t in ts)

    def get_moves(ts):
        moves = []
        for f in range(len(ts)):
            if not ts[f]: continue
            top = ts[f][-1]
            # Count consecutive top
            cnt = 0
            for k in range(len(ts[f])-1, -1, -1):
                if ts[f][k] == top: cnt += 1
                else: break
            for d in range(len(ts)):
                if f == d: continue
                if len(ts[d]) >= LAYERS: continue
                if not ts[d]:
                    # Don't pour complete single-color into empty
                    if len(set(ts[f])) == 1: continue
                    moves.append((f, d))
                elif ts[d][-1] == top and len(ts[d]) + cnt <= LAYERS:
                    moves.append((f, d))
        return moves

    def do_move(ts, f, d):
        ns = [list(t) for t in ts]
        top = ns[f][-1]
        while ns[f] and ns[f][-1] == top and len(ns[d]) < LAYERS:
            ns[d].append(ns[f].pop())
        return ns

    visited = {state_key(tubes)}
    queue = [(tubes, [])]

    for _ in range(15000):  # limit search
        if not queue: break
        current, path = queue.pop(0)
        for move in get_moves(current):
            ns = do_move(current, move[0], move[1])
            key = state_key(ns)
            if key in visited: continue
            visited.add(key)
            new_path = path + [move]
            if all_done(ns):
                return new_path[0] if new_path else None
            queue.append((ns, new_path))

    # If no solution found in limit, just return first valid move
    moves = get_moves(tubes)
    return moves[0] if moves else None

# ════════════════════════════════════════════════════════════════
#  ICON BUTTONS
# ════════════════════════════════════════════════════════════════

def draw_icon_undo(surf, cx, cy, sz, color):
    """Curved undo arrow."""
    # Arc
    rect = (cx - sz, cy - sz, sz*2, sz*2)
    pygame.draw.arc(surf, color, rect, math.radians(30), math.radians(270), 2)
    # Arrow head
    ax = cx + int(sz * math.cos(math.radians(30)))
    ay = cy - int(sz * math.sin(math.radians(30)))
    pts = [(ax, ay), (ax + 4, ay - 5), (ax + 6, ay + 2)]
    pygame.draw.polygon(surf, color, pts)

def draw_icon_restart(surf, cx, cy, sz, color):
    """Circular restart arrow."""
    pygame.draw.arc(surf, color, (cx-sz, cy-sz, sz*2, sz*2), math.radians(45), math.radians(360), 2)
    ax = cx + int(sz * math.cos(math.radians(45)))
    ay = cy - int(sz * math.sin(math.radians(45)))
    pts = [(ax, ay), (ax + 3, ay - 6), (ax + 6, ay + 1)]
    pygame.draw.polygon(surf, color, pts)

def draw_icon_hint(surf, cx, cy, sz, color):
    """Light bulb."""
    # Bulb
    pygame.draw.circle(surf, color, (cx, cy - 2), sz - 2, 2)
    # Rays
    for i in range(4):
        angle = math.radians(i * 90 + 45)
        x1 = cx + int((sz+1) * math.cos(angle))
        y1 = cy - 2 + int((sz+1) * math.sin(angle))
        x2 = cx + int((sz+3) * math.cos(angle))
        y2 = cy - 2 + int((sz+3) * math.sin(angle))
        pygame.draw.line(surf, color, (x1, y1), (x2, y2), 2)
    # Base
    pygame.draw.rect(surf, color, (cx-3, cy+sz-3, 6, 3), border_radius=1)

def draw_icon_add(surf, cx, cy, sz, color):
    """Plus icon for add tube."""
    pygame.draw.line(surf, color, (cx - sz + 2, cy), (cx + sz - 2, cy), 2)
    pygame.draw.line(surf, color, (cx, cy - sz + 2), (cx, cy + sz - 2), 2)

def draw_icon_back(surf, cx, cy, sz, color):
    """Back arrow."""
    pygame.draw.line(surf, color, (cx + sz//2, cy - sz//2), (cx - sz//2, cy), 2)
    pygame.draw.line(surf, color, (cx - sz//2, cy), (cx + sz//2, cy + sz//2), 2)

# ════════════════════════════════════════════════════════════════
#  ASSETS
# ════════════════════════════════════════════════════════════════

def make_star(c1, c2, size=34):
    s = S(size, size)
    cx,cy = size//2, size//2
    ro, ri = size//2-2, size//5
    pts = [(cx + (ro if i%2==0 else ri)*math.cos(math.radians(i*36-90)),
            cy + (ro if i%2==0 else ri)*math.sin(math.radians(i*36-90))) for i in range(10)]
    pygame.draw.polygon(s, c1, pts)
    pts2 = [(cx + ((ro-3) if i%2==0 else max(1,ri-1))*math.cos(math.radians(i*36-90)),
             cy + ((ro-3) if i%2==0 else max(1,ri-1))*math.sin(math.radians(i*36-90))) for i in range(10)]
    pygame.draw.polygon(s, c2, pts2)
    return s

STAR_ON = make_star((245,190,15),(255,230,80))
STAR_OFF = make_star((180,185,200),(200,205,220))

def make_coin():
    s = S(24,24)
    pygame.draw.circle(s,(255,193,7),(12,12),11)
    pygame.draw.circle(s,(255,225,60),(12,11),9)
    t = f11.render("$",True,(190,140,0))
    s.blit(t,(12-t.get_width()//2,12-t.get_height()//2))
    pygame.draw.circle(s,(210,165,0),(12,12),11,2)
    return s

COIN = make_coin()

# ════════════════════════════════════════════════════════════════
#  GAME
# ════════════════════════════════════════════════════════════════

class Game:
    def __init__(self):
        self.state = "menu"
        self.lv = 1
        self.coins = 100
        self.mv = 0
        self.sel = -1
        self.tubes = []
        self.undo_stack = []
        self.pos = []
        self.pts = []  # particles
        self.wt = 0
        self.mt = 0
        self.hint_move = None
        self.hint_blink = 0
        self.completed_tubes = set()
        self.extra_tubes = 0

        # Pour anim
        self.pa = False
        self.ps = self.pd = -1
        self.pp = self.pt_ = 0
        self.po = [0.0, 0.0]
        self.p_tilt = 0.0
        self.poured = False
        self.stream_pts = []

    def load(self, n):
        self.lv = n
        self.tubes = gen_level(n)
        self.mv = 0
        self.sel = -1
        self.undo_stack = []
        self.pts = []
        self.state = "play"
        self.pa = False
        self.wt = 0
        self.hint_move = None
        self.hint_blink = 0
        self.completed_tubes = set()
        self.extra_tubes = 0
        self._layout()

    def _layout(self):
        self.pos = []
        n = len(self.tubes)
        per = min(n, 5)
        rows = math.ceil(n / per)
        sp = TW + 20

        start_y = 125
        if rows > 1:
            start_y = 115

        for i in range(n):
            r = i // per
            c = i % per
            nr = min(per, n - r * per)
            tw = nr * sp - 20
            sx = (SW - tw) // 2
            x = sx + c * sp
            y = start_y + r * (TH + 45)
            self.pos.append((x, y))

    def tube_at(self, mx, my):
        for i,(x,y) in enumerate(self.pos):
            if pygame.Rect(x-10, y-15, TW+20, TH+35).collidepoint(mx,my):
                return i
        return -1

    def can_pour(self, s, d):
        a, b = self.tubes[s], self.tubes[d]
        if not a: return False
        if len(b) >= LAYERS: return False
        if not b: return True
        return a[-1] == b[-1]

    def do_pour(self, s, d):
        a, b = self.tubes[s], self.tubes[d]
        self.undo_stack.append(copy.deepcopy(self.tubes))
        top = a[-1]
        count = 0
        while a and a[-1] == top and len(b) < LAYERS:
            b.append(a.pop())
            count += 1
        self.mv += 1
        SND_DROP.play()

        # Check if target tube just completed
        if is_done(b) and d not in self.completed_tubes:
            self.completed_tubes.add(d)
            self._tube_complete_fx(d)
            SND_COMPLETE.play()

        self.hint_move = None
        return count

    def do_undo(self):
        if not self.undo_stack or self.pa: return
        self.tubes = self.undo_stack.pop()
        self.mv = max(0, self.mv - 1)
        self.sel = -1
        self.hint_move = None
        self.completed_tubes = {i for i, t in enumerate(self.tubes) if t and is_done(t)}
        SND_UNDO.play()

    def add_tube(self):
        if self.extra_tubes >= 2: return
        if not self.coins >= 30: return
        self.coins -= 30
        self.tubes.append([])
        self.extra_tubes += 1
        self._layout()
        SND_TAP.play()

    def get_hint(self):
        h = find_hint(self.tubes)
        if h:
            self.hint_move = h
            self.hint_blink = 0
            SND_TAP.play()

    def _tube_complete_fx(self, idx):
        x, y = self.pos[idx]
        cx = x + TW // 2
        cy = y + TH // 2
        color = WATER.get(self.tubes[idx][0], (200, 200, 200))
        for _ in range(25):
            self.pts.append(Particle(cx + random.randint(-15, 15),
                                    cy + random.randint(-30, 30),
                                    brighter(color, 30),
                                    random.uniform(-3, 3), random.uniform(-5, -1),
                                    random.uniform(3, 6), shape=random.choice([0, 2])))

    def stars(self):
        c, _ = get_diff(self.lv)
        opt = c * 2
        if self.mv <= opt: return 3
        if self.mv <= opt * 2: return 2
        return 1

    # ── Pour animation with tilt ──

    def start_pour(self, s, d):
        self.pa = True; self.ps = s; self.pd = d
        self.pp = 0; self.pt_ = 0
        self.po = [0.0, 0.0]; self.p_tilt = 0.0
        self.poured = False; self.stream_pts = []
        SND_POUR.play()

    def upd_pour(self, dt):
        if not self.pa: return

        spd = 3.5
        self.pt_ += dt * spd
        t = min(1, self.pt_)
        t = t * t * (3 - 2 * t)

        sx, sy = self.pos[self.ps]
        dx, dy = self.pos[self.pd]
        direction = 1 if dx > sx else -1

        if self.pp == 0:  # Lift
            self.po = [0, -55 * t]
            self.p_tilt = 0
            if self.pt_ >= 1: self.pp = 1; self.pt_ = 0

        elif self.pp == 1:  # Slide over
            target_x = (dx - sx) + direction * 25
            self.po = [target_x * t, -55]
            self.p_tilt = 0
            if self.pt_ >= 1: self.pp = 2; self.pt_ = 0

        elif self.pp == 2:  # Tilt + pour
            target_x = (dx - sx) + direction * 25
            self.po = [target_x, -55]
            self.p_tilt = -direction * 45 * t  # Tilt the tube!

            if not self.poured and self.pt_ >= 0.4:
                self.do_pour(self.ps, self.pd)
                self.poured = True

            # Stream particles while tilting
            if self.pt_ > 0.2 and self.pt_ < 0.8:
                px = dx + TW // 2
                py = dy - 5
                if self.tubes[self.pd]:
                    c = WATER.get(self.tubes[self.pd][-1], (200, 200, 200))
                    for _ in range(2):
                        self.stream_pts.append(Particle(
                            px + random.randint(-4, 4), py + random.randint(-10, 5),
                            brighter(c, 20),
                            random.uniform(-1, 1), random.uniform(1, 4),
                            random.uniform(2, 4), gv=True, shape=0))

            if self.pt_ >= 1: self.pp = 3; self.pt_ = 0

        elif self.pp == 3:  # Untilt + return
            target_x = (dx - sx) + direction * 25
            self.po = [target_x * (1-t), -55 * (1-t)]
            self.p_tilt = -direction * 45 * (1-t)
            if self.pt_ >= 1:
                self.pa = False; self.po = [0,0]; self.p_tilt = 0
                if all_done(self.tubes):
                    self.state = "win"; self.wt = 0
                    self._spawn_win()
                    SND_WIN.play()

        self.stream_pts = [p for p in self.stream_pts if p.update(dt)]

    def _spawn_win(self):
        cols = [(255,107,107),(78,205,196),(255,230,109),(162,155,254),
                (255,159,243),(110,200,230),(255,177,66),(150,220,180)]
        for _ in range(130):
            self.pts.append(Particle(
                random.randint(10, SW-10), random.randint(-40, SH//2),
                random.choice(cols),
                random.uniform(-5,5), random.uniform(-9,0),
                random.uniform(4,11), shape=random.choice([0,1,2])))

    # ── Drawing ──

    def draw_bar(self):
        bar = S(SW, 75)
        bar.fill((255, 255, 255, 200))
        screen.blit(bar, (0, 0))
        pygame.draw.line(screen, (200, 210, 225), (0, 75), (SW, 75), 1)

        lt = f24.render(f"Level {self.lv}", True, (50, 55, 75))
        screen.blit(lt, (18, 14))

        c, _ = get_diff(self.lv)
        dn = {3:"Easy",4:"Normal",5:"Medium",6:"Hard",7:"Expert",8:"Master",9:"Insane"}
        dc = {3:(100,180,100),4:(80,150,210),5:(200,170,50),6:(220,130,50),
              7:(210,80,80),8:(180,70,160),9:(160,40,40)}
        dt = f12.render(dn.get(c,""), True, dc.get(c,(120,120,120)))
        screen.blit(dt, (18, 40))

        mt = f16.render(f"Moves: {self.mv}", True, (100, 105, 130))
        screen.blit(mt, (SW//2 - mt.get_width()//2, 28))

        screen.blit(COIN, (SW - 90, 25))
        ct = f20.render(str(self.coins), True, (200, 160, 0))
        screen.blit(ct, (SW - 64, 25))

    def draw_icon_btn(self, x, y, sz, icon_fn, label, hover, highlight=False):
        """Draw a circular icon button."""
        r = sz // 2
        # Shadow
        pygame.draw.circle(screen, (0, 0, 0, 15), (x + r + 1, y + r + 2), r)

        bg = (255, 255, 255, 230) if not hover else (240, 245, 255, 240)
        if highlight:
            pulse = int(abs(math.sin(self.hint_blink * 4)) * 40)
            bg = (255, 240, 200 + pulse, 240)

        circ = S(sz, sz)
        pygame.draw.circle(circ, bg, (r, r), r)
        pygame.draw.circle(circ, (180, 190, 210, 150), (r, r), r, 1)
        screen.blit(circ, (x, y))

        ic = (70, 80, 110) if not hover else (40, 50, 80)
        icon_fn(screen, x + r, y + r, 8, ic)

        lt = f10.render(label, True, (120, 125, 150))
        screen.blit(lt, (x + r - lt.get_width()//2, y + sz + 2))

    def draw_tubes(self, dt):
        for i, tube in enumerate(self.tubes):
            tx, ty = self.pos[i]
            ox, oy = 0.0, 0.0
            tilt = 0.0

            if self.pa and self.ps == i:
                ox, oy = self.po[0], self.po[1]
                tilt = self.p_tilt
            elif i == self.sel and not self.pa:
                oy = -14

            # Hint blink
            is_hint = (self.hint_move and (i == self.hint_move[0] or i == self.hint_move[1]))

            done = is_done(tube) if tube else False
            sel = (i == self.sel and not self.pa)

            # Choose pre-rendered glass
            if sel:
                glass = TUBE_SELECTED
            elif done:
                glass = TUBE_COMPLETE
            else:
                glass = TUBE_NORMAL

            # Hint glow
            if is_hint and not sel:
                pulse = abs(math.sin(self.hint_blink * 4))
                glow = S(TW + 30, TH + 30)
                a = int(50 * pulse)
                pygame.draw.rect(glow, (255, 220, 80, a),
                               (0, 0, TW+30, TH+30), border_radius=BOT_CURVE+15)
                screen.blit(glow, (int(tx + ox) - 15, int(ty + oy) - 15))

            if tilt != 0:
                # Render tube + liquid to temp surface, rotate
                temp = S(TW + TUBE_PAD*2, TH + TUBE_PAD*2 + 20)
                temp.blit(glass, (0, 0))
                draw_liquid_in_tube(temp, TUBE_PAD, TUBE_PAD + 12, tube)

                rotated = pygame.transform.rotate(temp, tilt)
                rw, rh = rotated.get_size()
                screen.blit(rotated,
                           (int(tx + ox) - TUBE_PAD + (TW + TUBE_PAD*2 - rw)//2,
                            int(ty + oy) - TUBE_PAD - 12 + (TH + TUBE_PAD*2 + 20 - rh)//2))
            else:
                screen.blit(glass, (int(tx + ox) - TUBE_PAD, int(ty + oy) - TUBE_PAD - 12))
                draw_liquid_in_tube(screen, int(tx + ox), int(ty + oy), tube)

                # Complete badge
                if done:
                    cx_ = int(tx + ox) + TW // 2
                    cy_ = int(ty + oy) - 6
                    pygame.draw.circle(screen, (76,175,80), (cx_,cy_), 10)
                    pygame.draw.circle(screen, (110,210,130), (cx_,cy_), 8)
                    pts_c = [(cx_-4,cy_+1),(cx_-1,cy_+4),(cx_+5,cy_-3)]
                    pygame.draw.lines(screen, (255,255,255), False, pts_c, 2)

    def draw_play(self, dt):
        screen.blit(BG_LIGHT, (0, 0))
        self.draw_bar()
        self.draw_tubes(dt)

        # Stream particles
        for p in self.stream_pts:
            p.draw(screen)

        # Game particles
        for p in self.pts:
            p.draw(screen)

        # ── Bottom buttons (icon-based) ──
        mouse = pygame.mouse.get_pos()
        btn_sz = 44
        gap = 14
        icons = [
            (draw_icon_undo, "Undo", "undo", False),
            (draw_icon_restart, "Restart", "restart", False),
            (draw_icon_hint, "Hint", "hint", self.hint_move is not None),
            (draw_icon_add, "Add +30", "add", False),
            (draw_icon_back, "Back", "back", False),
        ]
        total = len(icons) * (btn_sz + gap) - gap
        sx = (SW - total) // 2
        by = SH - 72

        self._btns = []
        for idx, (icon_fn, label, name, hl) in enumerate(icons):
            bx = sx + idx * (btn_sz + gap)
            rect = pygame.Rect(bx, by, btn_sz, btn_sz + 14)
            hov = rect.collidepoint(mouse)
            self.draw_icon_btn(bx, by, btn_sz, icon_fn, label, hov, hl)
            self._btns.append((rect, name))

    def draw_win(self, dt):
        self.wt += dt

        ov = S(SW, SH)
        a = min(160, int(self.wt * 500))
        ov.fill((0, 0, 0, a))
        screen.blit(ov, (0, 0))

        if self.wt < 0.2: return None, None

        pw, ph = 340, 360
        px = (SW-pw)//2
        py = (SH-ph)//2 - 20

        # Shadow
        sh = S(pw+8, ph+8)
        pygame.draw.rect(sh, (0,0,0,60), (4,6,pw,ph), border_radius=22)
        screen.blit(sh, (px-4,py-3))

        # Panel
        panel = S(pw, ph)
        panel.fill((255, 255, 255, 245))
        mask = S(pw, ph)
        pygame.draw.rect(mask, (255,255,255), (0,0,pw,ph), border_radius=22)
        panel.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, (200,210,225), (px,py,pw,ph), 1, border_radius=22)

        tt = f32.render("Level Complete!", True, (70, 190, 110))
        screen.blit(tt, (SW//2-tt.get_width()//2, py+28))

        st = self.stars()
        sw_ = 36; sg = 14
        total_s = sw_*3 + sg*2
        ssx = SW//2 - total_s//2
        for i in range(3):
            x_ = ssx + i*(sw_+sg)
            y_ = py + 85
            delay = i * 0.12
            elapsed = max(0, self.wt - 0.2 - delay)
            if elapsed > 0:
                sc = min(1, elapsed*6)
                bounce = 1 + 0.25*max(0, 1-elapsed*4)
                fsz = int(sw_*sc*bounce)
                img = STAR_ON if i < st else STAR_OFF
                scaled = pygame.transform.smoothscale(img, (fsz, fsz))
                screen.blit(scaled, (x_+sw_//2-fsz//2, y_+sw_//2-fsz//2))

        mt = f20.render(f"Moves: {self.mv}", True, (80, 85, 110))
        screen.blit(mt, (SW//2-mt.get_width()//2, py+140))

        reward = st * 15
        screen.blit(COIN, (SW//2-40, py+175))
        rt = f24.render(f"+ {reward}", True, (200, 160, 0))
        screen.blit(rt, (SW//2-12, py+175))

        mouse = pygame.mouse.get_pos()
        bw_, bh_ = 135, 48
        gap_ = 14
        bx1 = SW//2 - bw_ - gap_//2
        bx2 = SW//2 + gap_//2
        by_ = py + 250

        nr = pygame.Rect(bx1, by_, bw_, bh_)
        rr = pygame.Rect(bx2, by_, bw_, bh_)

        for rect, text, base_c in [(nr,"Next Level",(70,185,105)),(rr,"Replay",(100,110,140))]:
            hov = rect.collidepoint(mouse)
            c = brighter(base_c, 15) if hov else base_c
            pygame.draw.rect(screen,(0,0,0,30),(rect.x+2,rect.y+3,bw_,bh_),border_radius=14)
            pygame.draw.rect(screen, c, rect, border_radius=14)
            pygame.draw.rect(screen, brighter(c,30), rect, 1, border_radius=14)
            t = f20.render(text, True, (255,255,255))
            screen.blit(t, (rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2))

        return nr, rr

    def draw_menu(self, dt):
        self.mt += dt
        screen.blit(BG_LIGHT, (0,0))

        if random.random() < 0.04:
            c = random.choice(list(WATER.values()))
            self.pts.append(Particle(random.randint(0,SW), SH+5, brighter(c,30),
                random.uniform(-0.3,0.3), random.uniform(-0.7,-0.3),
                random.uniform(2,4), gv=False, shape=0))

        for p in self.pts:
            p.draw(screen)

        b = f12.render("SUPER GAME APP", True, (140, 150, 175))
        screen.blit(b, (SW//2-b.get_width()//2, 140))

        t1 = f48.render("Water Sort", True, (50, 60, 85))
        screen.blit(t1, (SW//2-t1.get_width()//2, 160))
        t2 = f32.render("Puzzle", True, (80, 150, 210))
        screen.blit(t2, (SW//2-t2.get_width()//2, 210))

        # Preview tubes
        preview = [[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4]]
        sp = TW + 14
        ptw = len(preview)*sp - 14
        psx = (SW-ptw)//2
        for i, pt in enumerate(preview):
            tx = psx + i * sp
            ty = 290 + int(math.sin(self.mt*2+i*1.1)*8)
            screen.blit(TUBE_COMPLETE, (tx-TUBE_PAD, ty-TUBE_PAD-12))
            draw_liquid_in_tube(screen, tx, ty, pt)

        # Play button
        mouse = pygame.mouse.get_pos()
        pr = pygame.Rect(SW//2-105, 520, 210, 56)
        hov = pr.collidepoint(mouse)
        pc = (80,200,120) if not hov else (95,215,135)

        pygame.draw.rect(screen,(0,0,0,30),(pr.x+2,pr.y+3,210,56),border_radius=28)
        pygame.draw.rect(screen, pc, pr, border_radius=28)
        shine = S(190,18)
        pygame.draw.rect(shine,(255,255,255,25),(0,0,190,18),border_radius=14)
        screen.blit(shine,(pr.x+10,pr.y+4))
        pygame.draw.rect(screen, brighter(pc,30), pr, 1, border_radius=28)
        pt_ = f24.render("P L A Y", True, (255,255,255))
        screen.blit(pt_, (pr.centerx-pt_.get_width()//2, pr.centery-pt_.get_height()//2))

        li = f16.render(f"Level {self.lv}", True, (100,110,140))
        screen.blit(li, (SW//2-li.get_width()//2, 595))

        screen.blit(COIN, (SW//2-30, 625))
        ci = f16.render(str(self.coins), True, (200,160,0))
        screen.blit(ci, (SW//2-4, 628))

        ft = f11.render("Tap PLAY to start", True, (160,170,190))
        screen.blit(ft, (SW//2-ft.get_width()//2, SH-30))

        return pr

    # ── Main loop ──

    def run(self):
        running = True
        play_r = next_r = rep_r = None

        while running:
            dt = clock.tick(FPS) / 1000.0
            mouse = pygame.mouse.get_pos()

            if self.hint_move:
                self.hint_blink += dt

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if self.state == "play": self.state = "menu"
                        else: running = False
                    if ev.key == pygame.K_u and self.state == "play": self.do_undo()
                    if ev.key == pygame.K_r and self.state == "play": self.load(self.lv)
                    if ev.key == pygame.K_h and self.state == "play": self.get_hint()

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.state == "menu":
                        if play_r and play_r.collidepoint(mouse):
                            SND_TAP.play()
                            self.load(self.lv)

                    elif self.state == "play" and not self.pa:
                        btn_hit = False
                        if hasattr(self, '_btns'):
                            for r, name in self._btns:
                                if r.collidepoint(mouse):
                                    if name == "undo": self.do_undo()
                                    elif name == "restart": self.load(self.lv)
                                    elif name == "hint": self.get_hint()
                                    elif name == "add": self.add_tube()
                                    elif name == "back": self.state = "menu"; SND_TAP.play()
                                    btn_hit = True; break

                        if not btn_hit:
                            ci = self.tube_at(*mouse)
                            if ci >= 0:
                                SND_TAP.play()
                                if self.sel == -1:
                                    if self.tubes[ci]: self.sel = ci
                                elif self.sel == ci:
                                    self.sel = -1
                                else:
                                    if self.can_pour(self.sel, ci):
                                        s = self.sel; self.sel = -1
                                        self.start_pour(s, ci)
                                    elif self.tubes[ci]:
                                        self.sel = ci
                                    else:
                                        self.sel = -1

                    elif self.state == "win":
                        if next_r and next_r.collidepoint(mouse):
                            SND_TAP.play()
                            self.coins += self.stars() * 15
                            self.load(self.lv + 1)
                        elif rep_r and rep_r.collidepoint(mouse):
                            SND_TAP.play()
                            self.load(self.lv)

            # Update
            self.upd_pour(dt)
            self.pts = [p for p in self.pts if p.update(dt)]

            if self.state == "win" and self.wt < 4 and random.random() < 0.1:
                cols = [(255,107,107),(78,205,196),(255,230,109),(162,155,254),(255,159,243)]
                self.pts.append(Particle(
                    random.randint(20,SW-20), random.randint(-20,SH//3),
                    random.choice(cols), random.uniform(-2,2), random.uniform(-3,1),
                    random.uniform(4,8), shape=random.choice([0,1,2])))

            # Draw
            if self.state == "menu":
                play_r = self.draw_menu(dt)
            elif self.state == "play":
                self.draw_play(dt)
            elif self.state == "win":
                self.draw_play(dt)
                next_r, rep_r = self.draw_win(dt)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
