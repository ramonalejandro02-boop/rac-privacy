"""Genera segmentos de voz con Kokoro (local, gratuito, Apache-2.0).
Uso: python tts_kokoro.py trabajos.json voz   (voz: em_alex, em_santa, ef_dora)
"""
import json, sys, numpy as np, soundfile as sf, torch
_ol = torch.load
torch.load = lambda *a, **k: _ol(*a, **{**k, "map_location": "cpu"})
from kokoro import KPipeline

jobs, voice = json.load(open(sys.argv[1])), sys.argv[2]
p = KPipeline(lang_code="e")
for i, j in enumerate(jobs):
    a = np.concatenate([au for _, _, au in p(j["text"], voice=j.get("voice", voice), speed=j.get("speed", 1.0))])
    sf.write(j["out"], a, 24000)
    print(f"[{i + 1}/{len(jobs)}] {j['text'][:50]}", flush=True)
