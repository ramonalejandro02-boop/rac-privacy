#!/usr/bin/env bash
# Detecta cortes de escena y separa el video en clips (+ miniaturas y lista CSV).
# Uso: ./scenes.sh entrada.mp4 [carpeta_salida] [umbral]   (umbral 27 por defecto; menor = más cortes)
set -euo pipefail
IN="${1:?entrada}"; OUTDIR="${2:-escenas}"; TH="${3:-27}"
mkdir -p "$OUTDIR"
"${VIDEO_VENV:-$HOME/video-env}/bin/scenedetect" -i "$IN" -o "$OUTDIR" -q detect-adaptive -t 3 list-scenes -q save-images -n 1 split-video
echo "OK -> $OUTDIR"
