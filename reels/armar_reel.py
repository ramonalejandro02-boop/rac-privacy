"""Arma un reel a partir de TU VOZ + clips o imágenes de cada escena.

Uso:   python3 armar_reel.py noe
Busca en la carpeta  reels/noe/ :
   voz.(m4a|mp3|wav|ogg|opus|aac)    -> tu voz en off con pausas entre escenas
   escena1.(mp4|mov|jpg|jpeg|png|webp) ... escenaN   -> un clip o imagen por escena
   musica.(mp3|m4a|wav)  (opcional)  -> música de fondo, se pone bajita
Salida: reels/noe/reel_final.mp4

Hace: corta tu voz por las pausas, ajusta cada escena a la duración de lo que dices,
subtítulos palabra por palabra sincronizados, palabras clave en amarillo,
zoom suave, destellos y whoosh en los cortes, trueno/golpes, barra de progreso y marca.
"""
import glob, json, math, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 44100
HERE = os.path.dirname(os.path.abspath(__file__))
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
YELLOW, WHITE = (255, 212, 0), (255, 255, 255)
BRAND = "@Alejandro Curiosidades"
GOLD = (242, 193, 78)
ESTILO = os.environ.get("ESTILO", "cine")  # "cine" (elegante, adultos) o "viral" (recuadros amarillos)

GUIONES = {
    "noe": [
        dict(dur=5, texto="Este hombre construyó un barco *GIGANTE*… sin que hubiera una sola nube en el cielo."),
        dict(dur=5, texto="Seguramente le dijeron *LOCO*. Se reían de él."),
        dict(dur=6, texto="Pero Noé no construía por lo que veía… sino por lo que *DIOS* le había dicho."),
        dict(dur=5, texto="Y un día… el cielo se oscureció. Y comenzó a *LLOVER*.", sfx="trueno"),
        dict(dur=9, texto="Hebreos 11:7: Por la fe Noé, cuando fue advertido por Dios acerca de cosas que *AÚN* *NO* *SE* *VEÍAN*… preparó el arca."),
        dict(dur=8, texto="Lo que Dios te prometió, aunque hoy no lo veas… va a *LLEGAR*. Escribe *LO* *CREO* si estás construyendo tu arca."),
    ],
}

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)

def find(folder, base, exts):
    for e in exts:
        hits = glob.glob(os.path.join(folder, f"{base}.{e}")) + glob.glob(os.path.join(folder, f"{base}.{e.upper()}"))
        if hits: return hits[0]
    return None

def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout.strip())

# ------------------------------------------------------------ voz ----------
def load_voice(path, clean=False):
    af = ["-af", "highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-15:TP=-1.5"] if clean else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, *af, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768

def detect_silences(path, noise_db):
    err = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=noise={noise_db}dB:d=0.45", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))

def split_voice(path, texts):
    """Devuelve [(inicio_escena, fin_escena, inicio_habla, fin_habla)] por escena."""
    total = duration(path); n = len(texts)
    sil = []
    for db in (-38, -34, -30, -26):
        sil = detect_silences(path, db)
        inner = [s for s in sil if s[0] > 0.3 and s[1] < total - 0.3]
        if len(inner) >= n - 1: break
    lead = next((e for s, e in sil if s <= 0.05), 0.0)
    tail = next((s for s, e in sil if e >= total - 0.05), total)
    inner = [s for s in sil if s[0] > 0.3 and s[1] < total - 0.3]
    if len(inner) >= n - 1:
        # las N-1 pausas más largas son los cortes entre escenas
        cuts = sorted(sorted(inner, key=lambda s: s[1] - s[0], reverse=True)[:n - 1])
    else:
        print("  Aviso: no encontré suficientes pausas; reparto por longitud del texto.")
        lens = np.array([len(t) for t in texts], float); acc = np.cumsum(lens) / lens.sum()
        span = tail - lead
        # ajusta cada corte a la respiración (punto de menor energía) más cercana
        x = load_voice(path); hop = int(0.02 * SR)
        env = np.sqrt(np.convolve(x ** 2, np.ones(hop * 15) / (hop * 15), "same")[::hop])
        cuts = []
        for a_ in acc[:-1]:
            c = lead + span * a_; i0, i1 = int((c - 1.6) / 0.02), int((c + 1.6) / 0.02)
            i0, i1 = max(i0, 1), min(i1, len(env) - 1); k = i0 + int(np.argmin(env[i0:i1])); tc = k * 0.02
            cuts.append((tc - 0.05, tc + 0.05))
    segs = []; prev_end = 0.0; speech_start = lead
    for i in range(n):
        if i < n - 1:
            c0, c1 = cuts[i]; mid = (c0 + c1) / 2
            segs.append((prev_end, mid, speech_start, c0)); prev_end = mid; speech_start = c1
        else:
            segs.append((prev_end, total + 0.6, speech_start, tail))
    return segs, total + 0.6

# ------------------------------------------------------------ escenas ------
def scene_frames(src, dur, idx):
    """Genera los cuadros de la escena (cubre 9:16, zoom suave) vía ffmpeg."""
    n = int(round(dur * FPS))
    is_img = src.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    if is_img:
        zin = idx % 2 == 0
        z = f"1+0.12*on/{n}" if zin else f"1.12-0.12*on/{n}"
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}")
        cmd = ["ffmpeg", "-v", "error", "-loop", "1", "-i", src, "-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    else:
        vf = (f"fps={FPS},scale={int(W*1.06)}:{int(H*1.06)}:force_original_aspect_ratio=increase,"
              f"crop={int(W*1.06)}:{int(H*1.06)},scale={W}:{H}")
        cd = duration(src)
        if dur > cd: vf = f"setpts={dur / cd:.4f}*PTS," + vf  # estira el clip en vez de repetirlo
        cmd = ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", src, "-an", "-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H * 3; last = None
    for _ in range(n):
        buf = p.stdout.read(size)
        if len(buf) == size: last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        yield last if last is not None else np.zeros((H, W, 3), np.uint8)
    p.stdout.close(); p.wait()

# ------------------------------------------------------------ subtítulos ---
_fc = {}
def font(size):
    if size not in _fc: _fc[size] = ImageFont.truetype(F_BLACK, size)
    return _fc[size]

def words_with_times(text, s0, s1):
    toks = text.replace("…", "… ").split()
    words = [(re.sub(r"[*]", "", t), t.startswith("*")) for t in toks]
    weights = np.array([len(w) + 2 + (6 if w.endswith(("…", ".", ",", ":")) else 0) for w, _ in words], float)
    edges = s0 + (s1 - s0) * np.concatenate([[0], np.cumsum(weights) / weights.sum()])
    return [dict(w=w, kw=k, t0=edges[i], t1=edges[i + 1]) for i, (w, k) in enumerate(words)]

def chunks(words, maxw=3, maxchars=18):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or sum(len(x["w"]) for x in cur) + len(w["w"]) > maxchars):
            out.append(cur); cur = []
        cur.append(w)
        if w["w"].endswith(("…", ".", ":", ",")): out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def draw_caption(img, chunk, t):
    size = 92; f = font(size); sp = 26
    ws = [f.getlength(w["w"]) + (40 if w["kw"] and ESTILO == "viral" else 0) for w in chunk]
    total = sum(ws) + sp * (len(chunk) - 1)
    scale = min(1, 980 / total); f2 = font(int(size * scale)) if scale < 1 else f
    ws = [x * scale for x in ws]; total = min(total, 980)
    x = (W - total) / 2; y = int(H * 0.70)
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for w, ww in zip(chunk, ws):
        if t < w["t0"] - 0.02:
            x += ww + sp; continue
        active = w["t0"] <= t < w["t1"]
        pop = min(1, (t - w["t0"]) / 0.12)
        dy = int((1 - pop) * 18)
        if w["kw"] and ESTILO == "cine":
            d.text((x, 66 + dy), w["w"], font=f2, fill=GOLD + (255,), stroke_width=5, stroke_fill=(20, 10, 0, 255))
        elif w["kw"]:
            d.rounded_rectangle([x, 60 + dy, x + ww, 60 + dy + f2.size * 1.22], radius=18, fill=YELLOW + (255,))
            d.text((x + 20 * scale, 66 + dy), w["w"], font=f2, fill=(0, 0, 0, 255))
        else:
            d.text((x, 66 + dy), w["w"], font=f2, fill=((255, 232, 190) if ESTILO == "cine" and active else YELLOW if active else WHITE) + (255,),
                   stroke_width=6, stroke_fill=(0, 0, 0, 255))
        x += ww + sp
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.6))
    shadow = Image.new("RGBA", lay.size, (0, 0, 0, 0)); shadow.putalpha(sh)
    img.alpha_composite(shadow, (4, y - 120)); img.alpha_composite(lay, (0, y - 130))

# ------------------------------------------------------------ audio --------
def build_audio(voice, total, segs, guion, music_path, kw_times):
    n = int(total * SR); out = np.zeros(n); rng = np.random.default_rng(3)
    out[:min(n, len(voice))] += voice[:n] * 1.0
    def add(sig, at, g):
        i = max(0, int(at * SR)); j = min(n, i + len(sig)); out[i:j] += sig[:j - i] * g
    def bandnoise(d, lo, hi):
        m = int(d * SR); X = np.fft.rfft(rng.normal(0, 1, m)); fr = np.fft.rfftfreq(m, 1 / SR)
        X[(fr < lo) | (fr > hi)] = 0; y = np.fft.irfft(X, m); return y / (np.abs(y).max() + 1e-9)
    for i, (a, b, s0, s1) in enumerate(segs):
        if i > 0:
            t_ = np.arange(int(0.35 * SR)) / SR
            add(bandnoise(0.35, 300, 4000) * np.sin(np.pi * t_ / 0.35) ** 2, a - 0.18, 0.18)
        if guion[i].get("sfx") == "trueno":
            t_ = np.arange(int(2.5 * SR)) / SR
            add(bandnoise(2.5, 30, 400) * np.exp(-t_ * 1.5), a + 2.3, 0.5); add(bandnoise(0.2, 2000, 12000) * np.exp(-t_[:int(0.2 * SR)] * 25), a + 2.3, 0.3)
    for kt in kw_times:
        t_ = np.arange(int(0.9 * SR)) / SR
        add(np.sin(2 * np.pi * np.cumsum(40 + 100 * np.exp(-t_ * 9)) / SR) * np.exp(-t_ * 4), kt, 0.22)
    if music_path == "PAD":
        # música suave generada: acordes cálidos tipo piano/pad (I–V–vi–IV en Do)
        prog = [[110.0, 130.81, 164.81, 220.0], [87.31, 130.81, 174.61, 220.0], [130.81, 164.81, 196.0, 261.63], [98.0, 146.83, 196.0, 246.94]]  # Am–F–C–G, más cinematográfico
        bar = 3.2; k = 0; t0 = 0.0
        while t0 < total:
            m = int((bar + 1.5) * SR); t_ = np.arange(m) / SR
            env = np.minimum(1, t_ / 0.04) * np.exp(-t_ * 0.9)
            sig = sum(np.sin(2 * np.pi * f * t_) + 0.3 * np.sin(4 * np.pi * f * t_) * np.exp(-t_ * 3) for f in prog[k % 4])
            pad = sum(np.sin(2 * np.pi * f * 1.003 * t_) for f in prog[k % 4]) * np.minimum(1, t_ / 0.8) * np.minimum(1, np.maximum(0, (bar + 1.5 - t_) / 1.0))
            add(sig * env * 0.035 + pad * 0.035, t0, 1.0); t0 += bar; k += 1
        fade = np.ones(n); fade[-2 * SR:] = np.linspace(1, 0, 2 * SR); out *= fade
    elif music_path:
        mus = load_voice(music_path)
        if len(mus) < n: mus = np.tile(mus, n // len(mus) + 1)
        mus = mus[:n]
        env = np.ones(n); env[:SR] = np.linspace(0, 1, SR); env[-2 * SR:] = np.linspace(1, 0, 2 * SR)
        out += mus * env * 0.13
    peak = np.abs(out).max()
    if peak > 0.98: out = out / peak * 0.98
    path = os.path.join(HERE, "_audio_armado.wav")
    with wave.open(path, "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    return path

# ------------------------------------------------------------ principal ----
def main(name):
    folder = os.path.join(HERE, name); guion = GUIONES[name]
    vpath = find(folder, "voz", ["m4a", "mp3", "wav", "ogg", "opus", "aac", "mp4", "mov"])
    srcs = [find(folder, f"escena{i+1}", ["mp4", "mov", "jpg", "jpeg", "png", "webp"]) for i in range(len(guion))]
    missing = [i + 1 for i, s in enumerate(srcs) if not s]
    if missing: sys.exit(f"Faltan escenas: {missing}")
    music = find(folder, "musica", ["mp3", "m4a", "wav"])
    if vpath:
        print("Analizando tu voz…")
        segs, total = split_voice(vpath, [g["texto"] for g in guion])
        voice = load_voice(vpath, clean=True)
        if not music: music = "PAD"
    else:
        print("Sin voz: uso duraciones por escena, texto en pantalla y música de fondo.")
        segs, a = [], 0.0
        for g in guion:
            d = g.get("dur") or max(3.5, len(g["texto"]) * 0.062)
            segs.append((a, a + d, a + 0.35, a + d - 0.5)); a += d
        total = a; voice = np.zeros(int(total * SR))
        if not music: music = "PAD"
    for i, s in enumerate(segs): print(f"  escena {i+1}: {s[0]:.2f}–{s[1]:.2f} s  (habla {s[2]:.2f}–{s[3]:.2f})")
    allwords = []
    for g, (a, b, s0, s1) in zip(guion, segs):
        ws = words_with_times(g["texto"], s0, s1); g["chunks"] = chunks(ws); allwords += ws
    kw_times = [w["t0"] for w in allwords if w["kw"]]
    apath = build_audio(voice, total, segs, guion, music, kw_times)
    out = os.path.join(folder, "reel_final.mp4" if vpath else "reel_sin_voz.mp4")
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-i", apath, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                             "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                             "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W]
    vign = (1 - 0.55 * np.clip(np.sqrt(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.8)) ** 2), 0, 1) ** 2.4)[:, :, None].astype(np.float32)
    fn = 0
    grain = [np.random.default_rng(i).normal(0, 7, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) for i in range(4)]
    for i, (g, src, (a, b, s0, s1)) in enumerate(zip(guion, srcs, segs)):
        print(f"Renderizando escena {i+1}…")
        dur = b - a
        for k, fr in enumerate(scene_frames(src, dur, i)):
            t = a + k / FPS
            arr = fr.astype(np.float32) * vign
            if ESTILO == "cine":
                arr = (arr - 128) * 1.08 + 128 + grain[k % len(grain)]
            lt = k / FPS
            if i > 0 and lt < 0.1: arr += (1 - lt / 0.1) * 200
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
            cur = next((c for c in g["chunks"] if c[0]["t0"] - 0.02 <= t < c[-1]["t1"] + 0.25), None)
            if cur: draw_caption(img, cur, t)
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, W, 14], fill=(0, 0, 0, 120)); d.rectangle([0, 0, int(W * t / total), 14], fill=(GOLD if ESTILO == "cine" else YELLOW) + (255,))
            d.text((W / 2, 150), BRAND, font=font(40), fill=(255, 255, 255, 190), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 140))
            out_img = img.convert("RGB")
            # pequeño golpe de zoom en palabras clave
            hit = max([0] + [1 - (t - kt) / 0.25 for kt in kw_times if 0 <= t - kt < 0.25])
            if hit > 0:
                zz = 1 + 0.03 * hit; cw, ch = W / zz, H / zz
                out_img = out_img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
            proc.stdin.write(out_img.tobytes()); fn += 1
    proc.stdin.close(); proc.wait(); os.remove(apath)
    print("Listo:", out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "noe")
