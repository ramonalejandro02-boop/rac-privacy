#!/usr/bin/env python3
"""Inserta TOMAS DE APOYO (B-roll) sobre el video principal.

El audio del video principal se mantiene siempre; las tomas de apoyo tapan la
imagen durante unos segundos (con fundido suave y zoom lento opcional).

Uso:
  # Automático: reparte las tomas a lo largo del video
  python broll.py principal.mp4 salida.mp4 --clips apoyo1.mp4 apoyo2.mp4 foto.jpg

  # Manual: en qué segundo entra cada toma y cuánto dura
  python broll.py principal.mp4 salida.mp4 --clips a.mp4 b.mp4 --at 4.5 12 --dur 3 2.5

  # Mantener a la persona en una esquina (picture-in-picture) mientras sale la toma
  python broll.py principal.mp4 salida.mp4 --clips a.mp4 --pip

Opciones: --skip-start 2 (no tapar los primeros segundos), --fade 0.25, --no-zoom,
          --ss 1.0 (segundo desde el que se toma cada clip de apoyo).
"""
import argparse
import json
import subprocess


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_type",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    return float(d["format"].get("duration", 0) or 0), v.get("width"), v.get("height")


def is_image(p):
    return p.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".heic"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("main")
    p.add_argument("output")
    p.add_argument("--clips", nargs="+", required=True)
    p.add_argument("--at", nargs="*", type=float, help="Segundos de entrada de cada toma")
    p.add_argument("--dur", nargs="*", type=float, help="Duración de cada toma (una o una por toma)")
    p.add_argument("--skip-start", type=float, default=2.0)
    p.add_argument("--skip-end", type=float, default=1.5)
    p.add_argument("--fade", type=float, default=0.25)
    p.add_argument("--ss", type=float, default=0.5)
    p.add_argument("--no-zoom", action="store_true")
    p.add_argument("--pip", action="store_true", help="Persona en recuadro en la esquina durante la toma")
    p.add_argument("--crf", type=int, default=17)
    a = p.parse_args()

    total, W, H = probe(a.main)
    n = len(a.clips)
    durs = a.dur or [3.0]
    durs = (durs * n)[:n] if len(durs) == 1 else durs
    if len(durs) != n:
        raise SystemExit("--dur debe tener 1 valor o uno por toma")
    if a.at:
        if len(a.at) != n:
            raise SystemExit("--at debe tener un valor por toma")
        starts = a.at
    else:  # reparto uniforme
        usable = total - a.skip_start - a.skip_end
        slot = usable / n
        durs = [max(1.0, min(d, slot * 0.8)) for d in durs]  # sin solapes
        starts = [a.skip_start + slot * i + max(0, (slot - durs[i]) / 2) for i in range(n)]

    inputs = ["-i", a.main]
    for c in a.clips:
        if is_image(c):
            inputs += ["-loop", "1", "-t", "30", "-i", c]
        else:
            inputs += ["-ss", str(a.ss), "-i", c]

    fc, last = [], "[0:v]"
    fc.append(f"[0:v]setpts=PTS-STARTPTS,format=yuv420p[base0]")
    last = "[base0]"
    for i, (st, d) in enumerate(zip(starts, durs), start=1):
        d = min(d, max(0.5, total - st))
        frames = int(d * 30) + 1
        zoom = "" if a.no_zoom else f",scale={W*2}:{H*2},zoompan=z='1+0.06*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30"
        fc.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30{zoom},"
            f"trim=duration={d:.3f},setpts=PTS-STARTPTS+{st:.3f}/TB,format=yuva420p,"
            f"fade=t=in:st={st:.3f}:d={a.fade}:alpha=1,fade=t=out:st={st + d - a.fade:.3f}:d={a.fade}:alpha=1[b{i}]")
        fc.append(f"{last}[b{i}]overlay=eof_action=pass:enable='between(t,{st:.3f},{st + d:.3f})'[base{i}]")
        last = f"[base{i}]"
        if a.pip:  # recuadro con la persona encima de la toma
            pw = int(W * 0.32) // 2 * 2
            fc.append(f"[0:v]scale={pw}:-2,pad=iw+12:ih+12:6:6:white[pip{i}]")
            fc.append(f"{last}[pip{i}]overlay=W-w-40:H-h-40:enable='between(t,{st:.3f},{st + d:.3f})'[basep{i}]")
            last = f"[basep{i}]"
        print(f"Toma {i}: {a.clips[i-1]}  {st:.2f}s -> {st + d:.2f}s")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats", *inputs, "-filter_complex", ";".join(fc),
           "-map", last, "-map", "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-t", f"{total:.3f}", a.output]
    subprocess.run(cmd, check=True)
    print("OK ->", a.output)


if __name__ == "__main__":
    main()
