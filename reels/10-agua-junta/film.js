// EL AGUA DE TODOS — cada cuadro es una función pura de t. Bocas sincronizadas con las voces reales.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, Subs = globalThis.Subs, Shots = globalThis.Shots, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { clamp, lerp, ease } = U;
  const { ev, at, wt } = S;
  const W = G.W, H = G.H, SAFE = G.SAFE;
  let VO = null, SUBS = [], LOGO = null;

  // ---------- el elenco (nuevo para este video) ----------
  const CAST = {
    tono: { outfit: 'shirt', shirt: '#3D7A74', bottoms: 'pants', shorts: '#4A3A2E', skin: '#A86E4B', hairStyle: 'short', hair: '#8E8E8E', facialHair: 'beard', build: 'heavy', headwear: 'cap', headwearColor: '#C8453B', shoes: '#2A2A2A' },
    silvia: { outfit: 'dress', shirt: '#E8718D', skin: '#D59B72', hairStyle: 'bun', hair: '#2A1E18', glasses: 'round', shoes: '#6B4E8A' },
    asesor: { outfit: 'shirt', shirt: '#1E9E57', bottoms: 'pants', shorts: '#203A5C', skin: '#B97D55', hairStyle: 'curlytop', hair: '#1E1612', facialHair: 'trimmed', shoes: '#2A2A2A' },
    v1: { outfit: 'tee', shirt: '#F2B84B', bottoms: 'pants', shorts: '#3A3A44', skin: '#8D5A3B', hairStyle: 'curly' },
    v2: { outfit: 'kameez', shirt: '#6B8ACF', bottoms: 'skirt', shorts: '#2F3B4A', skin: '#C98A62', hairStyle: 'long', hair: '#3A2418' },
    v3: { outfit: 'hoodie', shirt: '#E07A5F', bottoms: 'pants', shorts: '#27305C', skin: '#D59B72', hairStyle: 'buzz' },
  };
  globalThis.CAST = CAST;
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

  // ---------- tomas ----------
  function hook(ctx, t) {
    sky(ctx, '#7EC4EC', '#D8EEF8');
    G.ellipse(ctx, 540, 980, 900, 380, { fill: '#8BBF6A', lw: 5, seed: 5 }); // el cerro
    tank(ctx, 760, 720, 0.8, t);
    houseFront(ctx, -60, 700, 420, 420, '#E9C46A', 10); houseFront(ctx, 700, 740, 420, 380, '#E07A5F', 50);
    ground(ctx, 1120); pipe(ctx, 1150, t);
    table(ctx, 300, 1190);
    Ch.person(ctx, { x: 300, y: 1300, s: 0.82, pose: 'stand', style: CAST.silvia, gesture: 'typing', mouth: 'smile', eyes: 'normal', seed: 200 });
    // la fila de vecinos pagando
    [['v1', 520], ['v2', 650], ['v3', 780]].forEach(([w, x], i) => Ch.person(ctx, { x, y: 1290, s: 0.68, pose: 'stand', style: CAST[w], gesture: i === 0 ? 'point' : null, mouth: 'smile', look: -0.6, seed: 210 + i * 30 }));
    const me = wt(at('hook'), 'menos');
    const tx = lerp(1200, 910, ease.outCubic(clamp((t - me + 0.4) / 0.8)));
    Ch.person(ctx, { x: tx, y: 1290, s: 0.74, sx: -1, pose: 'stand', style: CAST.tono, crossArms: t > me, mouth: 'smirk', eyes: 'normal', look: -0.3, seed: 240 });
    title(ctx, 'TODOS PAGAN', 430, clamp((t - 0.6) / 0.5));
    title(ctx, '…MENOS UNO', 560, clamp((t - me + 0.1) / 0.4), { color: '#E0503E', size: 96, rot: 0.03 });
    for (let k = 0; k < 3; k++) { const p = (t * 0.8 + k / 3) % 1; coin(ctx, 300 + Math.sin(k * 2) * 40, 1130 - p * 160, 24); }
  }
  function noche(ctx, t) {
    sky(ctx, '#0E1A3A', '#2B3B6A');
    for (let k = 0; k < 40; k++) G.ellipse(ctx, G.rnd(k, 1) * W, 280 + G.rnd(k, 2) * 700, 3, 3, { fill: '#FFF', lw: 0, seed: 300 + k });
    G.ellipse(ctx, 820, 520, 70, 70, { fill: '#F4EBC8', lw: 4, seed: 310 });
    houseFront(ctx, 520, 700, 520, 460, '#5A6E8C', 320);
    ground(ctx, 1160, '#4A5468'); pipe(ctx, 1190, t);
    const con = clamp((t - (S.at('noche').t + 0.6)) / 1.2);
    hose(ctx, 420, 1200, 660, 1090, t, con);
    // la linterna
    ctx.save(); ctx.globalAlpha = 0.18 + 0.04 * Math.sin(t * 9); ctx.fillStyle = '#FFF3A8'; ctx.beginPath(); ctx.moveTo(330, 900); ctx.lineTo(560, 1210); ctx.lineTo(300, 1240); ctx.fill(); ctx.restore();
    Ch.person(ctx, { x: 260, y: 1300, s: 0.8, pose: 'stand', style: CAST.tono, handR: [120, -260], handL: [-60, -320], mouth: 'smirk', eyes: 'normal', look: 0.8, legBend: 0.4, seed: 240 });
    wrench(ctx, 260 + 0.8 * 120, 1300 + 0.8 * -260);
    title(ctx, 'DE NOCHE…', 430, clamp((t - ev.noche) / 0.4), { color: '#F2C230' });
    tag(ctx, 'SIN PERMISO', 540, 640, clamp((t - wt(at('noche'), 'permiso')) / 0.3), { bg: '#E0503E', fg: '#FFF', rot: -0.05 });
  }
  function pleito(ctx, t) {
    const tT = t >= ev.tono - 0.15;
    sky(ctx, tT ? '#3D7A74' : '#E8718D', tT ? '#1F4A46' : '#B04A66');
    ground(ctx, 1180, tT ? '#B7C98A' : '#E6CFA8'); pipe(ctx, 1210, t);
    Ch.person(ctx, { x: 290, y: 1300, s: 1.15, pose: 'stand', style: CAST.silvia, gesture: !tT ? 'point' : 'akimbo', mouth: mouthOf('silvia', t) || (tT ? 'flat' : 'open'), brows: 'determined', eyes: 'normal', look: 0.6, seed: 200 });
    Ch.person(ctx, { x: 790, y: 1300, s: 1.15, sx: -1, pose: 'stand', style: CAST.tono, crossArms: tT, gesture: tT ? null : 'shrug', mouth: mouthOf('tono', t) || (tT ? 'smirk' : 'o'), brows: tT ? 'neutral' : 'worried', eyes: 'normal', look: -0.6, seed: 240 });
    tag(ctx, tT ? 'DON TOÑO' : 'DOÑA SILVIA · TESORERA', 540, 420, 1, { bg: tT ? '#F6F0E2' : '#F6F0E2', size: 40 });
  }
  function tension(ctx, t) {
    sky(ctx, '#F2E3C6', '#E9D2A6');
    const L = at('tension'), de = wt(L, 'derecho'), bo = wt(L, 'bomba'), tu = wt(L, 'tubos'), lu = wt(L, 'luz'), cu = wt(L, 'cuota');
    tag(ctx, 'EL AGUA ES UN DERECHO', 540, 420, clamp((t - de + 0.2) / 0.3), { bg: '#5FA8D3', fg: '#FFF', size: 46 });
    // el sistema: tanque → bomba → tubos → casas
    tank(ctx, 220, 1060, 0.6, t);
    if (t > bo - 0.2) { G.rrect(ctx, 360, 900, 160, 120, 14, { fill: '#C8453B', lw: 5, seed: 130 }); G.text(ctx, 'BOMBA', 440, 975, { size: 30, align: 'center', fam: 'Bungee', weight: 400, color: '#FFF' }); }
    if (t > tu - 0.2) { G.line(ctx, [[300, 1000], [360, 960]], { color: '#7C8A96', lw: 18, seed: 131 }); G.line(ctx, [[520, 960], [600, 960], [600, 1060], [900, 1060]], { color: '#7C8A96', lw: 18, seed: 132 }); }
    if (t > lu - 0.2) { const b = 0.5 + 0.5 * Math.sin(t * 10); G.poly(ctx, [[440, 820], [410, 870], [440, 870], [420, 910], [470, 850], [440, 850], [460, 820]], { fill: `rgba(242,194,48,${0.6 + 0.4 * b})`, lw: 4, seed: 133 }); }
    [700, 830].forEach((x, k) => houseFront(ctx, x - 60, 1080, 150, 160, ['#E9C46A', '#8AB6A8'][k], 140 + k * 10));
    const cp = clamp((t - cu) / 0.5);
    if (cp > 0) for (let k = 0; k < 6; k++) { const p = (t * 0.9 + k / 6) % 1; coin(ctx, lerp(760, 440, p), 1300 - Math.sin(p * Math.PI) * 140, 26); }
    tag(ctx, 'SE PAGA ENTRE TODOS', 540, 1300 - 40, cp, { bg: '#F2B84B', size: 44 });
  }
  function presion(ctx, t) {
    sky(ctx, '#7EC4EC', '#D8EEF8');
    const L = at('presion'), pr = wt(L, 'presion'), da = wt(L, 'danar');
    const drop = clamp((t - pr + 0.4) / 1.0);
    houseFront(ctx, -40, 700, 380, 420, '#E9C46A', 10, { faucet: { strength: 1 - drop * 0.95 }, t });
    houseFront(ctx, 360, 740, 360, 380, '#8AB6A8', 50, { faucet: { strength: 1 - drop * 0.9 }, t });
    ground(ctx, 1120); pipe(ctx, 1150, t);
    hose(ctx, 800, 1160, 880, 1060, t, 1);
    gauge(ctx, 860, 640, 1 - drop * 0.85, t);
    title(ctx, 'BAJA LA\nPRESIÓN', 430, clamp((t - pr) / 0.4), { color: '#5FA8D3', size: 92 });
    if (t > da) { const p = clamp((t - da) / 0.4); ctx.save(); ctx.globalAlpha = p; G.line(ctx, [[560, 1130], [600, 1170], [580, 1190], [630, 1230]], { color: '#E0503E', lw: 8, seed: 150 }); ctx.restore(); tag(ctx, 'DAÑA LA RED', 320, 1270, p, { bg: '#E0503E', fg: '#FFF', size: 42 }); }
  }
  function mito(ctx, t) {
    sky(ctx, '#3A1230', '#1A0E2E');
    const L = at('mito'), co = wt(L, 'cortarle'), qu = wt(L, 'quitarle'), sa = wt(L, 'salida');
    tag(ctx, 'CORTARLE EL TUBO', 540, 640, clamp((t - co + 0.2) / 0.3), { size: 50, rot: -0.04 });
    tag(ctx, 'QUITARLE EL AGUA', 540, 820, clamp((t - qu + 0.2) / 0.3), { size: 50, rot: 0.04 });
    bigX(ctx, clamp((t - sa + 0.4) / 0.4), 170, 560, 910, 900);
    title(ctx, 'TAMPOCO ES\nLA SALIDA', 1080, clamp((t - sa + 0.1) / 0.4), { color: '#E0503E', size: 96 });
  }
  function pasos(ctx, t) {
    const act = t >= ev.p3 - 0.2 ? 2 : t >= ev.p2 - 0.2 ? 1 : 0;
    sky(ctx, ['#F29C8F', '#8FB3F2', '#7FD3A0'][act], '#203A5C');
    card(ctx, 470, 1, 'HABLAR', 'Ofrecer un arreglo de pago', '#E07A5F', act === 0, clamp((t - ev.pasos) / 0.4));
    card(ctx, 660, 2, 'ASAMBLEA', 'Reglas claras para todos', '#5FA8D3', act === 1, clamp((t - ev.p2 + 0.2) / 0.4));
    card(ctx, 850, 3, 'ORIENTACIÓN', 'en CONAFEPH', '#1E9E57', act === 2, clamp((t - ev.p3 + 0.2) / 0.4), true);
    Ch.person(ctx, { x: 250, y: 1300, s: 0.62, pose: 'stand', style: CAST.asesor, gesture: 'pointUp', mouth: 'smile', eyes: 'happy', seed: 260 });
    tag(ctx, 'ASESOR CONAFEPH', 640, 1180, clamp((t - ev.pasos - 0.3) / 0.3), { bg: '#1E9E57', fg: '#FFF', size: 38 });
  }
  function final(ctx, t) {
    sky(ctx, '#FFD27A', '#FFF1D6');
    tank(ctx, 830, 760, 0.7, t);
    ground(ctx, 1150, '#B7D98A'); pipe(ctx, 1180, t);
    table(ctx, 360, 1210);
    Ch.person(ctx, { x: 290, y: 1300, s: 0.75, pose: 'stand', style: CAST.silvia, handR: [130, -300], mouth: 'grin', eyes: 'happy', seed: 200 });
    Ch.person(ctx, { x: 470, y: 1300, s: 0.75, sx: -1, pose: 'stand', style: CAST.tono, handR: [130, -300], mouth: 'grin', eyes: 'happy', seed: 240 });
    coin(ctx, 380, 1150 - Math.abs(Math.sin(t * 4)) * 20, 26);
    [['v1', 680], ['v2', 840]].forEach(([w, x], i) => { Ch.person(ctx, { x, y: 1290, s: 0.62, pose: 'stand', style: CAST[w], gesture: 'cheer', mouth: 'open', eyes: 'happy', seed: 210 + i * 30 }); bucket(ctx, x + 70, 1300, 0.7, '#3D7AB8', 1); });
    title(ctx, 'EL AGUA\nES DE TODOS', 430, clamp((t - ev.final) / 0.4), { color: '#5FA8D3', size: 100 });
    G.confetti(ctx, t, ev.final, { n: 60, seed: 4 });
  }
  function cierre(ctx, t) {
    sky(ctx, '#0E2A47', '#14335A');
    const p = clamp((t - ev.cierre) / 0.7), k = ease.outBack(p, 2);
    ctx.save(); ctx.translate(540, 760); ctx.scale(k, k); G.ellipse(ctx, 0, 0, 250, 250, { fill: '#FFF', lw: 6, seed: 400 }); if (LOGO) ctx.drawImage(LOGO, -220, -220, 440, 440); ctx.restore();
    title(ctx, 'CONAFEPH', 1130, clamp((t - ev.cierre - 0.5) / 0.4), { color: '#FFF', size: 110, rot: 0 });
    tag(ctx, 'ORIENTACIÓN PARA PATRONATOS', 540, 1270, clamp((t - ev.cierre - 1) / 0.3), { bg: '#F2B84B', size: 38 });
  }

  const film = Shots.film([
    { at: 0, draw: hook, cam: Shots.push(1.0, 1.05) },
    { at: ev.noche, draw: noche, in: 'whip', cam: Shots.push(1, 1.07) },
    { at: ev.pleito, draw: pleito, in: 'cut', cam: Shots.push(1, 1.03) },
    { at: ev.tension, draw: tension, in: 'whip' },
    { at: ev.presion, draw: presion, in: 'cut', cam: Shots.push(1, 1.05) },
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
