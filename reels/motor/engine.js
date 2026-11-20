// Motor 3D CONAFEPH: colonia hondureña, personajes y utilidades de animación (Three.js)
import * as THREE from 'three';
import { RoundedBoxGeometry } from './lib/addons/RoundedBoxGeometry.js';
export { THREE };

export const PAL = {
  navy: 0x0E2A47, green: 0x1E8E4E, white: 0xFAFAF7, alert: 0xC8553D,
  asphalt: 0x4B5361, sidewalk: 0xD7DADF, curb: 0xBFC5CC, grass: 0x8FBF7A,
  skin1: 0xC98B62, skin2: 0xB57A52, skin3: 0xD9A07A,
};

// ---------- utilidades ----------
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
export const easeBack = t => { t = clamp(t); const c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
export const prog = (u, a, b) => clamp((u - a) / (b - a));
export const v3 = (x, y, z) => new THREE.Vector3(x, y, z);

const matCache = new Map();
export function mat(color, o = {}) {
  const k = color + JSON.stringify(o);
  if (!matCache.has(k)) matCache.set(k, new THREE.MeshStandardMaterial({ color, roughness: o.r ?? .75, metalness: o.m ?? 0, transparent: o.op !== undefined, opacity: o.op ?? 1, emissive: o.em ?? 0x000000, emissiveIntensity: o.ei ?? 1 }));
  return matCache.get(k);
}
export function mesh(geo, m, p = [0, 0, 0], shadow = true) {
  const x = new THREE.Mesh(geo, m); x.position.set(...p); x.castShadow = shadow; x.receiveShadow = true; return x;
}
const box = (w, h, d, c, p, o) => mesh(new THREE.BoxGeometry(w, h, d), mat(c, o), p);
const rbox = (w, h, d, r, c, p, o) => mesh(new RoundedBoxGeometry(w, h, d, 3, r), mat(c, o), p);

// ---------- render ----------
export function createWorld(canvas, W = 1080, H = 1920) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene();
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d'); const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, '#6FB2E6'); gr.addColorStop(.6, '#BFE0F6'); gr.addColorStop(1, '#F3F1E8');
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  const sky = new THREE.CanvasTexture(c); sky.colorSpace = THREE.SRGBColorSpace; scene.background = sky;
  scene.fog = new THREE.Fog(0xDCEBF5, 35, 90);
  const camera = new THREE.PerspectiveCamera(38, W / H, .1, 300);
  const hemi = new THREE.HemisphereLight(0xDDEEFF, 0xC9B79C, 1.1); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xFFF1DC, 2.6);
  sun.position.set(-14, 22, 16); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); const s = sun.shadow.camera; s.left = -26; s.right = 26; s.top = 26; s.bottom = -26; s.far = 80;
  sun.shadow.bias = -0.0005; sun.shadow.radius = 4; scene.add(sun); scene.add(sun.target);
  return { renderer, scene, camera, sun, hemi };
}

// ---------- colonia ----------
function windowGrill(w, h) {
  const g = new THREE.Group();
  g.add(box(w, h, .06, 0x9DB7CC, [0, 0, 0], { r: .2, m: .1 }));
  g.add(box(w + .16, .1, .14, 0xF2F2EE, [0, -h / 2 - .05, .02]));
  for (let i = 1; i < 5; i++) g.add(box(.035, h, .08, PAL.navy, [-w / 2 + i * w / 5, 0, .06]));
  g.add(box(w, .035, .08, PAL.navy, [0, 0, .06]));
  return g;
}
function gate(w, h, color = PAL.navy) {
  const g = new THREE.Group();
  g.add(box(w, .1, .1, color, [0, h - .05, 0])); g.add(box(w, .1, .1, color, [0, .1, 0]));
  const n = Math.round(w / .16);
  for (let i = 0; i <= n; i++) g.add(box(.04, h, .05, color, [-w / 2 + i * w / n, h / 2, 0]));
  g.add(box(w, h * .35, .03, color, [0, h * .22, 0]));
  return g;
}
export function house({ x, w = 6.4, color = 0xF4EBDD, trim = PAL.navy, side = -1, gateX = .8, gateW = 2.8, tank = true, rebar = false, stories = 1 }) {
  // side=-1: frente hacia +z, ubicada en z negativo
  const G = new THREE.Group(); G.position.set(x, 0, side < 0 ? -5.6 : 5.6); if (side > 0) G.rotation.y = Math.PI;
  const H = 3.3 * stories, D = 5;
  G.add(box(w - .2, H, D, color, [0, H / 2, -1.1 - D / 2], { r: .9 }));
  G.add(box(w, .28, D + .5, 0xE9E6DF, [0, H + .14, -1.1 - D / 2 + .1]));
  G.add(box(w - .2, .12, .14, trim, [0, H - .3, -1.04]));
  for (let s = 0; s < stories; s++) {
    G.add(windowGrill(1.4, 1.05).translateX(-w / 2 + 1.4).translateY(2.05 + s * 3.3).translateZ(-1.05));
    if (s > 0) G.add(windowGrill(1.4, 1.05).translateX(w / 2 - 1.5).translateY(2.05 + s * 3.3).translateZ(-1.05));
  }
  G.add(box(.95, 2.1, .08, trim, [w / 2 - 1.5, 1.05, -1.05]));
  // muro perimetral con portón
  const wallH = 2.05, gl = gateX - gateW / 2, gr = gateX + gateW / 2;
  const segL = gl + w / 2, segR = w / 2 - gr;
  if (segL > 0) G.add(box(segL, wallH, .22, color, [-w / 2 + segL / 2, wallH / 2, 0], { r: .9 }));
  if (segR > 0) G.add(box(segR, wallH, .22, color, [gr + segR / 2, wallH / 2, 0], { r: .9 }));
  G.add(box(w, .1, .3, 0xEDEAE3, [0, wallH + .05, 0]));
  G.add(box(w, .3, .24, trim, [0, .15, .01]));
  const gt = gate(gateW, 1.95, trim); gt.position.set(gateX, 0, 0); G.add(gt); G.userData.gate = gt;
  // patio
  G.add(box(w - .2, .04, 1.1, 0xCFCAC0, [0, .02, -.55], { r: 1 }));
  if (tank) { const t = mesh(new THREE.CylinderGeometry(.5, .55, 1.0, 20), mat(0x1F2328, { r: .5 }), [-w / 2 + 1.1, H + .78, -4]); G.add(t); }
  if (rebar) for (let i = 0; i < 4; i++) G.add(mesh(new THREE.CylinderGeometry(.025, .025, .9, 6), mat(0x7A5A44, { r: .6, m: .4 }), [w / 2 - .4, H + .7, -1.4 - i * 1.2]));
  return G;
}
export function pole(x, z) {
  const g = new THREE.Group(); g.position.set(x, 0, z);
  g.add(mesh(new THREE.CylinderGeometry(.11, .15, 8, 10), mat(0xB9B4AA), [0, 4, 0]));
  g.add(box(1.8, .12, .12, 0x8C877E, [0, 7.4, 0]));
  return g;
}
export function wire(scene, a, b, sag = .8, color = 0x22262B) {
  const pts = []; for (let i = 0; i <= 20; i++) { const t = i / 20; const p = a.clone().lerp(b, t); p.y -= Math.sin(Math.PI * t) * sag; pts.push(p); }
  const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, .018, 4), mat(color)); scene.add(m);
}
export function tree(x, z, s = 1) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s);
  g.add(mesh(new THREE.CylinderGeometry(.14, .2, 2.2, 8), mat(0x7A5A40), [0, 1.1, 0]));
  [[0, 2.8, 0, 1.25], [.7, 2.5, .3, .85], [-.7, 2.55, -.2, .9], [.1, 3.4, -.3, .8]].forEach(([a, b, c, r]) =>
    g.add(mesh(new THREE.IcosahedronGeometry(r, 2), mat(0x4E9A5C, { r: .9 }), [a, b, c])));
  return g;
}
export function buildColonia(scene) {
  const R = {};
  const ground = mesh(new THREE.PlaneGeometry(300, 300), mat(0xCBBFA6), [0, -.02, 0], false); ground.rotation.x = -Math.PI / 2; scene.add(ground);
  const road = mesh(new THREE.PlaneGeometry(120, 8), mat(PAL.asphalt, { r: .95 }), [0, 0, 0], false); road.rotation.x = -Math.PI / 2; scene.add(road);
  for (let x = -60; x < 60; x += 4) { const d = mesh(new THREE.PlaneGeometry(1.8, .16), mat(0xF4F4F0), [x, .005, 0], false); d.rotation.x = -Math.PI / 2; scene.add(d); }
  for (const s of [-1, 1]) {
    scene.add(box(120, .16, 1.6, PAL.sidewalk, [0, .08, s * 4.8], { r: .95 }));
    scene.add(box(120, .2, .14, PAL.curb, [0, .1, s * 4.02]));
  }
  // rampa de entrada (casa de Marta)
  R.ramp = box(2.8, .17, 1.6, 0xE8E6E0, [1.6, .09, -4.8], { r: .95 }); scene.add(R.ramp);
  const cols = [0xF2DCC2, 0xCFE3F2, 0xFAFAF7, 0xD6EBDD, 0xEBD9BF, 0xF5E6A8, 0xE3D3EA];
  R.houses = [];
  const xs = [-20, -13.4, -6.8, 0, 6.8, 13.4, 20];
  xs.forEach((x, i) => {
    const h = house({ x, w: 6.6, color: x === 0 ? 0xFAFAF7 : cols[i % cols.length], trim: x === 0 ? PAL.navy : [0x3A4B5C, 0x6B4E3D, PAL.navy, 0x2F5D50][i % 4], gateX: x === 0 ? 1.6 : (i % 2 ? .9 : -.6), stories: i === 1 || i === 5 ? 2 : 1, rebar: i === 4 || i === 1, tank: i !== 2 });
    scene.add(h); R.houses.push(h); if (x === 0) R.marta = h;
  });
  xs.forEach((x, i) => scene.add(house({ x: x + 3.3, w: 6.6, color: cols[(i + 3) % cols.length], side: 1, gateX: (i % 2 ? .9 : -.6), stories: i % 3 === 0 ? 2 : 1, rebar: i % 2 === 0 })));
  const poles = [[-10, -4.4], [5.6, -4.4], [17.5, -4.4], [-6.5, 4.4], [11, 4.4]];
  poles.forEach(p => scene.add(pole(...p)));
  for (const [a, b] of [[0, 1], [1, 2]]) for (const dx of [-.8, .8]) wire(scene, v3(poles[a][0] + dx, 7.4, -4.4), v3(poles[b][0] + dx, 7.4, -4.4), .7);
  wire(scene, v3(-6.5, 7.1, 4.4), v3(11, 7.1, 4.4), .7); wire(scene, v3(5.6, 7.1, -4.4), v3(-6.5, 7.1, 4.4), .5);
  [[-16, 5.2, 1.1], [8, 5.2, .9], [25, -5, 1], [-27, 5.2, 1.2]].forEach(t => scene.add(tree(...t)));
  // montañas al fondo (Honduras)
  for (let i = 0; i < 9; i++) { const m = mesh(new THREE.ConeGeometry(14 + (i % 3) * 5, 10 + (i % 4) * 3, 7), mat(i % 2 ? 0x7FAE86 : 0x6E9E79, { r: 1 }), [-70 + i * 18, 4, -70 - (i % 3) * 10], false); scene.add(m); }
  return R;
}

// ---------- vehículos y objetos ----------
export function car(color = 0x5B7A99) {
  const g = new THREE.Group(); const body = new THREE.Group(); g.add(body);
  body.add(rbox(3.9, .75, 1.75, .28, color, [0, .68, 0], { r: .35, m: .2 }));
  body.add(rbox(2.2, .72, 1.55, .26, 0x2B3C52, [-.25, 1.3, 0], { r: .15, m: .3 }));
  body.add(rbox(2.0, .1, 1.5, .05, color, [-.25, 1.67, 0], { r: .35, m: .2 }));
  for (const z of [-.8, .8]) { body.add(rbox(.2, .14, .3, .05, 0xFFF6D8, [1.92, .78, z * .8], { em: 0xFFF2C8, ei: .4 })); body.add(rbox(.12, .14, .28, .05, 0xD3423B, [-1.95, .8, z * .82])); }
  body.add(box(.1, .14, 1.0, 0x2A2F36, [1.97, .5, 0]));
  g.userData.wheels = [];
  for (const [x, z] of [[1.25, .82], [-1.25, .82], [1.25, -.82], [-1.25, -.82]]) {
    const w = new THREE.Group(); w.position.set(x, .38, z);
    const t = mesh(new THREE.CylinderGeometry(.38, .38, .28, 22), mat(0x1C1F24, { r: .9 })); t.rotation.x = Math.PI / 2; w.add(t);
    const h = mesh(new THREE.CylinderGeometry(.2, .2, .3, 14), mat(0xC9CED6, { m: .6, r: .3 })); h.rotation.x = Math.PI / 2; w.add(h);
    g.add(w); g.userData.wheels.push(w);
  }
  g.userData.body = body;
  g.userData.setX = (x, prevX) => { g.position.x = x; const d = x - (prevX ?? x); g.userData.wheels.forEach(w => w.rotation.z -= d / .38); };
  return g;
}
export function tire() { const t = mesh(new THREE.TorusGeometry(.36, .16, 12, 24), mat(0x1E2125, { r: .95 })); t.rotation.x = Math.PI / 2; const g = new THREE.Group(); t.position.y = .16; g.add(t); return g; }
export function stone(s = 1) { const g = new THREE.Group(); const m = mesh(new THREE.DodecahedronGeometry(.32 * s, 1), mat(0x9A958C, { r: 1 }), [0, .25 * s, 0]); m.scale.y = .7; g.add(m); return g; }
export function textPlane(text, { w = 4, h = 1, bg = '#0E2A47', fg = '#fff', font = 900, size = 110 } = {}) {
  const c = document.createElement('canvas'); c.width = 1024; c.height = Math.round(1024 * h / w);
  const g = c.getContext('2d'); g.fillStyle = bg; g.fillRect(0, 0, c.width, c.height);
  g.fillStyle = fg; g.font = `${font} ${size}px Montserrat`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text, c.width / 2, c.height / 2 + 6);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: t, roughness: .8 }), [0, 0, 0], false);
}

// ---------- personajes ----------
export function character(o) {
  const C = { skin: PAL.skin1, shirt: 0xE8A87C, pants: 0x34465C, hair: 0x2B1E17, shoes: 0x2A2A2E, ...o };
  const g = new THREE.Group(); const rig = new THREE.Group(); g.add(rig);
  const legs = [];
  for (const s of [-1, 1]) {
    const hip = new THREE.Group(); hip.position.set(s * .13, .78, 0);
    hip.add(mesh(new THREE.CapsuleGeometry(.105, .42, 6, 12), mat(C.pants), [0, -.36, 0]));
    hip.add(rbox(.2, .12, .32, .05, C.shoes, [0, -.73, .05]));
    rig.add(hip); legs.push(hip);
  }
  const torso = new THREE.Group(); torso.position.y = .8; rig.add(torso);
  torso.add(mesh(new THREE.CapsuleGeometry(.31, .32, 8, 18), mat(C.shirt), [0, .3, 0]));
  if (C.skirt) torso.add(mesh(new THREE.CylinderGeometry(.3, .44, .5, 20), mat(C.skirt), [0, -.08, 0]));
  if (C.collar) torso.add(mesh(new THREE.TorusGeometry(.17, .045, 8, 18), mat(C.collar), [0, .66, 0]).rotateX(Math.PI / 2));
  const arms = [];
  for (const s of [-1, 1]) {
    const sh = new THREE.Group(); sh.position.set(s * .37, .5, 0);
    sh.add(mesh(new THREE.CapsuleGeometry(.085, .36, 6, 10), mat(C.sleeve ?? C.shirt), [0, -.24, 0]));
    sh.add(mesh(new THREE.SphereGeometry(.095, 14, 12), mat(C.skin), [0, -.5, 0]));
    sh.rotation.z = s * .12; torso.add(sh); arms.push(sh);
  }
  const head = new THREE.Group(); head.position.y = .98; torso.add(head);
  const skull = mesh(new THREE.SphereGeometry(.4, 32, 24), mat(C.skin, { r: .6 })); skull.scale.set(1, .97, .95); head.add(skull);
  for (const s of [-1, 1]) head.add(mesh(new THREE.SphereGeometry(.08, 12, 10), mat(C.skin), [s * .39, -.02, 0]));
  const eyes = [];
  for (const s of [-1, 1]) {
    const e = new THREE.Group(); e.position.set(s * .145, .03, .33);
    const wht = mesh(new THREE.SphereGeometry(.088, 16, 14), mat(0xFFFFFF, { r: .3 }), [0, 0, 0], false); wht.scale.z = .55; e.add(wht);
    e.add(mesh(new THREE.SphereGeometry(.056, 14, 12), mat(0x2A1B12, { r: .2 }), [0, -.005, .035], false));
    e.add(mesh(new THREE.SphereGeometry(.018, 8, 8), mat(0xFFFFFF, { em: 0xffffff, ei: .6 }), [.02 * s, .025, .075], false));
    head.add(e); eyes.push(e);
    const brow = rbox(.14, .035, .03, .012, C.hair, [s * .15, .15, .36]); brow.rotation.z = -s * .08; head.add(brow); e.userData.brow = brow;
  }
  head.add(mesh(new THREE.SphereGeometry(.055, 12, 10), mat(C.skin2 ?? C.skin, { r: .6 }), [0, -.06, .39], false));
  for (const s of [-1, 1]) { const ck = mesh(new THREE.SphereGeometry(.07, 12, 10), mat(0xE88E7D, { op: .45 }), [s * .23, -.1, .3], false); ck.scale.z = .3; head.add(ck); }
  const mouth = mesh(new THREE.SphereGeometry(.08, 16, 12), mat(0x7A2E2A, { r: .5 }), [0, -.19, .355], false); mouth.scale.set(1, .25, .35); head.add(mouth);
  // pelo
  const hairM = mat(C.hair, { r: .85 });
  const cap = mesh(new THREE.SphereGeometry(.42, 32, 16, 0, Math.PI * 2, 0, Math.PI * (C.longHair ? .62 : .48)), hairM); cap.rotation.x = -.35; cap.position.set(0, .03, -.03); head.add(cap);
  if (C.bun) head.add(mesh(new THREE.SphereGeometry(.17, 16, 12), hairM, [0, .3, -.3]));
  if (C.longHair) { const b = mesh(new THREE.CapsuleGeometry(.3, .3, 6, 16), hairM, [0, -.12, -.17]); b.scale.z = .7; head.add(b); }
  if (C.mustache) head.add(rbox(.24, .06, .07, .03, C.hair, [0, -.125, .37]));
  if (C.cap) {
    const hat = mesh(new THREE.SphereGeometry(.43, 32, 14, 0, Math.PI * 2, 0, Math.PI * .45), mat(C.cap, { r: .7 })); hat.position.set(0, .05, 0); hat.rotation.x = -.15; head.add(hat);
    const visor = mesh(new THREE.CylinderGeometry(.3, .3, .03, 24, 1, false, -Math.PI / 2, Math.PI), mat(C.cap, { r: .7 }), [0, .17, .3]); visor.rotation.x = .25; head.add(visor);
  }
  if (C.glasses) for (const s of [-1, 1]) { const r = mesh(new THREE.TorusGeometry(.1, .014, 8, 20), mat(0x222222), [s * .145, .03, .385], false); head.add(r); }
  g.userData = { rig, legs, arms, head, eyes, mouth, torso, blinkOff: o.blinkOff ?? 0 };
  return g;
}
// pose: {walk, talk, armL, armR, armLz, armRz, look, nod, t, lean}
export function pose(ch, p) {
  const u = ch.userData, t = p.t ?? 0;
  const w = p.walk ?? 0, ws = p.walkSpeed ?? 9;
  const sw = Math.sin(t * ws) * .55 * w;
  u.legs[0].rotation.x = sw; u.legs[1].rotation.x = -sw;
  u.rig.position.y = Math.abs(Math.cos(t * ws)) * .05 * w + Math.sin(t * 2.1 + u.blinkOff) * .008;
  const breathe = Math.sin(t * 2 + u.blinkOff) * .03;
  u.arms[0].rotation.x = (p.armR ?? -sw * .8) + breathe; u.arms[1].rotation.x = (p.armL ?? sw * .8) - breathe;
  u.arms[0].rotation.z = -(p.armRz ?? .12); u.arms[1].rotation.z = (p.armLz ?? .12);
  u.torso.rotation.x = p.lean ?? 0;
  u.head.rotation.y = p.look ?? 0; u.head.rotation.x = (p.nod ?? 0) + Math.sin(t * 1.3 + u.blinkOff) * .02;
  u.head.rotation.z = p.tilt ?? 0;
  const talk = p.talk ?? 0;
  u.mouth.scale.y = .22 + talk * .9; u.mouth.scale.x = 1 - talk * .15;
  const bt = (t + u.blinkOff) % 3.4; const blink = bt < .12 ? Math.sin(bt / .12 * Math.PI) : 0;
  u.eyes.forEach(e => { e.scale.y = 1 - blink * .9; e.userData.brow.position.y = .15 + (p.brow ?? 0) * .04; });
}
// guiar personaje mirando hacia un punto
export function face(ch, x, z) { ch.rotation.y = Math.atan2(x - ch.position.x, z - ch.position.z); }

export function broom() {
  const g = new THREE.Group();
  g.add(mesh(new THREE.CylinderGeometry(.03, .03, 1.5, 8), mat(0xC69C6D), [0, .75, 0]));
  g.add(mesh(new THREE.ConeGeometry(.2, .4, 12), mat(0xE2C46A, { r: 1 }), [0, -.05, 0]));
  return g;
}

// proyección a pantalla para etiquetas HTML
export function toScreen(camera, p, W = 1080, H = 1920) {
  const v = p.clone().project(camera); return { x: (v.x + 1) / 2 * W, y: (1 - v.y) / 2 * H, vis: v.z < 1 };
}
// cámara por tomas: lista de {t, pos:[..], look:[..], fov}
export function shot(camera, keys, u) {
  let i = 0; while (i < keys.length - 1 && u > keys[i + 1].t) i++;
  const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)];
  const k = a === b ? 0 : ease((u - a.t) / (b.t - a.t));
  camera.position.set(lerp(a.pos[0], b.pos[0], k), lerp(a.pos[1], b.pos[1], k), lerp(a.pos[2], b.pos[2], k));
  camera.lookAt(lerp(a.look[0], b.look[0], k), lerp(a.look[1], b.look[1], k), lerp(a.look[2], b.look[2], k));
  const f = lerp(a.fov ?? 38, b.fov ?? 38, k) * (window.FOV_MULT ?? 1.5); if (camera.fov !== f) { camera.fov = f; camera.updateProjectionMatrix(); }
}
