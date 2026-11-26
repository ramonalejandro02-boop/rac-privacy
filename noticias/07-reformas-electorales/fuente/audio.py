import json, subprocess, wave, numpy as np
tl=json.load(open('timeline.json')); ev=tl['ev']; S=ev['S']
SR=48000; T=tl['total']+.3; n=int(SR*T); sfx=np.zeros(n)
def put(at,sig):
    a=int(at*SR); b=min(n,a+len(sig))
    if 0<=a<n: sfx[a:b]+=sig[:b-a]
def tt(L): return np.arange(int(L*SR))/SR
def click():
    x=tt(.08); return (np.sin(2*np.pi*900*x)*np.exp(-x*80))*.18
def thump():
    x=tt(.4); return np.sin(2*np.pi*(60+45*np.exp(-x*18))*x)*np.exp(-x*9)*.35
def ding(fr=1046):
    x=tt(.6); return (np.sin(2*np.pi*fr*x)+.3*np.sin(2*np.pi*fr*2.01*x))*np.exp(-x*6)*.12
# solo 3 efectos
put(ev['lunes']-.2+.3,ding(1568)); put(ev['n86']-.1,thump()); put(ev['cta'],ding())
x=np.clip(sfx,-1,1); w=wave.open('sfx.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
inp=[];flt=[]
for i,s in enumerate(S):
    inp+=['-i',f's{i+1}_t.wav']; ms=int(s*1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inp+=['-i','sfx.wav']; k=len(S)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0,apad[voice]')
flt.append(f'[voice][{k}:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k','audio.m4a'],check=True)
print('ok')
