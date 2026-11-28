import json, subprocess
scenes=[]; t=0.0; N=11
for i in range(1,N+1):
    f=f's{i}_t.wav'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur,3)+.38
    if i==N: dur+=1.6
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
MERGE=[('seis punto noventa y ocho por ciento','6.98%'),('cuatro punto cuatro','4.4%'),('tres punto nueve','3.9%'),('cero punto cinco','0.5%'),('tres punto cinco','3.5%'),
 ('cuarenta y seis por ciento','46%'),('ciento cuarenta y seis','146'),('cien','100'),('siete de cada diez','7 DE CADA 10'),('dos mil veintitrés','2023'),('veinte por ciento','20%'),('siete por ciento','7%'),('ocho','8'),('unah','UNAH')]
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
ev={'S':S,'alcanza':W(0,'alcanza'),'imag':W(0,'imaginación'),
 'alta':W(1,'alta'),'n698':W(1,'seis'),
 'gt':W(2,'guatemala'),'sv':W(2,'salvador'),'cr':W(2,'costa'),
 'feb':W(3,'febrero'),'dupl':W(3,'duplicó'),
 'comb':W(4,'combustible'),'n46':W(4,'cuarenta'),'cien':[w for w in scenes[4]['words'] if w[2].lower()=='cien'][0][0],'n146':W(4,'ciento',1),
 'seq':W(5,'sequía'),'p1':W(5,'huevos'),'p2':W(5,'papas'),'p3':W(5,'lácteos'),'p4':W(5,'frijoles'),'p5':W(5,'carne'),
 'n7':S[6],'caros':W(6,'caros'),
 'empezo':W(7,'empezó'),'y23':W(7,'dos'),'n20':W(7,'veinte'),
 'unah':W(8,'unah'),'n7b':W(8,'siete'),
 'plan':W(9,'plan'),'cuando':W(9,'cuándo'),'preg':W(9,'pregunta'),
 'mossi':W(10,'mossi'),'imp':W(10,'impuesto'),'pobres':W(10,'pobres'),'pagas':W(10,'pagás'),'compra':W(10,'compra')}
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2)); print({k:(round(v,2) if not isinstance(v,list) else [round(x,2) for x in v]) for k,v in ev.items()})
