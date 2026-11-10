"""Cinematic motion-graphics edit for a vertical work clip (no speech).

usage: python3 -I render.py SRC OUT [--preview t1,t2,...]
"""
import sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
SRC = os.environ.get("FX_SRC") or sys.argv[1]
OUT = os.environ.get("FX_OUT") or (sys.argv[2] if len(sys.argv) > 2 else "")
PREVIEW = None
if __name__ == "__main__" and len(sys.argv) > 3 and sys.argv[3] == "--preview":
    PREVIEW = [float(x) for x in sys.argv[4].split(",")]

SW, SH = 720, 1280
W, H = 1080, 1920
K = W / SW
FPS = 14999 / 500

ORANGE = (255, 122, 26, 255)
WHITE = (255, 255, 255, 255)
INK = (12, 16, 22)

FD = "/usr/share/fonts"
import glob
def font_path(name):
    m = [p for p in glob.glob("/usr/share/fonts/**/*", recursive=True) if p.lower().endswith(name.lower())]
    if not m:
        raise SystemExit("font not found " + name)
    return m[0]

F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease_out_cubic(x): return 1 - (1 - x) ** 3
def ease_in_out(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out_back(x, s=1.70158): return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def ease_out_expo(x): return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def lerp(a, b, x): return a + (b - a) * x
def window(t, a, b, fin=0.25, fout=0.25):
    """opacity envelope for an element visible in [a,b]"""
    return min(prog(t, a, a + fin), 1 - prog(t, b - fout, b))

# ---------------------------------------------------------------- load
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, SH, SW, 3)
N = len(frames)
DUR = N / FPS
print("frames", N, "dur", round(DUR, 2), flush=True)

# ---------------------------------------------------------------- tracking (floor region, away from the worker)
ry0, ry1, rx0, rx1 = 820, 1260, 0, 460
ref = cv2.cvtColor(frames[0], cv2.COLOR_RGB2GRAY)[ry0:ry1, rx0:rx1].astype(np.float32)
han = cv2.createHanningWindow((rx1 - rx0, ry1 - ry0), cv2.CV_32F)
offs = []
for f in frames:
    g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY)[ry0:ry1, rx0:rx1].astype(np.float32)
    (dx, dy), _ = cv2.phaseCorrelate(ref, g, han)
    offs.append((dx, dy))
offs = np.array(offs)
k = 9
pad = np.pad(offs, ((k // 2, k // 2), (0, 0)), mode="edge")
offs = np.stack([np.convolve(pad[:, j], np.ones(k) / k, mode="valid") for j in range(2)], 1)
SPOT0 = np.array([527.0, 757.0])
def spot(i):  # world (1080) coords of the corrosion spot
    return (SPOT0 + offs[min(i, N - 1)]) * K
print("track range", offs.min(0).round(1), offs.max(0).round(1), flush=True)

# ---------------------------------------------------------------- subject mask (everything that is not deck)
def fg_mask(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    teal = (h >= 26) & (h <= 100) & (s >= 25) & (v >= 45)
    fg = (~teal).astype(np.uint8)
    fg[:300] = 0
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
    keep = np.zeros(n, np.uint8)
    keep[1:] = (st[1:, cv2.CC_STAT_AREA] >= 2500)
    fg = keep[lab]
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    fg = cv2.dilate(fg, np.ones((3, 3), np.uint8))
    fg = cv2.resize(fg.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(fg, (0, 0), 1.6)

# ---------------------------------------------------------------- grade + vignette
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
VIG = (1 - 0.30 * np.clip(rr - 0.45, 0, 1) ** 1.6)[..., None].astype(np.float32)

def grade(f):
    x = f.astype(np.float32) / 255
    x = 0.5 + (x - 0.5) * 1.10                      # contrast
    gray = x.mean(2, keepdims=True)
    x = gray + (x - gray) * 1.10                     # saturation
    x = x * np.array([1.015, 1.0, 0.985], np.float32)  # warm a touch
    x = np.clip(x, 0, 1)
    x = cv2.resize(x, (W, H), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(x, (0, 0), 1.2)
    x = np.clip(x + (x - blur) * 0.45, 0, 1)          # mild sharpen after upscale
    return x

# ---------------------------------------------------------------- text helpers
_tc = {}
def text_sprite(txt, path, size, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0, 255),
                shadow=True, tracking=0):
    key = (txt, path, int(size), fill, stroke, shadow, tracking)
    if key in _tc:
        return _tc[key]
    f = font(path, size)
    if tracking:
        widths = [f.getlength(c) + tracking for c in txt]
        tw = int(sum(widths)) + 4
    else:
        tw = int(f.getlength(txt)) + 4
    asc, desc = f.getmetrics()
    pad = int(size * 0.35) + stroke
    im = Image.new("RGBA", (tw + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def draw(dd, col, sw):
        if tracking:
            x = pad
            for c, w in zip(txt, widths):
                dd.text((x, pad), c, font=f, fill=col, stroke_width=sw, stroke_fill=col if sw else None)
                x += w
        else:
            dd.text((pad, pad), txt, font=f, fill=col, stroke_width=sw, stroke_fill=stroke_fill if sw else None)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw(ImageDraw.Draw(sh), (0, 0, 0, 150), stroke)
        sh = sh.filter(ImageFilter.GaussianBlur(size * 0.08))
        im.alpha_composite(sh, (0, int(size * 0.04)))
    if stroke and not tracking:
        d.text((pad, pad), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    else:
        draw(d, fill, 0)
    res = (im, pad)
    _tc[key] = res
    return res

def paste(canvas, spr, x, y, alpha=1.0, scale=1.0, anchor="lt", blur=0):
    """paste sprite so that its *text box* (excluding pad) anchors at x,y"""
    im, pad = spr
    if alpha <= 0.003:
        return
    if scale != 1.0:
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.BICUBIC)
        pad = pad * scale
    if blur > 0.3:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    bw, bh = im.width - 2 * pad, im.height - 2 * pad
    ox = {"l": 0, "c": bw / 2, "r": bw}[anchor[0]]
    oy = {"t": 0, "m": bh / 2, "b": bh}[anchor[1]]
    canvas.alpha_composite(im, (int(round(x - ox - pad)), int(round(y - oy - pad))))

def glass(canvas, box, r=28, alpha=1.0, fill=(14, 18, 24, 175), border=(255, 255, 255, 60)):
    if alpha <= 0.003: return
    x0, y0, x1, y1 = [int(v) for v in box]
    layer = Image.new("RGBA", (x1 - x0 + 40, y1 - y0 + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((20, 26, x1 - x0 + 20, y1 - y0 + 26), r, fill=(0, 0, 0, int(90 * alpha)))
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((20, 20, x1 - x0 + 20, y1 - y0 + 20), r,
                        fill=fill[:3] + (int(fill[3] * alpha),),
                        outline=border[:3] + (int(border[3] * alpha),), width=2)
    canvas.alpha_composite(layer, (x0 - 20, y0 - 20))

def with_alpha(c, a): return c[:3] + (int(c[3] * a),)

# ---------------------------------------------------------------- virtual camera
CX0, CY0 = W / 2, H / 2
def camera(t, sp):
    zc = (640.0, 1000.0)
    if t < 3.0:
        z = lerp(1.12, 1.04, ease_out_cubic(prog(t, 0, 3.0))); c = (CX0, CY0)
    elif t < 13.6:
        x = ease_in_out(prog(t, 3.0, 13.6))
        z = lerp(1.04, 1.12, x); c = (lerp(CX0, 600, x), lerp(CY0, 1010, x))
    elif t < 17.6:
        x = ease_out_expo(prog(t, 13.6, 14.2))
        z = lerp(1.12, 1.20, x) + 0.04 * prog(t, 14.2, 17.6)
        c = (lerp(600, zc[0], x), lerp(1010, zc[1], x))
    else:
        x = ease_in_out(prog(t, 17.6, 18.5))
        z = lerp(1.24, 1.05, x) - 0.05 * prog(t, 18.5, DUR)
        c = (lerp(zc[0], CX0, x), lerp(zc[1], CY0, x))
    # subtle handheld-safe drift
    z = max(z, 1.0)
    cw, ch = W / z, H / z
    cx = clamp(c[0], cw / 2, W - cw / 2); cy = clamp(c[1], ch / 2, H - ch / 2)
    return z, cx - cw / 2, cy - ch / 2

def apply_cam(img, z, x0, y0):
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def to_screen(p, z, x0, y0): return ((p[0] - x0) * z, (p[1] - y0) * z)

# ---------------------------------------------------------------- captions
CAPS = [
    (0.35, 3.00, "Así se elimina la *corrosión* en cubierta"),
    (3.20, 6.40, "Primero, ubicamos el *punto* *dañado*"),
    (6.60, 10.0, "El *martillo* *de* *agujas* rompe el óxido y la pintura vieja"),
    (10.2, 13.5, "Golpea *miles* de veces por minuto"),
    (13.8, 17.4, "Hasta dejar el *metal* *limpio*"),
    (17.6, 20.3, "Listo para *primer* y pintura nueva"),
]
CAP_SIZE = 64
CAP_MAXW = 820
CAP_CX = 515
CAP_Y = 1470

def layout_caption(text):
    f = font(F_XB, CAP_SIZE)
    words = []
    for w in text.split():
        kw = w.startswith("*") and w.endswith("*")
        words.append((w.strip("*"), kw))
    space = f.getlength(" ") * 1.35 + 4
    lines, cur, cw = [], [], 0
    for w, kw in words:
        ww = f.getlength(w)
        if cur and cw + space + ww > CAP_MAXW:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + ww
        cur.append((w, kw, ww))
    lines.append((cur, cw))
    out = []
    lh = CAP_SIZE * 1.18
    for li, (ws, lw) in enumerate(lines):
        x = CAP_CX - lw / 2
        for w, kw, ww in ws:
            out.append((w, kw, x + ww / 2, CAP_Y + li * lh))
            x += ww + space
    return out

CAP_LAYOUT = [(a, b, layout_caption(tx)) for a, b, tx in CAPS]

def draw_captions(cv, t):
    for a, b, words in CAP_LAYOUT:
        if not (a <= t <= b): continue
        env = window(t, a, b, 0.12, 0.18)
        n = len(words)
        reveal_end = a + (b - a) * 0.62
        step = (reveal_end - a) / n
        lift = (1 - ease_out_cubic(prog(t, a, a + 0.3))) * 30
        for i, (w, kw, cx, cy) in enumerate(words):
            ts = a + i * step
            if t < ts: continue
            p = prog(t, ts, ts + 0.20)
            sc = ease_out_back(p, 2.2) if p < 1 else 1.0
            sc = 0.55 + 0.45 * sc
            active = ts <= t < ts + step * 1.6 and t < reveal_end + 0.3
            if active: sc *= 1.08
            col = ORANGE if kw else WHITE
            spr = text_sprite(w, F_XB, CAP_SIZE, fill=col, stroke=6, stroke_fill=(0, 0, 0, 255))
            paste(cv, spr, cx, cy + lift, alpha=env * clamp(p * 2.5), scale=sc, anchor="cm")

# ---------------------------------------------------------------- world-space graphics (tracked)
def draw_ring(cv, t, sp):
    a, b = 3.2, 6.6
    if not (a <= t <= b): return
    env = window(t, a, b, 0.05, 0.3)
    d = ImageDraw.Draw(cv)
    x, y = sp
    r = 96 + 3 * math.sin(t * 6)
    sweep = 360 * ease_out_cubic(prog(t, a, a + 0.55))
    d.arc((x - r, y - r * 0.62, x + r, y + r * 0.62), -90, -90 + sweep, fill=with_alpha(ORANGE, env), width=7)
    # pulse wave
    pw = (t - a) % 1.0
    r2 = r + 60 * pw
    d.ellipse((x - r2, y - r2 * .62, x + r2, y + r2 * .62), outline=(255, 255, 255, int(160 * (1 - pw) * env)), width=3)
    # leader line + label
    lp = ease_out_cubic(prog(t, a + 0.35, a + 0.75))
    p0 = (x - r * 0.95, y - r * 0.2)
    p1 = (x - r - 110, y - 150)
    p2 = (575, y - 150)
    if lp > 0:
        seg1 = (lerp(p0[0], p1[0], clamp(lp * 2)), lerp(p0[1], p1[1], clamp(lp * 2)))
        d.line([p0, seg1], fill=with_alpha(WHITE, env), width=4)
        if lp > .5:
            seg2 = (lerp(p1[0], p2[0], clamp(lp * 2 - 1)), p1[1])
            d.line([p1, seg2], fill=with_alpha(WHITE, env), width=4)
        d.ellipse((p0[0] - 7, p0[1] - 7, p0[0] + 7, p0[1] + 7), fill=with_alpha(WHITE, env))
    la = env * ease_out_cubic(prog(t, a + 0.65, a + 1.0))
    if la > 0:
        dx = (1 - la) * 40
        spr = text_sprite("PUNTO DE CORROSIÓN", F_XB, 34, tracking=2, shadow=False)
        bw = spr[0].width - 2 * spr[1]
        box = (p2[0] - bw - 44 + dx, p2[1] - 34, p2[0] + dx, p2[1] + 34)
        glass(cv, box, r=34, alpha=la, fill=(255, 122, 26, 235), border=(255, 255, 255, 90))
        paste(cv, spr, box[0] + 22, p2[1], alpha=la, anchor="lm")

def draw_tool_label(cv, t, sp):
    a, b = 6.6, 10.0
    if not (a <= t <= b): return
    env = window(t, a, b, 0.05, 0.3)
    d = ImageDraw.Draw(cv)
    tgt = (sp[0] + 40, sp[1] - 190)
    dot = ease_out_back(prog(t, a, a + 0.3))
    rr = 12 * dot
    d.ellipse((tgt[0] - rr, tgt[1] - rr, tgt[0] + rr, tgt[1] + rr), fill=with_alpha(ORANGE, env))
    pr = (t - a) % 0.9 / 0.9
    r2 = 12 + 30 * pr
    d.ellipse((tgt[0] - r2, tgt[1] - r2, tgt[0] + r2, tgt[1] + r2), outline=(255, 122, 26, int(220 * (1 - pr) * env)), width=3)
    lp = ease_out_cubic(prog(t, a + 0.15, a + 0.5))
    p1 = (tgt[0] - 140, tgt[1] - 110)
    end = (lerp(tgt[0], p1[0], lp), lerp(tgt[1], p1[1], lp))
    if lp > 0: d.line([tgt, end], fill=with_alpha(WHITE, env), width=4)
    la = env * ease_out_cubic(prog(t, a + 0.4, a + 0.75))
    if la > 0:
        s1 = text_sprite("MARTILLO DE AGUJAS", F_XB, 40, shadow=False)
        s2 = text_sprite("Needle scaler · herramienta neumática", F_SB, 26, fill=(255, 255, 255, 200), shadow=False)
        bw = max(s1[0].width - 2 * s1[1], s2[0].width - 2 * s2[1])
        x1 = p1[0] - 6; x0 = x1 - bw - 52
        dy = (1 - la) * 24
        box = (x0, p1[1] - 62 + dy, x1, p1[1] + 50 + dy)
        glass(cv, box, alpha=la)
        d2 = ImageDraw.Draw(cv)
        d2.rounded_rectangle((x0 + 18, box[1] + 22, x0 + 26, box[3] - 22), 4, fill=with_alpha(ORANGE, la))
        paste(cv, s1, x0 + 40, box[1] + 18, alpha=la)
        paste(cv, s2, x0 + 40, box[1] + 70, alpha=la)

def draw_impacts(cv, t, sp):
    a, b = 10.2, 13.5
    if not (a <= t <= b): return
    env = window(t, a, b, 0.2, 0.3)
    d = ImageDraw.Draw(cv)
    x, y = sp[0], sp[1] - 10
    for k in range(3):
        ph = ((t - a) * 3.2 + k / 3) % 1.0
        r = 30 + 120 * ease_out_cubic(ph)
        al = int(230 * (1 - ph) * env)
        col = (255, 122, 26, al) if k == 0 else (255, 255, 255, al)
        d.ellipse((x - r, y - r * .6, x + r, y + r * .6), outline=col, width=5 if k == 0 else 3)

# behind-the-subject giant word
def draw_behind(t):
    a, b = 13.6, 17.6
    if not (a <= t <= b): return None
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    env = window(t, a, b, 0.01, 0.35)
    word = "ÓXIDO"
    size = 205
    f = font(F_BLACK, size)
    total = sum(f.getlength(c) for c in word) - 8 * (len(word) - 1)
    x = 640 - total / 2
    base_y = 760
    for i, c in enumerate(word):
        p = prog(t, a + 0.05 + i * 0.06, a + 0.5 + i * 0.06)
        e = ease_out_back(p, 1.6)
        spr = text_sprite(c, F_BLACK, size, fill=WHITE, shadow=True)
        cw = f.getlength(c)
        paste(lay, spr, x + cw / 2, base_y + (1 - e) * 160, alpha=env * clamp(p * 3), anchor="cm",
              scale=0.85 + 0.15 * e)
        x += cw - 8
    # strike-through
    sp_ = ease_in_out(prog(t, a + 1.35, a + 1.85))
    if sp_ > 0:
        d = ImageDraw.Draw(lay)
        x0 = 640 - total / 2 - 30; x1 = lerp(x0, 640 + total / 2 + 30, sp_)
        d.rounded_rectangle((x0, base_y - 14, x1, base_y + 14), 14, fill=with_alpha(ORANGE, env))
    return lay

def draw_sin(cv, t):
    a, b = 13.6, 17.6
    if not (a <= t <= b): return
    env = window(t, a, b, 0.01, 0.35)
    f = font(F_BLACK, 205)
    total = sum(f.getlength(c) for c in "ÓXIDO") - 8 * 4
    sa = prog(t, a + 1.8, a + 2.1)
    if sa > 0:
        e = ease_out_back(sa, 3)
        spr = text_sprite("SIN", F_BLACK, 110, fill=ORANGE, shadow=True)
        paste(cv, spr, 640 - total / 2 + 10, 760 - 135, alpha=env * clamp(sa * 3), anchor="lb",
              scale=lerp(1.6, 1.0, e))

# ---------------------------------------------------------------- screen-space graphics
def draw_hook(cv, t):
    a, b = 0.0, 3.05
    if t > b: return
    out = prog(t, 2.75, 3.05)
    oy = -ease_in_out(out) * 60
    alpha = 1 - out
    kk = text_sprite("MANTENIMIENTO EN CUBIERTA", F_XB, 30, fill=ORANGE, tracking=5, shadow=True)
    kp = ease_out_cubic(prog(t, 0.05, 0.45))
    paste(cv, kk, 78 + (1 - kp) * -40, 250 + oy, alpha=alpha * kp)
    d = ImageDraw.Draw(cv)
    d.rectangle((78, 300 + oy, 78 + 90 * kp, 306 + oy), fill=with_alpha(ORANGE, alpha * kp))
    for i, (txt, col, y) in enumerate([("ADIÓS", WHITE, 330), ("AL ÓXIDO", ORANGE, 480)]):
        p = ease_out_expo(prog(t, 0.12 + i * 0.16, 0.75 + i * 0.16))
        spr = text_sprite(txt, F_BLACK, 168, fill=col, shadow=True)
        # mask-reveal from below: render then clip
        im, pad = spr
        bh = im.height
        sub = Image.new("RGBA", (im.width, bh), (0, 0, 0, 0))
        sub.alpha_composite(im, (0, int((1 - p) * bh * 0.8)))
        clip = Image.new("L", sub.size, 0)
        ImageDraw.Draw(clip).rectangle((0, 0, sub.width, pad + 168 * 1.05), fill=255)
        sub.putalpha(Image.fromarray(np.minimum(np.array(sub.getchannel("A")), np.array(clip))))
        paste(cv, (sub, pad), 70, y + oy, alpha=alpha)

def draw_bolt(d, x, y, s, col):
    pts = [(0.55, 0), (0.1, 0.55), (0.45, 0.55), (0.3, 1), (0.9, 0.38), (0.52, 0.38), (0.75, 0)]
    d.polygon([(x + px * s, y + py * s) for px, py in pts], fill=col)

def draw_blows_card(cv, t):
    a, b = 10.35, 13.5
    if not (a <= t <= b): return
    env = window(t, a, b, 0.3, 0.3)
    e = ease_out_back(prog(t, a, a + 0.45))
    dx = (1 - e) * -420
    box = (70 + dx, 1210, 610 + dx, 1350)
    glass(cv, box, alpha=env)
    d = ImageDraw.Draw(cv)
    d.ellipse((box[0] + 22, 1236, box[0] + 110, 1324), fill=with_alpha(ORANGE, env))
    sh = 1 + 0.08 * math.sin(t * 40) * (t < b - 0.3)
    draw_bolt(d, box[0] + 66 - 26 * sh, 1250, 60 * sh, with_alpha(WHITE, env))
    paste(cv, text_sprite("MILES DE GOLPES", F_BLACK, 42, shadow=False), box[0] + 132, 1244, alpha=env)
    paste(cv, text_sprite("por minuto sobre la superficie", F_SB, 27, fill=(255, 255, 255, 210), shadow=False),
          box[0] + 132, 1296, alpha=env)

def draw_progress(cv, t):
    a, b = 13.9, 17.4
    if not (a <= t <= b): return
    env = window(t, a, b, 0.3, 0.3)
    e = ease_out_cubic(prog(t, a, a + 0.4))
    y = 1245 + (1 - e) * 40
    box = (70, y, 720, y + 150)
    glass(cv, box, alpha=env)
    p = ease_in_out(prog(t, a + 0.3, b - 0.6))
    paste(cv, text_sprite("PREPARACIÓN DE SUPERFICIE", F_XB, 25, tracking=1, shadow=False), 100, y + 26, alpha=env)
    pct = text_sprite(f"{int(round(p * 100))}%", F_BLACK, 46, fill=ORANGE, shadow=False)
    paste(cv, pct, 690, y + 18, alpha=env, anchor="rt")
    d = ImageDraw.Draw(cv)
    d.rounded_rectangle((100, y + 92, 690, y + 114), 11, fill=(255, 255, 255, int(45 * env)))
    if p > 0.01:
        d.rounded_rectangle((100, y + 92, 100 + 590 * p, y + 114), 11, fill=with_alpha(ORANGE, env))

def draw_checklist(cv, t):
    a, b = 17.75, 20.4
    if not (a <= t <= b): return
    env = window(t, a, b, 0.25, 0.3)
    items = ["Remover óxido", "Limpiar superficie", "Aplicar primer", "Pintura final"]
    e = ease_out_cubic(prog(t, a, a + 0.4))
    x0, y0 = 70 - (1 - e) * 60, 215
    rowh = 84
    box = (x0, y0, x0 + 560, y0 + 100 + rowh * len(items))
    glass(cv, box, alpha=env)
    paste(cv, text_sprite("PROCESO", F_XB, 28, fill=ORANGE, tracking=5, shadow=False), x0 + 34, y0 + 30, alpha=env)
    d = ImageDraw.Draw(cv)
    for i, it in enumerate(items):
        ip = ease_out_cubic(prog(t, a + 0.2 + i * 0.18, a + 0.55 + i * 0.18))
        if ip <= 0: continue
        al = env * ip
        cy = y0 + 112 + i * rowh + (1 - ip) * 20
        cx = x0 + 56
        done = i == 0
        if done:
            cp = prog(t, a + 0.8, a + 1.1)
            d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=with_alpha(ORANGE, al * max(cp, .0)),
                      outline=with_alpha(ORANGE, al), width=3)
            if cp > 0:
                pts = [(cx - 10, cy), (cx - 3, cy + 8), (cx + 11, cy - 9)]
                if cp < .5:
                    q = cp * 2; pts = [pts[0], (lerp(pts[0][0], pts[1][0], q), lerp(pts[0][1], pts[1][1], q))]
                else:
                    q = cp * 2 - 1; pts = [pts[0], pts[1], (lerp(pts[1][0], pts[2][0], q), lerp(pts[1][1], pts[2][1], q))]
                d.line(pts, fill=with_alpha(WHITE, al), width=5, joint="curve")
        else:
            d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), outline=(255, 255, 255, int(150 * al)), width=3)
            paste(cv, text_sprite(str(i + 1), F_XB, 24, shadow=False, fill=(255, 255, 255, 200)), cx, cy, alpha=al, anchor="cm")
        col = WHITE if done else (255, 255, 255, 190)
        paste(cv, text_sprite(it, F_XB if done else F_SB, 38, fill=col, shadow=False), cx + 48, cy, alpha=al, anchor="lm")
        if done and prog(t, a + 1.1, a + 1.4) > 0:
            tag = text_sprite("HECHO", F_XB, 22, fill=INK + (255,), shadow=False, tracking=2)
            tp = ease_out_back(prog(t, a + 1.1, a + 1.4))
            tx = x0 + 470
            d.rounded_rectangle((tx - 52 * tp, cy - 18, tx + 52 * tp, cy + 18), 18, fill=with_alpha((255, 255, 255, 235), al))
            if tp > .6: paste(cv, tag, tx, cy, alpha=al, anchor="cm")

def draw_end(cv, t):
    a = 20.45
    if t < a: return
    p1 = prog(t, a, a + 0.5); p2 = prog(t, a + 0.25, a + 0.75)
    e1, e2 = ease_out_expo(p1), ease_out_expo(p2)
    paste(cv, text_sprite("PREVENIR", F_BLACK, 150, fill=WHITE), W / 2, 820, alpha=clamp(p1 * 2),
          scale=lerp(1.25, 1.0, e1), anchor="cm", blur=(1 - e1) * 10)
    paste(cv, text_sprite("ES AHORRAR", F_BLACK, 150, fill=ORANGE), W / 2, 985, alpha=clamp(p2 * 2),
          scale=lerp(1.25, 1.0, e2), anchor="cm", blur=(1 - e2) * 10)
    sp = ease_out_cubic(prog(t, a + 0.6, a + 1.1))
    if sp > 0:
        s = text_sprite("Mantenimiento a tiempo = menos reparaciones", F_SB, 34, fill=(255, 255, 255, 230))
        paste(cv, s, W / 2, 1110 + (1 - sp) * 20, alpha=sp, anchor="cm")

# ---------------------------------------------------------------- frame
def render(i):
    t = i / FPS
    f = frames[i]
    sp = spot(i)
    world = grade(f)
    # behind-subject layer
    bl = draw_behind(t)
    if bl is not None:
        m = fg_mask(f)
        arr = np.asarray(bl).astype(np.float32) / 255
        a = arr[..., 3:4] * (1 - m[..., None])
        world = world * (1 - a) + arr[..., :3] * a
    # world overlay (tracked graphics)
    wo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_ring(wo, t, sp); draw_sin(wo, t); draw_tool_label(wo, t, sp); draw_impacts(wo, t, sp)
    arr = np.asarray(wo).astype(np.float32) / 255
    world = world * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]
    z, x0, y0 = camera(t, sp)
    scr = apply_cam(world, z, x0, y0)
    scr = scr * VIG
    # end darken
    dk = 0.42 * ease_in_out(prog(t, 20.3, 20.9))
    if dk: scr = scr * (1 - dk)
    # flash on punch-in
    fl = 0.30 * (1 - prog(t, 13.6, 13.95)) if t >= 13.6 else 0
    if fl: scr = scr + (1 - scr) * fl
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_hook(so, t); draw_blows_card(so, t); draw_progress(so, t); draw_checklist(so, t)
    draw_captions(so, t); draw_end(so, t)
    arr = np.asarray(so).astype(np.float32) / 255
    scr = scr * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]
    # fade-in first frames
    return (np.clip(scr, 0, 1) * 255 + 0.5).astype(np.uint8)

if __name__ == "__main__":
    if PREVIEW:
        for t in PREVIEW:
            i = min(int(t * FPS), N - 1)
            Image.fromarray(render(i)).save(f"{OUT}_{t:05.2f}.jpg", quality=88)
        sys.exit()

    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
        "-i", SRC, "-map", "0:v", "-map", "1:a",
        "-af", f"highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={DUR - 0.5:.2f}:d=0.5",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    for i in range(N):
        enc.stdin.write(render(i).tobytes())
        if i % 60 == 0: print("frame", i, "/", N, flush=True)
    enc.stdin.close(); enc.wait()
    print("done", OUT)
