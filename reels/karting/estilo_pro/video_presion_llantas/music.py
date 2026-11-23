import json,numpy as np,wave,subprocess
SR=48000;T=json.load(open('/tmp/k13/timing.json'));S=T['scenes'];N=int((T['total']+0.3)*SR);rng=np.random.default_rng(3)
def env(n,a=0.003,d=0.2):x=np.arange(n)/SR;return np.minimum(1,x/a)*np.exp(-x/d)
def put(b,t0,s):
    i=int(t0*SR);j=min(N,i+len(s))
    if 0<=i<N:b[i:j]+=s[:j-i]
mus=np.zeros(N);bpm=100;beat=60/bpm
chords=[[220,261.6,329.6,392],[174.6,220,261.6,329.6],[196,246.9,293.7,392],[164.8,196,246.9,329.6]]
bass=[55,43.65,49,41.2]
for b in range(int(T['total']/beat)+2):
    tb=b*beat;bar=(b//4)%4;n=int(0.35*SR);x=np.arange(n)/SR
    if b%4 in (0,2): put(mus,tb,0.45*np.sin(2*np.pi*(45+60*np.exp(-x*30))*x)*env(n,0.002,0.2))   # soft kick
    if b%4 in (1,3): put(mus,tb,0.10*rng.standard_normal(n)*env(n,0.002,0.05))                   # soft snap
    m=int(0.03*SR);put(mus,tb+0.5*beat,0.035*np.diff(np.r_[0,rng.standard_normal(m)])*env(m,0.001,0.012))
    if b%4==0:
        m=int(beat*4*SR);xx=np.arange(m)/SR;pad=sum(np.sin(2*np.pi*f*xx)*(0.8+0.2*np.sin(2*np.pi*0.3*xx))+0.25*np.sin(2*np.pi*f*2.002*xx) for f in chords[bar])
        put(mus,tb,0.03*pad*np.minimum(1,xx/0.8)*np.minimum(1,(beat*4-xx)/0.6))
        m2=int(beat*4*SR);put(mus,tb,0.12*np.sin(2*np.pi*bass[bar]*np.arange(m2)/SR)*np.minimum(1,np.arange(m2)/SR/0.05)*np.exp(-np.arange(m2)/SR/2.5))
    # gentle pluck arpeggio
    f=chords[bar][b%4]*2;m=int(0.5*SR);xx=np.arange(m)/SR;put(mus,tb+0.25*beat,0.035*np.sin(2*np.pi*f*xx)*np.exp(-xx*6))
mus=np.convolve(mus,np.ones(5)/5,'same')
von=np.zeros(N)
for s in S:
    for w in s['words']:von[int(w['s']*SR):int(w['e']*SR)]=1
k=int(0.25*SR);mus*=1-0.5*np.clip(np.convolve(von,np.ones(k)/k,'same'),0,1)
sfx=np.zeros(N)
def whoosh(t0,amp=0.22,d=0.6):n=int(d*SR);x=rng.standard_normal(n);x=np.convolve(x,np.ones(30)/30,'same');put(sfx,t0,amp*x*np.sin(np.pi*np.arange(n)/n)**2)
for i in range(1,6):whoosh(S[i]['start']-0.55)
fade=np.minimum(1,np.arange(N)/SR/0.8)*np.minimum(1,(N/SR-np.arange(N)/SR)/1.5)
out=np.clip((mus*0.7+sfx)*fade,-1,1)
with wave.open('/tmp/k13/bed.wav','wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((out*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i','/tmp/k13/out.mp4','-i','/tmp/k13/voz.wav','-i','/tmp/k13/bed.wav','-filter_complex','[2:a]aformat=channel_layouts=stereo,volume=0.85[b];[1:a][b]amix=inputs=2:normalize=0,alimiter=limit=0.95[o]','-map','0:v','-map','[o]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','/tmp/k13/final.mp4'],check=True)
print('ok')
