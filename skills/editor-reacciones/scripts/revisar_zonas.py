#!/usr/bin/env python3
"""
Simula la interfaz de Facebook Reels sobre cuadros del video para revisar zonas seguras.

  python3 studio/revisar_zonas.py video.mp4 salida.png 1.0 9.0 20.0 ...

Pinta en rojo semitransparente lo que tapa Facebook: barra de arriba, columna de
íconos de la derecha y el bloque de nombre/descripción de abajo.
"""
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__file__))
from efectos import ZONA  # noqa: E402


def marcar(fr):
    h, w = fr.shape[:2]
    capa = fr.copy()
    rojo = (40, 40, 230)
    cv2.rectangle(capa, (0, 0), (w, int(ZONA["arriba"] * h)), rojo, -1)
    cv2.rectangle(capa, (int(ZONA["derecha"] * w), int(ZONA["iconos_desde"] * h)),
                  (w, int(ZONA["abajo"] * h)), rojo, -1)
    cv2.rectangle(capa, (0, int(ZONA["abajo"] * h)), (w, h), rojo, -1)
    lx = int(ZONA.get("lados", 0) * w)                  # orillas que Facebook recorta
    cv2.rectangle(capa, (0, 0), (lx, h), rojo, -1)
    cv2.rectangle(capa, (w - lx, 0), (w, h), rojo, -1)
    return cv2.addWeighted(capa, 0.45, fr, 0.55, 0)


def main():
    video, salida, tiempos = sys.argv[1], sys.argv[2], [float(t) for t in sys.argv[3:]] or [1.0]
    cuadros = []
    for t in tiempos:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
                              "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        fr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        fr = cv2.resize(marcar(fr), (270, 480))
        cv2.putText(fr, f"{t:.1f}s", (6, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cuadros.append(fr)
    cv2.imwrite(salida, np.hstack(cuadros))
    print("listo ->", salida)


if __name__ == "__main__":
    main()
