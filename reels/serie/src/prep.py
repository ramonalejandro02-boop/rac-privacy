"""Per video: folder, guion.json, reel.html (spec embedded). Run with system python."""
import json,os,shutil,sys
sys.path.insert(0,'.'); from specs import VIDEOS
for v in VIDEOS:
    d=v['slug']; os.makedirs(d+'/audio',exist_ok=True)
    json.dump([{'id':s['id'],'text':s['text']} for s in v['scenes']],open(f'{d}/guion.json','w'),ensure_ascii=False,indent=1)
    spec={'num':v.get('num',{}),'scenes':[{'id':s['id'],'shots':s['shots']} for s in v['scenes']]}
    open(f'{d}/reel.html','w').write(open('plantilla.html').read().replace('__SPEC__',json.dumps(spec,ensure_ascii=False)))
    for f in ['pipeline.py','render.js','gsap.min.js']: shutil.copy(f,d)
    if not os.path.exists(d+'/fonts'): os.symlink(os.path.realpath('fonts'),d+'/fonts')
print('ok',len(VIDEOS))
