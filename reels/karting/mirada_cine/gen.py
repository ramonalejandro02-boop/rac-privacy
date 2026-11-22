import torch,json,sys
from diffusers import AutoPipelineForText2Image
torch.set_num_threads(4)
p=AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo",torch_dtype=torch.bfloat16,variant="fp16")
STYLE=", cinematic film still, professional motorsport photography, anamorphic, dramatic light, high detail, sharp focus, 35mm film grain"
NEG=""
SH={
 "A_visor":"extreme close-up of a racing driver's eyes behind an open full-face helmet visor, eyes looking down, intense, reflections on the visor, sweat, golden hour rim light",
 "B_spin":"a racing go-kart spinning off track into the gravel trap, dust cloud and tyre smoke, tyre barrier wall in background, dramatic motion blur, afternoon sun",
 "C_hands":"close-up of racing gloves gripping a go-kart steering wheel tightly, knuckles, motion blur background of asphalt, dramatic side light",
 "D_pov":"point of view from inside a racing go-kart looking down at the front nose and the asphalt rushing below, steering wheel and gloves at bottom, speed motion blur",
 "E_profile":"side profile of a young kart racer wearing a white helmet, visor up, eyes focused far ahead on the track, sunset backlight, shallow depth of field",
 "F_approach":"low angle shot of a racing go-kart braking hard approaching a corner on a kart track, front wheels, tyre smoke, red and white kerbs, sunset, motion blur",
 "G_apex":"racing go-kart clipping the inside red and white kerb at the apex of a corner, inside wheel lifted, low angle from the kerb, motion blur background, golden hour",
 "H_exit":"aerial drone view of a racing go-kart accelerating out of a corner on an empty kart track at sunset, long shadows, tyre marks on asphalt, cinematic",
 "I_eye":"macro close-up of a single human eye looking through a racing helmet visor, the reflection of a race track corner visible in the eye and visor, intense focus",
}
which=sys.argv[1:] or list(SH)
for k in which:
  for seed in (11,23):
    g=torch.Generator().manual_seed(seed)
    im=p(prompt=SH[k]+STYLE,num_inference_steps=3,guidance_scale=0.0,width=576,height=1024,generator=g).images[0]
    im.save(f'shots/{k}_{seed}.png'); print(k,seed,flush=True)
