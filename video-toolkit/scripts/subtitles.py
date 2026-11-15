#!/usr/bin/env python3
"""Subtítulos automáticos con Whisper (tiempo por palabra).

Genera:
  - .srt                     subtítulos normales (YouTube, CapCut, Premiere)
  - .ass                     subtítulos animados estilo Reels (palabra resaltada) para quemar con FFmpeg
  - captions.json            para Remotion (composición WordCaptions)
Y opcionalmente quema los subtítulos en el video (--burn).

Uso:
  python subtitles.py video.mp4 --lang es --burn
  python subtitles.py video.mp4 --model medium --words-per-line 3 --color "#FFD60A"
Modelos: tiny | base | small (por defecto) | medium | large-v3   (más grande = más preciso, más lento)
Requiere acceso a huggingface.co la primera vez para descargar el modelo.
"""
import argparse, json, os, subprocess


def ts_srt(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h:02d}:{m:02d}:{t % 60:06.3f}".replace(".", ",")


def ts_ass(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass_color(hexc):
    h = hexc.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("--lang", default=None, help="es, en... (vacío = detectar)")
    p.add_argument("--model", default="small")
    p.add_argument("--words-per-line", type=int, default=3)
    p.add_argument("--font", default="Montserrat")
    p.add_argument("--size", type=int, default=0, help="Tamaño de letra (0 = automático)")
    p.add_argument("--color", default="#FFD60A", help="Color de la palabra activa")
    p.add_argument("--upper", action="store_true", default=True)
    p.add_argument("--burn", action="store_true", help="Quemar subtítulos en el video")
    a = p.parse_args()

    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, info = model.transcribe(a.input, language=a.lang, word_timestamps=True, vad_filter=True)
    words = [w for s in segs for w in (s.words or [])]
    print(f"Idioma: {info.language}  palabras: {len(words)}")

    base = os.path.splitext(a.input)[0]
    clean = lambda w: w.word.strip()

    # JSON para Remotion
    with open(base + ".captions.json", "w", encoding="utf-8") as f:
        json.dump([{"text": clean(w), "startMs": int(w.start * 1000), "endMs": int(w.end * 1000)} for w in words], f, ensure_ascii=False)

    groups = [words[i:i + a.words_per_line] for i in range(0, len(words), a.words_per_line)]

    # SRT
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for i, g in enumerate(groups, 1):
            f.write(f"{i}\n{ts_srt(g[0].start)} --> {ts_srt(g[-1].end)}\n{' '.join(clean(w) for w in g)}\n\n")

    # ASS animado (palabra activa resaltada y con "pop")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", a.input], capture_output=True, text=True).stdout.strip()
    W, H = (int(x) for x in probe.split(",")[:2]) if probe else (1080, 1920)
    size = a.size or int(min(W, H) * 0.085)
    hl = ass_color(a.color)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Pop,{a.font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{max(3, size // 14)},{max(2, size // 25)},2,60,60,{int(H * 0.2)},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for g in groups:
        for j, w in enumerate(g):
            end = g[j + 1].start if j + 1 < len(g) else w.end
            parts = []
            for k, x in enumerate(g):
                t = clean(x).upper() if a.upper else clean(x)
                parts.append(r"{\c" + hl + r"\fscx85\fscy85\t(0,90,\fscx112\fscy112)\t(90,160,\fscx100\fscy100)}" + t + r"{\r}" if k == j else t)
            lines.append(f"Dialogue: 0,{ts_ass(w.start)},{ts_ass(end)},Pop,,0,0,0,,{' '.join(parts)}")
    with open(base + ".ass", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("OK ->", base + ".srt", base + ".ass", base + ".captions.json")

    if a.burn:
        fonts = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
        out = base + ".subtitulado.mp4"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.input,
                        "-vf", f"ass={base}.ass:fontsdir={fonts}", "-c:v", "libx264", "-crf", "17", "-c:a", "copy", out], check=True)
        print("OK ->", out)


if __name__ == "__main__":
    main()
