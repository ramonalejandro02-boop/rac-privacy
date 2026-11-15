#!/usr/bin/env python3
"""Voz profesional y efectos de sonido con Pedalboard (motor de audio de Spotify).

Presets:
  limpia     reducción de ruido IA (spectral gating) + cadena de estudio
  locutor    voz grave y presente de radio/locución
  trailer    voz épica de tráiler de cine (grave + reverb grande)
  radio      voz de radio antigua / walkie
  telefono   llamada telefónica
  cueva      reverb enorme
  robot      voz robótica
  grave / aguda  cambia el tono (+/- semitonos con --semitones)

Uso: python voice_fx.py entrada.(wav|mp3|mp4) salida.(wav|mp4) locutor
"""
import argparse, os, subprocess, tempfile
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input"); p.add_argument("output"); p.add_argument("preset", default="limpia", nargs="?")
    p.add_argument("--semitones", type=float, default=None)
    p.add_argument("--denoise", type=float, default=0.85, help="0-1 fuerza de la reducción de ruido")
    a = p.parse_args()
    from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, Compressor, Gain, Reverb, PeakFilter, LowShelfFilter,
                            HighShelfFilter, Limiter, NoiseGate, PitchShift, Distortion, Bitcrush, Chorus, Delay)
    from pedalboard.io import AudioFile
    import noisereduce as nr

    tmp = tempfile.mkdtemp()
    wav_in = os.path.join(tmp, "in.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, "-vn", "-ar", "48000", wav_in], check=True)
    with AudioFile(wav_in) as f:
        audio, sr = f.read(f.frames), f.samplerate

    audio = nr.reduce_noise(y=audio, sr=sr, prop_decrease=a.denoise, stationary=False).astype(np.float32)
    studio = [HighpassFilter(80), NoiseGate(threshold_db=-50, ratio=4), LowShelfFilter(150, 1.5), PeakFilter(350, -2.5, 1.0),
              PeakFilter(3500, 3, 0.9), HighShelfFilter(10000, 2), Compressor(threshold_db=-20, ratio=3.5, attack_ms=8, release_ms=150), Gain(4)]
    presets = {
        "limpia": studio,
        "locutor": [HighpassFilter(60), LowShelfFilter(120, 4), PeakFilter(300, -3, 1), PeakFilter(4000, 4, 1), Compressor(-24, 5, 5, 120), Gain(6)],
        "trailer": [PitchShift(-3), HighpassFilter(40), LowShelfFilter(110, 6), PeakFilter(3000, 2, 1), Compressor(-25, 6, 3, 200), Gain(6),
                    Reverb(room_size=0.85, damping=0.4, wet_level=0.25, dry_level=0.85, width=1.0)],
        "radio": studio[:-1] + [HighpassFilter(500), LowpassFilter(3800), Distortion(8), Compressor(-18, 6), Gain(2)],
        "telefono": [HighpassFilter(400), LowpassFilter(3200), Bitcrush(bit_depth=10), Compressor(-20, 6), Gain(4)],
        "cueva": studio + [Reverb(room_size=0.98, damping=0.2, wet_level=0.5, dry_level=0.6), Delay(0.35, 0.3, 0.2)],
        "robot": studio + [PitchShift(-2), Chorus(rate_hz=40, depth=0.6, mix=0.7), Bitcrush(bit_depth=8)],
        "grave": studio + [PitchShift(a.semitones or -4)],
        "aguda": studio + [PitchShift(a.semitones or 4)],
    }
    if a.preset not in presets: raise SystemExit("Presets: " + ", ".join(presets))
    chain = presets[a.preset] + [Limiter(threshold_db=-1.0)]
    if a.semitones is not None and a.preset not in ("grave", "aguda"): chain.insert(0, PitchShift(a.semitones))
    out = Pedalboard(chain)(audio, sr)

    wav_out = os.path.join(tmp, "out.wav")
    with AudioFile(wav_out, "w", sr, out.shape[0]) as f:
        f.write(out)
    if a.output.lower().endswith((".mp4", ".mov", ".mkv")):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, "-i", wav_out, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1", "-c:a", "aac", "-b:a", "256k", a.output], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_out, "-af", "loudnorm=I=-14:TP=-1", "-ar", "48000", a.output], check=True)
    print(f"OK -> {a.output}  (preset {a.preset})")


if __name__ == "__main__":
    main()
