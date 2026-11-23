import json, subprocess, sys, os
d = sys.argv[1]
MIN = {2: 3.0, 4: 3.0, 6: 3.4}
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
    return [w for w in scenes[si]['words'] if w[2].lower().startswith(txt)][k][0]
ev = {
    'walk1': [S[1], S[1] + 2.2], 'chest1': S[2] + 0.2, 'hazlo': word(2, 'hazlo'),
    'walk2': [S[3], S[3] + 2.4], 'chest2': S[4] + 0.2, 'descanso': word(4, 'cinco'), 'x4': word(4, 'repite'),
    'walk3': [S[5], S[5] + 2.0], 'boss': S[5] + 0.5,
    'hits': [S[6] + 0.3, S[6] + 1.0, S[6] + 1.7, S[6] + 2.4], 'win': S[6] + 2.9,
    'lvl1': S[1], 'lvl2': S[3], 'lvl3': S[5], 'cta': S[7],
}
json.dump({'total': round(t, 3), 'scenes': scenes, 'ev': ev}, open(os.path.join(d, 'timeline.json'), 'w'), ensure_ascii=False)
print(round(t, 2), S)
