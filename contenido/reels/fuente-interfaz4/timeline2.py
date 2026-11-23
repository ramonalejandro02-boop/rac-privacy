import json, subprocess, sys, os
d = sys.argv[1]
MIN = {4: 2.4}
scenes = []; t = 0
for i in range(1, 9):
    f = os.path.join(d, f's{i}.mp3')
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
    dur = max(round(dur - 0.25, 3), MIN.get(i, 0))
    if i == 8: dur += 2.0
    w = json.load(open(f + '.json'))
    scenes.append({'start': round(t, 3), 'dur': dur, 'words': [[round(t + a, 3), round(t + a + b, 3), x] for a, b, x in w]})
    t += dur
S = [s['start'] for s in scenes]
def word(si, txt, k=0):
    ws = [w for w in scenes[si]['words'] if w[2].lower().startswith(txt)]
    return ws[k][0]
ev = {
    'typing1': [S[0] + 0.2, S[0] + 0.9], 'm1': S[0] + 0.9,
    'm2': S[1] + 1.9,
    'typing2': [S[2] + 0.1, S[2] + 0.8], 'm3': S[2] + 0.8,
    'm4': S[3] + 0.6,
    'm5': S[4] + 0.5, 'scam': S[4] + 1.7,
    'f1': word(5, 'prisa'), 'f2': word(5, 'código'), 'f3': word(5, 'primero'),
    'never': S[6], 'cta': S[7],
}
json.dump({'total': round(t, 3), 'scenes': scenes, 'ev': ev}, open(os.path.join(d, 'timeline.json'), 'w'), ensure_ascii=False)
print(round(t, 2), S, ev)
