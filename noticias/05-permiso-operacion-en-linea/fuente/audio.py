import json, subprocess, wave, numpy as np
tl=json.load(open('timeline.json')); ev=tl['ev']; S=ev['S']
SR=48000; T=tl['total']+.3; n=int(SR*T); rng=np.random.default_rng(11)
def f(m): return 440*2**((m-69)/12)
def put(buf,at,sig,gn=1.0):
    a=int(at*SR); b=min(n,a+len(sig))
    if 0<=a<n: buf[a:b]+=gn*sig[:b-a]
def tt(L): return np.arange(int(L*SR))/SR
def piano(m,L=1.6):
    x=tt(L); fr=f(m); return (np.sin(2*np.pi*fr*x)+.5*np.sin(4*np.pi*fr*x)*np.exp(-x*3)+.2*np.sin(6*np.pi*fr*x)*np.exp(-x*5))*np.exp(-x*2.2)*np.minimum(1,x/.005)
mus=np.zeros(n)
beat=60/96
minor=[[48,52,55],[43,47,50],[45,48,52],[41,45,48]]
major=[[48,52,55],[43,47,50],[45,48,52],[41,45,48]]   # C G Am F
t=0;bar=0
while t<T:
    prog=major if t>=S[7] else minor
    ch=prog[bar%4]
    # arpeggio 8ths
    pat=[0,1,2,1,0,2,1,2]
    for j,p in enumerate(pat):
        put(mus,t+j*beat/2,piano(ch[p]+12,1.4),.22)
    put(mus,t,piano(ch[0]-12,3.0),.35)
    L=beat*4; x=tt(L); env=np.minimum(1,x/.8)*np.minimum(1,(L-x)/.8)
    for m in ch: put(mus,t,(np.sin(2*np.pi*f(m)*x)+.4*np.sin(2*np.pi*f(m)*1.004*x))*env,.05)
    if t>=S[3]:  # soft pulse joins
        for b in range(4):
            xx=tt(.25); put(mus,t+b*beat,np.sin(2*np.pi*(50+70*np.exp(-xx*30))*xx)*np.exp(-xx*14),.35)
    t+=beat*4; bar+=1
mus=mus/np.abs(mus).max()*.12
sfx=np.zeros(n)
def whoosh(L=.4):
    x=rng.uniform(-1,1,int(L*SR)); e=np.sin(np.linspace(0,np.pi,len(x)))**2; return np.convolve(x,np.ones(24)/24,'same')*e*.45
def pop(fr=900):
    x=tt(.12); return np.sin(2*np.pi*(fr+600*np.exp(-x*40))*x)*np.exp(-x*30)*.3
def ding(fr=1318):
    x=tt(.7); return (np.sin(2*np.pi*fr*x)+.4*np.sin(2*np.pi*fr*2.01*x))*np.exp(-x*5)*.2
def boom():
    x=tt(.9); return np.sin(2*np.pi*(40+45*np.exp(-x*7))*x)*np.exp(-x*3.5)*.9
def thud():
    x=tt(.3); return (np.sin(2*np.pi*(70+60*np.exp(-x*25))*x)*np.exp(-x*12)+rng.uniform(-1,1,len(x))*np.exp(-x*40)*.4)*.8
def scratch(L=1.3):
    x=rng.uniform(-1,1,int(L*SR)); m=np.abs(np.sin(np.arange(len(x))/SR*2*np.pi*6)); return np.convolve(x,np.ones(6)/6,'same')*m*.12
def crack():
    x=tt(.15); return rng.uniform(-1,1,len(x))*np.exp(-x*35)*.35
for s in S[1:]: put(sfx,s-.08,whoosh())
for i in range(16): put(sfx,ev['filas']-.3+2.5*(i/16)**.8,pop(600+i*30),.4)
put(sfx,ev['enero'],pop(700)); put(sfx,ev['permiso'],pop())
for i in range(int(6/.25)): put(sfx,S[1]+i*.25,crack(),.25)
put(sfx,ev['perdido'],thud()); put(sfx,ev['trami']-.4,whoosh(.4)); put(sfx,ev['veces'],pop(1000))
put(sfx,ev['acaba'],boom()); put(sfx,ev['acaba'],thud())
put(sfx,S[3]+.1,whoosh(.5)); put(sfx,ev['linea'],pop(1200)); put(sfx,ev['linea']+.4,ding(1318)); put(sfx,ev['linea']+.52,ding(1568)); put(sfx,ev['cel'],pop())
put(sfx,ev['decl'],ding(1046))
for x in ('x1','x2','x3'): put(sfx,ev[x],thud()); put(sfx,ev[x]+.1,crack())
put(sfx,ev['sar'],pop()); put(sfx,ev['contrato']-.3,thud()); put(sfx,ev['contrato']+.2,scratch(1)); put(sfx,ev['sola'],thud()); put(sfx,ev['todo'],ding(1318))
put(sfx,ev['alc']-.3,whoosh()); put(sfx,ev['formal'],thud())
for x in ('malls','medios','redes'): put(sfx,ev[x]-.15,pop(900))
put(sfx,ev['frase'],thud()); put(sfx,ev['reinv'],ding(1046))
put(sfx,ev['vez']+.5,pop()); put(sfx,ev['vez']+.7,pop(1100)); put(sfx,ev['cta'],ding(1046)); put(sfx,ev['cta']+.12,ding(1568))
def wav(name,x):
    x=np.clip(x,-1,1); w=wave.open(name,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
wav('sfx.wav',sfx*.7)
inp=[];flt=[]
for i,s in enumerate(S):
    inp+=['-i',f's{i+1}_t.wav']; ms=int(s*1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inp+=['-i','sfx.wav']; k=len(S)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0,apad[voice]')
flt.append(f'[voice][{k}:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k','audio.m4a'],check=True)
print('ok')
