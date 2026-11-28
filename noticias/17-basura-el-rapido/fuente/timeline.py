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
MERGE=[('veinte','20'),('mil cien','1,100'),('dos mil veintidós','2022')]
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
ev={'S':S,'comida':W(0,'comida'),'casa':W(0,'casa'),'amanece':W(0,'amanece'),
 'cerro':W(1,'cerro'),'basura':W(1,'basura'),'rapido':W(1,'rápido'),'sps':W(1,'san'),
 'rutina':W(2,'rutina'),
 'vendedoras':W(3,'vendedoras'),'veinte':W(3,'veinte'),'olores':W(3,'olores'),'aguas':W(3,'aguas'),
 'medicos':W(4,'médicos'),'mosquitos':W(4,'mosquitos'),'roedores':W(4,'roedores'),'enferma':W(4,'enferma'),'ninos':W(4,'niños'),
 'muni':W(5,'municipalidad'),'mil':W(5,'mil'),'toneladas':W(5,'toneladas'),'dia':W(5,'día'),
 'camion':W(6,'camión'),'quien':W(6,'quién'),'responde':W(6,'responde'),
 'autoridades':W(7,'autoridades'),'empresa':W(7,'empresa'),'tira':W(7,'tira'),'calle':W(7,'calle'),'pasan':W(7,'pasan'),'crece':W(7,'crece'),
 'quejas':W(8,'quejas'),'desde':W(8,'desde'),
 'comida2':W(9,'comida'),'deberias':W(9,'deberías'),'salud':W(9,'salud')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
