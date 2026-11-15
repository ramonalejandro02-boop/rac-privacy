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

M=https://storage.googleapis.com/mediapipe-models
[ -f "$DIR/models/face_detector.tflite" ] || curl -sSL -o "$DIR/models/face_detector.tflite" $M/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
[ -f "$DIR/models/pose_landmarker.task" ] || curl -sSL -o "$DIR/models/pose_landmarker.task" $M/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
mkdir -p "$DIR/models/rnnoise"
for m in sh bd cb mp lq; do [ -f "$DIR/models/rnnoise/$m.rnnn" ] || curl -sSL -o "$DIR/models/rnnoise/$m.rnnn" https://raw.githubusercontent.com/richardpl/arnndn-models/master/$m.rnnn; done

# Modelos opcionales (si la red lo permite)
"$VENV/bin/python" -c "from rembg import new_session; [new_session(m) for m in ('birefnet-portrait','u2net_human_seg')]" >/dev/null 2>&1 && echo "rembg: modelos listos" || echo "rembg: no se pudo descargar el modelo (usa --engine mediapipe)"
"$VENV/bin/auto-editor" --version >/dev/null 2>&1 || true
"$VENV/bin/python" -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" >/dev/null 2>&1 \
  && echo "whisper: modelo listo" || echo "whisper: no se pudo descargar (falta acceso a huggingface.co)"

(cd "$DIR/remotion" && npm install --no-fund --no-audit --silent)
echo "Listo. Activa el entorno con: source $VENV/bin/activate"
