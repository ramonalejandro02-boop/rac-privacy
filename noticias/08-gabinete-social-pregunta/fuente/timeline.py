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
MERGE=[('dos mil veintisiete','2027'),('dos mil treinta y siete','2037'),('dos mil veintinueve','2029'),('doscientos noventa y ocho','298'),('diecinueve','19'),('dieciocho','18'),('veinticinco','25'),('diez','10')]
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
ev={'S':S,'ofic':W(0,'oficinas'),'asf':W(0,'nasry'),
 'gab':W(1,'gabinete'),'n19':W(1,'diecinueve'),'meta':W(1,'meta'),
 'sec':W(2,'secretaría'),'min':W(2,'fátima'),
 'pol':W(3,'política'),'d10':W(3,'diez'),'y27':W(3,'dos',0),'y37':W(3,'dos',1),'n25':W(3,'veinticinco'),'gar':W(3,'garantías'),
 'g1':W(3,'educación'),'g2':W(3,'salud'),'g3':W(3,'alimentación'),'g4':W(3,'ingresos'),'g5':W(3,'adultos'),'g6':W(3,'servicios'),'g7':W(3,'emergencias'),
 'ene':W(4,'enero'),'feb':W(4,'febrero'),'eval':W(4,'evaluación'),'y29':W(4,'dos'),
 'preg':W(5,'pregunta'),'salir':W(5,'salir'),'gente':W(5,'gente'),
 'n298':W(6,'doscientos'),'n18':W(6,'dieciocho'),'colores':W(6,'colores'),'llegar':W(6,'llegar'),'familia':W(6,'familia'),
 'vos':W(7,'vos'),'cta':W(7,'contalo')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
