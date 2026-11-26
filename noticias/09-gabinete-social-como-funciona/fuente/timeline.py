import json, subprocess
scenes=[]; t=0.0; N=9
for i in range(1,N+1):
    f=f's{i}_t.wav'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur,3)+.38+(.4 if i==4 else 0)
    if i==N: dur+=1.4
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('diez','10'),('diecinueve','19'),('cuatro','4'),('dos','2'),('cinco','5')]
MERGE=[(m.split(),r) for m,r in MERGE]
for sc in scenes:
    sc['sub']=[]; ws=sc['words']; i=0
    while i<len(ws):
        for seq,rep in MERGE:
            if [w[2].lower() for w in ws[i:i+len(seq)]]==seq:
                sc['sub'].append([ws[i][0],ws[i+len(seq)-1][1],rep]); i+=len(seq); break
        else: sc['sub'].append(ws[i]); i+=1
def W(si,pre,k=0): return [w for w in scenes[si]['words'] if w[2].lower().startswith(pre)][k][0]
S=[s['start'] for s in scenes]
ev={'S':S,'gab':W(0,'gabinete'),'min':W(0,'fátima'),
 'nov':W(1,'noviembre'),'n19':W(1,'diecinueve'),
 'e1':W(2,'bienestar'),'e2':W(2,'capital'),'e3':W(2,'ingresos'),'e4':W(2,'servicios'),
 'seq':W(3,'sequía'),
 'racion':W(4,'ración'),'meses':W(4,'meses'),'fam5':W(4,'cinco'),
 'agri':W(5,'agricultura'),'sembrar':W(5,'sembrar'),'cop':W(5,'copeco'),'edu':W(5,'educación'),'salud':W(5,'salud'),
 'misma':W(6,'misma'),'integral':W(6,'integral'),
 'pol':W(7,'política'),'prox':W(7,'próximo'),
 'llego':W(8,'llegó'),'cta':W(8,'comentá')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
