import json,subprocess,numpy as np
from faster_whisper import WhisperModel
m=WhisperModel('small',device='cpu',compute_type='int8')
L=json.load(open('lines.json'))
GAPS=[0.55,0.5,0.55,0.5,0.55,0.3];t0=0.5;scenes=[];parts=[]
for i,txt in enumerate(L):
    subprocess.run(['ffmpeg','-v','error','-y','-i',f'vo/{i+1}.wav','-af','silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,apad=pad_dur=0.05','-ar','48000',f'vo/t{i+1}.wav'],check=True)
    a=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',f'vo/t{i+1}.wav','-ar','16000','-ac','1','-f','f32le','-'],capture_output=True).stdout,dtype=np.float32);dur=len(a)/16000
    segs,_=m.transcribe(a,language='es',word_timestamps=True);ww=[w for s in segs for w in s.words];sw=txt.split()
    print(i+1,round(dur,2),len(ww),len(sw))
    if len(ww)==len(sw): times=[(w.start,w.end) for w in ww]
    else:
        st=ww[0].start;en=ww[-1].end;L2=[len(x) for x in sw];c=np.cumsum([0]+L2)/sum(L2);times=[(st+c[q]*(en-st),st+c[q+1]*(en-st)) for q in range(len(sw))]
    scenes.append({'start':round(t0,3),'end':round(t0+dur,3),'words':[{'w':w,'s':round(t0+x,3),'e':round(t0+y,3)} for w,(x,y) in zip(sw,times)]})
    parts.append((t0,i+1));t0+=dur+GAPS[i]
total=t0+2.2
json.dump({'scenes':scenes,'total':round(total,3)},open('timing.json','w'),ensure_ascii=False)
inputs=[];flt=[]
for q,(st,n) in enumerate(parts):
    inputs+=['-i',f'vo/t{n}.wav'];flt.append(f'[{q}:a]adelay={int(st*1000)}|{int(st*1000)}[a{q}]')
flt.append(''.join(f'[a{q}]' for q in range(len(parts)))+f'amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-15:TP=-1.5[o]')
subprocess.run(['ffmpeg','-v','error','-y',*inputs,'-filter_complex',';'.join(flt),'-map','[o]','-ar','48000','-ac','2','voz.wav'],check=True)
print('total',total);[print(s['start'],s['end']) for s in scenes]
