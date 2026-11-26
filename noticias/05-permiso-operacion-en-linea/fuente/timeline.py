import json, subprocess
scenes=[]; t=0.0; N=9
PAD={1:.3,2:.2,3:.4,8:.4}
for i in range(1,N+1):
    f=f's{i}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur-0.15,3)+PAD.get(i,.15)
    if i==N: dur+=2.2
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('dos mil veintisiete','2027')]
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
ev={'S':S,'filas':W(0,'filas'),'enero':W(0,'enero'),'permiso':W(0,'permiso'),
 'dia':W(1,'día'),'perdido':W(1,'perdido'),'veces':W(1,'veces'),'trami':W(1,'tramitador'),
 'acaba':W(2,'acaba'),
 'y27':W(3,'dos'),'linea':W(3,'línea'),'cel':W(3,'celular'),
 'decl':W(4,'declaraciones'),'x1':W(4,'centro'),'x2':W(4,'filas'),'x3':W(4,'tramitador'),
 'sar':W(5,'sar'),'contrato':W(5,'contrato'),'sola':W(5,'sola'),'todo':W(5,'todo'),
 'alc':W(6,'juan'),'formal':W(6,'formalizarán'),'malls':W(6,'malls'),'medios':W(6,'medios'),'redes':W(6,'redes'),
 'frase':S[7],'digit':W(7,'digitalizar'),'reinv':W(7,'reinventar'),
 'vez':W(8,'vez'),'cta':W(8,'comentá')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print(ev)
