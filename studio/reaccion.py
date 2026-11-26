#!/usr/bin/env python3
"""
Reacciones del creador para el formato "split" (creador arriba, clip abajo).

Un catálogo JSON marca qué partes del video de reacción son cada cosa:
  {"video": "/ruta/reaccion.mp4",
   "escuchar": [[0, 3.5], [7, 11], ...],          # en silencio, atento / sonriendo
   "risa": [[12, 15.3], ...],
   "viste": [[15.5, 17.2]], "no_puede_ser": [...], "que_loco": [...], "esperaba": [...],
   "se_paso": [...], "opinas": [...], "mira": [...], "ay_no": [...], "claro": [...]}

En el plan:  "reacciones": [{"t": 12.6, "tipo": "risa"}, {"t": 20.0, "tipo": "viste"}, ...]
(t en segundos del clip original). Fuera de esos momentos se usa "escuchar", avanzando
en orden para que no se repita el mismo pedazo seguido.
"""
import json
import subprocess

import cv2
import numpy as np


class Reaccion:
    def __init__(self, catalogo, ancho, alto):
        self.cat = json.load(open(catalogo)) if isinstance(catalogo, str) else catalogo
        self.video = self.cat["video"]
        self.ancho, self.alto = ancho, alto
        self.cap = cv2.VideoCapture(self.video)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.pos = -1
        self.cursor = 0.0            # avance dentro de los tramos de "escuchar"
        self.ult_t = None
        self.escuchar = self.cat.get("escuchar") or [[0, 3]]
        self.uso = {}                # rota entre varias versiones del mismo tipo

    def _frame(self, seg):
        idx = int(seg * self.fps)
        if idx != self.pos + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = self.cap.read()
        self.pos = idx
        if not ok:
            return np.zeros((self.alto, self.ancho, 3), np.uint8)
        h, w = fr.shape[:2]
        # recortar a la forma del recuadro (centrado, un poco hacia arriba para la cara)
        ar = self.ancho / self.alto
        if w / h > ar:
            nw = int(h * ar)
            x0 = (w - nw) // 2
            fr = fr[:, x0:x0 + nw]
        else:
            nh = int(w / ar)
            y0 = max(0, int((h - nh) * 0.35))
            fr = fr[y0:y0 + nh]
        return cv2.resize(fr, (self.ancho, self.alto), interpolation=cv2.INTER_AREA)

    def tramo_de(self, ev):
        """Elige qué versión del tipo usar (rota entre las disponibles)."""
        opciones = self.cat.get(ev["tipo"]) or self.cat.get("risa") or self.escuchar
        k = ev.get("version")
        if k is None:
            k = self.uso.get(ev["tipo"], 0)
            self.uso[ev["tipo"]] = k + 1
            ev["version"] = k
        return opciones[k % len(opciones)]

    def cuadro(self, t, eventos):
        for ev in eventos:
            a, b = self.tramo_de(ev)
            d = ev.get("dur", b - a)
            if ev["t"] <= t < ev["t"] + d:
                return self._frame(a + min(t - ev["t"], b - a - 0.04))
        # escuchar: avanzar en orden por los tramos tranquilos
        dt = 0 if self.ult_t is None else max(0.0, min(t - self.ult_t, 0.2))
        self.ult_t = t
        self.cursor += dt
        total = sum(b - a for a, b in self.escuchar)
        c = self.cursor % total
        for a, b in self.escuchar:
            if c < b - a:
                return self._frame(a + c)
            c -= b - a
        return self._frame(self.escuchar[0][0])

    def audio(self, eventos, dur, sr):
        """Pista con la voz/risa real del creador en sus momentos de reacción."""
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", self.video, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                             capture_output=True).stdout
        voz = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        pista = np.zeros(int((dur + 2) * sr), np.float32)
        ventanas = []
        for ev in eventos:
            if ev.get("mudo"):
                continue
            a, b = self.tramo_de(ev)
            d = min(ev.get("dur", b - a), b - a)
            seg = voz[int(a * sr):int((a + d) * sr)].copy()
            n = len(seg)
            if n == 0:
                continue
            fade = min(int(0.04 * sr), n // 2)
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
            i0 = int(ev["t"] * sr)
            i1 = min(len(pista), i0 + n)
            pista[i0:i1] += seg[:i1 - i0] * ev.get("vol", 1.4)
            ventanas.append((ev["t"], ev["t"] + d))
        return np.clip(pista, -1, 1), ventanas
