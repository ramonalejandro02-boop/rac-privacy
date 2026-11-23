"""Convierte timeline.json (voces Kokoro verificadas con Whisper) al formato del motor de animación:
out/voice.json (líneas, palabras y envolvente de boca) y timeline.js (tiempos para score.js)."""
import json, re, unicodedata, os
tl = json.load(open('timeline.json'))
norm = lambda w: re.sub(r'[^a-zñ0-9]', '', unicodedata.normalize('NFD', w.lower()).encode('ascii', 'ignore').decode()) if w else ''
lines = []
for s in tl['segments']:
    sw, aw, ws, j = s['text'].split(), s.get('words', []), [], 0
    for w in sw:
        hit = -1
        for d in range(3):
            if j + d < len(aw):
                a, b = norm(aw[j + d]['w']), norm(w)
                if a and b and (a.startswith(b[:3]) or b.startswith(a[:3])): hit = j + d; break
        if hit >= 0: ws.append({'w': w, 't': aw[hit]['s'], 'end': aw[hit]['e']}); j = hit + 1
        else: ws.append({'w': w, 't': None, 'end': None})
    for k, x in enumerate(ws):
        if x['t'] is None:
            pv = next((y for y in reversed(ws[:k]) if y['t'] is not None), None); nx = next((y for y in ws[k + 1:] if y['t'] is not None), None)
            a = pv['end'] if pv else s['start']; b = nx['t'] if nx else s['end']; x['t'], x['end'] = a, max(a + .05, b)
    lines.append({'t': s['start'], 'end': s['end'], 'text': s['text'], 'who': s.get('who', 'nar'), 'scene': s['scene'], 'words': ws})
env = tl['env']
os.makedirs('out', exist_ok=True)
json.dump({'engine': 'kokoro', 'lines': lines, 'mouth': {'fps': 30, 'open': env, 'wide': [.5] * len(env)}}, open('out/voice.json', 'w'), ensure_ascii=False)
open('timeline.js', 'w').write('(function(){const D=' + json.dumps({'duration': tl['duration'], 'lines': [{k: l[k] for k in ('t', 'end', 'who', 'scene', 'text')} | {'words': l['words']} for l in lines]}, ensure_ascii=False) + ';if(typeof module!=="undefined")module.exports=D;else globalThis.TLD=D;})();\n')
print('ok', tl['duration'], len(lines))
