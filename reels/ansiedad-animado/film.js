// "Cuando la ansiedad no te deja dormir" — cuento animado. Cada cuadro es función pura de t.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { SEG } = S;
  const { clamp, lerp, ease } = U;
  const W = G.W, H = G.H;
  const FLOOR = 1600, MAT = 1330; // piso y parte de arriba del colchón
  const sm = (t, a, b) => ease.inOutQuad(clamp((t - a) / (b - a)));

  const MAN = { skin: '#D9A47A', hair: '#2B1D14', hairStyle: 'short', facialHair: 'stubble', outfit: 'tee', shirt: '#5B6E82', bottoms: 'pants', shorts: '#3A4150', build: 'regular' };
  const JESUS = { skin: '#E0B089', hair: '#5A3A22', hairStyle: 'long', facialHair: 'beard', outfit: 'thobe', robe: '#F3EEE4', sleeves: 'long', build: 'regular' };
  globalThis.CAST = { hombre: MAN, jesus: JESUS };

  function glow(ctx, x, y, r, col, a) { if (a <= 0) return; const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${col},${a})`); g.addColorStop(0.3, `rgba(${col},${a * 0.4})`); g.addColorStop(1, `rgba(${col},0)`); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.restore(); }
  function spark(ctx, x, y, s, a) { if (a < 0.03) return; glow(ctx, x, y, s * 6, '255,232,180', a * 0.6); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(255,250,236,${a})`; ctx.beginPath(); ctx.moveTo(x, y - s * 2.4); ctx.quadraticCurveTo(x, y, x + s * 2.4, y); ctx.quadraticCurveTo(x, y, x, y + s * 2.4); ctx.quadraticCurveTo(x, y, x - s * 2.4, y); ctx.quadraticCurveTo(x, y, x, y - s * 2.4); ctx.fill(); ctx.restore(); }

  // ---------- la recámara ----------
  function room(ctx, t, warm) {
    // pared y piso
    const wall = ctx.createLinearGradient(0, 0, 0, FLOOR); wall.addColorStop(0, lerpCol('#0E1630', '#3A3550', warm)); wall.addColorStop(1, lerpCol('#18223E', '#5A4A5A', warm));
    ctx.fillStyle = wall; ctx.fillRect(0, 0, W, FLOOR);
    G.poly(ctx, [[-20, FLOOR], [W + 20, FLOOR], [W + 20, H + 20], [-20, H + 20]], { fill: lerpCol('#1E1A24', '#4A3A34', warm), seed: 5, hatch: { color: 'rgba(0,0,0,0.18)', gap: 12 } });
    // ventana con luna y estrellas
    const wx = 600, wy = 260, ww = 380, wh = 520;
    ctx.save(); ctx.beginPath(); ctx.rect(wx, wy, ww, wh); ctx.clip();
    const sk = ctx.createLinearGradient(0, wy, 0, wy + wh); sk.addColorStop(0, lerpCol('#071029', '#3A4C7A', warm)); sk.addColorStop(1, lerpCol('#1A2A50', '#E8B48A', warm)); ctx.fillStyle = sk; ctx.fillRect(wx, wy, ww, wh);
    for (let i = 0; i < 40; i++) { const x = wx + U.hash(i, 5) * ww, y = wy + U.hash(i, 6) * wh * 0.7; ctx.fillStyle = `rgba(235,240,255,${0.3 + 0.7 * Math.abs(Math.sin(t * 1.3 + i))})`; ctx.beginPath(); ctx.arc(x, y, 1.2 + U.hash(i, 7) * 1.6, 0, 7); ctx.fill(); }
    glow(ctx, wx + 270, wy + 140, 200, '200,215,255', 0.45); ctx.fillStyle = '#F1F4FF'; ctx.beginPath(); ctx.arc(wx + 270, wy + 140, 46, 0, 7); ctx.fill();
    ctx.restore();
    G.rrect(ctx, wx - 18, wy - 18, ww + 36, wh + 36, 8, { fill: null, lw: 10, seed: 8 }); G.line(ctx, [[wx + ww / 2, wy], [wx + ww / 2, wy + wh]], { lw: 8, seed: 9 }); G.line(ctx, [[wx, wy + wh / 2], [wx + ww, wy + wh / 2]], { lw: 8, seed: 10 });
    // luz de luna en la pared
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(150,170,230,${0.07})`; ctx.beginPath(); ctx.moveTo(wx, wy + wh); ctx.lineTo(wx + ww, wy + wh); ctx.lineTo(wx + ww - 120, FLOOR + 200); ctx.lineTo(wx - 420, FLOOR + 200); ctx.fill(); ctx.restore();
    // cuadro en la pared y buró con reloj
    G.rrect(ctx, 150, 360, 210, 160, 6, { fill: '#2A3150', lw: 6, seed: 12 }); G.poly(ctx, [[175, 495], [240, 420], [290, 470], [330, 430], [335, 495]], { fill: '#3E4870', lw: 3, seed: 13 });
    G.rrect(ctx, 900, 1250, 150, 350, 10, { fill: '#3A2C26', lw: 5, seed: 14, hatch: { color: 'rgba(0,0,0,0.2)', gap: 9 } });
    G.rrect(ctx, 915, 1170, 120, 76, 10, { fill: '#111418', lw: 4, seed: 15 });
    const blink = Math.floor(t * 2) % 2 === 0;
    ctx.save(); ctx.shadowColor = 'rgba(255,90,70,0.9)'; ctx.shadowBlur = 18; ctx.fillStyle = '#FF6A5A'; ctx.font = '700 46px Inter, Arial'; ctx.textAlign = 'center'; ctx.fillText(blink ? '3:00' : '3 00', 975, 1226); ctx.restore();
  }
  function lerpCol(a, b, k) { const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)); const A = p(a), B = p(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(',')})`; }
  function bedBack(ctx) { // cabecera, colchón, almohada
    G.rrect(ctx, 60, 1030, 70, 570, 14, { fill: '#4A3426', lw: 5, seed: 20, hatch: { color: 'rgba(0,0,0,0.2)', gap: 9 } });
    G.rrect(ctx, 80, MAT, 800, 150, 24, { fill: '#D9D4CC', lw: 5, seed: 21 });
    G.rrect(ctx, 80, MAT + 120, 800, 150, 10, { fill: '#5A4030', lw: 5, seed: 22, hatch: { color: 'rgba(0,0,0,0.2)', gap: 9 } });
    G.rrect(ctx, 120, MAT - 70, 230, 95, 44, { fill: '#EEEAE2', lw: 4, seed: 23 });
  }
  function blanket(ctx, x0) { G.poly(ctx, [[x0, MAT - 70], [880, MAT - 60], [890, MAT + 120], [x0 - 20, MAT + 125]], { fill: '#3C5A86', lw: 5, seed: 24, hatch: { color: 'rgba(255,255,255,0.08)', gap: 10 } }); }
  function lyingMan(ctx, o) { Ch.person(ctx, { x: 830, y: MAT - 38, s: 1.25, rot: -Math.PI / 2, pose: 'stand', style: MAN, handL: [-28, -205], handR: [30, -215], ...o }); }
  function darkCloud(ctx, x, y, a, t) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; for (let k = 0; k < 7; k++) { const ox = (k - 3) * 55 + Math.sin(t * 1.5 + k) * 8, oy = -Math.sin((k / 6) * Math.PI) * 50 + Math.cos(t * 1.2 + k) * 6; G.ellipse(ctx, x + ox, y + oy, 75, 50, { fill: '#2A2A34', seed: 70 + k, lw: 3 }); } ctx.restore(); }
  function jesus(ctx, o, a = 1) {
    ctx.save(); ctx.globalAlpha = a;
    glow(ctx, o.x, o.y - (o.pose === 'sit' ? 180 : 330) * o.s, 420 * o.s, '255,236,200', 0.35 * a);
    Ch.person(ctx, { pose: 'stand', eyes: 'normal', mouth: 'smile', brows: 'neutral', style: JESUS, ...o });
    const s = o.s, x = o.x, y = o.y + (o.pose === 'sit' ? 150 * s : 0), f = o.facing === -1 ? -1 : 1;
    G.poly(ctx, [[x - 62 * s * f, y - 300 * s], [x - 20 * s * f, y - 312 * s], [x + 58 * s * f, y - 150 * s], [x + 66 * s * f, y - (o.pose === 'sit' ? 150 : 40) * s], [x + 34 * s * f, y - (o.pose === 'sit' ? 150 : 30) * s], [x + 20 * s * f, y - 140 * s]], { fill: '#B3262E', seed: 61, lw: 3, step: 14 });
    ctx.restore();
  }
  const WORRIES = [{ text: 'deudas', x: 250, y: 840 }, { text: 'mi familia', x: 540, y: 740 }, { text: '¿y mañana?', x: 820, y: 880 }];
  function worryBubble(ctx, w, x, y, a, sc = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(sc, sc);
    for (let k = 0; k < 5; k++) G.ellipse(ctx, (k - 2) * 46, -Math.sin((k / 4) * Math.PI) * 26, 62, 46, { fill: '#F2EEE6', seed: 90 + k + w.length, lw: 3 });
    ctx.fillStyle = '#2A2A30'; ctx.font = '700 40px Inter, Arial'; ctx.textAlign = 'center'; ctx.fillText(w, 0, -2); ctx.restore(); }

  // ---------- subtítulos ----------
  function captions(ctx, t) {
    const line = S.subtitles.find((l) => t >= l.t - 0.05 && t < l.end); if (!line) return;
    const size = 50, y = 600;
    ctx.save(); ctx.font = `700 ${size}px Inter, Arial, sans-serif`;
    const sp = 16, ws = line.words.map((w) => ctx.measureText(w.w).width), total = ws.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
    let x = (W - total) / 2;
    ctx.fillStyle = 'rgba(10,14,22,0.35)'; ctx.beginPath(); ctx.roundRect(x - 26, y - size * 0.98, total + 52, size * 1.42, 22); ctx.fill();
    line.words.forEach((w, i) => { if (t >= w.t - 0.03) { const cur = t < w.end + 0.05; ctx.shadowColor = 'rgba(0,0,0,0.75)'; ctx.shadowBlur = 14; ctx.fillStyle = cur || w.key ? '#FFFFFF' : 'rgba(230,234,240,0.62)'; ctx.fillText(w.w, x, y); } x += ws[i] + sp; });
    ctx.restore();
  }

  // ---------- escenas ----------
  const zoomAt = (ctx, cx, cy, z, fn) => { ctx.save(); ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-cx, -cy); fn(); ctx.restore(); };
  function scene1(ctx, t) { // acostado, despierto a las 3:00
    zoomAt(ctx, 600, 1250, lerp(1.0, 1.12, sm(t, 0, SEG[0][1])), () => {
      room(ctx, t, 0); bedBack(ctx); lyingMan(ctx, { eyes: 'wide', brows: 'worried', mouth: 'flat', look: Math.sin(t * 0.8) * 0.5, blink: (t % 3.2) < 0.12 ? 1 : 0 }); blanket(ctx, 400);
    });
  }
  function sitMan(o) { return { x: 470, y: MAT + 10, s: 1.35, pose: 'sit', style: MAN, ...o }; }
  function scene2(ctx, t) { // sentado en la orilla de la cama, aparecen las preocupaciones
    const lt = t - SEG[1][0];
    room(ctx, t, 0); bedBack(ctx);
    Ch.person(ctx, sitMan({ gesture: lt > 1 ? 'facepalm' : undefined, eyes: lt > 1 ? 'closed' : 'normal', brows: 'worried', mouth: 'wavy' }));
    WORRIES.forEach((w, i) => { const a = sm(lt, 0.4 + i * 1.0, 0.9 + i * 1.0); worryBubble(ctx, w.text, w.x, w.y + Math.sin(t * 1.6 + i) * 10, a, 0.8 + 0.5 * ease.outBack(a)); });
  }
  function scene3(ctx, t) { // le pesa todo: nube oscura encima, el pecho apretado
    const lt = t - SEG[2][0], k = sm(lt, 0, 1.5);
    zoomAt(ctx, 470, 1100, lerp(1.0, 1.15, sm(lt, 0, 4)), () => {
      room(ctx, t, 0); bedBack(ctx);
      Ch.person(ctx, sitMan({ gesture: 'facepalm', eyes: 'closed', brows: 'worried', mouth: 'wavy', sy: 1 - 0.04 * k, headRot: 0.15 * k }));
      WORRIES.forEach((w, i) => worryBubble(ctx, w.text, lerp(w.x, 470 + (i - 1) * 230, k), lerp(w.y, 860 + (i % 2) * 70, k) + Math.sin(t * 2 + i) * 8, 1 - 0.2 * k, 1.25));
      darkCloud(ctx, 470, 760, k * 0.9, t);
    });
    const pulse = 0.18 * k * Math.max(0, Math.sin(t * 7)); ctx.fillStyle = `rgba(40,0,10,${pulse})`; ctx.fillRect(0, 0, W, H); // latido
  }
  function scene4(ctx, t) { // entra la luz; Jesús se sienta a su lado y le pone la mano en el hombro
    const lt = t - SEG[3][0], light = sm(lt, 0, 1.6), sit = sm(lt, 1.2, 2.2), reach = sm(lt, 2.2, 2.9);
    room(ctx, t, light * 0.55); glow(ctx, 790, 520, 700, '255,214,160', 0.5 * light); bedBack(ctx);
    for (let i = 0; i < 16; i++) spark(ctx, 600 + U.hash(i, 3) * 380, 300 + U.hash(i, 4) * 900 - (t * 20 % 200), 2 + U.hash(i, 5) * 2, light * Math.max(0, Math.sin(t * 1.7 + i)));
    const looks = sm(lt, 2.6, 3.4);
    Ch.person(ctx, sitMan({ gesture: looks < 0.4 ? 'facepalm' : undefined, eyes: looks > 0.3 ? 'normal' : 'closed', brows: looks > 0.5 ? 'up' : 'worried', mouth: looks > 0.7 ? 'smile' : 'flat', look: looks, headRot: -0.1 * looks }));
    const jx = 740, jo = sit < 1 ? { x: lerp(860, jx, sit), y: sit < 0.6 ? FLOOR : MAT + 10, pose: sit < 0.6 ? 'stand' : 'sit' } : { x: jx, y: MAT + 10, pose: 'sit' };
    jesus(ctx, { ...jo, s: 1.4, facing: -1, look: -1, handL: reach > 0 ? [lerp(-62, -135, reach), lerp(-6, -150, reach)] : undefined }, sm(lt, 0, 1.0));
  }
  function scene5(ctx, t) { // versículo: las preocupaciones van a las manos de Jesús y se vuelven estrellas
    const lt = t - SEG[4][0];
    room(ctx, t, 0.55); glow(ctx, 790, 520, 700, '255,214,160', 0.5); bedBack(ctx);
    Ch.person(ctx, sitMan({ eyes: 'normal', brows: 'up', mouth: 'smile', look: 0.8, handR: lt > 0.6 ? [110, -120] : undefined }));
    jesus(ctx, { x: 740, y: MAT + 10, pose: 'sit', s: 1.4, facing: -1, look: -0.8, handL: [-110, -110], handR: [-60, -120] });
    const hx = 600, hy = MAT - 150;
    WORRIES.forEach((w, i) => {
      const st = 0.8 + i * 1.6, k = sm(lt, st, st + 1.4), gone = sm(lt, st + 1.4, st + 2.2);
      if (gone < 1) worryBubble(ctx, w.text, lerp(470 + (i - 1) * 230, hx, k), lerp(860 + (i % 2) * 70, hy, k), 1 - gone, lerp(1.25, 0.4, k));
      for (let j = 0; j < 8; j++) { const u = lt - (st + 1.6) - j * 0.12; if (u > 0 && u < 3.5) spark(ctx, hx + Math.sin(j * 2.3 + i) * 40 + u * 30, hy - u * 260, 3, Math.max(0, 1 - u / 3.5)); }
    });
  }
  function scene6(ctx, t) { // duerme en paz; Jesús lo cuida junto a la ventana
    const lt = t - SEG[5][0];
    zoomAt(ctx, 600, 1200, lerp(1.08, 1.0, sm(lt, 0, 6)), () => {
      room(ctx, t, 0.25); glow(ctx, 790, 520, 600, '255,214,160', 0.3); bedBack(ctx);
      lyingMan(ctx, { eyes: 'sleep', brows: 'neutral', mouth: 'smile', sy: 1 + Math.sin(t * 1.4) * 0.012 }); blanket(ctx, 400);
      jesus(ctx, { x: 905, y: FLOOR, s: 1.25, facing: -1, look: -1, lookY: 0.4 });
      for (let i = 0; i < 14; i++) spark(ctx, 620 + U.hash(i, 8) * 360, 280 + U.hash(i, 9) * 500, 2 + U.hash(i, 10) * 2, 0.7 * Math.max(0, Math.sin(t * 1.5 + i)));
    });
  }

  Studio.film({
    draw(ctx, t) {
      const i = SEG.findIndex((s, k) => t < s[1] || k === SEG.length - 1);
      [scene1, scene2, scene3, scene4, scene5, scene6][i](ctx, t);
      const into = t - SEG[i][0], out = SEG[i][1] - t;
      const f = Math.max(i > 0 ? 1 - clamp(into / 0.35) : 0, i < SEG.length - 1 ? 1 - clamp(out / 0.35) : 0);
      if (f > 0) { ctx.fillStyle = `rgba(6,8,14,${f * 0.85})`; ctx.fillRect(0, 0, W, H); }
      captions(ctx, t);
      if (t < 0.4) { ctx.fillStyle = `rgba(0,0,0,${1 - t / 0.4})`; ctx.fillRect(0, 0, W, H); }
    },
    post: { paper: 0.35, vignette: 0.45, grain: 0.05 },
  });
})();
