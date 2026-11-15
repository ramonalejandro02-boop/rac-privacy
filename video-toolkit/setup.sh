#!/usr/bin/env bash
# Instala todo el kit de video. Ejecutar una vez por sesión/máquina:  bash video-toolkit/setup.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${VIDEO_VENV:-$HOME/video-env}"

command -v ffmpeg >/dev/null || { echo "Instala ffmpeg (apt install ffmpeg / brew install ffmpeg)"; exit 1; }
# MediaPipe necesita libEGL en Linux
if command -v apt-get >/dev/null && ! ldconfig -p | grep -q libEGL.so.1; then apt-get install -y -q libegl1 libgles2 >/dev/null 2>&1 || sudo apt-get install -y -q libegl1 libgles2 || true; fi

if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$DIR/requirements.txt"

mkdir -p "$DIR/models"
[ -f "$DIR/models/selfie_multiclass.tflite" ] || curl -sSL -o "$DIR/models/selfie_multiclass.tflite" \
  https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite

# Modelos opcionales (si la red lo permite)
"$VENV/bin/python" -c "from rembg import new_session; new_session('u2net_human_seg')" >/dev/null 2>&1 && echo "rembg: modelo listo" || echo "rembg: no se pudo descargar el modelo (usa --engine mediapipe)"
"$VENV/bin/python" -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" >/dev/null 2>&1 \
  && echo "whisper: modelo listo" || echo "whisper: no se pudo descargar (falta acceso a huggingface.co)"

(cd "$DIR/remotion" && npm install --no-fund --no-audit --silent)
echo "Listo. Activa el entorno con: source $VENV/bin/activate"
