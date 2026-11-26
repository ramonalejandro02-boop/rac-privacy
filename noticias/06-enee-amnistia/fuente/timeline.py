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
MERGE=[('veintinueve','29'),('enée','ENEE')]
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
ev={'S':S,'luz':W(0,'luz'),'enee':W(0,'enée'),'d29':W(0,'veintinueve'),'dic':W(0,'diciembre'),
 'ley':W(1,'ley'),'amn':W(1,'amnistía'),'recargos':W(1,'recargos'),'nadie':W(1,'nadie'),
 'sind':W(2,'sindicato'),'pocas':W(2,'pocas'),
 'vas':W(3,'vas'),'fecha':W(3,'fecha'),'plan':W(3,'plan'),'agres':W(3,'agresivo'),'perd':W(3,'pérdidas'),
 'ajuste':W(4,'ajuste'),'consum':W(4,'consumidor'),'vos':W(4,'vos'),
 'ofic':W(5,'oficinas'),'resolv':W(5,'resolvás'),'saldo':W(5,'saldo'),
 'gob':W(6,'gobierno'),'lugar':W(6,'lugar'),'reforma':W(6,'reforma'),'licit':W(6,'licitaciones'),'demanda':W(6,'demanda'),'prox':W(6,'próximo'),
 'deuda':W(7,'deuda'),'cta':W(7,'comentá')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
