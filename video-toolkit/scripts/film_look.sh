#!/usr/bin/env bash
# Filtro estilo PELÍCULA con FFmpeg.
# Uso: ./film_look.sh entrada.mp4 salida.mp4 [estilo] [opciones]
# Estilos: teal-orange | kodak | noir | bleach | vintage | matrix | lut=archivo.cube
# Opciones (variables de entorno):
#   GRAIN=0-40 (grano, por defecto 12)   VIGNETTE=1|0   LETTERBOX=1|0 (franjas 2.39:1)
#   FPS24=1 (cadencia de cine)            HALATION=1|0 (brillo suave en luces)   CRF=17
set -euo pipefail
IN="${1:?entrada}"; OUT="${2:?salida}"; STYLE="${3:-teal-orange}"
GRAIN="${GRAIN:-12}"; VIGNETTE="${VIGNETTE:-1}"; LETTERBOX="${LETTERBOX:-1}"; FPS24="${FPS24:-0}"; HALATION="${HALATION:-1}"; CRF="${CRF:-17}"

case "$STYLE" in
  teal-orange) GRADE="curves=r='0/0 0.25/0.22 0.75/0.82 1/1':g='0/0 0.5/0.5 1/0.97':b='0/0.06 0.25/0.30 0.75/0.70 1/0.92',colorbalance=rs=-0.08:bs=0.10:rh=0.10:bh=-0.10,eq=contrast=1.08:saturation=1.12" ;;
  kodak)       GRADE="curves=preset=increase_contrast,colorbalance=rm=0.05:gm=0.01:bm=-0.06:rh=0.06:bh=-0.08,eq=saturation=1.15:gamma=0.97:contrast=1.04" ;;
  noir)        GRADE="hue=s=0,curves=all='0/0 0.15/0.05 0.5/0.5 0.85/0.97 1/1',eq=contrast=1.25" ;;
  bleach)      GRADE="eq=saturation=0.45:contrast=1.3:gamma=0.95,curves=all='0/0.03 0.5/0.48 1/0.98'" ;;
  vintage)     GRADE="curves=preset=vintage,eq=saturation=0.85:contrast=0.95,colorbalance=rs=0.05:bs=-0.05" ;;
  matrix)      GRADE="colorchannelmixer=rr=0.85:gg=1.05:bb=0.8,curves=g='0/0.03 0.5/0.55 1/1',eq=contrast=1.12:saturation=0.8" ;;
  lut=*)       GRADE="lut3d=file='${STYLE#lut=}':interp=tetrahedral" ;;
  *) echo "Estilo desconocido: $STYLE"; exit 1 ;;
esac

VF="format=gbrp,$GRADE"
[ "$HALATION" = "1" ] && VF="$VF,split[a][b];[b]curves=all='0/0 0.7/0 1/1',gblur=sigma=18,colorchannelmixer=rr=1:gg=0.45:bb=0.25[h];[a][h]blend=all_mode=screen:all_opacity=0.35"
[ "$GRAIN" != "0" ] && VF="$VF,noise=c0s=${GRAIN}:c0f=t+u:c1s=$((GRAIN/3)):c2s=$((GRAIN/3))"
[ "$VIGNETTE" = "1" ] && VF="$VF,vignette=angle=PI/5"
[ "$LETTERBOX" = "1" ] && VF="$VF,drawbox=x=0:y=0:w=iw:h=(ih-iw/2.39)/2:color=black:t=fill,drawbox=x=0:y=ih-(ih-iw/2.39)/2:w=iw:h=(ih-iw/2.39)/2:color=black:t=fill"
[ "$FPS24" = "1" ] && VF="$VF,fps=24"
VF="$VF,format=yuv420p"

ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -filter_complex "$VF" \
  -c:v libx264 -preset slow -crf "$CRF" -c:a copy "$OUT"
echo "OK -> $OUT"
