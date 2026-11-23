import json, subprocess, sys, os
d = sys.argv[1]
MIN = {3: 4.0}
scenes = []; t = 0
for i in range(1, 9):
    f = os.path.join(d, f's{i}.mp3')
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
    dur = max(round(dur - 0.25, 3), MIN.get(i, 0))
    if i == 8: dur += 2.2
    w = json.load(open(f + '.json'))
    scenes.append({'start': round(t, 3), 'dur': dur, 'words': [[round(t + a, 3), round(t + a + b, 3), x] for a, b, x in w]})
    t += dur
S = [s['start'] for s in scenes]
def word(si, txt, k=0):
    return [w for w in scenes[si]['words'] if w[2].lower().startswith(txt)][k][0]
ev = {
    'S': S,
    'hook': word(0, 'vamos'),
    'p1keys': [word(1, x) for x in ('uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis')], 'r1': word(1, 'menos'), 'top': word(1, 'y'),
    'r2': word(2, 'veinte'),
    'r3': word(3, 'millón'),
    'truco': word(4, 'truco'),
    'p4keys': [word(5, x) for x in ('gato', 'nube', 'tornillo', 'mango', 'río', 'lápiz')], 'r4': word(5, 'setecientos'), 'easy': word(5, 'fácil'),
    'tfa': word(6, 'verificación'), 'correct': word(6, 'aunque'), 'denied': word(6, 'no', 0) if False else word(6, 'entran'),
    'cta': S[7],
}
json.dump({'total': round(t, 3), 'scenes': scenes, 'ev': ev}, open(os.path.join(d, 'timeline.json'), 'w'), ensure_ascii=False)
print(round(t, 2), S)
