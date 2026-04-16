"""
Water Sort Puzzle — Matching commercial reference exactly
3D bottles with cap/neck/body/base, dark galaxy background
"""

import pygame
import pygame.gfxdraw
import sys, random, copy, math, array, json, os

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)

SW, SH = 440, 850
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Water Sort Puzzle")
clock = pygame.time.Clock()
FPS = 60
LAYERS = 4

def A(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)

# ═══════════════════════════════════════════════════
#  SOUNDS
# ═══════════════════════════════════════════════════

def _snd(freq, dur, vol=0.2):
    sr=44100;n=int(sr*dur);b=array.array('h')
    for i in range(n):
        t=i/sr;v=math.sin(2*math.pi*freq*t)*vol
        env=min(1,i/100)*max(0,1-i/n)
        b.append(int(v*env*32767))
    return pygame.mixer.Sound(buffer=b)

def _water():
    sr=44100;n=int(sr*0.4);b=array.array('h');rng=random.Random(7);prev=0
    for i in range(n):
        t=i/sr;env=min(1,i/300)*max(0,1-i/n)
        noise=rng.uniform(-1,1);prev=prev*0.9+noise*0.1
        v=prev*0.4+math.sin(2*math.pi*180*t+3*math.sin(2*math.pi*30*t))*0.25
        b.append(int(v*env*0.3*32767))
    return pygame.mixer.Sound(buffer=b)

def _splash():
    sr=44100;n=int(sr*0.12);b=array.array('h');rng=random.Random(13);prev=0
    for i in range(n):
        env=min(1,i/60)*max(0,1-i/n)**2
        prev=prev*0.82+rng.uniform(-1,1)*0.18
        b.append(int(prev*env*0.3*32767))
    return pygame.mixer.Sound(buffer=b)

def _chime(notes,each=0.1):
    sr=44100;b=array.array('h')
    for note in notes:
        for i in range(int(sr*each)):
            t=i/sr;env=min(1,i/50)*max(0,1-i/(sr*each)*0.5)
            v=math.sin(2*math.pi*note*t)*0.25+math.sin(2*math.pi*note*2*t)*0.08
            b.append(int(v*env*32767))
    return pygame.mixer.Sound(buffer=b)

S_TAP=_snd(900,0.04,0.1);S_POUR=_water();S_SPLASH=_splash()
S_DONE=_chime([523,659,784]);S_WIN=_chime([523,587,659,784,1047],0.08)
S_UNDO=_snd(350,0.05,0.08);S_ERR=_snd(200,0.08,0.06)

# ═══════════════════════════════════════════════════
#  COLORS — Exactly matching reference screenshot
# ═══════════════════════════════════════════════════

WATER = {
    1: (120, 215, 50),    # Bright green (reference top-left)
    2: (255, 100, 180),   # Hot pink
    3: (100, 60, 170),    # Dark purple
    4: (240, 200, 40),    # Golden yellow
    5: (40, 90, 220),     # Royal blue
    6: (230, 55, 45),     # Red
    7: (255, 145, 30),    # Orange
    8: (60, 200, 230),    # Cyan/light blue
    9: (240, 140, 200),   # Light pink/magenta
    10:(170, 120, 80),    # Brown
    11:(200, 240, 80),    # Lime
    12:(240, 230, 130),   # Pale yellow
}

def br(c,n=40): return tuple(min(255,x+n) for x in c)
def dk(c,n=35): return tuple(max(0,x-n) for x in c)
def lp(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

# ═══════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════

def MF(s,b=False):
    for n in["SF Pro Rounded","Avenir Next","Helvetica Neue","Arial Rounded MT Bold","Arial"]:
        try:return pygame.font.SysFont(n,s,b)
        except:pass
    return pygame.font.SysFont(None,s,b)

f40=MF(40,True);f26=MF(26,True);f20=MF(20,True);f16=MF(16,True)
f14=MF(14);f12=MF(12,True);f10=MF(10,True);f9=MF(9,True);f8=MF(8)

# ═══════════════════════════════════════════════════
#  BACKGROUND — Dark galaxy
# ═══════════════════════════════════════════════════

def make_bg():
    s=pygame.Surface((SW,SH))
    for y in range(SH):
        t=y/SH
        r=int(8*(1-t)+3*t);g=int(10*(1-t)+5*t);b=int(42*(1-t)+20*t)
        pygame.draw.line(s,(r,g,b),(0,y),(SW,y))
    rng=random.Random(42)
    for _ in range(100):
        x,y=rng.randint(0,SW),rng.randint(0,SH)
        bri=rng.randint(30,110);sz=rng.choice([1,1,1,2])
        pygame.draw.circle(s,(bri,bri,bri+20),(x,y),sz)
    # Nebula
    g=A(SW,SH)
    pygame.draw.circle(g,(25,15,70,18),(SW//2,SH//3),260)
    pygame.draw.circle(g,(15,10,50,12),(100,SH*2//3),180)
    s.blit(g,(0,0))
    return s

BG=make_bg()

# ═══════════════════════════════════════════════════
#  BOTTLE GEOMETRY (matching reference proportions)
# ═══════════════════════════════════════════════════
#  Reference shows: wide body, narrow neck, small rounded cap,
#  visible base/stand at bottom, tall proportions

BW = 52        # body width
BH = 170       # body height
NW = 28        # neck width
NH = 14        # neck height
CW = 22        # cap width
CH = 8         # cap height
BASE_H = 12    # base/stand height
BOT_R = 18     # body bottom curve
WALL = 3
IW = BW - WALL*2
LH = (BH - BOT_R - WALL) // LAYERS

FULL_H = CH + NH + BH + BASE_H
B_PAD = 22  # padding for surface

# ═══════════════════════════════════════════════════
#  BOTTLE RENDERER
# ═══════════════════════════════════════════════════

def render_bottle(selected=False, complete=False):
    """Render 3D bottle matching reference: cap + neck + body + base."""
    w = BW + B_PAD*2
    h = FULL_H + B_PAD*2
    s = A(w, h)

    ox = B_PAD
    cap_x = ox + (BW-CW)//2
    neck_x = ox + (BW-NW)//2

    cap_y = B_PAD
    neck_y = cap_y + CH
    body_y = neck_y + NH
    base_y = body_y + BH

    # Base color scheme
    if selected:
        bc=(35,80,190); bdr=(70,140,255); gc=(70,150,255,55)
    elif complete:
        bc=(25,70,170); bdr=(60,170,130); gc=(60,200,120,40)
    else:
        bc=(18,25,65); bdr=(40,55,120); gc=None

    # ── GLOW ──
    if gc:
        for r in range(28,0,-2):
            a=gc[3]*(1-r/28)
            pygame.draw.rect(s,(*gc[:3],int(a)),(ox-r,body_y-r,BW+r*2,BH+r*2),border_radius=BOT_R+r)

    # ── BODY — 3D cylindrical ──
    body=A(BW,BH)
    for col in range(BW):
        t=(col-BW/2)/(BW/2)
        # Cylindrical: bright left-of-center, dark edges
        brightness = 0.3 + 0.7 * math.exp(-((t+0.3)**2)/0.1)
        r=max(0,min(255,int(bc[0]*brightness*2.2)))
        g=max(0,min(255,int(bc[1]*brightness*2.2)))
        b=max(0,min(255,int(bc[2]*brightness*2.2)))
        # Rect part
        for row in range(BH-BOT_R):
            body.set_at((col,row),(r,g,b,215))
        # Bottom curve
        for row in range(BOT_R):
            ey=row/max(1,BOT_R)
            ex=abs(t)
            if ex**2+(1-ey)**2<=1.08:
                dr=max(0,int(r*(1-ey*0.35)))
                dg=max(0,int(g*(1-ey*0.35)))
                db=max(0,int(b*(1-ey*0.35)))
                body.set_at((col,BH-BOT_R+row),(dr,dg,db,215))

    # Highlight streaks
    for row in range(6,BH-BOT_R-6):
        t=(row-6)/max(1,BH-BOT_R-12)
        inten=int(80*math.exp(-((t-0.12)**2)/0.008)+35*math.exp(-((t-0.45)**2)/0.06))
        if inten>2:
            for dx in range(7):
                a=int(inten*max(0,1-dx/6))
                if a>0 and WALL+1+dx<BW:
                    px=body.get_at((WALL+1+dx,row))
                    body.set_at((WALL+1+dx,row),(min(255,px[0]+a),min(255,px[1]+a),min(255,px[2]+a),px[3]))
    # Right highlight (dimmer)
    for row in range(12,BH-BOT_R-12):
        t=(row-12)/max(1,BH-BOT_R-24)
        inten=int(18*math.exp(-((t-0.3)**2)/0.04))
        if inten>1 and BW-WALL-4>=0:
            px=body.get_at((BW-WALL-4,row))
            body.set_at((BW-WALL-4,row),(min(255,px[0]+inten),min(255,px[1]+inten),min(255,px[2]+inten),px[3]))

    s.blit(body,(ox,body_y))

    # Body outline
    pygame.draw.line(s,(*bdr,180),(ox,body_y),(ox,body_y+BH-BOT_R),2)
    pygame.draw.line(s,(*bdr,140),(ox+BW-1,body_y),(ox+BW-1,body_y+BH-BOT_R),2)
    pygame.draw.arc(s,(*bdr,160),(ox,body_y+BH-BOT_R*2,BW,BOT_R*2),math.pi,2*math.pi,2)

    # ── NECK ──
    neck=A(NW,NH)
    for col in range(NW):
        t=(col-NW/2)/(NW/2)
        brightness=0.4+0.6*math.exp(-((t+0.2)**2)/0.15)
        r=max(0,min(255,int(bc[0]*brightness*1.8)))
        g=max(0,min(255,int(bc[1]*brightness*1.8)))
        b=max(0,min(255,int(bc[2]*brightness*1.8)))
        for row in range(NH):
            neck.set_at((col,row),(r,g,b,200))
    s.blit(neck,(neck_x,neck_y))
    pygame.draw.line(s,(*bdr,120),(neck_x,neck_y),(neck_x,neck_y+NH),1)
    pygame.draw.line(s,(*bdr,100),(neck_x+NW-1,neck_y),(neck_x+NW-1,neck_y+NH),1)

    # Shoulders (diagonal lines connecting neck to body)
    pygame.draw.line(s,(*bdr,90),(neck_x,neck_y+NH),(ox+1,body_y+1),1)
    pygame.draw.line(s,(*bdr,90),(neck_x+NW,neck_y+NH),(ox+BW-1,body_y+1),1)

    # ── CAP ──
    cap=A(CW,CH)
    for col in range(CW):
        t=(col-CW/2)/(CW/2)
        brightness=0.5+0.5*math.exp(-(t**2)/0.2)
        cap_c=(50,70,140) if not selected else (60,100,200)
        if complete:cap_c=(50,140,100)
        r=max(0,min(255,int(cap_c[0]*brightness*2)))
        g=max(0,min(255,int(cap_c[1]*brightness*2)))
        b_=max(0,min(255,int(cap_c[2]*brightness*2)))
        for row in range(CH):
            cap.set_at((col,row),(r,g,b_,220))
    pygame.draw.rect(cap,(*br(bdr,20),100),(0,0,CW,CH),1,border_radius=3)
    s.blit(cap,(cap_x,cap_y))

    # ── BASE/STAND (light colored, like reference) ──
    base=A(BW+4,BASE_H)
    # Trapezoidal base: wider at bottom
    for row in range(BASE_H):
        t=row/max(1,BASE_H-1)
        w_at = int(BW*0.6 + BW*0.4*t*0.3)  # slightly wider at bottom
        bx=(BW+4-w_at)//2
        base_c = (180,170,150) if not selected else (200,190,170)
        if complete: base_c=(170,200,170)
        # Gradient
        rc = int(base_c[0]*(1-t*0.3))
        gc_ = int(base_c[1]*(1-t*0.3))
        bc_ = int(base_c[2]*(1-t*0.3))
        pygame.draw.line(base,(rc,gc_,bc_,180),(bx,row),(bx+w_at,row))
    s.blit(base,(ox-2,base_y))

    return s

BOTTLE_N = render_bottle(False,False)
BOTTLE_S = render_bottle(True,False)
BOTTLE_C = render_bottle(False,True)

# ═══════════════════════════════════════════════════
#  LIQUID RENDERER
# ═══════════════════════════════════════════════════

def draw_liquid(surf, bx, by, tube, show_qmarks=False):
    """Draw liquid inside bottle body. Flat vivid colors, full width fill."""
    body_y = by  # top of body area
    lx = bx + WALL + 1
    lw = IW - 2
    bottom = body_y + BH - WALL - 1

    for i in range(LAYERS):
        ly = bottom - (i+1)*LH
        lh = LH

        if i < len(tube):
            cid = tube[i]
            color = WATER.get(cid, (150,150,150))

            # Flat fill with very subtle gradient
            layer = A(lw, lh + (BOT_R if i==0 else 0))
            for row in range(lh):
                t = row/max(1,lh-1)
                if t<0.05: c=lp(br(color,40),color,t/0.05)
                elif t>0.95: c=lp(color,dk(color,20),(t-0.95)/0.05)
                else: c=color
                pygame.draw.line(layer,(*c,245),(0,row),(lw,row))

            # Bottom curve fill
            if i==0:
                for row in range(BOT_R):
                    t=row/max(1,BOT_R-1)
                    dy=BOT_R-row
                    hw=math.sqrt(max(0,BOT_R**2-dy**2))*lw/(2*BOT_R)
                    cx=lw//2
                    x1=max(0,int(cx-hw));x2=min(lw,int(cx+hw))
                    c=lp(color,dk(color,25),t*0.5)
                    pygame.draw.line(layer,(*c,245),(x1,lh+row),(x2,lh+row))

            surf.blit(layer,(lx,ly))

            # Shine strip left
            sh=A(5,lh-2)
            for row in range(lh-2):
                t=row/max(1,lh-3)
                a=int(55*math.sin(t*math.pi))
                if a>2:pygame.draw.line(sh,(255,255,255,a),(0,row),(3,row))
            surf.blit(sh,(lx+2,ly+1))

            # Right edge shadow
            rs=A(4,lh-2)
            for row in range(lh-2):
                a=int(20*math.sin(row/max(1,lh-3)*math.pi))
                if a>1:pygame.draw.line(rs,(0,0,0,a),(0,row),(2,row))
            surf.blit(rs,(lx+lw-5,ly+1))

            # Border between different colors
            if i>0 and i<len(tube) and tube[i]!=tube[i-1]:
                border_y=bottom-i*LH
                pygame.draw.line(surf,(*dk(color,60),60),(lx,border_y),(lx+lw,border_y),1)

            # Meniscus on top layer
            if i==len(tube)-1:
                men=A(lw,4)
                for col in range(lw):
                    t_=(col-lw/2)/(lw/2)
                    h_=int(2*(1-t_**2))
                    a_=int(75*(1-abs(t_)*0.4))
                    mc=br(color,55)
                    for row in range(min(h_,4)):
                        men.set_at((col,row),(*mc,max(0,a_-row*20)))
                surf.blit(men,(lx,ly))

        elif show_qmarks and i < LAYERS:
            # Empty slot — show ? mark (like reference)
            qm = f20.render("?", True, (60,70,110))
            qx = bx + BW//2 - qm.get_width()//2
            qy = ly + lh//2 - qm.get_height()//2
            surf.blit(qm, (qx, qy))

# ═══════════════════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════════════════

class Pt:
    __slots__=['x','y','vx','vy','life','sz','c','gv','sh','dc']
    def __init__(s,x,y,c,vx=None,vy=None,sz=None,gv=True,sh=0):
        s.x=x;s.y=y;s.c=c;s.sh=sh
        s.vx=vx if vx is not None else random.uniform(-3,3)
        s.vy=vy if vy is not None else random.uniform(-6,-2)
        s.sz=sz or random.uniform(3,7);s.life=1.0;s.gv=gv
        s.dc=random.uniform(0.7,1.4)
    def upd(s,dt):
        s.x+=s.vx*60*dt;s.y+=s.vy*60*dt
        if s.gv:s.vy+=10*dt
        s.life-=dt/s.dc;return s.life>0
    def draw(s,sf):
        a=max(0,min(255,int(s.life*255)));sz=max(1,int(s.sz*max(0.2,s.life)))
        if a<5 or sz<1:return
        t=A(sz*2+2,sz*2+2)
        if s.sh==0:pygame.draw.circle(t,(*s.c,a),(sz+1,sz+1),sz)
        elif s.sh==1:
            w=max(1,int(sz*abs(math.sin(s.life*10))));h=max(1,int(sz*0.5))
            pygame.draw.rect(t,(*s.c,a),(sz+1-w//2,sz+1-h//2,w,h))
        elif s.sh==2:
            cx,cy=sz+1,sz+1
            pts=[(cx+(sz if i%2==0 else sz*0.4)*math.cos(math.radians(i*36-90+s.life*200)),
                  cy+(sz if i%2==0 else sz*0.4)*math.sin(math.radians(i*36-90+s.life*200))) for i in range(10)]
            pygame.draw.polygon(t,(*s.c,a),pts)
        elif s.sh==3:
            cx,cy=sz+1,sz+1
            for ang in range(0,360,60):
                rad=math.radians(ang+s.life*180)
                pygame.draw.line(t,(*s.c,a),(cx,cy),(cx+int(sz*math.cos(rad)),cy+int(sz*math.sin(rad))),1)
        sf.blit(t,(int(s.x)-sz-1,int(s.y)-sz-1))

# ═══════════════════════════════════════════════════
#  LEVEL GEN + SOLVER
# ═══════════════════════════════════════════════════

def get_diff(lv):
    if lv<=3:return 3,2
    if lv<=8:return 4,2
    if lv<=15:return 5,2
    if lv<=25:return 6,2
    if lv<=40:return 7,2
    if lv<=60:return 8,2
    return 9,2

def gen_level(lv):
    rng=random.Random(lv*31337+97);nc,ne=get_diff(lv)
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
            top=ts[f][-1];cnt=sum(1 for k in range(len(ts[f])-1,-1,-1) if ts[f][k]==top)
            for d in range(len(ts)):
                if f==d or len(ts[d])>=LAYERS:continue
                if not ts[d]:
                    if len(set(ts[f]))!=1:mv.append((f,d))
                elif ts[d][-1]==top and len(ts[d])+cnt<=LAYERS:mv.append((f,d))
        return mv
    def do(ts,f,d):
        ns=[list(t) for t in ts];top=ns[f][-1]
        while ns[f] and ns[f][-1]==top and len(ns[d])<LAYERS:ns[d].append(ns[f].pop())
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
    mv=moves(tubes);return mv[0] if mv else None

# ═══════════════════════════════════════════════════
#  SAVE
# ═══════════════════════════════════════════════════

SAVE_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)),"save.json")
def save_data(d):
    try:
        with open(SAVE_PATH,'w') as f:json.dump(d,f)
    except:pass
def load_data():
    try:
        with open(SAVE_PATH) as f:return json.load(f)
    except:return{"level":1,"coins":100,"undos":5,"hints":4,"adds":4,"stars":{},"best":1}

# ═══════════════════════════════════════════════════
#  ASSETS
# ═══════════════════════════════════════════════════

def make_star(c1,c2,sz=34):
    s=A(sz,sz);cx,cy=sz//2,sz//2;ro,ri=sz//2-2,sz//5
    pts=[(cx+(ro if i%2==0 else ri)*math.cos(math.radians(i*36-90)),
          cy+(ro if i%2==0 else ri)*math.sin(math.radians(i*36-90))) for i in range(10)]
    pygame.draw.polygon(s,c1,pts)
    pts2=[(cx+((ro-3) if i%2==0 else max(1,ri-1))*math.cos(math.radians(i*36-90)),
           cy+((ro-3) if i%2==0 else max(1,ri-1))*math.sin(math.radians(i*36-90))) for i in range(10)]
    pygame.draw.polygon(s,c2,pts2);return s

STAR_ON=make_star((245,195,20),(255,230,80))
STAR_OFF=make_star((40,45,70),(55,60,85))

def make_coin():
    s=A(24,24);pygame.draw.circle(s,(255,193,7),(12,12),11)
    pygame.draw.circle(s,(255,225,60),(12,11),9)
    t=f10.render("$",True,(190,140,0));s.blit(t,(12-t.get_width()//2,12-t.get_height()//2))
    pygame.draw.circle(s,(210,165,0),(12,12),11,2);return s

COIN_IMG=make_coin()

# ═══════════════════════════════════════════════════
#  BOTTOM BUTTON BAR (pill-shaped container like reference)
# ═══════════════════════════════════════════════════

def draw_btn_bar(surf, buttons_data, mouse):
    """Draw buttons inside a single pill-shaped container bar."""
    btn_r = 24
    gap = 32
    n = len(buttons_data)
    total_w = n * (btn_r*2) + (n-1)*gap + 40  # 40 = padding
    bar_h = btn_r*2 + 28
    bar_x = (SW - total_w)//2
    bar_y = SH - 85

    # Pill container
    pill = A(total_w, bar_h)
    pygame.draw.rect(pill, (20, 25, 55, 180), (0, 0, total_w, bar_h), border_radius=bar_h//2)
    pygame.draw.rect(pill, (50, 65, 120, 120), (0, 0, total_w, bar_h), 2, border_radius=bar_h//2)
    surf.blit(pill, (bar_x, bar_y))

    rects = []
    for i, (icon_fn, count, color, name) in enumerate(buttons_data):
        cx = bar_x + 20 + btn_r + i*(btn_r*2+gap)
        cy = bar_y + bar_h//2 - 6

        rect = pygame.Rect(cx-btn_r-4, cy-btn_r-4, btn_r*2+8, btn_r*2+20)
        hov = rect.collidepoint(mouse)

        # Glow on hover
        if hov:
            pygame.draw.circle(surf, (*br(color,30), 40), (cx, cy), btn_r+6)

        # Circle
        pygame.draw.circle(surf, (*color, 200), (cx, cy), btn_r)
        pygame.draw.circle(surf, (*br(color,50), 150), (cx, cy), btn_r, 2)

        # Icon
        icon_fn(surf, cx, cy)

        # Count badge (orange circle below, like reference)
        badge_y = cy + btn_r + 4
        badge = A(20, 16)
        pygame.draw.rect(badge, (200, 120, 30, 220), (0, 0, 20, 16), border_radius=8)
        ct = f9.render(str(count), True, (255, 255, 255))
        badge.blit(ct, (10-ct.get_width()//2, 8-ct.get_height()//2))
        surf.blit(badge, (cx-10, badge_y))

        rects.append((rect, name))

    return rects

def icon_undo(s,cx,cy):
    c=(255,255,255)
    pygame.draw.arc(s,c,(cx-7,cy-7,14,14),math.radians(30),math.radians(300),2)
    ax=cx+int(7*math.cos(math.radians(30)));ay=cy-int(7*math.sin(math.radians(30)))
    pygame.draw.polygon(s,c,[(ax-1,ay-4),(ax+4,ay),(ax-1,ay+2)])

def icon_hint(s,cx,cy):
    c=(255,255,255)
    pygame.draw.polygon(s,c,[(cx-2,cy-9),(cx+4,cy-1),(cx,cy-1),(cx+2,cy+9),(cx-4,cy+1),(cx,cy+1)])

def icon_add(s,cx,cy):
    c=(255,255,255)
    # +0 like reference
    pygame.draw.line(s,c,(cx-6,cy),(cx+6,cy),2)
    pygame.draw.line(s,c,(cx,cy-6),(cx,cy+6),2)
    # Small tube outline
    pygame.draw.rect(s,c,(cx+5,cy-3,4,7),1,border_radius=1)

# ═══════════════════════════════════════════════════
#  GAME
# ═══════════════════════════════════════════════════

class Game:
    def __init__(self):
        self.sav=load_data();self.state="menu"
        self.lv=self.sav.get("level",1);self.coins=self.sav.get("coins",100)
        self.mv=0;self.sel=-1;self.tubes=[];self.undo_stack=[];self.pos=[]
        self.pts=[];self.wt=0;self.mt=0;self.hint_move=None;self.hint_blink=0
        self.done_set=set();self.extra=0
        self.uc=self.sav.get("undos",5);self.hc=self.sav.get("hints",4);self.ac=self.sav.get("adds",4)
        self.pa=False;self.ps=self.pd=-1;self.pp=0;self.pt_=0
        self.po=[0,0];self.tilt=0;self.poured=False;self.spts=[]
        self.sel_b={};self._btns=[]

    def _save(self):
        self.sav.update({"level":self.lv,"coins":self.coins,"undos":self.uc,"hints":self.hc,"adds":self.ac})
        save_data(self.sav)

    def load(self,n):
        self.lv=n;self.tubes=gen_level(n);self.mv=0;self.sel=-1
        self.undo_stack=[];self.pts=[];self.state="play"
        self.pa=False;self.wt=0;self.hint_move=None;self.hint_blink=0
        self.done_set=set();self.extra=0;self.sel_b={};self.spts=[]
        self._layout()

    def _layout(self):
        self.pos=[];n=len(self.tubes)
        # Split into 2 rows: fuller tubes on top, emptier on bottom (like reference)
        per=min(n,5 if n<=10 else 6)
        rows=math.ceil(n/per)
        sp=BW+16
        play_top=100;play_bot=SH-100
        total_h=rows*(FULL_H+15)-15
        start_y=play_top+max(0,(play_bot-play_top-total_h)//2)

        for i in range(n):
            r=i//per;c=i%per
            nr=min(per,n-r*per);tw=nr*sp-16;sx=(SW-tw)//2
            self.pos.append((sx+c*sp, start_y+r*(FULL_H+15)))

    def tube_at(self,mx,my):
        for i,(x,y) in enumerate(self.pos):
            if pygame.Rect(x-8,y,BW+16,FULL_H+10).collidepoint(mx,my):return i
        return -1

    def can_pour(self,s,d):
        a,b=self.tubes[s],self.tubes[d]
        if not a or len(b)>=LAYERS:return False
        return not b or a[-1]==b[-1]

    def do_pour(self,s,d):
        a,b=self.tubes[s],self.tubes[d]
        self.undo_stack.append(copy.deepcopy(self.tubes))
        top=a[-1]
        while a and a[-1]==top and len(b)<LAYERS:b.append(a.pop())
        self.mv+=1;S_SPLASH.play()
        if is_done(b) and d not in self.done_set:
            self.done_set.add(d);self._fx(d);S_DONE.play()
        self.hint_move=None

    def do_undo(self):
        if not self.undo_stack or self.pa:return
        if self.uc<=0:S_ERR.play();return
        self.tubes=self.undo_stack.pop();self.mv=max(0,self.mv-1);self.sel=-1
        self.hint_move=None;self.done_set={i for i,t in enumerate(self.tubes) if t and is_done(t)}
        self.uc-=1;S_UNDO.play()

    def add_tube(self):
        if self.ac<=0:S_ERR.play();return
        self.tubes.append([]);self.ac-=1;self.extra+=1;self._layout();S_TAP.play()

    def get_hint(self):
        if self.hc<=0:S_ERR.play();return
        h=find_hint(self.tubes)
        if h:self.hint_move=h;self.hint_blink=0;self.hc-=1;S_TAP.play()

    def _fx(self,idx):
        x,y=self.pos[idx];cx=x+BW//2;cy=y+FULL_H//2
        c=WATER.get(self.tubes[idx][0],(200,200,200))
        for _ in range(30):
            self.pts.append(Pt(cx+random.randint(-15,15),cy+random.randint(-40,20),
                br(c,40),random.uniform(-3,3),random.uniform(-6,-1),
                random.uniform(3,7),sh=random.choice([0,2,3])))

    def stars(self):
        c,_=get_diff(self.lv);opt=c*2
        if self.mv<=opt:return 3
        if self.mv<=opt*2:return 2
        return 1

    def start_pour(self,s,d):
        self.pa=True;self.ps=s;self.pd=d;self.pp=0;self.pt_=0
        self.po=[0,0];self.tilt=0;self.poured=False;self.spts=[];S_POUR.play()

    def upd_pour(self,dt):
        if not self.pa:return
        self.pt_+=dt*3.8;t=min(1,self.pt_);t=t*t*(3-2*t)
        sx,sy=self.pos[self.ps];dx,dy=self.pos[self.pd];dr=1 if dx>sx else -1
        if self.pp==0:
            self.po=[0,-55*t];self.tilt=0
            if self.pt_>=1:self.pp=1;self.pt_=0
        elif self.pp==1:
            tx=(dx-sx)+dr*20;self.po=[tx*t,-55];self.tilt=0
            if self.pt_>=1:self.pp=2;self.pt_=0
        elif self.pp==2:
            tx=(dx-sx)+dr*20;self.po=[tx,-55];self.tilt=-dr*50*t
            if not self.poured and self.pt_>=0.35:self.do_pour(self.ps,self.pd);self.poured=True
            if 0.15<self.pt_<0.85:
                px=dx+BW//2;py=dy+CH+NH
                if self.tubes[self.pd]:
                    c=WATER.get(self.tubes[self.pd][-1],(200,200,200))
                    for _ in range(3):
                        self.spts.append(Pt(px+random.randint(-4,4),py+random.randint(-5,10),
                            br(c,20),random.uniform(-0.8,0.8),random.uniform(1,5),random.uniform(2,4)))
            if self.pt_>=1:self.pp=3;self.pt_=0
        elif self.pp==3:
            tx=(dx-sx)+dr*20;self.po=[tx*(1-t),-55*(1-t)];self.tilt=-dr*50*(1-t)
            if self.pt_>=1:
                self.pa=False;self.po=[0,0];self.tilt=0
                if all_done(self.tubes):
                    self.state="win";self.wt=0;self._win_fx();S_WIN.play()
                    rw=self.stars()*15;self.coins+=rw
                    self.sav["stars"][str(self.lv)]=self.stars()
                    if self.lv>=self.sav.get("best",1):self.sav["best"]=self.lv+1
                    self._save()
        self.spts=[p for p in self.spts if p.upd(dt)]

    def _win_fx(self):
        cols=[(255,107,107),(78,205,196),(255,230,109),(162,155,254),(255,159,243),(110,200,230)]
        for _ in range(150):
            self.pts.append(Pt(random.randint(10,SW-10),random.randint(-50,SH//2),
                random.choice(cols),random.uniform(-5,5),random.uniform(-9,0),
                random.uniform(4,12),sh=random.choice([0,1,2,3])))

    # ── DRAW ──

    def draw_bar(self):
        # Level badge (centered, like reference)
        bw=150;bx=(SW-bw)//2;by=18
        badge=A(bw,34)
        pygame.draw.rect(badge,(15,20,50,230),(0,0,bw,34),border_radius=17)
        pygame.draw.rect(badge,(45,60,110,150),(0,0,bw,34),2,border_radius=17)
        # Eye icon
        pygame.draw.circle(badge,(140,150,190),(22,17),5,1)
        pygame.draw.circle(badge,(140,150,190),(22,17),2)
        lt=f16.render(f"Level {self.lv}",True,(230,235,255))
        badge.blit(lt,(38,17-lt.get_height()//2))
        screen.blit(badge,(bx,by))

        # Difficulty tag
        c,_=get_diff(self.lv)
        dn={3:"EASY",4:"NORMAL",5:"MEDIUM",6:"HARD",7:"EXPERT",8:"MASTER",9:"INSANE"}
        dc={3:(60,190,100),4:(60,150,220),5:(220,190,40),6:(230,120,40),
            7:(220,60,60),8:(190,60,170),9:(190,40,40)}
        d=dn.get(c,"");dcc=dc.get(c,(150,150,150))
        dw=max(48,len(d)*8+14);dx=(SW-dw)//2
        diff=A(dw,18)
        pygame.draw.rect(diff,(*dcc,220),(0,0,dw,18),border_radius=9)
        dt=f9.render(d,True,(255,255,255))
        diff.blit(dt,(dw//2-dt.get_width()//2,9-dt.get_height()//2))
        screen.blit(diff,(dx,by+38))

        # Coins top right
        screen.blit(COIN_IMG,(SW-80,12))
        ct=f16.render(str(self.coins),True,(255,220,50))
        screen.blit(ct,(SW-54,13))

    def draw_tubes(self,dt):
        for i,tube in enumerate(self.tubes):
            tx,ty=self.pos[i];ox,oy=0.0,0.0;tilt=0.0
            if self.pa and self.ps==i:ox,oy=self.po[0],self.po[1];tilt=self.tilt
            elif i==self.sel and not self.pa:
                if i not in self.sel_b:self.sel_b[i]=0
                self.sel_b[i]+=dt*8
                oy=-math.sin(min(math.pi,self.sel_b[i]))*16

            is_hint=(self.hint_move and (i==self.hint_move[0] or i==self.hint_move[1]))
            done=is_done(tube) if tube else False
            sel=(i==self.sel and not self.pa)

            bottle=BOTTLE_S if sel else (BOTTLE_C if done else BOTTLE_N)

            if is_hint and not sel:
                pulse=abs(math.sin(self.hint_blink*4))
                glow=A(BW+30,FULL_H+30)
                pygame.draw.rect(glow,(255,220,80,int(50*pulse)),(0,0,BW+30,FULL_H+30),border_radius=20)
                screen.blit(glow,(int(tx+ox)-15,int(ty+oy)-15))

            fx=int(tx+ox)-B_PAD;fy=int(ty+oy)-B_PAD
            body_x=int(tx+ox);body_y=int(ty+oy)+CH+NH

            is_partial = len(tube)>0 and len(tube)<LAYERS and not done
            is_empty = len(tube)==0

            if abs(tilt)>0.5:
                temp=A(BW+B_PAD*2,FULL_H+B_PAD*2)
                temp.blit(bottle,(0,0))
                draw_liquid(temp,B_PAD,B_PAD+CH+NH,tube)
                rotated=pygame.transform.rotate(temp,tilt)
                rw,rh=rotated.get_size()
                screen.blit(rotated,(fx+(BW+B_PAD*2-rw)//2,fy+(FULL_H+B_PAD*2-rh)//2))
            else:
                screen.blit(bottle,(fx,fy))
                draw_liquid(screen,body_x,body_y,tube,show_qmarks=is_partial)

                if done:
                    bcx=body_x+BW//2;bcy=int(ty+oy)+2
                    pygame.draw.circle(screen,(76,175,80),(bcx,bcy),10)
                    pygame.draw.circle(screen,(110,210,130),(bcx,bcy),8)
                    pygame.draw.lines(screen,(255,255,255),False,[(bcx-4,bcy+1),(bcx-1,bcy+4),(bcx+5,bcy-3)],2)

        for k in list(self.sel_b):
            if k!=self.sel:del self.sel_b[k]

    def draw_play(self,dt):
        screen.blit(BG,(0,0));self.draw_bar();self.draw_tubes(dt)
        for p in self.spts:p.draw(screen)
        for p in self.pts:p.draw(screen)

        mouse=pygame.mouse.get_pos()
        btns=[(icon_undo,self.uc,(160,100,30),"undo"),
              (icon_hint,self.hc,(120,50,170),"hint"),
              (icon_add,self.ac,(40,80,180),"add")]
        self._btns=draw_btn_bar(screen,btns,mouse)

        h=f8.render("U=Undo  H=Hint  R=Restart  ESC=Menu",True,(25,30,55))
        screen.blit(h,(SW//2-h.get_width()//2,SH-15))

    def draw_win(self,dt):
        self.wt+=dt
        ov=A(SW,SH);ov.fill((0,0,0,min(170,int(self.wt*500))));screen.blit(ov,(0,0))
        if self.wt<0.2:return None,None

        pw,ph=360,370;px=(SW-pw)//2;py=(SH-ph)//2-20
        sh=A(pw+8,ph+8);pygame.draw.rect(sh,(0,0,0,70),(4,6,pw,ph),border_radius=24)
        screen.blit(sh,(px-4,py-3))

        panel=A(pw,ph)
        for row in range(ph):
            t=row/ph
            pygame.draw.line(panel,(int(20*(1-t)+12*t),int(25*(1-t)+15*t),int(55*(1-t)+35*t),240),(0,row),(pw,row))
        mask=A(pw,ph);pygame.draw.rect(mask,(255,255,255),(0,0,pw,ph),border_radius=24)
        panel.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(panel,(px,py));pygame.draw.rect(screen,(50,60,100),(px,py,pw,ph),2,border_radius=24)

        tt=f26.render("Level Complete!",True,(100,230,140))
        screen.blit(tt,(SW//2-tt.get_width()//2,py+28))

        st=self.stars();sw_=36;sg=16;ssx=SW//2-(sw_*3+sg*2)//2
        for i in range(3):
            x_=ssx+i*(sw_+sg);y_=py+85;delay=i*0.14;el=max(0,self.wt-0.2-delay)
            if el>0:
                sc=min(1,el*6);bo=1+0.25*max(0,1-el*4);fsz=int(sw_*sc*bo)
                img=STAR_ON if i<st else STAR_OFF
                scaled=pygame.transform.smoothscale(img,(fsz,fsz))
                screen.blit(scaled,(x_+sw_//2-fsz//2,y_+sw_//2-fsz//2))

        mt=f16.render(f"Moves: {self.mv}",True,(170,175,200))
        screen.blit(mt,(SW//2-mt.get_width()//2,py+142))
        rw_=self.stars()*15
        screen.blit(COIN_IMG,(SW//2-40,py+175))
        rt=f20.render(f"+ {rw_}",True,(255,220,50))
        screen.blit(rt,(SW//2-12,py+176))

        mouse=pygame.mouse.get_pos();bw_,bh_=140,48;gap_=14
        bx1=SW//2-bw_-gap_//2;bx2=SW//2+gap_//2;by_=py+260
        nr=pygame.Rect(bx1,by_,bw_,bh_);rr=pygame.Rect(bx2,by_,bw_,bh_)
        for rect,text,bc in[(nr,"Next Level",(60,180,100)),(rr,"Replay",(50,60,100))]:
            hov=rect.collidepoint(mouse);c=br(bc,15) if hov else bc
            pygame.draw.rect(screen,(0,0,0,40),(rect.x+2,rect.y+3,bw_,bh_),border_radius=14)
            pygame.draw.rect(screen,c,rect,border_radius=14)
            pygame.draw.rect(screen,br(c,35),rect,1,border_radius=14)
            t=f16.render(text,True,(240,245,255))
            screen.blit(t,(rect.centerx-t.get_width()//2,rect.centery-t.get_height()//2))
        return nr,rr

    def draw_menu(self,dt):
        self.mt+=dt;screen.blit(BG,(0,0))
        if random.random()<0.04:
            self.pts.append(Pt(random.randint(0,SW),SH+5,random.choice(list(WATER.values())),
                random.uniform(-0.3,0.3),random.uniform(-0.6,-0.2),random.uniform(2,4),gv=False,sh=3))
        for p in self.pts:p.draw(screen)

        screen.blit(f12.render("SUPER GAME APP",True,(70,80,130)),(SW//2-55,155))
        t1=f40.render("Water Sort",True,(220,230,255));screen.blit(t1,(SW//2-t1.get_width()//2,175))
        t2=f26.render("Puzzle",True,(70,150,230));screen.blit(t2,(SW//2-t2.get_width()//2,225))

        preview=[[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4]]
        sp=BW+12;ptw=len(preview)*sp-12;psx=(SW-ptw)//2
        for i,pt in enumerate(preview):
            tx=psx+i*sp;ty=310+int(math.sin(self.mt*2+i*1.1)*8)
            screen.blit(BOTTLE_C,(tx-B_PAD,ty-B_PAD))
            draw_liquid(screen,tx,ty+CH+NH,pt)

        mouse=pygame.mouse.get_pos()
        pr=pygame.Rect(SW//2-105,560,210,56);hov=pr.collidepoint(mouse)
        pc=(50,180,100) if not hov else (65,200,115)
        pygame.draw.rect(screen,(0,0,0,40),(pr.x+2,pr.y+4,210,56),border_radius=28)
        btn=A(210,56);lt=br(pc,20);dkk=dk(pc,10)
        for row in range(56):
            t=row/55
            pygame.draw.line(btn,(int(lt[0]*(1-t)+dkk[0]*t),int(lt[1]*(1-t)+dkk[1]*t),int(lt[2]*(1-t)+dkk[2]*t),240),(0,row),(209,row))
        mask=A(210,56);pygame.draw.rect(mask,(255,255,255),(0,0,210,56),border_radius=28)
        btn.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(btn,pr.topleft);pygame.draw.rect(screen,br(pc,40),pr,1,border_radius=28)
        pt_=f20.render("P L A Y",True,(255,255,255))
        screen.blit(pt_,(pr.centerx-pt_.get_width()//2,pr.centery-pt_.get_height()//2))

        screen.blit(f14.render(f"Level {self.lv}",True,(100,110,155)),(SW//2-30,635))
        screen.blit(COIN_IMG,(SW//2-30,660))
        screen.blit(f14.render(str(self.coins),True,(255,220,50)),(SW//2-4,663))
        screen.blit(f8.render("Tap PLAY to start",True,(45,50,75)),(SW//2-45,SH-28))
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
                        if play_r and play_r.collidepoint(mouse):S_TAP.play();self.load(self.lv)
                    elif self.state=="play" and not self.pa:
                        btn_hit=False
                        for r,name in self._btns:
                            if r.collidepoint(mouse):
                                if name=="undo":self.do_undo()
                                elif name=="hint":self.get_hint()
                                elif name=="add":self.add_tube()
                                btn_hit=True;break
                        if not btn_hit:
                            ci=self.tube_at(*mouse)
                            if ci>=0:
                                S_TAP.play()
                                if self.sel==-1:
                                    if self.tubes[ci]:self.sel=ci;self.sel_b={}
                                elif self.sel==ci:self.sel=-1
                                else:
                                    if self.can_pour(self.sel,ci):
                                        s=self.sel;self.sel=-1;self.start_pour(s,ci)
                                    elif self.tubes[ci]:self.sel=ci;self.sel_b={}
                                    else:self.sel=-1
                    elif self.state=="win":
                        if next_r and next_r.collidepoint(mouse):S_TAP.play();self.load(self.lv+1)
                        elif rep_r and rep_r.collidepoint(mouse):S_TAP.play();self.load(self.lv)

            self.upd_pour(dt);self.pts=[p for p in self.pts if p.upd(dt)]
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

if __name__=="__main__":Game().run()
