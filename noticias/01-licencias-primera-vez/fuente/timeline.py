import json, subprocess, os
scenes=[]; t=0.0
N=9
for i in range(1,N+1):
    f=f's{i}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur-0.15,3)+ (0.35 if i in (1,5) else 0.1)
    if i==N: dur+=2.0
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
def W(si,pre,k=0):
    m=[w for w in scenes[si]['words'] if w[2].lower().startswith(pre)]
    return m[k][0]
S=[s['start'] for s in scenes]
ev={'S':S,
 'ojo':W(0,'ojo'),
 'nov':W(1,'treinta'),'solo':W(1,'solo'),'tgu':W(1,'tegucigalpa'),'sps':W(1,'pedro'),
 'renov':W(2,'renovaciones'),'brig':W(2,'brigadas'),
 'razon':S[3],'r1':W(3,'demasiadas'),'r2':W(3,'poco'),'r3':W(3,'denuncias'),
 'pero':S[4],'contra':W(4,'contrario'),
 'pn':W(5,'nacional'),'pl':W(5,'liberal'),'lb':W(5,'libre'),'todos':W(5,'todos'),
 'zam':W(6,'tomás'),'mocion':W(6,'moción'),'tr':W(6,'tránsito'),'po':W(6,'policía'),'se':W(6,'seguridad'),
 'c1':W(7,'rápido'),'c2':W(7,'cerca'),'c3':W(7,'cobros'),
 'v1':W(8,'dos'),'v2':W(8,'todo'),'cta':W(8,'comentá'),
}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print(ev)
