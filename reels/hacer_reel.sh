#!/bin/bash
# Arma un reel completo con ilustraciones IA animadas + voz clonada.
# Uso: bash reels/hacer_reel.sh <historia> <carpeta_render_3d>
#  Requiere: reels/<historia>/ai/escena*.png, reels/<historia>/clon/vo/*.wav, <render>/<historia>/cfg.json
set -e
H=$1; R=$2; cd "$(dirname "$0")"
python3 unir_voz.py "$H"
D=$(python3 -c "import json;print(','.join(str(round(b-a+0.4,2)) for a,b,_,_ in json.load(open('$H/voz_segs.json'))))")
mkdir -p "$R/$H" && cp "$H"/ai/escena*.png "$R/$H/"
(cd "$R" && PAGE="animar_ai.html?c=$H/cfg.json&d=$D" DUR="$D" node render.js video "$OLDPWD/$H" | grep -E "lista|ERR")
ESTILO=ilustrado python3 armar_reel.py "$H" | tail -1
