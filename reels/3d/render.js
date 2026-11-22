// node render.js stills   -> previews  |  node render.js video <outdir>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const DUR = (process.env.DUR || '5,5,6,5,9,8').split(',').map(Number), FPS = 30, PAGE = process.env.PAGE || 'scene.html';
const root = __dirname;
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : f.endsWith('.png') ? 'image/png' : f.endsWith('.jpg') ? 'image/jpeg' : f.endsWith('.json') ? 'application/json' : 'text/html' }); fs.createReadStream(f).pipe(r);
}).listen(8765);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('http://localhost:8765/' + PAGE); await p.waitForFunction('window.ready === true', null, { timeout: 60000 });
  const mode = process.argv[2] || 'stills';
  if (mode === 'stills') {
    for (let i = 0; i < DUR.length; i++) {
      await p.evaluate(i => setScene(i), i);
      for (let k = 0; k < 3; k++) await p.evaluate(t => renderAt(t), DUR[i] * (k + 1) / 4);
      await p.screenshot({ path: path.join(root, `still${i + 1}.jpg`), type: 'jpeg', quality: 85 });
    }
  } else {
    const out = process.argv[3]; const only = process.argv[4] ? process.argv[4].split(',').map(Number) : DUR.map((_, i) => i);
    for (const i of only) {
      const t0 = Date.now();
      await p.evaluate(i => setScene(i), i);
      const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, `escena${i + 1}.mp4`)]);
      const n = DUR[i] * FPS;
      for (let f = 0; f < n; f++) {
        await p.evaluate(t => renderAt(t), f / FPS);
        const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      }
      ff.stdin.end(); await new Promise(r => ff.on('close', r));
      console.log(`escena ${i + 1} lista en ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
  }
  await b.close(); srv.close();
})();
