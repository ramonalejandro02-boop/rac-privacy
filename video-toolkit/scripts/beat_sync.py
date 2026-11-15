#!/usr/bin/env python3
"""Sincroniza cortes con el ritmo de la música.

1) Analiza la canción: tempo (BPM) y golpes -> beats.json (útil también en Remotion).
2) Con --clips, monta automáticamente un video cortando en cada golpe (o cada N golpes).

Uso:
  python beat_sync.py cancion.mp3                                   # solo análisis
  python beat_sync.py cancion.mp3 --clips carpeta_clips/ -o montaje.mp4 --every 2 --vertical
"""
import argparse, glob, json, os, random, subprocess, tempfile


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("music")
    p.add_argument("--clips", help="Carpeta con videos/fotos")
    p.add_argument("-o", "--output", default="montaje_ritmo.mp4")
    p.add_argument("--every", type=int, default=2, help="Cortar cada N golpes")
    p.add_argument("--max-seconds", type=float, default=30)
    p.add_argument("--vertical", action="store_true")
    p.add_argument("--shuffle", action="store_true")
    p.add_argument("--flash", action="store_true", help="Destello blanco en cada corte")
    a = p.parse_args()

    import librosa, numpy as np
    y, sr = librosa.load(a.music, sr=22050, mono=True, duration=a.max_seconds + 5)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beats = librosa.frames_to_time(frames, sr=sr).tolist()
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    strength = [float(onset_env[min(f, len(onset_env) - 1)]) for f in frames]
    out_json = os.path.splitext(a.music)[0] + ".beats.json"
    with open(out_json, "w") as f:
        json.dump({"bpm": float(np.atleast_1d(tempo)[0]), "beats": beats, "strength": strength}, f)
    print(f"BPM: {float(np.atleast_1d(tempo)[0]):.1f}  golpes: {len(beats)}  -> {out_json}")
    if not a.clips: return

    files = sorted(sum([glob.glob(os.path.join(a.clips, e)) for e in ("*.mp4", "*.mov", "*.MOV", "*.MP4", "*.jpg", "*.jpeg", "*.png", "*.webm")], []))
    if not files: raise SystemExit("No hay clips en " + a.clips)
    if a.shuffle: random.shuffle(files)
    cuts = [0.0] + [b for b in beats[a.every::a.every] if b <= a.max_seconds]
    W, H = (1080, 1920) if a.vertical else (1920, 1080)
    tmp = tempfile.mkdtemp()
    parts = []
    for i in range(len(cuts) - 1):
        d = cuts[i + 1] - cuts[i]
        src = files[i % len(files)]
        outp = os.path.join(tmp, f"{i:04d}.mp4")
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1"
        if a.flash: vf += ",fade=t=in:st=0:d=0.12:color=white"
        if src.lower().endswith((".jpg", ".jpeg", ".png")):
            vf = f"scale={W*1.2:.0f}:{H*1.2:.0f}:force_original_aspect_ratio=increase,zoompan=z='1+0.002*on':d={int(d*30)+1}:s={W}x{H}:fps=30,setsar=1" + (",fade=t=in:st=0:d=0.12:color=white" if a.flash else "")
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", src, "-t", f"{d:.3f}", "-vf", vf]
        else:
            start = random.uniform(0, 1.0)
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", src, "-t", f"{d:.3f}", "-vf", vf, "-an"]
        subprocess.run(cmd + ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", outp], check=True)
        parts.append(outp)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{x}'\n" for x in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", a.music, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", a.output], check=True)
    print(f"OK -> {a.output}  ({len(parts)} cortes)")


if __name__ == "__main__":
    main()
