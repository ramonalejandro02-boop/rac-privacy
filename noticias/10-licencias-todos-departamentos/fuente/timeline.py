import json, subprocess
scenes=[]; t=0.0; N=8
for i in range(1,N+1):
    f=f's{i}_t.wav'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur,3)+.38
    if i==N: dur+=1.4
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
for sc in scenes: sc['sub']=sc['words']
def W(si,pre,k=0): return [w for w in scenes[si]['words'] if w[2].lower().startswith(pre)][k][0]
S=[s['start'] for s in scenes]
ev={'S':S,'lic':W(0,'licencia'),'buenas':W(0,'buenas'),
 'renov':W(1,'renovación'),'todas':W(1,'todas'),'cab':W(1,'cabeceras'),
 'min':W(2,'ministro'),'gen':W(2,'gerzon'),
 'pol':W(3,'policía'),'sup':W(3,'supervisión'),'cert':W(3,'certificación'),'pers':W(3,'personal'),
 'obj':W(4,'objetivo'),'err':W(4,'erradicar'),'corr':W(4,'corrupción'),'hist':W(4,'históricamente'),
 'modelo':W(5,'modelo'),'prac':W(5,'prácticas'),'acc':W(5,'acceso'),'aten':W(5,'atención'),'susp':W(5,'suspensiones'),
 'prop':W(6,'propuesta'),'ley':W(6,'ley'),'cong':W(6,'congreso'),
 'exp':W(7,'historia'),'cta':W(7,'licencia')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
