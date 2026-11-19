"""Une las frases de la voz clonada en un solo audio, limpio y sin silencios largos.

Uso:  python3 unir_voz.py levantate
Lee   reels/<historia>/clon/vo/1.wav, 2.wav, ...
Crea  reels/<historia>/voz.wav  y  voz_segs.json  (tiempos exactos por escena para armar_reel.py)
"""
import glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAUSA = 0.7          # silencio entre escenas (s)
CLEAN = ("silenceremove=start_periods=1:start_threshold=-42dB,"
         "silenceremove=stop_periods=-1:stop_duration=0.4:stop_threshold=-42dB:stop_silence=0.22,"  # acorta pausas internas
         "areverse,silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
         "highpass=f=70,loudnorm=I=-16:TP=-1.5")

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout)

def main(name):
    folder = os.path.join(HERE, name)
    srcs = sorted(glob.glob(os.path.join(folder, "clon", "vo", "[0-9]*.wav")), key=lambda p: int(os.path.basename(p).split(".")[0]))
    if not srcs: sys.exit("No hay audios en clon/vo/")
    tmp, segs, t = [], [], 0.0
    for i, s in enumerate(srcs):
        o = os.path.join(folder, f"_t{i}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", s, "-af", CLEAN, "-ar", "44100", "-ac", "1", o], check=True)
        d = dur(o); lead = 0.15 if i == 0 else 0.3
        segs.append([t, t + lead + d + PAUSA, t + lead, t + lead + d]); tmp.append((o, lead)); t += lead + d + PAUSA
    segs[-1][1] += 0.8
    fc = "".join(f"[{k}]adelay={int(l * 1000)},apad=pad_dur={PAUSA}[a{k}];" for k, (_, l) in enumerate(tmp))
    fc += "".join(f"[a{k}]" for k in range(len(tmp))) + f"concat=n={len(tmp)}:v=0:a=1"
    cmd = ["ffmpeg", "-v", "error", "-y"] + sum([["-i", o] for o, _ in tmp], []) + ["-filter_complex", fc, os.path.join(folder, "voz.wav")]
    subprocess.run(cmd, check=True)
    for o, _ in tmp: os.remove(o)
    json.dump(segs, open(os.path.join(folder, "voz_segs.json"), "w"))
    print("Escenas (s):", [round(b - a, 2) for a, b, _, _ in segs], "total", round(segs[-1][1], 1))

if __name__ == "__main__":
    main(sys.argv[1])
