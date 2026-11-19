#!/usr/bin/env python3
"""
Montaje con escenas animadas intercaladas.

Estructura:
  original (≈5 s, con emojis y efectos)  ->  se congela (disco rayado)
  -> ESCENA ANIMADA propia: la persona recortada como sticker, fondo animado,
     emojis actuando el chiste, texto grande y VOZ EN OFF
  -> vuelve el original -> otra escena -> ...

Uso:
  python3 studio/montaje.py entrada.mp4 salida.mp4 --plan studio/planes/montaje_picaro.json \
      [--palabras palabras.json]

Formato del plan: ver studio/planes/montaje_picaro.json
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import wave

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from transformar import ESTILOS, MODELOS, FondoAnimado, log  # noqa: E402
from efectos import (H, SR, W, Eventos, Subs, a_bgra, ease_back, ease_io,  # noqa: E402
                     sintetizar, sticker_pil, superponer, texto_pil)

VOZ = os.environ.get("STUDIO_VOZ", os.path.join(MODELOS, "piper", "es_MX-claude-high.onnx"))
FPS = 30


# --------------------------------------------------------------------------
# Voz en off
# --------------------------------------------------------------------------
MOTOR_TTS = os.environ.get("STUDIO_TTS", "kokoro")        # kokoro (natural) | piper
VOZ_KOKORO = os.environ.get("STUDIO_VOZ_KOKORO", "ef_dora")  # ef_dora = mujer, em_alex = hombre
_kokoro = None


VENV_VOZ = os.environ.get("STUDIO_VENV_VOZ", "/home/user/venv-voz/bin/python")
_clon = {}   # texto -> wav pre-generado con la voz clonada


def preparar_clon(textos, ref, tmp):
    """Genera de una vez todas las frases con la voz clonada (carga el modelo una sola vez)."""
    tj = os.path.join(tmp, "textos.json")
    json.dump(textos, open(tj, "w"), ensure_ascii=False)
    carpeta = os.path.join(tmp, "clon")
    log(f"clonando voz para {len(textos)} frases (≈30 s cada una)...")
    subprocess.run([VENV_VOZ, os.path.join(AQUI, "clonar_voz.py"), "--ref", ref, "--textos", tj,
                    "--salida", carpeta], check=True)
    for i, t in enumerate(textos):
        _clon[t] = os.path.join(carpeta, f"vo_{i:03d}.wav")


def voz_en_off(texto, salida, velocidad=0.9):
    global _kokoro
    crudo = salida + ".raw.wav"
    if texto in _clon:
        crudo = _clon[texto]
    elif MOTOR_TTS == "kokoro":
        from kokoro_onnx import Kokoro
        import soundfile as sf
        if _kokoro is None:
            kd = os.path.join(MODELOS, "kokoro")
            _kokoro = Kokoro(os.path.join(kd, "kokoro-v1.0.onnx"), os.path.join(kd, "voices-es.bin"))
        audio, sr = _kokoro.create(texto, voice=VOZ_KOKORO, speed=1.0 / velocidad * 0.9, lang="es-419")
        sf.write(crudo, audio, sr)
    else:
        subprocess.run([sys.executable, "-m", "piper", "-m", VOZ, "-f", crudo,
                        "--length-scale", str(velocidad)], input=texto.encode(), check=True,
                       stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", crudo, "-ar", str(SR), "-ac", "1",
                    "-af", "highpass=f=80,acompressor=threshold=-18dB:ratio=3,volume=1.6", salida], check=True)
    with wave.open(salida) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x


def palabras_vo(texto, x, t0):
    """Reparte las palabras del texto sobre la parte con voz (por largo de palabra)."""
    env = np.convolve(np.abs(x), np.ones(800) / 800, "same")
    on = np.where(env > env.max() * 0.08)[0]
    a, b = (on[0] / SR, on[-1] / SR) if len(on) else (0, len(x) / SR)
    pal = texto.split()
    pesos = np.array([len(p) + 2 for p in pal], np.float32)
    cs = np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum()
    return [dict(t=p, a=t0 + a + (b - a) * cs[i], b=t0 + a + (b - a) * cs[i + 1]) for i, p in enumerate(pal)]


# --------------------------------------------------------------------------
# Recorte de persona como sticker (borde blanco + sombra)
# --------------------------------------------------------------------------
_seg = None


def recorte_sticker(src, t, caja, alto_obj=1000, ancho_max=980):
    global _seg
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    cap = cv2.VideoCapture(src)
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read()
    cap.release()
    h, w = fr.shape[:2]
    x0, y0, x1, y1 = [int(v) for v in (caja[0] * w, caja[1] * h, caja[2] * w, caja[3] * h)]
    crop = fr[y0:y1, x0:x1]
    esc = min(alto_obj / crop.shape[0], ancho_max / crop.shape[1])
    crop = cv2.resize(crop, None, fx=esc, fy=esc, interpolation=cv2.INTER_CUBIC)
    crop = cv2.detailEnhance(crop, sigma_s=6, sigma_r=0.12)
    if _seg is None:
        _seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpt.BaseOptions(model_asset_path=os.path.join(MODELOS, "selfie_multiclass.tflite")),
            running_mode=vision.RunningMode.IMAGE, output_confidence_masks=True))
    r = _seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,
                              data=np.ascontiguousarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))))
    m = 1 - r.confidence_masks[0].numpy_view().astype(np.float32)
    m = m[..., 0] if m.ndim == 3 else m
    m = cv2.resize(m, (crop.shape[1], crop.shape[0]))
    m = cv2.GaussianBlur(m, (0, 0), 3)
    m = (m > 0.5).astype(np.uint8)
    # quedarse con la mancha más grande (la persona principal)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = (lab == k).astype(np.uint8)
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)
    pad = 40
    ch, cw = crop.shape[:2]
    big = np.zeros((ch + pad * 2, cw + pad * 2, 4), np.float32)
    big[pad:pad + ch, pad:pad + cw, :3] = crop
    alpha = np.zeros(big.shape[:2], np.float32)
    alpha[pad:pad + ch, pad:pad + cw] = m
    borde = cv2.dilate((alpha > 0.4).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27)))
    borde = cv2.GaussianBlur(borde.astype(np.float32), (0, 0), 1.5)
    sombra = cv2.GaussianBlur(borde, (0, 0), 10)
    sombra = np.roll(np.roll(sombra, 14, 0), 10, 1) * 0.55
    rgb = big[..., :3] * alpha[..., None] + 255 * (1 - alpha[..., None])        # blanco fuera = borde
    a_tot = np.maximum(borde, sombra)
    rgb = np.where((borde > 0.01)[..., None], rgb, 0)                            # sombra negra
    out = np.dstack([rgb, a_tot * 255]).clip(0, 255).astype(np.uint8)
    return out


# --------------------------------------------------------------------------
# Props animados de las escenas
# --------------------------------------------------------------------------
def ease_bounce(x):
    x = min(max(x, 0), 1)
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def dibujar_prop(cv, p, u, d, cache):
    u = u - p.get("t", 0)
    if u < 0:
        return
    px = p.get("size", 220)
    key = (p["emoji"], px)
    if key not in cache:
        cache[key] = a_bgra(texto_pil(p["emoji"], px, stroke=None, sw=0))
    im = cache[key]
    tx, ty = p.get("x", 0.5) * W, p.get("y", 0.5) * H
    anim = p.get("anim", "pulso")
    sal = max(0.0, 1 - (d - p.get("t", 0) - u) / 0.15)
    sc, rot, x, y = 1.0, 0.0, tx, ty
    if anim == "rebote":
        y = -200 + (ty + 200) * ease_bounce(u / 0.7)
        rot = 6 * math.sin(u * 5)
    elif anim == "desliza":
        desde = -0.35 * W if p.get("desde", "izq") == "izq" else 1.35 * W
        x = desde + (tx - desde) * ease_back(u / 0.45)
        rot = 10 * math.sin(u * 7)
    elif anim == "orbita":
        a = p.get("fase", 0) + u * p.get("vel", 2.4)
        r = p.get("radio", 380)
        x = tx + r * math.cos(a)
        y = ty + r * 0.4 * math.sin(a)
        sc = 0.75 + 0.3 * (math.sin(a) + 1) / 2
    elif anim == "crece":
        sc = ease_back(u / 0.4) * (1 + 0.05 * math.sin(u * 9))
        rot = 5 * math.sin(u * 4)
    elif anim == "cruza":
        dd = p.get("dur_cruce", 2.2)
        x = -0.3 * W + 1.6 * W * min(u / dd, 1)
        y = ty + 18 * math.sin(u * 10)
    else:  # pulso
        sc = ease_back(u / 0.3) * (1 + 0.08 * math.sin(u * 8))
        rot = 8 * math.sin(u * 3)
    superponer(cv, im, x, y, sc * (1 - sal), rot)


# --------------------------------------------------------------------------
# Render de una escena
# --------------------------------------------------------------------------
def render_escena(src, esc, salida, tmp, idx, claves, subs_x=0.5, subs_ancho=0.92):
    vo_wav = os.path.join(tmp, f"vo{idx}.wav")
    vo = voz_en_off(esc["voz"], vo_wav, esc.get("velocidad", 0.82))
    t_vo = 0.3
    d = max(esc.get("min", 2.5), t_vo + len(vo) / SR + 0.35)
    n = int(d * FPS)
    est = ESTILOS[esc.get("estilo", "neon")]
    fondo = FondoAnimado(W, H, est, seed=idx)
    corte = recorte_sticker(src, esc["congelar"], esc["caja"], esc.get("alto", 1000))
    texto = a_bgra(sticker_pil(esc["texto"], esc.get("tam_texto", 86), esc.get("fondo", "#FFE600"),
                               esc.get("color", "#111111"), rot=esc.get("rot", -3), max_w=1000))
    subs = Subs(palabras_vo(esc["voz"], vo, t_vo), claves + esc.get("claves", []), est["palabra"], px=88,
                y=esc.get("subs_y", 0.885), x=esc.get("subs_x", subs_x), ancho=esc.get("subs_ancho", subs_ancho))
    evs = Eventos(esc.get("eventos", []), None)
    cache = {}
    # energía de la voz para animar el fondo
    hop = SR / FPS
    energia = np.array([np.sqrt(np.mean(vo[int(max(0, (i / FPS - t_vo)) * SR):int(max(0, (i / FPS - t_vo)) * SR + hop)] ** 2 + 1e-9))
                        for i in range(n)])
    energia = np.nan_to_num(energia)
    energia = np.clip(energia / (energia.max() + 1e-6), 0, 1)
    cx, cy = esc.get("x", 0.5) * W, esc.get("y", 0.56) * H

    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                            "-pix_fmt", "yuv420p", os.path.join(tmp, f"esc{idx}.mp4")], stdin=subprocess.PIPE)
    for i in range(n):
        u = i / FPS
        cv = fondo.frame(u, float(energia[i]))
        # persona: entra de golpe, respira, zoom lento, tiembla si se pide
        sc = (1.25 - 0.25 * ease_back(u / 0.3)) * (1 + 0.06 * u / d) * (1 + 0.015 * math.sin(u * 4))
        rot = esc.get("rot_persona", 0) + 2.0 * math.sin(u * 2.2)
        dx = dy = 0
        if esc.get("temblor"):
            dx, dy = 9 * math.sin(u * 60), 7 * math.cos(u * 47)
        superponer(cv, corte, cx + dx, cy + dy, sc, rot)
        for p in esc.get("props", []):
            dibujar_prop(cv, p, u, d, cache)
        evs.dibujar(cv, u)
        superponer(cv, texto, W / 2, esc.get("texto_y", 0.15) * H, ease_back((u - 0.1) / 0.3) * (1 + 0.02 * math.sin(u * 5)))
        subs.dibujar(cv, u)
        fa = max(0.9 * (1 - u / 0.18), 0.8 * (1 - (d - u) / 0.12), 0)
        if fa > 0:
            cv = cv2.addWeighted(cv, 1 - fa, np.full_like(cv, 255), fa, 0)
        enc.stdin.write(cv.tobytes())
    enc.stdin.close()
    enc.wait()

    # audio: disco rayado + voz + sonidos de props + whoosh de salida
    pista = np.zeros(int((d + 1) * SR), np.float32)

    def mezclar(y, t, vol=1.0):
        a = int(t * SR)
        b = min(len(pista), a + len(y))
        pista[a:b] += y[:b - a] * vol
    mezclar(sintetizar("scratch"), 0, 0.55)
    mezclar(vo, t_vo, 1.0)
    for p in esc.get("props", []) + esc.get("eventos", []):
        if p.get("sfx"):
            mezclar(sintetizar(p["sfx"]), p.get("t", 0), 0.4 * p.get("vol", 1.0))
    mezclar(sintetizar("whoosh"), d - 0.4, 0.35)
    pista = np.clip(pista[:int(d * SR)], -1, 1)
    aw = os.path.join(tmp, f"esc{idx}.wav")
    with wave.open(aw, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((pista * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(tmp, f"esc{idx}.mp4"), "-i", aw,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", "-shortest", salida],
                   check=True)
    log(f"  escena {idx}: {d:.1f}s  «{esc['voz']}»")
    return d


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--palabras")
    ap.add_argument("--base", help="video base ya renderizado con efectos.py (para no repetir)")
    ap.add_argument("--mi-voz", help="audio con TU voz (15-30 s): las voces en off salen con tu voz clonada")
    ap.add_argument("--presentador", help="video tuyo (fondo negro o normal) para salir en pantalla")
    ap.add_argument("--presentador-espejo", action="store_true", help="voltear el video del presentador")
    args = ap.parse_args()
    plan = json.load(open(args.plan))
    tmp = tempfile.mkdtemp(prefix="montaje_")
    if args.mi_voz:
        ref = os.path.join(tmp, "ref.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", args.mi_voz, "-t", "30", "-ac", "1", "-ar", "24000",
                        "-af", "highpass=f=70,afftdn=nf=-25,loudnorm=I=-18", ref], check=True)
        preparar_clon([s["voz"] for s in plan["secuencia"] if "voz" in s], ref, tmp)

    base = args.base
    if not base:
        base = os.path.join(tmp, "base.mp4")
        plan_base = os.path.join(tmp, "plan_base.json")
        json.dump(plan["base"], open(plan_base, "w"), ensure_ascii=False)
        cmd = [sys.executable, os.path.join(AQUI, "efectos.py"), args.entrada, base, "--plan", plan_base, "--sin-barra"]
        if args.palabras:
            cmd += ["--palabras", args.palabras]
        log("renderizando partes originales con efectos...")
        subprocess.run(cmd, check=True)

    claves = plan["base"].get("claves", [])
    sx = plan["base"].get("subs_x", 0.5) if args.presentador else 0.5
    sa = plan["base"].get("subs_ancho", 0.92) if args.presentador else 0.92
    partes, total, tramos = [], 0.0, []
    for k, seg in enumerate(plan["secuencia"]):
        out = os.path.join(tmp, f"parte{k:02d}.mp4")
        if "orig" in seg:
            a, b = seg["orig"]
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-i", base, "-t", str(b - a),
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
                            "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", out], check=True)
            tramos.append(dict(a=total, b=total + (b - a), modo="esquina", habla=False))
            total += b - a
        else:
            d = render_escena(args.entrada, seg, out, tmp, k, claves, sx, sa)
            modo = seg.get("presentador", "esquina")
            tramos.append(dict(a=total, b=total + 0.3, modo=modo, habla=False))
            tramos.append(dict(a=total + 0.3, b=total + d, modo=modo, habla=True))
            total += d
        partes.append(out)
    for j, tr in enumerate(tramos):
        tr["anima"] = j == 0 or tramos[j - 1]["modo"] != tr["modo"]

    # unir todo + barra de progreso global + volumen final
    ins = []
    for p in partes:
        ins += ["-i", p]
    cadena = "".join(f"[{i}:v][{i}:a]" for i in range(len(partes)))
    col = "0x{:02X}{:02X}{:02X}".format(*ESTILOS[plan["base"].get("estilo", "farandula")]["palabra"][::-1])
    if args.presentador:
        unido = os.path.join(tmp, "unido.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex",
                        f"{cadena}concat=n={len(partes)}:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "aac", "-b:a", "256k", unido],
                       check=True)
        from presentador import Presentador, aplicar
        log("poniendo al presentador en pantalla...")
        pres = Presentador(args.presentador, espejo=args.presentador_espejo)
        con_pres = os.path.join(tmp, "con_presentador.mp4")
        aplicar(unido, con_pres, pres, tramos, FPS)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", con_pres, "-i", unido, "-map", "0:v", "-map", "1:a",
                        "-c", "copy", os.path.join(tmp, "unido2.mp4")], check=True)
        ins, cadena = ["-i", os.path.join(tmp, "unido2.mp4")], "[0:v][0:a]"
        partes = [None]
    fc = (f"{cadena}concat=n={len(partes)}:v=1:a=1[v][a];"
          f"color=c={col}:s={W}x14:r={FPS}[bar];"
          f"[v][bar]overlay=x='-W+W*t/{total:.3f}':y=H-14:shortest=1[vo];"
          f"[a]loudnorm=I=-14:TP=-1.5,aresample={SR}[ao]")
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.salida], check=True)
    log(f"listo -> {args.salida} ({total:.1f}s)")


if __name__ == "__main__":
    main()
