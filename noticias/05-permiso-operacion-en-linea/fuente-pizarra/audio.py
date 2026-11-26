import json, subprocess, wave, numpy as np
tl=json.load(open('timeline.json')); ev=tl['ev']; S=ev['S']
SR=48000; T=tl['total']+.3; n=int(SR*T); rng=np.random.default_rng(31)
sfx=np.zeros(n)
def put(at,sig,gn=1.0):
    a=int(at*SR); b=min(n,a+len(sig))
    if 0<=a<n: sfx[a:b]+=gn*sig[:b-a]
def scribble(L):
    m=int(L*SR); x=rng.uniform(-1,1,m); x=np.convolve(x,np.ones(3)/3,'same')
    tt=np.arange(m)/SR; mod=.5+.5*np.abs(np.sin(2*np.pi*(7+3*np.sin(tt*5))*tt))
    env=np.minimum(1,tt/.02)*np.minimum(1,(L-tt)/.03); return x*mod*env*.10
def squeak(L=.12):
    tt=np.arange(int(L*SR))/SR; f=1800+600*np.sin(tt*40); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*12)*.05
def wipe(L=.32):
    x=rng.uniform(-1,1,int(L*SR)); e=np.sin(np.linspace(0,np.pi,len(x)))**1.5; return np.convolve(x,np.ones(40)/40,'same')*e*.9
def tap():
    tt=np.arange(int(.06*SR))/SR; return np.sin(2*np.pi*220*tt)*np.exp(-tt*60)*.4
for s in S[1:]: put(s,wipe())
# drawing moments (start, duration)
D=[(.05,.6),(.1,1.2),(ev['filas'],1.9),(ev['enero']-.2,.9),(ev['permiso'],.9),
   (S[1]+.05,1.3),(ev['perdido']-.1,.9),(ev['veces'],.4),(ev['trami']-.5,1.1),
   (S[2],.6),(S[3]+.05,1.8),(ev['linea']-.3,.9),(ev['cel'],.5),
   (S[4]+.02,.5),(ev['decl']+.3,.5),(ev['x1']-.6,.8),(ev['x2']-.6,.8),(ev['x3']-.6,.8),
   (ev['contrato']-.3,1.3),(ev['sola'],.5),(ev['todo']-.7,1.2),
   (S[6]+.05,1.0),(ev['formal'],1.4),(ev['malls']-.35,.6),(ev['medios']-.35,.6),(ev['redes']-.35,1.1),
   (S[7]+.05,.5),(ev['digit']-.1,1.1),(ev['reinv']-.1,1.6),
   (S[8]+.02,.4),(ev['vez'],1.2),(ev['cta']-.3,1.0)]
for a,L in D: put(a,scribble(L)); put(a,squeak(),1)
for x in ('x1','x2','x3'): put(ev[x],squeak(.2),1.5)
put(ev['contrato']-.3,tap()); put(ev['sar']-.1,tap())
x=np.clip(sfx,-1,1); w=wave.open('sfx.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
inp=[];flt=[]
for i,s in enumerate(S):
    inp+=['-i',f's{i+1}_t.wav']; ms=int(s*1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inp+=['-i','sfx.wav']; k=len(S)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0,apad[voice]')
flt.append(f'[voice][{k}:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k','audio.m4a'],check=True)
print('ok')
