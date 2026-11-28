import json, subprocess
scenes=[]; t=0.0; N=10
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
MERGE=[('sesenta y cinco por ciento','65%'),('diez por ciento','10%'),('nueve por ciento','9%'),('seis mil millones','6 mil millones'),('seis','6'),('asj','ASJ')]
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
ev={'S':S,'recibo':W(0,'recibo'),'aprieta':W(0,'aprieta'),'vence':W(0,'vencimiento'),
 'congel':W(1,'congelamiento'),'termina':W(1,'termina'),'marzo':W(1,'marzo'),
 'presidente':W(2,'presidente'),'ajuste':W(2,'ajuste'),'inevitable':W(2,'inevitable'),'abril':W(2,'abril'),
 'ampliar':W(3,'ampliar'),'subsidiar':W(3,'subsidiar'),'gobierno':W(3,'gobierno'),
 'alivio':W(4,'alivio'),'parejo':W(4,'parejo'),'diez':W(4,'diez'),'sesenta':W(4,'sesenta'),
 'mitad':W(5,'mitad'),'apenas':W(5,'apenas'),'nueve':W(5,'nueve'),
 'cuesta':W(6,'cuesta'),'seis':W(6,'seis'),'meses':W(6,'meses'),'claramente':W(6,'claramente'),'paga':W(6,'paga'),
 'hoy':W(7,'hoy'),'recibo2':W(7,'recibo'),'despues':W(7,'después'),'intereses':W(7,'intereses'),
 'cuanto':W(8,'cuánto'),'quien':W(8,'quién'),'nadie':W(8,'nadie'),
 'casa':W(9,'casa'),'apagan':W(9,'apagan'),'focos':W(9,'focos'),'abril2':W(9,'abril'),'cuantos':W(9,'cuántos')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
