import json, subprocess, wave, numpy as np
tl=json.load(open('timeline.json')); ev=tl['ev']; S=ev['S']
SR=48000; T=tl['total']+.3; n=int(SR*T); rng=np.random.default_rng(7)
def f(m): return 440*2**((m-69)/12)
def put(buf,at,sig,gn=1.0):
    a=int(at*SR); b=min(n,a+len(sig))
    if 0<=a<n: buf[a:b]+=gn*sig[:b-a]
def tt(L): return np.arange(int(L*SR))/SR
mus=np.zeros(n)
beat=60/110; step=beat/4; prog=[[45,52,57,60],[41,48,53,57],[43,50,55,59],[40,47,52,55]]
t=0;i=0
while t<T:
    ch=prog[(i//32)%4]
    if i%2==0:
        nt=ch[(i//2)%4]+12; x=tt(.18); put(mus,t,np.sin(2*np.pi*f(nt)*x)*np.exp(-x*22),.28)
    if i%8==0:
        x=tt(.2); put(mus,t,np.sin(2*np.pi*(48+100*np.exp(-x*35))*x)*np.exp(-x*16),.8)
    if i%8==4:
        L=int(.12*SR); put(mus,t,rng.uniform(-1,1,L)*np.exp(-np.arange(L)/SR*35),.12)
    if i%2==1:
        L=int(.03*SR); put(mus,t,rng.uniform(-1,1,L)*np.exp(-np.arange(L)/SR*150),.06)
    if i%32==0:
        L=beat*8; x=tt(L); env=np.minimum(1,x/1.)*np.minimum(1,(L-x)/1.)
        for m in ch[:3]: put(mus,t,(np.sin(2*np.pi*f(m-12)*x)+.5*np.sin(2*np.pi*f(m-12)*1.005*x))*env,.07)
        x=tt(beat*8); put(mus,t,np.sin(2*np.pi*f(ch[0]-24)*x)*np.minimum(1,x/.05)*np.exp(-x*.3),.25)
    i+=1; t+=step
mus=mus/np.abs(mus).max()*.11
sfx=np.zeros(n)
def whoosh(L=.4):
    x=rng.uniform(-1,1,int(L*SR)); e=np.sin(np.linspace(0,np.pi,len(x)))**2; return np.convolve(x,np.ones(24)/24,'same')*e*.5
def pop(fr=900):
    x=tt(.12); return np.sin(2*np.pi*(fr+600*np.exp(-x*40))*x)*np.exp(-x*30)*.35
def ding(fr=1318):
    x=tt(.6); return (np.sin(2*np.pi*fr*x)+.4*np.sin(2*np.pi*fr*2.01*x))*np.exp(-x*6)*.22
def boom():
    x=tt(.8); return np.sin(2*np.pi*(40+50*np.exp(-x*8))*x)*np.exp(-x*4)*.9
def tick():
    x=tt(.02); return np.sin(2*np.pi*3000*x)*np.exp(-x*300)*.25
for s in S[1:]: put(sfx,s-.08,whoosh())
put(sfx,.15,whoosh(.5))
put(sfx,ev['gob'],pop()); put(sfx,ev['inf'],pop(700))
a=ev['apr']
for j in range(30): put(sfx,a+1.8*(j/30)**1.6,tick())
put(sfx,a+1.8,boom()); put(sfx,a+1.8,ding(1568)); put(sfx,ev['transf'],pop(800))
put(sfx,ev['bajo'],whoosh(.5)); put(sfx,ev['bajo'],boom())
for j in range(20): put(sfx,ev['n236']+1.3*(j/20)**1.3,tick(),.7)
put(sfx,ev['n236']+1.3,pop(500))
for j in range(30): put(sfx,ev['ejec']+2.6*(j/30)**1.2,tick(),.6)
put(sfx,ev['pct'],ding(1318))
for j in range(21): put(sfx,ev['n21']-.6+1.4*(j/21)**.9,pop(1200),.5)
put(sfx,ev['fcm'],boom()); put(sfx,ev['n20'],ding(1568))
for x in ('tres','cuatro','once'): put(sfx,ev[x],pop(900))
put(sfx,ev['n110'],boom())
for i in range(10): put(sfx,ev['siete']+i*.08,pop(1000 if i<7 else 600),.6)
put(sfx,ev['n14'],boom()); put(sfx,ev['orig'],pop())
for i in range(14): put(sfx,ev['agreg']-.3+i*.09,tick(),.8)
put(sfx,ev['n49'],ding(1318))
put(sfx,ev['grupo'],pop()); put(sfx,ev['iglesia'],pop(1100))
put(sfx,ev['n22'],boom()); put(sfx,ev['n80'],ding(880))
put(sfx,ev['bien'],pop()); put(sfx,ev['bien']+.2,pop(1100)); put(sfx,ev['cta'],ding(1046)); put(sfx,ev['cta']+.12,ding(1568))
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
