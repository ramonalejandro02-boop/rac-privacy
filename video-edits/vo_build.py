import sys, json, re, difflib, subprocess, numpy as np, soundfile as sf, scipy.signal as ss
sys.path.insert(0, "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad")
from tts import Kokoro
from faster_whisper import WhisperModel
S = "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad"
SCRIPT = json.load(open(sys.argv[1] if len(sys.argv) > 1 else f"{S}/script.json"))
VO = sys.argv[2] if len(sys.argv) > 2 else f"{S}/vo"
k = Kokoro()
wm = WhisperModel(f"{S}/whisper-small", device="cpu", compute_type="int8")
norm = lambda w: re.sub(r"[^a-záéíóúñü0-9]", "", w.lower())
out = {}
for seg in SCRIPT:
    key, text = seg["id"], seg["vo"]
    plain = seg.get("tts", text.replace("*", ""))
    a, sr, ph = k(plain, sid=29, speed=seg.get("speed", 1.05))
    a = a / (np.abs(a).max() + 1e-9) * 0.9
    raw = f"{VO}/{key}_raw.wav"; sf.write(raw, a, sr)
    wav = f"{VO}/{key}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
        "highpass=f=80,equalizer=f=200:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,"
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
        "-ar", "48000", "-ac", "1", wav], check=True)
    v, _ = sf.read(wav, dtype="float32")
    a16 = ss.resample_poly(v, 16000, 48000).astype(np.float32)
    segs, _ = wm.transcribe(a16, language="es", word_timestamps=True, initial_prompt=plain)
    ww = [w for s in segs for w in s.words]
    script_words = text.split()
    sw = [norm(w.replace("*", "")) for w in script_words]
    hw = [norm(w.word) for w in ww]
    times = [None] * len(sw)
    sm = difflib.SequenceMatcher(a=sw, b=hw, autojunk=False)
    for blk in sm.get_matching_blocks():
        for j in range(blk.size):
            times[blk.a + j] = (ww[blk.b + j].start, ww[blk.b + j].end)
    dur = len(v) / 48000
    # interpolate gaps
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(times)):
        if times[i] is None:
            prev = max([j for j in known if j < i], default=None)
            nxt = min([j for j in known if j > i], default=None)
            t0 = times[prev][1] if prev is not None else 0.0
            t1 = times[nxt][0] if nxt is not None else dur
            gap = [j for j in range(len(times)) if (prev is None or j > prev) and (nxt is None or j < nxt)]
            n = len(gap); pos = gap.index(i)
            times[i] = (t0 + (t1 - t0) * pos / n, t0 + (t1 - t0) * (pos + 1) / n)
    out[key] = {"dur": dur, "words": [{"w": w, "s": round(t[0], 3), "e": round(t[1], 3)} for w, t in zip(script_words, times)],
                "matched": len(known), "total": len(sw), "heard": " ".join(x.word for x in ww)}
    print(key, round(dur, 2), f"{len(known)}/{len(sw)}", "|", out[key]["heard"], flush=True)
json.dump(out, open(f"{VO}/timing.json", "w"), ensure_ascii=False, indent=1)
