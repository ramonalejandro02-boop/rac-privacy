"""Genera los segmentos de voz con Chatterbox Multilingual (local, licencia MIT).
Uso: python tts_chatterbox.py trabajos.json voz_referencia.wav
trabajos.json = [{"text": "...", "out": "seg00.wav", "exaggeration": 0.55}, ...]
"""
import json, sys, torch, torchaudio as ta
_ol = torch.load
torch.load = lambda *a, **k: _ol(*a, **{**k, "map_location": "cpu"})
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

torch.set_num_threads(4)
jobs, ref = json.load(open(sys.argv[1])), sys.argv[2]
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
for i, j in enumerate(jobs):
    torch.manual_seed(j.get("seed", 1234))
    kw = {} if ref == "default" else {"audio_prompt_path": j.get("ref", ref)}
    w = m.generate(j["text"], language_id="es", **kw,
                   exaggeration=j.get("exaggeration", 0.55), cfg_weight=j.get("cfg", 0.5),
                   temperature=j.get("temperature", 0.75))
    ta.save(j["out"], w, m.sr)
    print(f"[{i + 1}/{len(jobs)}] {j['text'][:50]}", flush=True)
