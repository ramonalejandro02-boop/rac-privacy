import json, subprocess
scenes=[]; t=0.0; N=9
PAD={1:.5,2:.3,3:.3,8:.5}
for i in range(1,N+1):
    f=f's{i}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur-0.15,3)+PAD.get(i,.15)
    if i==N: dur+=2.2
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('seis de cada diez','6 DE CADA 10'),('un millón setecientos mil','1,700,000'),('cuatro de cada diez','4 DE CADA 10'),
 ('dos mil treinta y seis','2036'),('veinte','20'),('diez','10')]
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
ev={'S':S,'hog':W(0,'hogares'),'pob':W(0,'pobreza'),
 'mill':W(1,'millón'),'casi':W(1,'casi'),'ext':W(1,'extrema'),
 'asf':W(2,'nasry'),'firmar':W(2,'firmar'),'gab':W(2,'gabinete'),
 'n20':S[3],'mesa':W(3,'mesa'),'obj':W(3,'objetivo'),'prot':W(3,'proteger'),'red':W(3,'reducir'),
 'sec':W(4,'secretaría'),'min':W(4,'ministra'),
 'cada':S[5],'comp':W(5,'compromiso'),'conj':W(5,'conjunto'),
 'pol':W(6,'política'),'plan':W(6,'plan'),'d10':W(6,'diez'),'y36':W(6,'dos'),
 'preg':S[7],'casa':W(7,'casa'),'papel':W(7,'papel'),
 'cta':S[8],'prim':W(8,'primero')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print(ev)
