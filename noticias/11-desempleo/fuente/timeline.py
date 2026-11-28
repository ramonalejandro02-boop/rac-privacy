import json, subprocess
scenes=[]; t=0.0; N=10
for i in range(1,N+1):
    f=f's{i}_t.wav'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur,3)+.38
    if i==N: dur+=1.6
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('dos mil veinticinco','2025'),('dos mil veintiséis','2026'),('doscientas once mil','211,000'),('doscientas noventa mil','290,000'),('setenta y nueve mil','79,000'),('treinta y siete punto seis por ciento','37.6%'),('fosdeh','FOSDEH')]
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
ev={'S':S,'trab':W(0,'trabajo'),
 'y25':W(1,'dos',0),'n211':W(1,'doscientas',0),'y26':W(1,'dos',2),'n290':W(1,'doscientas',1),
 'n79':W(2,'setenta'),'pct':W(2,'treinta'),'ine':W(2,'ine'),
 'hogar':W(3,'hogar'),'ingr':W(3,'ingresos'),
 'fos':W(4,'fosdeh'),'cierre':W(4,'cierre'),'comb':W(4,'combustibles'),'costos':W(4,'costos'),
 'agri':W(5,'agricultura'),'manu':W(5,'manufactura'),
 'acad':W(6,'academia'),'plan':W(6,'plan'),'venc':W(6,'venció'),'nuevo':W(6,'nuevo'),
 'gob':W(7,'gobierno'),'prod':W(7,'productividad'),'corr':W(7,'corredores'),'infra':W(7,'infraestructura'),'seg':W(7,'seguridad'),'inv':W(7,'inversión'),
 'reto':W(8,'reto'),'empl':W(8,'empleos'),
 'alguien':W(9,'alguien'),'busc':W(9,'buscando')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
