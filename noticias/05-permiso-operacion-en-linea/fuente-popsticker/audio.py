import json, subprocess, wave, numpy as np
tl=json.load(open('timeline.json')); ev=tl['ev']; S=ev['S']
SR=48000; T=tl['total']+.3; n=int(SR*T); rng=np.random.default_rng(21)
def put(at,sig,gn=1.0):
    a=int(at*SR); b=min(n,a+len(sig))
    if 0<=a<n: sfx[a:b]+=gn*sig[:b-a]
def tt(L): return np.arange(int(L*SR))/SR
sfx=np.zeros(n)
def boing(f0=300):
    x=tt(.35); fr=f0*(1+.6*np.exp(-x*10)*np.sin(x*60)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-x*8)*.35
def pop(fr=900):
    x=tt(.1); return np.sin(2*np.pi*(fr+700*np.exp(-x*50))*x)*np.exp(-x*35)*.32
def swish(L=.25):
    x=rng.uniform(-1,1,int(L*SR)); e=np.sin(np.linspace(0,np.pi,len(x)))**2; return np.convolve(x,np.ones(10)/10,'same')*e*.4
def ding(fr=1318):
    x=tt(.6); return (np.sin(2*np.pi*fr*x)+.4*np.sin(2*np.pi*fr*2.01*x))*np.exp(-x*6)*.2
def kaboom():
    x=tt(.7); return (np.sin(2*np.pi*(50+80*np.exp(-x*9))*x)*np.exp(-x*5)+rng.uniform(-1,1,len(x))*np.exp(-x*12)*.5)*.8
def tick():
    x=tt(.02); return np.sin(2*np.pi*2600*x)*np.exp(-x*300)*.2
def flap():
    x=rng.uniform(-1,1,int(.06*SR)); return np.convolve(x,np.ones(30)/30,'same')*.5
def chime():
    return np.concatenate([ding(1046)[:int(.12*SR)],ding(1318)[:int(.12*SR)],ding(1568)])
for s in S[1:]: put(s,swish())
put(.05,boing(260))
for i in range(30): put(ev['filas']+2.6*(i/30)**1.2,tick())
for i in range(9): put(ev['filas']+.15+i*.28,pop(700+i*40),.6)
put(ev['enero'],boing(330)); put(ev['permiso'],pop())
for i in range(int((S[2]-S[1])/.18)): put(S[1]+i*.18,tick(),.6)
put(ev['perdido'],boing(240)); put(ev['veces'],pop(1100))
for i in range(12): put(ev['trami']-.3+i*.12,flap(),.5)
put(S[2],kaboom())
put(S[3]+.2,swish(.4)); put(ev['linea']-.1,pop(600)); put(ev['linea']+.35,chime()); put(ev['cel'],pop())
put(ev['decl'],boing(300))
for x in ('x1','x2','x3'): put(ev[x]-.6,pop(800)); put(ev[x],boing(180))
put(ev['sar'],pop()); put(ev['contrato']-.2,boing(280)); put(ev['sola'],pop(1000)); put(ev['todo']-.3,boing(350)); put(ev['todo'],ding(1568))
put(ev['alc'],pop()); put(ev['formal'],pop(1100))
for x in ('malls','medios','redes'): put(ev[x]-.15,boing(400))
put(S[7]+.05,pop()); put(ev['digit']-.1,pop(800)); put(ev['digit']+.6,swish(.3)); put(ev['reinv']-.1,boing(320)); put(ev['reinv']+.6,swish(.6))
put(ev['vez'],pop()); put(ev['vez']+.4,boing(300)); put(ev['vez']+.6,boing(220)); put(ev['cta'],chime())
x=np.clip(sfx*.8,-1,1); w=wave.open('sfx.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
inp=[];flt=[]
for i,s in enumerate(S):
    inp+=['-i',f's{i+1}_t.wav']; ms=int(s*1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inp+=['-i','sfx.wav']; k=len(S)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0,apad[voice]')
flt.append(f'[voice][{k}:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k','audio.m4a'],check=True)
print('ok')
