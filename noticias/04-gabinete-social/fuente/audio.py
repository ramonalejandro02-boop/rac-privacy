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
beat=60/76
minor=[[45,48,52],[41,45,48],[48,52,55],[43,47,50]]   # Am F C G
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
for i in range(10): put(sfx,.05+i*.05+.2,pop(700+i*40),.6)
for i in range(6): put(sfx,ev['pob']+i*.07,crack())
put(sfx,ev['pob']+.5,boom()); put(sfx,ev['pob']+.5,thud())
for i in range(4): put(sfx,ev['casi']+.2+i*.12,crack())
put(sfx,ev['ext']-.2,thud())
put(sfx,S[2]+.3,thud()); put(sfx,ev['firmar'],scratch()); put(sfx,ev['gab']+.3,boom()); put(sfx,ev['gab']+.3,thud())
for i in range(20): put(sfx,S[3]-.1+1.4*(i/20)**.9,pop(800+i*25),.5)
put(sfx,ev['prot'],ding(1046)); put(sfx,ev['red'],ding(1318))
put(sfx,ev['sec']-.1,thud()); put(sfx,ev['min'],pop()); put(sfx,ev['sec']+.9,thud())
for i in range(20): put(sfx,ev['cada']+.3+i*.16,scratch(.3),.7)
put(sfx,ev['conj'],thud())
for i in range(11): put(sfx,ev['plan']-.3+2*(i/10),pop(600+i*60),.5)
put(sfx,ev['d10'],ding(1568)); put(sfx,S[6]+1.2,thud())
put(sfx,ev['casa']-.5,pop()); put(sfx,ev['papel']-.5,pop(700)); put(sfx,ev['papel']+.2,boom())
for i in range(4): put(sfx,ev['prim']+.3+i*.15,pop(900+i*100))
put(sfx,ev['prim']+1.2,ding(1046)); put(sfx,ev['prim']+1.32,ding(1568))
def wav(name,x):
    x=np.clip(x,-1,1); w=wave.open(name,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
wav('music.wav',mus); wav('sfx.wav',sfx*.7)
inp=[];flt=[]
for i,s in enumerate(S):
    inp+=['-i',f's{i+1}.mp3']; ms=int(s*1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inp+=['-i','music.wav','-i','sfx.wav']; k=len(S)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0,apad[voice]')
flt.append(f'[voice]asplit=2[vo][sc];[{k}:a][sc]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[duck];[vo][duck][{k+1}:a]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k','audio.m4a'],check=True)
print('ok')
