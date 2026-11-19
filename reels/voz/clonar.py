"""Genera voz en off con la voz clonada de Alejandro (Chatterbox multilingüe, CPU).

Requiere un entorno con acceso a Hugging Face. Instalación (una vez por sesión):
  uv venv -p 3.11 clone-env && . clone-env/bin/activate && uv pip install -q chatterbox-tts "setuptools<81" faster-whisper
Uso (desde la raíz del repo):
  python reels/voz/clonar.py guion.json carpeta_salida
guion.json = [["texto a decir (números en letras)", "texto esperado"], ...]
Salida: 1.wav, 2.wav, ... (mejor de hasta 3 tomas, verificada con Whisper).
"""
import sys, json, os, re, unicodedata, difflib, torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from faster_whisper import WhisperModel

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref.wav")
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
lines = json.load(open(src))
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
asr = WhisperModel("small", device="cpu", compute_type="int8")
for i, (l, exp) in enumerate(lines):
    best = None
    for take in range(3):
        torch.manual_seed(900 + i * 10 + take)
        w = m.generate(l, language_id="es", audio_prompt_path=REF, exaggeration=0.55, cfg_weight=0.4)
        p = f"{out}/{i+1}_t{take}.wav"; ta.save(p, w, m.sr)
        segs, _ = asr.transcribe(p, language="es"); hyp = " ".join(s.text for s in segs)
        sc = difflib.SequenceMatcher(None, norm(exp), norm(hyp)).ratio()
        print("TAKE", i + 1, take, round(w.shape[-1] / m.sr, 2), round(sc, 2), hyp, flush=True)
        if best is None or sc > best[0]: best = (sc, p)
        if sc >= 0.93: break
    os.replace(best[1], f"{out}/{i+1}.wav")
    for f in os.listdir(out):
        if "_t" in f: os.remove(os.path.join(out, f))
