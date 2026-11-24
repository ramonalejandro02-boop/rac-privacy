#!/usr/bin/env python3
"""
Estudio de transformación de video (reacciones / farándula).

Toma un video y produce uno nuevo con:
  - Motion graphics animados DETRÁS de la persona (separa persona y fondo con IA)
  - Borde de luz (glow) alrededor de la persona
  - Seguimiento de cara + zoom de énfasis cuando la voz sube
  - Corrección de color / look cinematográfico
  - Subtítulos automáticos estilo TikTok (palabra activa resaltada)
  - Reencuadre a 9:16 (o 16:9 / 1:1)

Uso:
  python3 studio/transformar.py entrada.mp4 salida.mp4 --estilo farandula
  python3 studio/transformar.py entrada.mp4 salida.mp4 --estilo neon --formato 16:9 --fondo blur
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELOS = os.environ.get("STUDIO_MODELS") or (
    "/home/user/models" if os.path.isdir("/home/user/models")
    else os.path.join(os.path.expanduser("~"), ".estudio", "models"))
FUENTE = os.path.join(AQUI, "fonts", "Anton-Regular.ttf")
if not os.path.exists(FUENTE):
    FUENTE = os.path.join(AQUI, "fonts", "InterDisplay-ExtraBold.otf")

# --------------------------------------------------------------------------
# Estilos: paleta del fondo animado, color del glow, color de palabra activa
# y parámetros del color grading. Colores en BGR.
# --------------------------------------------------------------------------
ESTILOS = {
    "farandula": dict(
        grad=[(120, 20, 90), (200, 40, 230), (40, 170, 255)],   # morado -> magenta -> dorado
        rayos=(255, 255, 255), rayos_alpha=0.16, glow=(80, 220, 255),
        palabra=(0, 230, 255), sat=1.25, contraste=0.22, calido=0.08, viñeta=0.35,
        particulas=(200, 255, 255)),
    "neon": dict(
        grad=[(40, 10, 20), (90, 20, 60), (60, 30, 10)],
        rayos=(255, 80, 255), rayos_alpha=0.10, glow=(255, 255, 0),
        palabra=(255, 255, 0), sat=1.35, contraste=0.28, calido=-0.04, viñeta=0.45,
        particulas=(255, 120, 255), anillos=True),
    "drama": dict(
        grad=[(10, 10, 30), (20, 20, 140), (10, 10, 60)],
        rayos=(60, 60, 255), rayos_alpha=0.18, glow=(40, 40, 255),
        palabra=(60, 60, 255), sat=1.05, contraste=0.32, calido=0.02, viñeta=0.55,
        particulas=(120, 120, 255)),
    "noticiero": dict(
        grad=[(90, 30, 10), (160, 70, 20), (60, 20, 5)],
        rayos=(255, 200, 120), rayos_alpha=0.08, glow=(255, 220, 160),
        palabra=(40, 210, 255), sat=1.15, contraste=0.18, calido=0.03, viñeta=0.30,
        particulas=(255, 230, 200)),
}

def _bgr(h):
    h = h.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))


def _estilo(c0, c1, c2, patron, glow="#FFFFFF", part="#FFFFFF", acento="#FFD166", sat=1.15, cont=0.18):
    return dict(grad=[_bgr(c0), _bgr(c1), _bgr(c2)], rayos=(255, 255, 255), rayos_alpha=0.07,
                glow=_bgr(glow), palabra=_bgr(acento), sat=sat, contraste=cont, calido=0.03,
                viñeta=0.30, particulas=_bgr(part), patron=patron)


ESTILOS.update({
    # Caribe
    "caribe": _estilo("#00B4D8", "#0077B6", "#023E8A", "ondas", glow="#90E0EF", acento="#FFD166"),
    "caribe2": _estilo("#48CAE4", "#00B4D8", "#03045E", "burbujas", glow="#CAF0F8", acento="#FFD166"),
    "caribe3": _estilo("#0096C7", "#023E8A", "#03045E", "puntos", glow="#90E0EF", acento="#EF476F"),
    # Atardecer
    "atardecer": _estilo("#F9A26C", "#F25F5C", "#7B2D8E", "burbujas", glow="#FFD6A5", acento="#FFE66D"),
    "atardecer2": _estilo("#FFB347", "#FF6F61", "#6A0572", "ondas", glow="#FFE5B4", acento="#FFE66D"),
    "atardecer3": _estilo("#F25F5C", "#B5179E", "#3A0CA3", "puntos", glow="#FFC6FF", acento="#FFE66D"),
    # Menta
    "menta": _estilo("#7FD8BE", "#2A9D8F", "#1D4E57", "puntos", glow="#D8F3DC", acento="#FF6B6B"),
    "menta2": _estilo("#95D5B2", "#40916C", "#1B4332", "ondas", glow="#D8F3DC", acento="#FFE66D"),
    "menta3": _estilo("#4ECDC4", "#1A759F", "#184E77", "burbujas", glow="#CAF0F8", acento="#FF6B6B"),
    # Noche
    "noche": _estilo("#2E2A5E", "#1B1B3A", "#0B0B1A", "rayos", glow="#7CFFCB", part="#7CFFCB", acento="#7CFFCB", cont=0.24),
    "noche2": _estilo("#3A1C71", "#1B1B3A", "#0B0B1A", "puntos", glow="#FF7AC6", part="#FF7AC6", acento="#FF7AC6", cont=0.24),
    "noche3": _estilo("#16324F", "#0B1D33", "#050D1A", "ondas", glow="#7CFFCB", part="#B8F2FF", acento="#7CFFCB", cont=0.24),
})

FORMATOS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}


def log(*a):
    print("[studio]", *a, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------
# Audio: extracción, energía por frame y transcripción
# --------------------------------------------------------------------------
def tiene_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                          "-show_entries", "stream=index", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return bool(out)


def extraer_wav(path, tmpdir):
    wav = os.path.join(tmpdir, "audio.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000",
                    "-vn", wav], check=True)
    return wav


def energia_por_frame(wav, fps, n_frames):
    with wave.open(wav) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr / fps
    e = np.zeros(n_frames, np.float32)
    for i in range(n_frames):
        a, b = int(i * hop), int((i + 1) * hop)
        if a >= len(x):
            break
        seg = x[a:b]
        e[i] = math.sqrt(float(np.mean(seg * seg))) if len(seg) else 0
    if e.max() > 0:
        e = e / (np.percentile(e, 98) + 1e-6)
    return np.clip(e, 0, 1.5)


def transcribir(wav, idioma, modelo):
    from faster_whisper import WhisperModel
    log(f"transcribiendo (whisper {modelo})...")
    m = WhisperModel(modelo, device="cpu", compute_type="int8",
                     download_root=os.path.join(MODELOS, "whisper"))
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    segs, info = m.transcribe(x, language=idioma, word_timestamps=True, vad_filter=True)
    palabras = []
    for s in segs:
        for w in (s.words or []):
            t = w.word.strip()
            if t:
                palabras.append(dict(t=t, a=w.start, b=w.end))
    log(f"  {len(palabras)} palabras, idioma={info.language}")
    return palabras


def agrupar(palabras, max_pal=3, pausa=0.45):
    grupos, act = [], []
    for w in palabras:
        if act and (len(act) >= max_pal or w["a"] - act[-1]["b"] > pausa
                    or act[-1]["t"][-1:] in ".?!,"):
            grupos.append(act)
            act = []
        act.append(w)
    if act:
        grupos.append(act)
    for g in grupos:   # extender el grupo hasta el siguiente para que no parpadee
        g_end = g[-1]["b"]
        g[-1]["b_vis"] = g_end + 0.25
    return grupos


# --------------------------------------------------------------------------
# Subtítulos animados
# --------------------------------------------------------------------------
class Subtitulos:
    def __init__(self, grupos, ancho, color_activo, tam):
        self.grupos = grupos
        self.ancho = ancho
        self.activo = tuple(int(c) for c in color_activo[::-1])  # BGR -> RGB
        self.font = ImageFont.truetype(FUENTE, tam)
        self.cache = {}
        self.idx = 0

    def _render(self, gi, wi):
        key = (gi, wi)
        if key in self.cache:
            return self.cache[key]
        g = self.grupos[gi]
        palabras = [w["t"].upper() for w in g]
        esp = self.font.getlength(" ")
        anchos = [self.font.getlength(p) for p in palabras]
        total = sum(anchos) + esp * (len(palabras) - 1)
        escala = min(1.0, (self.ancho * 0.9) / max(total, 1))
        font = self.font if escala >= 1 else ImageFont.truetype(FUENTE, int(self.font.size * escala))
        anchos = [font.getlength(p) for p in palabras]
        esp = font.getlength(" ")
        total = sum(anchos) + esp * (len(palabras) - 1)
        asc, desc = font.getmetrics()
        borde = max(4, font.size // 9)
        W, H = int(total + borde * 4), int(asc + desc + borde * 4)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = borde * 2
        for i, p in enumerate(palabras):
            col = self.activo if i == wi else (255, 255, 255)
            d.text((x, borde * 2), p, font=font, fill=col + (255,),
                   stroke_width=borde, stroke_fill=(0, 0, 0, 255))
            x += anchos[i] + esp
        arr = np.array(img)
        rgba = np.dstack([arr[..., 2], arr[..., 1], arr[..., 0], arr[..., 3]])  # a BGRA
        # sombra suave
        sombra = cv2.GaussianBlur(rgba[..., 3], (0, 0), borde)
        self.cache[key] = (rgba, sombra)
        return self.cache[key]

    def dibujar(self, frame, t, y_rel=0.72):
        while self.idx < len(self.grupos) - 1 and t > self.grupos[self.idx][-1].get("b_vis", 0):
            self.idx += 1
        if not self.grupos:
            return
        g = self.grupos[self.idx]
        if t < g[0]["a"] or t > g[-1].get("b_vis", g[-1]["b"]):
            return
        wi = 0
        for i, w in enumerate(g):
            if t >= w["a"]:
                wi = i
        rgba, sombra = self._render(self.idx, wi)
        # animación "pop" al aparecer el grupo
        dt = t - g[0]["a"]
        s = 1.0 + 0.18 * max(0.0, 1 - dt / 0.12) if dt < 0.12 else 1.0
        if dt < 0.12:
            s = 0.75 + 0.25 * (dt / 0.12) + 0.08 * math.sin(dt / 0.12 * math.pi)
        if abs(s - 1) > 0.01:
            rgba = cv2.resize(rgba, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
            sombra = cv2.resize(sombra, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        h, w = rgba.shape[:2]
        H, W = frame.shape[:2]
        x0, y0 = (W - w) // 2, int(H * y_rel - h / 2)
        pegar(frame, rgba, sombra, x0, y0)


def pegar(frame, rgba, sombra, x0, y0):
    H, W = frame.shape[:2]
    h, w = rgba.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    sub = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    sh = sombra[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)[..., None] / 255 * 0.6
    roi = frame[ya:yb, xa:xb].astype(np.float32)
    roi *= (1 - sh)
    a = sub[..., 3:4].astype(np.float32) / 255
    roi = roi * (1 - a) + sub[..., :3].astype(np.float32) * a
    frame[ya:yb, xa:xb] = roi.astype(np.uint8)


# --------------------------------------------------------------------------
# Fondo animado (motion graphics)
# --------------------------------------------------------------------------
class FondoAnimado:
    def __init__(self, W, H, est, seed=7):
        self.W, self.H, self.e = W, H, est
        self.w, self.h = W // 3, H // 3          # se calcula a 1/3 y se escala (rápido)
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        cx, cy = self.w / 2, self.h * 0.42
        self.ang = np.arctan2(yy - cy, xx - cx)
        self.rad = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(self.w, self.h)
        self.yn = yy / self.h
        self.xn = xx / self.w
        rng = np.random.default_rng(seed)
        self.patron = est.get("patron", "rayos")
        nb = 9
        self.burb = dict(x=rng.random(nb), y=rng.random(nb), r=0.10 + rng.random(nb) * 0.16,
                         vx=(rng.random(nb) - 0.5) * 0.03, vy=-0.01 - rng.random(nb) * 0.025, f=rng.random(nb) * 6.28)
        n = 45 if self.patron != "rayos" else 60
        self.p = dict(x=rng.random(n) * W, y=rng.random(n) * H, v=40 + rng.random(n) * 120,
                      r=2 + rng.random(n) * 6, f=rng.random(n) * 6.28)

    def frame(self, t, energia):
        e = self.e
        c0, c1, c2 = [np.array(c, np.float32) for c in e["grad"]]
        # gradiente diagonal que se mueve
        g = (self.yn * 0.7 + self.xn * 0.3 + 0.15 * np.sin(t * 0.6 + self.xn * 3))[..., None]
        g = np.clip(g, 0, 1)
        img = np.where(g < 0.5, c0 + (c1 - c0) * (g / 0.5), c1 + (c2 - c1) * ((g - 0.5) / 0.5))
        blanco = np.array(e["rayos"], np.float32)
        if self.patron == "rayos":                       # rayos giratorios (sunburst)
            rayos = (np.sin(self.ang * 14 + t * 0.8) > 0.55).astype(np.float32)
            rayos *= np.clip(1.2 - self.rad * 1.6, 0, 1)
            a = e["rayos_alpha"] * 2.2 * (1 + 0.8 * energia)
            img = img * (1 - a * rayos[..., None]) + blanco * a * rayos[..., None]
        elif self.patron == "ondas":                     # ondas suaves que se desplazan
            o = 0.5 + 0.5 * np.sin(self.xn * 7 + self.yn * 11 - t * 1.1)
            o2 = 0.5 + 0.5 * np.sin(self.xn * -5 + self.yn * 6 + t * 0.7)
            m = (o * 0.6 + o2 * 0.4) ** 3 * (0.10 + 0.06 * energia)
            img = img * (1 - m[..., None]) + blanco * m[..., None]
        elif self.patron == "burbujas":                  # círculos grandes desenfocados (bokeh)
            b = self.burb
            asp = self.h / self.w
            acc = np.zeros_like(self.xn)
            for i in range(len(b["x"])):
                bx = (b["x"][i] + b["vx"][i] * t) % 1.0
                by = (b["y"][i] + b["vy"][i] * t) % 1.0
                r = b["r"][i] * (1 + 0.08 * math.sin(t * 1.3 + b["f"][i]))
                d2 = (self.xn - bx) ** 2 + ((self.yn - by) * asp) ** 2
                acc += np.exp(-d2 / (r * r * 0.5))
            m = np.clip(acc, 0, 1.5) * (0.13 + 0.05 * energia)
            img = img * (1 - m[..., None]) + blanco * m[..., None]
        elif self.patron == "puntos":                    # cuadrícula de puntos que respira
            paso = 16
            gx = (self.xn * self.w + t * 6) % paso - paso / 2
            gy = (self.yn * self.h + t * 10) % paso - paso / 2
            rr = 2.2 + 1.4 * energia + 0.6 * np.sin(self.rad * 12 - t * 2)
            dots = np.clip(rr - np.sqrt(gx * gx + gy * gy), 0, 1)
            m = dots * 0.16
            img = img * (1 - m[..., None]) + blanco * m[..., None]
        # anillos que pulsan con la voz (estilo neon)
        if e.get("anillos"):
            r = (self.rad * 9 - t * 1.5) % 1.0
            ring = np.exp(-((r - 0.5) ** 2) / 0.004) * (0.35 + 0.65 * energia)
            ring *= np.clip(1.3 - self.rad * 1.5, 0, 1)
            img += ring[..., None] * np.array(e["glow"], np.float32) * 0.7
        # halo central que respira
        halo = np.exp(-(self.rad ** 2) / 0.05) * (0.25 + 0.35 * energia)
        img += halo[..., None] * 255 * 0.5
        img = cv2.resize(np.clip(img, 0, 255).astype(np.uint8), (self.W, self.H),
                         interpolation=cv2.INTER_LINEAR)
        # partículas / destellos
        p = self.p
        col = e["particulas"]
        for i in range(len(p["x"])):
            y = (p["y"][i] - p["v"][i] * t) % self.H
            x = p["x"][i] + 20 * math.sin(t + p["f"][i])
            br = 0.5 + 0.5 * math.sin(t * 3 + p["f"][i])
            r = int(p["r"][i] * (0.6 + br))
            cv2.circle(img, (int(x), int(y)), r, tuple(int(c * (0.5 + 0.5 * br)) for c in col),
                       -1, cv2.LINE_AA)
        return img


# --------------------------------------------------------------------------
# Color grading
# --------------------------------------------------------------------------
class Grading:
    def __init__(self, W, H, est):
        x = np.arange(256, dtype=np.float32) / 255
        k = est["contraste"]
        s = x + k * (x - 0.5) * (1 - np.abs(2 * x - 1)) * 2          # curva S
        s = np.clip(s, 0, 1)
        w = est["calido"]
        # cálido en altas luces, teal en sombras (look cine)
        r = np.clip(s + w * s, 0, 1)
        b = np.clip(s + w * (1 - s) * 0.8 - w * s * 0.6, 0, 1)
        g = np.clip(s + w * 0.2 * s, 0, 1)
        self.lut = np.dstack([(b * 255), (g * 255), (r * 255)]).astype(np.uint8).reshape(256, 1, 3)
        self.sat = est["sat"]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vig = (1 - est["viñeta"] * np.clip(d - 0.55, 0, 1) ** 1.5)[..., None].astype(np.float32)

    def persona(self, img):
        img = cv2.LUT(img, self.lut)
        f = img.astype(np.float32)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
        f = gray + (f - gray) * self.sat
        return np.clip(f, 0, 255)

    def final(self, f):
        return np.clip(f * self.vig, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------
# IA: segmentación de persona y detección de cara (MediaPipe)
# --------------------------------------------------------------------------
class Vision:
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        self.mp = mp
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpt.BaseOptions(model_asset_path=os.path.join(MODELOS, "selfie_multiclass.tflite")),
            running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True))
        self.face = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=mpt.BaseOptions(model_asset_path=os.path.join(MODELOS, "face_detector.tflite")),
            running_mode=vision.RunningMode.VIDEO, min_detection_confidence=0.4))
        self.prev_mask = None

    def _img(self, bgr):
        return self.mp.Image(image_format=self.mp.ImageFormat.SRGB,
                             data=np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))

    def cara(self, bgr, ts):
        r = self.face.detect_for_video(self._img(bgr), ts)
        if not r.detections:
            return None
        b = max(r.detections, key=lambda d: d.bounding_box.width * d.bounding_box.height).bounding_box
        return (b.origin_x + b.width / 2, b.origin_y + b.height / 2, b.width, b.height)

    def mascara(self, bgr, ts):
        r = self.seg.segment_for_video(self._img(bgr), ts)
        m = 1.0 - r.confidence_masks[0].numpy_view().astype(np.float32)   # 0 = fondo
        if m.ndim == 3:
            m = m[..., 0]
        m = cv2.resize(m, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
        if self.prev_mask is not None and self.prev_mask.shape == m.shape:
            m = 0.6 * m + 0.4 * self.prev_mask              # estabilidad temporal
        self.prev_mask = m
        m = np.clip((m - 0.35) / 0.3, 0, 1)                  # endurecer borde
        m = cv2.GaussianBlur(m, (0, 0), 2)
        return m


# --------------------------------------------------------------------------
# Cámara virtual: sigue la cara y hace zoom de énfasis
# --------------------------------------------------------------------------
class Camara:
    def __init__(self, sw, sh, ow, oh, fps, zoom_base):
        self.sw, self.sh = sw, sh
        ar = ow / oh
        if sw / sh > ar:
            self.bh, self.bw = sh, sh * ar
        else:
            self.bw, self.bh = sw, sw / ar
        self.bw /= zoom_base
        self.bh /= zoom_base
        self.cx, self.cy = sw / 2, sh / 2
        self.zoom = 1.0
        self.pulso = 0.0
        self.fps = fps
        self.cool = 0

    def actualizar(self, cara, energia, energia_prom, t):
        if cara:
            tx, ty = cara[0], cara[1] + cara[3] * 0.35
            a = 0.12
            self.cx += (tx - self.cx) * a
            self.cy += (ty - self.cy) * a
        # disparar pulso de zoom cuando la voz sube mucho
        self.cool -= 1
        if energia > max(0.75, energia_prom * 1.8) and self.cool <= 0:
            self.pulso = 1.0
            self.cool = int(self.fps * 1.2)
        self.pulso *= 0.90
        objetivo = 1.0 + 0.04 * math.sin(t * 0.35) + 0.16 * self.pulso
        self.zoom += (objetivo - self.zoom) * 0.35
        w, h = self.bw / self.zoom, self.bh / self.zoom
        x0 = min(max(self.cx - w / 2, 0), self.sw - w)
        y0 = min(max(self.cy - h / 2, 0), self.sh - h)
        return x0, y0, w, h


def recortar(frame, rect, ow, oh):
    x0, y0, w, h = rect
    M = np.float32([[ow / w, 0, -x0 * ow / w], [0, oh / h, -y0 * oh / h]])
    return cv2.warpAffine(frame, M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# --------------------------------------------------------------------------
# Pipeline principal
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Transforma un video en contenido original estilizado")
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--estilo", default="farandula", choices=list(ESTILOS))
    ap.add_argument("--formato", default="9:16", choices=list(FORMATOS) + ["original"])
    ap.add_argument("--fondo", default="motion", choices=["motion", "blur", "original"],
                    help="motion = gráficos animados detrás; blur = fondo original desenfocado")
    ap.add_argument("--sin-subs", action="store_true")
    ap.add_argument("--subs-json", help="usar subtítulos de un JSON [{t,a,b}] en vez de transcribir")
    ap.add_argument("--idioma", default="es")
    ap.add_argument("--whisper", default="large-v3-turbo")
    ap.add_argument("--sin-glow", action="store_true")
    ap.add_argument("--zoom", type=float, default=1.0, help="zoom base (1.0 = sin zoom extra)")
    ap.add_argument("--inicio", type=float, default=0)
    ap.add_argument("--duracion", type=float, default=0)
    ap.add_argument("--espejo", action="store_true", help="voltear horizontalmente")
    ap.add_argument("--crf", type=int, default=19)
    args = ap.parse_args()

    est = ESTILOS[args.estilo]
    tmp = tempfile.mkdtemp(prefix="studio_")
    src = args.entrada
    if args.inicio or args.duracion:
        src = os.path.join(tmp, "corte.mp4")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(args.inicio), "-i", args.entrada]
        if args.duracion:
            cmd += ["-t", str(args.duracion)]
        subprocess.run(cmd + ["-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-c:a", "aac", src],
                       check=True)

    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if args.formato == "original":
        ow, oh = sw - sw % 2, sh - sh % 2
    else:
        ow, oh = FORMATOS[args.formato]
    log(f"entrada {sw}x{sh} @ {fps:.2f}fps, {n} frames -> salida {ow}x{oh}, estilo {args.estilo}")

    audio = tiene_audio(src)
    energia = np.zeros(n + 1, np.float32)
    grupos = []
    if audio:
        wav = extraer_wav(src, tmp)
        energia = energia_por_frame(wav, fps, n + 1)
        if not args.sin_subs:
            if args.subs_json:
                palabras = json.load(open(args.subs_json))
            else:
                palabras = transcribir(wav, args.idioma, args.whisper)
            grupos = agrupar(palabras)
    energia_suave = cv2.GaussianBlur(energia.reshape(-1, 1), (1, 0), sigmaX=1, sigmaY=fps * 2).ravel()

    vis = Vision()
    fondo = FondoAnimado(ow, oh, est)
    grad = Grading(ow, oh, est)
    cam = Camara(sw, sh, ow, oh, fps, args.zoom)
    subs = Subtitulos(grupos, ow, est["palabra"], int(min(ow, oh) * 0.13)) if grupos else None
    glow_col = np.array(est["glow"], np.float32)

    video_tmp = os.path.join(tmp, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{ow}x{oh}", "-r", f"{fps}", "-i", "-", "-c:v", "libx264",
                            "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p", video_tmp],
                           stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if args.espejo:
            fr = cv2.flip(fr, 1)
        t = i / fps
        ts = int(t * 1000)
        e = float(energia[min(i, len(energia) - 1)])
        cara = vis.cara(fr, ts)
        rect = cam.actualizar(cara, e, float(energia_suave[min(i, len(energia_suave) - 1)]), t)
        fr = recortar(fr, rect, ow, oh)

        persona = grad.persona(fr)
        if args.fondo == "original":
            out = persona
        else:
            m = vis.mascara(fr, ts)[..., None]
            if args.fondo == "motion":
                bg = fondo.frame(t, min(e, 1.0)).astype(np.float32)
            else:
                bg = cv2.GaussianBlur(persona, (0, 0), 18) * 0.7
            if not args.sin_glow:
                halo = np.clip(cv2.GaussianBlur(m, (0, 0), 14)[..., None] * 1.8 - m, 0, 1)
                bg = bg + halo * glow_col * (0.6 + 0.6 * min(e, 1.0))
            out = persona * m + bg * (1 - m)
        out = grad.final(out)
        if subs:
            subs.dibujar(out, t)
        enc.stdin.write(out.tobytes())
        i += 1
        if i % 50 == 0:
            log(f"  frame {i}/{n}")
    cap.release()
    vis.seg.close()
    vis.face.close()
    enc.stdin.close()
    enc.wait()

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video_tmp]
    if audio:
        cmd += ["-i", src, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", "-shortest", args.salida]
    subprocess.run(cmd, check=True)
    log(f"listo -> {args.salida}")


if __name__ == "__main__":
    main()
