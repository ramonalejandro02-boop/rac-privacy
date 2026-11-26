// MEDIA CALLE ES SU TALLER — cada cuadro es una función pura de t. Bocas sincronizadas con las voces reales.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, Subs = globalThis.Subs, Shots = globalThis.Shots, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { clamp, lerp, ease } = U;
  const { ev, at, wt } = S;
  const W = G.W, H = G.H, SAFE = G.SAFE;
  let VO = null, SUBS = [], LOGO = null;

  // ---------- el elenco (nuevo para este video) ----------
  const CAST = {
    memo: { outfit: 'tee', shirt: '#4F6D8F', bottoms: 'pants', shorts: '#2E3440', skin: '#9C6644', hairStyle: 'short', hair: '#1E1612', facialHair: 'stubble', headwear: 'cap', headwearColor: '#F2B84B', build: 'broad', shoes: '#2A2A2A' },
    lupe: { outfit: 'dress', shirt: '#7A5CC0', skin: '#D59B72', hairStyle: 'long', hair: '#4A2E1E', glasses: 'bold', shoes: '#3A2A2A' },
    nieto1: { outfit: 'tee', shirt: '#E8718D', bottoms: 'shorts', shorts: '#27305C', skin: '#C98A62', hairStyle: 'curly' },
    nieto2: { outfit: 'tee', shirt: '#3FA89B', bottoms: 'shorts', shorts: '#F2B84B', skin: '#B97D55', hairStyle: 'ponytail' },
    asesora: { outfit: 'shirt', shirt: '#1E9E57', bottoms: 'skirt', shorts: '#203A5C', skin: '#C98A62', hairStyle: 'bun', hair: '#1E1612', glasses: 'round', shoes: '#2A2A2A' },
  };
  globalThis.CAST = CAST;
  // ---------- utilería del taller ----------
  function carBody(ctx, x, y, s, col, seed, { wheels = [1, 1], hood = 0 } = {}) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    G.rrect(ctx, -240, -150, 480, 110, 34, { fill: col, lw: 6, seed });
    G.poly(ctx, [[-150, -150], [-90, -240], [110, -240], [170, -150]], { fill: Ch.shade(col, 0.85), lw: 6, seed: seed + 1, step: 20 });
    G.poly(ctx, [[-130, -155], [-82, -225], [0, -225], [0, -155]], { fill: '#BFE0F0', lw: 4, seed: seed + 2, step: 20 });
    G.poly(ctx, [[20, -155], [20, -225], [100, -225], [150, -155]], { fill: '#BFE0F0', lw: 4, seed: seed + 3, step: 20 });
    if (hood) { ctx.save(); ctx.translate(170, -150); ctx.rotate(-0.9 * hood); G.rrect(ctx, 0, -10, 90, 18, 6, { fill: col, lw: 5, seed: seed + 4 }); ctx.restore(); }
    [-150, 150].forEach((wx, k) => { if (wheels[k]) { G.ellipse(ctx, wx, -40, 52, 52, { fill: '#2A2A30', lw: 5, seed: seed + 5 + k }); G.ellipse(ctx, wx, -40, 20, 20, { fill: '#B8BEC6', lw: 3, seed: seed + 7 + k }); } else { G.rrect(ctx, wx - 30, -60, 60, 60, 6, { fill: '#8E6444', lw: 4, seed: seed + 9 + k }); } });
    ctx.restore();
  }
  function tireStack(ctx, x, y, n, s = 1) { for (let k = 0; k < n; k++) { G.ellipse(ctx, x, y - k * 34 * s, 62 * s, 22 * s, { fill: '#2A2A30', lw: 4, seed: 600 + k + x }); G.ellipse(ctx, x, y - k * 34 * s - 4, 26 * s, 9 * s, { fill: '#55585E', lw: 2, seed: 610 + k + x }); } }
  function engineBlock(ctx, x, y, s = 1) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); G.rrect(ctx, -90, -110, 180, 110, 12, { fill: '#6E747C', lw: 5, seed: 620 }); for (let k = 0; k < 4; k++) G.ellipse(ctx, -60 + k * 40, -118, 14, 10, { fill: '#4A4E55', lw: 3, seed: 621 + k }); G.rrect(ctx, -110, -60, 30, 30, 6, { fill: '#4A4E55', lw: 3, seed: 626 }); ctx.restore(); }
  function oil(ctx, x, y, r, seed = 630) { if (r <= 1) return; G.ellipse(ctx, x, y, r, r * 0.32, { fill: '#2B2622', lw: 3, seed }); ctx.save(); ctx.globalAlpha = 0.35; G.ellipse(ctx, x - r * 0.3, y - r * 0.08, r * 0.35, r * 0.07, { fill: '#8E7BC8', lw: 0, seed: seed + 1 }); ctx.restore(); }
  function toolbox(ctx, x, y) { G.rrect(ctx, x - 60, y - 60, 120, 60, 8, { fill: '#C8453B', lw: 5, seed: 640 }); G.rrect(ctx, x - 24, y - 80, 48, 22, 6, { fill: 'none', lw: 5, seed: 641 }); }
  function shopSign(ctx, x, y) { G.rrect(ctx, x - 180, y - 50, 360, 100, 10, { fill: '#F2B84B', lw: 6, seed: 650 }); G.text(ctx, 'TALLER MEMO', x, y + 18, { size: 50, align: 'center', fam: 'Permanent Marker', weight: 400, color: INK }); }
  function clang(ctx, x, y, t, p) { if (p <= 0) return; const k = 1 + 0.12 * Math.sin(t * 30); ctx.save(); ctx.translate(x, y); ctx.rotate(-0.12); ctx.scale(k * p, k * p); G.text(ctx, '¡CLANG!', 0, 0, { size: 90, align: 'center', fam: 'Bungee', weight: 400, color: '#F2B84B', stroke: INK, strokeW: 12 }); ctx.restore(); for (let i = 0; i < 3; i++) G.line(ctx, [[x - 170 - i * 20, y - 60 + i * 40], [x - 230 - i * 20, y - 70 + i * 40]], { color: INK, lw: 6, seed: 660 + i }); }
  function clockFace(ctx, x, y, label) { G.ellipse(ctx, x, y, 80, 80, { fill: '#F6F0E2', lw: 6, seed: 670 }); G.line(ctx, [[x, y], [x, y - 55]], { color: INK, lw: 7, seed: 671 }); G.line(ctx, [[x, y], [x + 40, y]], { color: INK, lw: 7, seed: 672 }); G.text(ctx, label, x, y + 130, { size: 40, align: 'center', fam: 'Bungee', weight: 400, color: '#FFF', stroke: INK, strokeW: 8 }); }
  function ball(ctx, x, y, r = 30) { G.ellipse(ctx, x, y, r, r, { fill: '#F6F0E2', lw: 4, seed: 680 }); G.poly(ctx, [[x - 8, y - 10], [x + 10, y - 8], [x + 12, y + 8], [x - 6, y + 12], [x - 14, y]], { fill: INK, lw: 2, seed: 681, step: 6 }); }
  function streetScene(ctx, t, o = {}) { // la calle con el taller de don Memo
    sky(ctx, o.top ?? '#86C5E8', o.bot ?? '#DFF0F8');
    houseFront(ctx, -40, 640, 560, 480, '#E9C46A', 10);
    shopSign(ctx, 260, 600);
    houseFront(ctx, 600, 700, 520, 420, '#E8A9B8', 50);
    ground(ctx, 1120, '#BDB09A');
    G.rrect(ctx, -20, 1120, W + 40, 40, 0, { fill: '#D9D2C3', lw: 4, seed: 690 }); // acera
  }

  // ---------- tomas ----------
  function hook(ctx, t) {
    streetScene(ctx, t);
    const ab = wt(at('hook'), 'abrio'), me = wt(at('hook'), 'media'), de = wt(at('hook'), 'desarmados');
    const n = clamp((t - me + 0.2) / 1.4);
    if (n > 0.05) carBody(ctx, lerp(-300, 220, ease.outCubic(clamp(n * 2))), 1290, 0.72, '#D9534F', 700, { wheels: [1, 0], hood: 1 });
    if (n > 0.4) carBody(ctx, lerp(1300, 820, ease.outCubic(clamp(n * 2 - 0.8))), 1300, 0.66, '#4F8FC0', 720, { wheels: [0, 1] });
    if (t > de - 0.3) { tireStack(ctx, 520, 1290, 3, 0.9); engineBlock(ctx, 560, 1180, 0.7); }
    Ch.person(ctx, { x: 470, y: 1300, s: 0.78, pose: 'stand', style: CAST.memo, gesture: t > ab ? 'thumbsUp' : null, mouth: 'grin', eyes: 'happy', seed: 300 });
    title(ctx, 'MEDIA CALLE', 430, clamp((t - me + 0.1) / 0.4));
    title(ctx, 'ES SU TALLER', 545, clamp((t - de) / 0.4), { color: '#E0503E', size: 96, rot: 0.03 });
  }
  function problemas(ctx, t) {
    streetScene(ctx, t, { top: '#F2C98A', bot: '#FBE7C4' });
    const L = at('problemas'), ac = wt(L, 'aceite'), ru = wt(L, 'ruido'), ll = wt(L, 'llantas');
    carBody(ctx, 220, 1290, 0.72, '#D9534F', 700, { wheels: [1, 0], hood: 1 }); tireStack(ctx, 560, 1290, 3, 0.9); engineBlock(ctx, 860, 1290, 0.8);
    oil(ctx, 420, 1145, 140 * clamp((t - ac + 0.2) / 1.2));
    tag(ctx, 'ACEITE EN LA ACERA', 540, 760, clamp((t - ac) / 0.3), { bg: '#2B2622', fg: '#F2B84B', size: 44, rot: -0.04 });
    if (t > ru - 0.2) { clockFace(ctx, 860, 520, '6:00 AM'); clang(ctx, 540, 900, t, clamp((t - ru + 0.2) / 0.3)); }
    if (t > ll - 0.3) Ch.person(ctx, { ...Ch.walk(t, { x0: 1150, speed: -240, t0: ll - 0.3 }), y: 1300, s: 0.7, sx: -1, style: CAST.lupe, brows: 'worried', eyes: 'normal', mouth: 'wavy', seed: 330 });
  }
  function pleito(ctx, t) {
    const mT = t >= ev.memo - 0.15;
    sky(ctx, mT ? '#4F6D8F' : '#7A5CC0', mT ? '#2C3E55' : '#4A3680');
    ground(ctx, 1180, mT ? '#BDB09A' : '#D8C9B0');
    tireStack(ctx, 540, 1200, 2, 0.7); oil(ctx, 560, 1240, 90);
    Ch.person(ctx, { x: 280, y: 1300, s: 1.12, pose: 'stand', style: CAST.lupe, gesture: !mT ? 'point' : 'akimbo', mouth: mouthOf('lupe', t) || (mT ? 'flat' : 'open'), brows: 'determined', eyes: 'normal', look: 0.6, seed: 330 });
    Ch.person(ctx, { x: 800, y: 1300, s: 1.12, sx: -1, pose: 'stand', style: CAST.memo, gesture: mT ? 'shrug' : null, crossArms: !mT, mouth: mouthOf('memo', t) || (mT ? 'flat' : 'smirk'), brows: mT ? 'worried' : 'neutral', eyes: 'normal', look: -0.6, seed: 300 });
    tag(ctx, mT ? 'DON MEMO · MECÁNICO' : 'DOÑA LUPE · VECINA', 540, 420, 1, { size: 40 });
  }
  function tension(ctx, t) {
    const L = at('tension'), tr = wt(L, 'trabajo'), ca = wt(L, 'calle'), ra = wt(L, 'razon');
    const sp = ease.outCubic(clamp((t - ev.tension) / 0.5)), mx = lerp(1080, 540, sp);
    ctx.fillStyle = '#4F6D8F'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#7A5CC0'; ctx.fillRect(mx, 0, W, H);
    G.line(ctx, [[mx, 0], [mx, H]], { color: INK, lw: 10, seed: 700 });
    Ch.person(ctx, { x: 280, y: 1250, s: 0.82, pose: 'stand', style: CAST.memo, handR: [140, -330], mouth: 'flat', eyes: 'normal', seed: 300 }); wrench(ctx, 280 + 0.82 * 140, 1250 - 0.82 * 330);
    Ch.person(ctx, { x: 800, y: 1250, s: 0.82, pose: 'stand', style: CAST.lupe, gesture: 'akimbo', mouth: 'flat', eyes: 'normal', seed: 330 });
    tag(ctx, 'SU TRABAJO', 270, 620, clamp((t - tr + 0.2) / 0.3), { size: 46, rot: -0.05 });
    tag(ctx, 'LA CALLE', 810, 620, clamp((t - ca + 0.2) / 0.3), { size: 50, rot: 0.05 });
    tag(ctx, 'LOS DOS TIENEN ALGO DE RAZÓN', 540, 1300 - 40, clamp((t - ra + 0.4) / 0.3), { bg: '#F2B84B', size: 34 });
  }
  function saber(ctx, t) {
    sky(ctx, '#2F7D6D', '#1E5248');
    const L = at('saber'), va = wt(L, 'valido'), bo = wt(L, 'bodega'), li = wt(L, 'libres'), se = wt(L, 'seguras'), co = wt(L, 'contamina');
    tag(ctx, 'TRABAJAR EN CASA: VÁLIDO', 540, 430, clamp((t - va + 0.2) / 0.3), { bg: '#F6F0E2', size: 38 });
    title(ctx, 'LA CALLE NO\nES BODEGA', 600, clamp((t - bo + 0.2) / 0.4), { color: '#F2B84B', size: 92 });
    tag(ctx, 'LIBRE', 330, 900, clamp((t - li) / 0.3), { bg: '#7FD3A0', size: 50, rot: -0.04 });
    tag(ctx, 'SEGURA', 740, 900, clamp((t - se) / 0.3), { bg: '#7FD3A0', size: 50, rot: 0.04 });
    const cp = clamp((t - co + 0.3) / 0.5);
    if (cp > 0) { oil(ctx, 540, 1130, 60 + 120 * cp, 760); for (let k = 0; k < 3; k++) { const p = (t * 0.6 + k / 3) % 1; ctx.save(); ctx.globalAlpha = 1 - p; G.ellipse(ctx, 470 + k * 70, 1100 - p * 120, 12, 18, { fill: '#2B2622', lw: 2, seed: 770 + k }); ctx.restore(); } tag(ctx, 'EL ACEITE CONTAMINA', 540, 1240, cp, { bg: '#E0503E', fg: '#FFF', size: 40 }); }
  }
  function mito(ctx, t) {
    sky(ctx, '#3A1230', '#1A0E2E');
    const L = at('mito'), po = wt(L, 'ponchar'), hu = wt(L, 'humillarlo'), ca = wt(L, 'calienta');
    tag(ctx, 'PONCHAR LLANTAS', 540, 640, clamp((t - po + 0.2) / 0.3), { size: 52, rot: -0.04 });
    tag(ctx, 'HUMILLARLO EN PÚBLICO', 540, 820, clamp((t - hu + 0.2) / 0.3), { size: 46, rot: 0.04 });
    bigX(ctx, clamp((t - ca + 0.3) / 0.4), 150, 560, 930, 900);
    title(ctx, 'SOLO CALIENTA\nEL PLEITO', 1080, clamp((t - ca) / 0.4), { color: '#E0503E', size: 86 });
  }
  function pasos(ctx, t) {
    const act = t >= ev.p3 - 0.2 ? 2 : t >= ev.p2 - 0.2 ? 1 : 0;
    sky(ctx, ['#F29C8F', '#8FB3F2', '#7FD3A0'][act], '#203A5C');
    card(ctx, 470, 1, 'CONVERSAR', 'Horarios y espacios de trabajo', '#E07A5F', act === 0, clamp((t - ev.pasos) / 0.4));
    card(ctx, 660, 2, 'PATRONATO', 'Reglas claras en la calle', '#5FA8D3', act === 1, clamp((t - ev.p2 + 0.2) / 0.4));
    card(ctx, 850, 3, 'ORIENTACIÓN', 'en CONAFEPH', '#1E9E57', act === 2, clamp((t - ev.p3 + 0.2) / 0.4), true);
    Ch.person(ctx, { x: 250, y: 1300, s: 0.62, pose: 'stand', style: CAST.asesora, gesture: 'pointUp', mouth: 'smile', eyes: 'happy', seed: 360 });
    tag(ctx, 'ASESORA CONAFEPH', 640, 1180, clamp((t - ev.pasos - 0.3) / 0.3), { bg: '#1E9E57', fg: '#FFF', size: 38 });
    if (act === 0 && t > ev.pasos + 1) clockFace(ctx, 860, 1040, '');
  }
  function final(ctx, t) {
    streetScene(ctx, t, { top: '#FFD27A', bot: '#FFF1D6' });
    // el carro dentro del portón (taller ordenado), la calle libre
    carBody(ctx, 260, 1110, 0.55, '#D9534F', 700, { hood: 0.6 });
    Ch.person(ctx, { x: 120, y: 1150, s: 0.55, pose: 'stand', style: CAST.memo, gesture: 'wave', mouth: 'grin', eyes: 'happy', seed: 300 });
    const bx = 620 + Math.sin(t * 2.4) * 150, by = 1230 - Math.abs(Math.sin(t * 4.8)) * 140;
    Ch.person(ctx, { x: 520, y: 1300, s: 0.5, pose: 'stand', style: CAST.nieto1, gesture: 'cheer', mouth: 'open', eyes: 'happy', seed: 380 });
    Ch.person(ctx, { x: 760, y: 1300, s: 0.48, pose: 'stand', style: CAST.nieto2, gesture: 'cheer', mouth: 'open', eyes: 'happy', seed: 400 });
    ball(ctx, bx, by);
    Ch.person(ctx, { x: 930, y: 1300, s: 0.62, pose: 'stand', style: CAST.lupe, gesture: 'thumbsUp', mouth: 'grin', eyes: 'happy', seed: 330 });
    title(ctx, 'TRABAJAR SIN\nQUITAR LA CALLE', 430, clamp((t - ev.final) / 0.4), { color: '#5FA8D3', size: 86 });
  }
  function cierre(ctx, t) {
    sky(ctx, '#0E2A47', '#14335A');
    const p = clamp((t - ev.cierre) / 0.7), k = ease.outBack(p, 2);
    ctx.save(); ctx.translate(540, 760); ctx.scale(k, k); G.ellipse(ctx, 0, 0, 250, 250, { fill: '#FFF', lw: 6, seed: 400 }); if (LOGO) ctx.drawImage(LOGO, -220, -220, 440, 440); ctx.restore();
    title(ctx, 'CONAFEPH', 1130, clamp((t - ev.cierre - 0.5) / 0.4), { color: '#FFF', size: 110, rot: 0 });
    tag(ctx, 'ORIENTACIÓN PARA PATRONATOS', 540, 1270, clamp((t - ev.cierre - 1) / 0.3), { bg: '#F2B84B', size: 38 });
  }

  const mouthOf = (who, t) => { const m = Subs.mouth(VO, t, who); return m.talking ? m : null; };
  const INK = '#2A2320';
  const title = (ctx, txt, y, p, { size = 110, color = '#F2B84B', rot = -0.03 } = {}) => {
    if (p <= 0) return; const k = ease.outBack(clamp(p), 2);
    ctx.save(); ctx.translate(540, y); ctx.rotate(rot); ctx.scale(k, k); ctx.globalAlpha = clamp(p * 2);
    txt.split('\n').forEach((l, i) => G.text(ctx, l, 0, i * size * 0.95, { size, align: 'center', fam: 'Bungee', weight: 400, color, stroke: INK, strokeW: 12 }));
    ctx.restore();
  };
  const tag = (ctx, txt, x, y, p, { bg = '#F6F0E2', fg = INK, size = 44, rot = 0 } = {}) => {
    if (p <= 0) return; const k = ease.outBack(clamp(p), 2), w = G.measure(ctx, txt, size, 'Bungee', 400) + 60;
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(k, k);
    G.rrect(ctx, -w / 2, -size * 0.85, w, size * 1.7, size * 0.5, { fill: bg, lw: 5, seed: Math.round(x + y) });
    G.text(ctx, txt, 0, size * 0.36, { size, align: 'center', fam: 'Bungee', weight: 400, color: fg });
    ctx.restore();
  };
  // ---------- utilería ----------
  function sky(ctx, top, bot) { const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, top); g.addColorStop(1, bot); ctx.fillStyle = g; ctx.fillRect(-400, -400, W + 800, H + 800); }
  function tank(ctx, x, y, s, t) { // el tanque de la junta de agua sobre el cerro
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    for (const lx of [-90, 90]) G.line(ctx, [[lx, 0], [lx * 0.6, -260]], { color: '#5A5048', lw: 10, seed: 30 + lx });
    G.line(ctx, [[-80, -90], [80, -90]], { color: '#5A5048', lw: 8, seed: 33 });
    G.rrect(ctx, -140, -470, 280, 220, 30, { fill: '#5FA8D3', lw: 6, seed: 34, hatch: { color: 'rgba(255,255,255,0.15)', gap: 12 } });
    G.text(ctx, 'JUNTA DE AGUA', 0, -350, { size: 30, align: 'center', fam: 'Bungee', weight: 400, color: '#F6F0E2' });
    ctx.restore();
  }
  function pipe(ctx, y, t, { leak = 0 } = {}) { // la tubería que corre por la calle
    G.rrect(ctx, -40, y - 18, W + 80, 36, 18, { fill: '#7C8A96', lw: 5, seed: 40 });
    for (let x = 60; x < W; x += 220) G.rrect(ctx, x, y - 24, 30, 48, 6, { fill: '#5E6B76', lw: 4, seed: 41 + x });
    // agua corriendo dentro (rayitas que avanzan)
    ctx.save(); ctx.globalAlpha = 0.6; for (let k = 0; k < 8; k++) { const x = ((t * 260 + k * 160) % (W + 200)) - 100; G.line(ctx, [[x, y], [x + 50, y]], { color: '#DFF3FF', lw: 6, seed: 50 + k }); } ctx.restore();
  }
  function hose(ctx, x0, y0, x1, y1, t, flow = 1) {
    G.line(ctx, [[x0, y0], [x0 + 60, y0 + 80], [(x0 + x1) / 2, y1 + 40], [x1, y1]], { color: '#2E8B57', lw: 16, seed: 60 });
    if (flow > 0) for (let k = 0; k < 10; k++) { const p = (t * 1.6 + k / 10) % 1; G.ellipse(ctx, x1 + 30 + p * 140, y1 - 40 + p * p * 220, 10 * (1 - p) + 4, 14 * (1 - p) + 4, { fill: '#9ED8F5', lw: 2, seed: 61 + k }); }
  }
  function houseFront(ctx, x, y, w, h, col, seed, { faucet = null, t = 0 } = {}) {
    G.rrect(ctx, x, y, w, h, 6, { fill: col, lw: 5, seed, hatch: { color: 'rgba(80,40,20,0.10)', gap: 11 } });
    G.rrect(ctx, x - 10, y - 20, w + 20, 26, 4, { fill: Ch.shade(col, 0.72), lw: 4, seed: seed + 1 });
    G.rrect(ctx, x + w * 0.1, y + h - 230, 110, 230, 6, { fill: '#8E6444', lw: 5, seed: seed + 2 });
    G.rrect(ctx, x + w * 0.5, y + 70, 140, 120, 6, { fill: '#5A7C8C', lw: 5, seed: seed + 3 });
    for (let g = 1; g < 4; g++) G.line(ctx, [[x + w * 0.5 + g * 35, y + 74], [x + w * 0.5 + g * 35, y + 186]], { color: INK, lw: 3, seed: seed + 4 + g });
    if (faucet) { // la pila del frente con su chorro
      const fx = x + w * 0.62, fy = y + h - 70;
      G.rrect(ctx, fx - 10, fy - 40, 20, 50, 4, { fill: '#9AA6B2', lw: 4, seed: seed + 9 });
      G.rrect(ctx, fx - 10, fy - 44, 60, 16, 6, { fill: '#9AA6B2', lw: 4, seed: seed + 10 });
      const str = faucet.strength;
      if (str > 0.05) G.line(ctx, [[fx + 44, fy - 30], [fx + 44 + Math.sin(t * 20) * 2, fy - 30 + 120 * str]], { color: '#7EC8F0', lw: 4 + 12 * str, seed: seed + 11 });
      else { const p = (t * 1.3) % 1; G.ellipse(ctx, fx + 44, fy - 24 + p * 100, 7, 10, { fill: '#7EC8F0', lw: 2, seed: seed + 12 }); }
    }
  }
  const ground = (ctx, y, col = '#C9B79C') => G.rrect(ctx, -20, y, W + 40, H - y + 40, 0, { fill: col, lw: 4, seed: 800, hatch: { color: 'rgba(90,60,30,0.12)', gap: 12 } });
  function bucket(ctx, x, y, s, col = '#3D7AB8', full = 0.5) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); G.poly(ctx, [[-44, -90], [44, -90], [34, 0], [-34, 0]], { fill: col, lw: 5, seed: 70 + x }); G.ellipse(ctx, 0, -90, 44, 12, { fill: full > 0.5 ? '#9ED8F5' : '#2A3A4A', lw: 4, seed: 71 + x }); ctx.restore(); }
  function table(ctx, x, y) { G.rrect(ctx, x - 170, y - 20, 340, 30, 6, { fill: '#B98A5E', lw: 5, seed: 90 }); for (const lx of [-150, 140]) G.rrect(ctx, x + lx, y + 10, 16, 110, 4, { fill: '#8E6444', lw: 4, seed: 91 + lx }); G.rrect(ctx, x - 60, y - 60, 120, 44, 4, { fill: '#F6F0E2', lw: 4, seed: 92 }); }
  function wrench(ctx, hx, hy) { ctx.save(); ctx.translate(hx, hy); ctx.rotate(0.6); G.rrect(ctx, -10, -70, 20, 110, 6, { fill: '#9AA6B2', lw: 4, seed: 95 }); G.rrect(ctx, -26, -96, 52, 34, 8, { fill: '#9AA6B2', lw: 4, seed: 96 }); ctx.restore(); }
  function coin(ctx, x, y, r = 28) { G.ellipse(ctx, x, y, r, r, { fill: '#F2C230', lw: 4, seed: Math.round(x) }); G.text(ctx, 'L', x, y + r * 0.38, { size: r * 1.1, align: 'center', fam: 'Bungee', weight: 400, color: '#8A6414' }); }
  function bigX(ctx, p, x0, y0, x1, y1) { if (p <= 0) return; ctx.save(); ctx.globalAlpha = clamp(p * 2); G.line(ctx, [[x0, y0], [lerp(x0, x1, p), lerp(y0, y1, p)]], { color: '#E0503E', lw: 26, seed: 97 }); G.line(ctx, [[x1, y0], [lerp(x1, x0, p), lerp(y0, y1, p)]], { color: '#E0503E', lw: 26, seed: 98 }); ctx.restore(); }
  function gauge(ctx, x, y, v, t) { // manómetro de presión
    G.ellipse(ctx, x, y, 130, 130, { fill: '#F6F0E2', lw: 7, seed: 110 });
    [['#3FA89B', -2.2, -0.9], ['#F2B84B', -0.9, 0.2], ['#E0503E', 0.2, 1.1]].forEach(([c, a0, a1], k) => { ctx.save(); ctx.strokeStyle = c; ctx.lineWidth = 22; ctx.beginPath(); ctx.arc(x, y, 96, a0 - Math.PI / 2 + 0, a1 - Math.PI / 2 + 0); ctx.stroke(); ctx.restore(); });
    const a = lerp(1.0, -2.0, clamp(v)) + Math.sin(t * 18) * 0.03;
    G.line(ctx, [[x, y], [x + Math.sin(a) * 90, y - Math.cos(a) * 90]], { color: INK, lw: 9, seed: 111 });
    G.ellipse(ctx, x, y, 16, 16, { fill: INK, lw: 2, seed: 112 });
    G.text(ctx, 'PRESIÓN', x, y + 80, { size: 26, align: 'center', fam: 'Bungee', weight: 400, color: INK });
  }
  function card(ctx, y, n, t1, t2, col, on, p, logo = false) {
    if (p <= 0) return; const dx = (1 - ease.outCubic(clamp(p))) * (n % 2 ? 900 : -900);
    ctx.save(); ctx.translate(dx, 0); ctx.globalAlpha = on ? 1 : 0.7;
    G.rrect(ctx, 90, y - 80, 900, 160, 30, { fill: '#F6F0E2', lw: on ? 8 : 5, seed: 120 + n });
    G.ellipse(ctx, 180, y, 54, 54, { fill: col, lw: 5, seed: 125 + n });
    G.text(ctx, String(n), 180, y + 22, { size: 60, align: 'center', fam: 'Bungee', weight: 400, color: '#FFF' });
    G.text(ctx, t1, 260, y - 8, { size: 46, fam: 'Bungee', weight: 400, color: INK });
    G.text(ctx, t2, 262, y + 46, { size: 32, color: logo ? '#1E9E57' : '#5A5048', weight: 800 });
    if (logo && LOGO) ctx.drawImage(LOGO, 860, y - 56, 110, 110);
    ctx.restore();
  }

  const film = Shots.film([
    { at: 0, draw: hook, cam: Shots.push(1.0, 1.05) },
    { at: ev.problemas, draw: problemas, in: 'whip', cam: Shots.push(1, 1.07) },
    { at: ev.pleito, draw: pleito, in: 'cut', cam: Shots.push(1, 1.03) },
    { at: ev.tension, draw: tension, in: 'whip' },
    { at: ev.saber, draw: saber, in: 'cut', cam: Shots.push(1, 1.05) },
    { at: ev.mito, draw: mito, in: 'flash' },
    { at: ev.pasos, draw: pasos, in: 'whip' },
    { at: ev.final, draw: final, in: 'flash', cam: Shots.push(1.06, 1) },
    { at: ev.cierre, draw: cierre, in: 'cut' },
  ]);

  Studio.film({
    post: { vignette: 0.2, grain: 0.04, paper: 0.35 },
    fadeOut: 0.6,
    async init() {
      VO = await Studio.loadJSON('out/voice.json');
      LOGO = await Studio.loadImage('assets/conafeph-logo.png');
      SUBS = Subs.fromVoice({ lines: VO.lines.filter((l) => l.scene !== 'cierre') }, { maxWords: 5 });
    },
    draw(ctx, t) {
      film(ctx, t);
      if (t < ev.cierre) Subs.draw(ctx, t, SUBS, { style: 'pop' });
      // marca arriba, dentro de la zona segura
      if (t < ev.cierre && LOGO) { G.rrect(ctx, 380, SAFE.y + 8, 320, 66, 33, { fill: '#F6F0E2', lw: 4, seed: 500 }); ctx.drawImage(LOGO, 388, SAFE.y + 12, 58, 58); G.text(ctx, 'CONAFEPH', 570, SAFE.y + 54, { size: 30, align: 'center', fam: 'Bungee', weight: 400, color: '#0E2A47' }); }
    },
  });
})();
