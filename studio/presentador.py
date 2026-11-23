#!/usr/bin/env python3
"""
Presentador: pone al creador en pantalla (presencia en pantalla = contenido original para Meta).

- Recorta a la persona de su video (fondo negro o cualquier fondo, usando IA).
- Detecta cuándo mueve la boca (MediaPipe Face Landmarker) y separa los cuadros en
  "hablando" y "escuchando". Cuando suena la voz en off usa los de hablando; cuando
  hablan otros, los de escuchando.
- Lo superpone sobre el montaje final como sticker (borde blanco + sombra), en una
  esquina o en grande (intro).
"""
import math
import os
import subprocess

import cv2
import numpy as np

from transformar import MODELOS, log


def _mascara(fr, seg=None):
    m = (fr.max(2) > 14).astype(np.uint8)                     # fondo negro puro
    if m.mean() > 0.6 and seg is not None:                    # fondo real: usar IA
        m = seg(fr)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        m = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    # rellenar huecos
    inv = (1 - m).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
    h, w = m.shape
    for k in range(1, n):
        x, y, ww, hh, a = st[k]
        if x > 0 and y > 0 and x + ww < w and y + hh < h:
            m[lab == k] = 1
    return m


class Presentador:
    def __init__(self, video, espejo=False, alto=560):
        self.video, self.espejo, self.alto = video, espejo, alto
        cap = cv2.VideoCapture(video)
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 24
        self.n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        self._analizar()
        self.cap = cv2.VideoCapture(video)
        self.pos = -1
        self.cache = {}

    def _analizar(self):
        """Apertura de boca por cuadro + caja de la persona."""
        import mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=mpt.BaseOptions(model_asset_path=os.path.join(MODELOS, "face_landmarker.task")),
            running_mode=vision.RunningMode.VIDEO, num_faces=1))
        cap = cv2.VideoCapture(self.video)
        ab, cajas = [], []
        i = 0
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if i % 2 == 0:
                m = _mascara(fr)
                ys, xs = np.where(m > 0)
                cajas.append((xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else (0, 0, 1, 1))
            else:
                cajas.append(cajas[-1])
            r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                             data=np.ascontiguousarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))),
                                    int(i * 1000 / self.fps))
            if r.face_landmarks:
                p = r.face_landmarks[0]
                cara = abs(p[152].y - p[10].y) + 1e-6
                ab.append(abs(p[14].y - p[13].y) / cara)
            else:
                ab.append(0.0)
            i += 1
        cap.release()
        lm.close()
        self.n = len(ab)
        a = np.array(ab)
        # "habla" = boca abriéndose y cerrándose (variación local), no solo abierta
        var = np.convolve(np.abs(np.diff(a, prepend=a[0])), np.ones(9) / 9, "same")
        hab = (var > np.percentile(var, 55)) | (a > np.percentile(a, 70))
        hab = np.convolve(hab.astype(float), np.ones(11) / 11, "same") > 0.5
        c = np.array(cajas[:len(ab)])
        top = np.median(c[:, 1])
        # descartar cuadros con objetos encima de la cabeza (manos, restos del recorte)
        bueno = c[:, 1] > top - 25
        bueno = np.convolve(bueno.astype(float), np.ones(7) / 7, "same") > 0.99
        self.hablando = np.where(hab & bueno)[0]
        self.callado = np.where(~hab & bueno)[0]
        if len(self.callado) < self.fps:
            self.callado = np.argsort(a)[: max(int(self.fps * 3), 1)]
            self.callado.sort()
        if len(self.hablando) < self.fps:
            self.hablando = np.arange(self.n)
        cb = c[bueno] if bueno.any() else c
        pad = 24
        x0, y0 = max(0, int(np.percentile(cb[:, 0], 2)) - pad), max(0, int(np.percentile(cb[:, 1], 2)) - pad)
        x1, y1 = int(np.percentile(cb[:, 2], 98)) + pad, int(cb[:, 3].max()) + 1
        self.caja = (int(x0), int(y0), int(x1), int(y1))
        log(f"presentador: {self.n} cuadros, {len(self.hablando)} hablando / {len(self.callado)} callado")

    def _leer(self, idx):
        if idx in self.cache:
            return self.cache[idx]
        if idx != self.pos + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = self.cap.read()
        self.pos = idx
        if not ok:
            return None
        x0, y0, x1, y1 = self.caja
        fr = fr[y0:y1, x0:x1]
        if self.espejo:
            fr = cv2.flip(fr, 1)
        m = _mascara(fr).astype(np.float32)
        esc = self.alto / fr.shape[0]
        fr = cv2.resize(fr, None, fx=esc, fy=esc, interpolation=cv2.INTER_CUBIC)
        m = cv2.resize(m, (fr.shape[1], fr.shape[0]))
        m = cv2.GaussianBlur(m, (0, 0), 1.2)
        # sticker: borde blanco + sombra
        pad = 26
        H, W = fr.shape[0] + pad * 2, fr.shape[1] + pad * 2
        a = np.zeros((H, W), np.float32)
        a[pad:pad + fr.shape[0], pad:pad + fr.shape[1]] = m
        rgb = np.full((H, W, 3), 255, np.float32)
        rgb[pad:pad + fr.shape[0], pad:pad + fr.shape[1]] = fr * m[..., None] + 255 * (1 - m[..., None])
        borde = cv2.dilate((a > 0.4).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
        borde = cv2.GaussianBlur(borde.astype(np.float32), (0, 0), 1.2)
        borde[-pad:, :] = 0                                     # base plana abajo (sale del borde)
        sombra = np.roll(cv2.GaussianBlur(borde, (0, 0), 9), 10, 1) * 0.5
        rgb = np.where((borde > 0.01)[..., None], rgb, 0)
        out = np.dstack([rgb, np.maximum(borde, sombra) * 255]).clip(0, 255).astype(np.uint8)
        self.cache = {idx: out}
        return out

    def cuadro(self, t, hablando):
        pool = self.hablando if hablando else self.callado
        # avanzar por el pool en orden (se ve continuo), en bucle
        k = int(t * self.fps) % len(pool)
        return self._leer(int(pool[k]))


def aplicar(video_in, video_out, pres, tramos, fps=30):
    """
    tramos: lista de dict(a, b, modo='esquina'|'grande'|'oculto', habla=bool)
    """
    from efectos import H, W, ease_back, superponer
    cap = cv2.VideoCapture(video_in)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", video_out], stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        t = i / fps
        tr = next((x for x in tramos if x["a"] <= t < x["b"]), None)
        if tr and tr["modo"] != "oculto":
            img = pres.cuadro(t, tr.get("habla", False))
            if img is not None:
                u = t - tr["a"]
                entra = ease_back(u / 0.3) if tr.get("anima", True) else 1.0
                if tr["modo"] == "grande":
                    sc = 1.0 * entra
                    cx, by = W * 0.5, H * 0.80
                else:
                    sc = 0.5 * entra
                    cx, by = W * 0.2, H * 0.80
                h, w = img.shape[:2]
                cy = by - h * sc / 2 + 4 + 6 * math.sin(t * 2.5)
                superponer(fr, img, cx, cy, sc, 1.5 * math.sin(t * 1.7))
        enc.stdin.write(fr.tobytes())
        i += 1
    cap.release()
    enc.stdin.close()
    enc.wait()
