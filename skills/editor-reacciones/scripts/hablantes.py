#!/usr/bin/env python3
"""
¿Quién habla? Detecta la persona que habla en cada frase mirando qué boca se mueve.

  python hablantes.py clip.mp4 palabras.json salida.png [--recorte x0,y0,x1,y1]

Para cada frase de la transcripción sigue las caras visibles (MediaPipe Face Landmarker),
mide cuánto se abre y se cierra cada boca mientras suena la frase, y marca la cara que más
se mueve. Si ninguna boca se mueve claramente, informa "nadie visible" (quien habla está de
espaldas o fuera de cuadro). Genera una imagen con un cuadro por frase y la cara marcada.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transformar import MODELOS, agrupar  # noqa: E402


def frases(palabras, pausa=0.6):
    fr, act = [], []
    for w in palabras:
        if act and (w["a"] - act[-1]["b"] > pausa or act[-1]["t"][-1:] in ".?!"):
            fr.append(act)
            act = []
        act.append(w)
    if act:
        fr.append(act)
    return [dict(a=f[0]["a"], b=f[-1]["b"], texto=" ".join(w["t"] for w in f)) for f in fr]


def analizar(video, palabras, recorte=None, por_seg=10):
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=os.path.join(MODELOS, "face_landmarker.task")),
        running_mode=vision.RunningMode.IMAGE, num_faces=4, min_face_detection_confidence=0.4))
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    paso = max(1, int(round(fps / por_seg)))
    obs = []          # (t, cx, cy, w, apertura, x0, y0, x1, y1) en coords relativas al cuadro
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % paso == 0:
            h, w = fr.shape[:2]
            rx0, ry0, rx1, ry1 = recorte or (0, 0, 1, 1)
            # "lupa": zonas solapadas agrandadas, para encontrar caras pequeñas
            zonas = []
            nx, ny = (2, 3) if h > w else (3, 2)
            for a in range(nx):
                for b in range(ny):
                    zx0 = rx0 + (rx1 - rx0) * max(0, a / nx - 0.1)
                    zx1 = rx0 + (rx1 - rx0) * min(1, (a + 1) / nx + 0.1)
                    zy0 = ry0 + (ry1 - ry0) * max(0, b / ny - 0.1)
                    zy1 = ry0 + (ry1 - ry0) * min(1, (b + 1) / ny + 0.1)
                    zonas.append((zx0, zy0, zx1, zy1))
            vistos = []
            for zx0, zy0, zx1, zy1 in zonas:
                sub = fr[int(zy0 * h):int(zy1 * h), int(zx0 * w):int(zx1 * w)]
                if sub.size == 0:
                    continue
                esc = 900 / max(sub.shape[:2])
                sub = cv2.resize(sub, None, fx=esc, fy=esc, interpolation=cv2.INTER_CUBIC)
                r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB,
                                       data=np.ascontiguousarray(cv2.cvtColor(sub, cv2.COLOR_BGR2RGB))))
                for p in r.face_landmarks or []:
                    xs = [q.x for q in p]
                    ys = [q.y for q in p]
                    x0, x1 = zx0 + min(xs) * (zx1 - zx0), zx0 + max(xs) * (zx1 - zx0)
                    y0, y1 = zy0 + min(ys) * (zy1 - zy0), zy0 + max(ys) * (zy1 - zy0)
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if any(abs(cx - v[0]) < 0.03 and abs(cy - v[1]) < 0.03 for v in vistos):
                        continue          # la misma cara encontrada en dos zonas
                    vistos.append((cx, cy))
                    cara = abs(p[152].y - p[10].y) + 1e-6
                    ab = abs(p[14].y - p[13].y) / cara
                    obs.append((i / fps, cx, cy, x1 - x0, ab, x0, y0, x1, y1))
        i += 1
    cap.release()
    lm.close()
    # agrupar observaciones en "pistas" por cercanía (la misma cara de un cuadro al siguiente)
    pistas = []
    for o in sorted(obs):
        mejor, dmin = None, 0.08
        for p in pistas:
            u = p[-1]
            if o[0] - u[0] < 0.6:
                d = np.hypot(o[1] - u[1], o[2] - u[2])
                if d < dmin:
                    mejor, dmin = p, d
        (mejor.append(o) if mejor is not None else pistas.append([o]))
    res = []
    for f in frases(palabras):
        candidatos = []
        for k, p in enumerate(pistas):
            seg = [o for o in p if f["a"] <= o[0] <= f["b"]]
            if len(seg) < 3:
                continue
            ab = np.array([o[4] for o in seg])
            mov = float(np.std(ab) + np.mean(np.abs(np.diff(ab))))
            m = seg[len(seg) // 2]
            candidatos.append(dict(pista=k, movimiento=round(mov, 4), caja=[round(v, 3) for v in m[5:9]],
                                   centro=[round(m[1], 3), round(m[2], 3)]))
        candidatos.sort(key=lambda c: -c["movimiento"])
        habla = candidatos[0] if candidatos and candidatos[0]["movimiento"] > 0.012 else None
        if habla and len(candidatos) > 1 and candidatos[1]["movimiento"] > habla["movimiento"] * 0.8:
            habla = dict(habla, dudoso=True)
        res.append(dict(f, habla=habla, caras_visibles=len(candidatos)))
    return res


def dibujar(video, res, salida):
    imgs = []
    for r in res:
        t = (r["a"] + r["b"]) / 2
        cap = cv2.VideoCapture(video)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        cap.release()
        if not ok:
            continue
        h, w = fr.shape[:2]
        if r["habla"]:
            x0, y0, x1, y1 = r["habla"]["caja"]
            col = (0, 200, 255) if r["habla"].get("dudoso") else (0, 255, 0)
            cv2.rectangle(fr, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), col, max(4, w // 150))
        esc = 300 / w
        fr = cv2.resize(fr, (300, int(h * esc)))
        etiqueta = f"{r['a']:.1f}s " + ("HABLA" if r["habla"] else "nadie visible")
        cv2.putText(fr, etiqueta, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        imgs.append(fr)
    if imgs:
        hmin = min(i.shape[0] for i in imgs)
        cv2.imwrite(salida, np.hstack([i[:hmin] for i in imgs]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("palabras")
    ap.add_argument("salida")
    ap.add_argument("--recorte")
    a = ap.parse_args()
    rec = [float(v) for v in a.recorte.split(",")] if a.recorte else None
    res = analizar(a.video, json.load(open(a.palabras)), rec)
    for r in res:
        h = r["habla"]
        quien = (f"cara en x={h['centro'][0]}, y={h['centro'][1]} (mov {h['movimiento']}{', DUDOSO' if h.get('dudoso') else ''})"
                 if h else "nadie visible (de espaldas o fuera de cuadro)")
        print(f"[{r['a']:5.1f}-{r['b']:5.1f}] {r['texto']}\n         -> {quien}; caras visibles: {r['caras_visibles']}")
    dibujar(a.video, res, a.salida)
    print("imagen ->", a.salida)


if __name__ == "__main__":
    main()
