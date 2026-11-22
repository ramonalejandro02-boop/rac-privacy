const {chromium}=require('playwright');const fs=require('fs');const {spawn}=require('child_process');
(async()=>{
 const mode=process.argv[2]; const tim=JSON.parse(fs.readFileSync('timing.json'));
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://127.0.0.1:8765/anim.html'); await p.evaluate(t=>setup(t),tim);
 if(mode==='stills'){ for(const t of process.argv.slice(3).map(Number)){const d=await p.evaluate(t=>frame(t),t);
   fs.writeFileSync(`still_${t}.jpg`,Buffer.from(d.split(',')[1],'base64'));} }
 else { const fps=30,N=Math.ceil(tim.total*fps);
   const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-i','-','-i','voz.wav','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','out.mp4'],{stdio:['pipe','inherit','inherit']});
   for(let i=0;i<N;i++){const d=await p.evaluate(t=>frame(t),i/fps); if(!ff.stdin.write(Buffer.from(d.split(',')[1],'base64')))await new Promise(r=>ff.stdin.once('drain',r));}
   ff.stdin.end(); await new Promise(r=>ff.on('close',r)); }
 await b.close();
})();
