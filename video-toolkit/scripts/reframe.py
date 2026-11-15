#!/usr/bin/env python3
"""Auto-reframe: convierte un video horizontal en vertical (9:16) u otro formato
siguiendo la cara de la persona con un movimiento de cámara suave.

Uso:
  python reframe.py entrada.mp4 salida.mp4                 # 9:16
  python reframe.py entrada.mp4 salida.mp4 --aspect 1:1    # cuadrado
  python reframe.py entrada.mp4 salida.mp4 --aspect 4:5 --smooth 0.92
"""
import argparse, os, subprocess
import cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input"); p.add_argument("output")
    p.add_argument("--aspect", default="9:16")
    p.add_argument("--smooth", type=float, default=0.9, help="0-0.98: más alto = cámara más suave")
    p.add_argument("--headroom", type=float, default=0.38, help="Posición vertical de la cara (0 arriba, 1 abajo)")
    p.add_argument("--zoom", type=float, default=1.0, help=">1 acerca más")
    p.add_argument("--model", default=os.path.join(ROOT, "models", "face_detector.tflite"))
    a = p.parse_args()

    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=mpp.BaseOptions(model_asset_path=a.model), min_detection_confidence=0.5))

    cap = cv2.VideoCapture(a.input)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    aw, ah = (float(x) for x in a.aspect.split(":"))
    ch = int(min(H, W * ah / aw) / a.zoom) // 2 * 2
    cw = int(ch * aw / ah) // 2 * 2
    ow, oh = (1080, int(1080 * ah / aw) // 2 * 2) if aw < ah else (int(1080 * aw / ah) // 2 * 2, 1080)

    # Pasada 1: posición de la cara por fotograma
    cx_list, cy_list, last = [], [], (W / 2, H * 0.4)
    while True:
        ok, f = cap.read()
        if not ok: break
        res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))
        if res.detections:
            b = max(res.detections, key=lambda d: d.bounding_box.width * d.bounding_box.height).bounding_box
            last = (b.origin_x + b.width / 2, b.origin_y + b.height / 2)
        cx_list.append(last[0]); cy_list.append(last[1])
    det.close()
    if not cx_list: raise SystemExit("Video vacío")

    # Suavizado en ambos sentidos (sin retraso) + zona muerta para que no "baile"
    def smooth(v):
        v = np.array(v, dtype=np.float64)
        f = v.copy()
        for i in range(1, len(v)): f[i] = a.smooth * f[i - 1] + (1 - a.smooth) * v[i]
        b = f.copy()
        for i in range(len(v) - 2, -1, -1): b[i] = a.smooth * b[i + 1] + (1 - a.smooth) * f[i]
        return b
    xs, ys = smooth(cx_list), smooth(cy_list)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}", "-r", str(fps), "-i", "-",
                           "-i", a.input, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", a.output],
                          stdin=subprocess.PIPE)
    for i in range(len(xs)):
        ok, f = cap.read()
        if not ok: break
        x0 = int(np.clip(xs[i] - cw / 2, 0, W - cw))
        y0 = int(np.clip(ys[i] - ch * a.headroom, 0, H - ch))
        crop = f[y0:y0 + ch, x0:x0 + cw]
        ff.stdin.write(cv2.resize(crop, (ow, oh), interpolation=cv2.INTER_LANCZOS4).tobytes())
        if i % 30 == 0: print(f"\r{i}/{total}", end="", flush=True)
    ff.stdin.close(); ff.wait()
    print(f"\nOK -> {a.output}")


if __name__ == "__main__":
    main()
