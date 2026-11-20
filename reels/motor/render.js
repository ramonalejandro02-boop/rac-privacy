// Renderiza un video del motor CONAFEPH cuadro por cuadro.
// Uso: node render.js <ruta_html_relativa_a_reels> <carpeta_frames> [preview t1,t2,...] [desde] [hasta]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.woff2': 'font/woff2', '.jpg': 'image/jpeg' };
const [, , page, out, prev, from, to] = process.argv;
const srv = http.createServer((q, r) => {
  const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(d); } });
}).listen(0, async () => {
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => { if (m.type() === 'error') console.error('PAGE:', m.text()); });
  p.on('pageerror', e => console.error('PAGEERR:', e.message));
  await p.goto(`http://localhost:${port}/${page}`);
  await p.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  fs.mkdirSync(out, { recursive: true });
  const dur = await p.evaluate(() => DURATION);
  const fps = 30;
  let times;
  if (prev && prev !== 'full') times = prev.split(',').map(Number);
  else { const n = Math.round(dur * fps); const a = from ? +from : 0, z = to ? +to : n; times = []; for (let i = a; i < z; i++) times.push(i / fps); }
  const t0 = Date.now();
  for (let i = 0; i < times.length; i++) {
    await p.evaluate(t => seek(t), times[i]);
    const idx = prev && prev !== 'full' ? i : Math.round(times[i] * fps);
    await p.screenshot({ path: `${out}/f${String(idx).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
    if (i % 150 === 0) console.log(`frame ${i}/${times.length} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await b.close(); srv.close();
});
