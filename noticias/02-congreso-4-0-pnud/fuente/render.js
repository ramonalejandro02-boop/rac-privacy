const {chromium}=require('playwright');const fs=require('fs');const path=require('path');const {spawn}=require('child_process');
(async()=>{
 const dir=path.resolve(process.argv[2]), mode=process.argv[3];
 const tl=JSON.parse(fs.readFileSync(path.join(dir,'timeline.json')));
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 p.on('pageerror',e=>console.error('PAGEERR',e.message));p.on('console',m=>console.log('LOG',m.text()));
 await p.goto('file://'+path.join(dir,'index.html'));await p.evaluate(t=>setup(t),tl);
 if(mode==='stills'){
   const ts=process.argv[4].split(',').map(Number);
   for(const t of ts){const d=await p.evaluate(t=>frame(t),t);fs.writeFileSync(path.join(dir,`still_${t}.jpg`),Buffer.from(d.split(',')[1],'base64'));}
 } else {
   const fps=30,n=Math.ceil(tl.total*fps);
   const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-preset','medium',path.join(dir,'video.mp4')],{stdio:['pipe','inherit','inherit']});
   for(let f=0;f<n;f++){const d=await p.evaluate(t=>frame(t),f/fps);
     if(!ff.stdin.write(Buffer.from(d.split(',')[1],'base64')))await new Promise(r=>ff.stdin.once('drain',r));
     if(f%300==0)console.log('frame',f,'/',n);}
   ff.stdin.end();await new Promise(r=>ff.on('close',r));
 }
 await b.close();
})();
