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
import efectos  # noqa: E402
from efectos import (H, SR, W, Eventos, Subs, a_bgra, ease_back, ease_io,  # noqa: E402
                     seguro, sintetizar, sticker_pil, superponer, texto_pil, usar_tema)

VOZ = os.environ.get("STUDIO_VOZ", os.path.join(MODELOS, "piper", "es_MX-claude-high.onnx"))
FPS = 30
SFX_TRANSICION = True


def sin_silencios_audio(a, b, audio, sr=16000, hueco=0.32, margen=0.08):
    """Quita pausas mirando la energía del audio (más preciso que los tiempos de palabras)."""
    seg = audio[int(a * sr):int(b * sr)]
    if len(seg) < sr * 0.5:
        return [(a, b)]
    hop = int(0.02 * sr)
    rms = np.array([np.sqrt(np.mean(seg[i:i + hop] ** 2)) for i in range(0, len(seg) - hop, hop)])
    rms = np.convolve(rms, np.ones(3) / 3, "same")
    umbral = max(np.percentile(rms, 90) * 0.12, 1e-4)
    callado = rms < umbral
    tramos, ini, k = [], a, 0
    n = len(callado)
    while k < n:
        if callado[k]:
            j = k
            while j < n and callado[j]:
                j += 1
            if (j - k) * 0.02 > hueco:
                t0, t1 = a + k * 0.02, a + j * 0.02
                if k == 0:
                    ini = max(a, t1 - margen)
                elif j == n:
                    tramos.append((ini, min(b, t0 + margen)))
                    ini = None
                else:
                    tramos.append((ini, t0 + margen))
                    ini = t1 - margen
            k = j
        else:
            k += 1
    if ini is not None:
        tramos.append((ini, b))
    return [(x, y) for x, y in tramos if y - x > 0.15]


def sin_silencios(a, b, palabras, hueco=0.35, margen=0.1):
    """Parte un tramo del original quitando las pausas largas entre palabras."""
    ws = [w for w in palabras if w["b"] > a and w["a"] < b]
    if not ws:
        return [(a, b)]
    tramos, ini = [], max(a, ws[0]["a"] - margen) if ws[0]["a"] - a > hueco else a
    for w0, w1 in zip(ws, ws[1:]):
        if w1["a"] - w0["b"] > hueco:
            tramos.append((ini, min(b, w0["b"] + margen)))
            ini = max(a, w1["a"] - margen)
    fin = b if b - ws[-1]["b"] <= hueco else min(b, ws[-1]["b"] + margen + 0.1)
    tramos.append((ini, fin))
    return [(x, y) for x, y in tramos if y - x > 0.15]


# --------------------------------------------------------------------------
# Voz en off
# --------------------------------------------------------------------------
MOTOR_TTS = os.environ.get("STUDIO_TTS", "kokoro")        # kokoro (natural) | piper
VOZ_KOKORO = os.environ.get("STUDIO_VOZ_KOKORO", "ef_dora")  # ef_dora = mujer, em_alex = hombre
_kokoro = None


def _venv_voz():
    if os.environ.get("STUDIO_VENV_VOZ"):
        return os.environ["STUDIO_VENV_VOZ"]
    for base in ("/home/user/venv-voz", os.path.join(os.path.expanduser("~"), ".estudio", "venv-voz")):
        for exe in ("bin/python", "Scripts/python.exe"):
            if os.path.exists(os.path.join(base, exe)):
                return os.path.join(base, exe)
    return os.path.join(os.path.expanduser("~"), ".estudio", "venv-voz", "bin", "python")


VENV_VOZ = _venv_voz()
_clon = {}   # texto -> wav pre-generado con la voz clonada


CACHE_VOZ = os.environ.get("STUDIO_CACHE_VOZ", os.path.join(MODELOS, "cache_voz"))


def _clave_voz(ref_original, texto):
    import hashlib
    h = hashlib.sha1(open(ref_original, "rb").read()).hexdigest()[:12]
    return os.path.join(CACHE_VOZ, h, hashlib.sha1(texto.encode()).hexdigest()[:16] + ".wav")


def preparar_clon(textos, ref, tmp, ref_original):
    """Genera de una vez las frases con la voz clonada (carga el modelo una sola vez). Usa caché."""
    import shutil
    faltan = [t for t in textos if not os.path.exists(_clave_voz(ref_original, t))]
    if faltan:
        tj = os.path.join(tmp, "textos.json")
        json.dump(faltan, open(tj, "w"), ensure_ascii=False)
        carpeta = os.path.join(tmp, "clon")
        log(f"clonando voz para {len(faltan)} frases (≈30 s cada una)...")
        subprocess.run([VENV_VOZ, os.path.join(AQUI, "clonar_voz.py"), "--ref", ref, "--textos", tj,
                        "--salida", carpeta], check=True)
        for i, t in enumerate(faltan):
            dst = _clave_voz(ref_original, t)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(carpeta, f"vo_{i:03d}.wav"), dst)
    for t in textos:
        _clon[t] = _clave_voz(ref_original, t)


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
    # recortar silencios al inicio y al final
    # recortar silencios del inicio/fin (ignorando ruiditos sueltos) y acortar pausas internas,
    # sin quitar nunca voz: todos los tramos con sonido dentro de la frase se conservan.
    env = np.convolve(np.abs(x), np.ones(int(0.05 * SR)) / int(0.05 * SR), "same")
    activo = env > env.max() * 0.06
    bordes = np.flatnonzero(np.diff(np.concatenate([[0], activo.astype(np.int8), [0]])))
    todos = list(zip(bordes[::2], bordes[1::2]))
    largos = [k for k, (a, b) in enumerate(todos) if b - a >= 0.25 * SR]
    if largos:
        i0, i1 = largos[0], largos[-1]
        # incluir palabras cortas pegadas a la frase (separadas por menos de 0.5 s)
        while i0 > 0 and todos[i0][0] - todos[i0 - 1][1] < 0.5 * SR:
            i0 -= 1
        while i1 < len(todos) - 1 and todos[i1 + 1][0] - todos[i1][1] < 0.5 * SR:
            i1 += 1
        dentro = todos[i0:i1 + 1]
        partes = [x[max(0, dentro[0][0] - int(0.06 * SR)):dentro[0][0]]]
        for k, (ta, tb) in enumerate(dentro):
            partes.append(x[ta:tb])
            if k < len(dentro) - 1:
                gap = dentro[k + 1][0] - tb
                partes.append(x[tb:tb + min(gap, int(0.18 * SR))])   # pausas de máx 0.18 s
        partes.append(x[dentro[-1][1]:min(len(x), dentro[-1][1] + int(0.2 * SR))])
        x = np.concatenate(partes)
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
    # rellenar huecos internos (ropa oscura confundida con el fondo)
    inv = (1 - m).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
    hh, ww = m.shape
    for k in range(1, n2):
        x, y, w2, h2, a = st2[k]
        if x > 0 and x + w2 < ww and y > 0:          # no toca bordes laterales/arriba = hueco
            m[lab2 == k] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
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
    sx_, sy_ = seguro(p.get("x", 0.5), p.get("y", 0.5), ymin=0.26, ymax=0.64)
    tx, ty = sx_ * W, sy_ * H
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
_contador_escena = [0]


def render_escena(src, esc, salida, tmp, idx, claves, subs_x=0.5, subs_ancho=0.92):
    vo_wav = os.path.join(tmp, f"vo{idx}.wav")
    vo = voz_en_off(esc["voz"], vo_wav, esc.get("velocidad", 0.82))
    t_vo = 0.3
    d = max(esc.get("min", 2.5), t_vo + len(vo) / SR + 0.35)
    n = int(d * FPS)
    if efectos.TEMA:
        esc_list = efectos.TEMA["escenas"]
        est = ESTILOS[esc_list[_contador_escena[0] % len(esc_list)]]
        _contador_escena[0] += 1
    else:
        est = ESTILOS[esc.get("estilo", "neon")]
    fondo = FondoAnimado(W, H, est, seed=idx)
    corte = recorte_sticker(src, esc["congelar"], esc["caja"], esc.get("alto", 760))
    texto = a_bgra(sticker_pil(esc["texto"], esc.get("tam_texto", 86), esc.get("fondo", "#FFE600"),
                               esc.get("color", "#111111"), rot=esc.get("rot", -3), max_w=1000))
    subs = Subs(palabras_vo(esc["voz"], vo, t_vo), claves + esc.get("claves", []), est["palabra"], px=88,
                y=esc.get("subs_y", 0.745), x=esc.get("subs_x", subs_x), ancho=esc.get("subs_ancho", subs_ancho))
    evs = Eventos(esc.get("eventos", []), None)
    cache = {}
    # energía de la voz para animar el fondo
    hop = SR / FPS
    energia = np.array([np.sqrt(np.mean(vo[int(max(0, (i / FPS - t_vo)) * SR):int(max(0, (i / FPS - t_vo)) * SR + hop)] ** 2 + 1e-9))
                        for i in range(n)])
    energia = np.nan_to_num(energia)
    energia = np.clip(energia / (energia.max() + 1e-6), 0, 1)
    cx, cy = esc.get("x", 0.5) * W, esc.get("y", 0.45) * H

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
        superponer(cv, texto, W / 2, max(esc.get("texto_y", 0.19), 0.17) * H, ease_back((u - 0.1) / 0.3) * (1 + 0.02 * math.sin(u * 5)))
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
    if SFX_TRANSICION:
        mezclar(sintetizar("scratch"), 0, 0.55)
    mezclar(vo, t_vo, 1.0)
    for p in esc.get("props", []) + esc.get("eventos", []):
        if p.get("sfx"):
            mezclar(sintetizar(p["sfx"]), p.get("t", 0), 0.4 * p.get("vol", 1.0))
    if SFX_TRANSICION:
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
    ap.add_argument("--usar-config", action="store_true",
                    help="tomar voz, presentador y espejo de ~/.estudio/config.json (ver instalar.py)")
    args = ap.parse_args()
    if args.usar_config:
        cfg_path = os.path.join(os.path.expanduser("~"), ".estudio", "config.json")
        cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
        args.mi_voz = args.mi_voz or cfg.get("voz")
        args.presentador = args.presentador or cfg.get("presentador")
        args.presentador_espejo = args.presentador_espejo or bool(cfg.get("espejo"))
    plan = json.load(open(args.plan))
    tmp = tempfile.mkdtemp(prefix="montaje_")
    log(f"carpeta temporal (partes para verificar): {tmp}")
    tema = usar_tema(plan.get("tema", "auto"), os.path.basename(args.entrada))
    plan["base"]["tema"] = tema
    log(f"tema de diseño: {tema}")
    if args.mi_voz:
        ref = os.path.join(tmp, "ref.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", args.mi_voz, "-t", "30", "-ac", "1", "-ar", "24000",
                        "-af", "highpass=f=70,afftdn=nf=-25,loudnorm=I=-18", ref], check=True)
        preparar_clon([s["voz"] for s in plan["secuencia"] if "voz" in s], ref, tmp, args.mi_voz)

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

    global SFX_TRANSICION
    SFX_TRANSICION = plan.get("sfx_transiciones", True)
    if plan.get("quitar_silencios"):
        crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", args.entrada, "-ac", "1", "-ar", "16000",
                                "-f", "s16le", "-"], capture_output=True).stdout
        audio_orig = np.frombuffer(crudo, np.int16).astype(np.float32) / 32768
        nueva = []
        for seg in plan["secuencia"]:
            if "orig" in seg and seg.get("silencios", True) is False:
                nueva.append({"orig": seg["orig"]})          # respetar pausas (reacciones)
            elif "orig" in seg:
                nueva += [{"orig": [x, y]} for x, y in sin_silencios_audio(seg["orig"][0], seg["orig"][1], audio_orig)]
            else:
                nueva.append(seg)
        log(f"silencios quitados: {sum('orig' in x for x in plan['secuencia'])} tramos -> {sum('orig' in x for x in nueva)}")
        plan["secuencia"] = nueva
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
    est_barra = ESTILOS[efectos.TEMA["base"]] if efectos.TEMA else ESTILOS[plan["base"].get("estilo", "farandula")]
    col = "0x{:02X}{:02X}{:02X}".format(*est_barra["palabra"][::-1])
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
