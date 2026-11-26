# Recorta silencios de cada sN.mp3 -> sN_t.wav y reajusta los tiempos de palabras -> sN_t.wav.json
import sys, json, subprocess, wave, numpy as np
SR=48000; MAXGAP=.09; EDGE=.03
def load(f):
    raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar',str(SR),'-f','s16le','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,np.int16).astype(np.float32)/32768
def tighten(i):
    a=load(f's{i}.mp3'); words=json.load(open(f's{i}.mp3.json'))
    fr=int(.01*SR); n=len(a)//fr; e=np.array([np.sqrt(np.mean(a[j*fr:(j+1)*fr]**2)+1e-12) for j in range(n)])
    db=20*np.log10(e); loud=db>db.max()-38
    # silent runs
    keep=[]; j=0; segs=[]
    while j<n:
        if not loud[j]:
            k=j
            while k<n and not loud[k]: k+=1
            segs.append((j,k)); j=k
        else: j+=1
    # build cut list (start,end) in seconds to remove
    cuts=[]
    for s,k in segs:
        t0,t1=s*.01,k*.01
        if s==0: cuts.append((0,max(0,t1-EDGE)))
        elif k>=n: cuts.append((t0+EDGE,len(a)/SR))
        elif t1-t0>MAXGAP: m=(t0+t1)/2; cuts.append((m-(t1-t0-MAXGAP)/2,m+(t1-t0-MAXGAP)/2))
    def remap(t):
        sh=0
        for c0,c1 in cuts:
            if t>=c1: sh+=c1-c0
            elif t>c0: sh+=t-c0
        return t-sh
    out=[];prev=0
    for c0,c1 in cuts:
        out.append(a[int(prev*SR):int(c0*SR)]); prev=c1
    out.append(a[int(prev*SR):]); b=np.concatenate(out)
    # short fades at joins are implicit; apply tiny fade in/out
    f=int(.005*SR); b[:f]*=np.linspace(0,1,f); b[-f:]*=np.linspace(1,0,f)
    w=wave.open(f's{i}_t.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(b,-1,1)*32767).astype('<i2').tobytes()); w.close()
    nw=[(remap(o),max(.05,remap(o+d)-remap(o)),x) for o,d,x in words]
    json.dump(nw,open(f's{i}_t.wav.json','w'),ensure_ascii=False)
    return len(a)/SR,len(b)/SR
N=int(sys.argv[1])
for i in range(1,N+1):
    o,nn=tighten(i); print(f's{i}: {o:.2f}s -> {nn:.2f}s')
