import json, sys, os, subprocess, wave, numpy as np
d = sys.argv[1]
tl = json.load(open(os.path.join(d, 'timeline.json'))); ev = tl['ev']; S = ev['S']
SR = 48000; T = tl['total'] + 0.3; n = int(SR * T)
rng = np.random.default_rng(3)
def f(m): return 440 * 2 ** ((m - 69) / 12)
def put(buf, at, sig, g=1.0):
    a = int(at * SR); b = min(n, a + len(sig))
    if 0 <= a < n: buf[a:b] += g * sig[:b - a]
def saw(freq, L):
    tt = np.arange(int(L * SR)) / SR; return 2 * ((tt * freq) % 1) - 1
def lp(x, k=8): return np.convolve(x, np.ones(k) / k, 'same')
mus = np.zeros(n)
# dark synth: 100 bpm 16ths bass on Em - C - Am - B
step = .15; bass = [40, 36, 45, 47]; t = 0; k = 0
while t < T:
    r = bass[(k // 16) % 4]
    L = step * .8; tt = np.arange(int(L * SR)) / SR
    put(mus, t, lp(saw(f(r), L), 24) * np.exp(-tt * 9), .5)
    if k % 8 == 0:
        tt = np.arange(int(.12 * SR)) / SR; put(mus, t, np.sin(2*np.pi*(50 + 120*np.exp(-tt*35))*tt) * np.exp(-tt*22), .8)
    if k % 4 == 2:
        hh = rng.uniform(-1, 1, int(.03 * SR)) * np.exp(-np.arange(int(.03*SR))/SR*120); put(mus, t, hh, .15)
    k += 1; t += step
# pad
for c in range(int(T / 2.4) + 1):
    r = bass[c % 4] + 24; tt = np.arange(int(2.4 * SR)) / SR; env = np.minimum(1, tt / .6) * np.minimum(1, (2.4 - tt) / .6)
    for m in (r, r + 7, r + 12): put(mus, c * 2.4, np.sin(2*np.pi*f(m)*tt) * env, .08)
mus = mus / np.abs(mus).max() * .10
sfx = np.zeros(n)
def click():
    L = int(.025 * SR); return rng.uniform(-1, 1, L) * np.exp(-np.arange(L)/SR*250) * .35
def beep(fr, L=.12, g=.25):
    tt = np.arange(int(L * SR)) / SR; return np.sign(np.sin(2*np.pi*fr*tt)) * np.exp(-tt*8) * g
def typing(a, b, rate=14):
    x = a
    while x < b: put(sfx, x + rng.uniform(0, .02), click()); x += 1 / rate
def alarm():
    out = np.concatenate([beep(880, .18, .3), np.zeros(int(.07*SR)), beep(660, .18, .3)]); return np.concatenate([out, out])
for s in S[1:]:
    L = int(.12 * SR); put(sfx, s, rng.uniform(-1, 1, L) * np.exp(-np.arange(L)/SR*30) * .25)  # static cut
typing(.2, 1.5)
for x in ev['p1keys']: put(sfx, x, click())
typing(S[2], S[2] + .8); typing(S[3], S[3] + 1.2); typing(S[6], S[6] + .6)
for x in ev['p4keys']: typing(x, x + .25)
put(sfx, 1.8, beep(1200, .06)); put(sfx, 2.4, beep(1200, .06))
put(sfx, ev['hook'], beep(440, .3))
put(sfx, ev['r1'], alarm()); put(sfx, ev['r2'], beep(520, .35, .3))
put(sfx, ev['r3'], beep(1046, .12)); put(sfx, ev['r3'] + .13, beep(1318, .2))
put(sfx, ev['truco'], beep(784, .1)); put(sfx, ev['truco'] + .11, beep(1046, .2))
put(sfx, ev['r4'], beep(1046, .12)); put(sfx, ev['r4'] + .13, beep(1318, .2))
put(sfx, ev['tfa'], beep(1200, .08)); put(sfx, ev['correct'], beep(1200, .08))
put(sfx, ev['denied'], alarm())
put(sfx, ev['cta'], beep(880, .1)); put(sfx, ev['cta'] + .12, beep(1318, .25))
def wav(name, x):
    x = np.clip(x, -1, 1); w = wave.open(os.path.join(d, name), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
wav('music.wav', mus); wav('sfx.wav', sfx * .8)
inputs = []; flt = []
for i, s in enumerate(S):
    inputs += ['-i', os.path.join(d, f's{i+1}.mp3')]; ms = int(s * 1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inputs += ['-i', os.path.join(d, 'music.wav'), '-i', os.path.join(d, 'sfx.wav')]; k = len(S)
flt.append(''.join(f'[v{i}]' for i in range(k)) + f'amix=inputs={k}:normalize=0[voice]')
flt.append(f'[voice]asplit=2[vo][sc];[{k}:a][sc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[duck];[vo][duck][{k+1}:a]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(flt), '-map', '[out]', '-t', str(tl['total']), '-c:a', 'aac', '-b:a', '192k', os.path.join(d, 'audio.m4a')], check=True)
print('ok')
