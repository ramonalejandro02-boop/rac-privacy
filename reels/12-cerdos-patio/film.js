// CRÍA CERDOS EN PLENO BARRIO — cada cuadro es una función pura de t. Bocas sincronizadas con las voces reales.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, Subs = globalThis.Subs, Shots = globalThis.Shots, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { clamp, lerp, ease } = U;
  const { ev, at, wt } = S;
  const W = G.W, H = G.H, SAFE = G.SAFE;
  let VO = null, SUBS = [], LOGO = null;

  // ---------- el elenco (nuevo para este video) ----------
  const CAST = {
    tino: { outfit: 'shirt', shirt: '#B5553C', bottoms: 'pants', shorts: '#5A4632', skin: '#A86E4B', hairStyle: 'short', hair: '#9A9A9A', facialHair: 'mustache', build: 'heavy', shoes: '#4A3A2A' },
    chabela: { outfit: 'tee', shirt: '#2E9C8F', bottoms: 'skirt', shorts: '#F2B84B', skin: '#E6B48C', hairStyle: 'curly', hair: '#2B211E', shoes: '#7A2E3A' },
    hijo1: { outfit: 'tee', shirt: '#F2B84B', bottoms: 'shorts', shorts: '#3D5A80', skin: '#E6B48C', hairStyle: 'buzz', hair: '#2B211E' },
    hija2: { outfit: 'dress', shirt: '#E8718D', skin: '#E6B48C', hairStyle: 'ponytail', hair: '#2B211E' },
    asesor: { outfit: 'shirt', shirt: '#1E9E57', bottoms: 'pants', shorts: '#203A5C', skin: '#8D5A3B', hairStyle: 'quiff', hair: '#1E1612', facialHair: 'trimmed', glasses: 'square', shoes: '#2A2A2A' },
  };
  // ---------- utilería del chiquero ----------
  const PINK = '#F4A6B4';
  function pig(ctx, x, y, s, seed, t, { sx = 1, mud = 0, happy = false } = {}) {
    const b = Math.sin(t * 3 + seed) * 4;
    ctx.save(); ctx.translate(x, y); ctx.scale(s * sx, s);
    for (const lx of [-85, -45, 45, 85]) G.rrect(ctx, lx - 14, -52, 28, 52, 8, { fill: Ch.shade(PINK, 0.88), lw: 4, seed: seed + lx });
    ctx.translate(0, b);
    G.line(ctx, [[-128, -110], [-150, -126], [-160, -110], [-146, -100], [-150, -134]], { color: Ch.shade(PINK, 0.8), lw: 6, seed: seed + 1 });
    G.ellipse(ctx, 0, -100, 135, 72, { fill: PINK, lw: 5, seed: seed + 2 });
    if (mud) { ctx.save(); ctx.globalAlpha = mud; G.ellipse(ctx, -50, -80, 40, 22, { fill: '#7A5A3A', lw: 0, seed: seed + 3 }); G.ellipse(ctx, 40, -120, 26, 16, { fill: '#7A5A3A', lw: 0, seed: seed + 4 }); ctx.restore(); }
    G.poly(ctx, [[98, -160], [112, -196], [134, -158]], { fill: Ch.shade(PINK, 0.85), lw: 4, seed: seed + 5, step: 10 });
    G.ellipse(ctx, 128, -118, 58, 52, { fill: PINK, lw: 5, seed: seed + 6 });
    G.poly(ctx, [[140, -158], [162, -192], [170, -150]], { fill: Ch.shade(PINK, 0.85), lw: 4, seed: seed + 7, step: 10 });
    G.ellipse(ctx, 178, -106, 26, 22, { fill: '#E98597', lw: 4, seed: seed + 8 });
    G.ellipse(ctx, 171, -106, 4, 6, { fill: INK, lw: 0, seed: seed + 9 }); G.ellipse(ctx, 185, -106, 4, 6, { fill: INK, lw: 0, seed: seed + 10 });
    if (happy) G.line(ctx, [[126, -132], [136, -140], [146, -132]], { color: INK, lw: 4, seed: seed + 11 });
    else G.ellipse(ctx, 138, -134, 6, 8, { fill: INK, lw: 0, seed: seed + 11 });
    ctx.restore();
  }
  function fence(ctx, x0, x1, y, h = 110, seed = 900) {
    for (let x = x0; x <= x1; x += 70) G.rrect(ctx, x - 9, y - h, 18, h + 6, 4, { fill: '#9C6B43', lw: 4, seed: seed + x });
    for (const r of [0.3, 0.72]) G.rrect(ctx, x0 - 14, y - h * r - 8, x1 - x0 + 28, 16, 5, { fill: '#B5834F', lw: 4, seed: seed + r * 100 });
  }
  function mudPool(ctx, x, y, w) { G.ellipse(ctx, x, y, w, w * 0.18, { fill: '#7A5A3A', lw: 3, seed: 910 }); }
  function stink(ctx, x, y, t, p, n = 3, s = 1) {
    if (p <= 0) return;
    for (let k = 0; k < n; k++) {
      const q = (t * 0.45 + k / n) % 1, xx = x + (k - (n - 1) / 2) * 70 * s, yy = y - q * 260 * s;
      const pts = []; for (let j = 0; j < 7; j++) pts.push([xx + Math.sin(j * 1.3 + t * 4 + k) * 16 * s, yy - j * 22 * s]);
      ctx.save(); ctx.globalAlpha = p * Math.sin(Math.PI * q) * 0.9; G.line(ctx, pts, { color: '#8DB75A', lw: 9 * s, seed: 920 + k }); ctx.restore();
    }
  }
  function flies(ctx, cx, cy, t, n, r = 120) {
    for (let k = 0; k < n; k++) {
      const a = t * (3 + k % 3) + k * 2.1, x = cx + Math.cos(a) * r * (0.5 + (k % 4) * 0.18), y = cy + Math.sin(a * 1.3) * r * 0.5 + Math.sin(t * 9 + k) * 8;
      ctx.save(); ctx.globalAlpha = 0.75; G.ellipse(ctx, x - 7, y - 9, 9, 6, { fill: '#DDEEFF', lw: 2, seed: 930 + k }); G.ellipse(ctx, x + 7, y - 9, 9, 6, { fill: '#DDEEFF', lw: 2, seed: 940 + k }); ctx.restore();
      G.ellipse(ctx, x, y, 8, 6, { fill: INK, lw: 0, seed: 950 + k });
    }
  }
  function stream(ctx, x0, x1, y, t, p) { // agua sucia del corral hacia la calle
    if (p <= 0) return; const xe = lerp(x0, x1, ease.outCubic(clamp(p)));
    const top = [], bot = []; for (let x = x0; x <= xe; x += 30) { const w = 16 + 10 * Math.sin(x * 0.03); top.push([x, y - w + Math.sin(x * 0.02) * 10]); bot.unshift([x, y + w + Math.sin(x * 0.02) * 10]); }
    if (top.length > 1) G.poly(ctx, top.concat(bot), { fill: '#8A7048', lw: 4, seed: 960, step: 30 });
    for (let k = 0; k < 6; k++) { const q = (t * 0.5 + k / 6) % 1, x = lerp(x0, xe, q); G.ellipse(ctx, x, y + Math.sin(x * 0.02) * 10, 8, 4, { fill: '#B39468', lw: 0, seed: 970 + k }); }
  }
  function germ(ctx, x, y, r, t, seed, col = '#7FB34A') {
    const w = Math.sin(t * 5 + seed) * 0.15; ctx.save(); ctx.translate(x, y); ctx.rotate(w);
    for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; G.line(ctx, [[Math.cos(a) * r, Math.sin(a) * r], [Math.cos(a) * r * 1.35, Math.sin(a) * r * 1.35]], { color: col, lw: 7, seed: seed + k }); }
    G.ellipse(ctx, 0, 0, r, r, { fill: col, lw: 5, seed: seed + 9 });
    G.ellipse(ctx, -r * 0.3, -r * 0.15, r * 0.14, r * 0.2, { fill: INK, lw: 0, seed: seed + 10 }); G.ellipse(ctx, r * 0.3, -r * 0.15, r * 0.14, r * 0.2, { fill: INK, lw: 0, seed: seed + 11 });
    G.line(ctx, [[-r * 0.3, r * 0.35], [0, r * 0.2], [r * 0.3, r * 0.35]], { color: INK, lw: 4, seed: seed + 12 });
    ctx.restore();
  }
  function phone(ctx, x, y, p, t) {
    if (p <= 0) return; const k = ease.outBack(clamp(p), 2);
    ctx.save(); ctx.translate(x, y); ctx.rotate(0.08); ctx.scale(k, k);
    G.rrect(ctx, -110, -190, 220, 380, 30, { fill: '#2A2A30', lw: 6, seed: 980 });
    G.rrect(ctx, -92, -160, 184, 320, 14, { fill: '#F6F0E2', lw: 3, seed: 981 });
    G.rrect(ctx, -76, -140, 152, 110, 8, { fill: '#F4A6B4', lw: 3, seed: 982 });
    G.ellipse(ctx, 0, -85, 40, 40, { fill: '#F2B84B', lw: 4, seed: 984 }); G.line(ctx, [[-22, -102], [-8, -94]], { color: INK, lw: 5, seed: 985 }); G.line(ctx, [[22, -102], [8, -94]], { color: INK, lw: 5, seed: 986 }); G.line(ctx, [[-16, -66], [0, -74], [16, -66]], { color: INK, lw: 5, seed: 987 });
    for (let k2 = 0; k2 < 3; k2++) G.rrect(ctx, -76, -10 + k2 * 36, 152 - k2 * 30, 16, 6, { fill: '#C9C1B0', lw: 0, seed: 983 + k2 });
    G.text(ctx, Math.floor(120 + t * 40) + ' COMPARTIDOS', 0, 140, { size: 20, align: 'center', fam: 'Bungee', weight: 400, color: '#E0503E' });
    ctx.restore();
  }
  function streetScene(ctx, t, o = {}) { // la cuadra: casa de don Tino con su corral y la casa de doña Chabela
    sky(ctx, o.top ?? '#9FD3C7', o.bot ?? '#E8F4EC');
    houseFront(ctx, -40, 660, 560, 460, '#A8C686', 10);
    houseFront(ctx, 600, 720, 520, 400, '#F4C27A', 50);
    ground(ctx, 1120, '#C7B48E');
  }
  function corral(ctx, t, o = {}) { // corral en el frente de la casa de don Tino
    mudPool(ctx, 290, 1250, o.clean ? 0 : 200);
    pig(ctx, 170, 1270, 0.82, 10, t, { mud: o.clean ? 0 : 1, happy: o.clean });
    pig(ctx, 420, 1290, 0.76, 30, t, { sx: -1, mud: o.clean ? 0 : 0.8, happy: o.clean });
    fence(ctx, 40, 560, 1300, 95);
  }

  // ---------- tomas ----------
  function hook(ctx, t) {
    streetScene(ctx, t);
    const L = at('hook'), ce = wt(L, 'cerdos'), cu = wt(L, 'cuadra'), ch = wt(L, 'chiquero');
    corral(ctx, t);
    stink(ctx, 290, 1120, t, clamp((t - cu + 0.3) / 0.6), 4, 1.2);
    if (t > cu) stink(ctx, 860, 1000, t + 1.3, clamp((t - cu) / 0.8), 3, 1);
    Ch.person(ctx, { x: 700, y: 1300, s: 0.78, pose: 'stand', style: CAST.tino, gesture: t > ce ? 'thumbsUp' : null, mouth: 'grin', eyes: 'happy', seed: 300 });
    title(ctx, 'TODA LA CUADRA', 430, clamp((t - cu + 0.1) / 0.4));
    title(ctx, 'HUELE A\nCHIQUERO', 545, clamp((t - ch) / 0.4), { color: '#8DB75A', size: 100, rot: 0.03 });
  }
  function problemas(ctx, t) {
    streetScene(ctx, t, { top: '#D8D49A', bot: '#F1EBC8' });
    const L = at('problemas'), mo = wt(L, 'moscas'), ol = wt(L, 'olor'), ag = wt(L, 'agua'), ca = wt(L, 'calle');
    corral(ctx, t);
    stream(ctx, 520, 1100, 1180, t, clamp((t - ag) / 1.6));
    flies(ctx, 300, 1050, t, Math.round(12 * clamp((t - mo + 0.3) / 0.8)), 170);
    stink(ctx, 290, 1120, t, 1, 4, 1.3);
    tag(ctx, 'MOSCAS', 300, 520, clamp((t - mo + 0.1) / 0.3), { bg: INK, fg: '#F6F0E2', size: 50, rot: -0.05 });
    tag(ctx, 'MAL OLOR', 760, 560, clamp((t - ol + 0.1) / 0.3), { bg: '#8DB75A', size: 50, rot: 0.05 });
    tag(ctx, 'AGUA SUCIA A LA CALLE', 540, 780, clamp((t - ag) / 0.3), { bg: '#8A7048', fg: '#FFF', size: 42 });
    if (t > ag - 0.4) Ch.person(ctx, { ...Ch.walk(t, { x0: 1150, speed: -150, t0: ag - 0.4 }), y: 1300, s: 0.7, sx: -1, style: CAST.chabela, gesture: 'facepalm', brows: 'worried', eyes: 'closed', mouth: 'wavy', seed: 330 });
  }
  function pleito(ctx, t) {
    const tT = t >= ev.tino - 0.15;
    sky(ctx, tT ? '#6B8E4E' : '#2E9C8F', tT ? '#3A5230' : '#1D5E57');
    ground(ctx, 1180, tT ? '#C7B48E' : '#D8C9B0');
    pig(ctx, 520, 1290, 0.72, 50, t, { mud: 1 });
    Ch.person(ctx, { x: 270, y: 1300, s: 1.12, pose: 'stand', style: CAST.chabela, gesture: !tT ? 'point' : 'akimbo', mouth: mouthOf('chabela', t) || (tT ? 'flat' : 'open'), brows: 'determined', eyes: 'normal', look: 0.6, seed: 330 });
    Ch.person(ctx, { x: 810, y: 1300, s: 1.12, sx: -1, pose: 'stand', style: CAST.tino, gesture: tT ? 'shrug' : null, crossArms: !tT, mouth: mouthOf('tino', t) || (tT ? 'flat' : 'smirk'), brows: tT ? 'worried' : 'neutral', eyes: 'normal', look: -0.6, seed: 300 });
    tag(ctx, tT ? 'DON TINO · DUEÑO DE LOS CERDOS' : 'DOÑA CHABELA · VECINA', 540, 420, 1, { size: tT ? 34 : 40 });
  }
  function tension(ctx, t) {
    const L = at('tension'), su = wt(L, 'sustento'), co = wt(L, 'costumbre'), sa = wt(L, 'salud');
    const sp = ease.outCubic(clamp((t - ev.tension) / 0.5)), mx = lerp(1080, 540, sp);
    ctx.fillStyle = '#6B8E4E'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#2E9C8F'; ctx.fillRect(mx, 0, W, H);
    G.line(ctx, [[mx, 0], [mx, H]], { color: INK, lw: 10, seed: 700 });
    pig(ctx, 140, 1262, 0.5, 70, t);
    Ch.person(ctx, { x: 300, y: 1260, s: 0.8, pose: 'stand', style: CAST.tino, gesture: 'thumbsUp', mouth: 'flat', eyes: 'normal', seed: 300 });
    Ch.person(ctx, { x: 760, y: 1260, s: 0.8, pose: 'stand', style: CAST.chabela, gesture: 'akimbo', mouth: 'flat', eyes: 'normal', seed: 330 });
    Ch.person(ctx, { x: 910, y: 1260, s: 0.48, pose: 'stand', style: CAST.hijo1, mouth: 'wavy', brows: 'worried', eyes: 'normal', seed: 380 });
    tag(ctx, 'SU SUSTENTO', 280, 560, clamp((t - su + 0.2) / 0.3), { size: 40, rot: -0.05 });
    tag(ctx, 'SU COSTUMBRE', 280, 680, clamp((t - co + 0.2) / 0.3), { size: 40, rot: 0.03 });
    tag(ctx, 'LA SALUD', 800, 560, clamp((t - sa + 0.1) / 0.3), { size: 46, rot: 0.05 });
    tag(ctx, 'DE SUS HIJOS', 800, 680, clamp((t - sa - 0.2) / 0.3), { size: 36, rot: -0.03 });
  }
  function saber(ctx, t) {
    sky(ctx, '#2F7D6D', '#1E5248');
    const L = at('saber'), de = wt(L, 'delito'), li = wt(L, 'limpio'), ca = wt(L, 'calle'), ri = wt(L, 'riesgo'), to = wt(L, 'todos');
    tag(ctx, 'CRIAR ANIMALES: NO ES DELITO', 540, 430, clamp((t - de + 0.3) / 0.3), { bg: '#F6F0E2', size: 32 });
    title(ctx, 'CORRAL\nLIMPIO', 600, clamp((t - li + 0.2) / 0.4), { color: '#7FD3A0', size: 100 });
    const cp = clamp((t - ca + 0.4) / 0.4);
    if (cp > 0) { stream(ctx, 140, 940, 930, t, cp); bigX(ctx, clamp((t - ca) / 0.4), 380, 850, 700, 1010); tag(ctx, 'NADA A LA CALLE', 540, 1060, cp, { bg: '#E0503E', fg: '#FFF', size: 44 }); }
    const rp = clamp((t - ri + 0.2) / 0.4);
    if (rp > 0) { for (let k = 0; k < 4; k++) germ(ctx, 220 + k * 210, 1215 - (k % 2) * 30, 34 * ease.outBack(clamp(rp * 1.5 - k * 0.15), 2), t, 1000 + k * 20, ['#7FB34A', '#C77DDB', '#F2B84B', '#7FB34A'][k]); }
  }
  function mito(ctx, t) {
    sky(ctx, '#3A1230', '#1A0E2E');
    const L = at('mito'), am = wt(L, 'amenazarlo'), re = wt(L, 'redes'), em = wt(L, 'empeora');
    tag(ctx, 'AMENAZAS', 540, 440, clamp((t - am + 0.2) / 0.3), { size: 56, rot: -0.04 });
    phone(ctx, 540, 720, clamp((t - re + 0.5) / 0.4), t);
    tag(ctx, 'EXHIBIRLO EN REDES', 540, 930, clamp((t - re + 0.2) / 0.3), { size: 44, rot: 0.04 });
    bigX(ctx, clamp((t - em + 0.3) / 0.4), 190, 400, 890, 980);
    title(ctx, 'SOLO EMPEORA\nEL PLEITO', 1090, clamp((t - em) / 0.4), { color: '#E0503E', size: 86 });
  }
  function pasos(ctx, t) {
    const act = t >= ev.p3 - 0.2 ? 2 : t >= ev.p2 - 0.2 ? 1 : 0;
    sky(ctx, ['#F29C8F', '#8FB3F2', '#7FD3A0'][act], '#203A5C');
    card(ctx, 470, 1, 'CONVERSAR', 'Limpieza diaria y corral lejos', '#E07A5F', act === 0, clamp((t - ev.pasos) / 0.4));
    card(ctx, 660, 2, 'PATRONATO', 'Reglas de salud en el barrio', '#5FA8D3', act === 1, clamp((t - ev.p2 + 0.2) / 0.4));
    card(ctx, 850, 3, 'ORIENTACIÓN', 'en CONAFEPH', '#1E9E57', act === 2, clamp((t - ev.p3 + 0.2) / 0.4), true);
    Ch.person(ctx, { x: 250, y: 1300, s: 0.62, pose: 'stand', style: CAST.asesor, gesture: act === 2 ? 'thumbsUp' : 'pointUp', mouth: 'smile', eyes: 'happy', seed: 360 });
    tag(ctx, 'ASESOR CONAFEPH', 650, 1180, clamp((t - ev.pasos - 0.3) / 0.3), { bg: '#1E9E57', fg: '#FFF', size: 40 });
  }
  function final(ctx, t) {
    streetScene(ctx, t, { top: '#FFD27A', bot: '#FFF1D6' });
    // corral limpio y lejos de la calle, cerdos contentos, niños jugando
    pig(ctx, 140, 1140, 0.5, 10, t, { happy: true }); pig(ctx, 330, 1150, 0.46, 30, t, { sx: -1, happy: true });
    fence(ctx, 30, 450, 1160, 70);
    for (let k = 0; k < 5; k++) { const q = (t * 0.7 + k / 5) % 1; ctx.save(); ctx.globalAlpha = Math.sin(Math.PI * q); const sx0 = 80 + k * 90, sy0 = 1020 - q * 60; G.poly(ctx, [[sx0, sy0 - 18], [sx0 + 5, sy0 - 5], [sx0 + 18, sy0], [sx0 + 5, sy0 + 5], [sx0, sy0 + 18], [sx0 - 5, sy0 + 5], [sx0 - 18, sy0], [sx0 - 5, sy0 - 5]], { fill: '#FFF', lw: 2, seed: 990 + k, step: 6 }); ctx.restore(); }
    Ch.person(ctx, { x: 540, y: 1300, s: 0.6, pose: 'stand', style: CAST.tino, gesture: 'wave', mouth: 'grin', eyes: 'happy', seed: 300 });
    const bx = 760 + Math.sin(t * 2.4) * 90, by = 1230 - Math.abs(Math.sin(t * 4.8)) * 140;
    Ch.person(ctx, { x: 690, y: 1300, s: 0.46, pose: 'stand', style: CAST.hijo1, gesture: 'cheer', mouth: 'open', eyes: 'happy', seed: 380 });
    Ch.person(ctx, { x: 830, y: 1300, s: 0.44, pose: 'stand', style: CAST.hija2, gesture: 'cheer', mouth: 'open', eyes: 'happy', seed: 400 });
    ball(ctx, bx, by);
    Ch.person(ctx, { x: 960, y: 1300, s: 0.6, sx: -1, pose: 'stand', style: CAST.chabela, gesture: 'thumbsUp', mouth: 'grin', eyes: 'happy', seed: 330 });
    title(ctx, 'UN BARRIO SANO\nENTRE TODOS', 430, clamp((t - ev.final) / 0.4), { color: '#7FD3A0', size: 86 });
  }
  function cierre(ctx, t) {
    sky(ctx, '#0E2A47', '#14335A');
    const p = clamp((t - ev.cierre) / 0.7), k = ease.outBack(p, 2);
    ctx.save(); ctx.translate(540, 760); ctx.scale(k, k); G.ellipse(ctx, 0, 0, 250, 250, { fill: '#FFF', lw: 6, seed: 400 }); if (LOGO) ctx.drawImage(LOGO, -220, -220, 440, 440); ctx.restore();
    title(ctx, 'CONAFEPH', 1130, clamp((t - ev.cierre - 0.5) / 0.4), { color: '#FFF', size: 110, rot: 0 });
    tag(ctx, 'ORIENTACIÓN PARA PATRONATOS', 540, 1270, clamp((t - ev.cierre - 1) / 0.3), { bg: '#F2B84B', size: 38 });
  }
  function ball(ctx, x, y, r = 30) { G.ellipse(ctx, x, y, r, r, { fill: '#F6F0E2', lw: 4, seed: 680 }); G.poly(ctx, [[x - 8, y - 10], [x + 10, y - 8], [x + 12, y + 8], [x - 6, y + 12], [x - 14, y]], { fill: INK, lw: 2, seed: 681, step: 6 }); }

  const mouthOf = (who, t) => { const m = Subs.mouth(VO, t, who); return m.talking ? m : null; };
  const INK = '#2A2320';
  const title = (ctx, txt, y, p, { size = 110, color = '#F2B84B', rot = -0.03 } = {}) => {
    if (p <= 0) return; const fit = Math.min(1, 920 / Math.max(...txt.split('\n').map((l) => G.measure(ctx, l, size, 'Bungee', 400) + 24))), k = ease.outBack(clamp(p), 2) * fit;
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
