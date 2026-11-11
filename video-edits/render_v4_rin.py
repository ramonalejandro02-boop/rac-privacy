"""Alloy-wheel straightening: voice-over + synced captions + footage call-outs + animated explainer inserts.

usage: python3 -I render3.py OUT.mp4 [--preview u1,u2,...]
"""
import os, sys, json, math, subprocess
import numpy as np, cv2, soundfile as sf, scipy.signal as ss
S = "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad"
P = f"{S}/v4"
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
SPEED = {"F1": 1.0, "F2": 1.5, "F3": 2.5, "F4": 1.0}
TAB = (560.0, 800.0)        # zoom focus (press / rim lip)
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
        od = LEAD + vd + 0.6
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
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.idx, self.cur = -1, None
    def get(self, i):
        while self.idx < i:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break
            self.cur = np.frombuffer(buf, np.uint8).reshape(H, W, 3); self.idx += 1
        return self.cur
def seek_frame(i):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{i / SFPS:.3f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo",
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
    if sid == "F1": pz = punch(uo, wt("F1", "bien"), 1.5)
    if sid == "F2": pz = punch(uo, wt("F2", "prensa"), 2.2)
    if sid == "F4": pz = punch(uo, wt("F4", "balancea"), 1.8)
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

def list_card(cv, uo, a, b, title, items, y=210):
    """items: [(text, appear_time)]"""
    if not (a <= uo <= b): return
    env = window(uo, a, b, 0.25, 0.25)
    e = ease_out_back(prog(uo, a, a + 0.45), 1.4)
    x0 = 60 - (1 - e) * 560
    rowh = 80
    glass(cv, (x0, y, x0 + 760, y + 90 + rowh * len(items)), r=30, alpha=env)
    paste(cv, text_sprite(title, F_XB, 26, fill=ORANGE, tracking=4, shadow=False), x0 + 34, y + 30, alpha=env)
    d = ImageDraw.Draw(cv)
    for k, (txt, t0) in enumerate(items):
        p = ease_out_cubic(prog(uo, t0 - 0.1, t0 + 0.25))
        if p <= 0: continue
        cy = y + 112 + k * rowh
        d.ellipse((x0 + 34, cy - 22, x0 + 78, cy + 22), fill=with_alpha(RED, env * p))
        icon(d, "warn", x0 + 56, cy, 30, with_alpha(WHITE, env * p))
        paste(cv, text_sprite(txt, F_XB, 40, shadow=False), x0 + 100 + (1 - p) * 30, cy, alpha=env * p, anchor="lm")

def screen_overlay(seg, uo):
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(so)
    sid = seg["id"]; s0, s1 = seg["start"], seg["start"] + seg["dur"]
    if sid == "F1":
        out = prog(uo, s1 - 0.35, s1); oy = -ease_in_out(out) * 60; al = 1 - out
        kp = ease_out_cubic(prog(uo, 0.05, 0.45))
        paste(so, text_sprite("REPARACIÓN DE RINES", F_XB, 30, fill=ORANGE, tracking=5), 78 - (1 - kp) * 40, 230 + oy, alpha=al * kp)
        d.rectangle((78, 280 + oy, 78 + 90 * kp, 286 + oy), fill=with_alpha(ORANGE, al * kp))
        for i, (txt, col, yy_) in enumerate([("¿RIN", WHITE, 310), ("DOBLADO?", ORANGE, 460)]):
            p = ease_out_expo(prog(uo, 0.12 + i * 0.16, 0.75 + i * 0.16))
            paste(so, text_sprite(txt, F_BLACK, 160, fill=col), 70, yy_ + oy + (1 - p) * 80, alpha=al * clamp(p * 1.6))
    if sid == "F2":
        card(so, uo, wt("F2", "agriete") - 0.15, wt("F2", "el", 2) - 0.1, "EL CALOR", "Evita grietas, no endereza", "warn")
        card(so, uo, wt("F2", "prensa") - 0.15, s1 - 0.1, "LA CLAVE", "Presión exacta mientras gira", "check", accent=GREEN)
    if sid == "F3":
        list_card(so, uo, wt("F3", "cómo") - 0.1, s1 - 0.1, "SEÑALES DE RIN DOBLADO",
                  [("El volante vibra en carretera", wt("F3", "vibra")), ("Pierde aire sin estar ponchada", wt("F3", "aire"))])
    if sid in ("F2", "F3"):
        sp = SPEED[sid]; env = window(uo, s0 + 0.2, s1 - 0.1, 0.3, 0.3)
        if env > 0:
            glass(so, (870, 1290, 1020, 1350), r=30, alpha=env)
            for k in range(2):
                bx = 895 + k * 24
                d.polygon([(bx, 1305), (bx + 22, 1320), (bx, 1335)], fill=with_alpha(WHITE, env))
            paste(so, text_sprite(f"{sp:g}X".replace(".", ","), F_XB, 28, shadow=False), 950, 1320, alpha=env, anchor="lm")
    if sid == "F4":
        card(so, uo, wt("F4", "balancea") - 0.2, wt("F4", "guarda") - 0.1, "SIEMPRE AL FINAL", "Balanceo + prueba de fugas", "check", accent=GREEN)
        a = wt("F4", "guarda") - 0.2; b = SEG["F4"]["words"][-1]["e"] + 0.6
        if a <= uo <= b:
            env = 1 - prog(uo, b - 0.35, b)
            p1 = prog(uo, a, a + 0.45); p2 = prog(uo, a + 0.25, a + 0.7)
            e1, e2 = ease_out_expo(p1), ease_out_expo(p2)
            paste(so, text_sprite("REPARA", F_BLACK, 170, fill=WHITE), W / 2, 800, alpha=env * clamp(p1 * 2), scale=lerp(1.25, 1, e1), anchor="cm", blur=(1 - e1) * 10)
            paste(so, text_sprite("CON CRITERIO", F_BLACK, 120, fill=ORANGE), W / 2, 960, alpha=env * clamp(p2 * 2), scale=lerp(1.25, 1, e2), anchor="cm", blur=(1 - e2) * 10)
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
    if seg["id"] == "F4":
        a = wt("F4", "guarda") - 0.3; b = SEG["F4"]["words"][-1]["e"] + 0.6
        scr = scr * (1 - 0.5 * ease_in_out(prog(uo, a, a + 0.5)) * (1 - prog(uo, b - 0.4, b)))
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

def rim(d, cx, cy, r, a, spokes=5, rot=0.0, bump=0.0, col=(170, 176, 186)):
    pts = []
    for k in range(120):
        th = k / 120 * 2 * math.pi
        rr_ = r * (1 + bump * math.exp(-((math.atan2(math.sin(th - rot - 0.6), math.cos(th - rot - 0.6))) / 0.35) ** 2))
        pts.append((cx + rr_ * math.cos(th), cy + rr_ * math.sin(th)))
    d.polygon(pts, fill=col + (a,))
    d.ellipse((cx - r * .82, cy - r * .82, cx + r * .82, cy + r * .82), fill=(40, 46, 58, a))
    for k in range(spokes):
        th = rot + k * 2 * math.pi / spokes
        d.line([(cx, cy), (cx + r * .8 * math.cos(th), cy + r * .8 * math.sin(th))], fill=col + (a,), width=int(r * .16))
    d.ellipse((cx - r * .22, cy - r * .22, cx + r * .22, cy + r * .22), fill=col + (a,))
    d.ellipse((cx - r * .08, cy - r * .08, cx + r * .08, cy + r * .08), fill=(40, 46, 58, a))

def mg_heat(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "EL DETALLE QUE IMPORTA", [("CALOR", WHITE, 120), ("MEDIDO", ORANGE, 120)])
    d = ImageDraw.Draw(cv)
    tc, tm, tr = wl(seg, "color"), wl(seg, "mide"), wl(seg, "resistencia")
    heat = ease_in_out(prog(ul, tc - 1.2, tc + 0.3))
    for k, (name, steel) in enumerate([("ACERO", True), ("ALUMINIO", False)]):
        ent = ease_out_cubic(prog(ul, 0.3 + k * 0.15, 0.8 + k * 0.15))
        if ent <= 0: continue
        y = 720 + k * 170; a = int(255 * ent)
        base = (120, 126, 136) if steel else (196, 202, 212)
        col = tuple(int(lerp(c, h, heat)) for c, h in zip(base, (255, 110, 30))) if steel else base
        if steel and heat > 0.2:
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(glow).rounded_rectangle((100, y - 50, 640, y + 50), 20, fill=(255, 120, 30, int(150 * heat * ent)))
            cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22))); d = ImageDraw.Draw(cv)
        d.rounded_rectangle((110, y - 42, 630, y + 42), 16, fill=col + (a,))
        paste(cv, text_sprite(name, F_XB, 34, fill=WHITE, shadow=False), 660, y, alpha=ent, anchor="lm")
        if not steel and heat > 0.6:
            paste(cv, text_sprite("¡mismo color!", F_SB, 30, fill=(255, 200, 150, 255), shadow=False), 660, y + 44, alpha=prog(heat, 0.6, 1), anchor="lm")
    # gauge
    ge = ease_out_cubic(prog(ul, tm - 0.3, tm + 0.2))
    if ge > 0:
        gx, gy, gr = 540, 1300, 170
        a = int(255 * ge)
        d.arc((gx - gr, gy - gr, gx + gr, gy + gr), 180, 300, fill=(46, 196, 140, a), width=26)
        d.arc((gx - gr, gy - gr, gx + gr, gy + gr), 300, 360, fill=(235, 64, 52, a), width=26)
        val = lerp(0.1, 0.62, ease_in_out(prog(ul, tm, tr - 0.3))) + 0.35 * ease_out_back(prog(ul, tr - 0.3, tr + 0.2))
        ang = math.pi * (1 + clamp(val, 0, 1.0))
        d.line([(gx, gy), (gx + (gr - 30) * math.cos(ang), gy + (gr - 30) * math.sin(ang))], fill=(255, 255, 255, a), width=8)
        d.ellipse((gx - 16, gy - 16, gx + 16, gy + 16), fill=(255, 255, 255, a))
        paste(cv, text_sprite("TEMPERATURA", F_XB, 28, fill=(220, 225, 235, 255), tracking=3, shadow=False), gx, gy + 40, alpha=ge, anchor="cm")
        pr = prog(ul, tr - 0.1, tr + 0.2)
        if pr > 0:
            pill(cv, gx, gy - gr - 60, "PIERDE RESISTENCIA", pr, fill=RED, anchor="cm")
    return cv

def mg_passes(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "EL MÉTODO", [("POCO A POCO", WHITE, 110)])
    d = ImageDraw.Draw(cv)
    tp, tg = wl(seg, "pasadas"), wl(seg, "golpe")
    n_pass = 3; span = max(tg - 0.4 - tp, 1.5)
    k = clamp((ul - tp) / span * n_pass, 0, n_pass)
    bump = 0.13 * (1 - ease_in_out(clamp(k / n_pass)))
    ent = ease_out_cubic(prog(ul, 0.3, 0.8))
    rim(d, 330, 920, 200, int(255 * ent), rot=ul * 2.2, bump=bump)
    # press roller
    rx = 330 + 200 * (1 + bump * 0.2) + 40
    d.rounded_rectangle((rx - 10, 880, rx + 70, 960), 18, fill=(255, 122, 26, int(255 * ent)))
    d.polygon([(rx - 22, 920), (rx - 4, 904), (rx - 4, 936)], fill=(255, 122, 26, int(255 * ent)))
    # deviation meter
    mx0, my = 640, 760
    paste(cv, text_sprite("DESVIACIÓN", F_XB, 28, fill=(220, 225, 235, 255), tracking=3, shadow=False), mx0, my, alpha=ent)
    d.rounded_rectangle((mx0, my + 40, mx0 + 360, my + 72), 16, fill=(255, 255, 255, int(40 * ent)))
    lvl = bump / 0.13
    if lvl > 0.02:
        col = RED if lvl > 0.5 else ORANGE if lvl > 0.2 else GREEN
        d.rounded_rectangle((mx0, my + 40, mx0 + 360 * lvl, my + 72), 16, fill=with_alpha(col, ent))
    for j in range(n_pass):
        on = k >= j + 1
        cy = my + 140 + j * 70
        d.ellipse((mx0, cy - 22, mx0 + 44, cy + 22), fill=with_alpha(GREEN, ent) if on else (255, 255, 255, int(40 * ent)))
        if on: icon(d, "check", mx0 + 22, cy, 30, with_alpha(WHITE, ent))
        paste(cv, text_sprite(f"Pasada {j + 1}", F_XB, 34, fill=WHITE, shadow=False), mx0 + 64, cy, alpha=ent * (1 if on else .45), anchor="lm")
    # one-hit warning
    gp = ease_out_back(prog(ul, tg - 0.15, tg + 0.25))
    if gp > 0:
        glass(cv, (90, 1200, 990, 1340), r=30, alpha=clamp(gp), fill=(60, 16, 16, 200), border=(235, 64, 52, 200))
        d = ImageDraw.Draw(cv)
        d.ellipse((120, 1225, 210, 1315), fill=with_alpha(RED, clamp(gp)))
        icon(d, "x", 165, 1270, 56, with_alpha(WHITE, clamp(gp)))
        paste(cv, text_sprite("De un solo golpe = grietas", F_XB, 44, shadow=False), 240, 1270, alpha=clamp(gp), anchor="lm")
    return cv

def mg_cracks(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "OJO", [("¿REPARAR", WHITE, 110), ("O CAMBIAR?", ORANGE, 110)])
    d = ImageDraw.Draw(cv)
    tg, tc = wl(seg, "grietas"), wl(seg, "cambia")
    for k, (lab, good) in enumerate([("ORILLA DOBLADA", True), ("GRIETA EN RAYO", False)]):
        cx = 280 + k * 520; cy = 920
        ent = ease_out_cubic(prog(ul, 0.3 + k * 0.15, 0.8 + k * 0.15))
        if ent <= 0: continue
        act = prog(ul, (0.9 if good else tg - 0.1), (1.2 if good else tg + 0.25))
        rim(d, cx, cy, 170, int(255 * ent), rot=0.3, bump=0.08 if good else 0.0)
        if not good and act > 0:
            sx, sy = cx + 40, cy - 30
            d.line([(sx, sy), (sx + 20 * act, sy - 30 * act), (sx + 10 * act, sy - 55 * act), (sx + 35 * act, sy - 90 * act)], fill=with_alpha(RED, 1), width=7)
        res = prog(ul, (tc - 0.6 if good else tc - 0.1), (tc - 0.3 if good else tc + 0.2))
        col = GREEN if good else RED
        if res > 0:
            d.ellipse((cx - 44, cy + 200, cx + 44, cy + 288), fill=with_alpha(col, res))
            icon(d, "check" if good else "x", cx, cy + 244, 56, with_alpha(WHITE, res))
            paste(cv, text_sprite("SE REPARA" if good else "SE CAMBIA", F_BLACK, 48, fill=col, shadow=False), cx, cy + 335, alpha=res, anchor="cm")
        paste(cv, text_sprite(lab, F_XB, 30, fill=(220, 225, 235, 255), tracking=2, shadow=False), cx, cy - 215, alpha=ent, anchor="cm")
    return cv

MG = {"heat": mg_heat, "passes": mg_passes, "cracks": mg_cracks}

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
