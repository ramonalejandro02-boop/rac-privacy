"""Transcribe segmentos con faster-whisper y devuelve palabras con tiempos.
Uso: python asr.py lista.json salida.json   (lista = [ruta_wav, ...])
"""
import json, sys
from faster_whisper import WhisperModel

m = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for p in json.load(open(sys.argv[1])):
    segs, _ = m.transcribe(p, language="es", word_timestamps=True, beam_size=5, vad_filter=False)
    words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
    out[p] = words
    print(p.split("/")[-1], " ".join(w["w"] for w in words), flush=True)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
