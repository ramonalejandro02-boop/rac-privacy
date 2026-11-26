#!/usr/bin/env python3
"""Copia el motor de studio/ dentro de la skill y arma el .zip para instalarla.
   python3 skills/empaquetar.py [carpeta_zip]"""
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(RAIZ, "skills", "editor-reacciones")
DEST = os.path.join(SKILL, "scripts")
ARCHIVOS = ["transformar.py", "efectos.py", "montaje.py", "presentador.py", "clonar_voz.py",
            "instalar.py", "analizar.py", "verificar.py", "revisar_zonas.py", "hablantes.py", "reaccion.py"]

shutil.rmtree(DEST, ignore_errors=True)
os.makedirs(os.path.join(DEST, "planes"))
for f in ARCHIVOS:
    shutil.copy(os.path.join(RAIZ, "studio", f), DEST)
shutil.copytree(os.path.join(RAIZ, "studio", "fonts"), os.path.join(DEST, "fonts"))
open(os.path.join(DEST, "fonts", "LICENCIAS.txt"), "w").write(
    "Anton, Inter Display y Noto Color Emoji: SIL Open Font License 1.1 (uso comercial permitido).\n")
shutil.copy(os.path.join(RAIZ, "studio", "planes", "lafruta_libro.json"), os.path.join(DEST, "planes", "ejemplo.json"))
salida = sys.argv[1] if len(sys.argv) > 1 else RAIZ
zipf = shutil.make_archive(os.path.join(salida, "editor-reacciones"), "zip", os.path.join(RAIZ, "skills"), "editor-reacciones")
print("skill lista ->", zipf)
