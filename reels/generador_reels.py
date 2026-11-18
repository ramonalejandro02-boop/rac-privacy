"""Generador de reels motivacionales/religiosos con animación dinámica.

Uso:  python3 generador_reels.py
Genera reel_02_silencio_de_dios.mp4 (1080x1920, 30 fps, con audio).

Técnicas de retención incluidas:
  - Gancho en el primer segundo con temblor de cámara e impacto sonoro
  - Texto palabra por palabra con "pop" y palabras clave resaltadas
  - Cortes cada 2-4 s con destello, zoom de golpe y whoosh
  - Relámpagos, lluvia, rayos de luz y partículas
  - Barra de progreso arriba y "loop" (el final conecta con el inicio)
"""
import math, random, subprocess, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"
F_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YELLOW, RED, WHITE, GOLD, CREAM = (255, 212, 0), (255, 59, 59), (255, 255, 255), (255, 200, 90), (255, 244, 220)
BRAND = "Alejandro Curiosidades"

# ---------------------------------------------------------------- GUION ----
# Palabras entre *asteriscos* = resaltado amarillo; entre !signos! = rojo.
# lines: (texto, tamaño, segundo en que empieza dentro de la escena)
SCENES = [
    dict(dur=2.0, bg="dark", shake=1.0, emoji=("✋", 0.0),
         lines=[("!DETENTE!", 190, 0.05), ("Esto *NO* es casualidad", 78, 0.75)]),
    dict(dur=3.0, bg="dark",
         lines=[("Llevas días cargando", 92, 0.1), ("algo que no le has", 92, 0.6),
                ("contado a *NADIE*", 104, 1.15)]),
    dict(dur=3.3, bg="storm", lightning=[1.75],
         lines=[("Oras...", 120, 0.1), ("y sientes que el cielo", 86, 0.75),
                ("está en !SILENCIO!", 108, 1.7)]),
    dict(dur=2.1, bg="dark", shake=0.4, emoji=("👇", 1.0),
         lines=[("Pero Dios tiene", 100, 0.05), ("algo que *DECIRTE*", 100, 0.45)]),
    dict(dur=6.0, bg="sunrise", riser=True,
         verse=[("“No temas,", 0.2), ("porque yo estoy contigo…", 1.0),
                ("siempre te ayudaré,", 2.0), ("siempre te sustentaré”", 2.9)],
         ref=("ISAÍAS 41:10", 4.0)),
    dict(dur=3.4, bg="gold", shake=0.8,
         lines=[("Su silencio", 120, 0.05), ("*NO* es", 120, 0.5), ("*AUSENCIA*", 130, 0.9)]),
    dict(dur=3.2, bg="gold",
         lines=[("Está *OBRANDO*", 112, 0.05), ("en lo que", 100, 0.7), ("aún no ves", 100, 1.1)]),
    dict(dur=3.4, bg="sunrise", emoji=("🙏", 1.4),
         lines=[("Si lo crees,", 110, 0.05), ("escribe *AMÉN*", 116, 0.55),
                ("y envíaselo a quien lo necesite", 48, 1.7)]),
    dict(dur=1.8, bg="dark", loop=True,
         lines=[("Porque esto no te", 92, 0.05), ("apareció por...", 92, 0.5)]),
]
OUT = os.path.join(HERE, "reel_02_silencio_de_dios.mp4")

# ------------------------------------------------------------ utilidades ---
def ease_out_back(p, s=2.2):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def fractal(w, h, seed, octaves=5):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        sw, sh = max(2, w >> (7 - o)), max(2, h >> (7 - o))
        n = Image.fromarray((rng.random((sh, sw)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(n, np.float32) / 255 * amp; tot += amp; amp *= 0.5
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min())

def vgrad(h, w, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        col = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
        out[:, :, c] = col[:, None]
    return out

# --------------------------------------------------------- fondos ----------
BW, BH = int(W * 1.2), int(H * 1.2)

def bg_dark():
    g = vgrad(BH, BW, [(0, (6, 4, 12)), (0.6, (28, 6, 14)), (1, (60, 10, 20))])
    f = fractal(BW, BH, 1)[:, :, None]
    return np.clip(g + f * np.array([60, 14, 30]) * 0.9, 0, 255)

def bg_storm():
    g = vgrad(BH, BW, [(0, (10, 14, 26)), (1, (24, 30, 44))])
    f = fractal(BW, BH, 7, 6)[:, :, None] ** 1.6
    return np.clip(g + f * np.array([70, 78, 96]), 0, 255)

def bg_sunrise():
    g = vgrad(BH, BW, [(0, (24, 28, 70)), (0.35, (150, 70, 90)), (0.6, (250, 150, 70)), (0.75, (255, 205, 120)), (1, (255, 225, 160))])
    yy, xx = np.mgrid[0:BH, 0:BW]
    sun = np.exp(-(((xx - BW / 2) / 260) ** 2 + ((yy - BH * 0.72) / 260) ** 2))[:, :, None]
    img = np.clip(g + sun * np.array([255, 220, 150]) * 0.9, 0, 255)
    im = Image.fromarray(img.astype(np.uint8)); d = ImageDraw.Draw(im)
    rng = random.Random(4)
    for layer, (base, col, rough) in enumerate([(0.74, (70, 40, 60), 90), (0.8, (40, 22, 40), 70), (0.86, (18, 10, 22), 50)]):
        pts = [(0, BH)]; y = BH * base
        for x in range(0, BW + 40, 40):
            y += rng.uniform(-rough, rough) * 0.5; y = min(max(y, BH * (base - 0.06)), BH * (base + 0.04))
            pts.append((x, y))
        pts.append((BW, BH)); d.polygon(pts, fill=col)
    # colina con cruz
    cx, cy = BW // 2, int(BH * 0.86)
    d.ellipse([cx - 520, cy - 90, cx + 520, cy + 400], fill=(10, 6, 14))
    d.rectangle([cx - 13, cy - 330, cx + 13, cy - 40], fill=(10, 6, 14))
    d.rectangle([cx - 105, cy - 260, cx + 105, cy - 236], fill=(10, 6, 14))
    return np.asarray(im, np.float32)

def bg_gold():
    yy, xx = np.mgrid[0:BH, 0:BW]
    r = np.sqrt(((xx - BW / 2) / BW) ** 2 + ((yy - BH * 0.45) / BW) ** 2)
    core = np.clip(1 - r * 1.4, 0, 1)[:, :, None] ** 1.5
    base = np.array([40, 18, 4]) + core * np.array([255, 200, 90])
    return np.clip(base, 0, 255)

print("Generando fondos…")
BGS = {"dark": bg_dark(), "storm": bg_storm(), "sunrise": bg_sunrise(), "gold": bg_gold()}
FOG = fractal(W * 2, H, 11, 5)
RAYS = Image.new("L", (2400, 2400), 0); _d = ImageDraw.Draw(RAYS)
for a in range(0, 360, 15):
    r1, r2 = math.radians(a), math.radians(a + 5)
    _d.polygon([(1200, 1200), (1200 + 1700 * math.cos(r1), 1200 + 1700 * math.sin(r1)), (1200 + 1700 * math.cos(r2), 1200 + 1700 * math.sin(r2))], fill=255)
RAYS = RAYS.filter(ImageFilter.GaussianBlur(18))
rain = Image.new("L", (W, H), 0); _d = ImageDraw.Draw(rain); _r = random.Random(9)
for _ in range(500):
    x, y, l = _r.uniform(-200, W), _r.uniform(0, H), _r.uniform(40, 110)
    _d.line([(x, y), (x + l * 0.25, y + l)], fill=_r.randint(60, 150), width=2)
RAIN = np.asarray(rain, np.float32)[:, :, None] / 255
yy, xx = np.mgrid[0:H, 0:W]
VIGN = (1 - 0.75 * np.clip(np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2), 0, 1) ** 2.2)[:, :, None].astype(np.float32)
del yy, xx
GRAIN = [np.random.default_rng(i).normal(0, 9, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) for i in range(4)]

def make_bolt():
    im = Image.new("L", (700, 1300), 0); d = ImageDraw.Draw(im); r = random.Random(2)
    def br(x, y, ang, length, width, depth):
        for _ in range(int(length / 40)):
            nx = x + math.sin(ang) * 40 + r.uniform(-25, 25); ny = y + math.cos(ang) * 40
            d.line([(x, y), (nx, ny)], fill=255, width=width); x, y = nx, ny
            if depth < 2 and r.random() < 0.12:
                br(x, y, ang + r.uniform(-0.9, 0.9), length * 0.4, max(1, width - 3), depth + 1)
    br(350, 0, 0.1, 1250, 9, 0)
    glow = im.filter(ImageFilter.GaussianBlur(25))
    a = np.maximum(np.asarray(im, np.float32), np.asarray(glow, np.float32) * 2.5)
    return np.clip(a, 0, 255) / 255
BOLT = make_bolt()

PART = [[random.uniform(0, W), random.uniform(0, H), random.uniform(2, 7), random.uniform(0.4, 1.4), random.uniform(0, 6)] for _ in range(90)]

# --------------------------------------------------------- texto -----------
_fc, _sc = {}, {}
def font(path, size):
    if (path, size) not in _fc: _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]

def parse(word):
    if len(word) > 2 and word[0] == "*" and word.endswith(("*", "*,", "*.")): return word.replace("*", ""), "hl"
    if len(word) > 2 and word[0] == "!" and "!" in word[1:]: return word.replace("!", ""), "red"
    return word, "n"

def sprite(word, style, size):
    key = (word, style, size)
    if key in _sc: return _sc[key]
    f = font(F_BLACK, size); w = int(f.getlength(word)); pad = int(size * 0.35)
    im = Image.new("RGBA", (w + pad * 2, int(size * 1.6) + pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if style == "hl":
        d.rounded_rectangle([pad - size * 0.18, pad * 0.6, pad + w + size * 0.18, pad * 0.6 + size * 1.25], radius=size * 0.18, fill=YELLOW + (255,))
        d.text((pad, pad * 0.6 + size * 0.05), word, font=f, fill=(0, 0, 0, 255))
        im = im.rotate(-3, resample=Image.BICUBIC, expand=True)
    else:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad + 6, pad * 0.6 + 10), word, font=f, fill=(0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        d.text((pad, pad * 0.6), word, font=f, fill=(RED if style == "red" else WHITE) + (255,),
               stroke_width=max(4, size // 18), stroke_fill=(0, 0, 0, 255))
        im = Image.alpha_composite(sh, im)
    _sc[key] = im
    return im

def emoji_sprite(ch, size=200):
    key = ("emoji", ch, size)
    if key not in _sc:
        f = ImageFont.truetype(F_EMOJI, 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
        _sc[key] = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return _sc[key]

def layout(scene):
    """Devuelve lista de palabras con posición, estilo, tamaño y tiempo de aparición."""
    lines = scene.get("lines", [])
    heights = [s * 1.25 for _, s, _ in lines]
    total = sum(heights); y = H * 0.46 - total / 2
    words = []
    for (text, size, t0), lh in zip(lines, heights):
        toks = [parse(w) for w in text.split()]
        f = font(F_BLACK, size); sp = size * 0.28
        widths = [f.getlength(w) + (size * 0.36 if st == "hl" else 0) for w, st in toks]
        lw = sum(widths) + sp * (len(toks) - 1)
        scale = min(1.0, 960 / lw)
        if scale < 1: size = int(size * scale); widths = [x * scale for x in widths]; sp *= scale; lw = 960
        x = (W - lw) / 2
        for i, ((w, st), ww) in enumerate(zip(toks, widths)):
            words.append(dict(w=w, st=st, size=size, cx=x + ww / 2, cy=y + lh / 2, t=t0 + i * 0.13))
            x += ww + sp
        y += lh
    return words

# --------------------------------------------------------- línea de tiempo -
t = 0.0
for s in SCENES:
    s["t0"] = t; t += s["dur"]; s["t1"] = t
    s["words"] = layout(s)
TOTAL = t
N = int(TOTAL * FPS)

# eventos de audio
impacts, whooshes, thunders, risers, booms = [], [], [], [], []
for i, s in enumerate(SCENES):
    if i > 0: whooshes.append(s["t0"] - 0.18)
    if s.get("shake"): booms.append(s["t0"] + 0.05)
    for w in s["words"]:
        if w["st"] != "n": impacts.append(s["t0"] + w["t"])
    for lt in s.get("lightning", []): thunders.append(s["t0"] + lt)
    if s.get("riser"): risers.append((s["t1"] - 2.2, s["t1"]))
    if s.get("ref"): impacts.append(s["t0"] + s["ref"][1])

# --------------------------------------------------------- render ----------
def render_frame(n):
    tt = n / FPS
    si = next(i for i, s in enumerate(SCENES) if tt < s["t1"] or i == len(SCENES) - 1)
    s = SCENES[si]; lt = tt - s["t0"]; prog = lt / s["dur"]
    # cámara: acercamiento lento + golpe de zoom al iniciar escena
    z = 1.0 + 0.10 * prog
    big = BGS[s["bg"]]
    cw, ch = int(BW / (1.2 * z) * 1.0), int(BH / (1.2 * z))
    ox, oy = (BW - cw) // 2, (BH - ch) // 2
    frame = np.asarray(Image.fromarray(big[oy:oy + ch, ox:ox + cw].astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32).copy()

    if s["bg"] in ("dark", "storm"):
        off = int((tt * 60) % W)
        fog = FOG[:, off:off + W][:, :, None]
        tint = np.array([90, 20, 40]) if s["bg"] == "dark" else np.array([60, 70, 90])
        frame += fog ** 2 * tint * 0.8
    if s["bg"] == "storm":
        r = np.roll(RAIN, int(tt * 2600) % H, axis=0)
        frame += r * 140
        for lt0 in s.get("lightning", []):
            dt = lt - lt0
            if 0 <= dt < 0.7:
                fl = (1.0 if dt < 0.06 else 0.0) + (0.8 if 0.12 < dt < 0.2 else 0.0) + max(0, 0.5 - dt) * 0.6
                frame = frame * (1 + fl * 1.6) + fl * 60
                if dt < 0.35:
                    b = BOLT[:, :, None]; x0 = 260
                    frame[0:1300, x0:x0 + 700] = frame[0:1300, x0:x0 + 700] * (1 - b) + b * np.array([235, 240, 255])
    if s["bg"] in ("gold", "sunrise"):
        rot = RAYS.rotate(tt * 8, resample=Image.BILINEAR)
        cy = int(H * 0.45) if s["bg"] == "gold" else int(H * 0.62)
        cr = np.asarray(rot.crop((1200 - W // 2, 1200 - cy, 1200 + W // 2, 1200 - cy + H)), np.float32)[:, :, None] / 255
        frame += cr * np.array([255, 210, 130]) * (0.35 if s["bg"] == "gold" else 0.22)

    img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    pcol = (255, 225, 160) if s["bg"] in ("gold", "sunrise") else (255, 170, 170) if s["bg"] == "dark" else (200, 215, 255)
    for q in PART:
        y = (q[1] - tt * 55 * q[3]) % H; x = q[0] + math.sin(tt + q[4]) * 20
        a = int(clamp(0.5 + 0.5 * math.sin(tt * 3 + q[4])) * 200)
        d.ellipse([x - q[2], y - q[2], x + q[2], y + q[2]], fill=pcol + (a,))

    fade_out = clamp((s["dur"] - lt) / 0.12)
    for w in s["words"]:
        p = (lt - w["t"]) / 0.22
        if p <= 0: continue
        sc = 1.9 + (1.0 - 1.9) * ease_out_back(clamp(p)) if p < 1 else 1.0
        sp = sprite(w["w"], w["st"], w["size"])
        nw, nh = max(1, int(sp.width * sc)), max(1, int(sp.height * sc))
        spr = sp.resize((nw, nh), Image.BILINEAR) if sc != 1 else sp
        al = clamp(p * 3) * fade_out
        if al < 1:
            a = spr.getchannel("A").point(lambda v: int(v * al)); spr = spr.copy(); spr.putalpha(a)
        img.alpha_composite(spr, (int(w["cx"] - nw / 2), int(w["cy"] - nh / 2)))

    if "verse" in s:
        f = font(F_SERIF, 84); y0 = H * 0.30
        for i, (txt, t0) in enumerate(s["verse"]):
            p = clamp((lt - t0) / 0.5)
            if p <= 0: continue
            lay = Image.new("RGBA", (W, 140), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.text((W / 2 + 4, 76), txt, font=f, fill=(0, 0, 0, 220), anchor="mm")
            lay = lay.filter(ImageFilter.GaussianBlur(7)); ld = ImageDraw.Draw(lay)
            ld.text((W / 2, 70), txt, font=f, fill=CREAM + (255,), anchor="mm", stroke_width=2, stroke_fill=(60, 30, 10, 255))
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * p * fade_out)))
            img.alpha_composite(lay, (0, int(y0 + i * 120 + (1 - p) * 50)))
        rt, rt0 = s["ref"]; p = clamp((lt - rt0) / 0.25)
        if p > 0:
            sp = sprite(rt, "hl", 80); sc = 1.9 + (1 - 1.9) * ease_out_back(p)
            spr = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
            img.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(y0 + 4 * 120 + 70 - spr.height / 2)))

    if "emoji" in s:
        ch_, et = s["emoji"]; p = (lt - et) / 0.3
        if p > 0:
            sc = 0.2 + 0.8 * ease_out_back(clamp(p)); bob = math.sin(lt * 6) * 12
            e = emoji_sprite(ch_, int(220 * sc))
            ey = H * 0.46 - sum(x[1] * 1.25 for x in s["lines"]) / 2 - 170
            if ch_ == "👇" or ch_ == "🙏": ey = H * 0.46 + sum(x[1] * 1.25 for x in s["lines"]) / 2 + 150
            img.alpha_composite(e, (int(W / 2 - e.width / 2), int(ey - e.height / 2 + bob)))

    # barra de progreso + marca
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=(0, 0, 0, 120)); d.rectangle([0, 0, int(W * tt / TOTAL), 14], fill=YELLOW + (255,))
    d.text((W / 2, 150), "@" + BRAND, font=font(F_BLACK, 40), fill=(255, 255, 255, 190), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 140))

    # golpe de zoom + temblor
    out = img.convert("RGB")
    punch = max(0.0, 0.07 * (1 - lt / 0.25)) if lt < 0.25 else 0
    shake = s.get("shake", 0) * max(0, 1 - lt / 0.6) * 22
    for w in s["words"]:
        if w["st"] != "n":
            dt = lt - w["t"]
            if 0 <= dt < 0.3: shake = max(shake, 14 * (1 - dt / 0.3)); punch = max(punch, 0.035 * (1 - dt / 0.3))
    if punch > 0 or shake > 0:
        zz = 1 + punch + shake / 250
        cw, ch = W / zz, H / zz
        dx, dy = random.uniform(-shake, shake), random.uniform(-shake, shake)
        x0 = min(max((W - cw) / 2 + dx, 0), W - cw); y0 = min(max((H - ch) / 2 + dy, 0), H - ch)
        out = out.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    arr = np.asarray(out, np.float32) * VIGN + GRAIN[n % 4]
    # destello blanco en cada corte
    if si > 0 and lt < 0.12: arr = arr + (1 - lt / 0.12) * 255 * 0.85
    return np.clip(arr, 0, 255).astype(np.uint8)

# --------------------------------------------------------- audio -----------
def synth_audio():
    n = int(TOTAL * SR) + SR
    out = np.zeros(n, np.float64); rng = np.random.default_rng(5)
    tt = np.arange(n) / SR
    def add(sig, at, gain=1.0):
        i = int(at * SR)
        if i < 0: sig = sig[-i:]; i = 0
        j = min(n, i + len(sig)); out[i:j] += sig[:j - i] * gain
    def bandnoise(dur, lo, hi):
        m = int(dur * SR); x = rng.normal(0, 1, m); X = np.fft.rfft(x); fr = np.fft.rfftfreq(m, 1 / SR)
        X[(fr < lo) | (fr > hi)] = 0; y = np.fft.irfft(X, m); return y / (np.abs(y).max() + 1e-9)
    # pad (acordes por escena)
    chords = {"dark": [110, 130.81, 164.81], "storm": [73.42, 87.31, 110], "gold": [130.81, 164.81, 196, 261.63], "sunrise": [87.31, 130.81, 174.61, 220]}
    for s in SCENES:
        a, b = s["t0"], s["t1"]; m = int((b - a + 0.6) * SR); t_ = np.arange(m) / SR
        sig = sum(np.sin(2 * np.pi * f * t_) + 0.35 * np.sin(2 * np.pi * f * 2.003 * t_) + 0.15 * np.sin(2 * np.pi * f * 3.01 * t_) for f in chords[s["bg"]])
        env = np.minimum(1, t_ / 0.35) * np.minimum(1, (len(t_) / SR - t_) / 0.5)
        add(sig * env, a, 0.05)
    # latido en la escena de tormenta y la del gancho
    for s in SCENES:
        if s["bg"] == "storm" or s.get("shake"):
            k = s["t0"]
            while k < s["t1"] - 0.2:
                for off in (0, 0.22):
                    m = int(0.25 * SR); t_ = np.arange(m) / SR
                    add(np.sin(2 * np.pi * (45 + 60 * np.exp(-t_ * 30)) * t_) * np.exp(-t_ * 14), k + off, 0.6)
                k += 0.85
    for at in impacts + booms:
        m = int(1.2 * SR); t_ = np.arange(m) / SR
        boom = np.sin(2 * np.pi * np.cumsum(40 + 110 * np.exp(-t_ * 9)) / SR) * np.exp(-t_ * 3.5)
        add(boom, at, 0.55); add(bandnoise(0.15, 1500, 9000) * np.exp(-np.arange(int(0.15 * SR)) / SR * 30), at, 0.25)
    for at in whooshes:
        m = int(0.35 * SR); t_ = np.arange(m) / SR
        add(bandnoise(0.35, 300, 4000) * np.sin(np.pi * t_ / 0.35) ** 2, at, 0.35)
    for at in thunders:
        m = int(2.5 * SR); t_ = np.arange(m) / SR
        add(bandnoise(2.5, 30, 400) * np.exp(-t_ * 1.6) * (0.4 + 0.6 * np.exp(-t_ * 8)), at, 0.9)
        add(bandnoise(0.2, 2000, 12000) * np.exp(-t_[:int(0.2 * SR)] * 25), at, 0.5)
    for a, b in risers:
        m = int((b - a) * SR); t_ = np.arange(m) / SR; p = t_ / (b - a)
        sig = bandnoise(b - a, 800, 9000) * p ** 2 * 0.6 + np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * p ** 2 * 0.25
        add(sig, a, 0.5)
    # lluvia de fondo
    for s in SCENES:
        if s["bg"] == "storm": add(bandnoise(s["dur"], 2000, 10000) * 0.12, s["t0"])
    out = out[:int(TOTAL * SR)]
    out = np.tanh(out * 1.3); out /= np.abs(out).max(); out *= 0.89
    path = os.path.join(HERE, "_audio_tmp.wav")
    with wave.open(path, "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((out * 32767).astype(np.int16).tobytes())
    return path

print("Generando audio…")
apath = synth_audio()
print(f"Renderizando {N} cuadros ({TOTAL:.1f} s)…")
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                         "-i", apath, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M",
                         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
random.seed(1)
for n in range(N):
    proc.stdin.write(render_frame(n).tobytes())
    if n % 150 == 0: print(f"  {n}/{N}")
proc.stdin.close(); proc.wait(); os.remove(apath)
print("Listo:", OUT)
