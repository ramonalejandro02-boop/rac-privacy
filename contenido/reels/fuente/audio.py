import json,sys,os,subprocess,numpy as np,wave
d=sys.argv[1];tl=json.load(open(os.path.join(d,'timeline.json')));SR=48000;T=tl['total']+0.3
n=int(SR*T);t=np.arange(n)/SR
def note(f):return 440*2**((f-69)/12)
# music: soft pad Am - F - C - G, 2.4s per chord, plus gentle pulse
chords=[[57,60,64],[53,57,60],[48,55,64],[55,59,62]];mus=np.zeros(n)
cl=2.4
for k in range(int(T/cl)+1):
    a,b=int(k*cl*SR),min(n,int((k+1)*cl*SR))
    if a>=n:break
    tt=np.arange(b-a)/SR;env=np.minimum(1,tt/0.4)*np.minimum(1,(cl-tt)/0.4)
    for m in chords[k%4]:
        f=note(m);mus[a:b]+=env*(np.sin(2*np.pi*f*tt)+.3*np.sin(2*np.pi*2*f*tt)+.15*np.sin(2*np.pi*f/2*tt))
# pulse every 0.6s (soft kick)
for k in range(int(T/.6)):
    a=int(k*.6*SR);L=int(.25*SR);tt=np.arange(min(L,n-a))/SR
    mus[a:a+len(tt)]+=1.6*np.sin(2*np.pi*(55+60*np.exp(-tt*30))*tt)*np.exp(-tt*14)
mus=mus/np.abs(mus).max()*0.11
sfx=np.zeros(n)
def add(at,sig):
    a=int(at*SR);b=min(n,a+len(sig));sfx[a:b]+=sig[:b-a]
def coinsnd():
    tt=np.arange(int(.35*SR))/SR;return .35*(np.sin(2*np.pi*1975*tt)*np.exp(-tt*12)+np.sin(2*np.pi*2637*tt)*np.exp(-tt*9)*(tt>.06))
def whoosh():
    L=int(.3*SR);x=np.random.default_rng(1).standard_normal(L);x=np.convolve(x,np.ones(30)/30,'same');tt=np.arange(L)/L
    return .5*x*np.sin(np.pi*tt)**2
def pop():
    tt=np.arange(int(.15*SR))/SR;return .35*np.sin(2*np.pi*(600+900*tt/.15)*tt)*np.exp(-tt*25)
st=[s['start'] for s in tl['scenes']]
for s in st[1:]:add(s-.05,whoosh())
add(st[0]+1.6,pop());add(st[1]+2.6,pop());add(st[6]+2.4,pop());add(st[7],pop())
for x in [.4,1.3,2.2,3.1]:add(st[2]+x+.45,coinsnd())
for k in range(10):add(st[4]+.3+k*.35,coinsnd()*.5)
for k in range(6):add(st[5]+.2+k*.4,coinsnd()*.45)
def wav(name,x):
    x=np.clip(x,-1,1);w=wave.open(os.path.join(d,name),'wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes());w.close()
wav('music.wav',mus);wav('sfx.wav',sfx)
# voice
inputs=[];flt=[]
for i,s in enumerate(st):
    inputs+=['-i',os.path.join(d,f's{i+1}.mp3')];ms=int(s*1000);flt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]')
inputs+=['-i',os.path.join(d,'music.wav'),'-i',os.path.join(d,'sfx.wav')]
k=len(st)
flt.append(''.join(f'[v{i}]' for i in range(k))+f'amix=inputs={k}:normalize=0[voice]')
flt.append(f'[voice]asplit=2[vo][sc];[{k}:a][sc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[duck];[vo][duck][{k+1}:a]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inputs,'-filter_complex',';'.join(flt),'-map','[out]','-t',str(tl['total']),'-c:a','aac','-b:a','192k',os.path.join(d,'audio.m4a')],check=True)
print('ok')
