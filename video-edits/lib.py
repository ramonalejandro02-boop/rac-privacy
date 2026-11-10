"""Shared motion-graphics helpers (fonts, easing, text sprites, glass cards, grade)."""

import sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter



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

