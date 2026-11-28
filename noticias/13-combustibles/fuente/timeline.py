import json, subprocess
scenes=[]; t=0.0; N=8
LINES=[l.strip() for l in open('lines.txt') if l.strip()]
for i in range(1,N+1):
    f=f's{i}_t.wav'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur,3)+.38
    if i==N: dur+=1.5
    w=json.load(open(f+'.json'))
    tok=LINES[i-1].split()
    if len(tok)==len(w): w=[[x[0],x[1],tk] for x,tk in zip(w,tok)]
    else: print('MISMATCH',i,len(tok),len(w))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('cinco','5')]
MERGE=[(m.split(),r) for m,r in MERGE]
for sc in scenes:
    sc['sub']=[]; ws=sc['words']; i=0
    while i<len(ws):
        for seq,rep in MERGE:
            if [w[2].lower().strip('.,;:?¿') for w in ws[i:i+len(seq)]]==seq:
                sc['sub'].append([ws[i][0],ws[i+len(seq)-1][1],rep]); i+=len(seq); break
        else: sc['sub'].append(ws[i]); i+=1
def W(si,w,k=0): return [x for x in scenes[si]['words'] if x[2].lower().strip('.,;:?¿')==w][k][0]
S=[s['start'] for s in scenes]
ev={'S':S,'bajo':W(0,'bajó'),'bus':W(0,'bus'),'comida':W(0,'comida'),
 'super':W(1,'súper'),'cinco':W(1,'cinco'),'tegus':W(1,'tegucigalpa'),'regular':W(1,'regular'),
 'diesel':W(2,'diésel'),'buses':W(2,'buses'),'camiones':W(2,'camiones'),'congelado':W(2,'congelado'),'subsidio':W(2,'subsidio'),
 'insp':W(3,'inspecciones'),'comprobar':W(3,'comprobar'),'transporte':W(3,'transporte'),'canasta':W(3,'canasta'),
 'precio':W(4,'precio'),'pesan':W(4,'pesan'),'otros':W(4,'otros'),'produccion':W(4,'producción'),
 'sube':W(5,'sube'),'enseguida':W(5,'enseguida'),'baja':W(5,'baja'),'rapido':W(5,'rápido'),
 'cuantos':W(6,'cuántos'),'cuando':W(6,'cuándo'),'resultados':W(6,'resultados'),
 'bomba':W(7,'bomba'),'falta':W(7,'falta'),'mesa':W(7,'mesa')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
