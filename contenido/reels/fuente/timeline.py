import json, subprocess, sys, os
d = sys.argv[1]
scenes = []; t = 0
for i in range(1, 9):
    f = os.path.join(d, f's{i}.mp3')
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
    dur = round(dur - 0.25, 3)
    if i == 8: dur += 1.8
    w = json.load(open(f + '.json'))
    scenes.append({'start': round(t, 3), 'dur': dur, 'words': [[round(t + a, 3), round(t + a + b, 3), x] for a, b, x in w]})
    t += dur
json.dump({'total': round(t, 3), 'scenes': scenes}, open(os.path.join(d, 'timeline.json'), 'w'), ensure_ascii=False)
# subtitle autoshrink patch (idempotent)
p = os.path.join(d, 'index.html'); s = open(p).read()
a = "const ws=parts.map(p=>g.measureText(p).width);const total=ws.reduce((a,b)=>a+b,0)+sp*(parts.length-1);"
b = "let ws=parts.map(p=>g.measureText(p).width);let total=ws.reduce((a,b)=>a+b,0)+sp*(parts.length-1);let fsz=fs;if(total>W-140){fsz=Math.floor(fs*(W-140)/total);g.font=`800 ${fsz}px 'Onest'`;ws=parts.map(p=>g.measureText(p).width);total=ws.reduce((a,b)=>a+b,0)+sp*(parts.length-1);}"
if a in s:
    s = s.replace(a, b).replace("g.roundRect(x-14,y-fs*.62,ws[i]+28,fs*1.24,18)", "g.roundRect(x-14,y-fsz*.62,ws[i]+28,fsz*1.24,18)")
open(p, 'w').write(s)
print(t, [x['start'] for x in scenes])
