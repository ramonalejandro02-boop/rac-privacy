import json, subprocess
scenes=[]; t=0.0; N=9
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
MERGE=[('dos mil ochocientos','2,800'),('dos mil veintisiete','2027'),('un millón treinta mil','1,030,000'),('treinta','30'),('veintisiete millones','27 millones')]
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
ev={'S':S,'milpa':W(0,'milpa'),'lluvia':W(0,'lluvia'),'aviones':W(0,'aviones'),
 'secretaria':W(1,'secretaría'),'termino':W(1,'terminó'),'treinta':W(1,'treinta'),'vuelos':W(1,'vuelos'),'dosmil':W(1,'dos'),'yoduro':W(1,'yoduro'),
 'costo':W(2,'costó'),'millon':W(2,'millón'),'dolares':W(2,'dólares'),'veintisiete':W(2,'veintisiete'),
 'autoridades':W(3,'autoridades'),'posible':W(3,'posible'),'medir':W(3,'medir'),'tecnica':W(3,'técnica'),
 'crisis':W(4,'crisis'),'cedio':W(4,'cedió'),
 'compro':W(5,'compró'),'cosechas':W(5,'cosechas'),'sin':W(5,'sin'),'saberlo':W(5,'saberlo'),
 'repetirse':W(6,'repetirse'),'y27':W(6,'dos'),'expertos':W(6,'expertos'),'sequia':W(6,'sequía'),'empeorar':W(6,'empeorar'),
 'repetir':W(7,'repetir'),'mida':W(7,'mida'),
 'siembra':W(8,'siembra'),'cielo':W(8,'cielo'),'tal':W(8,'tal'),'vez':W(8,'vez')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
