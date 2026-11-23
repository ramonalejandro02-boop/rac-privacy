import json,numpy as np,wave,subprocess
SR=48000;T=json.load(open('/tmp/k12/timing.json'));S=T['scenes'];N=int((T['total']+0.3)*SR);rng=np.random.default_rng(11)
def wT(k,p):
    ws=[w for w in S[k]['words'] if w['w'].lower().strip('¡!¿?,.:…').startswith(p)];return ws[0]['s'] if ws else None
def env(n,a=0.003,d=0.2):x=np.arange(n)/SR;return np.minimum(1,x/a)*np.exp(-x/d)
def put(b,t0,s):
    i=int(t0*SR);j=min(N,i+len(s))
    if 0<=i<N:b[i:j]+=s[:j-i]
mus=np.zeros(N);bpm=128;beat=60/bpm
bassn=[49.0,49.0,41.2,43.65];chords=[[196,233.1,293.7],[196,233.1,293.7],[164.8,207.7,246.9],[174.6,220,261.6]]
for b in range(int(T['total']/beat)+1):
    tb=b*beat;bar=(b//4)%4;n=int(0.3*SR);x=np.arange(n)/SR
    put(mus,tb,0.7*np.sin(2*np.pi*(46+120*np.exp(-x*38))*x)*env(n,0.001,0.15))
    if b%2==1: put(mus,tb,0.26*rng.standard_normal(n)*env(n,0.001,0.07)+0.14*np.sin(2*np.pi*200*x)*env(n,0.001,0.05))
    m=int(0.04*SR);put(mus,tb+0.5*beat,0.07*np.diff(np.r_[0,rng.standard_normal(m)])*env(m,0.001,0.015))
    m=int(beat*SR*0.95);xx=np.arange(m)/SR;f=bassn[bar];saw=2*((f*xx)%1)-1;put(mus,tb,0.15*np.tanh(2.2*saw)*env(m,0.005,0.3))
    if b%4==0:
        m=int(beat*4*SR);xx=np.arange(m)/SR;pad=sum(np.sin(2*np.pi*fr*xx)+0.3*np.sin(2*np.pi*fr*2.003*xx) for fr in chords[bar]);put(mus,tb,0.03*pad*np.minimum(1,xx/0.4)*np.exp(-xx/3))
mus=np.convolve(mus,np.ones(3)/3,'same')
von=np.zeros(N)
for s in S:
    for w in s['words']:von[int(w['s']*SR):int(w['e']*SR)]=1
k=int(0.2*SR);mus*=1-0.55*np.clip(np.convolve(von,np.ones(k)/k,'same'),0,1)
sfx=np.zeros(N)
def whoosh(t0,amp=0.4,d=0.55):n=int(d*SR);x=rng.standard_normal(n);x=np.convolve(x,np.ones(12)/12,'same');put(sfx,t0,amp*x*np.sin(np.pi*np.arange(n)/n)**2)
def hit(t0,amp=0.6):n=int(0.8*SR);x=np.arange(n)/SR;put(sfx,t0,amp*(np.sin(2*np.pi*(60-25*x)*x)*env(n,0.001,0.35)+0.3*rng.standard_normal(n)*env(n,0.001,0.04)))
def tick(t0,amp=0.22,f=2200):n=int(0.06*SR);x=np.arange(n)/SR;put(sfx,t0,amp*np.sin(2*np.pi*f*x)*env(n,0.001,0.015))
def screech(t0,d,amp=0.12):n=int(d*SR);x=np.arange(n)/SR;f=2400+300*np.sin(2*np.pi*7*x);put(sfx,t0,amp*np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*np.arange(n)/n)*(0.6+0.4*rng.random(n)))
t=np.arange(N)/SR;eng=np.zeros(N)
for a,b_ in [(0,4.4),(wT(3,'dobla')-0.3,wT(3,'dobla')+2.5),(S[5]['start']-0.3,S[5]['start']+3)]:
    msk=(t>=a)&(t<b_);f=190+40*np.sin(2*np.pi*0.7*(t-a));ph=2*np.pi*np.cumsum(np.where(msk,f,0))/SR;eng+=np.where(msk,0.07*np.sign(np.sin(ph))*np.minimum(1,(t-a)/0.2)*np.minimum(1,(b_-t)/0.3),0)
eng=np.convolve(eng,np.ones(8)/8,'same')
hit(0.0,0.55);screech(0.3,1.2)
for i in range(1,6):c=S[i]['start']-0.3;whoosh(c-0.35);hit(c,0.45)
for k_,p in [(0,'diferencial'),(0,'suspensión'),(1,'eje'),(1,'llantas'),(1,'velocidad'),(2,'afuera'),(2,'adentro'),(3,'flexiona'),(3,'levanta'),(4,'suspensión'),(4,'rígido'),(5,'sigue')]:
    v=wT(k_,p)
    if v:tick(v-0.12)
hit(wT(0,'cómo')-0.1,0.8);v=wT(2,'arrastra');screech(v-0.3,1.5,0.15);v=wT(3,'dobla');hit(v-0.3,0.7)
out=np.clip(mus*0.6+sfx+eng,-1,1)
with wave.open('/tmp/k12/bed.wav','wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((out*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i','/tmp/k12/out.mp4','-i','/tmp/k12/voz.wav','-i','/tmp/k12/bed.wav','-filter_complex','[2:a]aformat=channel_layouts=stereo,volume=0.8[b];[1:a][b]amix=inputs=2:normalize=0,alimiter=limit=0.95[o]','-map','0:v','-map','[o]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','/tmp/k12/final3.mp4'],check=True)
print('ok')
