import json, subprocess
scenes=[]; t=0.0; N=10
for i in range(1,N+1):
    f=f's{i}_t.wav'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur,3)+.38
    if i==N: dur+=1.4
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('catorce','14'),('cuatro','4'),('cuarenta','40'),('ochenta y seis','86')]
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
ev={'S':S,'votar':W(0,'votar'),'cambiar':W(0,'cambiar'),'congreso':W(0,'congreso'),'lunes':W(0,'lunes'),
 'l1':W(1,'electoral',0),'l2':W(1,'procesal'),'l3':W(1,'política'),'l4':W(1,'código'),
 'n40':W(2,'cuarenta'),
 'soc':W(3,'sociedad'),'pnud':W(3,'pnud'),
 'trep':W(4,'trep'),'prelim':W(4,'preliminares'),'noche':W(4,'noche'),
 'ext':W(5,'extranjera'),'cne':W(5,'cne'),
 'resume':W(6,'resume'),'mismos':W(6,'mismos'),'tendremos':W(6,'tendremos'),
 'sv':W(7,'segunda'),'n86':W(7,'ochenta'),'dict':W(7,'dictamen'),'cual':W(7,'cualquier'),'mocion':W(7,'moción'),
 'presu':W(8,'presupuesto'),'agit':W(8,'agitada'),
 'quer':W(9,'querés'),'cta':W(9,'comentá')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
