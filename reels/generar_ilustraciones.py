"""Genera ilustraciones pintadas con IA local (DreamShaper 8 + LCM, CPU, sin costo).
Uso: python generar_ilustraciones.py escenas.json carpeta_salida
escenas.json = [{"prompt": "...", "seed": 1}, ...]
"""
import json, os, sys, torch
from diffusers import StableDiffusionPipeline, LCMScheduler
torch.set_num_threads(os.cpu_count())
ESTILO = (", digital painting, storybook animation style, soft painterly brushstrokes, cinematic volumetric lighting, "
          "teal and warm gold color palette, highly detailed, beautiful 2D illustration, vertical composition")
NEG = "photo, photorealistic, 3d render, deformed, extra limbs, bad hands, text, watermark, signature, blurry, ugly, lowres"
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
p = StableDiffusionPipeline.from_pretrained("Lykon/dreamshaper-8", torch_dtype=torch.float32, safety_checker=None)
p.scheduler = LCMScheduler.from_config(p.scheduler.config)
p.load_lora_weights("latent-consistency/lcm-lora-sdv1-5"); p.fuse_lora()
for i, sc in enumerate(json.load(open(src))):
    f = os.path.join(out, f"escena{i+1}.png")
    if os.path.exists(f): continue
    im = p(sc["prompt"] + ESTILO, negative_prompt=NEG, num_inference_steps=7, guidance_scale=1.5,
           width=576, height=1024, generator=torch.manual_seed(sc.get("seed", 7))).images[0]
    im.save(f); print("lista", f, flush=True)
