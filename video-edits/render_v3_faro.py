"""Headlight-tab repair: voice-over + synced captions + footage call-outs + animated explainer inserts.

usage: python3 -I render3.py OUT.mp4 [--preview u1,u2,...]
"""
import os, sys, json, math, subprocess
import numpy as np, cv2, soundfile as sf, scipy.signal as ss
S = "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad"
P = f"{S}/v3"
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
SPEED = {"F1": 1.0, "F2": 1.6, "F3": 1.25, "F4": 2.2, "F5": 1.2}
TAB = (590.0, 1060.0)       # broken tab position in the source frame
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
    if sid == "F1": pz = punch(uo, wt("F1", "pestaña"), 2.5)
    if sid == "F2": pz = punch(uo, wt("F2", "espátula"), 2.2)
    if sid == "F4": pz = punch(uo, wt("F4", "grosor"), 2.0)
    z += 0.16 * pz
    cx = lerp(W / 2, TAB[0] + 60, 0.5 + 0.5 * pz); cy = lerp(H / 2, TAB[1], 0.4 + 0.6 * pz)
    cw, ch = W / z, H / z
    cx = clamp(cx, cw / 2, W - cw / 2); cy = clamp(cy, ch / 2, H - ch / 2)
    return z, cx - cw / 2, cy - ch / 2

def apply_cam(img, z, x0, y0):
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def world_overlay(seg, uo):
    wo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(wo)
    sid = seg["id"]; x, y = TAB
    if sid == "F1":
        a = wt("F1", "pestaña") - 0.1
        if uo >= a:
            env = 1 - prog(uo, seg["start"] + seg["dur"] - 0.3, seg["start"] + seg["dur"])
            r = 70 + 3 * math.sin(uo * 7)
            sw = 360 * ease_out_cubic(prog(uo, a, a + 0.5))
            d.arc((x - r, y - r, x + r, y + r), -90, -90 + sw, fill=with_alpha(ORANGE, env), width=8)
            pw = (uo - a) % 1.0; r2 = r + 50 * pw
            d.ellipse((x - r2, y - r2, x + r2, y + r2), outline=(255, 255, 255, int(170 * (1 - pw) * env)), width=3)
            lp = ease_out_cubic(prog(uo, a + 0.3, a + 0.6))
            if lp > 0:
                p0 = (x - 20, y + r); p1 = (x - 60, y + 175)
                d.line([p0, (lerp(p0[0], p1[0], lp), lerp(p0[1], p1[1], lp))], fill=with_alpha(WHITE, env), width=4)
            pill(wo, x - 60, y + 210, "PESTAÑA ROTA", env * ease_out_cubic(prog(uo, a + 0.5, a + 0.8)), anchor="cm")
    if sid == "F2":
        a = wt("F2", "espátula") - 0.1; b = wt("F2", "y", 1) - 0.1 if len([w for w in SEG["F2"]["words"] if norm(w["w"]) == "y"]) > 1 else a + 3.2
        env = window(uo, a, b, 0.2, 0.3)
        if env > 0:
            sx, sy = 800, 1185
            lp = ease_out_cubic(prog(uo, a, a + 0.35))
            d.line([(sx, sy), (sx, lerp(sy, sy + 150, lp))], fill=with_alpha(WHITE, env), width=4)
            d.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), fill=with_alpha(ORANGE, env))
            pill(wo, sx, sy + 190, "ESPÁTULA = BASE PLANA", env * ease_out_cubic(prog(uo, a + 0.25, a + 0.55)), anchor="cm")
    return wo

def screen_overlay(seg, uo):
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(so)
    sid = seg["id"]; s0, s1 = seg["start"], seg["start"] + seg["dur"]
    if sid == "F1":
        out = prog(uo, s1 - 0.35, s1); oy = -ease_in_out(out) * 60; al = 1 - out
        kp = ease_out_cubic(prog(uo, 0.05, 0.45))
        paste(so, text_sprite("REPARACIÓN DE FAROS", F_XB, 30, fill=ORANGE, tracking=5), 78 - (1 - kp) * 40, 230 + oy, alpha=al * kp)
        d.rectangle((78, 280 + oy, 78 + 90 * kp, 286 + oy), fill=with_alpha(ORANGE, al * kp))
        for i, (txt, col, yy) in enumerate([("NO TIRES", WHITE, 310), ("EL FARO", ORANGE, 460)]):
            p = ease_out_expo(prog(uo, 0.12 + i * 0.16, 0.75 + i * 0.16))
            paste(so, text_sprite(txt, F_BLACK, 160, fill=col), 70, yy + oy + (1 - p) * 80, alpha=al * clamp(p * 1.6))
    if sid == "F2":
        a = wt("F2", "mismo") - 0.15
        card(so, uo, a, s1 - 0.1, "CLAVE", "Varilla del mismo plástico", "rod")
    if sid == "F3":
        card(so, uo, wt("F3", "capas") - 0.15, wt("F3", "burbujas") - 0.2, "TIP PRO", "Capas delgadas", "layers")
        card(so, uo, wt("F3", "burbujas") - 0.1, s1 - 0.1, "RESULTADO", "Sin burbujas = más fuerte", "check", accent=GREEN)
    if sid in ("F2", "F4"):
        sp = SPEED[sid]; env = window(uo, s0 + 0.2, s1 - 0.1, 0.3, 0.3)
        if env > 0:
            glass(so, (870, 400, 1020, 460), r=30, alpha=env)
            for k in range(2):
                bx = 895 + k * 24
                d.polygon([(bx, 415), (bx + 22, 430), (bx, 445)], fill=with_alpha(WHITE, env))
            paste(so, text_sprite(f"{sp:g}X".replace(".", ","), F_XB, 28, shadow=False), 950, 430, alpha=env, anchor="lm")
    if sid == "F4":
        card(so, uo, wt("F4", "grosor") - 0.15, wt("F4", "trabaja") - 0.1, "OJO", "Mismo grosor que la original", "layers")
        card(so, uo, wt("F4", "calienta") - 0.2, s1 - 0.1, "CUIDADO", "El calor deforma el plástico", "warn", accent=RED)
    if sid == "F5":
        card(so, uo, wt("F5", "aprietes") - 0.2, wt("F5", "revisa") - 0.1, "MONTAJE", "Apriete suave: es plástico", "bolt")
        card(so, uo, wt("F5", "revisa") - 0.1, wt("F5", "fracción") - 0.4, "AL TERMINAR", "Revisa la alineación de luces", "beam")
        a = wt("F5", "fracción") - 0.3
        if uo >= a:
            p1 = prog(uo, a, a + 0.45); p2 = prog(uo, a + 0.25, a + 0.7)
            e1, e2 = ease_out_expo(p1), ease_out_expo(p2)
            paste(so, text_sprite("REPARA", F_BLACK, 170, fill=WHITE), W / 2, 800, alpha=clamp(p1 * 2), scale=lerp(1.25, 1, e1), anchor="cm", blur=(1 - e1) * 10)
            paste(so, text_sprite("NO REEMPLACES", F_BLACK, 120, fill=ORANGE), W / 2, 960, alpha=clamp(p2 * 2), scale=lerp(1.25, 1, e2), anchor="cm", blur=(1 - e2) * 10)
            sp = ease_out_cubic(prog(uo, a + 0.7, a + 1.2))
            if sp > 0: paste(so, text_sprite("Guarda este video para tu próximo golpe", F_SB, 36, fill=(255, 255, 255, 235)), W / 2, 1080 + (1 - sp) * 20, alpha=sp, anchor="cm")
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
    if seg["id"] == "F5":
        a = wt("F5", "fracción") - 0.4
        scr = scr * (1 - 0.5 * ease_in_out(prog(uo, a, a + 0.5)))
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

def mg_why(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "¿POR QUÉ IMPORTA?", [("UN FARO", WHITE, 120), ("SUELTO", ORANGE, 120)])
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tv, td, tg = wl(seg, "vibra"), wl(seg, "desalinea"), wl(seg, "deslumbrando")
    ent = ease_out_cubic(prog(ul, 0.2, 0.7))
    # road
    hz = 800
    d.polygon([(470, hz), (610, hz), (1080, 1400), (0, 1400)], fill=(40, 46, 58, int(255 * ent)))
    for k in range(6):
        q0 = ((k / 6) + ul * 0.6) % 1; q1 = q0 + 0.07
        y0_, y1_ = lerp(hz, 1400, q0 ** 2), lerp(hz, 1400, min(q1, 1) ** 2)
        d.polygon([(540 - lerp(2, 14, q0 ** 2), y0_), (540 + lerp(2, 14, q0 ** 2), y0_), (540 + lerp(2, 14, min(q1, 1) ** 2), y1_), (540 - lerp(2, 14, min(q1, 1) ** 2), y1_)],
                  fill=(230, 230, 230, int(200 * ent)))
    # beam
    vib = 6 * math.sin(ul * 38) * ease_out_cubic(prog(ul, tv - 0.1, tv + 0.3)) * (1 - prog(ul, td + 0.6, td + 1.0))
    tilt = -150 * ease_in_out(prog(ul, td - 0.1, td + 0.5))
    hx, hy = 260, 1330
    tip_y = 930 + tilt + vib * 6
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(beam).polygon([(hx - 30, hy - 20), (hx + 30, hy + 10), (700, tip_y + 120), (560, tip_y - 30)], fill=(255, 226, 140, int(110 * ent)))
    beam = beam.filter(ImageFilter.GaussianBlur(14)); lay.alpha_composite(beam)
    d = ImageDraw.Draw(lay)
    d.ellipse((hx - 46, hy - 30 + vib, hx + 46, hy + 30 + vib), fill=(255, 240, 190, int(255 * ent)))
    # oncoming car
    cx, cy = 640, 905
    d.rounded_rectangle((cx - 60, cy - 30, cx + 60, cy + 30), 12, fill=(70, 78, 92, int(255 * ent)))
    d.rounded_rectangle((cx - 42, cy - 52, cx + 42, cy - 22), 10, fill=(110, 120, 140, int(255 * ent)))
    gp = ease_out_back(prog(ul, tg - 0.1, tg + 0.35))
    if gp > 0:
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        for k in range(12):
            ang = k * math.pi / 6 + ul
            gd.line([(cx, cy - 40), (cx + math.cos(ang) * 120 * gp, cy - 40 + math.sin(ang) * 120 * gp)], fill=(255, 245, 200, 200), width=6)
        gd.ellipse((cx - 50 * gp, cy - 90 * gp, cx + 50 * gp, cy + 10 * gp), fill=(255, 250, 220, 230))
        glow = glow.filter(ImageFilter.GaussianBlur(6)); lay.alpha_composite(glow)
    cv.alpha_composite(lay)
    for k, (tw_, txt, col) in enumerate([(tv, "VIBRA", ORANGE), (td, "SE DESALINEA", ORANGE), (tg, "DESLUMBRA", RED)]):
        pill(cv, 980, 1060 + k * 92, txt, clamp(prog(ul, tw_ - 0.12, tw_ + 0.1)), fill=col, anchor="rm")
    return cv

def mg_plastic(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "EL SECRETO", [("MISMO", WHITE, 120), ("PLÁSTICO", ORANGE, 120)])
    d = ImageDraw.Draw(cv)
    codes = [("PP", wl(seg, "pp")), ("ABS", wl(seg, "abs")), ("PC", wl(seg, "pc"))]
    for k, (c, t0) in enumerate(codes):
        p = ease_out_back(prog(ul, t0 - 0.1, t0 + 0.25))
        if p <= 0: continue
        cx = 220 + k * 320; cy = 760
        w2, h2 = 130 * p, 70 * p
        d.rounded_rectangle((cx - w2, cy - h2, cx + w2, cy + h2), int(22 * p), fill=(30, 36, 48, 255), outline=(255, 255, 255, 120), width=3)
        paste(cv, text_sprite(f">{c}<", F_BLACK, 64, fill=WHITE, shadow=False), cx, cy, scale=max(p, .01), anchor="cm")
    tm, tf, tr = wl(seg, "mezclas"), wl(seg, "fusionan"), wl(seg, "romper")
    rows = [(1010, (34, 165, 146), (34, 165, 146), "PP + PP", True), (1240, (34, 165, 146), (150, 90, 210), "PP + ABS", False)]
    for k, (y, c1, c2, lab, good) in enumerate(rows):
        ent = ease_out_cubic(prog(ul, tm - 0.2 + k * 0.15, tm + 0.3 + k * 0.15))
        if ent <= 0: continue
        join = ease_in_out(prog(ul, tm + 0.2, tf - 0.1))
        gap = lerp(120, 0, join)
        al = int(255 * ent)
        d.rounded_rectangle((120, y - 50, 420 - gap / 2, y + 50), 14, fill=c1 + (al,))
        d.rounded_rectangle((420 + gap / 2, y - 50, 720, y + 50), 14, fill=c2 + (al,))
        paste(cv, text_sprite(lab, F_XB, 34, shadow=False), 420, y, alpha=ent, anchor="cm")
        res = prog(ul, (tf if good else tr) - 0.1, (tf if good else tr) + 0.2)
        if not good and res > 0:
            d.line([(420, y - 58), (408, y - 20), (432, y + 10), (414, y + 58)], fill=(255, 255, 255, int(255 * res)), width=6)
        if res > 0:
            col = GREEN if good else RED
            d.ellipse((780, y - 46, 872, y + 46), fill=with_alpha(col, res))
            icon(d, "check" if good else "x", 826, y, 60, with_alpha(WHITE, res))
            paste(cv, text_sprite("SE FUSIONA" if good else "SE SEPARA", F_XB, 30, fill=col, shadow=False), 826, y + 82, alpha=res, anchor="cm")
    return cv

def mg_thickness(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "LA CLAVE", [("EL GROSOR", WHITE, 120)])
    d = ImageDraw.Draw(cv)
    items = [(16, "MUY DELGADA", wl(seg, "delgada"), "thin"), (78, "MUY GRUESA", wl(seg, "gruesa"), "thick"), (40, "IGUAL A LA\nORIGINAL", wl(seg, "igual"), "ok")]
    for k, (th, lab, t0, kind) in enumerate(items):
        cx = 190 + k * 350; base_y = 1000
        ent = ease_out_cubic(prog(ul, 0.3 + k * 0.12, 0.8 + k * 0.12))
        if ent <= 0: continue
        act = prog(ul, t0 - 0.1, t0 + 0.25)
        dim = 0.45 + 0.55 * act
        a = int(255 * ent * dim)
        glass(cv, (cx - 150, 640, cx + 150, 1300), r=34, alpha=ent * (0.6 + 0.4 * act),
              border=((GREEN if kind == "ok" else RED)[:3] + (int(200 * act),)) if act > 0 else (255, 255, 255, 50))
        d = ImageDraw.Draw(cv)
        # headlight housing above
        hy = base_y - 150 - (40 if kind == "thick" else 0) * act
        d.rounded_rectangle((cx - 110, hy - 70, cx + 110, hy), 18, fill=(70, 78, 92, a))
        d.ellipse((cx - 40, hy - 60, cx + 40, hy - 10), fill=(255, 240, 190, a))
        # tab profile
        d.rounded_rectangle((cx - 110, base_y - th, cx + 60, base_y), 8, fill=(25, 27, 31, a), outline=(110, 116, 128, a), width=3)
        d.ellipse((cx - 20, base_y - th / 2 - 9, cx + 0, base_y - th / 2 + 9), fill=(70, 78, 92, a))
        d.rectangle((cx - 120, base_y, cx + 120, base_y + 40), fill=(150, 156, 166, a))
        if kind == "thin" and act > 0:
            d.line([(cx + 10, base_y - th - 6), (cx + 22, base_y - th / 2), (cx + 8, base_y + 4)], fill=with_alpha(RED, act), width=5)
        if kind == "thick" and act > 0:
            d.line([(cx + 85, hy + 6), (cx + 85, base_y - th - 6)], fill=with_alpha(RED, act), width=4)
            d.polygon([(cx + 75, hy + 18), (cx + 95, hy + 18), (cx + 85, hy + 4)], fill=with_alpha(RED, act))
            d.polygon([(cx + 75, base_y - th - 18), (cx + 95, base_y - th - 18), (cx + 85, base_y - th - 4)], fill=with_alpha(RED, act))
        col = GREEN if kind == "ok" else RED
        if act > 0:
            d.ellipse((cx - 40, 1100, cx + 40, 1180), fill=with_alpha(col, act))
            icon(d, "check" if kind == "ok" else "x", cx, 1140, 52, with_alpha(WHITE, act))
        for li, ln in enumerate(lab.split("\n")):
            paste(cv, text_sprite(ln, F_XB, 28, fill=WHITE if act > 0 else (200, 205, 215, 255), shadow=False), cx, 1215 + li * 34, alpha=ent * dim, anchor="cm")
    return cv

MG = {"why": mg_why, "plastic": mg_plastic, "thickness": mg_thickness}

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
