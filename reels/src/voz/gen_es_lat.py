"""Generate each scene sentence-by-sentence with Latin-American respelling; keep the best of up to 4 takes per sentence."""
import json, re, sys, difflib, torch, librosa, numpy as np, soundfile as sf
sys.argv = ['x']; import tts
from seseo import seseo
from faster_whisper import WhisperModel
R = '/tmp/claude-0/-home-user-rac-privacy/60f45fd2-d7d3-53ee-935e-2e8fb9afed24/scratchpad/reel'
wm = WhisperModel('small', device='cpu', compute_type='int8')
norm = lambda s: re.sub(r'[^a-záéíóúñü ]', '', s.lower()).split()
NUMS = {'225': 'doscientos veinticinco', '12': 'doce', '2026': 'dos mil veintiséis', '91': 'noventa y uno'}
def heard(path):
    a, _ = librosa.load(path, sr=16000); t = ' '.join(x.text for x in wm.transcribe(a, language='es')[0])
    for k, v in NUMS.items(): t = re.sub(rf'\b{k}\b', v, t)
    return t
for s in json.load(open(f'{R}/guion.json')):
    sents = [x for x in re.split(r'(?<=[.?!])\s+', s['text']) if x.strip()]
    parts = []
    for i, sent in enumerate(sents):
        best = (-1, None)
        for k in range(4):
            torch.manual_seed(300 + 17 * i + k); out = f"/tmp/claude-0/-home-user-rac-privacy/60f45fd2-d7d3-53ee-935e-2e8fb9afed24/scratchpad/voz/lat_{s['id']}_{i}_{k}.wav"
            tts.say(seseo(sent), out, ref='ref_grave.wav', ex=0.3, temp=0.65)
            r = difflib.SequenceMatcher(None, norm(sent), norm(heard(out))).ratio()
            if r > best[0]: best = (r, out)
            if r >= 0.97: break
        print(s['id'], i, f'{best[0]:.2f}', sent[:60], flush=True)
        w, sr = librosa.load(best[1], sr=None); idx = np.where(np.abs(w) > 0.012)[0]
        parts.append(w[max(0, idx[0] - 1200): idx[-1] + 3000])
    gap = np.zeros(int(.22 * sr)); out = parts[0]
    for p in parts[1:]: out = np.concatenate([out, gap, p])
    sf.write(f"{R}/audio_lat_raw/{s['id']}.wav", out, sr, subtype='PCM_16')
print('LISTO')
