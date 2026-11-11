"""Horizontal grinder: voice-over + synced captions + footage call-outs + animated explainer inserts.

usage: python3 -I render3.py OUT.mp4 [--preview u1,u2,...]
"""
import os, sys, json, math, subprocess
import numpy as np, cv2, soundfile as sf, scipy.signal as ss
S = "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad"
P = f"{S}/v5"
sys.path.insert(0, S)
from lib import (W, H, Image, ImageDraw, ImageFilter, font, text_sprite, paste, glass, with_alpha, grade, VIG,
                 clamp, prog, ease_out_cubic, ease_in_out, ease_out_back, ease_out_expo, lerp, window,
                 ORANGE, WHITE, F_BLACK, F_XB, F_SB)

OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
SRC = f"{P}/in/raw.mp4"
SFPS = 30.0
OFPS = 30
LEAD, TAIL = 0.25, 0.35
SR = 48000
SPEED = {"F1": 1.0, "F2": 1.0}
TAB = (560.0, 760.0)        # zoom focus (hopper)
GREEN = (46, 196, 140, 255)
RED = (235, 64, 52, 255)

SCRIPT = json.load(open(f"{P}/script.json"))
TIM = json.load(open(f"{P}/vo/timing.json"))

# ---------------------------------------------------------------- timeline
SEGS, u = [], 0.0
for sc in SCRIPT:
    vd = TIM[sc["id"]]["dur"]
    seg = dict(sc)
    if sc["type"] == "foot":
        sd = sc["src"][1] - sc["src"][0]
        od = max(sd / SPEED[sc["id"]], LEAD + vd + TAIL)
        seg["rate"] = sd / od
    else:
        od = LEAD + vd + 0.6 + (1.3 if sc is SCRIPT[-1] else 0)
    seg["start"], seg["dur"], seg["vo_start"] = u, od, u + LEAD
    seg["words"] = [dict(w, s=w["s"] + u + LEAD, e=w["e"] + u + LEAD) for w in TIM[sc["id"]]["words"]]
    SEGS.append(seg); u += od
TOTAL = u
SEG = {s["id"]: s for s in SEGS}
BOUNDS = [s["start"] for s in SEGS[1:]]
print("total", round(TOTAL, 2), [(s["id"], round(s["start"], 2), round(s["dur"], 2), round(s.get("rate", 1), 2)) for s in SEGS], flush=True)

def norm(w): return "".join(c for c in w.lower() if c.isalnum())
def wt(seg_id, word, nth=0):
    hits = [w["s"] for w in SEG[seg_id]["words"] if norm(w["w"]) == word]
    return hits[nth]
def seg_at(uo): return next(s for s in SEGS[::-1] if uo >= s["start"])

# ---------------------------------------------------------------- captions
CAP_SIZE, CAP_MAXW, CAP_CX, CAP_Y = 64, 820, 515, 1480

def pages_for(seg):
    pages, cur = [], []
    for w in seg["words"]:
        cur.append(w)
        txt = " ".join(x["w"].replace("*", "") for x in cur)
        if len(txt) >= 24 or w["w"].rstrip("*")[-1:] in ",.:…?":
            pages.append(cur); cur = []
    if cur: pages.append(cur)
    out = []
    for i, p in enumerate(pages):
        a = p[0]["s"] - 0.06
        b = pages[i + 1][0]["s"] - 0.06 if i + 1 < len(pages) else p[-1]["e"] + 0.45
        out.append((a, b, p))
    return out

def layout(words):
    f = font(F_XB, CAP_SIZE); space = f.getlength(" ") * 1.35 + 4
    items = [(w["w"].replace("*", ""), "*" in w["w"], f.getlength(w["w"].replace("*", "")), w) for w in words]
    lines, cur, cw = [], [], 0
    for it in items:
        if cur and cw + space + it[2] > CAP_MAXW:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + it[2]; cur.append(it)
    lines.append((cur, cw))
    out = []
    for li, (ws, lw) in enumerate(lines):
        x = CAP_CX - lw / 2
        for txt, kw, ww, w in ws:
            out.append((txt, kw, x + ww / 2, CAP_Y + li * CAP_SIZE * 1.2, ww, w)); x += ww + space
    return out

PAGE_LAYOUT = [(a, b, layout(p)) for s in SEGS for a, b, p in pages_for(s)]

def draw_captions(cv, uo):
    d = ImageDraw.Draw(cv)
    for a, b, items in PAGE_LAYOUT:
        if not (a <= uo < b): continue
        env = min(prog(uo, a, a + 0.08), 1 - prog(uo, b - 0.08, b)) if b - a > 0.2 else 1
        for idx, (txt, kw, cx, cy, ww, w) in enumerate(items):
            if uo < w["s"] - 0.04: continue
            nxt = items[idx + 1][5]["s"] - 0.04 if idx + 1 < len(items) else w["e"] + 0.15
            p = prog(uo, w["s"] - 0.04, w["s"] + 0.14)
            sc = 0.6 + 0.4 * (ease_out_back(p, 2.2) if p < 1 else 1)
            if w["s"] - 0.04 <= uo < nxt:
                pw = ww * sc / 2 + 16
                d.rounded_rectangle((cx - pw, cy - CAP_SIZE * 0.62, cx + pw, cy + CAP_SIZE * 0.55), 16, fill=with_alpha(ORANGE, env))
                paste(cv, text_sprite(txt, F_XB, CAP_SIZE, fill=WHITE, shadow=False), cx, cy, alpha=env, scale=sc * 1.04, anchor="cm")
            else:
                spr = text_sprite(txt, F_XB, CAP_SIZE, fill=ORANGE if kw else WHITE, stroke=6, stroke_fill=(0, 0, 0, 255))
                paste(cv, spr, cx, cy, alpha=env * clamp(p * 2.5), scale=sc, anchor="cm")

# ---------------------------------------------------------------- shared UI pieces
def pill(cv, x, y, txt, alpha, fill=ORANGE, size=30, anchor="lm", tcol=WHITE):
    if alpha <= 0.01: return
    spr = text_sprite(txt, F_XB, size, fill=tcol, tracking=2, shadow=False)
    bw = spr[0].width - 2 * spr[1]; w = bw + 48; h = size + 34
    x0 = x - {"l": 0, "c": w / 2, "r": w}[anchor[0]]
    glass(cv, (x0, y - h / 2, x0 + w, y + h / 2), r=h / 2, alpha=alpha, fill=fill[:3] + (235,), border=(255, 255, 255, 80))
    paste(cv, spr, x0 + 24, y, alpha=alpha, anchor="lm")

def icon(d, kind, cx, cy, s, col):
    if kind == "check":
        d.line([(cx - s * .45, cy), (cx - s * .12, cy + s * .32), (cx + s * .45, cy - s * .35)], fill=col, width=max(3, int(s * .16)), joint="curve")
    elif kind == "x":
        w = max(3, int(s * .16))
        d.line([(cx - s * .38, cy - s * .38), (cx + s * .38, cy + s * .38)], fill=col, width=w)
        d.line([(cx - s * .38, cy + s * .38), (cx + s * .38, cy - s * .38)], fill=col, width=w)
    elif kind == "warn":
        d.polygon([(cx, cy - s * .48), (cx + s * .52, cy + s * .42), (cx - s * .52, cy + s * .42)], fill=col)
        d.rectangle((cx - s * .05, cy - s * .18, cx + s * .05, cy + s * .14), fill=(20, 24, 30, 255))
        d.ellipse((cx - s * .06, cy + s * .22, cx + s * .06, cy + s * .34), fill=(20, 24, 30, 255))
    elif kind == "layers":
        for k in range(3):
            y = cy + s * .3 - k * s * .28
            d.rounded_rectangle((cx - s * .45, y - s * .1, cx + s * .45, y + s * .1), int(s * .08), fill=col)
    elif kind == "rod":
        d.rounded_rectangle((cx - s * .5, cy - s * .08, cx + s * .5, cy + s * .08), int(s * .08), fill=col)
        d.ellipse((cx + s * .3, cy - s * .2, cx + s * .56, cy + s * .2), fill=(255, 190, 90, 255))
    elif kind == "bolt":
        d.regular_polygon((cx, cy, s * .42), 6, fill=col)
        d.ellipse((cx - s * .16, cy - s * .16, cx + s * .16, cy + s * .16), fill=(20, 24, 30, 255))
    elif kind == "beam":
        d.ellipse((cx - s * .5, cy - s * .3, cx - s * .05, cy + s * .3), fill=col)
        for k in (-1, 0, 1):
            d.line([(cx + s * .02, cy + k * s * .2), (cx + s * .5, cy + k * s * .28)], fill=col, width=max(3, int(s * .1)))

def card(cv, uo, a, b, kicker, title, ic=None, y=210, accent=ORANGE):
    if not (a <= uo <= b): return
    env = window(uo, a, b, 0.25, 0.25)
    e = ease_out_back(prog(uo, a, a + 0.45), 1.4)
    x0 = 60 - (1 - e) * 520
    f = font(F_XB, 46)
    tw = f.getlength(title)
    x1 = x0 + 150 + tw + 50
    glass(cv, (x0, y, x1, y + 150), r=30, alpha=env)
    d = ImageDraw.Draw(cv)
    d.ellipse((x0 + 28, y + 30, x0 + 118, y + 120), fill=with_alpha(accent, env))
    if ic: icon(d, ic, x0 + 73, y + 75, 56, with_alpha(WHITE, env))
    paste(cv, text_sprite(kicker, F_XB, 24, fill=accent, tracking=4, shadow=False), x0 + 145, y + 30, alpha=env)
    paste(cv, text_sprite(title, F_XB, 46, shadow=False), x0 + 145, y + 66, alpha=env)

# ---------------------------------------------------------------- source frames
class Reader:
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", "fps=30,scale=1080:1920:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.idx, self.cur = -1, None
    def get(self, i):
        while self.idx < i:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break
            self.cur = np.frombuffer(buf, np.uint8).reshape(H, W, 3); self.idx += 1
        return self.cur
def seek_frame(i):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{i / SFPS:.3f}", "-i", SRC, "-vf", "scale=1080:1920:flags=lanczos", "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)
READER = None
def src_frame(t):
    i = int(t * SFPS)
    return READER.get(i) if READER else seek_frame(i)

# ---------------------------------------------------------------- footage
def punch(uo, tw, hold=2.0):
    return ease_out_expo(prog(uo, tw - 0.05, tw + 0.3)) * (1 - ease_in_out(prog(uo, tw + hold, tw + hold + 0.6)))

def camera(seg, uo):
    x = prog(uo, seg["start"], seg["start"] + seg["dur"])
    z = 1.0 + 0.05 * ease_in_out(x)
    pz = 0.0
    sid = seg["id"]
    if sid == "F1": pz = punch(uo, wt("F1", "valor"), 1.6)
    if sid == "F2": pz = punch(uo, wt("F2", "alimenta"), 1.2)
    z += 0.16 * pz
    cx = lerp(W / 2, TAB[0] + 60, 0.5 + 0.5 * pz); cy = lerp(H / 2, TAB[1], 0.4 + 0.6 * pz)
    cw, ch = W / z, H / z
    cx = clamp(cx, cw / 2, W - cw / 2); cy = clamp(cy, ch / 2, H - ch / 2)
    return z, cx - cw / 2, cy - ch / 2

def apply_cam(img, z, x0, y0):
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def world_overlay(seg, uo):
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def screen_overlay(seg, uo):
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(so)
    sid = seg["id"]; s0, s1 = seg["start"], seg["start"] + seg["dur"]
    if sid == "F1":
        out = prog(uo, s1 - 0.35, s1); oy = -ease_in_out(out) * 60; al = 1 - out
        kp = ease_out_cubic(prog(uo, 0.05, 0.45))
        paste(so, text_sprite("TRITURACIÓN DE MADERA", F_XB, 30, fill=ORANGE, tracking=5), 78 - (1 - kp) * 40, 230 + oy, alpha=al * kp)
        d.rectangle((78, 280 + oy, 78 + 90 * kp, 286 + oy), fill=with_alpha(ORANGE, al * kp))
        for i, (txt, col, yy_) in enumerate([("NO ES", WHITE, 310), ("BASURA", ORANGE, 460)]):
            p = ease_out_expo(prog(uo, 0.12 + i * 0.16, 0.75 + i * 0.16))
            paste(so, text_sprite(txt, F_BLACK, 170, fill=col), 70, yy_ + oy + (1 - p) * 80, alpha=al * clamp(p * 1.6))
    if sid == "F2":
        card(so, uo, wt("F2", "productividad") - 0.15, s1 - 0.1, "LA CLAVE", "Cómo se alimenta", "check", accent=GREEN, y=230)
    return so

def comp(base, layer):
    arr = np.asarray(layer).astype(np.float32) / 255
    return base * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]

def render_foot(seg, uo):
    t = seg["src"][0] + (uo - seg["start"]) * seg["rate"]
    world = grade(src_frame(t))
    world = comp(world, world_overlay(seg, uo))
    z, x0, y0 = camera(seg, uo)
    scr = apply_cam(world, z, x0, y0) * VIG
    return comp(scr, screen_overlay(seg, uo))

# ---------------------------------------------------------------- MG scenes
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BG = np.dstack([lerp(11, 17, yy / H), lerp(18, 28, yy / H), lerp(32, 46, yy / H)]) / 255
BG = np.clip(BG + ((xx % 54 < 3) & (yy % 54 < 3)).astype(np.float32)[..., None] * 0.05, 0, 1).astype(np.float32)
NAVY = (13, 20, 34)

def mg_base(ul):
    cx = W * (0.3 + 0.15 * math.sin(ul * 0.6))
    g = np.exp(-(((xx - cx) / 520) ** 2 + ((yy - H * .45) / 700) ** 2))[..., None]
    return Image.fromarray((np.clip(BG + g * np.array([0.10, 0.06, 0.02], np.float32), 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def mg_title(cv, ul, kicker, lines, y0=300):
    kp = ease_out_cubic(prog(ul, 0.0, 0.4))
    paste(cv, text_sprite(kicker, F_XB, 30, fill=ORANGE, tracking=5, shadow=False), 90 - (1 - kp) * 40, y0, alpha=kp)
    ImageDraw.Draw(cv).rectangle((90, y0 + 48, 90 + 90 * kp, y0 + 54), fill=with_alpha(ORANGE, kp))
    y = y0 + 75
    for i, (txt, col, size) in enumerate(lines):
        p = ease_out_expo(prog(ul, 0.1 + i * 0.12, 0.7 + i * 0.12))
        paste(cv, text_sprite(txt, F_BLACK, size, fill=col), 86, y + (1 - p) * 60, alpha=clamp(p * 1.5))
        y += size

def wl(seg, word, nth=0): return wt(seg["id"], word, nth) - seg["start"]

BROWN = (150, 96, 52)
STEEL = (150, 156, 166)

def rotor_draw(d, cx, cy, r, ang, a, hammers=6, tooth_hl=-1, hl=0.0):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(70, 76, 88, a), outline=STEEL + (a,), width=6)
    d.ellipse((cx - r * .25, cy - r * .25, cx + r * .25, cy + r * .25), fill=STEEL + (a,))
    for k in range(hammers):
        th = ang + k * 2 * math.pi / hammers
        px, py = cx + r * .92 * math.cos(th), cy + r * .92 * math.sin(th)
        col = (255, 122, 26) if k != tooth_hl else tuple(int(lerp(c, h, hl)) for c, h in zip((255, 122, 26), (235, 40, 40)))
        w = r * .16
        pts = [(px + w * math.cos(th + q), py + w * math.sin(th + q)) for q in (0.8, 2.3, 3.9, 5.4)]
        d.polygon(pts, fill=col + (a,))
        d.line([(cx + r * .25 * math.cos(th), cy + r * .25 * math.sin(th)), (px, py)], fill=STEEL + (a,), width=int(r * .08))

def branch(d, x, y, s, a, seed=0):
    d.line([(x, y), (x + 120 * s, y - 8 * s)], fill=BROWN + (a,), width=int(9 * s))
    for k in range(3):
        bx = x + (25 + 30 * k) * s
        d.line([(bx, y - 4 * s), (bx + 26 * s, y - (26 + 6 * ((k + seed) % 2)) * s)], fill=BROWN + (a,), width=int(5 * s))

def mg_rotor(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "CÓMO FUNCIONA", [("TRITURADORA", WHITE, 100), ("HORIZONTAL", ORANGE, 100)])
    d = ImageDraw.Draw(cv)
    ent = ease_out_cubic(prog(ul, 0.3, 0.8)); a = int(255 * ent)
    tr, tc = wl(seg, "rotor"), wl(seg, "criba")
    RX, RY, RR = 760, 1010, 150
    # feed belt
    d.rounded_rectangle((50, 1040, 600, 1080), 20, fill=(40, 44, 52, a))
    for k in range(12):
        cx_ = 60 + ((k * 50 + ul * 140) % 540)
        d.rectangle((cx_, 1032, cx_ + 10, 1042), fill=STEEL + (a,))
    for k in range(4):
        bx = ((k * 150 + ul * 140) % 600) - 120
        if bx < 500: branch(d, bx, 1028, 1.0, a, k)
    # feed roller
    fr = 52; fa = -ul * 3
    d.ellipse((560 - fr, 980 - fr, 560 + fr, 980 + fr), fill=(90, 96, 108, a))
    for k in range(8):
        th = fa + k * math.pi / 4
        d.polygon([(560 + fr * math.cos(th - .2), 980 + fr * math.sin(th - .2)), (560 + (fr + 16) * math.cos(th), 980 + (fr + 16) * math.sin(th)),
                   (560 + fr * math.cos(th + .2), 980 + fr * math.sin(th + .2))], fill=STEEL + (a,))
    # housing + screen
    d.arc((RX - RR - 34, RY - RR - 34, RX + RR + 34, RY + RR + 34), 190, 350, fill=(110, 116, 128, a), width=14)
    sp = ease_out_cubic(prog(ul, tc - 0.2, tc + 0.3))
    scol = (255, 122, 26) if sp > 0 else (110, 116, 128)
    for k in range(14):
        a0 = 15 + k * 11
        d.arc((RX - RR - 30, RY - RR - 30, RX + RR + 30, RY + RR + 30), a0, a0 + 7, fill=scol + (a,), width=12)
    rotor_draw(d, RX, RY, RR, ul * 9, a)
    # chips
    for j in range(int(ul / 0.03)):
        age = ul - j * 0.03
        if age > 0.9 or ul < 0.6: continue
        x = RX - 110 + (j * 37 % 220); y = RY + RR + 40 + 260 * age ** 1.6
        if y > 1360: continue
        s_ = 5 + (j % 3) * 2
        d.rectangle((x - s_, y - s_, x + s_, y + s_), fill=(196, 140, 80, a))
    d.rounded_rectangle((560, 1360, 1030, 1392), 16, fill=(40, 44, 52, a))
    # labels
    lp = ease_out_cubic(prog(ul, tr - 0.1, tr + 0.25))
    if lp > 0:
        d.line([(RX, RY - RR - 40), (RX, RY - RR - 40 - 50 * lp)], fill=(255, 255, 255, int(200 * lp)), width=3)
        pill(cv, RX, RY - RR - 120, "ROTOR CON MARTILLOS", lp, anchor="cm")
    if sp > 0:
        d.line([(RX - RR - 20, RY + 110), (RX - RR - 140 * sp, RY + 170)], fill=(255, 255, 255, int(200 * sp)), width=3)
        pill(cv, RX - RR - 130, RY + 185, "CRIBA = TAMAÑO", sp, anchor="rm")
    for k, wname in enumerate(["astilla", "mulch", "biomasa"]):
        p = clamp(prog(wl(seg, wname) - 0.1, 0, 1) if False else prog(ul, wl(seg, wname) - 0.1, wl(seg, wname) + 0.15))
        pill(cv, [60, 248, 418][k], 1320, wname.upper(), p, fill=(46, 140, 100, 255) if k == 1 else ORANGE, size=26)
    return cv

def gauge(cv, d, gx, gy, gr, val, a, label):
    d.arc((gx - gr, gy - gr, gx + gr, gy + gr), 180, 250, fill=(235, 64, 52, a), width=22)
    d.arc((gx - gr, gy - gr, gx + gr, gy + gr), 250, 360, fill=(46, 196, 140, a), width=22)
    ang = math.pi * (1 + clamp(val, 0, 1))
    d.line([(gx, gy), (gx + (gr - 26) * math.cos(ang), gy + (gr - 26) * math.sin(ang))], fill=(255, 255, 255, a), width=7)
    d.ellipse((gx - 13, gy - 13, gx + 13, gy + 13), fill=(255, 255, 255, a))
    paste(cv, text_sprite(label, F_XB, 24, fill=(220, 225, 235, 255), tracking=3, shadow=False), gx, gy + 34, alpha=a / 255, anchor="cm")

def mg_feed(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "LA CLAVE", [("ALIMENTACIÓN", WHITE, 100)])
    d = ImageDraw.Draw(cv)
    ts, tv, tm = wl(seg, "saturas"), wl(seg, "revoluciones"), wl(seg, "menos")
    panels = [(60, "PAREJA Y CONSTANTE", True, 0.3), (560, "SATURADA", False, ts - 0.15)]
    for x0, lab, good, t0 in panels:
        ent = ease_out_cubic(prog(ul, t0, t0 + 0.4))
        if ent <= 0: continue
        a = int(255 * ent); col = GREEN if good else RED
        glass(cv, (x0, 620, x0 + 460, 1340), r=30, alpha=ent, border=col[:3] + (180,))
        d = ImageDraw.Draw(cv)
        paste(cv, text_sprite(lab, F_XB, 30, fill=col, tracking=2, shadow=False), x0 + 230, 670, alpha=ent, anchor="cm")
        # material stream
        if good:
            for k in range(6):
                bx = x0 + 30 + ((k * 70 + ul * 120) % 400)
                d.rounded_rectangle((bx, 770, bx + 40, 800), 8, fill=BROWN + (a,))
        else:
            for k in range(18):
                bx = x0 + 40 + (k * 53) % 360; by = 800 - (k // 6) * 30 - 10 * math.sin(k)
                d.rounded_rectangle((bx, by - 15, bx + 60, by + 15), 8, fill=BROWN + (a,))
        d.rectangle((x0 + 30, 810, x0 + 430, 820), fill=(80, 86, 96, a))
        if good: val = 0.85 + 0.02 * math.sin(ul * 9)
        else: val = lerp(0.85, 0.2, ease_in_out(prog(ul, tv - 0.3, tv + 0.4))) + 0.03 * math.sin(ul * 23)
        gauge(cv, d, x0 + 230, 1050, 140, val, a, "RPM DEL ROTOR")
        prod = 1.0 if good else lerp(1.0, 0.3, ease_in_out(prog(ul, tm - 0.3, tm + 0.3)))
        paste(cv, text_sprite("PRODUCCIÓN", F_XB, 24, fill=(220, 225, 235, 255), tracking=3, shadow=False), x0 + 40, 1160, alpha=ent)
        d.rounded_rectangle((x0 + 40, 1200, x0 + 420, 1230), 15, fill=(255, 255, 255, int(40 * ent)))
        d.rounded_rectangle((x0 + 40, 1200, x0 + 40 + 380 * prod, 1230), 15, fill=col[:3] + (a,))
        r_ = prog(ul, (1.0 if good else tm - 0.1), (1.3 if good else tm + 0.2))
        if r_ > 0:
            d.ellipse((x0 + 190, 1258, x0 + 270, 1338), fill=with_alpha(col, r_ * ent))
            icon(d, "check" if good else "x", x0 + 230, 1298, 50, with_alpha(WHITE, r_ * ent))
    return cv

def mg_contam(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "CUIDADO", [("ENEMIGOS", WHITE, 100), ("DEL ROTOR", ORANGE, 100)])
    d = ImageDraw.Draw(cv)
    ent = ease_out_cubic(prog(ul, 0.3, 0.8)); a = int(255 * ent)
    RX, RY, RR = 700, 960, 150
    td, tr = wl(seg, "dientes"), wl(seg, "raíces")
    hl = prog(ul, td - 0.1, td + 0.3) * (0.6 + 0.4 * math.sin(ul * 12))
    rotor_draw(d, RX, RY, RR, ul * 7, a, tooth_hl=0, hl=hl)
    items = [("piedras", "PIEDRAS", 0), ("tierra", "TIERRA", 1), ("metal", "METAL", 2)]
    for k, (w, lab, kind) in enumerate(items):
        t0 = wl(seg, w) - 0.15
        p = prog(ul, t0, t0 + 0.55)
        if p <= 0: continue
        sy = 760 + k * 190
        x = lerp(150, RX - RR - 10, ease_in_out(p)); y = lerp(sy, RY, ease_in_out(p) ** 2)
        if p < 1:
            if kind == 0:
                d.polygon([(x - 34, y), (x - 10, y - 30), (x + 28, y - 22), (x + 36, y + 14), (x, y + 30), (x - 26, y + 20)], fill=(130, 130, 136, 255))
            elif kind == 1:
                d.ellipse((x - 38, y - 24, x + 38, y + 24), fill=(110, 76, 44, 255))
                for q in range(5): d.ellipse((x - 25 + q * 12, y - 6 + (q % 2) * 10, x - 19 + q * 12, y + (q % 2) * 10), fill=(70, 48, 28, 255))
            else:
                d.regular_polygon((x, y, 30), 6, fill=(190, 196, 206, 255)); d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=NAVY + (255,))
        else:
            sp_ = prog(ul, t0 + 0.55, t0 + 0.9)
            if sp_ < 1:
                for q in range(10):
                    an = q * 0.63
                    r1, r2 = 10 + 60 * sp_, 30 + 90 * sp_
                    d.line([(RX - RR + r1 * math.cos(an), RY + r1 * math.sin(an)), (RX - RR + r2 * math.cos(an), RY + r2 * math.sin(an))],
                           fill=(255, 220, 120, int(255 * (1 - sp_))), width=5)
        lp = clamp(p * 3)
        paste(cv, text_sprite(lab, F_XB, 34, fill=WHITE, shadow=False), 90, sy - 70 if k else sy - 70, alpha=lp * (1 - 0.5 * prog(ul, t0 + 1.2, t0 + 1.6)))
    pt = ease_out_cubic(prog(ul, td - 0.1, td + 0.3))
    if pt > 0: pill(cv, RX, RY - RR - 70, "DESGASTE DE DIENTES", pt, fill=RED, anchor="cm")
    tp = ease_out_back(prog(ul, tr - 0.2, tr + 0.25), 1.4)
    if tp > 0:
        x0 = 60 - (1 - tp) * 400
        glass(cv, (x0, 1215, x0 + 960, 1345), r=30, alpha=clamp(tp), border=(46, 196, 140, 180))
        d = ImageDraw.Draw(cv)
        d.ellipse((x0 + 26, 1240, x0 + 106, 1320), fill=with_alpha(GREEN, clamp(tp)))
        icon(d, "check", x0 + 66, 1280, 50, with_alpha(WHITE, clamp(tp)))
        paste(cv, text_sprite("TIP", F_XB, 24, fill=GREEN, tracking=4, shadow=False), x0 + 130, 1245, alpha=clamp(tp))
        paste(cv, text_sprite("Sacude la tierra de las raíces", F_XB, 40, shadow=False), x0 + 130, 1278, alpha=clamp(tp))
    return cv

def use_icon(d, kind, cx, cy, a):
    if kind == "mulch":
        for k in range(14):
            x = cx - 60 + (k * 37) % 120; y = cy + 10 + (k * 23) % 40
            d.rectangle((x, y, x + 14, y + 8), fill=(196, 140, 80, a))
        d.ellipse((cx - 22, cy - 50, cx + 22, cy + 6), fill=(46, 170, 100, a)); d.line([(cx, cy - 46), (cx, cy + 10)], fill=(20, 90, 50, a), width=4)
    elif kind == "compost":
        d.polygon([(cx - 80, cy + 45), (cx, cy - 45), (cx + 80, cy + 45)], fill=(110, 76, 44, a))
        for k in range(3): d.arc((cx - 30 + k * 20, cy - 80 - k * 6, cx - 10 + k * 20, cy - 50 - k * 6), 200, 340, fill=(220, 225, 235, a), width=4)
    elif kind == "ganado":
        d.polygon([(cx - 80, cy - 5), (cx, cy - 65), (cx + 80, cy - 5)], fill=(200, 70, 50, a))
        d.rectangle((cx - 66, cy - 5, cx + 66, cy + 50), fill=(200, 70, 50, a))
        d.rectangle((cx - 22, cy + 5, cx + 22, cy + 50), fill=(240, 230, 210, a))
        d.line([(cx - 22, cy + 5), (cx + 22, cy + 50)], fill=(200, 70, 50, a), width=4); d.line([(cx + 22, cy + 5), (cx - 22, cy + 50)], fill=(200, 70, 50, a), width=4)
    else:
        d.polygon([(cx, cy - 70), (cx + 45, cy), (cx + 30, cy + 45), (cx - 30, cy + 45), (cx - 45, cy)], fill=(255, 122, 26, a))
        d.polygon([(cx, cy - 25), (cx + 22, cy + 15), (cx + 12, cy + 45), (cx - 12, cy + 45), (cx - 22, cy + 15)], fill=(255, 210, 90, a))

def mg_uses(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "DE RESIDUO A PRODUCTO", [("¿PARA QUÉ", WHITE, 100), ("SIRVE?", ORANGE, 100)])
    d = ImageDraw.Draw(cv)
    cells = [("mulch", "MULCH", "Jardinería y suelos"), ("compost", "COMPOST", "Abono orgánico"),
             ("ganado", "CAMA PARA GANADO", "Establos y corrales"), ("biomasa", "BIOMASA", "Combustible y energía")]
    for k, (kind, lab, sub) in enumerate(cells):
        t0 = wl(seg, kind) - 0.12
        p = ease_out_back(prog(ul, t0, t0 + 0.35), 1.5)
        if p <= 0: continue
        cx = 60 + (k % 2) * 500; cy = 650 + (k // 2) * 330
        al = clamp(p)
        glass(cv, (cx, cy + (1 - al) * 40, cx + 460, cy + 300 + (1 - al) * 40), r=30, alpha=al)
        d = ImageDraw.Draw(cv)
        use_icon(d, kind, cx + 230, cy + 105 + (1 - al) * 40, int(255 * al))
        paste(cv, text_sprite(lab, F_XB, 36, shadow=False), cx + 230, cy + 205 + (1 - al) * 40, alpha=al, anchor="cm")
        paste(cv, text_sprite(sub, F_SB, 26, fill=(205, 212, 222, 255), shadow=False), cx + 230, cy + 250 + (1 - al) * 40, alpha=al, anchor="cm")
    te = wl(seg, "ingreso") - 0.25
    if ul >= te - 0.3:
        dk = 0.75 * ease_in_out(prog(ul, te - 0.3, te + 0.2))
        ov = Image.new("RGBA", (W, H), (8, 12, 20, int(255 * dk))); cv.alpha_composite(ov)
        p1, p2 = prog(ul, te, te + 0.45), prog(ul, te + 0.25, te + 0.7)
        e1, e2 = ease_out_expo(p1), ease_out_expo(p2)
        paste(cv, text_sprite("NO ES BASURA", F_BLACK, 130, fill=WHITE), W / 2, 820, alpha=clamp(p1 * 2), scale=lerp(1.25, 1, e1), anchor="cm", blur=(1 - e1) * 10)
        paste(cv, text_sprite("ES INGRESO", F_BLACK, 150, fill=ORANGE), W / 2, 990, alpha=clamp(p2 * 2), scale=lerp(1.25, 1, e2), anchor="cm", blur=(1 - e2) * 10)
    return cv

MG = {"rotor": mg_rotor, "feed": mg_feed, "contam": mg_contam, "uses": mg_uses}

def render_mg(seg, uo):
    return np.asarray(MG[seg["scene"]](seg, uo - seg["start"]).convert("RGB")).astype(np.float32) / 255

# ---------------------------------------------------------------- frames
WT = 0.18
def whip(img, p, direction):
    img = np.roll(img, int(W * 0.55 * p) * (-1 if direction < 0 else 1), axis=1)
    k = int(1 + 140 * p)
    return cv2.blur(img, (k, 1)) if k > 1 else img

def frame(uo):
    seg = seg_at(uo)
    img = render_foot(seg, uo) if seg["type"] == "foot" else render_mg(seg, uo)
    for b in BOUNDS:
        if b - WT <= uo < b: img = whip(img, prog(uo, b - WT, b) ** 2, -1)
        elif b <= uo < b + WT: img = whip(img, (1 - prog(uo, b, b + WT)) ** 2, +1)
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw_captions(so, uo)
    img = comp(img, so)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

# ---------------------------------------------------------------- audio
def build_audio(path):
    orig = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, np.float32)
    n = int(round(TOTAL * SR)); bg = np.zeros(n, np.float32)
    def take(start_s, length, gain):
        seg = np.resize(np.roll(orig, -int(start_s * SR)), length) * gain
        f = min(int(0.04 * SR), length // 2); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        return seg
    for s in SEGS:
        i0 = int(s["start"] * SR); L = min(int(s["dur"] * SR), n - i0)
        bg[i0:i0 + L] += take(s["src"][0], L, 1.0) if s["type"] == "foot" else take(8.0, L, 0.5)
    bg *= 0.07 / (np.sqrt(np.mean(bg ** 2)) + 1e-9)
    vo = np.zeros(n, np.float32)
    for s in SEGS:
        v, _ = sf.read(f"{P}/vo/{s['id']}.wav", dtype="float32")
        i0 = int(s["vo_start"] * SR); L = min(len(v), n - i0); vo[i0:i0 + L] += v[:L]
    k = int(0.25 * SR)
    env = np.convolve((np.abs(vo) > 0.02).astype(np.float32), np.ones(k) / k, mode="same")
    env = np.convolve(np.clip(env * 3, 0, 1), np.ones(k) / k, mode="same")
    sos = ss.butter(2, [400, 5000], btype="band", fs=SR, output="sos")
    wh = np.zeros(n, np.float32); rng = np.random.default_rng(3)
    for b in BOUNDS:
        L = int(0.5 * SR); i0 = int((b - 0.3) * SR)
        seg = ss.sosfilt(sos, rng.standard_normal(L)).astype(np.float32) * np.sin(np.linspace(0, np.pi, L)) ** 3
        seg *= 0.10 / (np.abs(seg).max() + 1e-9); wh[i0:i0 + L] += seg[:max(0, min(L, n - i0))]
    mix = bg * (1.0 - 0.62 * env) + vo * 0.95 + wh
    fo = int(0.6 * SR); mix[-fo:] *= np.linspace(1, 0, fo)
    sf.write(path, np.clip(mix, -1, 1), SR)

if PREVIEW:
    for uo in PREVIEW:
        Image.fromarray(frame(uo)).save(f"{OUT}_{uo:05.2f}.jpg", quality=88)
    sys.exit()

READER = Reader()
wav = OUT + ".mix.wav"; build_audio(wav)
NF = int(round(TOTAL * OFPS))
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(OFPS), "-i", "-",
                        "-i", wav, "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
for j in range(NF):
    enc.stdin.write(frame(j / OFPS).tobytes())
    if j % 150 == 0: print("frame", j, "/", NF, flush=True)
enc.stdin.close(); enc.wait()
print("done", OUT)
