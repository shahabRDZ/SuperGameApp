"""
Water Sort Puzzle — Premium Quality
Matching commercial game reference: 3D bottles, dark theme, vibrant colors
"""

import pygame
import pygame.gfxdraw
import sys, random, copy, math, array, json, os

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)

SW, SH = 440, 820
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Water Sort Puzzle")
clock = pygame.time.Clock()
FPS = 60
LAYERS = 4

def A(w, h):
    """Create alpha surface."""
    return pygame.Surface((w, h), pygame.SRCALPHA)

# ═══════════════════════════════════════════════════════════
#  SOUNDS — Realistic water
# ═══════════════════════════════════════════════════════════

def _snd(freq, dur, vol=0.25, fadein=100, fadeout=True):
    sr=44100; n=int(sr*dur); b=array.array('h')
    for i in range(n):
        t=i/sr; v=math.sin(2*math.pi*freq*t)*vol
        env=min(1, i/fadein) * (max(0,1-i/n) if fadeout else 1)
        b.append(int(v*env*32767))
    return pygame.mixer.Sound(buffer=b)

def _water_snd(dur=0.35):
    sr=44100; n=int(sr*dur); b=array.array('h')
    rng=random.Random(7)
    prev=0
    for i in range(n):
        t=i/sr
        env=min(1,i/300)*max(0,1-i/n)
        # Filtered noise + resonance
        noise=rng.uniform(-1,1)
        # Low pass
        prev=prev*0.92+noise*0.08
        v=prev*0.5 + math.sin(2*math.pi*200*t+4*math.sin(2*math.pi*35*t))*0.3
        b.append(int(v*env*0.3*32767))
    return pygame.mixer.Sound(buffer=b)

def _splash():
    sr=44100; dur=0.15; n=int(sr*dur); b=array.array('h')
    rng=random.Random(13)
    prev=0
    for i in range(n):
        env=min(1,i/80)*max(0,1-i/n)**2
        noise=rng.uniform(-1,1)
        prev=prev*0.85+noise*0.15
        b.append(int(prev*env*0.35*32767))
    return pygame.mixer.Sound(buffer=b)

def _chime(notes, each=0.11):
    sr=44100; b=array.array('h')
    for note in notes:
        n=int(sr*each)
        for i in range(n):
            t=i/sr; env=min(1,i/60)*max(0,1-i/n*0.6)
            v=(math.sin(2*math.pi*note*t)*0.3+math.sin(2*math.pi*note*2*t)*0.08)
            b.append(int(v*env*32767))
    return pygame.mixer.Sound(buffer=b)

SND_TAP=_snd(900,0.04,0.12)
SND_POUR=_water_snd(0.5)
SND_SPLASH=_splash()
SND_COMPLETE=_chime([523,659,784])
SND_WIN=_chime([523,587,659,784,1047],0.09)
SND_UNDO=_snd(350,0.06,0.1)
SND_ERROR=_snd(200,0.1,0.08)

# ═══════════════════════════════════════════════════════════
#  COLORS — Bright vivid (matching reference screenshot)
# ═══════════════════════════════════════════════════════════

WATER = {
    1: (82, 230, 85),      # Bright Green
    2: (255, 105, 180),    # Hot Pink
    3: (120, 80, 190),     # Purple
    4: (255, 200, 40),     # Golden Yellow
    5: (50, 120, 230),     # Royal Blue
    6: (255, 70, 50),      # Red
    7: (255, 155, 50),     # Orange
    8: (60, 210, 230),     # Cyan
    9: (230, 130, 200),    # Light Pink
    10:(180, 140, 100),    # Brown
    11:(170, 255, 120),    # Lime
    12:(255, 245, 140),    # Pale Yellow
}

def brighter(c, n=40): return tuple(min(255, x+n) for x in c)
def dimmer(c, n=35): return tuple(max(0, x-n) for x in c)
def lerpc(a, b, t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

# ═══════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════

def MF(sz, bold=False):
    for n in ["Avenir Next","SF Pro Rounded","Helvetica Neue","Arial Rounded MT Bold","Arial"]:
        try: return pygame.font.SysFont(n, sz, bold)
        except: pass
    return pygame.font.SysFont(None, sz, bold)

f44=MF(44,True); f28=MF(28,True); f22=MF(22,True); f18=MF(18,True)
f15=MF(15,True); f13=MF(13); f11=MF(11,True); f10=MF(10); f9=MF(9,True)

# ═══════════════════════════════════════════════════════════
#  BACKGROUND — Dark space/galaxy
# ═══════════════════════════════════════════════════════════

def make_bg():
    s = pygame.Surface((SW, SH))
    # Deep blue-purple gradient
    for y in range(SH):
        t = y / SH
        r = int(10*(1-t) + 5*t)
        g = int(12*(1-t) + 8*t)
        b = int(45*(1-t) + 25*t)
        pygame.draw.line(s, (r, g, b), (0, y), (SW, y))

    # Stars
    rng = random.Random(42)
    for _ in range(80):
        x = rng.randint(0, SW)
        y = rng.randint(0, SH)
        brightness = rng.randint(40, 120)
        sz = rng.choice([1, 1, 1, 2])
        pygame.draw.circle(s, (brightness, brightness, brightness+30), (x, y), sz)

    # Subtle nebula glow
    glow = A(SW, SH)
    pygame.draw.circle(glow, (30, 20, 80, 20), (SW//2, SH//3), 250)
    pygame.draw.circle(glow, (20, 10, 60, 15), (SW//4, SH*2//3), 180)
    s.blit(glow, (0, 0))

    return s

BG = make_bg()

# ═══════════════════════════════════════════════════════════
#  TUBE GEOMETRY — Tall bottle with cap
# ═══════════════════════════════════════════════════════════

TW = 46          # bottle outer width
TH = 165         # bottle body height
NECK_W = 30      # neck width
NECK_H = 18      # neck height
CAP_W = 26       # cap width
CAP_H = 10       # cap height
WALL = 3
BOT_R = 16       # bottom curve radius
IW = TW - WALL*2 # inner width
LH = (TH - BOT_R - WALL) // LAYERS  # layer height

TOTAL_TUBE_H = CAP_H + NECK_H + TH  # total including cap+neck

# ═══════════════════════════════════════════════════════════
#  BOTTLE RENDERER — 3D metallic/glass look
# ═══════════════════════════════════════════════════════════

def render_bottle(selected=False, complete=False):
    """Render a 3D bottle with cap, neck, and body."""
    pad = 20
    w = TW + pad*2
    h = TOTAL_TUBE_H + pad*2
    surf = A(w, h)

    ox = pad  # body x offset
    cap_x = pad + (TW - CAP_W)//2
    neck_x = pad + (TW - NECK_W)//2

    # Y positions
    cap_y = pad
    neck_y = cap_y + CAP_H
    body_y = neck_y + NECK_H

    # Colors based on state
    if selected:
        body_c = (40, 100, 200)
        glow_c = (60, 140, 255, 50)
        border_c = (80, 160, 255)
        cap_c = (50, 120, 230)
    elif complete:
        body_c = (30, 80, 180)
        glow_c = (50, 200, 120, 40)
        border_c = (60, 180, 140)
        cap_c = (40, 160, 120)
    else:
        body_c = (25, 35, 80)
        glow_c = None
        border_c = (50, 70, 140)
        cap_c = (35, 50, 110)

    # ── Glow ──
    if glow_c:
        for r in range(25, 0, -2):
            a = glow_c[3] * (1 - r/25)
            rect = (ox-r, body_y-r, TW+r*2, TH+r*2)
            pygame.draw.rect(surf, (*glow_c[:3], int(a)), rect, border_radius=BOT_R+r)

    # ── Body ──
    body = A(TW, TH)

    # 3D cylindrical gradient across width
    for col in range(TW):
        t = (col - TW/2) / (TW/2)  # -1 to 1
        # Cylindrical lighting: bright on left-center, dark at edges
        brightness = 0.35 + 0.65 * math.exp(-((t+0.25)**2)/0.12)
        r = max(0, min(255, int(body_c[0] * brightness * 1.8)))
        g = max(0, min(255, int(body_c[1] * brightness * 1.8)))
        b = max(0, min(255, int(body_c[2] * brightness * 1.8)))

        # Draw column (body minus bottom curve area)
        for row in range(TH - BOT_R):
            body.set_at((col, row), (r, g, b, 220))

        # Bottom curve: only draw if within the ellipse
        for row in range(BOT_R):
            ey = row / max(1, BOT_R)
            ex = abs(t)
            if ex*ex + (1-ey)*(1-ey) <= 1.05:
                # Darken slightly toward bottom
                dr = max(0, int(r * (1 - ey*0.3)))
                dg = max(0, int(g * (1 - ey*0.3)))
                db = max(0, int(b * (1 - ey*0.3)))
                body.set_at((col, TH - BOT_R + row), (dr, dg, db, 220))

    # Main highlight streak (left side)
    for row in range(8, TH - BOT_R - 8):
        t = (row-8) / max(1, TH-BOT_R-16)
        inten = int(70 * math.exp(-((t-0.15)**2)/0.01) + 30 * math.exp(-((t-0.5)**2)/0.08))
        if inten > 3:
            for dx in range(6):
                a = int(inten * max(0, 1 - dx/5))
                if a > 0 and WALL+2+dx < TW:
                    px = body.get_at((WALL+2+dx, row))
                    nr = min(255, px[0]+a)
                    ng = min(255, px[1]+a)
                    nb = min(255, px[2]+a)
                    body.set_at((WALL+2+dx, row), (nr, ng, nb, px[3]))

    # Right subtle highlight
    for row in range(15, TH - BOT_R - 15):
        t = (row-15) / max(1, TH-BOT_R-30)
        inten = int(20 * math.exp(-((t-0.3)**2)/0.04))
        if inten > 2 and TW-WALL-5 >= 0:
            px = body.get_at((TW-WALL-5, row))
            body.set_at((TW-WALL-5, row), (min(255,px[0]+inten),min(255,px[1]+inten),min(255,px[2]+inten),px[3]))

    surf.blit(body, (ox, body_y))

    # ── Border outline ──
    # Left & right walls
    pygame.draw.line(surf, (*border_c, 180), (ox, body_y), (ox, body_y+TH-BOT_R), 2)
    pygame.draw.line(surf, (*border_c, 140), (ox+TW-1, body_y), (ox+TW-1, body_y+TH-BOT_R), 2)
    # Bottom arc
    pygame.draw.arc(surf, (*border_c, 160),
                   (ox, body_y+TH-BOT_R*2, TW, BOT_R*2), math.pi, 2*math.pi, 2)

    # ── Neck ──
    neck = A(NECK_W, NECK_H)
    for col in range(NECK_W):
        t = (col - NECK_W/2) / (NECK_W/2)
        brightness = 0.4 + 0.6 * math.exp(-((t+0.2)**2)/0.15)
        r = max(0,min(255,int(body_c[0]*brightness*1.5)))
        g = max(0,min(255,int(body_c[1]*brightness*1.5)))
        b = max(0,min(255,int(body_c[2]*brightness*1.5)))
        for row in range(NECK_H):
            neck.set_at((col, row), (r, g, b, 210))
    surf.blit(neck, (neck_x, neck_y))

    # Neck borders
    pygame.draw.line(surf, (*border_c, 140), (neck_x, neck_y), (neck_x, neck_y+NECK_H), 1)
    pygame.draw.line(surf, (*border_c, 120), (neck_x+NECK_W-1, neck_y), (neck_x+NECK_W-1, neck_y+NECK_H), 1)

    # Shoulder connections (neck to body)
    pygame.draw.line(surf, (*border_c, 100), (neck_x, neck_y+NECK_H), (ox, body_y), 1)
    pygame.draw.line(surf, (*border_c, 100), (neck_x+NECK_W, neck_y+NECK_H), (ox+TW, body_y), 1)

    # ── Cap ──
    cap = A(CAP_W, CAP_H)
    for col in range(CAP_W):
        t = (col - CAP_W/2) / (CAP_W/2)
        brightness = 0.5 + 0.5 * math.exp(-(t**2)/0.2)
        r = max(0,min(255,int(cap_c[0]*brightness*2)))
        g = max(0,min(255,int(cap_c[1]*brightness*2)))
        b = max(0,min(255,int(cap_c[2]*brightness*2)))
        for row in range(CAP_H):
            cap.set_at((col, row), (r, g, b, 230))
    pygame.draw.rect(cap, (*brighter(cap_c,40), 140), (0,0,CAP_W,CAP_H), 1, border_radius=3)
    surf.blit(cap, (cap_x, cap_y))

    return surf, (pad, pad + CAP_H + NECK_H)  # Return body offset

# Pre-render
BOTTLE_NORMAL, BODY_OFF_N = render_bottle(False, False)
BOTTLE_SELECTED, BODY_OFF_S = render_bottle(True, False)
BOTTLE_COMPLETE, BODY_OFF_C = render_bottle(False, True)
B_PAD = 20  # padding used in render

def draw_liquid(surf, bx, by, tube_data):
    """Draw flat vibrant liquid blocks inside bottle body area."""
    if not tube_data:
        return

    lx = bx + WALL + 1
    lw = IW - 2
    bottom = by + TH - WALL

    for i, cid in enumerate(tube_data):
        if cid <= 0: continue
        color = WATER.get(cid, (150,150,150))
        light = brighter(color, 50)
        dark = dimmer(color, 25)

        ly = bottom - (i+1)*LH
        lh = LH

        # ── Flat color fill with subtle top-to-bottom gradient ──
        layer = A(lw, lh + (BOT_R if i==0 else 0))

        for row in range(lh):
            t = row / max(1, lh-1)
            # Very subtle gradient: slightly light at top, base, slightly dark at bottom
            if t < 0.1:
                c = lerpc(light, color, t/0.1)
            elif t > 0.9:
                c = lerpc(color, dark, (t-0.9)/0.1)
            else:
                c = color
            pygame.draw.line(layer, (*c, 240), (0, row), (lw, row))

        # Bottom layer fills curve
        if i == 0:
            for row in range(BOT_R):
                t = row / max(1, BOT_R-1)
                dy = BOT_R - row
                half_w = math.sqrt(max(0, BOT_R**2 - dy**2)) * lw / (2*BOT_R)
                cx = lw // 2
                x1 = max(0, int(cx - half_w))
                x2 = min(lw, int(cx + half_w))
                c = lerpc(color, dark, t*0.4)
                pygame.draw.line(layer, (*c, 240), (x1, lh+row), (x2, lh+row))

        surf.blit(layer, (lx, ly))

        # ── Shine strip (left) ──
        sh = A(5, lh-2)
        for row in range(lh-2):
            t = row/max(1,lh-3)
            a = int(50 * math.sin(t*math.pi))
            if a > 3:
                pygame.draw.line(sh, (255,255,255,a), (0,row), (3,row))
        surf.blit(sh, (lx+3, ly+1))

        # ── Right edge dark ──
        rd = A(4, lh-2)
        for row in range(lh-2):
            t = row/max(1,lh-3)
            a = int(25 * math.sin(t*math.pi))
            if a > 2:
                pygame.draw.line(rd, (0,0,0,a), (0,row), (2,row))
        surf.blit(rd, (lx+lw-5, ly+1))

        # ── Thin border between different colors ──
        if i > 0 and tube_data[i] != tube_data[i-1]:
            border_y = bottom - i*LH
            pygame.draw.line(surf, (*dimmer(color,50), 80), (lx, border_y), (lx+lw, border_y), 1)

    # ── Top meniscus ──
    top_i = len(tube_data) - 1
    if top_i >= 0:
        top_c = WATER.get(tube_data[top_i], (150,150,150))
        top_y = bottom - (top_i+1)*LH
        men = A(lw, 4)
        for col in range(lw):
            t = (col-lw/2)/(lw/2)
            h_ = int(2*(1-t*t))
            a = int(80*(1-abs(t)*0.4))
            mc = brighter(top_c, 60)
            for row in range(h_):
                if row < 4:
                    men.set_at((col, row), (*mc, max(0,a-row*20)))
        surf.blit(men, (lx, top_y))


# ═══════════════════════════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════════════════════════

class Pt:
    __slots__=['x','y','vx','vy','life','sz','c','gv','sh','dc']
    def __init__(s,x,y,c,vx=None,vy=None,sz=None,gv=True,sh=0):
        s.x=x;s.y=y;s.c=c;s.sh=sh
        s.vx=vx if vx is not None else random.uniform(-3,3)
        s.vy=vy if vy is not None else random.uniform(-6,-2)
        s.sz=sz or random.uniform(3,7)
        s.life=1.0;s.gv=gv;s.dc=random.uniform(0.7,1.4)
    def upd(s,dt):
        s.x+=s.vx*60*dt;s.y+=s.vy*60*dt
        if s.gv:s.vy+=10*dt
        s.life-=dt/s.dc;return s.life>0
    def draw(s,sf):
        a=max(0,min(255,int(s.life*255)))
        sz=max(1,int(s.sz*max(0.2,s.life)))
        if a<5 or sz<1:return
        t=A(sz*2+2,sz*2+2)
        if s.sh==0:
            pygame.draw.circle(t,(*s.c,a),(sz+1,sz+1),sz)
        elif s.sh==1:
            w=max(1,int(sz*abs(math.sin(s.life*10))));h=max(1,int(sz*0.5))
            pygame.draw.rect(t,(*s.c,a),(sz+1-w//2,sz+1-h//2,w,h),border_radius=1)
        elif s.sh==2:
            cx,cy=sz+1,sz+1
            pts=[(cx+(sz if i%2==0 else sz*0.4)*math.cos(math.radians(i*36-90+s.life*200)),
                  cy+(sz if i%2==0 else sz*0.4)*math.sin(math.radians(i*36-90+s.life*200))) for i in range(10)]
            pygame.draw.polygon(t,(*s.c,a),pts)
        elif s.sh==3: # sparkle
            cx,cy=sz+1,sz+1
            for ang in range(0,360,90):
                rad=math.radians(ang+s.life*150)
                pygame.draw.line(t,(*s.c,a),(cx,cy),(cx+int(sz*math.cos(rad)),cy+int(sz*math.sin(rad))),1)
        sf.blit(t,(int(s.x)-sz-1,int(s.y)-sz-1))

# ═══════════════════════════════════════════════════════════
#  LEVEL GEN + HINT SOLVER
# ═══════════════════════════════════════════════════════════

def get_diff(lv):
    if lv<=3:return 3,2
    if lv<=8:return 4,2
    if lv<=15:return 5,2
    if lv<=25:return 6,2
    if lv<=40:return 7,2
    if lv<=60:return 8,2
    return 9,2

def gen_level(lv):
    rng=random.Random(lv*31337+97)
    nc,ne=get_diff(lv)
    pool=[]
    for c in range(1,nc+1):pool.extend([c]*LAYERS)
    for _ in range(300):
        rng.shuffle(pool)
        tubes=[pool[i*LAYERS:(i+1)*LAYERS] for i in range(nc)]
        if not any(len(set(t))==1 for t in tubes):break
    for _ in range(ne):tubes.append([])
    return [list(t) for t in tubes]

def is_done(t):return len(t)==LAYERS and len(set(t))==1
def all_done(ts):return all((not t) or is_done(t) for t in ts)

def find_hint(tubes):
    def key(ts):return tuple(tuple(t) for t in ts)
    def moves(ts):
        mv=[]
        for f in range(len(ts)):
            if not ts[f]:continue
            top=ts[f][-1]
            cnt=sum(1 for k in range(len(ts[f])-1,-1,-1) if ts[f][k]==top)
            for d in range(len(ts)):
                if f==d:continue
                if len(ts[d])>=LAYERS:continue
                if not ts[d]:
                    if len(set(ts[f]))==1:continue
                    mv.append((f,d))
                elif ts[d][-1]==top and len(ts[d])+cnt<=LAYERS:
                    mv.append((f,d))
        return mv
    def do(ts,f,d):
        ns=[list(t) for t in ts]
        top=ns[f][-1]
        while ns[f] and ns[f][-1]==top and len(ns[d])<LAYERS:
            ns[d].append(ns[f].pop())
        return ns
    vis={key(tubes)};q=[(tubes,[])]
    for _ in range(12000):
        if not q:break
        cur,path=q.pop(0)
        for m in moves(cur):
            ns=do(cur,m[0],m[1]);k=key(ns)
            if k in vis:continue
            vis.add(k);np=path+[m]
            if all_done(ns):return np[0]
            q.append((ns,np))
    mv=moves(tubes)
    return mv[0] if mv else None

# ═══════════════════════════════════════════════════════════
#  SAVE SYSTEM
# ═══════════════════════════════════════════════════════════

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")

def save_progress(data):
    try:
        with open(SAVE_PATH, 'w') as f:
            json.dump(data, f)
    except:
        pass

def load_progress():
    try:
        with open(SAVE_PATH) as f:
            return json.load(f)
    except:
        return {"level": 1, "coins": 100, "hints": 5, "undos": 5, "adds": 3,
                "stars": {}, "best_level": 1}

# ═══════════════════════════════════════════════════════════
#  ASSETS
# ═══════════════════════════════════════════════════════════

def make_star_img(c1,c2,size=34):
    s=A(size,size);cx,cy=size//2,size//2
    ro,ri=size//2-2,size//5
    pts=[(cx+(ro if i%2==0 else ri)*math.cos(math.radians(i*36-90)),
          cy+(ro if i%2==0 else ri)*math.sin(math.radians(i*36-90))) for i in range(10)]
    pygame.draw.polygon(s,c1,pts)
    pts2=[(cx+((ro-3) if i%2==0 else max(1,ri-1))*math.cos(math.radians(i*36-90)),
           cy+((ro-3) if i%2==0 else max(1,ri-1))*math.sin(math.radians(i*36-90))) for i in range(10)]
    pygame.draw.polygon(s,c2,pts2)
    return s

STAR_ON=make_star_img((245,195,20),(255,230,80))
STAR_OFF=make_star_img((40,45,70),(55,60,85))

def make_coin():
    s=A(24,24)
    pygame.draw.circle(s,(255,193,7),(12,12),11)
    pygame.draw.circle(s,(255,225,60),(12,11),9)
    t=f10.render("$",True,(190,140,0))
    s.blit(t,(12-t.get_width()//2,12-t.get_height()//2))
    pygame.draw.circle(s,(210,165,0),(12,12),11,2)
    return s

COIN_IMG=make_coin()

# ═══════════════════════════════════════════════════════════
#  CIRCULAR ICON BUTTONS (like reference)
# ═══════════════════════════════════════════════════════════

def draw_circle_btn(surf, cx, cy, radius, icon_fn, count, color, hover=False, glow_c=None):
    """Draw circular button with icon and count badge."""
    # Glow ring
    if glow_c:
        for r in range(radius+8, radius, -1):
            a = int(60 * (1 - (r-radius)/8))
            pygame.draw.circle(surf, (*glow_c, a), (cx, cy), r)

    # Outer ring
    ring_c = brighter(color, 30) if hover else color
    pygame.draw.circle(surf, (*ring_c, 220), (cx, cy), radius, 3)

    # Inner fill
    inner = A(radius*2, radius*2)
    pygame.draw.circle(inner, (*dimmer(color, 30), 160), (radius, radius), radius-3)
    surf.blit(inner, (cx-radius, cy-radius))

    # Icon
    icon_fn(surf, cx, cy)

    # Count badge (bottom)
    if count is not None:
        badge_w = max(18, len(str(count))*8+10)
        badge_x = cx - badge_w//2
        badge_y = cy + radius + 2
        badge = A(badge_w, 16)
        pygame.draw.rect(badge, (*color, 200), (0,0,badge_w,16), border_radius=8)
        t = f9.render(str(count), True, (255,255,255))
        badge.blit(t, (badge_w//2-t.get_width()//2, 8-t.get_height()//2))
        surf.blit(badge, (badge_x, badge_y))

def icon_undo(surf, cx, cy):
    color = (255, 255, 255)
    # Curved arrow
    pygame.draw.arc(surf, color, (cx-8, cy-8, 16, 16), math.radians(30), math.radians(300), 2)
    # Arrow head
    ax = cx + int(8*math.cos(math.radians(30)))
    ay = cy - int(8*math.sin(math.radians(30)))
    pygame.draw.polygon(surf, color, [(ax-1,ay-4),(ax+5,ay+1),(ax-1,ay+2)])

def icon_hint(surf, cx, cy):
    color = (255, 255, 255)
    # Lightning bolt / wand
    pts = [(cx-2,cy-10),(cx+4,cy-2),(cx,cy-2),(cx+2,cy+10),(cx-4,cy+2),(cx,cy+2)]
    pygame.draw.polygon(surf, color, pts)

def icon_add(surf, cx, cy):
    color = (255, 255, 255)
    # +0 (add tube)
    pygame.draw.line(surf, color, (cx-7, cy), (cx+7, cy), 2)
    pygame.draw.line(surf, color, (cx, cy-7), (cx, cy+7), 2)
    # Small "0" or tube shape
    pygame.draw.rect(surf, color, (cx+4, cy-4, 5, 8), 1, border_radius=2)

# ═══════════════════════════════════════════════════════════
#  GAME
# ═══════════════════════════════════════════════════════════

class Game:
    def __init__(self):
        self.save = load_progress()
        self.state = "menu"
        self.lv = self.save.get("level", 1)
        self.coins = self.save.get("coins", 100)
        self.mv = 0
        self.sel = -1
        self.tubes = []
        self.undo_stack = []
        self.pos = []
        self.pts = []
        self.wt = 0
        self.mt = 0
        self.hint_move = None
        self.hint_blink = 0
        self.completed_tubes = set()
        self.extra_tubes = 0

        # Counts (like reference)
        self.undo_count = self.save.get("undos", 5)
        self.hint_count = self.save.get("hints", 5)
        self.add_count = self.save.get("adds", 3)

        # Pour anim
        self.pa=False; self.ps=self.pd=-1; self.pp=0; self.pt_=0
        self.po=[0.0,0.0]; self.tilt=0.0; self.poured=False
        self.stream_pts=[]

        # Selection bounce
        self.sel_bounce = {}  # tube_idx -> bounce_t

        # Liquid fill animation
        self.fill_anim = {}  # tube_idx -> (target_layers, current_visual_h, color)

    def _save(self):
        self.save["level"] = self.lv
        self.save["coins"] = self.coins
        self.save["undos"] = self.undo_count
        self.save["hints"] = self.hint_count
        self.save["adds"] = self.add_count
        save_progress(self.save)

    def load(self, n):
        self.lv=n; self.tubes=gen_level(n); self.mv=0; self.sel=-1
        self.undo_stack=[]; self.pts=[]; self.state="play"
        self.pa=False; self.wt=0; self.hint_move=None; self.hint_blink=0
        self.completed_tubes=set(); self.extra_tubes=0
        self.sel_bounce={}; self.fill_anim={}; self.stream_pts=[]
        self._layout()

    def _layout(self):
        self.pos=[]
        n=len(self.tubes)
        per=min(n,5)
        rows=math.ceil(n/per)
        sp=TW+18
        # Center vertically in play area (below bar, above buttons)
        play_top = 115
        play_bottom = SH - 110
        play_h = play_bottom - play_top
        total_h = rows * (TOTAL_TUBE_H + 20) - 20
        start_y = play_top + max(0, (play_h - total_h)//2)

        for i in range(n):
            r=i//per; c=i%per
            nr=min(per, n-r*per)
            tw=nr*sp-18
            sx=(SW-tw)//2
            x=sx+c*sp
            y=start_y+r*(TOTAL_TUBE_H+20)
            self.pos.append((x,y))

    def tube_at(self,mx,my):
        for i,(x,y) in enumerate(self.pos):
            if pygame.Rect(x-8,y,TW+16,TOTAL_TUBE_H+10).collidepoint(mx,my):
                return i
        return -1

    def can_pour(self,s,d):
        a,b=self.tubes[s],self.tubes[d]
        if not a:return False
        if len(b)>=LAYERS:return False
        if not b:return True
        return a[-1]==b[-1]

    def do_pour(self,s,d):
        a,b=self.tubes[s],self.tubes[d]
        self.undo_stack.append(copy.deepcopy(self.tubes))
        top=a[-1]; cnt=0
        while a and a[-1]==top and len(b)<LAYERS:
            b.append(a.pop()); cnt+=1
        self.mv+=1; SND_SPLASH.play()
        if is_done(b) and d not in self.completed_tubes:
            self.completed_tubes.add(d)
            self._tube_fx(d); SND_COMPLETE.play()
        self.hint_move=None; return cnt

    def do_undo(self):
        if not self.undo_stack or self.pa:return
        if self.undo_count <= 0:SND_ERROR.play();return
        self.tubes=self.undo_stack.pop()
        self.mv=max(0,self.mv-1);self.sel=-1;self.hint_move=None
        self.completed_tubes={i for i,t in enumerate(self.tubes) if t and is_done(t)}
        self.undo_count-=1;SND_UNDO.play()

    def add_tube(self):
        if self.add_count<=0:SND_ERROR.play();return
        self.tubes.append([]);self.add_count-=1
        self.extra_tubes+=1;self._layout();SND_TAP.play()

    def get_hint(self):
        if self.hint_count<=0:SND_ERROR.play();return
        h=find_hint(self.tubes)
        if h:
            self.hint_move=h;self.hint_blink=0
            self.hint_count-=1;SND_TAP.play()

    def _tube_fx(self,idx):
        x,y=self.pos[idx]
        cx=x+TW//2;cy=y+TOTAL_TUBE_H//2
        c=WATER.get(self.tubes[idx][0],(200,200,200))
        for _ in range(30):
            self.pts.append(Pt(cx+random.randint(-15,15),cy+random.randint(-40,20),
                brighter(c,40),random.uniform(-3,3),random.uniform(-6,-1),
                random.uniform(3,7),sh=random.choice([0,2,3])))

    def stars(self):
        c,_=get_diff(self.lv);opt=c*2
        if self.mv<=opt:return 3
        if self.mv<=opt*2:return 2
        return 1

    # ── Pour animation with tilt ──
    def start_pour(self,s,d):
        self.pa=True;self.ps=s;self.pd=d;self.pp=0;self.pt_=0
        self.po=[0,0];self.tilt=0;self.poured=False;self.stream_pts=[]
        SND_POUR.play()

    def upd_pour(self,dt):
        if not self.pa:return
        self.pt_+=dt*3.8
        t=min(1,self.pt_);t=t*t*(3-2*t)
        sx,sy=self.pos[self.ps];dx,dy=self.pos[self.pd]
        dr=1 if dx>sx else -1
        if self.pp==0:
            self.po=[0,-55*t];self.tilt=0
            if self.pt_>=1:self.pp=1;self.pt_=0
        elif self.pp==1:
            tx=(dx-sx)+dr*22
            self.po=[tx*t,-55];self.tilt=0
            if self.pt_>=1:self.pp=2;self.pt_=0
        elif self.pp==2:
            tx=(dx-sx)+dr*22
            self.po=[tx,-55];self.tilt=-dr*50*t
            if not self.poured and self.pt_>=0.35:
                self.do_pour(self.ps,self.pd);self.poured=True
            # Stream
            if 0.15<self.pt_<0.85:
                px=dx+TW//2;py=dy+CAP_H+NECK_H
                if self.tubes[self.pd]:
                    c=WATER.get(self.tubes[self.pd][-1],(200,200,200))
                    for _ in range(3):
                        self.stream_pts.append(Pt(px+random.randint(-5,5),
                            py+random.randint(-8,8),brighter(c,20),
                            random.uniform(-0.8,0.8),random.uniform(1,5),
                            random.uniform(2,4)))
            if self.pt_>=1:self.pp=3;self.pt_=0
        elif self.pp==3:
            tx=(dx-sx)+dr*22
            self.po=[tx*(1-t),-55*(1-t)];self.tilt=-dr*50*(1-t)
            if self.pt_>=1:
                self.pa=False;self.po=[0,0];self.tilt=0
                if all_done(self.tubes):
                    self.state="win";self.wt=0;self._win_fx();SND_WIN.play()
                    reward=self.stars()*15;self.coins+=reward
                    self.save["stars"][str(self.lv)]=self.stars()
                    if self.lv>=self.save.get("best_level",1):
                        self.save["best_level"]=self.lv+1
                    self._save()
        self.stream_pts=[p for p in self.stream_pts if p.upd(dt)]

    def _win_fx(self):
        cols=[(255,107,107),(78,205,196),(255,230,109),(162,155,254),
              (255,159,243),(110,200,230),(255,177,66),(150,220,180)]
        for _ in range(140):
            self.pts.append(Pt(random.randint(10,SW-10),random.randint(-50,SH//2),
                random.choice(cols),random.uniform(-5,5),random.uniform(-9,0),
                random.uniform(4,12),sh=random.choice([0,1,2,3])))

    # ── Drawing ──

    def draw_bar(self):
        # Level badge (like reference)
        # Dark pill with level number
        badge_w = 140
        badge_x = (SW-badge_w)//2
        badge_y = 22

        badge = A(badge_w, 36)
        pygame.draw.rect(badge, (20,25,55,220), (0,0,badge_w,36), border_radius=18)
        pygame.draw.rect(badge, (50,70,140,150), (0,0,badge_w,36), 2, border_radius=18)
        # Eye icon placeholder
        pygame.draw.circle(badge, (150,160,200), (20, 18), 6, 1)
        pygame.draw.circle(badge, (150,160,200), (20, 18), 2)
        # Level text
        lt = f18.render(f"Level {self.lv}", True, (220,225,245))
        badge.blit(lt, (36, 18-lt.get_height()//2))
        screen.blit(badge, (badge_x, badge_y))

        # Difficulty label below
        c,_ = get_diff(self.lv)
        dn={3:"EASY",4:"NORMAL",5:"MEDIUM",6:"HARD",7:"EXPERT",8:"MASTER",9:"INSANE"}
        dc={3:(80,200,120),4:(80,170,230),5:(230,200,60),6:(240,140,50),
            7:(230,80,80),8:(200,80,180),9:(200,50,50)}
        dname = dn.get(c,"")
        dcolor = dc.get(c,(150,150,150))

        diff_w = max(50, len(dname)*9+16)
        diff_x = (SW-diff_w)//2
        diff = A(diff_w, 20)
        pygame.draw.rect(diff, (*dcolor, 200), (0,0,diff_w,20), border_radius=10)
        dt = f9.render(dname, True, (255,255,255))
        diff.blit(dt, (diff_w//2-dt.get_width()//2, 10-dt.get_height()//2))
        screen.blit(diff, (diff_x, badge_y+40))

        # Coins (top right)
        screen.blit(COIN_IMG, (SW-85, 15))
        ct = f18.render(str(self.coins), True, (255,220,50))
        screen.blit(ct, (SW-58, 16))

        # Moves (top left)
        mt = f13.render(f"Moves: {self.mv}", True, (130,140,180))
        screen.blit(mt, (15, 20))

    def draw_tubes(self,dt):
        for i,tube in enumerate(self.tubes):
            tx,ty = self.pos[i]
            ox,oy = 0.0,0.0
            tilt = 0.0

            if self.pa and self.ps==i:
                ox,oy=self.po[0],self.po[1]
                tilt=self.tilt
            elif i==self.sel and not self.pa:
                # Smooth bounce
                if i not in self.sel_bounce:
                    self.sel_bounce[i]=0
                self.sel_bounce[i]+=dt*8
                bounce=math.sin(min(math.pi,self.sel_bounce[i]))*16
                oy=-bounce

            is_hint=(self.hint_move and (i==self.hint_move[0] or i==self.hint_move[1]))
            done=is_done(tube) if tube else False
            sel=(i==self.sel and not self.pa)

            if sel:bottle=BOTTLE_SELECTED;boff=BODY_OFF_S
            elif done:bottle=BOTTLE_COMPLETE;boff=BODY_OFF_C
            else:bottle=BOTTLE_NORMAL;boff=BODY_OFF_N

            # Hint glow
            if is_hint and not sel:
                pulse=abs(math.sin(self.hint_blink*4))
                glow=A(TW+30,TOTAL_TUBE_H+30)
                a=int(50*pulse)
                pygame.draw.rect(glow,(255,220,80,a),(0,0,TW+30,TOTAL_TUBE_H+30),border_radius=20)
                screen.blit(glow,(int(tx+ox)-15,int(ty+oy)-15))

            bx = int(tx+ox) - B_PAD
            by = int(ty+oy) - B_PAD
            body_x = int(tx+ox)
            body_y = int(ty+oy) + CAP_H + NECK_H

            if abs(tilt)>0.5:
                # Render tilted
                temp=A(TW+B_PAD*2,TOTAL_TUBE_H+B_PAD*2)
                temp.blit(bottle,(0,0))
                # Draw liquid in body area of temp
                draw_liquid(temp,B_PAD,B_PAD+CAP_H+NECK_H,tube)
                rotated=pygame.transform.rotate(temp,tilt)
                rw,rh=rotated.get_size()
                screen.blit(rotated,(bx+(TW+B_PAD*2-rw)//2,by+(TOTAL_TUBE_H+B_PAD*2-rh)//2))
            else:
                screen.blit(bottle,(bx,by))
                draw_liquid(screen,body_x,body_y,tube)

                # Complete badge
                if done:
                    bcx=body_x+TW//2;bcy=int(ty+oy)-2
                    pygame.draw.circle(screen,(76,175,80),(bcx,bcy),10)
                    pygame.draw.circle(screen,(110,210,130),(bcx,bcy),8)
                    pygame.draw.lines(screen,(255,255,255),False,
                        [(bcx-4,bcy+1),(bcx-1,bcy+4),(bcx+5,bcy-3)],2)

        # Clean up bounce for deselected
        for k in list(self.sel_bounce):
            if k != self.sel:
                del self.sel_bounce[k]

    def draw_bottom_btns(self):
        mouse=pygame.mouse.get_pos()
        btn_r=25;gap=24
        btns=[
            (icon_undo, self.undo_count, (180,120,40), "undo", (220,170,50)),
            (icon_hint, self.hint_count, (140,60,180), "hint", (180,100,220)),
            (icon_add, self.add_count, (50,100,200), "add", (80,140,240)),
        ]
        total_w = len(btns)*(btn_r*2+gap)-gap
        sx = (SW-total_w)//2 + btn_r
        by = SH - 55

        self._btns=[]
        for idx,(icon_fn,count,color,name,glow_c) in enumerate(btns):
            cx=sx+idx*(btn_r*2+gap)
            rect=pygame.Rect(cx-btn_r-5,by-btn_r-5,btn_r*2+10,btn_r*2+25)
            hov=rect.collidepoint(mouse)
            draw_circle_btn(screen,cx,by,btn_r,icon_fn,count,color,hov,
                           glow_c if hov else None)
            self._btns.append((rect,name))

    def draw_play(self,dt):
        screen.blit(BG,(0,0))
        self.draw_bar()
        self.draw_tubes(dt)

        for p in self.stream_pts:p.draw(screen)
        for p in self.pts:p.draw(screen)

        self.draw_bottom_btns()

        # Keyboard hints
        h=f10.render("U=Undo  H=Hint  R=Restart  ESC=Menu",True,(30,35,60))
        screen.blit(h,(SW//2-h.get_width()//2,SH-18))

    def draw_win(self,dt):
        self.wt+=dt
        ov=A(SW,SH);a=min(170,int(self.wt*500));ov.fill((0,0,0,a))
        screen.blit(ov,(0,0))
        if self.wt<0.2:return None,None

        pw,ph=360,370;px=(SW-pw)//2;py=(SH-ph)//2-20

        # Shadow
        sh=A(pw+8,ph+8);pygame.draw.rect(sh,(0,0,0,70),(4,6,pw,ph),border_radius=24)
        screen.blit(sh,(px-4,py-3))

        # Panel (dark matching theme)
        panel=A(pw,ph)
        for row in range(ph):
            t=row/ph
            r=int(20*(1-t)+12*t);g=int(25*(1-t)+15*t);b=int(55*(1-t)+35*t)
            pygame.draw.line(panel,(r,g,b,240),(0,row),(pw,row))
        mask=A(pw,ph);pygame.draw.rect(mask,(255,255,255),(0,0,pw,ph),border_radius=24)
        panel.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(panel,(px,py))
        pygame.draw.rect(screen,(50,60,100),(px,py,pw,ph),2,border_radius=24)

        tt=f28.render("Level Complete!",True,(100,230,140))
        screen.blit(tt,(SW//2-tt.get_width()//2,py+28))

        st=self.stars();sw_=36;sg=16
        total_s=sw_*3+sg*2;ssx=SW//2-total_s//2
        for i in range(3):
            x_=ssx+i*(sw_+sg);y_=py+85
            delay=i*0.14;elapsed=max(0,self.wt-0.2-delay)
            if elapsed>0:
                sc=min(1,elapsed*6);bounce=1+0.25*max(0,1-elapsed*4)
                fsz=int(sw_*sc*bounce)
                img=STAR_ON if i<st else STAR_OFF
                scaled=pygame.transform.smoothscale(img,(fsz,fsz))
                screen.blit(scaled,(x_+sw_//2-fsz//2,y_+sw_//2-fsz//2))

        mt=f18.render(f"Moves: {self.mv}",True,(170,175,200))
        screen.blit(mt,(SW//2-mt.get_width()//2,py+140))

        reward=self.stars()*15
        screen.blit(COIN_IMG,(SW//2-40,py+175))
        rt=f22.render(f"+ {reward}",True,(255,220,50))
        screen.blit(rt,(SW//2-12,py+176))

        mouse=pygame.mouse.get_pos()
        bw_,bh_=140,48;gap_=14
        bx1=SW//2-bw_-gap_//2;bx2=SW//2+gap_//2;by_=py+260

        nr=pygame.Rect(bx1,by_,bw_,bh_);rr=pygame.Rect(bx2,by_,bw_,bh_)
        for rect,text,bc in[(nr,"Next Level",(60,180,100)),(rr,"Replay",(50,60,100))]:
            hov=rect.collidepoint(mouse)
            c=brighter(bc,15) if hov else bc
            pygame.draw.rect(screen,(0,0,0,40),(rect.x+2,rect.y+3,bw_,bh_),border_radius=14)
            pygame.draw.rect(screen,c,rect,border_radius=14)
            pygame.draw.rect(screen,brighter(c,35),rect,1,border_radius=14)
            t=f18.render(text,True,(240,245,255))
            screen.blit(t,(rect.centerx-t.get_width()//2,rect.centery-t.get_height()//2))

        return nr,rr

    def draw_menu(self,dt):
        self.mt+=dt
        screen.blit(BG,(0,0))

        if random.random()<0.04:
            c=random.choice(list(WATER.values()))
            self.pts.append(Pt(random.randint(0,SW),SH+5,c,
                random.uniform(-0.3,0.3),random.uniform(-0.6,-0.2),
                random.uniform(2,4),gv=False,sh=3))
        for p in self.pts:p.draw(screen)

        b=f11.render("SUPER GAME APP",True,(80,90,140))
        screen.blit(b,(SW//2-b.get_width()//2,150))

        t1=f44.render("Water Sort",True,(220,230,255))
        screen.blit(t1,(SW//2-t1.get_width()//2,170))
        t2=f28.render("Puzzle",True,(70,150,230))
        screen.blit(t2,(SW//2-t2.get_width()//2,220))

        # Preview bottles
        preview=[[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4]]
        sp=TW+14;ptw=len(preview)*sp-14;psx=(SW-ptw)//2
        for i,pt in enumerate(preview):
            tx=psx+i*sp
            ty=300+int(math.sin(self.mt*2+i*1.1)*8)
            screen.blit(BOTTLE_COMPLETE,(tx-B_PAD,ty-B_PAD))
            draw_liquid(screen,tx,ty+CAP_H+NECK_H,pt)

        # Play button
        mouse=pygame.mouse.get_pos()
        pr=pygame.Rect(SW//2-105,545,210,56)
        hov=pr.collidepoint(mouse)
        pc=(50,180,100) if not hov else (65,200,115)

        pygame.draw.rect(screen,(0,0,0,40),(pr.x+2,pr.y+4,210,56),border_radius=28)
        # Gradient button
        btn=A(210,56)
        lt=brighter(pc,20);dk=dimmer(pc,10)
        for row in range(56):
            t=row/55
            r=int(lt[0]*(1-t)+dk[0]*t);g=int(lt[1]*(1-t)+dk[1]*t);b_=int(lt[2]*(1-t)+dk[2]*t)
            pygame.draw.line(btn,(r,g,b_,240),(0,row),(209,row))
        mask=A(210,56);pygame.draw.rect(mask,(255,255,255),(0,0,210,56),border_radius=28)
        btn.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(btn,pr.topleft)
        pygame.draw.rect(screen,brighter(pc,40),pr,1,border_radius=28)
        pt_=f22.render("P L A Y",True,(255,255,255))
        screen.blit(pt_,(pr.centerx-pt_.get_width()//2,pr.centery-pt_.get_height()//2))

        li=f15.render(f"Level {self.lv}",True,(100,110,155))
        screen.blit(li,(SW//2-li.get_width()//2,620))
        screen.blit(COIN_IMG,(SW//2-30,650))
        ci=f15.render(str(self.coins),True,(255,220,50))
        screen.blit(ci,(SW//2-4,653))

        ft=f10.render("Tap PLAY to start",True,(50,55,80))
        screen.blit(ft,(SW//2-ft.get_width()//2,SH-30))
        return pr

    def run(self):
        running=True;play_r=next_r=rep_r=None
        while running:
            dt=clock.tick(FPS)/1000.0;mouse=pygame.mouse.get_pos()
            if self.hint_move:self.hint_blink+=dt

            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:running=False
                if ev.type==pygame.KEYDOWN:
                    if ev.key==pygame.K_ESCAPE:
                        if self.state=="play":self.state="menu"
                        else:running=False
                    if ev.key==pygame.K_u and self.state=="play":self.do_undo()
                    if ev.key==pygame.K_r and self.state=="play":self.load(self.lv)
                    if ev.key==pygame.K_h and self.state=="play":self.get_hint()
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.state=="menu":
                        if play_r and play_r.collidepoint(mouse):SND_TAP.play();self.load(self.lv)
                    elif self.state=="play" and not self.pa:
                        btn_hit=False
                        if hasattr(self,'_btns'):
                            for r,name in self._btns:
                                if r.collidepoint(mouse):
                                    if name=="undo":self.do_undo()
                                    elif name=="hint":self.get_hint()
                                    elif name=="add":self.add_tube()
                                    btn_hit=True;break
                        if not btn_hit:
                            ci=self.tube_at(*mouse)
                            if ci>=0:
                                SND_TAP.play()
                                if self.sel==-1:
                                    if self.tubes[ci]:self.sel=ci;self.sel_bounce={}
                                elif self.sel==ci:self.sel=-1
                                else:
                                    if self.can_pour(self.sel,ci):
                                        s=self.sel;self.sel=-1;self.start_pour(s,ci)
                                    elif self.tubes[ci]:self.sel=ci;self.sel_bounce={}
                                    else:self.sel=-1
                    elif self.state=="win":
                        if next_r and next_r.collidepoint(mouse):
                            SND_TAP.play();self.load(self.lv+1)
                        elif rep_r and rep_r.collidepoint(mouse):
                            SND_TAP.play();self.load(self.lv)

            self.upd_pour(dt)
            self.pts=[p for p in self.pts if p.upd(dt)]
            if self.state=="win" and self.wt<4 and random.random()<0.1:
                cols=[(255,107,107),(78,205,196),(255,230,109),(162,155,254),(255,159,243)]
                self.pts.append(Pt(random.randint(20,SW-20),random.randint(-20,SH//3),
                    random.choice(cols),random.uniform(-2,2),random.uniform(-3,1),
                    random.uniform(4,8),sh=random.choice([0,1,2,3])))

            if self.state=="menu":play_r=self.draw_menu(dt)
            elif self.state=="play":self.draw_play(dt)
            elif self.state=="win":self.draw_play(dt);next_r,rep_r=self.draw_win(dt)
            pygame.display.flip()
        pygame.quit();sys.exit()

if __name__=="__main__":
    Game().run()
