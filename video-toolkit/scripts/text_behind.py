#!/usr/bin/env python3
"""Texto DETRÁS de la persona.

Recorta a la persona en cada fotograma con IA, dibuja el texto sobre el fondo
y vuelve a poner a la persona encima. Conserva el audio original.

Ejemplos:
  python text_behind.py entrada.mp4 salida.mp4 --text "IMPARABLE"
  python text_behind.py entrada.mp4 salida.mp4 --text "HOLA" --color "#ffcc00" --size 0.35 --y 0.35 --start 1 --end 6
  python text_behind.py foto.jpg foto_out.png --text "VERANO" --engine rembg   # imagen, máxima calidad

Motores:
  mediapipe (por defecto) rápido, ideal para video.
  rembg     más preciso en bordes (pelo), más lento: mejor para fotos o clips cortos.
            Usa BiRefNet-portrait (calidad máxima). Otro modelo: REMBG_MODEL=u2net_human_seg
"""
import argparse
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_FONT = os.path.join(ROOT, "fonts", "Anton.ttf")
DEFAULT_MODEL = os.path.join(ROOT, "models", "selfie_multiclass.tflite")


def hex_to_rgba(h, alpha=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


class Segmenter:
    def __init__(self, engine, model_path):
        self.engine = engine
        if engine == "mediapipe":
            import mediapipe as mp
            from mediapipe.tasks import python as mpp
            from mediapipe.tasks.python import vision
            self.mp = mp
            opts = vision.ImageSegmenterOptions(
                base_options=mpp.BaseOptions(model_asset_path=model_path),
                output_confidence_masks=True,
            )
            self.seg = vision.ImageSegmenter.create_from_options(opts)
        else:
            from rembg import new_session, remove
            self.remove = remove
            self.session = new_session(os.environ.get("REMBG_MODEL", "birefnet-portrait"))

    def close(self):
        if self.engine == "mediapipe":
            self.seg.close()

    def mask(self, bgr):
        """Devuelve máscara float32 0..1 (1 = persona)."""
        if self.engine == "mediapipe":
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
            res = self.seg.segment(img)
            # selfie_multiclass: 0 = fondo; persona = 1 - fondo
            bg = res.confidence_masks[0].numpy_view()
            m = 1.0 - bg.astype(np.float32)
            if m.shape[:2] != bgr.shape[:2]:
                m = cv2.resize(m, (bgr.shape[1], bgr.shape[0]))
            return m
        rgb = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        m = self.remove(rgb, session=self.session, only_mask=True)
        return np.asarray(m, dtype=np.float32) / 255.0


def render_text_layer(w, h, a):
    """Capa RGBA con el texto (se calcula una vez)."""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    lines = a.text.split("\\n")
    size = int(h * a.size / max(1, len(lines)))
    font = ImageFont.truetype(a.font, size)
    # Ajustar para que quepa en el ancho
    while max(draw.textlength(l, font=font) for l in lines) > w * 0.94 and size > 10:
        size = int(size * 0.95)
        font = ImageFont.truetype(a.font, size)
    spacing = int(size * 0.05)
    block_h = sum(font.getbbox(l)[3] - font.getbbox(l)[1] for l in lines) + spacing * (len(lines) - 1)
    y = int(h * a.y - block_h / 2)
    for line in lines:
        bbox = font.getbbox(line)
        tw = draw.textlength(line, font=font)
        x = int((w - tw) / 2)
        if a.shadow:
            draw.text((x + size // 40, y - bbox[1] + size // 40), line, font=font, fill=(0, 0, 0, 110))
        draw.text((x, y - bbox[1]), line, font=font, fill=hex_to_rgba(a.color, int(255 * a.opacity)))
        y += (bbox[3] - bbox[1]) + spacing
    arr = np.asarray(layer).astype(np.float32) / 255.0
    return arr[..., :3][..., ::-1].copy(), arr[..., 3:4].copy()  # BGR, alpha


def composite(frame, text_bgr, text_a, mask, fade):
    f = frame.astype(np.float32) / 255.0
    ta = text_a * fade
    with_text = f * (1 - ta) + text_bgr * ta
    m = mask[..., None]
    out = with_text * (1 - m) + f * m  # persona encima del texto
    return np.clip(out * 255, 0, 255).astype(np.uint8)


def refine(mask, prev, a):
    m = np.clip((mask - 0.5) * a.contrast + 0.5, 0, 1)  # bordes más definidos
    if a.feather > 0:
        k = a.feather * 2 + 1
        m = cv2.GaussianBlur(m, (k, k), 0)
    if prev is not None and a.smooth > 0:  # suavizado temporal anti-parpadeo
        m = a.smooth * prev + (1 - a.smooth) * m
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--text", required=True, help='Texto. Usa "\\n" para varias líneas.')
    p.add_argument("--font", default=DEFAULT_FONT)
    p.add_argument("--color", default="#ffffff")
    p.add_argument("--opacity", type=float, default=1.0)
    p.add_argument("--size", type=float, default=0.32, help="Altura del texto relativa al video (0-1)")
    p.add_argument("--y", type=float, default=0.38, help="Centro vertical del texto (0 arriba, 1 abajo)")
    p.add_argument("--shadow", action="store_true")
    p.add_argument("--start", type=float, default=0.0, help="Segundo en que aparece el texto")
    p.add_argument("--end", type=float, default=None, help="Segundo en que desaparece")
    p.add_argument("--fade", type=float, default=0.4, help="Duración del fundido (s)")
    p.add_argument("--engine", choices=["mediapipe", "rembg"], default="mediapipe")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--feather", type=int, default=2, help="Suavizado del borde en px")
    p.add_argument("--contrast", type=float, default=2.5, help="Dureza del borde de la máscara")
    p.add_argument("--smooth", type=float, default=0.35, help="Anti-parpadeo 0-0.9")
    p.add_argument("--crf", type=int, default=17)
    a = p.parse_args()

    seg = Segmenter(a.engine, a.model)

    # Imagen
    if a.input.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        img = cv2.imread(a.input)
        h, w = img.shape[:2]
        tb, ta = render_text_layer(w, h, a)
        m = refine(seg.mask(img), None, a)
        cv2.imwrite(a.output, composite(img, tb, ta, m, 1.0))
        seg.close()
        print("OK ->", a.output)
        return

    cap = cv2.VideoCapture(a.input)
    if not cap.isOpened():
        sys.exit(f"No se pudo abrir {a.input}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    tb, ta = render_text_layer(w, h, a)

    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
        "-i", a.input, "-map", "0:v", "-map", "1:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest", a.output,
    ], stdin=subprocess.PIPE)

    prev, i = None, 0
    end = a.end if a.end is not None else total / fps + 1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        if t < a.start or t > end:
            out = frame
            prev = None
        else:
            fade = 1.0 if a.fade <= 0 else min(1.0, (t - a.start) / a.fade, (end - t) / a.fade)
            prev = refine(seg.mask(frame), prev, a)
            out = composite(frame, tb, ta, prev, max(0.0, fade))
        ff.stdin.write(out.tobytes())
        i += 1
        if i % 30 == 0:
            print(f"\r{i}/{total} fotogramas", end="", flush=True)
    cap.release()
    ff.stdin.close()
    ff.wait()
    seg.close()
    print(f"\nOK -> {a.output}")


if __name__ == "__main__":
    main()
