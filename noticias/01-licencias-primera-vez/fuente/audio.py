import json, os, subprocess, wave, numpy as np
tl=json.load(open('timeline.json')); ev=tl['ev']; S=ev['S']
SR=48000; T=tl['total']+.3; n=int(SR*T); rng=np.random.default_rng(5)
def f(m): return 440*2**((m-69)/12)
def put(buf,at,sig,gn=1.0):
    a=int(at*SR); b=min(n,a+len(sig))
    if 0<=a<n: buf[a:b]+=gn*sig[:b-a]
def tt(L): return np.arange(int(L*SR))/SR
mus=np.zeros(n)
# news bed: 104 bpm, pluck arpeggio + soft kick + shaker, chords Dm Bb F C
beat=60/104; step=beat/2; prog=[[50,53,57],[46,50,53],[41,45,48],[48,52,55]]
t=0;i=0
while t<T:
    ch=prog[(i//16)%4]; note=ch[i%3]+12*(1+(i%4==3))
    x=tt(.35); put(mus,t,(np.sin(2*np.pi*f(note)*x)+.3*np.sin(4*np.pi*f(note)*x))*np.exp(-x*9),.35)
    if i%4==0:
        x=tt(.18); put(mus,t,np.sin(2*np.pi*(45+90*np.exp(-x*30))*x)*np.exp(-x*18),.9)
    if i%2==1:
        L=int(.05*SR); put(mus,t,rng.uniform(-1,1,L)*np.exp(-np.arange(L)/SR*80),.12)
    if i%16==0:
        x=tt(beat*8); env=np.minimum(1,x/.8)*np.minimum(1,(beat*8-x)/.8)
        for m in ch: put(mus,t,np.sin(2*np.pi*f(m-12)*x)*env,.1)
    i+=1; t+=step
mus=mus/np.abs(mus).max()*.11
sfx=np.zeros(n)
def whoosh(L=.4):
    x=rng.uniform(-1,1,int(L*SR)); e=np.sin(np.linspace(0,np.pi,len(x)))**2
    k=np.ones(30)/30; return np.convolve(x,k,'same')*e*.6
def thud():
    x=tt(.35); return (np.sin(2*np.pi*(70+60*np.exp(-x*25))*x)*np.exp(-x*12)+rng.uniform(-1,1,len(x))*np.exp(-x*40)*.5)*.9
def pop(fr=900):
    x=tt(.12); return np.sin(2*np.pi*(fr+600*np.exp(-x*40))*x)*np.exp(-x*30)*.4
def ding(fr=1318):
    x=tt(.6); return (np.sin(2*np.pi*fr*x)+.4*np.sin(2*np.pi*fr*2.01*x))*np.exp(-x*6)*.25
for s in S[1:]: put(sfx,s-.05,whoosh())
put(sfx,.1,whoosh(.5)); put(sfx,.6,whoosh(.4))
put(sfx,ev['ojo'],thud())
put(sfx,ev['nov'],pop(700)); put(sfx,ev['tgu'],pop()); put(sfx,ev['sps'],pop(1100))
put(sfx,ev['renov'],ding()); put(sfx,ev['brig'],pop(600))
for x in ('r1','r2','r3'): put(sfx,ev[x],pop(800))
put(sfx,ev['pero'],thud()); put(sfx,ev['contra'],whoosh(.5))
for x in ('pn','pl','lb'): put(sfx,ev[x],pop(1000))
put(sfx,ev['todos'],ding(1046))
put(sfx,ev['zam'],pop()); put(sfx,ev['mocion'],pop(700)); put(sfx,ev['mocion']+.5,thud())
for x in ('tr','po','se'): put(sfx,ev[x],pop(1200))
for x in ('c1','c2','c3'): put(sfx,ev[x],ding(1568))
put(sfx,ev['v1'],pop()); put(sfx,ev['v2'],pop(1100)); put(sfx,ev['cta'],ding(1046)); put(sfx,ev['cta']+.12,ding(1568))
def wav(name,x):
    x=np.clip(x,-1,1); w=wave.open(name,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
wav('music.wav',mus); wav('sfx.wav',sfx*.7)
inp=[];flt=[]
for i,s in enumerate(S):
    inp+=['-i',f's{i+1}.mp3']; ms=int(s*1000); flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inp+=['-i','music.wav','-i','sfx.wav']; k=len(S)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0,apad[voice]')
flt.append(f'[voice]asplit=2[vo][sc];[{k}:a][sc]sidechaincompress=threshold=0.05:ratio=5:attack=20:release=300[duck];[vo][duck][{k+1}:a]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k','audio.m4a'],check=True)
print('ok')
