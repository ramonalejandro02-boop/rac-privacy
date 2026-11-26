#!/usr/bin/env python3
"""
Motor de motion graphics por palabra clave.

Cuando en el video se dice una palabra clave, aparece un efecto: emoji animado,
sticker de texto, lluvia de emojis, ráfaga, zoom al que habla, temblor, flash
y efecto de sonido. Todo va sincronizado con la transcripción.

Diseño 9:16: fondo animado + el video en un panel con borde de luz + título
arriba + subtítulos abajo + barra de progreso.

Uso:
  # automático (detecta palabras clave del diccionario)
  python3 studio/efectos.py entrada.mp4 salida.mp4 --auto
  # con plan creativo hecho a mano (recomendado para el mejor resultado)
  python3 studio/efectos.py entrada.mp4 salida.mp4 --plan plan.json

Formato del plan: ver studio/planes/ejemplo_picaro.json
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transformar import (ESTILOS, FUENTE, FondoAnimado, Grading, agrupar,  # noqa: E402
                         energia_por_frame, extraer_wav, log, tiene_audio, transcribir)

EMOJI_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "NotoColorEmoji.ttf")
W, H = 1080, 1920
SR = 44100

# Zona segura de Facebook/Instagram Reels (medida en capturas reales):
# arriba: hora + flecha + lupa + menú; derecha: 👍 💬 ↗ 🔖 (desde ~56% de alto);
# abajo: nombre de la página, fecha y descripción (desde ~80%).
ZONA = dict(arriba=0.115, abajo=0.79, derecha=0.87, iconos_desde=0.56)


def seguro(x, y, ymin=0.27, ymax=0.62):
    """Ajusta una posición relativa (x, y) para que no caiga bajo la interfaz de Reels."""
    y = min(max(y, ymin), ymax)
    if y > ZONA["iconos_desde"] - 0.04:
        x = min(x, ZONA["derecha"] - 0.08)
    return min(max(x, 0.12), 0.88), y

# --------------------------------------------------------------------------
# Diccionario automático: palabra clave -> (emojis, sonido)
# --------------------------------------------------------------------------
CLAVES_AUTO = [
    (r"amor|enamor|love|te quiero|beso|novi", "💘😍", "ding"),
    (r"fij|mir|ojo|vist", "👀", "whoosh"),
    (r"madera|dur[oa]|grande|larg", "🍆😏", "silbido"),
    (r"calor|fuego|caliente|rico|rica|fuyín", "🥵🔥", "boom"),
    (r"diabl|malo|mala|maldit", "😈", "boing"),
    (r"dinero|plata|pisto|reales|millon", "💸🤑", "ding"),
    (r"mentir|mentira|cuenta", "🤥", "boing"),
    (r"llor|triste", "😭", "bajada"),
    (r"jaja|risa|chiste", "🤣", "pop"),
    (r"no me digas|en serio|qué\b", "🙄", "pop"),
    (r"comer|comida|hambre", "🍑😋", "pop"),
    (r"cama|noche|dormir", "🛏️😏", "silbido"),
]


# --------------------------------------------------------------------------
# Render de texto + emojis
# --------------------------------------------------------------------------
_EF = None
_cache_emoji = {}
# Groserías: se tapan con "piii" en el audio y con asteriscos en los subtítulos.
GROSERIAS = re.compile(
    r"^(put[oa]s?|hijueputa|hdp|mierdas?|coño|carajos?|vergas?|pingas?|mamag[uü]e?vo|mamahuevo|"
    r"cabr[oó]n(es|a|as)?|pendej\\w*|joder|jodid[oa]s?|culos?|ching\w*|maric[oó]n|marica|cojones|coj[oó]n|"
    r"sing[aá]\w*|singao|g[uü]evos?|fuck\w*|shit|bitch\w*|motherfucker)$")


def es_groseria(palabra):
    w = re.sub(r"[^\wáéíóúñü]", "", palabra.lower())
    return bool(w) and bool(GROSERIAS.match(w))


def tapar_palabra(p):
    letras = re.sub(r"[^\wáéíóúñüÁÉÍÓÚÑÜ]", "", p)
    return (letras[:1] + "***") if letras else p


_cache_font = {}
INTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "InterDisplay-{}.otf")
FUENTE_STICKER = INTER.format("Bold")        # títulos y stickers: moderna, no tan gruesa
FUENTE_SUBS = INTER.format("ExtraBold")      # subtítulos: legible sin ser pesada

# Temas: paleta de stickers, acento de subtítulos y fondos (base + escenas).
# Las parejas son (fondo, texto). Los colores de los planes viejos se remapean al tema.
TEMAS = {
    "caribe": dict(base="caribe", escenas=["caribe2", "caribe3", "caribe"],
                   stickers=[("#FFFFFF", "#023E8A"), ("#FFD166", "#1D3557"), ("#EF476F", "#FFFFFF")],
                   titulo=("#FFFFFF", "#023E8A"), acento=("#FFD166", "#1D3557"), clave="#FFD166"),
    "atardecer": dict(base="atardecer", escenas=["atardecer2", "atardecer3", "atardecer"],
                      stickers=[("#FFF4E6", "#7B2D8E"), ("#2B2D42", "#FFF4E6"), ("#FFD6A5", "#6A0572")],
                      titulo=("#FFF4E6", "#7B2D8E"), acento=("#2B2D42", "#FFFFFF"), clave="#FFE66D"),
    "menta": dict(base="menta", escenas=["menta3", "menta2", "menta"],
                  stickers=[("#FFFFFF", "#1D4E57"), ("#FF6B6B", "#FFFFFF"), ("#FFE66D", "#1D4E57")],
                  titulo=("#FFFFFF", "#1D4E57"), acento=("#FF6B6B", "#FFFFFF"), clave="#FFE66D"),
    "noche": dict(base="noche", escenas=["noche2", "noche3", "noche"],
                  stickers=[("#24224A", "#F8F8FF"), ("#7CFFCB", "#14132B"), ("#FF7AC6", "#14132B")],
                  titulo=("#24224A", "#F8F8FF"), acento=("#7CFFCB", "#14132B"), clave="#FF7AC6"),
}
TEMA = None
_MAPA_COLORES = {"#FFE600": 1, "#FFFFFF": 0, "#FF3FA4": 2, "#00E5FF": 0, "#FF4A1C": 2, "#111111": 1}


def usar_tema(nombre, semilla=""):
    """Activa un tema por nombre, o elige uno automáticamente (distinto por video) con 'auto'."""
    global TEMA
    if not nombre:
        TEMA = None
        return None
    if nombre == "auto":
        # rotar los temas en orden para que dos videos seguidos nunca se repitan
        from transformar import MODELOS
        claves = sorted(TEMAS)
        estado = os.path.join(MODELOS, "ultimo_tema.txt")
        previo = open(estado).read().strip() if os.path.exists(estado) else None
        nombre = claves[(claves.index(previo) + 1) % len(claves)] if previo in claves else claves[0]
        try:
            os.makedirs(MODELOS, exist_ok=True)
            open(estado, "w").write(nombre)
        except OSError:
            pass
    TEMA = dict(TEMAS[nombre], nombre=nombre)
    return nombre


def colores_sticker(fondo, color):
    if not TEMA:
        return fondo, color
    k = _MAPA_COLORES.get(str(fondo).upper(), 0)
    return TEMA["stickers"][k % len(TEMA["stickers"])]


def font(px, archivo=None):
    archivo = archivo or FUENTE
    if (px, archivo) not in _cache_font:
        _cache_font[(px, archivo)] = ImageFont.truetype(archivo, px)
    return _cache_font[(px, archivo)]


def es_emoji(s):
    return ord(s[0]) >= 0x2300


def separar(s):
    """Divide en grafemas simples (emoji con modificadores/ZWJ juntos)."""
    out, i = [], 0
    while i < len(s):
        j = i + 1
        if 0x1F1E6 <= ord(s[i]) <= 0x1F1FF and j < len(s) and 0x1F1E6 <= ord(s[j]) <= 0x1F1FF:
            j += 1                                  # banderas: dos letras regionales juntas (🇭🇳)
        while j < len(s) and (s[j] in "️⃣‍" or 0x1F3FB <= ord(s[j]) <= 0x1F3FF
                              or s[j - 1] == "‍"):
            j += 1
        out.append(s[i:j])
        i = j
    return out


def emoji_pil(e):
    global _EF
    if e not in _cache_emoji:
        if _EF is None:
            _EF = ImageFont.truetype(EMOJI_FONT, 109)
        img = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((10, 10), e, font=_EF, embedded_color=True)
        bb = img.getbbox() or (0, 0, 1, 1)
        _cache_emoji[e] = img.crop(bb)
    return _cache_emoji[e]


def texto_pil(texto, px, fill=(255, 255, 255), stroke=(0, 0, 0), sw=None, fuente=None, sombra=False):
    """Texto mixto (palabras + emojis) en una línea. Devuelve PIL RGBA."""
    sw = max(3, px // 10) if sw is None else sw
    f = font(px, fuente)
    asc, desc = f.getmetrics()
    alto = asc + desc + sw * 2
    piezas, buf = [], ""
    for g in separar(texto):
        if es_emoji(g):
            if buf:
                piezas.append(("t", buf))
                buf = ""
            piezas.append(("e", g))
        else:
            buf += g
    if buf:
        piezas.append(("t", buf))
    imgs = []
    for k, v in piezas:
        if k == "t":
            w = int(f.getlength(v)) + sw * 2
            im = Image.new("RGBA", (max(w, 1) + 6, alto + 6), (0, 0, 0, 0))
            if sombra:                                   # sombra suave debajo (no borde grueso)
                sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
                ImageDraw.Draw(sh).text((sw + 3, sw + 5), v, font=f, fill=(0, 0, 0, 150),
                                        stroke_width=sw, stroke_fill=(0, 0, 0, 150))
                from PIL import ImageFilter
                im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(4)))
            ImageDraw.Draw(im).text((sw, sw), v, font=f, fill=fill + (255,), stroke_width=sw if stroke else 0,
                                    stroke_fill=stroke + (255,) if stroke else None)
            imgs.append(im)
        else:
            e = emoji_pil(v)
            s = int(px * 1.1)
            e = e.resize((int(e.width * s / e.height), s), Image.LANCZOS)
            im = Image.new("RGBA", (e.width + 8, alto + 6), (0, 0, 0, 0))
            im.paste(e, (4, (alto - s) // 2 - sw // 2), e)
            imgs.append(im)
    tw = sum(i.width for i in imgs)
    out = Image.new("RGBA", (max(tw, 1), alto), (0, 0, 0, 0))
    x = 0
    for i in imgs:
        out.paste(i, (x, 0), i)
        x += i.width
    return out


def lineas_pil(texto, px, max_w, interlinea=0, **kw):
    lineas = [texto_pil(l, px, **kw) for l in texto.split("\n")]
    m = max(l.width for l in lineas)
    if m > max_w:
        px = int(px * max_w / m)
        lineas = [texto_pil(l, px, **kw) for l in texto.split("\n")]
    w = max(l.width for l in lineas)
    h = sum(l.height for l in lineas) + interlinea * (len(lineas) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for l in lineas:
        out.paste(l, ((w - l.width) // 2, y), l)
        y += l.height + interlinea
    return out


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def sticker_pil(texto, px, fondo="#FFE600", color="#111111", rot=-5, max_w=950):
    from PIL import ImageFilter
    fondo, color = colores_sticker(fondo, color)
    px = int(px * 0.9)
    txt = lineas_pil(texto, px, max_w - 100, interlinea=-int(px * 0.12), fill=hex2rgb(color),
                     stroke=None, sw=0, fuente=FUENTE_STICKER)
    padx, pady = int(px * 0.55), int(px * 0.32)
    w, h = txt.width + padx * 2, txt.height + pady * 2
    m = 40
    im = Image.new("RGBA", (w + m * 2, h + m * 2), (0, 0, 0, 0))
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((m + 4, m + 12, m + w + 4, m + h + 12), radius=int(h * 0.32),
                                             fill=(0, 0, 0, 90))
    im = Image.alpha_composite(im, sombra.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m, m, m + w, m + h), radius=int(min(h * 0.32, 60)), fill=hex2rgb(fondo) + (255,))
    # brillo sutil arriba (acabado tipo "glass")
    brillo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(brillo).rounded_rectangle((m + 6, m + 5, m + w - 6, m + h * 0.45), radius=int(min(h * 0.3, 50)),
                                             fill=(255, 255, 255, 28))
    im = Image.alpha_composite(im, brillo)
    im.paste(txt, (m + padx, m + pady), txt)
    return im.rotate(rot * 0.5, resample=Image.BICUBIC, expand=True)


def a_bgra(pil):
    a = np.array(pil)
    return np.dstack([a[..., 2], a[..., 1], a[..., 0], a[..., 3]])


def superponer(canvas, bgra, cx, cy, escala=1.0, rot=0.0, alpha=1.0):
    if escala <= 0.01 or alpha <= 0.01:
        return
    img = bgra
    if abs(escala - 1) > 0.01:
        img = cv2.resize(img, None, fx=escala, fy=escala,
                         interpolation=cv2.INTER_AREA if escala < 1 else cv2.INTER_LINEAR)
    if abs(rot) > 0.3:
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1)
        c, s = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(h * s + w * c), int(h * c + w * s)
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        img = cv2.warpAffine(img, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    h, w = img.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    CH, CW = canvas.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(CW, x0 + w), min(CH, y0 + h)
    if xa >= xb or ya >= yb:
        return
    sub = img[ya - y0:yb - y0, xa - x0:xb - x0]
    a = sub[..., 3:4].astype(np.float32) / 255 * alpha
    roi = canvas[ya:yb, xa:xb].astype(np.float32)
    canvas[ya:yb, xa:xb] = (roi * (1 - a) + sub[..., :3].astype(np.float32) * a).astype(np.uint8)


def ease_back(x):
    x = min(max(x, 0), 1)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_io(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------
# Efectos de sonido sintetizados (no requieren archivos ni licencias)
# --------------------------------------------------------------------------
def _fase(f):
    return 2 * np.pi * np.cumsum(f) / SR


def sintetizar(nombre):
    def tt(d):
        return np.arange(int(SR * d)) / SR
    if nombre == "pop":
        t = tt(0.12)
        y = np.sin(_fase(700 * np.exp(-t * 25) + 220)) * np.exp(-t * 30)
    elif nombre == "boing":
        t = tt(0.7)
        f = 160 + 90 * np.sin(2 * np.pi * 11 * t) * np.exp(-t * 2.5) + 120 * t
        y = np.sin(_fase(f)) * np.exp(-t * 4.5)
    elif nombre == "whoosh":
        t = tt(0.5)
        n = np.random.default_rng(1).standard_normal(len(t))
        k = np.ones(18) / 18
        n = np.convolve(n, k, "same") - np.convolve(n, np.ones(90) / 90, "same")
        y = n * np.sin(np.pi * t / t[-1]) ** 2 * 3
    elif nombre == "ding":
        t = tt(1.1)
        y = (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 3136 * t)
             + 0.2 * np.sin(2 * np.pi * 4704 * t)) * np.exp(-t * 4)
    elif nombre == "silbido":   # silbato que sube (el clásico "fiu fiu" pícaro)
        t = tt(0.6)
        f = 520 + 1400 * (t / t[-1]) ** 1.6 + 25 * np.sin(2 * np.pi * 7 * t)
        y = np.sin(_fase(f)) * np.minimum(1, t * 30) * np.minimum(1, (t[-1] - t) * 12)
    elif nombre == "bajada":    # "wah wah wah" de fracaso
        notas = [(392, .28), (370, .28), (349, .28), (330, .8)]
        parts = []
        for f0, d in notas:
            t = tt(d)
            f = f0 * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
            ph = _fase(f)
            parts.append((np.sin(ph) + 0.35 * np.sin(3 * ph) + 0.15 * np.sin(5 * ph))
                         * np.minimum(1, t * 40) * np.minimum(1, (t[-1] - t) * 10))
        y = np.concatenate(parts)
    elif nombre == "scratch":   # disco rayado (congelado de imagen)
        t = tt(0.45)
        f = 300 + 1700 * np.abs(np.sin(2 * np.pi * 2.6 * t)) * np.exp(-t * 1.5)
        ph = _fase(f)
        saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
        n = np.random.default_rng(3).standard_normal(len(t)) * 0.25
        y = (saw * 0.7 + n) * np.exp(-t * 3) * np.minimum(1, t * 200)
    elif nombre == "beep":       # pitido de censura (1 kHz)
        t = tt(0.4)
        y = np.sin(2 * np.pi * 1000 * t) * np.minimum(1, t * 300) * np.minimum(1, (t[-1] - t) * 300)
        return (y * 0.55).astype(np.float32)
    elif nombre == "boom":
        t = tt(1.3)
        y = np.tanh(3 * np.sin(_fase(65 * np.exp(-t * 1.8) + 32))) * np.exp(-t * 3.2)
    else:
        return np.zeros(1, np.float32)
    y = y / (np.abs(y).max() + 1e-9) * 0.8
    return y.astype(np.float32)


# --------------------------------------------------------------------------
# Eventos
# --------------------------------------------------------------------------
class Eventos:
    def __init__(self, eventos, panel):
        self.ev = sorted(eventos, key=lambda e: e["t"])
        self.panel = panel
        self.cache = {}
        for i, e in enumerate(self.ev):
            e.setdefault("dur", 1.5)
            e["_i"] = i
            if e["tipo"] in ("lluvia", "rafaga"):
                rng = np.random.default_rng(100 + i)
                n = e.get("n", 18 if e["tipo"] == "lluvia" else 10)
                em = separar(e["emoji"])
                e["_p"] = [dict(e=em[k % len(em)], x=rng.random(), y=rng.random(), v=rng.random(),
                                r=rng.random(), s=rng.random(), a=rng.random() * 6.28) for k in range(n)]

    def activos(self, t):
        return [e for e in self.ev if e["t"] <= t < e["t"] + e["dur"]]

    def img(self, key, fn):
        if key not in self.cache:
            self.cache[key] = fn()
        return self.cache[key]

    def zoom(self, t):
        """Devuelve (cx, cy, s) relativos a la fuente."""
        cx, cy, s = 0.5, 0.5, 1.0 + 0.03 * math.sin(t * 0.5)
        for e in self.ev:
            if e["tipo"] != "zoom":
                continue
            u = t - e["t"]
            rampa = e.get("rampa", 0.25)
            if 0 <= u < e["dur"]:
                k = ease_io(min(u / rampa, (e["dur"] - u) / rampa, 1))
                if e.get("lento"):
                    k = ease_io(u / e["dur"])
                cx = cx + (e["x"] - cx) * k
                cy = cy + (e["y"] - cy) * k
                s = s + (e["s"] - s) * k
        return cx, cy, s

    def temblor(self, t):
        dx = dy = 0.0
        for e in self.ev:
            if e["tipo"] == "temblor" or (e.get("temblor") and e["tipo"] != "temblor"):
                d = e["dur"] if e["tipo"] == "temblor" else 0.4
                u = t - e["t"]
                if 0 <= u < d:
                    amp = e.get("amp", 18) * (1 - u / d)
                    dx += amp * math.sin(u * 70)
                    dy += amp * math.cos(u * 57)
        return dx, dy

    def flash(self, t):
        a = 0.0
        for e in self.ev:
            if e["tipo"] == "flash" or e.get("flash"):
                u = t - e["t"]
                d = e["dur"] if e["tipo"] == "flash" else 0.25
                if 0 <= u < d:
                    a = max(a, 0.85 * (1 - u / d))
        return a

    def dibujar(self, cv, t):
        for e in self.activos(t):
            u = t - e["t"]
            d = e["dur"]
            fin = max(0.0, 1 - (d - u) / 0.22)        # 0..1 en los últimos 0.22 s
            tipo = e["tipo"]
            if tipo == "emoji":
                px = e.get("size", 260)
                im = self.img(("e", e["emoji"], px), lambda: a_bgra(texto_pil(e["emoji"], px, stroke=None, sw=0)))
                sc = ease_back(u / 0.28) * (1 - fin)
                rot = e.get("rot", 0) + 9 * math.sin(u * 6 + e["_i"])
                ex, ey = seguro(e["x"], e["y"], ymax=0.55)
                y = ey * H - 14 * math.sin(u * 3.2)
                superponer(cv, im, ex * W, y, sc, rot)
            elif tipo == "sticker":
                px = e.get("size", 80)
                im = self.img(("s", e["_i"]), lambda: a_bgra(sticker_pil(
                    e["texto"], px, e.get("fondo", "#FFE600"), e.get("color", "#111111"), e.get("rot", -4))))
                sc = ease_back(u / 0.3) * (1 - fin) * (1 + 0.025 * math.sin(u * 5))
                superponer(cv, im, e.get("x", 0.5) * W, max(e.get("y", 0.28), 0.275) * H, sc)
            elif tipo == "lluvia":
                for p in e["_p"]:
                    px = int(90 + 80 * p["s"])
                    im = self.img(("e", p["e"], px), lambda: a_bgra(texto_pil(p["e"], px, stroke=None, sw=0)))
                    y = -150 - p["y"] * 700 + (800 + 700 * p["v"]) * u
                    x = p["x"] * W + 40 * math.sin(u * 2 + p["a"])
                    superponer(cv, im, x, y, 1.0, (p["r"] - 0.5) * 60 + 90 * u * (p["v"] - .5), 1 - fin)
            elif tipo == "rafaga":
                ox, oy = [v * k for v, k in zip(seguro(e.get("x", 0.5), e.get("y", 0.5)), (W, H))]
                for p in e["_p"]:
                    px = int(110 + 70 * p["s"])
                    im = self.img(("e", p["e"], px), lambda: a_bgra(texto_pil(p["e"], px, stroke=None, sw=0)))
                    ang = p["a"]
                    dist = (420 + 380 * p["v"]) * (1 - math.exp(-u * 3.5))
                    x = ox + math.cos(ang) * dist
                    y = oy + math.sin(ang) * dist + 350 * u * u
                    superponer(cv, im, x, y, ease_back(u / 0.25) * (0.7 + 0.5 * u / d), 30 * u, 1 - fin)


# --------------------------------------------------------------------------
# Subtítulos con palabras clave resaltadas
# --------------------------------------------------------------------------
class Subs:
    def __init__(self, palabras, claves, color_activo, color_clave="#FF3FA4", px=104, y=0.875, x=0.5, ancho=0.92):
        self.claves = [c.lower() for c in claves]
        self.act = tuple(int(c) for c in color_activo[::-1])
        self.cla = hex2rgb(color_clave)
        self.pastilla = None
        if TEMA:
            self.pastilla = (hex2rgb(TEMA["acento"][0]), hex2rgb(TEMA["acento"][1]))
            self.cla = hex2rgb(TEMA["clave"])
        y = min(y, 0.75)                                   # encima del nombre de la página
        if x + ancho / 2 > ZONA["derecha"] - 0.01:          # antes de la columna de íconos
            ancho = max(0.42, 2 * (ZONA["derecha"] - 0.01 - x))
            x = min(x, ZONA["derecha"] - 0.01 - ancho / 2)
        self.px, self.y, self.x, self.ancho = px, y, x, ancho
        # con poco espacio (al lado del presentador) van de a 2 palabras para que se lean grandes
        self.grupos = agrupar(palabras, max_pal=2 if ancho < 0.6 else 3)
        self.cache = {}
        self.i = 0

    def es_clave(self, w):
        w = re.sub(r"[^\wáéíóúñü]", "", w.lower())
        return any(c in w for c in self.claves) if w else False

    def render(self, gi, wi):
        if (gi, wi) in self.cache:
            return self.cache[(gi, wi)]
        g = self.grupos[gi]
        px = int(self.px * 0.92)
        f = font(px, FUENTE_SUBS)
        sw = max(2, px // 26)                                  # borde fino, no grueso
        palabras = [(tapar_palabra(w["t"]) if (es_groseria(w["t"]) or w.get("censura")) else w["t"]).upper() for w in g]
        imgs = []
        for i, p in enumerate(palabras):
            clave = self.es_clave(p)
            if i == wi and self.pastilla:
                # palabra activa: pastilla de color con texto en contraste
                t_img = texto_pil(p, px, fill=self.pastilla[1], stroke=None, sw=0, fuente=FUENTE_SUBS)
                pad = int(px * 0.18)
                bg = Image.new("RGBA", (t_img.width + pad * 2, t_img.height + pad), (0, 0, 0, 0))
                ImageDraw.Draw(bg).rounded_rectangle((0, int(pad * 0.6), bg.width - 1, bg.height - 1),
                                                     radius=int(px * 0.28), fill=self.pastilla[0] + (255,))
                bg.paste(t_img, (pad, int(pad * 0.5)), t_img)
                imgs.append(bg)
            else:
                col = self.act if (i == wi and not self.pastilla) else (self.cla if clave else (255, 255, 255))
                imgs.append(texto_pil(p, px, fill=col, stroke=(20, 20, 30), sw=sw, fuente=FUENTE_SUBS, sombra=True))
        esp = int(f.getlength(" ") * 0.9)
        w = sum(i.width for i in imgs) + esp * (len(imgs) - 1)
        h = max(i.height for i in imgs)
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = 0
        for i in imgs:
            out.paste(i, (x, (h - i.height) // 2), i)
            x += i.width + esp
        if out.width > W * self.ancho:
            out = out.resize((int(W * self.ancho), int(out.height * W * self.ancho / out.width)), Image.LANCZOS)
        self.cache[(gi, wi)] = a_bgra(out)
        return self.cache[(gi, wi)]

    def dibujar(self, cv, t):
        if not self.grupos:
            return
        while self.i < len(self.grupos) - 1 and t > self.grupos[self.i][-1]["b_vis"]:
            self.i += 1
        g = self.grupos[self.i]
        if t < g[0]["a"] or t > g[-1]["b_vis"]:
            return
        wi = max([k for k, w in enumerate(g) if t >= w["a"]] or [0])
        dt = t - g[0]["a"]
        sc = 0.8 + 0.2 * ease_back(dt / 0.15)
        superponer(cv, self.render(self.i, wi), W * self.x, self.y * H, sc)


# --------------------------------------------------------------------------
# Plan automático a partir de palabras clave
# --------------------------------------------------------------------------
def plan_auto(palabras):
    ev, ultimo, lado = [], -10, 0
    for w in palabras:
        txt = w["t"].lower()
        for patron, emojis, sfx in CLAVES_AUTO:
            if re.search(patron, txt) and w["a"] - ultimo > 1.6:
                lado = 1 - lado
                for k, em in enumerate(separar(emojis)):
                    ev.append(dict(t=w["a"] + 0.12 * k, tipo="emoji", emoji=em, dur=1.6,
                                   x=0.22 + 0.56 * lado + (0.12 if k else 0) * (1 if lado == 0 else -1),
                                   y=0.38 + 0.06 * k, size=240 - 40 * k))
                ev.append(dict(t=w["a"], tipo="sfx", sfx=sfx, dur=0.1))
                ultimo = w["a"]
                break
    return ev


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--plan", help="JSON con titulo, eventos, palabras clave")
    ap.add_argument("--auto", action="store_true", help="agregar efectos automáticos por palabra clave")
    ap.add_argument("--palabras", help="JSON de palabras [{t,a,b}] (si no, se transcribe)")
    ap.add_argument("--estilo", default=None)
    ap.add_argument("--whisper", default="large-v3-turbo")
    ap.add_argument("--vol-sfx", type=float, default=0.5)
    ap.add_argument("--sin-barra", action="store_true")
    args = ap.parse_args()

    plan = json.load(open(args.plan)) if args.plan else {}
    usar_tema(plan.get("tema"), os.path.basename(args.entrada))
    est = ESTILOS[TEMA["base"] if TEMA else (args.estilo or plan.get("estilo", "farandula"))]
    tmp = tempfile.mkdtemp(prefix="efx_")
    src = args.entrada

    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    paso = max(1, round(fps / 30))          # 60 fps -> procesar a 30
    fps, n = fps / paso, n // paso
    rf = plan.get("recorte_fuente")        # [x0,y0,x1,y1] relativo: quita textos/bordes del original
    if rf:
        rx0, ry0, rx1, ry1 = int(rf[0] * sw), int(rf[1] * sh), int(rf[2] * sw), int(rf[3] * sh)
        sw, sh = rx1 - rx0, ry1 - ry0
    dur = n / fps

    audio = tiene_audio(src)
    energia = np.zeros(n + 1, np.float32)
    palabras = []
    if audio:
        wav = extraer_wav(src, tmp)
        energia = energia_por_frame(wav, fps, n + 1)
        if args.palabras or plan.get("palabras"):
            palabras = json.load(open(args.palabras or plan["palabras"]))
        else:
            palabras = transcribir(wav, "es", args.whisper)
    # censura: groserías detectadas + rangos manuales del plan ("censura": [[a, b], ...])
    censuras = [tuple(c) for c in plan.get("censura", [])]
    for w in palabras:
        manual = any(a <= (w["a"] + w["b"]) / 2 <= b for a, b in censuras)
        if es_groseria(w["t"]) or manual:
            w["censura"] = True
            if not manual:
                censuras.append((w["a"], w["b"]))
    censuras = sorted((max(0.0, a - 0.03), b + 0.05) for a, b in censuras)
    if censuras:
        log(f"censura con pitido en: {[(round(a, 2), round(b, 2)) for a, b in censuras]}")
    eventos = list(plan.get("eventos", []))
    if args.auto:
        eventos += plan_auto(palabras)

    # Formato "split": creador arriba (video de reacción real), clip abajo, sin decoración.
    split = plan.get("formato") == "split"
    reac = reac_eventos = None
    if split:
        from reaccion import Reaccion
        # 9:16 sin espacios vacíos: franja animada arriba (bajo la barra de la app), creador,
        # línea de color animada y el clip hasta el borde de abajo.
        plan.setdefault("panel_ancho", W)
        plan.setdefault("panel_y", 0.43 * H)
        plan.setdefault("panel_abajo", 1.0)
        plan.setdefault("panel_alto", 1.0 - 0.43)
        plan.setdefault("subs_x", 0.5)
        plan.setdefault("subs_ancho", 0.74)
        plan.setdefault("subs_y", 0.72)
        cat = plan.get("catalogo_reaccion")
        if not cat:
            cfg_path = os.path.join(os.path.expanduser("~"), ".estudio", "config.json")
            cat = (json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}).get("reaccion")
        reac_y0 = int(0.105 * H)
        reac_h = int(W * 9 / 16)
        reac = Reaccion(cat, W, reac_h)
        reac_eventos = [dict(ev) for ev in plan.get("reacciones", [])]

    # Panel del video
    pw = plan.get("panel_ancho", 1000)
    ph = int(sh * pw / sw)
    ph_max = int(plan.get("panel_abajo", 0.72) * H) - int(plan.get("panel_y", 0.225 * H))
    if plan.get("panel_alto"):                # videos horizontales: panel más alto, recorta los lados siguiendo el zoom
        ph = int(plan["panel_alto"] * H)
    if ph > ph_max:
        ph = ph_max            # se mantiene el ancho completo: se recorta arriba/abajo siguiendo el zoom
    px0, py0 = (W - pw) // 2, int(plan.get("panel_y", 0.225 * H))
    radio = 0 if split else 38
    mask = np.zeros((ph, pw), np.uint8)
    cv2.rectangle(mask, (radio, 0), (pw - radio, ph), 255, -1)
    cv2.rectangle(mask, (0, radio), (pw, ph - radio), 255, -1)
    for cx, cy in [(radio, radio), (pw - radio, radio), (radio, ph - radio), (pw - radio, ph - radio)]:
        if radio:
            cv2.circle(mask, (cx, cy), radio, 255, -1, cv2.LINE_AA)
    mask_f = (mask.astype(np.float32) / 255)[..., None]
    borde = np.zeros((H, W), np.float32)
    borde[py0:py0 + ph, px0:px0 + pw] = mask_f[..., 0]
    glow = np.clip(cv2.GaussianBlur(borde, (0, 0), 22) * 2.2 - borde, 0, 1)[..., None]
    glow_col = np.array(est["glow"], np.float32)

    fondo = FondoAnimado(W, H, est)
    if split:                                            # sin brillo alrededor del clip
        glow = glow * 0
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        fondo_liso = (np.array([18, 16, 14], np.float32) * (1 - yy) + np.array([30, 24, 22], np.float32) * yy) \
            * np.ones((1, W, 1), np.float32)
    grad = Grading(pw, ph, est)
    evs = Eventos(eventos, (px0, py0, pw, ph))
    subs = Subs(palabras, plan.get("claves", []), est["palabra"], y=plan.get("subs_y", 0.875),
                x=plan.get("subs_x", 0.5), ancho=plan.get("subs_ancho", 0.92)) if palabras else None
    titulo = plan.get("titulo")
    titulo_img = None
    if titulo:
        tf, tc = TEMA["titulo"] if TEMA else (plan.get("titulo_fondo", "#FFFFFF"), plan.get("titulo_color", "#111111"))
        _t = TEMA
        globals()["TEMA"] = None                          # el título usa su color propio, sin remapear
        titulo_img = a_bgra(sticker_pil(titulo, 78, tf, tc, rot=0, max_w=1000))
        globals()["TEMA"] = _t
    barra_col = tuple(int(c) for c in est["palabra"])

    out_v = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-", "-c:v", "libx264", "-preset",
                            "medium", "-crf", "19", "-pix_fmt", "yuv420p", out_v], stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, fr = cap.read()
        for _ in range(paso - 1):
            cap.grab()
        if not ok:
            break
        for tx0, ty0, tx1, ty1 in plan.get("tapar", []):
            hh, ww = fr.shape[:2]
            a0, b0, a1, b1 = int(tx0 * ww), int(ty0 * hh), int(tx1 * ww), int(ty1 * hh)
            zona = fr[b0:b1, a0:a1]
            if zona.size:
                peq = cv2.resize(zona, (max(1, zona.shape[1] // 14), max(1, zona.shape[0] // 14)),
                                 interpolation=cv2.INTER_AREA)
                fr[b0:b1, a0:a1] = cv2.GaussianBlur(cv2.resize(peq, (zona.shape[1], zona.shape[0]),
                                                               interpolation=cv2.INTER_LINEAR), (0, 0), 6)
        if rf:
            fr = fr[ry0:ry1, rx0:rx1]
        t = i / fps
        e = float(min(energia[min(i, len(energia) - 1)], 1.0))
        cv = fondo.frame(t, e).astype(np.float32)
        cv += glow * glow_col * (0.55 + 0.6 * e)
        # panel con zoom virtual
        zx, zy, zs = evs.zoom(t)
        base_w = min(sw, sh * pw / ph)          # ventana con la misma forma que el panel
        cw, chh = base_w / zs, base_w * ph / pw / zs
        x0 = min(max(zx * sw - cw / 2, 0), sw - cw)
        y0 = min(max(zy * sh - chh / 2, 0), sh - chh)
        M = np.float32([[pw / cw, 0, -x0 * pw / cw], [0, ph / chh, -y0 * ph / chh]])
        panel = cv2.warpAffine(fr, M, (pw, ph), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        panel = grad.persona(panel)
        roi = cv[py0:py0 + ph, px0:px0 + pw]
        cv[py0:py0 + ph, px0:px0 + pw] = panel * mask_f + roi * (1 - mask_f)
        if split:                                        # el creador reaccionando, arriba
            cv[reac_y0:reac_y0 + reac_h] = reac.cuadro(t, reac_eventos)
            # línea de color con un brillo que la recorre (separa creador y clip)
            l0, l1 = reac_y0 + reac_h, py0
            acento = np.array(est["palabra"], np.float32)
            cv[l0:l1] = acento * 0.85
            bx = int((t * 0.35 % 1.0) * (W + 400)) - 200
            xs = np.arange(W, dtype=np.float32)
            brillo = np.exp(-((xs - bx) / 90.0) ** 2)[None, :, None]
            cv[l0:l1] = cv[l0:l1] * (1 - brillo * 0.7) + 255 * brillo * 0.7
        cv = np.clip(cv, 0, 255).astype(np.uint8)
        if titulo_img is not None:
            sc = ease_back(t / 0.35) if t < 0.35 else 1 + 0.015 * math.sin(t * 3)
            superponer(cv, titulo_img, W / 2, plan.get("titulo_y", 0.163) * H, sc)
        evs.dibujar(cv, t)
        if subs:
            subs.dibujar(cv, t)
        if not args.sin_barra:
            cv2.rectangle(cv, (0, H - 14), (int(W * t / dur), H), barra_col, -1)
        dx, dy = evs.temblor(t)
        if dx or dy:
            cv = cv2.warpAffine(cv, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        fa = evs.flash(t)
        if fa > 0:
            cv = cv2.addWeighted(cv, 1 - fa, np.full_like(cv, 255), fa, 0)
        enc.stdin.write(cv.tobytes())
        i += 1
        if i % 60 == 0:
            log(f"  frame {i}/{n}")
    cap.release()
    enc.stdin.close()
    enc.wait()

    # pista de efectos de sonido
    pista = np.zeros(int((dur + 2) * SR), np.float32)
    for ev in eventos:
        s = ev.get("sfx")
        if s:
            y = sintetizar(s) * ev.get("vol", 1.0)
            a = int(ev["t"] * SR)
            b = min(len(pista), a + len(y))
            pista[a:b] += y[:b - a]
    for ca, cb in censuras:                         # pitido del largo exacto de la palabra
        n = int((cb - ca) * SR)
        tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * 1000 * tt) * np.minimum(1, tt * 300) * np.minimum(1, (tt[-1] - tt) * 300 if n else 1)
        a = int(ca * SR)
        b = min(len(pista), a + n)
        pista[a:b] += (y[:b - a] * 0.45 / max(args.vol_sfx, 0.05)).astype(np.float32)
    bajar = ""
    if split and reac_eventos:
        voz_r, ventanas = reac.audio(reac_eventos, dur, SR)
        n = min(len(pista), len(voz_r))
        pista[:n] += voz_r[:n] / max(args.vol_sfx, 0.05)
        if ventanas:
            cond = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in ventanas)
            bajar = f"volume=volume=0.4:enable='{cond}',"
    for v in plan.get("voces", []):                 # voz en off del creador sobre el clip
        import soundfile as sf
        x, sr_v = sf.read(v["wav"], dtype="float32")
        if x.ndim > 1:
            x = x.mean(1)
        if sr_v != SR:
            x = np.interp(np.arange(0, len(x), sr_v / SR), np.arange(len(x)), x).astype(np.float32)
        i0 = int(v["t"] * SR)
        i1 = min(len(pista), i0 + len(x))
        pista[i0:i1] += x[:i1 - i0] * 1.1 / max(args.vol_sfx, 0.05)
        cond = f"between(t,{v['t']:.3f},{v['t'] + v['dur']:.3f})"
        bajar += f"volume=volume=0.18:enable='{cond}',"
    pista = np.clip(pista, -1, 1)
    sfx_wav = os.path.join(tmp, "sfx.wav")
    import wave
    with wave.open(sfx_wav, "w") as wv:
        wv.setnchannels(1)
        wv.setsampwidth(2)
        wv.setframerate(SR)
        wv.writeframes((pista * 32767).astype(np.int16).tobytes())

    silenciar = ""
    if censuras:
        cond = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in censuras)
        silenciar = f"volume=volume=0:enable='{cond}',"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", out_v]
    if audio:
        cmd += ["-i", src, "-i", sfx_wav, "-filter_complex",
                f"[1:a]aresample={SR},{silenciar}{bajar}loudnorm=I=-15:TP=-2,aresample={SR}[v];[2:a]volume={args.vol_sfx}[s];"
                "[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[m]",
                "-map", "0:v", "-map", "[m]"]
    else:
        cmd += ["-i", sfx_wav, "-map", "0:v", "-map", "1:a", "-shortest"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.salida]
    subprocess.run(cmd, check=True)
    log(f"listo -> {args.salida}")


if __name__ == "__main__":
    main()
