const {chromium}=require('playwright');const {spawn}=require('child_process');const path=require('path');
(async()=>{
 const mode=process.argv[2]; const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
 p.on('pageerror',e=>console.error('PAGEERR',e.message));
 await p.goto('file://'+path.resolve('build.html')); await p.evaluate(()=>window.ready);
 const total=await p.evaluate(()=>window.TOTAL);
 if(mode==='preview'){ const ts=process.argv[3].split(',').map(Number);
   for(const t of ts){await p.evaluate(t=>window.seek(t),t);await p.screenshot({path:`prev/f_${t.toFixed(1)}.jpg`,type:'jpeg',quality:80})}
 } else { const fps=30,n=Math.ceil(total*fps);
   const ff=spawn('ffmpeg',['-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','video_mute.mp4'],{stdio:['pipe','inherit','inherit']});
   for(let i=0;i<n;i++){await p.evaluate(t=>window.seek(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:95});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%300===0)console.log('frame',i,'/',n)}
   ff.stdin.end();await new Promise(r=>ff.on('close',r));
 }
 await b.close();
})();
