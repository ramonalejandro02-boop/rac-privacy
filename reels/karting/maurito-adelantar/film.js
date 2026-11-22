// THE FILM: Maurito teaches how to overtake. Every frame is a pure function of t; every hit is in score.js.
// Maurito himself is the user's own artwork (assets/maurito.png), cut out as a die-cut sticker so the
// hand-drawn world and the character read as one style.
(function () {
  const U = globalThis.U, G = globalThis.G, Subs = globalThis.Subs, Shots = globalThis.Shots, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { clamp, lerp, ease } = U;
  const { ev } = S;
  const W = G.W, H = G.H, SAFE = G.SAFE;
  let VO = null, SUBS = [], MAU = null, HEAD = null;
  const RED = '#E4312B', BLUE = '#2347C6', YEL = '#FFC934', GRN = '#29B35A', ORG = '#FF8A2A', INK = '#1F1A24', CREAM = '#FFF6E6';
  const pop = (t, t0, d = 0.22, k = 2.2) => (t < t0 ? 0 : ease.outBack(clamp((t - t0) / d), k));
  const talk = (t) => { const mm = Subs.mouth(VO, t, 'maurito'); return mm.talking ? mm.open : 0; };

  // ---------- Maurito as a die-cut sticker ----------
  function makeSticker(img, border) {
    const c = document.createElement('canvas'); c.width = img.width + border * 2; c.height = img.height + border * 2;
    const x = c.getContext('2d');
    for (let a = 0; a < 32; a++) x.drawImage(img, border + Math.cos(a / 32 * Math.PI * 2) * border, border + Math.sin(a / 32 * Math.PI * 2) * border);
    x.globalCompositeOperation = 'source-in'; x.fillStyle = '#FFFFFF'; x.fillRect(0, 0, c.width, c.height);
    x.globalCompositeOperation = 'source-over'; x.drawImage(img, border, border);
    return c;
  }
  // origin at the feet; h = height on screen; sq = squash (1 = none)
  function maurito(ctx, x, y, h, t, { rot = 0, sq = 1, flip = 1, shadow = true } = {}) {
    const k = h / MAU.height, tk = talk(t);
    const bob = 1 + 0.03 * tk * Math.sin(t * 28);
    if (shadow) { ctx.save(); ctx.globalAlpha = 0.25; G.ellipse(ctx, x, y + 4, h * 0.26, h * 0.035, { fill: '#000', lw: 0, seed: 3 }); ctx.restore(); }
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot + Math.sin(t * 2.4) * 0.012); ctx.scale(flip * k / (sq * bob), k * sq * bob);
    ctx.shadowColor = 'rgba(0,0,0,0.25)'; ctx.shadowBlur = 30; ctx.shadowOffsetY = 18;
    ctx.drawImage(MAU, -MAU.width / 2, -MAU.height);
    ctx.restore();
  }
  function avatar(ctx, t, x = 140, y = 700, r = 92) {
    ctx.save(); ctx.translate(x, y + Math.sin(t * 3) * 5);
    G.ellipse(ctx, 6, 10, r, r, { fill: 'rgba(0,0,0,0.25)', lw: 0, seed: 7 });
    G.ellipse(ctx, 0, 0, r, r, { fill: '#FFFFFF', lw: 7, seed: 8 });
    ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r - 10, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = BLUE; ctx.fillRect(-r, -r, 2 * r, 2 * r);
    const tk = talk(t), s = (2 * r) / 250 * (1 + 0.04 * tk * Math.sin(t * 28));
    ctx.drawImage(MAU, 150, 0, 260, 250, -130 * s, -112 * s, 260 * s, 250 * s);
    ctx.restore();
    G.ellipse(ctx, 0, 0, r - 4, r - 4, { fill: null, stroke: RED, lw: 9, seed: 9 });
    ctx.restore();
  }

  // ---------- UI pieces ----------
  function badge(ctx, text, x, y, t, t0, { bg = RED, fg = '#FFFFFF', size = 64, rot = -0.04, icon = null } = {}) {
    const p = pop(t, t0); if (p <= 0) return;
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(p, p);
    const tw = G.measure(ctx, text, size, 'Bungee', 400); const iw = icon ? size * 1.1 : 0;
    const w = tw + size * 1.2 + iw, h = size * 1.7;
    G.rrect(ctx, -w / 2 + 8, -h / 2 + 12, w, h, h * 0.3, { fill: 'rgba(0,0,0,0.3)', lw: 0, seed: 11 });
    G.rrect(ctx, -w / 2, -h / 2, w, h, h * 0.3, { fill: bg, lw: 6, seed: 12 });
    if (icon) icon(ctx, -w / 2 + size * 0.6 + iw / 2 - size * 0.15, 0, size * 0.42, fg);
    G.text(ctx, text, -w / 2 + size * 0.6 + iw + tw / 2, size * 0.36, { size, align: 'center', fam: 'Bungee', weight: 400, color: fg, stroke: INK, strokeW: fg === '#FFFFFF' ? 6 : 0 });
    ctx.restore();
  }
  const IC = {
    check: (ctx, x, y, r, c) => G.line(ctx, [[x - r * 0.8, y], [x - r * 0.2, y + r * 0.6], [x + r * 0.9, y - r * 0.7]], { color: c, lw: r * 0.38, seed: 21 }),
    wind: (ctx, x, y, r, c) => { for (let i = -1; i <= 1; i++) G.line(ctx, [[x - r, y + i * r * 0.55], [x + r * 0.6, y + i * r * 0.55], [x + r, y + i * r * 0.55 - r * 0.3]], { color: c, lw: r * 0.24, seed: 22 + i }); },
    arrow: (ctx, x, y, r, c) => G.poly(ctx, [[x - r, y - r * 0.3], [x + r * 0.1, y - r * 0.3], [x + r * 0.1, y - r * 0.8], [x + r, y], [x + r * 0.1, y + r * 0.8], [x + r * 0.1, y + r * 0.3], [x - r, y + r * 0.3]], { fill: c, lw: 0, seed: 25, step: 30 }),
    brake: (ctx, x, y, r, c) => { G.ellipse(ctx, x, y, r * 0.85, r * 0.85, { fill: null, stroke: c, lw: r * 0.25, seed: 26 }); G.ellipse(ctx, x, y, r * 0.35, r * 0.35, { fill: c, lw: 0, seed: 27 }); },
    x: (ctx, x, y, r, c) => { G.line(ctx, [[x - r * 0.7, y - r * 0.7], [x + r * 0.7, y + r * 0.7]], { color: c, lw: r * 0.36, seed: 28 }); G.line(ctx, [[x + r * 0.7, y - r * 0.7], [x - r * 0.7, y + r * 0.7]], { color: c, lw: r * 0.36, seed: 29 }); },
  };
  function stepCard(ctx, n, title, t, t0) {
    const p = pop(t, t0, 0.25, 2.5); if (p <= 0) return;
    ctx.save(); ctx.translate(W / 2, 330); ctx.rotate(-0.03); ctx.scale(p, p);
    const tw = G.measure(ctx, title, 66, 'Bungee', 400), w = tw + 190;
    G.rrect(ctx, -w / 2, -70, w, 140, 30, { fill: INK, lw: 6, seed: 31 });
    G.ellipse(ctx, -w / 2 + 75, 0, 50, 50, { fill: YEL, lw: 6, seed: 32 });
    G.text(ctx, String(n), -w / 2 + 75, 22, { size: 62, align: 'center', fam: 'Bungee', weight: 400, color: INK });
    G.text(ctx, title, -w / 2 + 150 + tw / 2, 24, { size: 66, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF' });
    ctx.restore();
  }
  function burst(ctx, x, y, r, col, text, size, t, t0) {
    const p = pop(t, t0, 0.2, 2.8); if (p <= 0) return;
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.08 + Math.sin((t - t0) * 6) * 0.02); ctx.scale(p, p);
    const pts = []; for (let i = 0; i < 24; i++) { const rr = i % 2 ? r * 0.72 : r, a = (i / 24) * Math.PI * 2; pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
    G.poly(ctx, pts, { fill: col, lw: 7, seed: 41, step: 200 });
    G.text(ctx, text, 0, size * 0.35, { size, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF', stroke: INK, strokeW: 10 });
    ctx.restore();
  }

  // ---------- karts (top view) ----------
  function kart(ctx, x, y, ang, s, body, helmet, num, seed) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang + Math.PI / 2); ctx.scale(s, s);
    G.rrect(ctx, -36, -54, 80, 124, 24, { fill: 'rgba(0,0,0,0.25)', lw: 0, seed: seed + 1 });
    for (const [wx, wy, w] of [[-36, -38, 22], [36, -38, 22], [-40, 34, 26], [40, 34, 26]]) G.rrect(ctx, wx - w / 2, wy - 16, w, 32, 7, { fill: '#26262B', lw: 4, seed: seed + wx + wy });
    G.rrect(ctx, -24, -58, 48, 118, 16, { fill: body, lw: 5, seed: seed + 5 });
    G.rrect(ctx, -28, -66, 56, 16, 7, { fill: INK, lw: 4, seed: seed + 6 });
    G.ellipse(ctx, 0, 10, 18, 18, { fill: helmet, lw: 4, seed: seed + 7 });
    if (helmet === '#FFFFFF') { ctx.fillStyle = BLUE; ctx.fillRect(-17, 3, 34, 7); }
    if (num) G.text(ctx, num, 0, -22, { size: 26, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF' });
    G.rrect(ctx, -32, 54, 64, 13, 6, { fill: INK, lw: 4, seed: seed + 8 });
    ctx.restore();
  }
  const mauKart = (ctx, x, y, a, s) => kart(ctx, x, y, a, s, RED, '#FFFFFF', '2', 300);
  const rivKart = (ctx, x, y, a, s) => kart(ctx, x, y, a, s, ORG, '#33333B', null, 400);

  // ---------- scenery ----------
  function grass(ctx, seed) {
    ctx.fillStyle = '#5DB052'; ctx.fillRect(-300, -300, W + 600, H + 600);
    ctx.save(); ctx.globalAlpha = 0.12; ctx.fillStyle = '#1E5E25';
    for (let i = -8; i < 14; i++) { ctx.save(); ctx.translate(540, 960); ctx.rotate(-0.5); ctx.fillRect(i * 150 - 1100, -2000, 75, 4000); ctx.restore(); }
    ctx.restore();
    for (let i = 0; i < 40; i++) G.line(ctx, [[G.rnd(i, seed) * W, G.rnd(i, seed + 1) * H], [G.rnd(i, seed) * W + 6, G.rnd(i, seed + 1) * H - 18]], { color: '#3E8A3A', lw: 4, seed: seed + i });
  }
  function kerb(ctx, pts, seed, off = 0) {
    G.line(ctx, pts, { color: '#FFFFFF', lw: 30, seed, amp: 0.3 });
    ctx.save(); ctx.setLineDash([34, 34]); ctx.lineDashOffset = -off; ctx.strokeStyle = RED; ctx.lineWidth = 30; ctx.lineCap = 'butt';
    ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke(); ctx.restore();
  }
  function straight(ctx, t) {
    grass(ctx, 50);
    const L = 230, R = 850, off = t * 1100;
    G.rrect(ctx, L - 10, -40, R - L + 40, H + 80, 0, { fill: 'rgba(0,0,0,0.2)', lw: 0, seed: 51 });
    G.rrect(ctx, L, -40, R - L, H + 80, 0, { fill: '#45474F', lw: 0, seed: 52, hatch: { color: 'rgba(255,255,255,0.04)', gap: 10 } });
    ctx.fillStyle = 'rgba(255,255,255,0.85)'; for (let y = (off % 200) - 200; y < H; y += 200) ctx.fillRect(536, y, 8, 100);
    kerb(ctx, [[L, -60], [L, H + 60]], 53, off); kerb(ctx, [[R, -60], [R, H + 60]], 54, off);
  }
  const C = { x: 850, y: 860 }, RIN = 90, ROUT = 520, XL = C.x - ROUT, XR = C.x - RIN;
  const arc = (r, n = 30) => { const p = []; for (let i = 0; i <= n; i++) { const a = Math.PI + (i / n) * Math.PI / 2; p.push([C.x + r * Math.cos(a), C.y + r * Math.sin(a)]); } return p; };
  const edge = (r) => [[C.x - r, H + 80], [C.x - r, C.y], ...arc(r), [W + 80, C.y - r]];
  function corner(ctx, t) {
    grass(ctx, 60);
    const outer = edge(ROUT), inner = edge(RIN).reverse();
    G.poly(ctx, [...outer, ...inner].map((p) => [p[0] + 12, p[1] + 18]), { fill: 'rgba(0,0,0,0.2)', lw: 0, seed: 61, step: 400 });
    G.poly(ctx, [...outer, ...inner], { fill: '#45474F', lw: 0, seed: 62, step: 400 });
    kerb(ctx, edge(RIN), 63); kerb(ctx, edge(ROUT), 64);
    for (const [y, l] of [[1330, '100'], [1120, '50']]) { G.rrect(ctx, XL - 115, y - 32, 80, 64, 8, { fill: '#FFFFFF', lw: 5, seed: 65 + y }); G.text(ctx, l, XL - 75, y + 12, { size: 32, align: 'center', fam: 'Bungee', weight: 400, color: INK }); }
    G.rrect(ctx, C.x + 70, C.y - 300, 210, 72, 14, { fill: INK, lw: 5, seed: 67 });
    G.text(ctx, 'CURVA 1', C.x + 175, C.y - 250, { size: 36, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF' });
  }
  function curve(pts, n = 24) { // catmull-rom through pts -> sampled with arc length
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) { const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      for (let k = 0; k < n; k++) { const u = k / n, u2 = u * u, u3 = u2 * u; out.push([0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3), 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)]); } }
    out.push(pts[pts.length - 1]); let L = 0; out[0].l = 0; for (let i = 1; i < out.length; i++) { L += Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]); out[i].l = L; } out.L = L; return out;
  }
  function at(P, f) { const l = clamp(f) * P.L; let i = 1; while (i < P.length - 1 && P[i].l < l) i++; const a = P[i - 1], b = P[i], q = (l - a.l) / Math.max(1e-6, b.l - a.l); return { x: lerp(a[0], b[0], q), y: lerp(a[1], b[1], q), ang: Math.atan2(b[1] - a[1], b[0] - a[0]) }; }
  function trail(ctx, P, f, color, lw = 12) { if (f <= 0) return; const e = at(P, f); const pts = P.filter((p) => p.l < f * P.L).map((p) => [p[0], p[1]]); pts.push([e.x, e.y]); ctx.save(); ctx.setLineDash([26, 20]); G.line(ctx, pts, { color, lw, seed: 71, amp: 0 }); ctx.restore(); }
  const LIN = XR - 120, LOUT = XL + 135;
  const P_M = curve([[LIN, 1180], [LIN, 900], [C.x - RIN - 65, C.y - 30], [C.x - 30, C.y - RIN - 75], [1200, C.y - RIN - 85]]);
  const P_R = curve([[LOUT, 1120], [LOUT, 880], [LOUT + 120, 600], [C.x, C.y - ROUT + 135], [1200, C.y - ROUT + 125]]);

  function sky(ctx, top = '#58A8E8', bottom = '#CDEBFF') { const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, top); g.addColorStop(0.55, bottom); g.addColorStop(1, bottom); ctx.fillStyle = g; ctx.fillRect(-300, -300, W + 600, H + 600); }
  function trackside(ctx, t) {
    sky(ctx);
    for (let i = 0; i < 4; i++) G.ellipse(ctx, 140 + i * 300 + Math.sin(t * 0.3 + i) * 20, 380 + (i % 2) * 70, 110, 44, { fill: '#FFFFFF', lw: 0, seed: 80 + i });
    // grandstand with a crowd
    G.rrect(ctx, -20, 840, W + 40, 320, 8, { fill: '#2C3E66', lw: 6, seed: 85 });
    for (let r = 0; r < 4; r++) for (let c = 0; c < 18; c++) { const x = 30 + c * 60 + (r % 2) * 30, y = 880 + r * 66, j = Math.max(0, Math.sin(t * 8 + c + r)) * (t > ev.ask ? 10 : 2);
      G.ellipse(ctx, x, y - j, 20, 20, { fill: ['#F2C28B', '#C98A62', '#8D5A3B'][(c + r) % 3], lw: 3, seed: 900 + r * 20 + c });
      G.rrect(ctx, x - 22, y + 16 - j, 44, 34, 10, { fill: [RED, BLUE, YEL, '#FFFFFF', GRN][(c * 3 + r) % 5], lw: 3, seed: 1000 + r * 20 + c }); }
    // banner + barrier
    G.rrect(ctx, -20, 1150, W + 40, 70, 0, { fill: RED, lw: 5, seed: 86 });
    for (let i = 0; i < 4; i++) G.text(ctx, 'KARTING', 130 + i * 300, 1203, { size: 46, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF' });
    // track
    G.rrect(ctx, -20, 1220, W + 40, 520, 0, { fill: '#45474F', lw: 5, seed: 87 });
    ctx.fillStyle = 'rgba(255,255,255,0.85)'; for (let x = 40; x < W; x += 220) ctx.fillRect(x, 1520, 110, 12);
    kerb(ctx, [[-60, 1740], [W + 60, 1740]], 88);
    G.rrect(ctx, -20, 1756, W + 40, 200, 0, { fill: '#5DB052', lw: 0, seed: 89 });
  }
  function kartSide(ctx, x, y, s, seed) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    G.ellipse(ctx, 0, 12, 300, 22, { fill: 'rgba(0,0,0,0.25)', lw: 0, seed });
    G.poly(ctx, [[-260, -60], [230, -60], [300, -20], [290, 0], [-250, 0]], { fill: '#24242A', lw: 6, seed: seed + 1, step: 60 });
    G.poly(ctx, [[-140, -140], [130, -140], [190, -100], [190, -60], [-170, -60]], { fill: RED, lw: 6, seed: seed + 2, step: 60 });
    G.text(ctx, '2', -10, -78, { size: 74, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF', stroke: INK, strokeW: 8 });
    G.poly(ctx, [[-60, -230], [20, -230], [40, -140], [-80, -140]], { fill: '#2B2B33', lw: 5, seed: seed + 3, step: 40 }); // seat
    for (const [wx, r] of [[-190, 80], [220, 66]]) { G.ellipse(ctx, wx, 0, r, r, { fill: '#1C1C20', lw: 6, seed: seed + wx }); G.ellipse(ctx, wx, 0, r * 0.45, r * 0.45, { fill: '#C9CDD5', lw: 5, seed: seed + wx + 1 }); }
    ctx.restore();
  }
  function alert(ctx, t) {
    ctx.fillStyle = '#FFE36B'; ctx.fillRect(-300, -300, W + 600, H + 600);
    G.rays(ctx, W / 2, 900, { n: 26, r0: 120, r1: 1700, color: '#FFC934', lw: 60, spin: t * 0.25, seed: 91 });
    for (let i = 0; i < 2; i++) { const y = i ? H - 70 : 40; ctx.save(); ctx.beginPath(); ctx.rect(0, y, W, 50); ctx.clip(); for (let x = -100 + ((t * 120) % 100); x < W + 100; x += 100) G.poly(ctx, [[x, y], [x + 50, y], [x + 10, y + 50], [x - 40, y + 50]], { fill: INK, lw: 0, seed: 92 + x, step: 100 }); ctx.restore(); }
  }
  function finish(ctx, t) {
    sky(ctx, '#3D8BE0', '#BFE6FF');
    G.rays(ctx, W / 2, 1000, { n: 22, r0: 150, r1: 1500, color: 'rgba(255,255,255,0.35)', lw: 50, spin: t * 0.2, seed: 95 });
    G.rrect(ctx, 70, 360, 26, 1200, 6, { fill: '#8A8F99', lw: 5, seed: 96 }); G.rrect(ctx, 984, 360, 26, 1200, 6, { fill: '#8A8F99', lw: 5, seed: 97 });
    G.rrect(ctx, 50, 300, 980, 150, 16, { fill: INK, lw: 6, seed: 98 });
    G.text(ctx, 'META', W / 2, 410, { size: 120, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF' });
    for (let i = 0; i < 24; i++) for (let j = 0; j < 2; j++) { ctx.fillStyle = (i + j) % 2 ? '#FFFFFF' : INK; ctx.fillRect(60 + i * 40, 450 + j * 32, 40, 32); }
    G.rrect(ctx, -20, 1500, W + 40, 460, 0, { fill: '#45474F', lw: 5, seed: 99 });
    for (let i = 0; i < 28; i++) for (let j = 0; j < 3; j++) { ctx.fillStyle = (i + j) % 2 ? '#FFFFFF' : INK; ctx.fillRect(i * 40, 1500 + j * 40, 40, 40); }
  }

  // ---------- shots ----------
  function intro(ctx, t) {
    trackside(ctx, t);
    const arrive = ease.outCubic(clamp(t / 1.0));
    kartSide(ctx, lerp(1500, 770, arrive), 1640, 0.95, 120);
    if (arrive < 1) for (let i = 0; i < 5; i++) G.line(ctx, [[lerp(1500, 770, arrive) + 320 + i * 50, 1520 + i * 28], [lerp(1500, 770, arrive) + 520 + i * 50, 1520 + i * 28]], { color: '#FFFFFF', lw: 6, seed: 130 + i });
    // Maurito jumps in and lands on the beat (ev.land)
    const j = clamp((t - 0.35) / (ev.land - 0.35));
    const x = lerp(-250, 340, ease.outQuad(j)), y = 1700 - Math.sin(Math.PI * j) * 420;
    const land = t >= ev.land ? Math.exp(-(t - ev.land) * 9) * Math.sin((t - ev.land) * 30) : 0;
    if (t > 0.35) maurito(ctx, x, y, 1000, t, { sq: 1 - 0.12 * land, rot: (1 - j) * -0.3 });
    badge(ctx, 'MAURITO #2', 600, 520, t, ev.name, { bg: BLUE, size: 72 });
    badge(ctx, 'PILOTO DE KARTING', 600, 650, t, ev.name + 0.25, { bg: '#FFFFFF', fg: INK, size: 40, rot: 0.02 });
    burst(ctx, 760, 900, 200, YEL, '¿ADELANTAR?', 46, t, ev.ask);
  }
  function paso1(ctx, t) {
    straight(ctx, t);
    const s0 = S.S.paso1[0], ry = 860 + Math.sin(t * 2) * 6, my = lerp(1480, 1120, ease.inOutQuad(clamp((t - s0 - 0.6) / 4)));
    const air = clamp((t - ev.aire) / 0.4);
    if (air > 0) {
      ctx.save(); ctx.globalAlpha = 0.85 * air;
      G.ellipse(ctx, 540, ry + 230, 120, 180, { fill: 'rgba(140,210,255,0.22)', stroke: 'rgba(200,235,255,0.9)', lw: 4, seed: 141 });
      for (let i = 0; i < 6; i++) { const yy = ry + 100 + ((t * 300 + i * 45) % 270); const pts = []; for (let x = -80; x <= 80; x += 10) pts.push([540 + x, yy + Math.sin(x * 0.08 + t * 10 + i) * 10]); G.line(ctx, pts, { color: '#DDF3FF', lw: 6, seed: 150 + i, amp: 0 }); }
      ctx.restore();
    }
    rivKart(ctx, 540, ry, -Math.PI / 2, 1.55); mauKart(ctx, 540, my, -Math.PI / 2, 1.55);
    for (let i = 0; i < 5; i++) G.line(ctx, [[500 + i * 20, my + 110 + G.rnd(i, 3) * 20], [500 + i * 20, my + 170 + G.rnd(i, 4) * 60]], { color: 'rgba(255,255,255,0.7)', lw: 4, seed: 160 + i });
    stepCard(ctx, 1, 'EL REBUFO', t, ev.p1);
    badge(ctx, '+ VELOCIDAD', 330, 1250, t, ev.vel, { bg: GRN, size: 44, rot: -0.06, icon: IC.arrow });
    badge(ctx, 'REBUFO', 790, 1080, t, ev.rebufo, { bg: BLUE, size: 58, rot: 0.05, icon: IC.wind });
    avatar(ctx, t);
  }
  function paso2(ctx, t) {
    corner(ctx, t);
    const s0 = S.S.paso2[0], d = S.S.paso2[1] - s0, f = ease.inOutQuad(clamp((t - s0 - 0.4) / (d - 0.8)));
    const ry = lerp(1520, 1190, clamp((t - s0) / d)), mx = lerp(LOUT + 10, LIN, f), my = lerp(1740, ry + 10, f);
    trail(ctx, curve([[LOUT + 10, 1720], [lerp(LOUT, LIN, 0.6), 1520], [LIN, ry + 60]]), ease.outCubic(clamp((t - s0 - 0.2) / 0.8)), GRN, 14);
    rivKart(ctx, LOUT, ry, -Math.PI / 2, 1.3); mauKart(ctx, mx, my, -Math.PI / 2 + 0.3 * Math.sin(f * Math.PI), 1.3);
    stepCard(ctx, 2, 'POR DENTRO', t, ev.p2);
    badge(ctx, 'POR DENTRO', LIN + 10, ry - 200, t, ev.dentro, { bg: GRN, size: 50, rot: 0.03, icon: IC.arrow });
    avatar(ctx, t);
  }
  function paso3(ctx, t) {
    corner(ctx, t);
    const s0 = S.S.paso3[0], d = S.S.paso3[1] - s0;
    const zone = ease.outCubic(clamp((t - ev.frena) / 0.3));
    if (zone > 0) { ctx.save(); ctx.globalAlpha = 0.5 * zone; G.rrect(ctx, LIN - 95, 960, 190, 210, 12, { fill: RED, lw: 0, seed: 171 }); ctx.restore(); }
    badge(ctx, 'FRENA AQUÍ', LIN, 1240, t, ev.frena, { bg: RED, size: 40, icon: IC.brake });
    const f = ease.inOutQuad(clamp((t - s0 - 0.9) / (ev.pass - s0 - 0.9)));
    const g2 = clamp((t - ev.pass) / 1.2);
    const pm = at(P_M, lerp(0, 0.86, f) + 0.14 * g2), pr = at(P_R, lerp(0, 0.62, f) + 0.25 * g2);
    trail(ctx, P_M, lerp(0, 0.86, f) + 0.14 * g2, '#FFFFFF', 10);
    rivKart(ctx, pr.x, pr.y, pr.ang, 1.2); mauKart(ctx, pm.x, pm.y, pm.ang, 1.2);
    if (f > 0.04 && f < 0.3) G.ellipse(ctx, pm.x, pm.y + 80, 40, 40, { fill: 'rgba(255,40,30,0.5)', lw: 0, seed: 172 });
    const av = clamp((t - ev.vertice) / 0.25);
    if (av > 0) { ctx.save(); ctx.globalAlpha = av; G.ellipse(ctx, C.x - RIN - 45, C.y - 45, 66 + Math.sin(t * 8) * 6, 66 + Math.sin(t * 8) * 6, { fill: null, stroke: YEL, lw: 10, seed: 173 }); ctx.restore(); }
    badge(ctx, 'VÉRTICE', C.x + 60, C.y + 130, t, ev.vertice, { bg: YEL, fg: INK, size: 46, icon: IC.check });
    stepCard(ctx, 3, 'FRENA RECTO', t, ev.p3);
    if (t > ev.pass) { badge(ctx, 'P1', pm.x, pm.y + 140, t, ev.pass, { bg: YEL, fg: INK, size: 60, rot: 0.06 }); G.confetti(ctx, t, ev.pass, { n: 70, seed: 7 }); }
    avatar(ctx, t);
  }
  function ojo(ctx, t) {
    alert(ctx, t);
    const shake = t > ev.choque ? Math.exp(-(t - ev.choque) * 5) * 14 : 0;
    ctx.save(); ctx.translate(Math.sin(t * 60) * shake, Math.cos(t * 50) * shake);
    // the inset: your nose doesn't reach their rear wheels
    const ia = pop(t, ev.ojo + 0.5, 0.3, 1.8);
    if (ia > 0) {
      ctx.save(); ctx.translate(W / 2 + 40, 820); ctx.scale(ia, ia);
      G.rrect(ctx, -330, -300, 660, 600, 36, { fill: '#2B2D35', lw: 8, seed: 181 });
      G.rrect(ctx, -250, -270, 500, 540, 20, { fill: '#45474F', lw: 0, seed: 182 });
      const dv = ease.inQuad(clamp((t - ev.metas) / (ev.choque - ev.metas)));
      rivKart(ctx, -80, -60, -Math.PI / 2, 1.15); mauKart(ctx, lerp(110, 0, dv), lerp(150, -20, dv), -Math.PI / 2 - 0.55 * dv, 1.15);
      ctx.save(); ctx.setLineDash([16, 12]); G.line(ctx, [[-240, -10], [240, -10]], { color: RED, lw: 6, seed: 183, amp: 0 }); ctx.restore();
      G.text(ctx, 'SUS LLANTAS DE ATRÁS', 0, -210, { size: 36, align: 'center', fam: 'Bungee', weight: 400, color: '#FFFFFF' });
      if (t < ev.choque) { const xa = pop(t, ev.metas, 0.2); if (xa > 0) { ctx.save(); ctx.translate(170, 150); ctx.scale(xa, xa); IC.x(ctx, 0, 0, 46, RED); ctx.restore(); } }
      ctx.restore();
    }
    burst(ctx, 230, 400, 140, RED, '¡OJO!', 64, t, ev.ojo);
    badge(ctx, 'NO TE METAS', W / 2, 1230, t, ev.metas, { bg: RED, size: 60, icon: IC.x });
    if (t > ev.choque) { G.rays(ctx, W / 2 + 40, 820, { n: 18, r0: 60, r1: 520, color: '#FFFFFF', lw: 30, spin: 0, seed: 184, alpha: Math.exp(-(t - ev.choque) * 3) }); burst(ctx, W / 2 + 40, 800, 190, RED, '¡PUM!', 70, t, ev.choque); }
    ctx.restore();
    avatar(ctx, t);
  }
  function resumen(ctx, t) {
    corner(ctx, t); ctx.fillStyle = 'rgba(25,20,35,0.6)'; ctx.fillRect(0, 0, W, H);
    G.text(ctx, 'RECUERDA', W / 2, 400, { size: 88, align: 'center', fam: 'Bungee', weight: 400, color: YEL, stroke: INK, strokeW: 10 });
    const items = [['REBUFO', BLUE, IC.wind, ev.r1], ['POR DENTRO', GRN, IC.arrow, ev.r2], ['FRENA RECTO', RED, IC.brake, ev.r3]];
    items.forEach(([l, c, ic, ts], i) => {
      badge(ctx, l, W / 2, 610 + i * 200, t, ts - 0.05, { bg: c, size: 66, rot: i % 2 ? 0.02 : -0.02, icon: ic });
      const cp = pop(t, ts + 0.15, 0.2); if (cp > 0) { ctx.save(); ctx.translate(900, 560 + i * 200); ctx.scale(cp, cp); G.ellipse(ctx, 0, 0, 40, 40, { fill: '#FFFFFF', lw: 6, seed: 190 + i }); IC.check(ctx, 0, 2, 26, GRN); ctx.restore(); }
    });
    badge(ctx, '¡VAS A PASAR A TODOS!', W / 2, 1230, t, ev.todos, { bg: YEL, fg: INK, size: 44, rot: -0.03 });
    avatar(ctx, t);
  }
  function outro(ctx, t) {
    finish(ctx, t);
    const a = t - ev.meta, jump = Math.abs(Math.sin(a * 5.5)) * 50;
    maurito(ctx, 560, 1560 - jump, 1050, t, { sq: 1 + 0.05 * Math.cos(a * 11) });
    G.confetti(ctx, t, ev.meta, { n: 140, seed: 9 });
    badge(ctx, 'SIGUE A MAURO OSORTO', W / 2, 1650, t, ev.meta + 0.4, { bg: RED, size: 46 });
  }

  const film = Shots.film([
    { at: 0, draw: intro, cam: Shots.push(1.0, 1.06) },
    { at: S.S.paso1[0], draw: paso1, in: 'whip', cam: Shots.push(1.04, 1.0) },
    { at: S.S.paso2[0], draw: paso2, in: 'whip', cam: Shots.push(1.0, 1.05) },
    { at: S.S.paso3[0], draw: paso3, in: 'whip', cam: Shots.push(1.05, 1.0) },
    { at: S.S.ojo[0], draw: ojo, in: 'flash', cam: Shots.shake(16, ev.ojo, 6) },
    { at: S.S.resumen[0], draw: resumen, in: 'iris' },
    { at: S.S.outro[0], draw: outro, in: 'flash', cam: Shots.push(1.0, 1.08) },
  ]);

  Studio.film({
    post: { vignette: 0.15, grain: 0.03, paper: 0.15 },
    fadeOut: 0.6,
    async init() {
      VO = await Studio.loadJSON('out/voice.json');
      SUBS = Subs.fromVoice(VO, { maxWords: 4 });
      const img = await Studio.loadImage('assets/maurito.png');
      MAU = makeSticker(img, 14);
    },
    draw(ctx, t) {
      film(ctx, t);
      Subs.draw(ctx, t, SUBS, { style: 'pop' });
    },
  });
})();
