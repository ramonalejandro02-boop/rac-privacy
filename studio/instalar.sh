#!/usr/bin/env bash
# Instala todo lo necesario para studio/transformar.py
set -e
MODELS=${STUDIO_MODELS:-/home/user/models}
command -v ffmpeg >/dev/null || (apt-get update -q && apt-get install -y -q ffmpeg)
apt-get install -y -q libegl1 libgles2 libgl1 >/dev/null 2>&1 || (apt-get update -q && apt-get install -y -q libegl1 libgles2 libgl1)
pip3 install -q opencv-python-headless numpy pillow moviepy faster-whisper mediapipe
mkdir -p "$MODELS"
[ -f "$MODELS/selfie_multiclass.tflite" ] || curl -sSL -o "$MODELS/selfie_multiclass.tflite" \
  https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
[ -f "$MODELS/face_detector.tflite" ] || curl -sSL -o "$MODELS/face_detector.tflite" \
  https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='$MODELS/whisper')"
echo "Listo: estudio instalado."
