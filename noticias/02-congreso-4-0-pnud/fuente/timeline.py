import json, subprocess
scenes=[]; t=0.0; N=8
for i in range(1,N+1):
    f=f's{i}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
    dur=round(dur-0.15,3)+(0.3 if i in (1,4) else 0.1)
    if i==N: dur+=2.0
    w=json.load(open(f+'.json'))
    scenes.append({'start':round(t,3),'dur':round(dur,3),'words':[[round(t+a,3),round(t+a+b,3),x] for a,b,x in w]})
    t+=dur
def W(si,pre,k=0):
    return [w for w in scenes[si]['words'] if w[2].lower().startswith(pre)][k][0]
S=[s['start'] for s in scenes]
ev={'S':S,
 'cambiar':W(0,'cambiar'),'inv':W(0,'inversión'),'num':W(0,'ciento'),'lps':W(0,'lempiras'),
 'martes':W(1,'martes'),'pnud':W(1,'pnud'),'firm':W(1,'firmaron'),'conv':W(1,'convenio'),
 'zam':W(2,'tomás'),'rep':W(2,'representante'),
 'c40':W(3,'congreso'),'cuatro':W(3,'cuatro'),'mod':W(3,'modernizar'),'hemi':W(3,'hemiciclo'),
 'segura':W(4,'segura'),'indiv':W(4,'individual'),'n128':W(4,'ciento'),'prop':W(4,'propietarios'),
 'dig':W(5,'digitalizar'),'herr':W(5,'herramientas'),'ia':W(5,'inteligencia'),
 'ciud':W(6,'ciudadanía'),'acc':W(6,'conozca'),'dec':W(6,'decide'),
 'vale':W(7,'vale'),'cta':W(7,'comentá'),
}
MERGE=[(['ciento','treinta','y','cinco','punto','cuatro'],'135.4'),(['ciento','veintiocho'],'128'),(['cuatro','punto','cero'],'4.0')]
for sc in scenes:
    sc['sub']=[]; ws=sc['words']; i=0
    while i<len(ws):
        done=False
        for seq,rep in MERGE:
            if [w[2].lower() for w in ws[i:i+len(seq)]]==seq:
                sc['sub'].append([ws[i][0],ws[i+len(seq)-1][1],rep]); i+=len(seq); done=True; break
        if not done: sc['sub'].append(ws[i]); i+=1
json.dump({'total':round(t,3),'scenes':scenes,'ev':ev},open('timeline.json','w'),ensure_ascii=False)
print(round(t,2),ev)
