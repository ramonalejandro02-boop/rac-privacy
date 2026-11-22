// Motor "flat" CONAFEPH: ilustración plana con degradados, siluetas y tarjetas flotantes (SVG)
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
export const easeBack = t => { t = clamp(t); const c = 1.6; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
export const prog = (u, a, b) => clamp((u - a) / (b - a));
const f = n => Math.round(n * 10) / 10;
export const FONT = 'font-family="Brand"';
export function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// paletas de cielo
export const SKY = {
  dusk: ['#2B1E4F', '#6B3A78', '#C8607A', '#F2A65A'],
  night: ['#0E1430', '#25204F', '#4A2F6B', '#7A4A7E'],
  teal: ['#0E3B3F', '#1E6B6A', '#5FB3A6', '#CDEBDD'],
  day: ['#3E8FD0', '#79B8E6', '#BFE0F2', '#EAF6FB'],
  green: ['#0D2E26', '#14463A', '#1D5A49', '#246B55'],
  purple: ['#1A1238', '#2F1F5E', '#4A2E86', '#5E3A9C'],
  warm: ['#3A1E2E', '#8A3B3B', '#E07B4A', '#F7C873'],
  golden: ['#2C3E70', '#6A6FA8', '#E7A38A', '#F7D9A0'],
};
export function defs() {
  let s = '<defs>';
  for (const [k, c] of Object.entries(SKY)) s += `<linearGradient id="sky-${k}" x1="0" y1="0" x2="0" y2="1">${c.map((x, i) => `<stop offset="${i / (c.length - 1)}" stop-color="${x}"/>`).join('')}</linearGradient>`;
  s += `<radialGradient id="glowW" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF4D6" stop-opacity=".9"/><stop offset="1" stop-color="#FFF4D6" stop-opacity="0"/></radialGradient>`;
  s += `<radialGradient id="glowG" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#3BD27A" stop-opacity=".55"/><stop offset="1" stop-color="#3BD27A" stop-opacity="0"/></radialGradient>`;
  s += `<radialGradient id="glowR" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FF5A4E" stop-opacity=".7"/><stop offset="1" stop-color="#FF5A4E" stop-opacity="0"/></radialGradient>`;
  s += `<linearGradient id="soil" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7A4E34"/><stop offset="1" stop-color="#3E2619"/></linearGradient>`;
  s += `<linearGradient id="grassG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6CC24A"/><stop offset="1" stop-color="#3E8E3A"/></linearGradient>`;
  s += `<linearGradient id="fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".35"/></linearGradient>`;
  s += `<filter id="sh" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#000" flood-opacity=".35"/></filter>`;
  s += `<filter id="soft"><feGaussianBlur stdDeviation="6"/></filter>`;
  return s + '</defs>';
}
export const sky = (k, h = 1920) => `<rect width="1080" height="${h}" fill="url(#sky-${k})"/>`;
export const glow = (x, y, r, id = 'glowW', op = 1) => `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" fill="url(#${id})" opacity="${op}"/>`;

// cerro con casitas de colores (colonia)
const HOUSE_COLS = ['#E85D75', '#F2A93B', '#4FB0C6', '#8E6FD8', '#5DBB63', '#F06C4B', '#3F8FD2', '#E3C14B', '#C55AB0', '#2FA58C'];
export function hill(seed, yTop, yBase, color, o = {}) {
  const r = rng(seed), amp = o.amp ?? 90, n = 6;
  const pts = []; for (let k = 0; k <= n; k++) pts.push([k * 1080 / n, yTop + Math.sin(k * 1.3 + seed) * amp * r()]);
  let d = `M-40 ${yBase} L-40 ${pts[0][1]}`; pts.forEach(([x, y], k) => { if (k) { const [px, py] = pts[k - 1]; d += ` Q${(px + x) / 2} ${py - 30} ${x} ${y}`; } }); d += ` L1120 ${pts.at(-1)[1]} L1120 ${yBase} Z`;
  let s = `<path d="${d}" fill="${color}"/>`;
  if (o.houses) {
    const dens = o.houses, size = o.size ?? 22, lit = o.lit ?? 0;
    for (let k = 0; k < dens; k++) {
      const x = r() * 1100 - 10, seg = Math.max(0, Math.min(n - 1, Math.floor(x / (1080 / n)))), [x0, y0] = pts[seg], [x1, y1] = pts[seg + 1];
      const yy = lerp(y0, y1, (x - x0) / (x1 - x0)) + 20 + r() * (yBase - yTop) * .85;
      if (yy > yBase - 6) continue;
      const w = size * (.8 + r() * .7), h = size * (.6 + r() * .5), c = HOUSE_COLS[Math.floor(r() * HOUSE_COLS.length)];
      s += `<rect x="${f(x)}" y="${f(yy)}" width="${f(w)}" height="${f(h)}" fill="${c}" opacity="${o.op ?? .95}"/><rect x="${f(x - 2)}" y="${f(yy - 3)}" width="${f(w + 4)}" height="4" fill="#E8E2D6" opacity=".8"/>`;
      if (r() < .6) s += `<rect x="${f(x + w * .3)}" y="${f(yy + h * .3)}" width="${f(w * .25)}" height="${f(h * .3)}" fill="${lit && r() < lit ? '#FFE9A8' : '#2A2240'}" opacity=".85"/>`;
    }
  }
  return s;
}
export function particles(t, n = 18, o = {}) {
  const r = rng(o.seed ?? 3); let s = '';
  for (let k = 0; k < n; k++) { const x = r() * 1080, y0 = (o.y0 ?? 400) + r() * (o.h ?? 1200), sp = .2 + r() * .5, p = (t * sp * .1 + r()) % 1; s += `<circle cx="${f(x + Math.sin(t + k) * 14)}" cy="${f(y0 - p * 200)}" r="${f(2 + r() * 4)}" fill="${o.c ?? '#FFF4D6'}" opacity="${f(Math.sin(p * Math.PI) * (o.op ?? .6))}"/>`; }
  return s;
}
// silueta sin cara (estilo del ejemplo), con luz de borde
// o: {x,y,s,c, arms:{l:[a1,a2], r:[a1,a2]}, hat, bun, skirt, walk, bob, rim}
export function figure(o) {
  const s = o.s ?? 1, c = o.c ?? '#7A4FB0', rim = o.rim ?? '#FFD9A8', bob = o.bob ?? 0;
  const dark = o.dark ?? shade(c, -.25);
  let g = `<g transform="translate(${f(o.x)},${f(o.y)}) scale(${s})">`;
  g += `<ellipse cx="0" cy="0" rx="90" ry="14" fill="#000" opacity=".2"/>`;
  const wk = o.walkAmt ?? 0, ph = o.walk ?? 0;
  for (const [i, sx] of [[0, -1], [1, 1]]) {
    const a = Math.sin(ph + i * Math.PI) * 18 * wk;
    g += `<g transform="rotate(${f(a)} ${sx * 26} -200)"><rect x="${sx * 26 - 24}" y="-210" width="48" height="210" rx="22" fill="${dark}"/></g>`;
  }
  g += `<path d="M-74 ${-360 + bob} Q-80 ${-410 + bob} -40 ${-420 + bob} H40 Q80 ${-410 + bob} 74 ${-360 + bob} L70 -180 Q70 -160 50 -160 H-50 Q-70 -160 -70 -180Z" fill="${c}"/>`;
  if (o.skirt) g += `<path d="M-74 -220 L-96 -110 Q0 -96 96 -110 L74 -220Z" fill="${o.skirt}"/>`;
  g += `<path d="M66 ${-400 + bob} Q78 ${-380 + bob} 74 ${-340 + bob} L70 -190" stroke="${rim}" stroke-width="6" fill="none" opacity=".7" stroke-linecap="round"/>`;
  const arms = o.arms ?? {};
  for (const [side, sd] of [['r', -1], ['l', 1]]) {
    let [a1, a2] = arms[side] ?? [8, 4];
    if (wk) a1 += Math.sin(ph + (sd > 0 ? 0 : Math.PI)) * 16 * wk;
    const x0 = sd * 66, y0 = -392 + bob, R = Math.PI / 180;
    const ex = x0 + sd * Math.sin(a1 * R) * 110, ey = y0 + Math.cos(a1 * R) * 110;
    const hx = ex + sd * Math.sin((a1 + a2) * R) * 100, hy = ey + Math.cos((a1 + a2) * R) * 100;
    g += `<path d="M${f(x0)} ${f(y0)} L${f(ex)} ${f(ey)} L${f(hx)} ${f(hy)}" stroke="${side === 'l' ? c : dark}" stroke-width="40" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
    if (o.hold && o.hold[side]) g += o.hold[side](hx, hy, sd);
  }
  g += `<rect x="-20" y="${-450 + bob}" width="40" height="40" fill="${dark}"/>`;
  g += `<circle cx="0" cy="${-500 + bob}" r="62" fill="${c}"/><path d="M44 ${-540 + bob} Q66 ${-510 + bob} 52 ${-468 + bob}" stroke="${rim}" stroke-width="6" fill="none" opacity=".75" stroke-linecap="round"/>`;
  if (o.bun) g += `<circle cx="0" cy="${-570 + bob}" r="30" fill="${dark}"/><path d="M-62 ${-505 + bob} Q-60 ${-568 + bob} 0 ${-566 + bob} Q60 ${-568 + bob} 62 ${-505 + bob} Q40 ${-540 + bob} 0 ${-542 + bob} Q-40 ${-540 + bob} -62 ${-505 + bob}Z" fill="${dark}"/>`;
  if (o.long) g += `<path d="M-64 ${-500 + bob} Q-66 ${-570 + bob} 0 ${-568 + bob} Q66 ${-570 + bob} 64 ${-500 + bob} L70 ${-400 + bob} H-70Z" fill="${dark}"/>`;
  if (o.hat) g += `<ellipse cx="0" cy="${-536 + bob}" rx="104" ry="20" fill="${o.hat}"/><path d="M-52 ${-536 + bob} Q-50 ${-600 + bob} 0 ${-602 + bob} Q50 ${-600 + bob} 52 ${-536 + bob}Z" fill="${o.hat}"/><rect x="-52" y="${-556 + bob}" width="104" height="12" fill="${shade(o.hat, -.3)}"/>`;
  if (o.cap) g += `<path d="M-60 ${-520 + bob} Q-58 ${-580 + bob} 0 ${-582 + bob} Q58 ${-580 + bob} 60 ${-520 + bob}Z" fill="${o.cap}"/><rect x="0" y="${-528 + bob}" width="96" height="16" rx="8" fill="${o.cap}"/>`;
  return g + `</g>`;
}
export function shade(hex, k) {
  const n = parseInt(hex.slice(1), 16); let r = n >> 16, g = n >> 8 & 255, b = n & 255;
  const m = v => Math.round(k < 0 ? v * (1 + k) : v + (255 - v) * k);
  return '#' + [m(r), m(g), m(b)].map(v => v.toString(16).padStart(2, '0')).join('');
}
export const ARMS = {
  idle: { r: [8, 4], l: [8, 4] }, up: { r: [8, 4], l: [160, 10] }, upBoth: { r: [160, 10], l: [160, 10] },
  point: { r: [8, 4], l: [80, 4] }, pointL: { r: [80, 4], l: [8, 4] }, head: { r: [150, 70], l: [150, 70] },
  hips: { r: [40, -100], l: [40, -100] }, cross: { r: [50, -120], l: [50, -120] }, shrug: { r: [55, 95], l: [55, 95] },
  phone: { r: [8, 4], l: [70, 90] }, wave: { r: [8, 4], l: [150, 20] },
};
// casa plana (vista frontal) con degradado
export function flatHouse(x, y, w, h, o = {}) {
  const wall = o.wall ?? '#3FA7A0', roof = o.roof ?? '#C9C2B6', door = o.door ?? '#C93A5C';
  let s = `<g ${o.filter ? 'filter="url(#sh)"' : ''}>`;
  s += `<rect x="${x}" y="${y - h}" width="${w}" height="${h}" fill="${wall}"/>`;
  s += `<rect x="${x}" y="${y - h}" width="${w}" height="${h}" fill="url(#fog)" opacity=".6"/>`;
  for (let k = 1; k < 7; k++) s += `<path d="M${x} ${y - h + k * h / 7} h${w}" stroke="${shade(wall, -.12)}" stroke-width="3" opacity=".5"/>`;
  s += `<path d="M${x - 24} ${y - h + 6} L${x + w + 24} ${y - h - 18} L${x + w + 24} ${y - h + 4} L${x - 24} ${y - h + 28}Z" fill="${roof}"/>`;
  s += `<rect x="${x + w * .16}" y="${y - h * .62}" width="${w * .2}" height="${h * .62}" fill="${door}"/><rect x="${x + w * .16}" y="${y - h * .62}" width="${w * .2}" height="10" fill="${shade(door, -.3)}"/>`;
  s += `<rect x="${x + w * .55}" y="${y - h * .66}" width="${w * .3}" height="${h * .3}" fill="#2A2240" opacity=".85"/>`;
  for (let k = 1; k < 6; k++) s += `<path d="M${x + w * .55 + k * w * .3 / 6} ${y - h * .66} v${h * .3}" stroke="#E3C14B" stroke-width="5"/>`;
  return s + `</g>`;
}
// árbol de mango plano
export function flatTree(x, y, s = 1, t = 0, o = {}) {
  const sw = Math.sin(t * 1.4) * 1.8;
  let g = `<g transform="translate(${f(x)},${f(y)}) scale(${s})">`;
  g += `<ellipse cx="0" cy="6" rx="220" ry="24" fill="#000" opacity=".2"/>`;
  g += `<path d="M-36 0 Q-24 -160 -40 -300 L-4 -306 Q8 -170 32 0Z" fill="#6E4430"/><path d="M-30 -230 Q-90 -270 -150 -296 M-16 -250 Q40 -296 120 -326" stroke="#6E4430" stroke-width="18" stroke-linecap="round" fill="none"/>`;
  g += `<g transform="rotate(${f(sw)} 0 -300)">`;
  const blobs = [[-170, -360, 120, '#2F7A3E'], [-250, -290, 90, '#2A6E38'], [40, -300, 110, '#2F7A3E'], [-40, -430, 150, '#3E9A4C'], [110, -380, 130, '#358A44'], [230, -330, 100, '#2F7A3E']];
  if (o.over) blobs.push([o.over, -300, 125, '#358A44']);
  blobs.forEach(([bx, by, r, c]) => g += `<circle cx="${bx}" cy="${by}" r="${r}" fill="${c}"/>`);
  blobs.forEach(([bx, by, r]) => g += `<path d="M${bx - r * .6} ${by - r * .55} A${r} ${r} 0 0 1 ${bx + r * .55} ${by - r * .6}" stroke="#7CD06A" stroke-width="10" fill="none" opacity=".35" stroke-linecap="round"/>`);
  [[-120, -330], [60, -360], [170, -300], [-30, -280], [-200, -260], [260, -270]].forEach(([mx, my], k) => g += `<ellipse cx="${mx}" cy="${my + Math.sin(t * 2 + k) * 2}" rx="17" ry="23" fill="#F2A93B"/><ellipse cx="${mx - 5}" cy="${my - 8}" rx="5" ry="8" fill="#FFD27A"/>`);
  g += `</g></g>`;
  return g;
}
// tarjeta de papel flotante
export function paper(x, y, w, h, o = {}) {
  const rot = o.rot ?? 0;
  let s = `<g transform="translate(${f(x)},${f(y)}) rotate(${rot})" filter="url(#sh)">`;
  s += `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${o.rx ?? 10}" fill="${o.bg ?? '#FBF6EC'}"/>`;
  if (o.head) s += `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${o.headH ?? 76}" rx="${o.rx ?? 10}" fill="${o.headBg ?? '#1E2A4A'}"/><rect x="${-w / 2}" y="${-h / 2 + (o.headH ?? 76) - 12}" width="${w}" height="12" fill="${o.headBg ?? '#1E2A4A'}"/><text x="0" y="${-h / 2 + (o.headH ?? 76) * .64}" ${FONT} font-weight="900" font-size="${o.headFs ?? 40}" text-anchor="middle" fill="#fff" letter-spacing="1">${o.head}</text>`;
  s += o.body ?? '';
  return s + `</g>`;
}
export function badge(x, y, text, o = {}) {
  const fs = o.fs ?? 36, w = o.w ?? text.length * fs * .62 + 44, h = fs * 1.55;
  const x0 = o.anchor === 'start' ? x : x - w / 2;
  return `<g filter="url(#sh)"><rect x="${f(x0)}" y="${f(y - h / 2)}" width="${f(w)}" height="${f(h)}" rx="${o.rx ?? 14}" fill="${o.bg ?? '#141A2E'}" stroke="${o.stroke ?? 'none'}" stroke-width="3"/><text x="${f(x0 + w / 2)}" y="${f(y + fs * .36)}" ${FONT} font-weight="800" font-size="${fs}" text-anchor="middle" fill="${o.fg ?? '#fff'}">${text}</text></g>`;
}
export function bigNum(x, y, num, unit, o = {}) {
  const fs = o.fs ?? 96, w = (num.length * fs * .62) + (unit.length * fs * .3) + 80, h = fs * 1.35;
  return `<g filter="url(#sh)"><rect x="${f(x - w / 2)}" y="${f(y - h / 2)}" width="${f(w)}" height="${f(h)}" rx="22" fill="#141A2E" opacity=".92"/><text x="${f(x - w / 2 + 40)}" y="${f(y + fs * .34)}" ${FONT} font-weight="900" font-size="${fs}" fill="${o.c ?? '#F7C948'}">${num}<tspan font-size="${fs * .45}" fill="#fff" dx="12">${unit}</tspan></text></g>`;
}
