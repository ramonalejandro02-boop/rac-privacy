import json, sys, os, subprocess, wave, numpy as np
d = sys.argv[1]
tl = json.load(open(os.path.join(d, 'timeline.json'))); ev = tl['ev']
SR = 48000; T = tl['total'] + 0.3; n = int(SR * T)
def note(m): return 440 * 2 ** ((m - 69) / 12)
# tense minor pad: Dm - Bb - Gm - A
chords = [[50, 53, 57], [46, 50, 53], [43, 50, 55], [45, 49, 52]]; cl = 2.4
mus = np.zeros(n)
for k in range(int(T / cl) + 1):
    a, b = int(k * cl * SR), min(n, int((k + 1) * cl * SR))
    if a >= n: break
    tt = np.arange(b - a) / SR; env = np.minimum(1, tt / .5) * np.minimum(1, (cl - tt) / .5)
    for m in chords[k % 4]:
        f = note(m); mus[a:b] += env * (np.sin(2*np.pi*f*tt) + .25*np.sin(2*np.pi*2*f*tt) + .2*np.sin(2*np.pi*f/2*tt))
for k in range(int(T / .5)):  # heartbeat-ish pulse
    a = int(k * .5 * SR); L = min(int(.22 * SR), n - a); tt = np.arange(L) / SR
    mus[a:a+L] += (1.8 if k % 2 == 0 else 1.0) * np.sin(2*np.pi*(48 + 50*np.exp(-tt*30))*tt) * np.exp(-tt*16)
mus = mus / np.abs(mus).max() * .10
sfx = np.zeros(n)
def add(at, sig):
    a = int(at * SR); b = min(n, a + len(sig)); sfx[a:b] += sig[:b - a]
def tone(f, L, dec): tt = np.arange(int(L * SR)) / SR; return np.sin(2*np.pi*f*tt) * np.exp(-tt*dec)
def incoming(): return .3 * np.concatenate([tone(880, .09, 30), tone(1320, .18, 18)])
def outgoing():
    tt = np.arange(int(.16 * SR)) / SR; return .25 * np.sin(2*np.pi*(500 + 2500*tt)*tt) * np.exp(-tt*20)
def whoosh():
    L = int(.3 * SR); x = np.random.default_rng(2).standard_normal(L); x = np.convolve(x, np.ones(30)/30, 'same')
    return .45 * x * np.sin(np.pi*np.arange(L)/L) ** 2
def alarm():
    tt = np.arange(int(.9 * SR)) / SR
    return .35 * np.sign(np.sin(2*np.pi*110*tt)) * np.exp(-tt*2.5) * .5 + .3 * np.sin(2*np.pi*(700 - 400*tt)*tt) * np.exp(-tt*3)
def ding(): return .3 * (tone(988, .5, 6) + .5 * tone(1480, .5, 8))
def boom():
    tt = np.arange(int(.6 * SR)) / SR; return .6 * np.sin(2*np.pi*(40 + 80*np.exp(-tt*12))*tt) * np.exp(-tt*5)
for s in tl['scenes'][1:]: add(s['start'] - .05, whoosh())
add(ev['m1'], incoming()); add(ev['m3'], incoming()); add(ev['m2'], outgoing()); add(ev['m4'], outgoing())
add(ev['m5'], alarm()); add(ev['scam'], boom())
for f in ('f1', 'f2', 'f3'): add(ev[f], ding())
add(ev['never'] + .9, boom()); add(ev['cta'] + .6, outgoing())
# silence music during the twist hit for impact
dip = np.ones(n); a, b = int(ev['m5'] * SR), int((ev['scam'] + .4) * SR); dip[a:b] = .25
mus *= dip
def wav(name, x):
    x = np.clip(x, -1, 1); w = wave.open(os.path.join(d, name), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
wav('music.wav', mus); wav('sfx.wav', sfx)
st = [s['start'] for s in tl['scenes']]; inputs = []; flt = []
for i, s in enumerate(st):
    inputs += ['-i', os.path.join(d, f's{i+1}.mp3')]; ms = int(s * 1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inputs += ['-i', os.path.join(d, 'music.wav'), '-i', os.path.join(d, 'sfx.wav')]; k = len(st)
flt.append(''.join(f'[v{i}]' for i in range(k)) + f'amix=inputs={k}:normalize=0[voice]')
flt.append(f'[voice]asplit=2[vo][sc];[{k}:a][sc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[duck];[vo][duck][{k+1}:a]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(flt), '-map', '[out]', '-t', str(tl['total']), '-c:a', 'aac', '-b:a', '192k', os.path.join(d, 'audio.m4a')], check=True)
print('ok')
