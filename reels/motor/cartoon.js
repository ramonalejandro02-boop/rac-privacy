// Motor 2D CONAFEPH: personajes y objetos estilo caricatura con contorno (SVG)
export const K = '#1F1F1F';
export const C = { navy: '#0E2A47', green: '#1E8E4E', red: '#D9483B', soft: '#F3F5F8', gray: '#C9CDD3', sky: '#BFE3F7' };
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
export const easeBack = t => { t = clamp(t); const c = 1.8; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
export const prog = (u, a, b) => clamp((u - a) / (b - a));
const f = n => Math.round(n * 10) / 10;
const D2R = Math.PI / 180;

// ---------- piezas básicas ----------
export const shadow = (x, y, w = 150) => `<ellipse cx="${x}" cy="${y}" rx="${w}" ry="${w * .16}" fill="#000" opacity=".09"/>`;
export function ground(y = 1380, tufts = [120, 300, 820, 960]) {
  let s = `<path d="M0 ${y} Q 270 ${y - 6} 540 ${y} T 1080 ${y}" stroke="${K}" stroke-width="4" fill="none"/>`;
  tufts.forEach((x, i) => s += tuft(x, y + (i % 2 ? 4 : 0)));
  return s;
}
export const tuft = (x, y, s = 1) => `<path d="M${x - 14 * s} ${y} l${6 * s} ${-22 * s} l${4 * s} ${16 * s} l${6 * s} ${-26 * s} l${5 * s} ${24 * s} l${6 * s} ${-16 * s} l${4 * s} ${24 * s}" stroke="${K}" stroke-width="3" fill="none" stroke-linejoin="round"/>`;
export function grassScene(hY = 1150) {
  let s = `<defs><linearGradient id="skyg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8CCDF0"/><stop offset="1" stop-color="#DDF1FB"/></linearGradient></defs>`;
  s += `<rect width="1080" height="${hY}" fill="url(#skyg)"/>`;
  s += `<path d="M0 ${hY} Q 300 ${hY - 30} 600 ${hY - 6} T 1080 ${hY - 10} V1920 H0Z" fill="#86BE5E" stroke="${K}" stroke-width="3"/>`;
  [[90, 1500], [300, 1700], [880, 1520], [700, 1760], [160, 1840], [980, 1820]].forEach(([x, y]) => s += tuft(x, y, 1.2));
  return s;
}

// ---------- personaje ----------
// o: {x,y,s,skin,shirt,pants,shoes,hair,style,cap,mustache,skirt,expr,talk,arms:{l:[a,b],r:[a,b]},hold:{l,r},look,blink,bob,tilt,dim}
export function person(o) {
  const s = o.s ?? 1, skin = o.skin ?? '#E9B48A', shirt = o.shirt ?? '#7FB2E0', pants = o.pants ?? '#3A4250', shoes = o.shoes ?? '#2B2B2B';
  const bob = o.bob ?? 0;
  let g = `<g transform="translate(${f(o.x)},${f(o.y)}) scale(${s})" ${o.dim ? `opacity="${o.dim}"` : ''}>`;
  g += shadow(0, 0, 120);
  // piernas
  const legTop = -260 + bob;
  if (o.skirt) {
    for (const sx of [-30, 30]) g += `<rect x="${sx - 17}" y="${legTop + 40}" width="34" height="${-legTop - 60}" rx="14" fill="${skin}" stroke="${K}" stroke-width="5"/>`;
  } else {
    for (const sx of [-34, 34]) g += `<rect x="${sx - 26}" y="${legTop}" width="52" height="${-legTop - 30}" rx="12" fill="${pants}" stroke="${K}" stroke-width="5"/>`;
  }
  for (const sx of [-36, 36]) g += `<path d="M${sx - 30} -4 v-30 q0 -14 14 -14 h${o.skirt ? 34 : 38} q16 0 ${o.skirt ? 22 : 26} 22 v22 z" fill="${shoes}" stroke="${K}" stroke-width="5" stroke-linejoin="round" transform="${sx < 0 ? `translate(${2 * sx},0) scale(-1,1)` : ''}"/>`;
  // torso
  const sh = -440 + bob, hip = -250 + bob;
  g += `<path d="M-86 ${sh + 28} q0 -30 30 -30 h112 q30 0 30 30 l10 ${hip - sh - 10} q0 14 -14 14 h-164 q-14 0 -14 -14 z" fill="${shirt}" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
  if (o.skirt) g += `<path d="M-92 ${hip - 10} L-118 ${hip + 120} Q0 ${hip + 140} 118 ${hip + 120} L92 ${hip - 10} Z" fill="${o.skirt}" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
  else g += `<rect x="-92" y="${hip - 18}" width="184" height="22" rx="6" fill="${pants}" stroke="${K}" stroke-width="5"/>`;
  if (o.collar !== false) g += `<path d="M-30 ${sh - 2} L0 ${sh + 40} L30 ${sh - 2}" fill="${o.collar ?? '#fff'}" stroke="${K}" stroke-width="4" stroke-linejoin="round"/>`;
  if (o.vest) g += `<path d="M-86 ${sh + 30} L-30 ${sh} L-14 ${hip} H-96Z M86 ${sh + 30} L30 ${sh} L14 ${hip} H96Z" fill="${o.vest}" stroke="${K}" stroke-width="4" stroke-linejoin="round"/>`;
  // brazos
  const arms = o.arms ?? {};
  let front = '';
  for (const [side, sd] of [['r', -1], ['l', 1]]) {
    const [a1, a2] = arms[side] ?? [12, 6];
    const x0 = sd * 84, y0 = sh + 26;
    const ex = x0 + sd * Math.sin(a1 * D2R) * 100, ey = y0 + Math.cos(a1 * D2R) * 100;
    const hx = ex + sd * Math.sin((a1 + a2) * D2R) * 96, hy = ey + Math.cos((a1 + a2) * D2R) * 96;
    let a = `<path d="M${f(x0)} ${f(y0)} L${f(ex)} ${f(ey)} L${f(hx)} ${f(hy)}" stroke="${K}" stroke-width="44" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
    a += `<path d="M${f(ex)} ${f(ey)} L${f(hx)} ${f(hy)}" stroke="${skin}" stroke-width="34" fill="none" stroke-linecap="round"/>`;
    a += `<path d="M${f(x0)} ${f(y0)} L${f(x0 + (ex - x0) * .62)} ${f(y0 + (ey - y0) * .62)}" stroke="${o.sleeve ?? shirt}" stroke-width="34" fill="none" stroke-linecap="round"/>`;
    const held = (o.hold ?? {})[side];
    if (held) a += held(hx, hy, sd);
    a += `<circle cx="${f(hx)}" cy="${f(hy)}" r="24" fill="${skin}" stroke="${K}" stroke-width="5"/>`;
    if ((o.thumb ?? {})[side]) a += `<path d="M${f(hx - 6)} ${f(hy - 18)} q-4 -28 10 -30 q10 0 6 28" fill="${skin}" stroke="${K}" stroke-width="5"/>`;
    if ((a1 > 100 && Math.abs(a1 + a2) > 150) || (o.armsFront ?? []).includes(side)) front += a; else g += a;
  }
  // cuello y cabeza
  const hx0 = 0, hy0 = -545 + bob;
  g += `<rect x="-20" y="${sh - 30}" width="40" height="40" fill="${skin}" stroke="${K}" stroke-width="5"/>`;
  g += `<g transform="rotate(${o.tilt ?? 0} ${hx0} ${hy0 + 60})">`;
  g += hairBack(o, hx0, hy0);
  g += `<circle cx="${hx0 - 92}" cy="${hy0 + 8}" r="18" fill="${skin}" stroke="${K}" stroke-width="5"/><circle cx="${hx0 + 92}" cy="${hy0 + 8}" r="18" fill="${skin}" stroke="${K}" stroke-width="5"/>`;
  g += `<ellipse cx="${hx0}" cy="${hy0}" rx="96" ry="100" fill="${skin}" stroke="${K}" stroke-width="5"/>`;
  g += face(o, hx0, hy0);
  g += hairFront(o, hx0, hy0);
  g += `</g>`;
  g += front;
  g += `</g>`;
  return g;
}
function hairBack(o, x, y) {
  const h = o.hair ?? '#2A1E18';
  if (o.style === 'bun') return `<circle cx="${x}" cy="${y - 108}" r="44" fill="${h}" stroke="${K}" stroke-width="5"/>`;
  if (o.style === 'long') return `<path d="M${x - 104} ${y - 10} Q${x - 120} ${y + 120} ${x - 70} ${y + 130} H${x + 70} Q${x + 120} ${y + 120} ${x + 104} ${y - 10} Z" fill="${h}" stroke="${K}" stroke-width="5"/>`;
  return '';
}
function hairFront(o, x, y) {
  const h = o.hair ?? '#2A1E18';
  let s = '';
  if (o.style === 'bun' || o.style === 'long')
    s += `<path d="M${x - 97} ${y + 10} Q${x - 104} ${y - 104} ${x} ${y - 102} Q${x + 104} ${y - 104} ${x + 97} ${y + 10} Q${x + 70} ${y - 50} ${x + 10} ${y - 62} Q${x - 30} ${y - 40} ${x - 97} ${y + 10}Z" fill="${h}" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
  else if (o.style === 'short') s += `<path d="M${x - 96} ${y - 6} Q${x - 100} ${y - 104} ${x} ${y - 104} Q${x + 100} ${y - 104} ${x + 96} ${y - 6} Q${x + 80} ${y - 56} ${x} ${y - 62} Q${x - 80} ${y - 56} ${x - 96} ${y - 6}Z" fill="${h}" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
  else if (o.style === 'bald') s += `<path d="M${x - 96} ${y + 4} Q${x - 98} ${y - 40} ${x - 80} ${y - 50} L${x - 70} ${y - 10}Z M${x + 96} ${y + 4} Q${x + 98} ${y - 40} ${x + 80} ${y - 50} L${x + 70} ${y - 10}Z" fill="${h}" stroke="${K}" stroke-width="4"/>`;
  if (o.cap) {
    s += `<path d="M${x - 100} ${y - 22} Q${x - 100} ${y - 120} ${x} ${y - 120} Q${x + 100} ${y - 120} ${x + 100} ${y - 22} Z" fill="${o.cap}" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
    s += `<path d="M${x - 104} ${y - 22} H${x + 150} q16 0 12 12 q-4 10 -18 10 H${x - 104}Z" fill="${o.cap}" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
    s += `<circle cx="${x}" cy="${y - 118}" r="8" fill="${o.cap}" stroke="${K}" stroke-width="4"/>`;
    if (o.capLogo) s += `<circle cx="${x}" cy="${y - 62}" r="18" fill="#fff" stroke="${K}" stroke-width="3"/><path d="M${x - 8} ${y - 62} l6 6 l10 -12" stroke="${C.green}" stroke-width="5" fill="none"/>`;
  }
  if (o.glasses) s += `<g fill="none" stroke="${K}" stroke-width="5"><circle cx="${x - 36}" cy="${y - 8}" r="24"/><circle cx="${x + 36}" cy="${y - 8}" r="24"/><path d="M${x - 12} ${y - 10} h24"/></g>`;
  return s;
}
function face(o, x, y) {
  const e = o.expr ?? 'neutral', lk = o.look ?? 0, talk = o.talk ?? 0;
  let s = '';
  const ey = y - 8;
  const blink = o.blink;
  for (const sd of [-1, 1]) {
    const cx = x + sd * 36 + lk * 8;
    if (blink || e === 'content') s += `<path d="M${cx - 12} ${ey + 2} q12 ${e === 'content' ? -12 : 6} 24 0" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round"/>`;
    else if (e === 'shock') s += `<circle cx="${cx}" cy="${ey}" r="16" fill="#fff" stroke="${K}" stroke-width="4"/><circle cx="${cx + lk * 4}" cy="${ey}" r="6" fill="${K}"/>`;
    else s += `<ellipse cx="${cx}" cy="${ey}" rx="9" ry="12" fill="${K}"/><circle cx="${cx + 3}" cy="${ey - 4}" r="3" fill="#fff"/>`;
    // cejas
    const by = ey - 36;
    const br = { neutral: [0, 0], happy: [-4, 0], big: [-6, 0], angry: [10, -10], shock: [-14, 0], worried: [-8, 8], think: sd > 0 ? [-10, 0] : [4, 0], smug: [0, 4], content: [-4, 0] }[e] ?? [0, 0];
    const inner = by + br[0] + (e === 'angry' ? 6 : 0), outer = by + br[0] + br[1] * -1;
    s += `<path d="M${cx - sd * 2 - 16 * -sd} ${inner} L${cx + sd * 18} ${outer + (e === 'angry' ? -6 : e === 'worried' ? 8 : 0)}" stroke="${o.hair ?? K}" stroke-width="7" stroke-linecap="round"/>`;
  }
  // nariz
  s += `<path d="M${x + lk * 6 - 4} ${y + 12} q8 10 0 18" stroke="${K}" stroke-width="4" fill="none" stroke-linecap="round"/>`;
  if (['happy', 'big', 'content'].includes(e)) for (const sd of [-1, 1]) s += `<ellipse cx="${x + sd * 58}" cy="${y + 26}" rx="16" ry="9" fill="#F08A7E" opacity=".45"/>`;
  if (o.mustache) s += `<path d="M${x - 40} ${y + 44} q20 -22 40 -8 q20 -14 40 8 q-20 10 -40 0 q-20 10 -40 0z" fill="${o.hair ?? K}" stroke="${K}" stroke-width="3"/>`;
  // boca
  const my = y + 56;
  if (talk > .05) {
    const h = 6 + talk * 26, w = 20 + talk * 6;
    s += `<ellipse cx="${x + lk * 6}" cy="${my + h / 3}" rx="${w}" ry="${h}" fill="#7A2620" stroke="${K}" stroke-width="4"/>`;
    if (h > 14) s += `<ellipse cx="${x + lk * 6}" cy="${my + h * .9}" rx="${w * .55}" ry="${h * .3}" fill="#E0726A"/>`;
  } else {
    const m = {
      neutral: `<path d="M${x - 16} ${my} h32" stroke="${K}" stroke-width="5" stroke-linecap="round"/>`,
      happy: `<path d="M${x - 30} ${my - 6} Q${x} ${my + 26} ${x + 30} ${my - 6}" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
      content: `<path d="M${x - 26} ${my - 4} Q${x} ${my + 18} ${x + 26} ${my - 4}" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
      big: `<path d="M${x - 36} ${my - 8} Q${x} ${my - 4} ${x + 36} ${my - 8} Q${x + 30} ${my + 40} ${x} ${my + 40} Q${x - 30} ${my + 40} ${x - 36} ${my - 8}Z" fill="#7A2620" stroke="${K}" stroke-width="5"/><path d="M${x - 30} ${my - 6} h60 v8 h-60z" fill="#fff"/><ellipse cx="${x}" cy="${my + 30}" rx="16" ry="7" fill="#E0726A"/>`,
      angry: `<path d="M${x - 26} ${my + 10} Q${x} ${my - 14} ${x + 26} ${my + 10}" stroke="${K}" stroke-width="6" fill="none" stroke-linecap="round"/>`,
      shock: `<ellipse cx="${x}" cy="${my + 8}" rx="18" ry="24" fill="#7A2620" stroke="${K}" stroke-width="5"/>`,
      worried: `<path d="M${x - 26} ${my + 4} q9 -10 17 0 t17 0 t17 0" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
      think: `<path d="M${x - 6} ${my + 2} q14 -6 26 -2" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
      smug: `<path d="M${x - 24} ${my + 2} Q${x + 4} ${my + 14} ${x + 28} ${my - 8}" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
    }[e];
    s += m ?? '';
  }
  return s;
}
// poses de brazos [hombro, codo]
export const POSE = {
  idle: { r: [10, 4], l: [10, 4] },
  point: { r: [12, 6], l: [85, 2] },
  pointR: { r: [85, 2], l: [12, 6] },
  hips: { r: [40, -95], l: [40, -95] },
  shrug: { r: [55, 95], l: [55, 95] },
  head: { r: [141, 73], l: [141, 73] },
  chin: { r: [40, 190], l: [12, 4] },
  chinL: { r: [12, 4], l: [40, 190] },
  wave: { r: [12, 4], l: [150, 15] },
  waveR: { r: [150, 15], l: [12, 4] },
  thumb: { r: [12, 4], l: [40, -110] },
  phone: { r: [150, 65], l: [12, 4] },
  broom: { r: [28, -60], l: [30, -70] },
  hand: { r: [12, 4], l: [55, -40] },
  handR: { r: [55, -40], l: [12, 4] },
  cross: { r: [40, -115], l: [40, -115] },
};

// ---------- objetos ----------
export function broom(x, y, ang = -20, s = 1) {
  return `<g transform="translate(${f(x)},${f(y)}) rotate(${f(ang)}) scale(${s})"><rect x="-8" y="-200" width="16" height="400" rx="6" fill="#C79B66" stroke="${K}" stroke-width="5"/><path d="M-50 200 L-36 150 H36 L50 200 Q0 214 -50 200Z" fill="#E8C35A" stroke="${K}" stroke-width="5" stroke-linejoin="round"/><path d="M-30 168 v30 M-10 168 v34 M10 168 v34 M30 168 v30" stroke="${K}" stroke-width="3"/><rect x="-40" y="140" width="80" height="20" rx="5" fill="${C.green}" stroke="${K}" stroke-width="5"/></g>`;
}
export const holdBroom = sw => (hx, hy) => broom(hx + 30, hy + 60, -25 + sw, 1);
export const holdPhone = () => (hx, hy, sd) => `<rect x="${f(hx - 16)}" y="${f(hy - 50)}" width="32" height="58" rx="7" fill="#2B2F36" stroke="${K}" stroke-width="4"/>`;
export const holdClip = () => (hx, hy) => `<rect x="${f(hx - 40)}" y="${f(hy - 90)}" width="80" height="104" rx="6" fill="#C79B66" stroke="${K}" stroke-width="5"/><rect x="${f(hx - 30)}" y="${f(hy - 78)}" width="60" height="80" fill="#fff" stroke="${K}" stroke-width="3"/><path d="M${f(hx - 20)} ${f(hy - 60)} h40 M${f(hx - 20)} ${f(hy - 44)} h40 M${f(hx - 20)} ${f(hy - 28)} h28" stroke="${K}" stroke-width="3"/>`;

export function house(x, y, w = 920, o = {}) {
  const wall = o.wall ?? '#F6F1E7', body = o.body ?? '#FFFFFF', trim = o.trim ?? C.navy;
  const L = x - w / 2, H = 560, wallH = 250;
  let s = `<g>`;
  // casa
  s += `<rect x="${L + 40}" y="${y - H}" width="${w - 80}" height="${H}" fill="${body}" stroke="${K}" stroke-width="5"/>`;
  s += `<rect x="${L + 20}" y="${y - H - 30}" width="${w - 40}" height="34" fill="#E3E0D8" stroke="${K}" stroke-width="5"/>`;
  s += `<rect x="${L + 40}" y="${y - H + 4}" width="${w - 80}" height="18" fill="${trim}" opacity=".85"/>`;
  // tinaco
  const tx = L + w - 210;
  s += `<path d="M${tx} ${y - H - 30} v-90 q0 -20 60 -20 q60 0 60 20 v90 z" fill="#2A2D33" stroke="${K}" stroke-width="5"/><ellipse cx="${tx + 60}" cy="${y - H - 136}" rx="40" ry="9" fill="#4A4F57" stroke="${K}" stroke-width="4"/>`;
  // ventanas con balcón
  for (const wx of [L + 110, L + w - 330]) {
    s += `<rect x="${wx}" y="${y - H + 70}" width="220" height="150" fill="#BFE0F2" stroke="${K}" stroke-width="5"/>`;
    for (let i = 1; i < 6; i++) s += `<path d="M${wx + i * 220 / 6} ${y - H + 70} v150" stroke="${K}" stroke-width="4"/>`;
    s += `<path d="M${wx} ${y - H + 145} h220" stroke="${K}" stroke-width="4"/>`;
  }
  // muro perimetral y portón
  const gx = x + (o.gateOff ?? 120), gw = o.gateW ?? 340;
  s += `<rect x="${L}" y="${y - wallH}" width="${gx - gw / 2 - L}" height="${wallH}" fill="${wall}" stroke="${K}" stroke-width="5"/>`;
  s += `<rect x="${gx + gw / 2}" y="${y - wallH}" width="${L + w - gx - gw / 2}" height="${wallH}" fill="${wall}" stroke="${K}" stroke-width="5"/>`;
  s += `<rect x="${L - 6}" y="${y - wallH - 16}" width="${gx - gw / 2 - L + 12}" height="18" fill="#E3E0D8" stroke="${K}" stroke-width="4"/><rect x="${gx + gw / 2 - 6}" y="${y - wallH - 16}" width="${L + w - gx - gw / 2 + 12}" height="18" fill="#E3E0D8" stroke="${K}" stroke-width="4"/>`;
  s += `<g>`;
  s += `<rect x="${gx - gw / 2}" y="${y - wallH + 10}" width="${gw}" height="${wallH - 10}" fill="none" stroke="${trim}" stroke-width="10"/>`;
  for (let i = 1; i < 10; i++) s += `<path d="M${gx - gw / 2 + i * gw / 10} ${y - wallH + 10} v${wallH - 10}" stroke="${trim}" stroke-width="7"/>`;
  s += `<rect x="${gx - gw / 2}" y="${y - 90}" width="${gw}" height="80" fill="${trim}"/>`;
  s += `</g>`;
  if (o.number !== false) s += `<rect x="${L + 30}" y="${y - wallH + 40}" width="70" height="44" rx="6" fill="#fff" stroke="${K}" stroke-width="4"/><text x="${L + 65}" y="${y - wallH + 73}" font-size="28" font-weight="800" text-anchor="middle" font-family="Baloo" fill="${K}">${o.number ?? 12}</text>`;
  s += `</g>`;
  return s;
}
export function sidewalk(y = 1380) {
  return `<rect x="-10" y="${y}" width="1100" height="40" fill="#E4E6EA" stroke="${K}" stroke-width="4"/><rect x="-10" y="${y + 40}" width="1100" height="400" fill="#9AA1AC"/><path d="M0 ${y + 180} h120 M240 ${y + 180} h120 M480 ${y + 180} h120 M720 ${y + 180} h120 M960 ${y + 180} h120" stroke="#fff" stroke-width="10"/>`;
}
export function car(x, y, color = '#5B8BC6', o = {}) {
  const s = o.s ?? 1, flip = o.flip ? -1 : 1, rot = o.wheel ?? 0;
  let g = `<g transform="translate(${f(x)},${f(y)}) scale(${flip * s},${s})">`;
  g += shadow(0, 4, 280);
  g += `<path d="M-270 -60 Q-276 -130 -230 -140 L-150 -150 Q-110 -240 -40 -244 H90 Q140 -244 180 -160 L250 -146 Q284 -138 284 -96 V-60 Q284 -40 262 -40 H-250 Q-270 -40 -270 -60Z" fill="${color}" stroke="${K}" stroke-width="6" stroke-linejoin="round"/>`;
  g += `<path d="M-128 -152 Q-96 -224 -40 -226 H20 V-152Z" fill="#CFE8F6" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
  g += `<path d="M40 -226 H88 Q128 -226 158 -152 H40Z" fill="#CFE8F6" stroke="${K}" stroke-width="5" stroke-linejoin="round"/>`;
  g += `<path d="M30 -150 V-50 M-130 -100 h30 M60 -100 h30" stroke="${K}" stroke-width="4" fill="none"/>`;
  g += `<path d="M262 -120 h18 v24 h-22z" fill="#FFE9A8" stroke="${K}" stroke-width="4"/><path d="M-268 -118 h14 v24 h-14z" fill="#E2554A" stroke="${K}" stroke-width="4"/>`;
  for (const wx of [-160, 170]) {
    g += `<circle cx="${wx}" cy="-40" r="52" fill="#262A30" stroke="${K}" stroke-width="5"/><circle cx="${wx}" cy="-40" r="24" fill="#C8CDD4" stroke="${K}" stroke-width="4"/>`;
    g += `<g transform="rotate(${f(rot)} ${wx} -40)"><path d="M${wx - 24} -40 h48 M${wx} -64 v48" stroke="${K}" stroke-width="4"/></g>`;
  }
  g += `</g>`;
  return g;
}
export function tire(x, y, s = 1) { return `<g transform="translate(${f(x)},${f(y)}) scale(${s})"><ellipse cx="0" cy="-40" rx="70" ry="40" fill="#2A2D33" stroke="${K}" stroke-width="5"/><ellipse cx="0" cy="-46" rx="34" ry="16" fill="#5A606A" stroke="${K}" stroke-width="4"/><path d="M-70 -40 v20 q0 22 70 24 q70 -2 70 -24 v-20" fill="#2A2D33" stroke="${K}" stroke-width="5"/></g>`; }
export function stone(x, y, s = 1) { return `<g transform="translate(${f(x)},${f(y)}) scale(${s})"><path d="M-60 0 Q-70 -50 -30 -66 Q10 -84 46 -60 Q74 -36 62 0Z" fill="#B8B2A7" stroke="${K}" stroke-width="5"/><path d="M-20 -50 q14 -8 26 -2" stroke="${K}" stroke-width="3" fill="none"/></g>`; }

// ---------- efectos ----------
export function anger(x, y, t, s = 1) {
  const k = .85 + .15 * Math.sin(t * 14);
  return `<g transform="translate(${x},${y}) scale(${s * k})" stroke="${C.red}" stroke-width="7" fill="none" stroke-linecap="round">${[1, 2, 3].map(i => `<path d="M${-60 - i * 26} ${-i * 34} a${80 + i * 30} ${80 + i * 30} 0 0 0 0 ${i * 68}" opacity="${1 - i * .2}"/><path d="M${60 + i * 26} ${-i * 34} a${80 + i * 30} ${80 + i * 30} 0 0 1 0 ${i * 68}" opacity="${1 - i * .2}"/>`).join('')}</g>`;
}
export const qmark = (x, y, s = 1, c = C.navy) => `<text x="${x}" y="${y}" font-family="Baloo" font-weight="800" font-size="${120 * s}" text-anchor="middle" fill="${c}" stroke="${K}" stroke-width="3">?</text>`;
export const excl = (x, y, s = 1) => `<text x="${x}" y="${y}" font-family="Baloo" font-weight="800" font-size="${130 * s}" text-anchor="middle" fill="${C.red}" stroke="${K}" stroke-width="3">!</text>`;
export function sparkle(x, y, s = 1, c = '#F2C230') { return `<path transform="translate(${x},${y}) scale(${s})" d="M0 -30 Q4 -4 30 0 Q4 4 0 30 Q-4 4 -30 0 Q-4 -4 0 -30Z" fill="${c}" stroke="${K}" stroke-width="3"/>`; }
export function sweat(x, y, s = 1) { return `<path transform="translate(${x},${y}) scale(${s})" d="M0 -30 Q22 0 14 16 Q0 30 -14 16 Q-22 0 0 -30Z" fill="#8FD0F5" stroke="${K}" stroke-width="4"/>`; }
export function notes(x, y, t) { return [0, 1].map(i => { const p = (t * .8 + i * .5) % 1; return `<text x="${x + i * 40 + Math.sin(p * 6) * 10}" y="${y - p * 120}" font-size="64" opacity="${1 - p}" fill="${C.navy}">${i ? '♫' : '♪'}</text>`; }).join(''); }
export function check(x, y, s = 1) { return `<g transform="translate(${x},${y}) scale(${s})"><circle r="52" fill="${C.green}" stroke="${K}" stroke-width="5"/><path d="M-24 2 l16 16 l32 -36" stroke="#fff" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>`; }
export function cross(x, y, s = 1) { return `<g transform="translate(${x},${y}) scale(${s})"><circle r="52" fill="${C.red}" stroke="${K}" stroke-width="5"/><path d="M-20 -20 l40 40 M20 -20 l-40 40" stroke="#fff" stroke-width="12" stroke-linecap="round"/></g>`; }
export function label(x, y, text, o = {}) {
  const fs = o.fs ?? 46, padX = o.padX ?? 30, w = o.w ?? text.length * fs * .56 + padX * 2, h = fs * 1.5;
  const bg = o.bg ?? '#fff', fg = o.fg ?? C.navy;
  return `<g transform="translate(${f(x)},${f(y)}) scale(${o.s ?? 1}) rotate(${o.rot ?? 0})"><rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${o.rx ?? 16}" fill="${bg}" stroke="${o.stroke ?? K}" stroke-width="5"/><text x="0" y="${fs * .35}" font-family="Baloo" font-weight="800" font-size="${fs}" text-anchor="middle" fill="${fg}">${text}</text></g>`;
}
export function bubble(x, y, lines, o = {}) {
  const fs = o.fs ?? 52, w = o.w ?? 760, h = lines.length * fs * 1.15 + 70, tx = o.tail ?? 0;
  let s = `<g transform="translate(${f(x)},${f(y)}) scale(${o.s ?? 1})">`;
  s += `<path d="M${-w / 2 + 40} ${-h} H${w / 2 - 40} Q${w / 2} ${-h} ${w / 2} ${-h + 40} V-40 Q${w / 2} 0 ${w / 2 - 40} 0 H${tx + 40} L${tx + (o.tailDx ?? -20)} 70 L${tx - 20} 0 H${-w / 2 + 40} Q${-w / 2} 0 ${-w / 2} -40 V${-h + 40} Q${-w / 2} ${-h} ${-w / 2 + 40} ${-h}Z" fill="${o.bg ?? '#fff'}" stroke="${K}" stroke-width="6" stroke-linejoin="round"/>`;
  if (o.who) s += `<text x="${-w / 2 + 40}" y="${-h + 52}" font-family="Baloo" font-weight="800" font-size="30" fill="${C.green}" letter-spacing="2">${o.who}</text>`;
  lines.forEach((l, i) => s += `<text x="0" y="${-h + 40 + (o.who ? 30 : 10) + (i + 1) * fs * 1.1}" font-family="Baloo" font-weight="800" font-size="${fs}" text-anchor="middle" fill="${o.fg ?? C.navy}">${l}</text>`);
  return s + `</g>`;
}
export function stamp(x, y, text, color, p, rot = -8) {
  const k = p <= 0 ? 0 : lerp(2.2, 1, easeOut(p));
  return p <= 0 ? '' : `<g transform="translate(${x},${y}) rotate(${rot}) scale(${k})" opacity="${clamp(p * 2)}"><rect x="${-text.length * 26 - 30}" y="-50" width="${text.length * 52 + 60}" height="100" rx="14" fill="#fff" stroke="${color}" stroke-width="10"/><text y="26" font-family="Baloo" font-weight="800" font-size="76" text-anchor="middle" fill="${color}" letter-spacing="6">${text}</text></g>`;
}
export function icoMuni(x, y, s = 1) { return `<g transform="translate(${x},${y}) scale(${s})"><path d="M-90 -60 L0 -120 L90 -60Z" fill="${C.navy}" stroke="${K}" stroke-width="5"/><rect x="-80" y="-60" width="160" height="16" fill="#fff" stroke="${K}" stroke-width="4"/>${[-60, -20, 20, 60].map(c => `<rect x="${c - 9}" y="-44" width="18" height="84" fill="#fff" stroke="${K}" stroke-width="4"/>`).join('')}<rect x="-90" y="40" width="180" height="18" fill="#fff" stroke="${K}" stroke-width="4"/></g>`; }
export function icoPolice(x, y, s = 1) { return `<g transform="translate(${x},${y}) scale(${s})"><path d="M0 -100 L70 -76 V-10 Q70 60 0 96 Q-70 60 -70 -10 V-76Z" fill="${C.navy}" stroke="${K}" stroke-width="5"/><path d="M0 -50 l14 30 l32 4 l-24 22 l6 32 l-28 -16 l-28 16 l6 -32 l-24 -22 l32 -4z" fill="#F2C230" stroke="${K}" stroke-width="3"/></g>`; }
export function noParking(x, y, s = 1) { return `<g transform="translate(${x},${y}) scale(${s})"><circle r="70" fill="#fff" stroke="${C.red}" stroke-width="14"/><text y="34" font-family="Baloo" font-weight="800" font-size="100" text-anchor="middle" fill="${C.navy}">P</text><path d="M-48 -48 L48 48" stroke="${C.red}" stroke-width="14"/></g>`; }

// transición de barrido ondulado (estilo pincel)
export function wipe(p) {
  if (p <= 0 || p >= 1) return '';
  const X = lerp(1250, -1800, p);
  let d = `M${X} -40`;
  for (let y = -40; y <= 1960; y += 40) d += ` L${f(X + Math.sin(y / 140 + p * 4) * 46 + Math.sin(y / 53) * 12)} ${y}`;
  d += ` L${X + 1600} 1960 L${X + 1600} -40Z`;
  return `<path d="${d}" fill="#000" opacity=".12" transform="translate(-28,0)" filter="url(#blur)"/><path d="${d}" fill="#fff"/>`;
}
