#!/usr/bin/env python3
"""
Verificaciones antes de entregar un video.

  python verificar.py audio  final.mp4 [carpeta_partes/]   # ¿se oyen todas las palabras? (por partes si se da)
  python verificar.py recortes clip.mp4 salida.png 12.4:0.5,0.35,0.92,0.62 29.6:...
        # vista previa de las personas recortadas para las escenas (congelar:caja)
"""
import glob
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transformar import MODELOS  # noqa: E402


def audio(archivos):
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", download_root=os.path.join(MODELOS, "whisper"))
    for f in archivos:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                             capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        segs, _ = m.transcribe(a, language="es", vad_filter=True)
        print(f"{os.path.basename(f)} ({len(a) / 16000:.1f}s): " + " ".join(s.text.strip() for s in segs), flush=True)


def recortes(clip, salida, specs):
    from montaje import recorte_sticker
    ims = []
    for sp in specs:
        t, caja = sp.split(":")
        x = recorte_sticker(clip, float(t), [float(v) for v in caja.split(",")], 500, 500)
        bg = np.full((x.shape[0], x.shape[1], 3), (150, 60, 200), np.uint8)
        al = x[..., 3:4] / 255.0
        im = (bg * (1 - al) + x[..., :3] * al).astype(np.uint8)
        im = cv2.resize(im, (300, int(im.shape[0] * 300 / im.shape[1])))
        cv2.putText(im, t, (5, 30), 0, 1, (0, 255, 255), 2)
        ims.append(im)
    h = min(i.shape[0] for i in ims)
    cv2.imwrite(salida, np.hstack([i[:h] for i in ims]))
    print("listo ->", salida)


if __name__ == "__main__":
    if sys.argv[1] == "audio":
        archivos = [sys.argv[2]]
        if len(sys.argv) > 3:
            archivos += sorted(glob.glob(os.path.join(sys.argv[3], "parte*.mp4")))
        audio(archivos)
    elif sys.argv[1] == "recortes":
        recortes(sys.argv[2], sys.argv[3], sys.argv[4:])
