#!/usr/bin/env bash
# Instala todo lo necesario para studio/transformar.py
set -e
MODELS=${STUDIO_MODELS:-/home/user/models}
command -v ffmpeg >/dev/null || (apt-get update -q && apt-get install -y -q ffmpeg)
apt-get install -y -q libegl1 libgles2 libgl1 >/dev/null 2>&1 || (apt-get update -q && apt-get install -y -q libegl1 libgles2 libgl1)
pip3 install -q opencv-python-headless numpy pillow moviepy faster-whisper mediapipe piper-tts kokoro-onnx soundfile
mkdir -p "$MODELS"
[ -f "$MODELS/selfie_multiclass.tflite" ] || curl -sSL -o "$MODELS/selfie_multiclass.tflite" \
  https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
[ -f "$MODELS/face_detector.tflite" ] || curl -sSL -o "$MODELS/face_detector.tflite" \
  https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='$MODELS/whisper')"
mkdir -p "$MODELS/piper"
for f in onnx onnx.json; do
  [ -f "$MODELS/piper/es_MX-claude-high.$f" ] || curl -sSL -o "$MODELS/piper/es_MX-claude-high.$f" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.$f"
done
python3 -c "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', download_root='$MODELS/whisper')"
mkdir -p "$MODELS/kokoro" && cd "$MODELS/kokoro"
HF=https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main
[ -f kokoro-v1.0.onnx ] || curl -sSL -o kokoro-v1.0.onnx $HF/onnx/model.onnx
for v in ef_dora em_alex; do [ -f $v.bin ] || curl -sSL -o $v.bin $HF/voices/$v.bin; done
python3 -c "
import numpy as np
np.savez('voices.npz', **{v: np.fromfile(v + '.bin', dtype=np.float32).reshape(-1, 1, 256) for v in ['ef_dora', 'em_alex']})"
mv voices.npz voices-es.bin
cd - >/dev/null
echo "Listo: estudio instalado."
