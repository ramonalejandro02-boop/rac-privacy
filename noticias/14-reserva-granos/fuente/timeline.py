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
MERGE=[('ochenta y cuatro mil','84 mil'),('mil','1,000')]
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
ev={'S':S,'frijoles':W(0,'frijoles'),'maiz':W(0,'maíz'),'mesa':W(0,'mesa'),'nino':W(0,'niño'),'escasos':W(0,'escasos'),
 'instituto':W(1,'instituto'),'blindo':W(1,'blindó'),'reserva':W(1,'reserva'),'granos':W(1,'granos'),
 'ochenta':W(2,'ochenta'),'bodegas':W(2,'bodegas'),'escasez':W(2,'escasez'),'espec':W(2,'especulación'),
 'envio':W(3,'envió'),'frijol':W(3,'frijol'),'banasupro':W(3,'banasupro'),'alzas':W(3,'alzas'),
 'mercados':W(4,'mercados'),'cosecha':W(4,'cosecha'),'ahora':W(4,'ahora'),'noesc':W(4,'escasez'),
 'sirve':W(5,'sirve'),'tiempo':W(5,'tiempo'),'semanas':W(5,'semanas'),'precio':W(5,'precio'),
 'gobierno':W(6,'gobierno'),'promete':W(6,'promete'),'robusta':W(6,'robusta'),'cuenta':W(6,'cuenta'),'sale':W(6,'sale'),'mercado':W(6,'mercado'),
 'guarda':W(7,'guarda'),'mide':W(7,'mide'),'libra':W(7,'libra'),'frijoles2':W(7,'frijoles')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
