// CRÍA CERDOS EN PLENO BARRIO (9:16): el chiquero de don Tino y la cuadra.
// Los tiempos salen de las voces reales (timeline.js), así imagen y sonido no se separan.
(function () {
  const node = typeof require !== 'undefined';
  const U = node ? require('./engine/util') : globalThis.U;
  const MU = node ? require('./engine/music') : globalThis.MUSIC;
  const TLD = node ? require('./timeline.js') : globalThis.TLD;
  const FPS = 30, FORMAT = '9:16';
  const [W, H] = U.formatSize(FORMAT);
  const SAFE = U.safeArea(W, H);
  const clock = MU.makeClock({ bpm: 100, offset: 0 });
  const DURATION = TLD.duration;
  const L = TLD.lines;
  const at = (scene, k = 0) => L.filter((l) => l.scene === scene)[k];
  const wt = (line, word) => { const n = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-zñ0-9]/g, ''); const w = line.words.find((x) => n(x.w).startsWith(n(word))); return w ? w.t : line.t; };
  const ev = {
    hook: 0, problemas: at('problemas').t - 0.2, pleito: at('pleito').t - 0.2, tino: at('pleito', 1).t, tension: at('tension').t - 0.2, saber: at('saber').t - 0.2,
    mito: at('mito').t - 0.2, pasos: at('pasos').t - 0.2, p2: at('pasos', 1).t, p3: at('pasos', 2).t, final: at('final').t - 0.2, cierre: at('cierre').t - 0.2,
  };
  const SCORE = { FPS, FORMAT, W, H, SAFE, DURATION, clock, T: clock.T, BEAT: clock.BEAT, L, at, wt, ev, markers: {} };
  if (node) module.exports = SCORE; else globalThis.SCORE = SCORE;
})();
