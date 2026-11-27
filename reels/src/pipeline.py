"""Reel pipeline: scene audio -> word timeline -> HTML build -> frames -> mixed MP4.
Usage: python3 pipeline.py <audio_dir> <output.mp4>
"""
import json, subprocess, sys, wave, os
import numpy as np

AUDIO, OUT = sys.argv[1], sys.argv[2]
GAP, LEAD = 0.12, 0.25
SR = 44100


def load(f):
    w = wave.open(f)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() == 2:
        a = a.reshape(-1, 2).mean(1)
    sr = w.getframerate()
    x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
    return np.interp(x, np.arange(len(a)), a)


def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    s, e = max(0, idx[0] - int(.05 * SR)), min(len(a), idx[-1] + int(.12 * SR))
    return a[s:e]


def squeeze(a, maxsil=0.2, thr=0.01):
    """Cap every internal silence at `maxsil` seconds (no dead air), with 5 ms fades at each cut."""
    win = int(.02 * SR)
    e = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, 'same'))
    sil = e < thr
    keep = np.ones(len(a), bool)
    i, cap = 0, int(maxsil * SR)
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]:
                j += 1
            if j - i > cap:
                mid = (i + j) // 2
                keep[mid - (j - i - cap) // 2: mid + (j - i - cap + 1) // 2] = False
            i = j
        else:
            i += 1
    out, f = [], int(.005 * SR)
    edges = np.flatnonzero(np.diff(np.r_[0, keep.astype(int), 0]))
    for s, e2 in zip(edges[::2], edges[1::2]):
        seg = a[s:e2].copy()
        if len(seg) > 2 * f:
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        out.append(seg)
    return np.concatenate(out)


def align(text, heard, dur, t0):
    """Give every script word a time: copy times from matching heard words, interpolate the rest."""
    import difflib, re
    norm = lambda w: re.sub(r'[^a-z0-9áéíóúñü]', '', w.lower())
    script = text.split()
    sm = difflib.SequenceMatcher(None, [norm(w) for w in script], [norm(h[0]) for h in heard], autojunk=False)
    times = [None] * len(script)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = heard[blk.b + k][1:]
    for op, i1, i2, j1, j2 in sm.get_opcodes():  # replaced spans: spread heard span over script span
        if op == 'replace' and j2 > j1:
            s0, e0 = heard[j1][1], heard[j2 - 1][2]
            for k, i in enumerate(range(i1, i2)):
                times[i] = (s0 + (e0 - s0) * k / (i2 - i1), s0 + (e0 - s0) * (k + 1) / (i2 - i1))
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(script)):  # remaining gaps: linear interpolation by character length
        if times[i] is None:
            lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
            a = times[lo][1] if lo is not None else 0.0
            b = times[hi][0] if hi is not None else dur
            span = [j for j in range(i, len(script)) if times[j] is None and (hi is None or j < hi)]
            tot = sum(len(script[j]) for j in span) or 1; acc = a
            for j in span:
                d = (b - a) * len(script[j]) / tot; times[j] = (acc, acc + d); acc += d
            known = [k for k, t in enumerate(times) if t]
    return [{'w': w, 's': round(t0 + t[0], 3), 'e': round(t0 + t[1], 3)} for w, t in zip(script, times)]


def timeline(guion):
    from faster_whisper import WhisperModel
    m = WhisperModel('small', device='cpu', compute_type='int8')
    t0, scenes, clips = LEAD, [], {}
    for s in guion:
        a = squeeze(trim(load(f"{AUDIO}/{s['id']}.wav")))
        clips[s['id']] = a
        a16 = np.interp(np.linspace(0, len(a) - 1, int(len(a) * 16000 / SR)), np.arange(len(a)), a).astype(np.float32)
        dur = len(a) / SR
        segs, _ = m.transcribe(a16, language='es', word_timestamps=True, vad_filter=False)
        heard = [(x.word.strip(), x.start, x.end) for sg in segs for x in sg.words]
        words = align(s['text'], heard, dur, t0)
        print(s['id'], f"({len(heard)} oídas / {len(words)} guion)", '|', ' '.join(w['w'] for w in words), flush=True)
        scenes.append({'id': s['id'], 'start': round(t0, 3), 'dur': round(dur, 3), 'end': round(t0 + dur, 3), 'words': words})
        t0 += dur + GAP
    return {'scenes': scenes, 'total': round(t0 + 0.6, 3)}, clips


def mix(tl, clips, path):
    T = tl['total']; N = int(T * SR); t = np.arange(N) / SR
    voice = np.zeros(N)
    for s in tl['scenes']:
        a = clips[s['id']]; i = int(s['start'] * SR); voice[i:i + len(a)] += a[:N - i]
    voice /= np.abs(voice).max() + 1e-9; voice *= 0.89
    music = np.zeros(N)
    n = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
    L = 4.0
    for k in range(int(T / L) + 1):
        st = int(k * L * SR); en = min(N, int((k + 1) * L * SR) + int(1.5 * SR))
        if st >= N: break
        tt = np.arange(en - st) / SR
        env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - L) / 0.6)
        for mm in chords[k % 4]:
            f = n(mm); music[st:en] += env * (np.sin(2 * np.pi * f * tt) * .6 + np.sin(2 * np.pi * f * 2.003 * tt) * .12)
        music[st:en] += env * np.sin(2 * np.pi * n(chords[k % 4][0] - 12) * tt) * .5
    # one-pole lowpass via lfilter-like loop (vectorised with cumulative trick is unstable; keep simple)
    from scipy.signal import lfilter
    music = lfilter([0.06], [1, -0.94], music)
    music /= np.abs(music).max()
    music *= np.minimum(1, t / 2.0) * np.minimum(1, (T - t) / 2.5)
    win = int(.25 * SR)
    envv = np.convolve(np.abs(voice), np.ones(win) / win, 'same')
    music *= 0.16 * (1 - 0.55 * np.clip(envv / 0.08, 0, 1))
    rng = np.random.default_rng(1); fx = np.zeros(N)
    for s in tl['scenes'][1:]:
        st = int((s['start'] - .45) * SR); L2 = int(.6 * SR)
        yy = lfilter([0.08], [1, -0.92], rng.standard_normal(L2))
        fx[st:st + L2] += yy * np.sin(np.linspace(0, np.pi, L2)) ** 2
    fx = fx / np.abs(fx).max() * 0.10
    out = voice + music + fx; out /= max(1, np.abs(out).max() / 0.97)
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    guion = json.load(open('guion.json'))
    tl, clips = timeline(guion)
    json.dump(tl, open('timeline.json', 'w'), ensure_ascii=False, indent=1)
    open('build.html', 'w').write(open('reel.html').read().replace('__TIMELINE__', json.dumps(tl, ensure_ascii=False)))
    mix(tl, clips, 'mix.wav')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'mix.wav', '-af', 'loudnorm=I=-15:TP=-1.5:LRA=9', '-ar', '44100', '-ac', '2', 'mix_norm.wav'], check=True)
    env = dict(os.environ, NODE_PATH=subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip())
    subprocess.run(['node', 'render.js', 'full'], check=True, env=env)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'video_mute.mp4', '-i', 'mix_norm.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], check=True)
    print('LISTO', OUT, tl['total'])
