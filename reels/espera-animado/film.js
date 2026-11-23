// LA PELÍCULA — cada cuadro es función pura de t. Estilo cuento ilustrado: hombre cansado + Jesús, luz, nubes pintadas.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { SEG, ev } = S;
  const { clamp, lerp, ease } = U;
  const W = G.W, H = G.H;
  const GROUND = 1560;
  const sm = (t, a, b) => ease.inOutQuad(clamp((t - a) / (b - a)));

  const MAN = { skin: '#D9A47A', hair: '#2B1D14', hairStyle: 'short', facialHair: 'stubble', outfit: 'hoodie', shirt: '#3E5368', bottoms: 'pants', shorts: '#2A2F3A', build: 'regular', sleeves: 'long' };
  const JESUS = { skin: '#E0B089', hair: '#5A3A22', hairStyle: 'long', facialHair: 'beard', outfit: 'thobe', robe: '#F3EEE4', sleeves: 'long', build: 'regular' };
  globalThis.CAST = { hombre: MAN, jesus: JESUS };

  // ---------- cielo, astros, nubes, luz ----------
  function sky(ctx, top, mid, bot) { const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, top); g.addColorStop(0.62, mid); g.addColorStop(1, bot); ctx.fillStyle = g; ctx.fillRect(-40, -40, W + 80, H + 80); }
  function glow(ctx, x, y, r, col, a) { const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${col},${a})`); g.addColorStop(0.3, `rgba(${col},${a * 0.4})`); g.addColorStop(1, `rgba(${col},0)`); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.restore(); }
  function stars(ctx, t, a) { for (let i = 0; i < 120; i++) { const x = U.hash(i, 1) * W, y = U.hash(i, 2) * 1050, r = 1 + U.hash(i, 3) * 2.2; ctx.fillStyle = `rgba(235,240,255,${a * (0.35 + 0.65 * Math.abs(Math.sin(t * 1.2 + i)))})`; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); } }
  function moon(ctx, x, y) { glow(ctx, x, y, 320, '190,210,255', 0.35); G.ellipse(ctx, x, y, 62, 62, { fill: '#F1F4FF', seed: 41, lw: 3 }); }
  function cloud(ctx, x, y, s, fill, seed) { for (let k = 0; k < 6; k++) { const ox = (k - 2.5) * 70 * s, oy = -Math.sin((k / 5) * Math.PI) * 45 * s; G.ellipse(ctx, x + ox, y + oy, 90 * s, 55 * s, { fill, seed: seed + k, lw: 3 }); } }
  function clouds(ctx, t, fill, n, y0, y1, speed, seed) { for (let i = 0; i < n; i++) { const s = 0.8 + U.hash(i, seed) * 0.9, x = ((U.hash(i, seed + 1) * (W + 700) + t * speed * (0.5 + U.hash(i, seed + 2))) % (W + 700)) - 350; cloud(ctx, x, lerp(y0, y1, U.hash(i, seed + 3)), s, fill, seed * 10 + i * 7); } }
  function beam(ctx, x0, x1, a) { if (a <= 0) return; ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.filter = 'blur(26px)'; const g = ctx.createLinearGradient(0, 0, 0, GROUND); g.addColorStop(0, `rgba(255,236,190,${a})`); g.addColorStop(1, `rgba(255,236,190,${a * 0.15})`); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x0 - 70, -40); ctx.lineTo(x0 + 70, -40); ctx.lineTo(x1 + 230, GROUND + 40); ctx.lineTo(x1 - 230, GROUND + 40); ctx.fill(); ctx.restore(); }
  function sparkles(ctx, t, n, y0, y1, a, seed) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (let i = 0; i < n; i++) { const x = U.hash(i, seed) * W + Math.sin(t * 0.7 + i) * 14, y = lerp(y0, y1, U.hash(i, seed + 1)) - ((t * (12 + 28 * U.hash(i, seed + 2))) % 260), tw = Math.max(0, Math.sin(t * 1.8 + i * 1.3)) * a, s = 2 + U.hash(i, seed + 3) * 3; if (tw < 0.03) continue; glow(ctx, x, y, s * 6, '255,232,180', tw * 0.6); ctx.fillStyle = `rgba(255,250,236,${tw})`; ctx.beginPath(); ctx.moveTo(x, y - s * 2.4); ctx.quadraticCurveTo(x, y, x + s * 2.4, y); ctx.quadraticCurveTo(x, y, x, y + s * 2.4); ctx.quadraticCurveTo(x, y, x - s * 2.4, y); ctx.quadraticCurveTo(x, y, x, y - s * 2.4); ctx.fill(); } ctx.restore(); }
  function rain(ctx, t, a) { ctx.strokeStyle = `rgba(200,215,235,${a})`; ctx.lineWidth = 2.5; for (let i = 0; i < 230; i++) { const x = U.hash(i, 77) * (W + 200) - 100, y = ((U.hash(i, 78) * H + t * 1500 * (0.8 + 0.4 * U.hash(i, 79))) % (H + 120)) - 60; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 10, y + 46); ctx.stroke(); } }
  function hills(ctx, back, front) {
    G.poly(ctx, [[-60, GROUND - 230], [260, GROUND - 330], [560, GROUND - 250], [860, GROUND - 360], [1140, GROUND - 260], [1140, H + 60], [-60, H + 60]], { fill: back, seed: 3, hatch: { color: 'rgba(0,0,0,0.12)', gap: 10 } });
    G.poly(ctx, [[-60, GROUND - 40], [400, GROUND - 90], [760, GROUND - 50], [1140, GROUND - 100], [1140, H + 60], [-60, H + 60]], { fill: front, seed: 4, hatch: { color: 'rgba(0,0,0,0.14)', gap: 9 } });
  }
  function sun(ctx, x, y, r, t, a) { glow(ctx, x, y, r * 10, '255,200,130', 0.5 * a); glow(ctx, x, y, r * 3, '255,240,210', 0.9 * a); G.rays && G.rays(ctx, x, y, { t, n: 18, r0: r * 1.3, r1: r * 9, color: `rgba(255,226,160,${0.18 * a})` }); G.ellipse(ctx, x, y, r, r, { fill: '#FFF6E2', seed: 77, lw: 2 }); }
  function birdsFly(ctx, t, t0, a) { for (let i = 0; i < 4; i++) { const u = (t - t0 - i * 0.5) / 7; if (u < 0 || u > 1.2) continue; Ch.bird(ctx, { x: lerp(-120, W + 140, u), y: 560 + i * 90 - Math.sin(u * 3 + i) * 50, s: 1.1 - i * 0.12, color: '#2A2420', t, flap: true, facing: 1 }); } }
  function dove(ctx, x, y, s, a, t) { if (a <= 0) return; const f = Math.sin(t * 5) * 0.35; glow(ctx, x, y, 200 * s, '255,236,190', 0.45 * a); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const [lw, al] of [[22 * s, 0.12], [9 * s, 0.4], [4 * s, 1]]) { ctx.strokeStyle = `rgba(255,248,230,${al * a})`; ctx.lineWidth = lw; ctx.beginPath();
      ctx.moveTo(x - 50 * s, y); ctx.quadraticCurveTo(x, y - 20 * s, x + 60 * s, y - 10 * s); ctx.moveTo(x - 5 * s, y - 6 * s); ctx.quadraticCurveTo(x - 70 * s, y - (80 + f * 70) * s, x - 140 * s, y - (45 + f * 90) * s); ctx.moveTo(x + 5 * s, y - 6 * s); ctx.quadraticCurveTo(x + 70 * s, y - (80 + f * 70) * s, x + 140 * s, y - (45 + f * 90) * s); ctx.moveTo(x - 50 * s, y); ctx.lineTo(x - 85 * s, y + 22 * s); ctx.stroke(); }
    ctx.restore(); }
  // manto rojo de Jesús sobre la túnica (banda del hombro a la cadera)
  function jesus(ctx, o, a = 1) {
    ctx.save(); ctx.globalAlpha = a;
    glow(ctx, o.x, o.y - 330 * o.s, 420 * o.s, '255,236,200', 0.35 * a);
    Ch.person(ctx, { pose: 'stand', eyes: 'normal', mouth: 'smile', brows: 'neutral', style: JESUS, ...o });
    const s = o.s, x = o.x, y = o.y, f = o.facing === -1 ? -1 : 1;
    G.poly(ctx, [[x - 62 * s * f, y - 300 * s], [x - 20 * s * f, y - 312 * s], [x + 58 * s * f, y - 150 * s], [x + 66 * s * f, y - 40 * s], [x + 34 * s * f, y - 30 * s], [x + 20 * s * f, y - 140 * s]], { fill: '#B3262E', seed: 61, lw: 3, step: 14 });
    ctx.restore();
  }

  // ---------- subtítulos: pequeños, centrados; palabras dichas en gris, la actual en blanco ----------
  function captions(ctx, t) {
    const line = S.subtitles.find((l) => t >= l.t - 0.05 && t < l.end);
    if (!line) return;
    const size = 50, y = 640;
    ctx.save(); ctx.font = `700 ${size}px Inter, Arial, sans-serif`; ctx.textBaseline = 'alphabetic';
    const sp = 16, ws = line.words.map((w) => ctx.measureText(w.w).width);
    const total = ws.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
    let x = (W - total) / 2;
    ctx.fillStyle = 'rgba(10,14,22,0.32)'; ctx.beginPath(); ctx.roundRect(x - 26, y - size * 0.98, total + 52, size * 1.42, 22); ctx.fill();
    line.words.forEach((w, i) => {
      if (t >= w.t - 0.03) {
        const cur = t < w.end + 0.05, col = cur || w.key ? '#FFFFFF' : 'rgba(230,234,240,0.62)';
        ctx.shadowColor = 'rgba(0,0,0,0.75)'; ctx.shadowBlur = 14; ctx.fillStyle = col; ctx.fillText(w.w, x, y);
      }
      x += ws[i] + sp;
    });
    ctx.restore();
  }

  // ---------- escenas ----------
  function scene1(ctx, t) { // noche: camina cansado, se detiene y mira al cielo
    const z = lerp(1, 1.06, sm(t, SEG[0][0], SEG[0][1]));
    ctx.save(); ctx.translate(W / 2, GROUND); ctx.scale(z, z); ctx.translate(-W / 2, -GROUND);
    sky(ctx, '#07102A', '#1B2C52', '#26304E'); stars(ctx, t, 1); moon(ctx, 790, 430); clouds(ctx, t, 'rgba(120,140,175,0.55)', 4, 300, 820, 10, 5);
    hills(ctx, '#1B2C3A', '#22364A');
    const stopT = 3.4, wx = Math.min(t, stopT);
    const p = t < stopT ? { ...Ch.walk(t, { x0: 60, speed: 95, t0: 0, s: 1.45 }) } : { x: 60 + 95 * stopT, pose: 'stand' };
    const look = sm(t, 3.8, 4.8);
    Ch.person(ctx, { ...p, y: GROUND, s: 1.45, style: MAN, eyes: 'normal', brows: 'worried', mouth: 'flat', headRot: -0.18 * look, lookY: -look, look: 0.2 });
    ctx.restore();
  }
  function rainNight(ctx, t, light) {
    sky(ctx, '#0A0F1C', '#202A3C', '#1A2230'); clouds(ctx, t, 'rgba(70,80,95,0.95)', 7, 80, 760, 22, 9);
    if (light > 0) { glow(ctx, 520, 160, 520, '255,214,150', 0.35 * light); beam(ctx, 560, 520, 0.22 * light); }
    hills(ctx, '#18222C', '#1D2830');
  }
  function scene2(ctx, t) { // de rodillas bajo la lluvia, ora con las manos alzadas
    const lt = t - SEG[1][0], z = lerp(1.08, 1.0, sm(lt, 0, 4.5));
    ctx.save(); ctx.translate(W / 2, GROUND); ctx.scale(z, z); ctx.translate(-W / 2, -GROUND);
    rainNight(ctx, t, 0);
    Ch.person(ctx, { x: 540, y: GROUND - 10, s: 1.5, pose: 'floor', gesture: 'dua', style: MAN, eyes: 'closed', brows: 'worried', mouth: 'flat', headRot: 0.12, sweat: 0 });
    rain(ctx, t, 0.5);
    if (Math.abs(lt - 2.2) < 0.06) { ctx.fillStyle = 'rgba(210,220,255,0.3)'; ctx.fillRect(0, 0, W, H); }
    ctx.restore();
  }
  function scene3(ctx, t) { // la lluvia se calma y una luz cálida empieza a abrirse sobre él
    const lt = t - SEG[2][0], light = sm(lt, 0.6, 3.8), z = lerp(1.0, 1.12, sm(lt, 0, 4.2));
    ctx.save(); ctx.translate(540, GROUND - 300); ctx.scale(z, z); ctx.translate(-540, -(GROUND - 300));
    rainNight(ctx, t, light);
    Ch.person(ctx, { x: 540, y: GROUND - 10, s: 1.5, pose: 'floor', gesture: 'dua', style: MAN, eyes: 'closed', brows: lerp(0, 1, light) > 0.6 ? 'neutral' : 'worried', mouth: 'flat', headRot: lerp(0.12, -0.05, light) });
    rain(ctx, t, 0.5 * (1 - light * 0.8)); sparkles(ctx, t, 18, 200, 1300, light, 31);
    ctx.restore();
  }
  function scene4(ctx, t) { // amanece: Jesús aparece, camina hacia él y pone la mano en su hombro
    const lt = t - SEG[3][0];
    sky(ctx, '#2A3B66', '#C98A7A', '#F2C08A'); glow(ctx, W / 2, GROUND - 420, 700, '255,190,130', 0.45);
    clouds(ctx, t, 'rgba(250,215,190,0.85)', 5, 160, 780, 12, 13); sparkles(ctx, t, 26, 150, 1400, 0.8, 37);
    hills(ctx, '#3D4C58', '#4B5C52');
    const app = sm(lt, 0, 1.0), jx = lerp(1020, 741, sm(lt, 0.4, 2.4)), walking = lt > 0.4 && lt < 2.4;
    const man = { x: 400, y: GROUND - 10, s: 1.45, pose: 'floor', style: MAN };
    const looks = sm(lt, 2.4, 3.4);
    Ch.person(ctx, { ...man, gesture: looks < 0.5 ? 'dua' : undefined, eyes: looks > 0.3 ? 'normal' : 'closed', brows: 'up', mouth: looks > 0.6 ? 'smile' : 'flat', look: 0.8 * looks, lookY: -looks, headRot: -0.15 * looks });
    const reach = sm(lt, 2.2, 2.9);
    jesus(ctx, { x: jx, y: GROUND, s: 1.5, ...(walking ? { pose: 'walk', walk: lt * 1.6 } : {}), facing: -1, look: -1, handL: reach > 0 ? [lerp(-92, -160, reach), lerp(-90, -158, reach)] : undefined }, app);
  }
  function scene5(ctx, t) { // versículo: el sol sale, las águilas vuelan, se pone de pie junto a Jesús
    const lt = t - SEG[4][0], z = lerp(1.06, 1.0, sm(lt, 0, 9));
    ctx.save(); ctx.translate(W / 2, GROUND); ctx.scale(z, z); ctx.translate(-W / 2, -GROUND);
    sky(ctx, '#3D6AA0', '#F2C79A', '#FFE2B8'); sun(ctx, W / 2, GROUND - 520, 70, t, 1);
    clouds(ctx, t, 'rgba(255,236,214,0.9)', 5, 200, 820, 10, 17); birdsFly(ctx, t, SEG[4][0] + 1.2, 1);
    hills(ctx, '#5E7258', '#6F8458'); sparkles(ctx, t, 30, 150, 1400, 0.9, 41);
    const up = sm(lt, 0.4, 1.8);
    if (up < 1) Ch.person(ctx, { x: 380, y: GROUND - 10, s: 1.45, pose: 'floor', style: MAN, eyes: 'normal', brows: 'up', mouth: 'smile', lookY: -1 });
    else Ch.person(ctx, { x: 380, y: GROUND, s: 1.45, pose: 'stand', style: MAN, eyes: 'normal', brows: 'up', mouth: 'smile', lookY: -1, look: 0.3, gesture: lt > 5 ? 'pointUp' : undefined });
    jesus(ctx, { x: 730, y: GROUND, s: 1.5, facing: -1, look: -0.6, lookY: -0.5 });
    ctx.restore();
  }
  function scene6(ctx, t) { // caminan juntos hacia el amanecer; él alza los brazos; baja la paloma de luz
    const lt = t - SEG[5][0];
    sky(ctx, '#4A79B0', '#F6CB98', '#FFE7C2'); sun(ctx, W / 2, GROUND - 480, 80, t, 1);
    clouds(ctx, t, 'rgba(255,240,222,0.9)', 5, 200, 800, 10, 19); hills(ctx, '#6A7E5C', '#7A8E5E'); sparkles(ctx, t, 34, 120, 1400, 1, 43);
    const walkEnd = 3.4, wk = lt < walkEnd;
    const mx = 230 + Math.min(lt, walkEnd) * 60, jx = mx + 330;
    if (wk) {
      Ch.person(ctx, { x: mx, y: GROUND, s: 1.45, pose: 'walk', walk: lt * 1.7, style: MAN, eyes: 'normal', mouth: 'smile', brows: 'neutral' });
      jesus(ctx, { x: jx, y: GROUND, s: 1.5, pose: 'walk', walk: lt * 1.7 + 0.5, facing: 1, look: -0.4 });
    } else {
      Ch.person(ctx, { x: mx, y: GROUND, s: 1.45, pose: 'stand', style: MAN, eyes: 'happy', mouth: 'grin', brows: 'up', gesture: 'cheer', lookY: -0.8 });
      jesus(ctx, { x: jx, y: GROUND, s: 1.5, facing: -1, look: -0.8, mouth: 'smile' });
    }
    const dk = sm(t, ev.dove, ev.dove + 2.6);
    dove(ctx, lerp(W + 120, 600, dk), lerp(380, 980, dk), 0.9, sm(t, ev.dove - 0.3, ev.dove + 0.8), t);
  }

  Studio.film({
    draw(ctx, t) {
      const i = SEG.findIndex((s, k) => t < s[1] || k === SEG.length - 1);
      [scene1, scene2, scene3, scene4, scene5, scene6][i](ctx, t);
      // fundido suave entre escenas
      const into = t - SEG[i][0], out = SEG[i][1] - t;
      const f = Math.max(i > 0 ? 1 - clamp(into / 0.35) : 0, i < SEG.length - 1 ? 1 - clamp(out / 0.35) : 0);
      if (f > 0) { ctx.fillStyle = `rgba(6,8,14,${f * 0.85})`; ctx.fillRect(0, 0, W, H); }
      captions(ctx, t);
      if (t < 0.4) { ctx.fillStyle = `rgba(0,0,0,${1 - t / 0.4})`; ctx.fillRect(0, 0, W, H); }
    },
    post: { paper: 0.35, vignette: 0.4, grain: 0.05 },
  });
})();
