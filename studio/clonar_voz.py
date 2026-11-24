#!/usr/bin/env python3
"""
Genera voz en off con TU voz clonada (Chatterbox Multilingual, licencia MIT, corre local).
Se ejecuta con el entorno aparte de voz (venv-voz), ver instalar.py.

  clonar_voz.py --ref mi_voz.wav --textos textos.json --salida carpeta/
  textos.json = ["frase 1", "frase 2", ...]  -> carpeta/vo_000.wav, vo_001.wav, ...

Consejo para la referencia: 15-30 s de tu voz hablando natural, sin música ni eco,
con la misma energía y acento que querés en los videos.
Chatterbox agrega una marca de agua inaudible que identifica el audio como generado por IA.
"""
import argparse
import json
import os

os.environ.setdefault("HF_HOME", os.path.join(os.environ.get("STUDIO_MODELS") or (
    "/home/user/models" if os.path.isdir("/home/user/models")
    else os.path.join(os.path.expanduser("~"), ".estudio", "models")), "hf"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--textos", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--expresividad", type=float, default=0.6, help="0.3 calmado ... 1.0 exagerado")
    ap.add_argument("--cfg", type=float, default=0.4, help="más bajo = más lento y pausado")
    args = ap.parse_args()
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    os.makedirs(args.salida, exist_ok=True)
    for i, t in enumerate(json.load(open(args.textos))):
        w = m.generate(t, language_id="es", audio_prompt_path=args.ref,
                       exaggeration=args.expresividad, cfg_weight=args.cfg)
        ta.save(os.path.join(args.salida, f"vo_{i:03d}.wav"), w, m.sr)
        print(f"vo_{i:03d}: {t}", flush=True)


if __name__ == "__main__":
    main()
