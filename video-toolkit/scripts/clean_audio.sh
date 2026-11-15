#!/usr/bin/env bash
# Mejora de sonido para voz: quita ruido, zumbido, clics, ecualiza, comprime y normaliza.
# Uso: ./clean_audio.sh entrada.(mp4|wav|mp3) salida.(mp4|wav|mp3) [preset]
# Presets: voz (por defecto) | podcast | ligero | musica
# Variables: TARGET=-14 (LUFS: -14 redes, -16 podcast, -23 TV)  DENOISE=12 (dB de reducción)
set -euo pipefail
IN="${1:?entrada}"; OUT="${2:?salida}"; PRESET="${3:-voz}"
TARGET="${TARGET:-}"; DENOISE="${DENOISE:-12}"

case "$PRESET" in
  voz)     TARGET="${TARGET:--14}"; CHAIN="highpass=f=80,lowpass=f=16000,bandreject=f=50:width_type=h:w=4,bandreject=f=60:width_type=h:w=4,adeclick,afftdn=nr=${DENOISE}:nf=-30:tn=1,equalizer=f=200:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.5:g=3,equalizer=f=10000:t=h:g=2,deesser=i=0.4,acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=3,alimiter=limit=0.95" ;;
  podcast) TARGET="${TARGET:--16}"; CHAIN="highpass=f=90,adeclick,afftdn=nr=$((DENOISE+4)):nf=-28:tn=1,anlmdn=s=4,equalizer=f=150:t=q:w=1:g=2,equalizer=f=400:t=q:w=1.5:g=-3,equalizer=f=4000:t=q:w=1.2:g=3,deesser=i=0.5,acompressor=threshold=-22dB:ratio=4:attack=5:release=120:makeup=4,alimiter=limit=0.95" ;;
  ligero)  TARGET="${TARGET:--14}"; CHAIN="highpass=f=70,afftdn=nr=6:nf=-35,acompressor=threshold=-18dB:ratio=2:makeup=2" ;;
  musica)  TARGET="${TARGET:--14}"; CHAIN="highpass=f=25,acompressor=threshold=-14dB:ratio=1.8:attack=20:release=250,alimiter=limit=0.97" ;;
  *) echo "Preset desconocido: $PRESET"; exit 1 ;;
esac

# Normalización a 2 pasadas (más precisa)
STATS=$(ffmpeg -hide_banner -i "$IN" -af "$CHAIN,loudnorm=I=${TARGET}:TP=-1.0:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
get(){ echo "$STATS" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
LN="loudnorm=I=${TARGET}:TP=-1.0:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true"

case "${OUT##*.}" in
  mp4|mov|mkv) ffmpeg -y -hide_banner -loglevel error -i "$IN" -af "$CHAIN,$LN" -c:v copy -c:a aac -b:a 256k -ar 48000 "$OUT" ;;
  *)           ffmpeg -y -hide_banner -loglevel error -i "$IN" -vn -af "$CHAIN,$LN" -ar 48000 "$OUT" ;;
esac
echo "OK -> $OUT  (objetivo ${TARGET} LUFS)"
