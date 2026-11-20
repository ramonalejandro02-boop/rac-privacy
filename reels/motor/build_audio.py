"""Motor de audio CONAFEPH: narración (Piper TTS local), música generada y efectos.

Uso: python3 build_audio.py <guion.json> <carpeta_salida> <modelo_voz.onnx | ref.wav> [python_chatterbox]
Si el 3er argumento es un .wav se usa Chatterbox (voz humana) con esa voz de referencia.
Salida: audio.wav (mezcla final), timeline.json (tiempos por segmento y envolvente para animar bocas).
"""
import json, subprocess, sys, wave, os
import numpy as np

SR = 44100
FPS = 30


def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:  # remuestreo lineal
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    return x


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def tts(text, model, out, speed):
    subprocess.run([sys.executable, "-m", "piper", "-m", model, "-f", out,
                    "--length-scale", str(speed), "--sentence-silence", "0.15"],
                   input=text.encode(), check=True, capture_output=True)
    x = read_wav(out)
    # recortar silencios de bordes
    idx = np.where(np.abs(x) > 0.01)[0]
    x = x[max(0, idx[0] - 800): idx[-1] + 1600] if len(idx) else x
    # ecualización suave: un poco de calidez y presencia
    return x / (np.max(np.abs(x)) + 1e-9) * 0.89


def adsr(n, a, r):
    e = np.ones(n)
    a = min(a, n); r = min(r, n - a)
    e[:a] = np.linspace(0, 1, a)
    if r > 0: e[-r:] = np.linspace(1, 0, r)
    return e


def note(f, dur, kind="pad"):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == "pad":
        s = sum(np.sin(2 * np.pi * f * k * t + k) / k ** 1.6 for k in range(1, 6))
        s += 0.5 * np.sin(2 * np.pi * f * 1.004 * t)  # leve coro
        return s * adsr(n, int(0.35 * SR), int(0.6 * SR)) * 0.16
    if kind == "pluck":
        s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
        return s * np.exp(-t * 7) * adsr(n, 60, 400) * 0.22
    if kind == "bass":
        s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
        return s * np.exp(-t * 1.6) * adsr(n, 200, 2000) * 0.34


def music(total):
    bpm = 96; beat = 60 / bpm; bar = 4 * beat
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69])]  # C G Am F
    out = np.zeros(int((total + 3) * SR))
    rng = np.random.default_rng(7)
    t0 = 0.0; i = 0
    while t0 < total + 1:
        root, ch = prog[i % 4]
        def add(sig, at):
            s = int(at * SR); e = min(len(out), s + len(sig)); out[s:e] += sig[: e - s]
        for m in ch[:3]: add(note(hz(m), bar + 0.4, "pad"), t0)
        add(note(hz(root), bar, "bass"), t0)
        arp = [ch[0], ch[1], ch[2], ch[3], ch[2], ch[1], ch[2], ch[3]]
        for k, m in enumerate(arp): add(note(hz(m + 12), beat * 1.5, "pluck") * (0.8 if k % 2 else 1), t0 + k * beat / 2)
        for b in range(4):  # bombo suave + shaker
            n = int(0.25 * SR); tt = np.arange(n) / SR
            if b in (0, 2): add(np.sin(2 * np.pi * (50 + 70 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14) * 0.38, t0 + b * beat)
            for off in (0.5,):
                nn = int(0.06 * SR); add(rng.normal(0, 1, nn) * np.exp(-np.arange(nn) / SR * 70) * 0.045, t0 + (b + off) * beat)
        t0 += bar; i += 1
    out = out[: int(total * SR)]
    out *= adsr(len(out), int(1.5 * SR), int(2.5 * SR))
    return out / (np.max(np.abs(out)) + 1e-9)


def whoosh(d=0.55):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.random.default_rng(3).normal(0, 1, n)
    # filtro paso bajo móvil sencillo
    y = np.zeros(n); a = 0
    for k in range(n):
        c = 0.02 + 0.25 * np.sin(np.pi * k / n); a += c * (x[k] - a); y[k] = a
    return y * np.sin(np.pi * t / d) ** 2 * 0.5


def pop(d=0.12):
    n = int(d * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 2500 * t) * t) * np.exp(-t * 40) * 0.35


def clean(x, max_gap=0.32):
    x = x / (np.max(np.abs(x)) + 1e-9)
    hop = 441; n = len(x) // hop
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    voiced = rms > 0.025
    if not voiced.any(): return x * .89
    a, b = np.argmax(voiced), n - np.argmax(voiced[::-1])
    a = max(0, a - 10); b = min(n, b + 22)          # 0.1 s antes, 0.22 s despues (no cortar finales)
    out = []; i = a; gap = 0
    while i < b:
        if not voiced[i]:
            gap += 1
            if gap * hop / SR > max_gap: i += 1; continue   # recorta silencios internos largos
        else: gap = 0
        out.append(x[i * hop:(i + 1) * hop]); i += 1
    y = np.concatenate(out)
    f = int(.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y * .89


def main(script_path, out_dir, model, py=None):
    os.makedirs(out_dir, exist_ok=True)
    sc = json.load(open(script_path))
    speed = sc.get("speed", 1.0)
    t = sc.get("lead", 0.5)
    segs = []; voice_parts = []
    human = model.endswith(".wav") or model == "default" or model.startswith("kokoro:")
    if human:
        jobs = [{"text": s.get("say", s["text"]), "out": f"{out_dir}/seg{i:02d}.wav", "exaggeration": s.get("exag", sc.get("exag", 0.55)), "cfg": s.get("cfg", sc.get("cfg", 0.45)), "seed": s.get("seed", 1234)}
                for i, s in enumerate(sc["segments"])]
        todo = [j for j in jobs if not os.path.exists(j["out"])]
        if todo:
            json.dump(todo, open(f"{out_dir}/jobs.json", "w"), ensure_ascii=False)
            if model.startswith("kokoro:"):
                subprocess.run([py, os.path.join(os.path.dirname(__file__), "tts_kokoro.py"), f"{out_dir}/jobs.json", model.split(":", 1)[1]], check=True)
            else:
                subprocess.run([py, os.path.join(os.path.dirname(__file__), "tts_chatterbox.py"), f"{out_dir}/jobs.json", model], check=True)
    for i, s in enumerate(sc["segments"]):
        if human:
            x = clean(read_wav(f"{out_dir}/seg{i:02d}.wav")); write_wav(f"{out_dir}/clean{i:02d}.wav", x)
        x = x if human else tts(s.get("say", s["text"]), model, f"{out_dir}/seg{i:02d}.wav", s.get("speed", speed))
        d = len(x) / SR
        segs.append({**s, "start": round(t, 3), "end": round(t + d, 3)})
        voice_parts.append((t, x))
        t += d + s.get("pause", 0.3)
    if human:  # tiempos exactos por palabra (Whisper) sobre el audio limpio
        wavs = [f"{out_dir}/clean{i:02d}.wav" for i in range(len(segs))]
        json.dump(wavs, open(f"{out_dir}/asr_in.json", "w"))
        subprocess.run([py, os.path.join(os.path.dirname(__file__), "asr.py"), f"{out_dir}/asr_in.json", f"{out_dir}/asr.json"], check=True)
        asr = json.load(open(f"{out_dir}/asr.json"))
        for i, s in enumerate(segs):
            s["words"] = [{"w": w["w"], "s": round(s["start"] + w["s"], 3), "e": round(s["start"] + w["e"], 3)} for w in asr[wavs[i]]]
    total = t + sc.get("tail", 2.5)
    voice = np.zeros(int(total * SR))
    for st, x in voice_parts: voice[int(st * SR): int(st * SR) + len(x)] += x
    # envolvente para boca (por frame)
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(voice[k:k + hop] ** 2))) for k in range(0, len(voice), hop)]
    m = max(env) or 1; env = [round(min(1, e / m * 1.6), 3) for e in env]
    # escenas
    scenes = {}
    for s in segs:
        sc_id = s["scene"]; scenes.setdefault(sc_id, [s["start"], s["end"]]); scenes[sc_id][1] = s["end"]
    ids = list(scenes)
    for a, b in zip(ids, ids[1:]): scenes[a][1] = scenes[b][0] - 0.15  # cubrir pausas
    scenes[ids[-1]][1] = total
    # música con ducking bajo la voz
    mus = music(total)
    venv = np.repeat(np.array(env), hop)[: len(mus)]
    venv = np.convolve(venv, np.ones(SR // 5) / (SR // 5), mode="same")
    duck = 1 - 0.55 * np.clip(venv * 1.4, 0, 1)
    mix = voice * 0.95 + mus * sc.get("music", 0.11) * duck
    # efectos en cambios de escena y apariciones
    for c in sc.get("whoosh", []):
        w = whoosh(); st = int(max(0, segs[c]["start"] - 0.35) * SR); mix[st: st + len(w)] += w[: len(mix) - st] * 0.22
    for c in sc.get("pops", []):
        p = pop(); st = int(c * SR); mix[st: st + len(p)] += p[: len(mix) - st]
    mix /= max(1.0, np.max(np.abs(mix)) / 0.95)
    write_wav(f"{out_dir}/audio.wav", mix)
    json.dump({"duration": round(total, 3), "segments": segs, "scenes": {k: v for k, v in scenes.items()},
               "env": env, "fps": FPS}, open(f"{out_dir}/timeline.json", "w"), ensure_ascii=False)
    print("duración", round(total, 2), "s")
    for s in segs: print(f'{s["start"]:6.2f}-{s["end"]:6.2f} [{s["scene"]}] {s.get("who","nar")}: {s["text"][:60]}')


if __name__ == "__main__":
    main(*sys.argv[1:5])
