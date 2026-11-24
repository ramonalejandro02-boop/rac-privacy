#!/usr/bin/env python3
"""
Instalador del estudio de reacciones (Mac, Windows o Linux).

  python3 instalar.py                 # instala todo en ~/.estudio
  python3 instalar.py --config --voz ~/mi_voz.m4a --presentador ~/yo.mov --espejo

Crea:
  ~/.estudio/venv        entorno principal (video, IA de recorte, subtítulos)
  ~/.estudio/venv-voz    entorno de clonación de voz (Chatterbox, licencia MIT)
  ~/.estudio/models      modelos (MediaPipe, Whisper)
  ~/.estudio/config.json tu voz, tu video de presentador y la carpeta de salida
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request

BASE = os.path.join(os.path.expanduser("~"), ".estudio")
MODELOS = os.path.join(BASE, "models")
CONFIG = os.path.join(BASE, "config.json")
WIN = platform.system() == "Windows"

MP = "https://storage.googleapis.com/mediapipe-models/"
DESCARGAS = {
    "selfie_multiclass.tflite": MP + "image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
    "face_detector.tflite": MP + "face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "face_landmarker.task": MP + "face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
}
PAQUETES = ["opencv-python-headless", "numpy", "pillow", "faster-whisper", "mediapipe", "kokoro-onnx", "soundfile"]
PAQUETES_VOZ = ["chatterbox-tts", "setuptools<81"]


def py(venv):
    return os.path.join(venv, "Scripts", "python.exe") if WIN else os.path.join(venv, "bin", "python")


def paso(msg):
    print(f"\n==> {msg}", flush=True)


def venv(ruta, paquetes):
    if not os.path.exists(py(ruta)):
        subprocess.run([sys.executable, "-m", "venv", ruta], check=True)
    subprocess.run([py(ruta), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run([py(ruta), "-m", "pip", "install", "-q"] + paquetes, check=True)


def ffmpeg():
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    sistema = platform.system()
    if sistema == "Darwin" and shutil.which("brew"):
        subprocess.run(["brew", "install", "ffmpeg"], check=False)
    elif WIN and shutil.which("winget"):
        subprocess.run(["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements",
                        "--accept-package-agreements"], check=False)
    elif shutil.which("apt-get"):
        subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False)
    ok = bool(shutil.which("ffmpeg"))
    if not ok:
        print("FALTA ffmpeg. Mac: 'brew install ffmpeg'. Windows: 'winget install Gyan.FFmpeg' "
              "(y abrir una terminal nueva). Linux: 'sudo apt install ffmpeg'.")
    return ok


def instalar():
    os.makedirs(MODELOS, exist_ok=True)
    paso("Revisando ffmpeg")
    ffmpeg()
    paso("Entorno principal (puede tardar unos minutos)")
    venv(os.path.join(BASE, "venv"), PAQUETES)
    paso("Entorno de clonación de voz (descarga grande, ~2 GB)")
    venv(os.path.join(BASE, "venv-voz"), PAQUETES_VOZ)
    paso("Modelos de MediaPipe")
    for nombre, url in DESCARGAS.items():
        destino = os.path.join(MODELOS, nombre)
        if not os.path.exists(destino):
            urllib.request.urlretrieve(url, destino)
            print("  ok", nombre)
    paso("Modelo de transcripción (Whisper large-v3-turbo)")
    subprocess.run([py(os.path.join(BASE, "venv")), "-c",
                    "from faster_whisper import WhisperModel; "
                    f"WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', download_root={os.path.join(MODELOS, 'whisper')!r})"],
                   check=True)
    paso("Modelo de clonación de voz")
    env = dict(os.environ, HF_HOME=os.path.join(MODELOS, "hf"))
    subprocess.run([py(os.path.join(BASE, "venv-voz")), "-c",
                    "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; ChatterboxMultilingualTTS.from_pretrained(device='cpu')"],
                   check=True, env=env)
    if not os.path.exists(CONFIG):
        guardar_config({})
    print("\nListo. Python del estudio:", py(os.path.join(BASE, "venv")))
    print("Configurá tu voz y tu presentador con:  instalar.py --config --voz RUTA --presentador RUTA [--espejo]")


def guardar_config(cambios):
    cfg = json.load(open(CONFIG)) if os.path.exists(CONFIG) else {}
    cfg.setdefault("salida", os.path.join(os.path.expanduser("~"), "Desktop", "videos_editados"))
    cfg.setdefault("espejo", False)
    cfg.update({k: v for k, v in cambios.items() if v is not None})
    os.makedirs(BASE, exist_ok=True)
    json.dump(cfg, open(CONFIG, "w"), ensure_ascii=False, indent=1)
    print("config:", json.dumps(cfg, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", action="store_true", help="solo guardar configuración")
    ap.add_argument("--voz", help="audio con tu voz (15-30 s, sin música)")
    ap.add_argument("--presentador", help="video tuyo para salir en pantalla")
    ap.add_argument("--espejo", action="store_true", help="el video del presentador viene en espejo")
    ap.add_argument("--salida", help="carpeta donde guardar los videos editados")
    a = ap.parse_args()
    if a.config:
        guardar_config(dict(voz=a.voz and os.path.abspath(a.voz),
                            presentador=a.presentador and os.path.abspath(a.presentador),
                            espejo=True if a.espejo else None, salida=a.salida))
    else:
        instalar()


if __name__ == "__main__":
    main()
