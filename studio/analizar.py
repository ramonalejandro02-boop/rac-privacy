#!/usr/bin/env python3
"""
Analiza un clip para planear la edición (lo que hay que mirar antes de escribir el plan).

  python analizar.py clip.mp4 carpeta_salida/                 # transcripción + hoja de contactos + info
  python analizar.py clip.mp4 carpeta_salida/ --cuadros 2 9.5 16   # además cuadros con cuadrícula

Genera en la carpeta:
  palabras.json     palabras con tiempos (para --palabras del montaje)
  transcripcion.txt frases con tiempos y lista palabra(tiempo)
  info.json         fps, tamaño, duración, cortes de toma, franja con contenido (bordes negros)
  hoja.png          un cuadro cada 2 s (para ver tomas, quién está, textos pegados)
  cuadros.png       cuadros pedidos con cuadrícula del 10 % (para ubicar personas: x, y de 0 a 1)
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transformar import MODELOS  # noqa: E402


def audio16k(video):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def transcribir(video, out):
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", download_root=os.path.join(MODELOS, "whisper"))
    segs, _ = m.transcribe(audio16k(video), language="es", word_timestamps=True, vad_filter=True)
    palabras, lineas = [], []
    for s in segs:
        lineas.append(f"[{s.start:5.1f}-{s.end:5.1f}] {s.text.strip()}")
        for w in s.words or []:
            if w.word.strip():
                palabras.append(dict(t=w.word.strip(), a=round(w.start, 2), b=round(w.end, 2)))
    json.dump(palabras, open(os.path.join(out, "palabras.json"), "w"), ensure_ascii=False)
    txt = "\n".join(lineas) + "\n\nPALABRAS:\n" + " ".join(f"{w['t']}({w['a']})" for w in palabras)
    open(os.path.join(out, "transcripcion.txt"), "w").write(txt)
    print(txt)


def info(video, out):
    c = cv2.VideoCapture(video)
    fps = c.get(cv2.CAP_PROP_FPS) or 30
    w, h = int(c.get(cv2.CAP_PROP_FRAME_WIDTH)), int(c.get(cv2.CAP_PROP_FRAME_HEIGHT))
    prev, i, saltos, filas = None, 0, [], None
    while True:
        ok, f = c.read()
        if not ok:
            break
        if i == int(fps * 3):
            r = np.where(f.max(2).max(1) > 20)[0]
            filas = (int(r.min()), int(r.max())) if len(r) else (0, h - 1)
        g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (64, 64)).astype(float)
        if prev is not None and np.abs(g - prev).mean() > 25:
            saltos.append(round(i / fps, 2))
        prev, i = g, i + 1
    cortes = [t for k, t in enumerate(saltos) if k == 0 or t - saltos[k - 1] > 0.5]
    d = dict(fps=fps, ancho=w, alto=h, duracion=round(i / fps, 2), cortes_de_toma=cortes,
             contenido_y=[round(filas[0] / h, 3), round(filas[1] / h, 3)] if filas else None)
    json.dump(d, open(os.path.join(out, "info.json"), "w"), indent=1)
    print("INFO:", json.dumps(d))


def hoja(video, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "fps=1/2,scale=180:-1,tile=10x4",
                    "-frames:v", "1", os.path.join(out, "hoja.png")], check=True)


def cuadros(video, out, tiempos):
    imgs = []
    for t in tiempos:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
                              "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        f = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        f = cv2.resize(f, (324, int(f.shape[0] * 324 / f.shape[1])))
        hh, ww = f.shape[:2]
        for k in range(1, 10):
            cv2.line(f, (int(ww * k / 10), 0), (int(ww * k / 10), hh), (0, 230, 255), 1)
            cv2.line(f, (0, int(hh * k / 10)), (ww, int(hh * k / 10)), (0, 230, 255), 1)
        cv2.putText(f, f"{t}", (6, hh - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        imgs.append(f)
    h = min(i.shape[0] for i in imgs)
    cv2.imwrite(os.path.join(out, "cuadros.png"), np.hstack([i[:h] for i in imgs]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("salida")
    ap.add_argument("--cuadros", nargs="*", type=float)
    ap.add_argument("--sin-transcribir", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    if a.cuadros:
        cuadros(a.video, a.salida, a.cuadros)
        print("cuadros ->", os.path.join(a.salida, "cuadros.png"))
        if a.sin_transcribir:
            return
    info(a.video, a.salida)
    hoja(a.video, a.salida)
    if not a.sin_transcribir:
        transcribir(a.video, a.salida)


if __name__ == "__main__":
    main()
