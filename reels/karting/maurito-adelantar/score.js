// MAURITO: CÓMO ADELANTAR (9:16, ~44s). A musical explainer: Maurito #2 teaches three steps to overtake
// in karting (rebufo, por dentro, frena recto) and one warning. The voiceover is pre-rendered (assets/voz.wav),
// its word times live in timing.js; every cut, stamp and hit below is read by BOTH song.js and film.js.
(function () {
  const node = typeof require !== 'undefined';
  const U = node ? require('./engine/util') : globalThis.U;
  const MU = node ? require('./engine/music') : globalThis.MUSIC;
  const TM = node ? require('./timing') : globalThis.TIMING;
  const { m, makeClock, makeChords } = MU;

  const FPS = 30;
  const FORMAT = '9:16';
  const STYLE = 'paper';
  const [W, H] = U.formatSize(FORMAT);
  const SAFE = U.safeArea(W, H);
  const clock = makeClock({ bpm: 120, offset: 0.3 });
  const { T, BEAT } = clock;
  const DURATION = 44.4;

  const SC = TM.scenes; // 7 spoken lines
  const word = (k, p, n = 0) => { const ws = SC[k].words.filter((w) => w.w.toLowerCase().replace(/[¡!¿?,.:]/g, '').startsWith(p)); return ws[n] ? ws[n].s : null; };

  // the sections follow the voice (each starts a hair before its line)
  const cut = (k) => SC[k].start - 0.25;
  const S = {
    intro: [0, cut(1)], paso1: [cut(1), cut(2)], paso2: [cut(2), cut(3)], paso3: [cut(3), cut(4)],
    ojo: [cut(4), cut(5)], resumen: [cut(5), cut(6)], outro: [cut(6), DURATION],
  };
  // every visual hit (a stamp, a badge, a crash) with a sound on the same instant
  const ev = {
    land: 1.15,                         // Maurito lands next to his kart
    name: word(0, 'soy') - 0.05,        // "MAURITO #2" stamp
    ask: word(0, 'adelantar') - 0.05,   // "¿ADELANTAR?" burst
    p1: cut(1) + 0.05, p2: cut(2) + 0.05, p3: cut(3) + 0.05,
    rebufo: word(1, 'rebufo') - 0.05, vel: word(1, 'velocidad') - 0.05, aire: word(1, 'rompe') - 0.05,
    dentro: word(2, 'dentro') - 0.05,
    frena: word(3, 'frena') - 0.05, vertice: word(3, 'vértice') - 0.05,
    ojo: cut(4) + 0.05, metas: word(4, 'metas') - 0.05, choque: word(4, 'choques') - 0.35,
    r1: word(5, 'rebufo') - 0.05, r2: word(5, 'dentro') - 0.05, r3: word(5, 'frena') - 0.05, todos: word(5, 'práctica') - 0.05,
    meta: cut(6) + 0.05,
  };
  ev.pass = ev.vertice + 1.6; // Maurito takes P1 just after the apex
  const cuts = [ev.p1, ev.p2, ev.p3, ev.ojo, cut(5), ev.meta];

  const { chords, chordAt } = makeChords(clock, {
    C: { notes: ['C4', 'E4', 'G4'], bass: 'C2' }, G: { notes: ['B3', 'D4', 'G4'], bass: 'G1' },
    Am: { notes: ['C4', 'E4', 'A4'], bass: 'A1' }, F: { notes: ['C4', 'F4', 'A4'], bass: 'F1' },
  }, Array.from({ length: 24 }, (_, b) => [b, 0, 4, ['C', 'G', 'Am', 'F'][b % 4]]));

  const markers = {
    land: { t: ev.land, sync: 'av' }, name: { t: ev.name, sync: 'av' }, ask: { t: ev.ask, sync: 'av' },
    p1: { t: ev.p1, sync: 'av' }, p2: { t: ev.p2, sync: 'av' }, p3: { t: ev.p3, sync: 'av' },
    choque: { t: ev.choque, sync: 'av' }, meta: { t: ev.meta, sync: 'av' },
    rebufo: ev.rebufo, dentro: ev.dentro, vertice: ev.vertice, ojo: ev.ojo, resumen: cut(5),
  };

  const SCORE = { FPS, FORMAT, STYLE, W, H, SAFE, DURATION, clock, T, BEAT, S, m, chords, chordAt, ev, cuts, markers, TM };
  if (node) module.exports = SCORE; else globalThis.SCORE = SCORE;
})();
