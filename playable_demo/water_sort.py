"""
Water Sort Puzzle — Production Quality
"""

import pygame
import pygame.gfxdraw
import sys
import random
import copy
import math

pygame.init()

# ════════════════════ SCREEN ════════════════════
SW, SH = 420, 780
screen = pygame.display.set_mode((SW, SH), pygame.SRCALPHA)
pygame.display.set_caption("Water Sort Puzzle")
clock = pygame.time.Clock()
FPS = 60
LAYERS = 4

# ════════════════════ COLORS ════════════════════
WATER = {
    1: (220, 50, 47),
    2: (38, 139, 210),
    3: (133, 153, 0),
    4: (253, 208, 35),
    5: (235, 120, 40),
    6: (148, 82, 200),
    7: (42, 161, 152),
    8: (236, 85, 157),
    9: (160, 120, 90),
    10:(88, 150, 200),
    11:(180, 210, 80),
    12:(210, 160, 60),
}

def lerp_color(a, b, t):
    return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

def brighter(c, n=50):
    return tuple(min(255, x+n) for x in c)

def dimmer(c, n=40):
    return tuple(max(0, x-n) for x in c)

# ════════════════════ FONTS ════════════════════
def F(size, bold=False):
    for name in ["Avenir Next", "Avenir", "SF Pro Display", "Helvetica Neue", "Helvetica", "Arial"]:
        try: return pygame.font.SysFont(name, size, bold)
        except: pass
    return pygame.font.SysFont(None, size, bold)

f48 = F(48, True)
f32 = F(32, True)
f24 = F(24, True)
f20 = F(20, True)
f16 = F(16)
f14 = F(14)
f12 = F(12)
f11 = F(11)

# ════════════════════ TUBE GEOMETRY ════════════════════
# Tube looks like a real test tube: rounded bottom, open top
TW = 48       # outer width
TH = 155      # outer height
WALL = 4      # glass wall thickness
IW = TW - WALL*2  # inner width
IH = TH - WALL - 12  # inner height (12 = bottom curve)
LH = (IH) // LAYERS  # layer height
BOT_R = IW // 2  # bottom curve radius

def make_alpha(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)

# ════════════════════ TUBE RENDERER ════════════════════

def draw_tube_body(surf, x, y, highlight=False, done=False):
    """Draw realistic glass test tube."""
    # Outer shape: two vertical lines + semicircle bottom
    glass_alpha = 140
    gc = (180, 195, 220) if not highlight else (255, 220, 100)
    if done:
        gc = (120, 220, 140)

    # Glass fill (subtle)
    inner = make_alpha(TW, TH)

    # Inner dark fill
    # Top rect part
    pygame.draw.rect(inner, (12, 14, 28, 160), (WALL, 0, IW, TH - BOT_R - WALL))
    # Bottom semicircle
    pygame.draw.ellipse(inner, (12, 14, 28, 160),
                        (WALL, TH - BOT_R*2 - WALL, IW, BOT_R*2))

    surf.blit(inner, (x, y))

    # Glass walls
    wall_surf = make_alpha(TW, TH)

    # Left wall
    for i in range(WALL):
        alpha = int(glass_alpha * (1 - i/WALL * 0.6))
        c = (*gc, alpha)
        pygame.draw.line(wall_surf, c, (i, 0), (i, TH - BOT_R - 2))

    # Right wall
    for i in range(WALL):
        alpha = int(glass_alpha * (0.4 + i/WALL * 0.3))
        c = (*gc, alpha)
        pygame.draw.line(wall_surf, c, (TW-1-i, 0), (TW-1-i, TH - BOT_R - 2))

    # Bottom arc
    for i in range(WALL):
        alpha = int(glass_alpha * (0.7))
        rect = (WALL - i, TH - BOT_R*2 - WALL + i, IW + i*2, BOT_R*2)
        pygame.draw.arc(wall_surf, (*gc, alpha),
                       rect, math.pi, 2*math.pi, 1)

    # Left inner shine (simulates glass reflection)
    for row in range(8, TH - BOT_R - 10):
        t = (row - 8) / max(1, TH - BOT_R - 18)
        # Bell curve shine
        intensity = math.exp(-((t - 0.25)**2) / 0.03) * 45
        if intensity > 2:
            pygame.draw.line(wall_surf, (255, 255, 255, int(intensity)),
                           (WALL + 1, row), (WALL + 4, row))

    # Right subtle reflection
    for row in range(15, TH - BOT_R - 15):
        t = (row - 15) / max(1, TH - BOT_R - 30)
        intensity = math.exp(-((t - 0.4)**2) / 0.05) * 20
        if intensity > 2:
            pygame.draw.line(wall_surf, (255, 255, 255, int(intensity)),
                           (TW - WALL - 3, row), (TW - WALL - 1, row))

    surf.blit(wall_surf, (x, y))

    # Top rim
    rim = make_alpha(TW, 4)
    pygame.draw.rect(rim, (*gc, 100), (0, 0, TW, 2), border_radius=1)
    pygame.draw.rect(rim, (*brighter(gc, 30), 60), (1, 0, TW-2, 1))
    surf.blit(rim, (x, y))


def draw_liquid(surf, x, y, tube_data):
    """Draw liquid layers inside tube with realistic appearance."""
    if not tube_data:
        return

    for i, cid in enumerate(tube_data):
        if cid <= 0:
            continue

        base = WATER.get(cid, (128,128,128))
        light = brighter(base, 45)
        dark = dimmer(base, 35)
        vdark = dimmer(base, 55)

        # Layer position (inside the tube)
        lx = x + WALL + 1
        lw = IW - 2

        # Calculate y position from bottom
        # Bottom of inner area
        inner_bottom = y + TH - WALL - 2
        ly = inner_bottom - (i + 1) * LH
        lh = LH

        if i == 0:
            # First layer: fill into the rounded bottom
            layer = make_alpha(lw, lh + BOT_R)

            # Main rect part
            for row in range(lh):
                t = row / max(1, lh - 1)
                c = lerp_color(light, base, min(1, t * 1.5))
                if t > 0.7:
                    c = lerp_color(base, dark, (t - 0.7) / 0.3)
                pygame.draw.line(layer, (*c, 225), (0, row), (lw, row))

            # Bottom curve fill
            for row in range(BOT_R):
                t = row / max(1, BOT_R - 1)
                # How wide is the tube at this point in the curve
                # Semicircle: width = 2*sqrt(r^2 - (r-row)^2) roughly
                dy = BOT_R - row
                if dy > BOT_R:
                    continue
                half_w = math.sqrt(max(0, BOT_R*BOT_R - dy*dy))
                cx = lw // 2
                x1 = max(0, int(cx - half_w))
                x2 = min(lw, int(cx + half_w))
                c = lerp_color(dark, vdark, t)
                pygame.draw.line(layer, (*c, 225), (x1, lh + row), (x2, lh + row))

            surf.blit(layer, (lx, ly))

        else:
            # Regular layer
            layer = make_alpha(lw, lh)

            for row in range(lh):
                t = row / max(1, lh - 1)
                if t < 0.15:
                    c = lerp_color(light, base, t / 0.15)
                elif t < 0.8:
                    c = base
                else:
                    c = lerp_color(base, dark, (t - 0.8) / 0.2)
                pygame.draw.line(layer, (*c, 225), (0, row), (lw, row))

            surf.blit(layer, (lx, ly))

        # Meniscus on top layer
        if i == len(tube_data) - 1:
            men = make_alpha(lw, 3)
            pygame.draw.line(men, (*brighter(base, 70), 90), (2, 0), (lw-2, 0))
            pygame.draw.line(men, (*brighter(base, 40), 50), (1, 1), (lw-1, 1))
            surf.blit(men, (lx, ly))

        # Subtle left highlight on liquid
        liq_shine = make_alpha(5, lh - 2)
        for row in range(lh - 2):
            t = row / max(1, lh - 3)
            a = int(30 * math.sin(t * math.pi))
            if a > 0:
                pygame.draw.line(liq_shine, (255, 255, 255, a), (0, row), (3, row))
        surf.blit(liq_shine, (lx + 2, ly + 1))

        # Divider line between layers (subtle)
        if i > 0:
            div = make_alpha(lw, 1)
            div.fill((*dimmer(base, 20), 40))
            surf.blit(div, (lx, ly + lh - 1))


def draw_selection_glow(surf, x, y):
    """Draw golden glow behind selected tube."""
    glow = make_alpha(TW + 30, TH + 30)
    for r in range(20, 0, -1):
        a = int(50 * (1 - r/20))
        rect = (15 - r, 15 - r, TW + r*2, TH + r*2)
        pygame.draw.rect(glow, (255, 210, 60, a), rect, border_radius=BOT_R + r)
    surf.blit(glow, (x - 15, y - 15))


def draw_complete_glow(surf, x, y):
    """Draw green glow behind completed tube."""
    glow = make_alpha(TW + 24, TH + 24)
    for r in range(16, 0, -1):
        a = int(35 * (1 - r/16))
        rect = (12 - r, 12 - r, TW + r*2, TH + r*2)
        pygame.draw.rect(glow, (80, 200, 100, a), rect, border_radius=BOT_R + r)
    surf.blit(glow, (x - 12, y - 12))


def draw_complete_badge(surf, x, y):
    """Checkmark badge."""
    cx = x + TW // 2
    cy = y - 6
    # Shadow
    pygame.draw.circle(surf, (0, 0, 0, 40), (cx + 1, cy + 2), 10)
    # Green circle
    pygame.draw.circle(surf, (76, 175, 80), (cx, cy), 10)
    pygame.draw.circle(surf, (100, 200, 110), (cx, cy), 8)
    # Check mark
    pts = [(cx-4, cy+1), (cx-1, cy+4), (cx+5, cy-3)]
    pygame.draw.lines(surf, (255, 255, 255), False, pts, 2)


# ════════════════════ LEVEL GEN ════════════════════

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

def is_done(tube):
    return len(tube)==LAYERS and len(set(tube))==1

def all_done(tubes):
    return all((not t) or is_done(t) for t in tubes)

# ════════════════════ PARTICLES ════════════════════

class P:
    __slots__=['x','y','vx','vy','life','sz','c','gv','shape','decay']
    def __init__(s, x, y, c, vx=None, vy=None, sz=None, gv=True, shape=0):
        s.x=x; s.y=y; s.c=c
        s.vx=vx if vx is not None else random.uniform(-3,3)
        s.vy=vy if vy is not None else random.uniform(-6,-1)
        s.sz=sz or random.uniform(3,7)
        s.life=1.0; s.gv=gv; s.shape=shape
        s.decay=random.uniform(0.7,1.3)
    def update(s, dt):
        s.x+=s.vx*60*dt; s.y+=s.vy*60*dt
        if s.gv: s.vy+=9*dt
        s.life-=dt/s.decay
        return s.life>0
    def draw(s, sf):
        a=max(0,min(255,int(s.life*255)))
        sz=max(1,int(s.sz*max(0.2,s.life)))
        if a<5 or sz<1: return
        t=make_alpha(sz*2+2,sz*2+2)
        if s.shape==0:
            pygame.draw.circle(t,(*s.c,a),(sz+1,sz+1),sz)
        elif s.shape==1: # confetti
            w=max(1,int(sz*abs(math.sin(s.life*8))))
            h=max(1,int(sz*0.5))
            pygame.draw.rect(t,(*s.c,a),(sz+1-w//2,sz+1-h//2,w,h))
        elif s.shape==2: # star
            cx,cy=sz+1,sz+1
            pts=[]
            for i in range(10):
                ag=math.radians(i*36-90+s.life*200)
                r=sz if i%2==0 else sz*0.4
                pts.append((cx+r*math.cos(ag),cy+r*math.sin(ag)))
            if len(pts)>=3:
                pygame.draw.polygon(t,(*s.c,a),pts)
        sf.blit(t,(int(s.x)-sz-1,int(s.y)-sz-1))

# ════════════════════ BACKGROUND ════════════════════

def make_bg():
    s = pygame.Surface((SW, SH))
    c1 = (18, 20, 42)
    c2 = (10, 11, 25)
    for y in range(SH):
        t = y/SH
        s.set_at  # use draw line for speed
        r=int(c1[0]*(1-t)+c2[0]*t)
        g=int(c1[1]*(1-t)+c2[1]*t)
        b=int(c1[2]*(1-t)+c2[2]*t)
        pygame.draw.line(s,(r,g,b),(0,y),(SW,y))
    # Subtle pattern dots
    rng = random.Random(42)
    for _ in range(60):
        x = rng.randint(0, SW)
        y = rng.randint(0, SH)
        a = rng.randint(5, 15)
        pygame.draw.circle(s, (255,255,255,a) if a > 0 else (30,30,50), (x,y), rng.randint(1,2))
    return s

BG = make_bg()

# ════════════════════ STAR ASSET ════════════════════

def make_star(c1, c2, size=32):
    s = make_alpha(size, size)
    cx,cy=size//2,size//2
    ro,ri=size//2-2, size//5
    pts=[]
    for i in range(10):
        a=math.radians(i*36-90)
        r=ro if i%2==0 else ri
        pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    pygame.draw.polygon(s,c1,pts)
    # Inner
    pts2=[]
    for i in range(10):
        a=math.radians(i*36-90)
        r=(ro-3) if i%2==0 else max(1,ri-1)
        pts2.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    pygame.draw.polygon(s,c2,pts2)
    return s

STAR_ON = make_star((245,190,15),(255,225,80))
STAR_OFF = make_star((45,48,65),(55,58,75))

# ════════════════════ COIN ════════════════════

def make_coin():
    s=make_alpha(24,24)
    pygame.draw.circle(s,(255,193,7),(12,12),11)
    pygame.draw.circle(s,(255,220,50),(12,11),9)
    t=f11.render("$",True,(190,140,0))
    s.blit(t,(12-t.get_width()//2,12-t.get_height()//2))
    pygame.draw.circle(s,(200,155,0),(12,12),11,2)
    return s

COIN = make_coin()

# ════════════════════ GAME CLASS ════════════════════

class Game:
    def __init__(self):
        self.st = "menu"
        self.lv = 1
        self.coins = 100
        self.mv = 0
        self.sel = -1
        self.tubes = []
        self.undo = []
        self.pos = []
        self.pts = []  # particles
        self.wt = 0    # win timer
        self.mt = 0    # menu timer

        # Pour animation
        self.pa = False  # pour active
        self.ps = -1     # pour source
        self.pd = -1     # pour dest
        self.pp = 0      # pour phase
        self.pt = 0      # pour time
        self.po = [0,0]  # pour offset
        self.poured = False

    def load(self, n):
        self.lv = n
        self.tubes = gen_level(n)
        self.mv = 0
        self.sel = -1
        self.undo = []
        self.pts = []
        self.st = "play"
        self.pa = False
        self.wt = 0
        self._layout()

    def _layout(self):
        self.pos = []
        n = len(self.tubes)
        per = min(n, 5)
        rows = math.ceil(n/per)
        sp = TW + 18

        for i in range(n):
            r = i // per
            c = i % per
            nr = min(per, n - r*per)
            tw = nr * sp - 18
            sx = (SW - tw) // 2
            x = sx + c * sp
            y = 130 + r * (TH + 45)
            self.pos.append((x, y))

    def tube_at(self, mx, my):
        for i,(x,y) in enumerate(self.pos):
            if pygame.Rect(x-8, y-15, TW+16, TH+30).collidepoint(mx,my):
                return i
        return -1

    def can_pour(self, s, d):
        a,b=self.tubes[s],self.tubes[d]
        if not a: return False
        if len(b)>=LAYERS: return False
        if not b: return True
        return a[-1]==b[-1]

    def do_pour(self, s, d):
        a,b=self.tubes[s],self.tubes[d]
        self.undo.append(copy.deepcopy(self.tubes))
        top=a[-1]
        while a and a[-1]==top and len(b)<LAYERS:
            b.append(a.pop())
        self.mv+=1

    def do_undo(self):
        if not self.undo or self.pa: return
        self.tubes=self.undo.pop()
        self.mv=max(0,self.mv-1)
        self.sel=-1

    def stars(self):
        c,_=get_diff(self.lv)
        opt=c*2
        if self.mv<=opt: return 3
        if self.mv<=opt*2: return 2
        return 1

    # ── Pour animation ──

    def start_pour(self, s, d):
        self.pa=True; self.ps=s; self.pd=d
        self.pp=0; self.pt=0; self.po=[0,0]; self.poured=False

    def upd_pour(self, dt):
        if not self.pa: return
        spd = 4.5
        self.pt += dt * spd
        t = min(1, self.pt)
        t = t*t*(3-2*t)  # smoothstep

        sx,sy = self.pos[self.ps]
        dx,dy = self.pos[self.pd]

        if self.pp==0:  # lift
            self.po=[0, -50*t]
            if self.pt>=1: self.pp=1; self.pt=0
        elif self.pp==1:  # slide
            tx=(dx-sx)+(22 if dx>sx else -22)
            self.po=[tx*t, -50]
            if self.pt>=1: self.pp=2; self.pt=0
        elif self.pp==2:  # pour
            tx=(dx-sx)+(22 if dx>sx else -22)
            self.po=[tx,-50]
            if not self.poured and self.pt>=0.25:
                self.do_pour(self.ps,self.pd)
                self.poured=True
                # Splash particles
                px=dx+TW//2; py=dy+10
                if self.tubes[self.pd]:
                    c=WATER.get(self.tubes[self.pd][-1],(200,200,200))
                    for _ in range(10):
                        self.pts.append(P(px+random.randint(-6,6),py,c,
                            random.uniform(-2,2),random.uniform(-5,-1),random.uniform(2,4)))
            if self.pt>=0.7: self.pp=3; self.pt=0
        elif self.pp==3:  # return
            tx=(dx-sx)+(22 if dx>sx else -22)
            self.po=[tx*(1-t), -50*(1-t)]
            if self.pt>=1:
                self.pa=False; self.po=[0,0]
                if all_done(self.tubes):
                    self.st="win"; self.wt=0
                    self._spawn_win()

    def _spawn_win(self):
        cols=[(255,107,107),(78,205,196),(255,230,109),(162,155,254),
              (255,159,243),(110,200,230),(255,177,66),(150,220,180)]
        for _ in range(120):
            c=random.choice(cols)
            sh=random.choice([0,1,2])
            self.pts.append(P(random.randint(10,SW-10),random.randint(-30,SH//2),
                c,random.uniform(-4,4),random.uniform(-8,0),random.uniform(4,10),shape=sh))

    # ── Draw helpers ──

    def draw_bar(self):
        bar=make_alpha(SW,75)
        for y in range(75):
            a = int(230*(1-y/90))
            pygame.draw.line(bar,(16,18,38,a),(0,y),(SW,y))
        screen.blit(bar,(0,0))
        pygame.draw.line(screen,(40,44,65),(0,75),(SW,75),1)

        # Level
        lt=f24.render(f"Level {self.lv}",True,(225,230,248))
        screen.blit(lt,(18,14))

        c,_=get_diff(self.lv)
        dn={3:"Easy",4:"Normal",5:"Medium",6:"Hard",7:"Expert",8:"Master",9:"Insane"}
        dc={3:(100,200,120),4:(100,170,220),5:(220,195,80),6:(230,140,60),
            7:(220,90,90),8:(190,80,170),9:(170,50,50)}
        d=dn.get(c,"")
        dt=f12.render(d,True,dc.get(c,(150,150,150)))
        screen.blit(dt,(18,42))

        # Moves center
        mt=f16.render(f"Moves: {self.mv}",True,(150,155,180))
        screen.blit(mt,(SW//2-mt.get_width()//2,28))

        # Coins right
        screen.blit(COIN,(SW-95,24))
        ct=f20.render(str(self.coins),True,(255,215,0))
        screen.blit(ct,(SW-68,24))

    def draw_btn(self, x, y, w, h, text, hover, color=(48,52,75)):
        c = brighter(color,15) if hover else color
        # Shadow
        sh=make_alpha(w,h)
        pygame.draw.rect(sh,(0,0,0,45),(2,3,w-2,h-2),border_radius=h//2)
        screen.blit(sh,(x,y))
        # Body
        pygame.draw.rect(screen,c,(x,y,w,h),border_radius=h//2)
        # Top shine
        shine=make_alpha(w-6,h//3)
        pygame.draw.rect(shine,(255,255,255,12),(0,0,w-6,h//3),border_radius=h//2)
        screen.blit(shine,(x+3,y+2))
        # Border
        pygame.draw.rect(screen,brighter(c,25),(x,y,w,h),1,border_radius=h//2)
        # Text
        t=f14.render(text,True,(210,215,230))
        screen.blit(t,(x+w//2-t.get_width()//2, y+h//2-t.get_height()//2))

    def draw_tubes(self):
        for i,tube in enumerate(self.tubes):
            tx,ty=self.pos[i]
            ox,oy=0,0

            if self.pa and self.ps==i:
                ox,oy=self.po[0],self.po[1]
            elif i==self.sel and not self.pa:
                oy=-16

            dx=tx+ox; dy=ty+oy
            done_t = is_done(tube) if tube else False
            sel_t = (i==self.sel and not self.pa)

            if sel_t:
                draw_selection_glow(screen, int(dx), int(dy))
            if done_t:
                draw_complete_glow(screen, int(dx), int(dy))

            draw_tube_body(screen, int(dx), int(dy), sel_t, done_t)
            draw_liquid(screen, int(dx), int(dy), tube)

            if done_t:
                draw_complete_badge(screen, int(dx), int(dy))

    def draw_play(self, dt):
        screen.blit(BG,(0,0))
        self.draw_bar()
        self.draw_tubes()

        # Particles
        for p in self.pts:
            p.draw(screen)

        # Bottom buttons
        mouse=pygame.mouse.get_pos()
        bw,bh=82,34
        gap=8
        total=bw*4+gap*3
        sx=(SW-total)//2
        by=SH-65

        names=["Undo","Restart","Hint","Back"]
        self._btns=[]
        for i,name in enumerate(names):
            bx=sx+i*(bw+gap)
            r=pygame.Rect(bx,by,bw,bh)
            self._btns.append((r,name))
            self.draw_btn(bx,by,bw,bh,name,r.collidepoint(mouse))

        h=f11.render("U=Undo  R=Restart  ESC=Menu",True,(35,38,55))
        screen.blit(h,(SW//2-h.get_width()//2,SH-22))

    def draw_win(self, dt):
        self.wt+=dt

        # Overlay
        ov=make_alpha(SW,SH)
        a=min(175,int(self.wt*500))
        ov.fill((0,0,0,a))
        screen.blit(ov,(0,0))

        if self.wt<0.2: return None,None

        pw,ph=340,350
        px=(SW-pw)//2; py=(SH-ph)//2-15

        # Shadow
        sh=make_alpha(pw+8,ph+8)
        pygame.draw.rect(sh,(0,0,0,80),(4,6,pw,ph),border_radius=22)
        screen.blit(sh,(px-4,py-3))

        # Panel gradient
        panel=make_alpha(pw,ph)
        for row in range(ph):
            t=row/ph
            r=int(32*(1-t)+20*t)
            g=int(36*(1-t)+22*t)
            b=int(58*(1-t)+40*t)
            pygame.draw.line(panel,(r,g,b,235),(0,row),(pw,row))
        # Mask to rounded
        mask=make_alpha(pw,ph)
        pygame.draw.rect(mask,(255,255,255),(0,0,pw,ph),border_radius=22)
        panel.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(panel,(px,py))

        # Border
        pygame.draw.rect(screen,(55,60,85),(px,py,pw,ph),1,border_radius=22)

        # Title
        tt=f32.render("Level Complete!",True,(100,225,135))
        screen.blit(tt,(SW//2-tt.get_width()//2,py+28))

        # Stars with bounce
        st=self.stars()
        sw=36; sg=14
        total_s=sw*3+sg*2
        ssx=SW//2-total_s//2
        for i in range(3):
            x=ssx+i*(sw+sg)
            y_s=py+85
            delay=i*0.12
            elapsed=max(0,self.wt-0.2-delay)
            if elapsed>0:
                sc=min(1.0,elapsed*6)
                bounce=1+0.25*max(0,1-elapsed*4)
                final_sz=int(sw*sc*bounce)
                img=STAR_ON if i<st else STAR_OFF
                scaled=pygame.transform.smoothscale(img,(final_sz,final_sz))
                screen.blit(scaled,(x+sw//2-final_sz//2, y_s+sw//2-final_sz//2))

        # Moves
        mt=f20.render(f"Moves: {self.mv}",True,(185,190,210))
        screen.blit(mt,(SW//2-mt.get_width()//2,py+140))

        # Reward
        reward=st*15
        screen.blit(COIN,(SW//2-40,py+175))
        rt=f24.render(f"+ {reward}",True,(255,215,0))
        screen.blit(rt,(SW//2-12,py+175))

        # Buttons
        mouse=pygame.mouse.get_pos()
        bw_b,bh_b=135,46
        gap_b=12
        bx1=SW//2-bw_b-gap_b//2
        bx2=SW//2+gap_b//2
        by_b=py+240

        nr=pygame.Rect(bx1,by_b,bw_b,bh_b)
        rr=pygame.Rect(bx2,by_b,bw_b,bh_b)

        # Next button (green)
        nc=brighter((55,170,90),15) if nr.collidepoint(mouse) else (55,170,90)
        pygame.draw.rect(screen,(0,0,0,50),(bx1+2,by_b+3,bw_b,bh_b),border_radius=14)
        pygame.draw.rect(screen,nc,nr,border_radius=14)
        pygame.draw.rect(screen,brighter(nc,30),nr,1,border_radius=14)
        nt=f20.render("Next Level",True,(255,255,255))
        screen.blit(nt,(nr.centerx-nt.get_width()//2,nr.centery-nt.get_height()//2))

        # Replay button
        rc=brighter((50,55,80),15) if rr.collidepoint(mouse) else (50,55,80)
        pygame.draw.rect(screen,(0,0,0,50),(bx2+2,by_b+3,bw_b,bh_b),border_radius=14)
        pygame.draw.rect(screen,rc,rr,border_radius=14)
        pygame.draw.rect(screen,brighter(rc,30),rr,1,border_radius=14)
        rrt=f20.render("Replay",True,(210,215,230))
        screen.blit(rrt,(rr.centerx-rrt.get_width()//2,rr.centery-rrt.get_height()//2))

        return nr, rr

    def draw_menu(self, dt):
        self.mt+=dt
        screen.blit(BG,(0,0))

        # Floating particles
        if random.random()<0.06:
            c=random.choice(list(WATER.values()))
            self.pts.append(P(random.randint(0,SW),SH+5,c,
                random.uniform(-0.3,0.3),random.uniform(-0.8,-0.3),
                random.uniform(2,4),gv=False))

        for p in self.pts:
            p.draw(screen)

        # Badge
        b=f12.render("SUPER GAME APP",True,(70,75,100))
        screen.blit(b,(SW//2-b.get_width()//2,135))

        # Title
        t1=f48.render("Water Sort",True,(230,235,255))
        screen.blit(t1,(SW//2-t1.get_width()//2,155))
        t2=f32.render("Puzzle",True,(80,160,225))
        screen.blit(t2,(SW//2-t2.get_width()//2,210))

        # Preview tubes
        preview = [
            [1,1,1,1], [2,2,2,2], [3,3,3,3], [4,4,4,4]
        ]
        sp = TW + 12
        total_pw = len(preview) * sp - 12
        psx = (SW - total_pw) // 2
        for i, pt in enumerate(preview):
            tx = psx + i * sp
            ty = 290 + int(math.sin(self.mt * 2 + i * 1.1) * 8)
            draw_complete_glow(screen, tx, ty)
            draw_tube_body(screen, tx, ty, False, True)
            draw_liquid(screen, tx, ty, pt)

        # Play button
        mouse = pygame.mouse.get_pos()
        play_r = pygame.Rect(SW//2-100, 520, 200, 56)
        hov = play_r.collidepoint(mouse)
        pc = brighter((50,180,100),15) if hov else (50,180,100)

        # Shadow
        pygame.draw.rect(screen,(0,0,0,60),(play_r.x+3,play_r.y+4,200,56),border_radius=28)
        # Gradient button
        btn_s = make_alpha(200,56)
        for row in range(56):
            t=row/55
            r=int(brighter(pc,20)[0]*(1-t)+dimmer(pc,10)[0]*t)
            g=int(brighter(pc,20)[1]*(1-t)+dimmer(pc,10)[1]*t)
            b_c=int(brighter(pc,20)[2]*(1-t)+dimmer(pc,10)[2]*t)
            pygame.draw.line(btn_s,(r,g,b_c,240),(0,row),(199,row))
        mask=make_alpha(200,56)
        pygame.draw.rect(mask,(255,255,255),(0,0,200,56),border_radius=28)
        btn_s.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(btn_s,play_r.topleft)

        # Shine
        sh=make_alpha(180,16)
        pygame.draw.rect(sh,(255,255,255,25),(0,0,180,16),border_radius=14)
        screen.blit(sh,(play_r.x+10,play_r.y+4))

        pygame.draw.rect(screen,brighter(pc,35),play_r,1,border_radius=28)

        pt=f24.render("P L A Y",True,(255,255,255))
        screen.blit(pt,(play_r.centerx-pt.get_width()//2, play_r.centery-pt.get_height()//2))

        # Level & coins
        li=f16.render(f"Level {self.lv}",True,(110,115,145))
        screen.blit(li,(SW//2-li.get_width()//2,595))

        screen.blit(COIN,(SW//2-35,625))
        ci=f16.render(str(self.coins),True,(255,215,0))
        screen.blit(ci,(SW//2-8,628))

        ft=f11.render("Tap PLAY to start",True,(40,44,60))
        screen.blit(ft,(SW//2-ft.get_width()//2,SH-30))

        return play_r

    # ── Main loop ──

    def run(self):
        running=True
        play_r=next_r=rep_r=None

        while running:
            dt=clock.tick(FPS)/1000.0
            mouse=pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: running=False
                if ev.type==pygame.KEYDOWN:
                    if ev.key==pygame.K_ESCAPE:
                        if self.st=="play": self.st="menu"
                        else: running=False
                    if ev.key==pygame.K_u and self.st=="play": self.do_undo()
                    if ev.key==pygame.K_r and self.st=="play": self.load(self.lv)

                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.st=="menu":
                        if play_r and play_r.collidepoint(mouse):
                            self.load(self.lv)

                    elif self.st=="play" and not self.pa:
                        btn_hit=False
                        if hasattr(self,'_btns'):
                            for r,name in self._btns:
                                if r.collidepoint(mouse):
                                    if name=="Undo": self.do_undo()
                                    elif name=="Restart": self.load(self.lv)
                                    elif name=="Back": self.st="menu"
                                    btn_hit=True; break

                        if not btn_hit:
                            ci=self.tube_at(*mouse)
                            if ci>=0:
                                if self.sel==-1:
                                    if self.tubes[ci]: self.sel=ci
                                elif self.sel==ci:
                                    self.sel=-1
                                else:
                                    if self.can_pour(self.sel,ci):
                                        s=self.sel; self.sel=-1
                                        self.start_pour(s,ci)
                                    elif self.tubes[ci]:
                                        self.sel=ci
                                    else:
                                        self.sel=-1

                    elif self.st=="win":
                        if next_r and next_r.collidepoint(mouse):
                            self.coins+=self.stars()*15
                            self.load(self.lv+1)
                        elif rep_r and rep_r.collidepoint(mouse):
                            self.load(self.lv)

            # Update
            self.upd_pour(dt)
            self.pts=[p for p in self.pts if p.update(dt)]

            if self.st=="win" and self.wt<4 and random.random()<0.12:
                cols=[(255,107,107),(78,205,196),(255,230,109),(162,155,254),(255,159,243)]
                self.pts.append(P(random.randint(20,SW-20),random.randint(-20,SH//3),
                    random.choice(cols),random.uniform(-2,2),random.uniform(-3,1),
                    random.uniform(4,8),shape=random.choice([0,1,2])))

            # Draw
            if self.st=="menu":
                play_r=self.draw_menu(dt)
            elif self.st=="play":
                self.draw_play(dt)
            elif self.st=="win":
                self.draw_play(dt)
                next_r,rep_r=self.draw_win(dt)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__=="__main__":
    Game().run()
