import sys,json; sys.argv=['p','audio','x.mp4']
import pipeline as p
tl,_=p.timeline(json.load(open('guion.json')))
json.dump(tl,open('timeline.json','w'),ensure_ascii=False,indent=1)
open('build.html','w').write(open('reel.html').read().replace('__TIMELINE__',json.dumps(tl,ensure_ascii=False)))
print('total',tl['total'])
