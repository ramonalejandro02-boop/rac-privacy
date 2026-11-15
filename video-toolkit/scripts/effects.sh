#!/usr/bin/env bash
# Efectos de edición con FFmpeg.
# Uso: ./effects.sh EFECTO entrada.mp4 salida.mp4 [valor]
#  slowmo [factor=2]      Cámara lenta suave con interpolación de movimiento (crea fotogramas nuevos)
#  speed  [factor=2]      Acelerar (timelapse) manteniendo tono de voz
#  stabilize              Estabilizar video movido (2 pasadas, vidstab)
#  upscale [alto=2160]    Escalar a 4K / 1080 con nitidez
#  zoom   [segundo=1]     "Punch-in": zoom rápido de impacto en ese segundo
#  shake  [intensidad=12] Temblor de cámara (impactos, golpes de música)
#  glitch                 Separación RGB + ruido digital
#  rgbsplit [px=8]        Aberración cromática
#  blurbg                 Video vertical con fondo desenfocado (horizontal -> 9:16 sin recortar)
#  reverse                Reproducir al revés
#  boomerang              Ida y vuelta
#  denoise                Quitar ruido de imagen (poca luz)
#  sharpen                Más nitidez
#  fadeinout [seg=0.5]    Fundido a negro al inicio y al final (imagen y sonido)
set -euo pipefail
FX="${1:?efecto}"; IN="${2:?entrada}"; OUT="${3:?salida}"; V="${4:-}"
ENC=(-c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p)
dur(){ ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN"; }
fps(){ ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$IN" | python3 -c "import sys;a,b=sys.stdin.read().strip().split('/');print(round(int(a)/int(b),3))"; }
hasaudio(){ ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$IN" | grep -q .; }
atempo(){ python3 -c "
f=float('$1');out=[]
while f>2: out.append('atempo=2');f/=2
while f<0.5: out.append('atempo=0.5');f/=0.5
out.append(f'atempo={f}');print(','.join(out))"; }
case "$FX" in
  slowmo)  F="${V:-2}"; R=$(fps); ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "minterpolate=fps=$(python3 -c "print($R*$F)"):mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts=$F*PTS,fps=$R" -an "${ENC[@]}" "$OUT" ;;
  speed)   F="${V:-2}"; if hasaudio; then ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -filter_complex "[0:v]setpts=PTS/$F[v];[0:a]$(atempo $F)[a]" -map "[v]" -map "[a]" "${ENC[@]}" "$OUT"; else ffmpeg -y -hide_banner -loglevel error -i "$IN" -vf "setpts=PTS/$F" "${ENC[@]}" "$OUT"; fi ;;
  stabilize) T=$(mktemp --suffix=.trf); ffmpeg -y -hide_banner -loglevel error -i "$IN" -vf "vidstabdetect=shakiness=7:accuracy=15:result=$T" -f null -; ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "vidstabtransform=input=$T:smoothing=30:zoom=2:optzoom=1,unsharp=5:5:0.6" "${ENC[@]}" -c:a copy "$OUT"; rm -f "$T" ;;
  upscale) H="${V:-2160}"; ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "scale=-2:$H:flags=lanczos+accurate_rnd,cas=0.5" "${ENC[@]}" -c:a copy "$OUT" ;;
  zoom)    S="${V:-1}"; ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "scale=iw*2:ih*2,zoompan=z='if(gte(it,$S),min(1.25,1+(it-$S)*3),1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$IN"):fps=$(fps)" "${ENC[@]}" -c:a copy "$OUT" ;;
  shake)   I="${V:-12}"; ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "crop=iw-$((I*2)):ih-$((I*2)):$I+$I*sin(t*47):$I+$I*cos(t*53),scale=iw+$((I*2)):ih+$((I*2))" "${ENC[@]}" -c:a copy "$OUT" ;;
  glitch)  ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "rgbashift=rh=-10:bh=10:rv=3,noise=alls=25:allf=t,eq=contrast=1.2" "${ENC[@]}" -c:a copy "$OUT" ;;
  rgbsplit) P="${V:-8}"; ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "rgbashift=rh=-$P:bh=$P" "${ENC[@]}" -c:a copy "$OUT" ;;
  blurbg)  ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.08[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" "${ENC[@]}" -c:a copy "$OUT" ;;
  reverse) ffmpeg -y -hide_banner -loglevel error -i "$IN" -vf reverse -af areverse "${ENC[@]}" "$OUT" ;;
  boomerang) ffmpeg -y -hide_banner -loglevel error -i "$IN" -filter_complex "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0" -an "${ENC[@]}" "$OUT" ;;
  denoise) ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "hqdn3d=4:3:6:4.5" "${ENC[@]}" -c:a copy "$OUT" ;;
  sharpen) ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -vf "cas=0.7" "${ENC[@]}" -c:a copy "$OUT" ;;
  fadeinout) S="${V:-0.5}"; D=$(dur); E=$(python3 -c "print($D-$S)"); if hasaudio; then A=(-af "afade=t=in:d=$S,afade=t=out:st=$E:d=$S"); else A=(); fi; ffmpeg -y -hide_banner -loglevel error -i "$IN" -vf "fade=t=in:d=$S,fade=t=out:st=$E:d=$S" "${A[@]}" "${ENC[@]}" "$OUT" ;;
  *) sed -n 2,20p "$0"; exit 1 ;;
esac
echo "OK -> $OUT"
