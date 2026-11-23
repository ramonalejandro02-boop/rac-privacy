// LA PARTITURA — única fuente de verdad para la música, la voz y la imagen.
// Voz: la voz clonada del usuario (../espera2/voz.wav). Los tiempos de cada frase vienen de voz_segs.json.
(function () {
  const node = typeof require !== 'undefined';
  const U = node ? require('./engine/util') : globalThis.U;
  const MU = node ? require('./engine/music') : globalThis.MUSIC;
  const { m, makeClock, makeChords } = MU;

  const FPS = 30;
  const FORMAT = U.pickFormat('9:16');
  const [W, H] = U.formatSize(FORMAT);
  const SAFE = U.safeArea(W, H);
  const WIDE = W / H > 1.2;
  const STYLE = 'watercolor';
  const clock = makeClock({ bpm: 72, offset: 0 }); // tierno y lento: 1 compás = 3.33 s
  const { T, BEAT } = clock;
  const DURATION = 37.6;

  // [inicio escena, fin escena, inicio habla, fin habla] de cada frase
  const SEG = [[0.0, 6.13, 0.15, 5.43], [6.13, 10.70, 6.43, 10.0], [10.70, 14.90, 11.0, 14.2], [14.90, 20.41, 15.2, 19.71], [20.41, 29.72, 20.71, 29.02], [29.72, 37.6, 30.02, 35.31]];
  const LINES = [
    'Si estás esperando algo de Dios, y sientes que se está tardando, mira esto.',
    'A veces oras, y oras, y parece que nada cambia.',
    'Pero el silencio de Dios no significa que se olvidó de ti.',
    'Mientras tú esperas, Él está acomodando cosas que todavía no puedes ver.',
    'Isaías 40:31: Los que esperan a Jehová tendrán nuevas fuerzas. Levantarán alas como las águilas.',
    'No te rindas. Lo que Dios empezó en ti, lo va a terminar. Si lo crees, escribe: amén.',
  ];
  const KEY = /^(Dios|olvidó|ver|nuevas|fuerzas|águilas|rindas|terminar|amén)/i;

  // palabras con tiempos estimados (por longitud, con pausa en la puntuación) -> subtítulos en frases cortas
  const subtitles = [];
  LINES.forEach((line, i) => {
    const [, , s0, s1] = SEG[i];
    const toks = line.split(' ');
    const wts = toks.map((w) => w.length + 2 + (/[,.:]$/.test(w) ? 5 : 0));
    const tot = wts.reduce((a, b) => a + b, 0);
    let acc = 0;
    const words = toks.map((w, k) => { const t = s0 + (s1 - s0) * acc / tot; acc += wts[k]; return { w, t, end: s0 + (s1 - s0) * acc / tot, key: KEY.test(w) }; });
    let cur = [];
    words.forEach((w, k) => {
      cur.push(w);
      const len = cur.map((x) => x.w).join(' ').length;
      if (/[,.:]$/.test(w.w) || len > 26 || k === words.length - 1) { subtitles.push({ t: cur[0].t, end: cur[cur.length - 1].end + 0.25, text: cur.map((x) => x.w).join(' '), words: cur }); cur = []; }
    });
  });

  const S = { s1: [SEG[0][0], SEG[0][1]], s2: [SEG[1][0], SEG[1][1]], s3: [SEG[2][0], SEG[2][1]], s4: [SEG[3][0], SEG[3][1]], s5: [SEG[4][0], SEG[4][1]], s6: [SEG[5][0], DURATION] };

  // armonía suave: Am – F – C – G (y un final en C)
  const { chords, chordAt } = makeChords(clock, {
    Am: { notes: ['A3', 'C4', 'E4'], bass: 'A1' }, F: { notes: ['A3', 'C4', 'F4'], bass: 'F1' },
    C: { notes: ['G3', 'C4', 'E4'], bass: 'C2' }, G: { notes: ['G3', 'B3', 'D4'], bass: 'G1' }, Cmaj9: { notes: ['E4', 'G4', 'B4', 'D5'], bass: 'C2' },
  }, [[0, 0, 4, 'Am'], [1, 0, 4, 'F'], [2, 0, 4, 'C'], [3, 0, 4, 'G'], [4, 0, 4, 'Am'], [5, 0, 4, 'F'], [6, 0, 4, 'C'], [7, 0, 4, 'G'], [8, 0, 4, 'F'], [9, 0, 4, 'G'], [10, 0, 4, 'Cmaj9'], [11, 0, 4, 'Cmaj9']]);

  const ev = { jesus: SEG[3][0] + 0.2, shoulder: SEG[3][0] + 2.6, rise: SEG[4][0] + 0.6, dove: SEG[5][0] + 2.0, end: DURATION };
  const markers = { s1: S.s1[0], s2: S.s2[0], s3: S.s3[0], jesus: ev.jesus, shoulder: ev.shoulder, verse: S.s5[0], final: S.s6[0], dove: ev.dove };

  const SCORE = { FPS, FORMAT, W, H, SAFE, WIDE, STYLE, DURATION, clock, T, BEAT, S, SEG, m, chords, chordAt, ev, markers, subtitles };
  if (node) module.exports = SCORE; else globalThis.SCORE = SCORE;
})();
