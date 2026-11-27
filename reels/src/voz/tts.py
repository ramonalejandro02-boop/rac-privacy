import sys,time,torch,torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(4)
m=ChatterboxMultilingualTTS.from_pretrained(device='cpu')
def say(text,out,ref='ref.wav',ex=0.5,cfg=0.5,temp=0.8):
    t=time.time(); w=m.generate(text,language_id='es',audio_prompt_path=ref,exaggeration=ex,cfg_weight=cfg,temperature=temp)
    ta.save(out,w,m.sr); print(out,round(w.shape[-1]/m.sr,2),'s audio en',round(time.time()-t,1),'s',flush=True)
if __name__=='__main__':
    say("¿Le deben meses de pensión alimenticia, y le dijeron que ya los perdió? Eso acaba de cambiar en Honduras.","prueba1.wav")
