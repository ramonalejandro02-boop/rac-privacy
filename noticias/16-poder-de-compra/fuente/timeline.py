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
MERGE=[('seis punto noventa y ocho por ciento','6.98%'),('siete por ciento','7%')]
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
ev={'S':S,'billete':W(0,'billete'),'menos':W(0,'menos'),
 'inflacion':W(1,'inflación'),'seis':W(1,'seis'),'octubre':W(1,'octubre'),
 'colegio':W(2,'colegio'),'dinero':W(2,'dinero'),'perdio':W(2,'perdió'),'siete':W(2,'siete'),'compra':W(2,'compra'),
 'comer':W(3,'comer'),'menos4':W(3,'menos'),'menor':W(3,'menor'),'calidad':W(3,'calidad'),
 'diciembre':W(4,'diciembre'),'aguinaldos':W(4,'aguinaldos'),'advierten':W(4,'advierten'),'presion':W(4,'presión'),
 'huevo':W(5,'huevo'),'acuerdo':W(5,'acuerdo'),'proveedores':W(5,'proveedores'),'mercados':W(5,'mercados'),'acatar':W(5,'acatar'),
 'resto':W(6,'resto'),'canasta':W(6,'canasta'),'protege':W(6,'protege'),
 'aguinaldo':W(7,'aguinaldo'),'vez':W(7,'vez'),'precios':W(7,'precios'),'quedan':W(7,'quedan'),
 'lista':W(8,'lista'),'corta':W(8,'corta'),'culpa':W(8,'culpa'),'lempira':W(8,'lempira'),'vale':W(8,'vale')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
