"""Spanish TTS: espeak-ng phonemes -> Kokoro v1.0 / Piper onnx (direct)."""
import sys, json, numpy as np, onnxruntime as ort, soundfile as sf
import espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
from phonemizer.backend import EspeakBackend
D = "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad/tts_dl"
BK = EspeakBackend("es-419", preserve_punctuation=True, with_stress=True)

class Kokoro:
    def __init__(s):
        m = f"{D}/kokoro-multi-lang-v1_0"
        s.sess = ort.InferenceSession(f"{m}/model.onnx", providers=["CPUExecutionProvider"])
        s.vocab = {}
        for line in open(f"{m}/tokens.txt", encoding="utf-8"):
            parts = line.rstrip("\n").rsplit(" ", 1)
            if len(parts) == 2: s.vocab[parts[0] if parts[0] else " "] = int(parts[1])
        s.voices = np.fromfile(f"{m}/voices.bin", dtype=np.float32).reshape(54, 510, 1, 256)
        s.inputs = [i.name for i in s.sess.get_inputs()]
    def __call__(s, text, sid=29, speed=1.0):
        ph = BK.phonemize([text])[0].strip()
        ids = [s.vocab[c] for c in ph if c in s.vocab]
        style = s.voices[sid, min(len(ids), 509)]
        toks = np.array([[0] + ids + [0]], dtype=np.int64)
        feed = {}
        for n in s.inputs:
            if "token" in n or n == "input_ids": feed[n] = toks
            elif "style" in n: feed[n] = style.astype(np.float32)
            elif "speed" in n: feed[n] = np.array([speed], dtype=np.float32)
        out = s.sess.run(None, feed)[0].reshape(-1)
        return out, 24000, ph

class Piper:
    def __init__(s, name="es_MX-claude-high"):
        m = f"{D}/vits-piper-{name}"
        s.sess = ort.InferenceSession(f"{m}/{name}.onnx", providers=["CPUExecutionProvider"])
        s.cfg = json.load(open(f"{m}/{name}.onnx.json"))
        s.map = s.cfg["phoneme_id_map"]
    def __call__(s, text, sid=0, speed=1.0):
        ph = BK.phonemize([text])[0].strip()
        ids = s.map["^"][:]
        for c in ph:
            if c in s.map: ids += s.map[c] + s.map["_"]
        ids += s.map["$"]
        inf = s.cfg.get("inference", {})
        scales = np.array([inf.get("noise_scale", .667), inf.get("length_scale", 1) / speed, inf.get("noise_w", .8)], np.float32)
        feed = {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64), "scales": scales}
        out = s.sess.run(None, feed)[0].reshape(-1)
        return out, s.cfg["audio"]["sample_rate"], ph

if __name__ == "__main__":
    out = sys.argv[1]
    txt = "Cuando la pintura se daña, el agua y el oxígeno llegan al acero, y la corrosión avanza por debajo."
    k = Kokoro(); print("kokoro inputs", k.inputs)
    for sid, n in [(29, "alex"), (28, "dora"), (53, "santa")]:
        a, sr, ph = k(txt, sid); sf.write(f"{out}/k_{n}.wav", a, sr); print(n, len(a) / sr)
    p = Piper(); a, sr, ph = p(txt); sf.write(f"{out}/p_claude.wav", a, sr); print("piper", len(a) / sr)
