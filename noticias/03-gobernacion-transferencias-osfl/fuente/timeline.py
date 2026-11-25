import json, subprocess
scenes=[]; t=0.0; N=12
for i in range(1,N+1):
    f=f's{i}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur-0.15,3)+(0.3 if i in (1,4,8) else 0.1)
    if i==N: dur+=2.0
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('dos mil veintiséis','2026'),('doscientos noventa punto siete','290.7'),('doscientos treinta y seis punto siete','236.7'),
 ('ciento cincuenta y seis punto un','156.1'),('sesenta y seis por ciento','66%'),('ciento diez','110'),('siete de cada diez','7 DE CADA 10'),
 ('cuarenta y nueve punto siete','49.7'),('un millón y medio','1.5 MILLONES'),('ochenta punto seis','80.6'),('dos millones','2 MILLONES'),
 ('veintiún','21'),('veinte','20'),('doce','12'),('once','11'),('nueve','9'),('catorce','14'),('veintidós','22'),('tres','3'),('cuatro','4')]
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
ev={'S':S,'gob':W(0,'gobernación'),'inf':W(0,'informe'),
 'apr':W(1,'doscientos'),'transf':W(1,'transferencias'),
 'bajo':W(2,'bajó'),'n236':W(2,'doscientos'),
 'ejec':W(3,'ejecutado'),'n156':W(3,'ciento'),'pct':W(3,'sesenta'),
 'n21':W(4,'veintiún'),
 'fcm':W(5,'fundación'),'n20':W(5,'veinte'),
 'tres':W(6,'tres'),'doce':W(6,'doce'),'cuatro':W(6,'cuatro'),'once':W(6,'once'),
 'n110':W(7,'ciento'),'siete':W(7,'siete'),
 'n14':S[8],'orig':W(8,'original'),'agreg':W(8,'agregaron'),'n49':W(8,'cuarenta'),
 'grupo':W(9,'grupo'),'iglesia':W(9,'iglesia'),
 'n22':S[10],'n80':W(10,'ochenta'),
 'bien':W(11,'bien'),'cta':W(11,'comentá')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print(ev)
print([w[2] for sc in scenes for w in sc['sub']])
