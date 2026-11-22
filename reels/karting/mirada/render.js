const {chromium}=require('playwright');const fs=require('fs');const {spawn}=require('child_process');
(async()=>{
 const mode=process.argv[2]; const tim=JSON.parse(fs.readFileSync('timing.json'));
 const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:1080,height:1920}});
 p.on('pageerror',e=>console.log('ERR',e.message)); p.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text());});
 await p.goto('http://127.0.0.1:8767/'+(process.env.PAGE||'scene.html')); await p.waitForFunction('window.ready===true',{timeout:60000});
 await p.evaluate(t=>setup(t),tim);
 if(mode==='stills'){ for(const t of process.argv.slice(3).map(Number)){const t0=Date.now();const d=await p.evaluate(t=>frame(t),t);
   fs.writeFileSync(`still_${t}.jpg`,Buffer.from(d.split(',')[1],'base64'));console.log('frame',t,Date.now()-t0,'ms');} }
 else { const fps=30,N=Math.ceil(tim.total*fps);const SP=[];
   const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-i','-','-i','voz.wav','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','out.mp4'],{stdio:['pipe','inherit','inherit']});
   for(let i=0;i<N;i++){const d=await p.evaluate(t=>frame(t),i/fps);SP.push(await p.evaluate(()=>window.SPEED||0)); if(!ff.stdin.write(Buffer.from(d.split(',')[1],'base64')))await new Promise(r=>ff.stdin.once('drain',r)); if(i%150===0)console.log('frame',i,'/',N);}
   ff.stdin.end();fs.writeFileSync('speeds.json',JSON.stringify(SP)); await new Promise(r=>ff.on('close',r)); }
 await b.close();
})();
