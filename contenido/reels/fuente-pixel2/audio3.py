import json, sys, os, subprocess, wave, numpy as np
d = sys.argv[1]
tl = json.load(open(os.path.join(d, 'timeline.json'))); ev = tl['ev']
SR = 48000; T = tl['total'] + 0.3; n = int(SR * T)
def f(m): return 440 * 2 ** ((m - 69) / 12)
def sq(freq, L, duty=.5, dec=0):
    tt = np.arange(int(L * SR)) / SR
    x = np.where((tt * freq) % 1 < duty, 1.0, -1.0)
    env = np.minimum(1, tt / .005) * np.minimum(1, (L - tt) / .01)
    if dec: env *= np.exp(-tt * dec)
    return x * env
def tri(freq, L):
    tt = np.arange(int(L * SR)) / SR; x = 2 * np.abs(2 * ((tt * freq) % 1) - 1) - 1
    return x * np.minimum(1, (L - tt) / .01)
mus = np.zeros(n)
def put(buf, at, sig, g=1.0):
    a = int(at * SR); b = min(n, a + len(sig))
    if a < n: buf[a:b] += g * sig[:b - a]
# chiptune loop: 120 bpm, 8th notes 0.25s; progression Am F C G (2 bars each = 2s)
step = .25
prog = [(57, [69, 72, 76, 72]), (53, [65, 69, 72, 69]), (48, [64, 67, 72, 67]), (55, [62, 67, 71, 67])]
k = 0; t = 0.0
while t < T:
    root, arp = prog[(k // 8) % 4]
    put(mus, t, sq(f(arp[k % 4]), step * .9, .25, 6), .22)
    if k % 2 == 0: put(mus, t, tri(f(root - 12), step * 1.8), .35)
    if k % 4 == 0:  # kick noise
        tt = np.arange(int(.08 * SR)) / SR; put(mus, t, np.sin(2*np.pi*(60 + 140*np.exp(-tt*40))*tt) * np.exp(-tt*30), .5)
    if k % 4 == 2:
        nz = np.random.default_rng(k).uniform(-1, 1, int(.05 * SR)) * np.exp(-np.arange(int(.05*SR))/SR*60); put(mus, t, nz, .12)
    k += 1; t += step
# boss section: lower the music a bit and add tension notes
mus *= .55
sfx = np.zeros(n)
def blip(seq, L=.07, duty=.5, g=.3):
    return np.concatenate([sq(f(m), L, duty) for m in seq]) * g
chest = blip([72, 76, 79, 84], .06)
levelup = blip([60, 64, 67, 72, 76, 79, 84], .06, .25)
coin = blip([83, 88], .07, .5, .28)
step_s = blip([45], .03, .5, .12)
hit = np.random.default_rng(7).uniform(-1, 1, int(.15 * SR)) * np.exp(-np.arange(int(.15*SR))/SR*25) * .45 + np.pad(blip([40], .1, .5, .3), (0, int(.15*SR)))[:int(.15*SR)]
victory = blip([72, 72, 72, 72, 68, 70, 72, 70, 72], .11, .5, .3)
roar = blip([40, 38, 36, 35], .12, .5, .35)
for lv in ('lvl1', 'lvl2', 'lvl3'): put(sfx, ev[lv], levelup)
put(sfx, ev['chest1'], chest); put(sfx, ev['chest1'] + .3, coin)
put(sfx, ev['chest2'], chest); put(sfx, ev['chest2'] + .3, coin)
put(sfx, ev['hazlo'], coin); put(sfx, ev['x4'], coin)
put(sfx, ev['boss'], roar)
for h in ev['hits']: put(sfx, h, hit)
put(sfx, ev['win'], victory)
put(sfx, ev['cta'], levelup)
for a, b in (ev['walk1'], ev['walk2'], ev['walk3']):
    x = a
    while x < b: put(sfx, x, step_s); x += .25
def wav(name, x):
    x = np.clip(x, -1, 1); w = wave.open(os.path.join(d, name), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
wav('music.wav', mus * .5); wav('sfx.wav', sfx * .8)
st = [s['start'] for s in tl['scenes']]; inputs = []; flt = []
for i, s in enumerate(st):
    inputs += ['-i', os.path.join(d, f's{i+1}.mp3')]; ms = int(s * 1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inputs += ['-i', os.path.join(d, 'music.wav'), '-i', os.path.join(d, 'sfx.wav')]; k = len(st)
flt.append(''.join(f'[v{i}]' for i in range(k)) + f'amix=inputs={k}:normalize=0[voice]')
flt.append(f'[voice]asplit=2[vo][sc];[{k}:a][sc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[duck];[vo][duck][{k+1}:a]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(flt), '-map', '[out]', '-t', str(tl['total']), '-c:a', 'aac', '-b:a', '192k', os.path.join(d, 'audio.m4a')], check=True)
print('ok')
