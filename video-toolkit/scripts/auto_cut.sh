#!/usr/bin/env bash
# Corte automático de silencios y pausas (jump cuts) con auto-editor.
# Uso: ./auto_cut.sh entrada.mp4 salida.mp4 [agresividad] [margen]
#   agresividad: suave | normal (defecto) | fuerte      margen: segundos que se conservan alrededor de la voz (defecto 0.15)
# Exportar a editor en vez de renderizar:  EXPORT=premiere|resolve|final-cut-pro|shotcut ./auto_cut.sh in.mp4 proyecto.xml
set -euo pipefail
IN="${1:?entrada}"; OUT="${2:?salida}"; LEVEL="${3:-normal}"; MARGIN="${4:-0.15}"
case "$LEVEL" in suave) TH="3%";; normal) TH="4%";; fuerte) TH="6%";; *) TH="$LEVEL";; esac
AE="${VIDEO_VENV:-$HOME/video-env}/bin/auto-editor"
if [ -n "${EXPORT:-}" ]; then
  "$AE" "$IN" --edit "audio:threshold=$TH" --margin "${MARGIN}sec" --export "$EXPORT" -o "$OUT" --no-open
else
  case "${OUT##*.}" in
    wav|mp3|m4a|flac) "$AE" "$IN" --edit "audio:threshold=$TH" --margin "${MARGIN}sec" -o "$OUT" --no-open ;;
    *)                "$AE" "$IN" --edit "audio:threshold=$TH" --margin "${MARGIN}sec" -c:v libx264 -b:v auto -o "$OUT" --no-open ;;
  esac
fi
echo "OK -> $OUT"
