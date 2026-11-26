// LA MÚSICA — piano y pads suaves bajo la voz clonada del usuario (sin efectos ni golpes).
const path = require('path');
const { SR, Bus, reverb } = require('./engine/audio/dsp');
const I = require('./engine/audio/instruments');
const MIX = require('./engine/audio/mix');
const sc = require('./score');
const { DURATION, BEAT, m } = sc;

const N = Math.ceil(DURATION * SR);
const bus = () => new Bus(N);
const pad = bus(), keys = bus(), bass = bus(), verb = bus();

// pads cálidos que respiran
for (const c of sc.chords) {
  if (c.t0 >= DURATION) continue;
  const d = Math.min(c.t1, DURATION) - c.t0;
  for (const n of c.notes) { const { L, R } = I.padNote(n, d + 0.6, { cutoff: 1100, attack: 0.9, release: 1.6 }); pad.addStereo(L, R, c.t0, 0.08); }
  bass.addMono(I.bass(c.bass + 12, d * 0.95, { bright: 0.15, sub: 0.9 }), c.t0, 0.28);
}
// arpegio de piano/caja de música, muy suave (corcheas en tiempos 1 y 3, notas del acorde)
for (const c of sc.chords) {
  if (c.t0 >= DURATION - 1) continue;
  const ns = [...c.notes.map((n) => n + 12)];
  for (let b = 0; b < 4; b++) {
    const t = c.t0 + b * BEAT;
    if (t >= DURATION - 1.5) break;
    const note = ns[(b * 2 + 1) % ns.length];
    const k = I.musicBox(note);
    keys.addMono(k, t, 0.09, b % 2 ? 0.25 : -0.25); verb.addMono(k, t, 0.12);
  }
}
// la voz clonada
const voice = MIX.loadAudio(path.join(__dirname, '..', 'ansiedad', 'voz.wav'), { at: 0, gain: 1.0 });
MIX.duck([pad, keys, bass], voice, { depth: 0.45, attack: 0.08, release: 0.6 });

const stems = { pad, keys, bass, verb: reverb(verb, { room: 0.88, damp: 0.35 }), voice };
const GAIN = { pad: 2.2, keys: 1.0, bass: 0.6, verb: 1, voice: 1.0 };
const out = path.join(__dirname, 'out');
const mix = MIX.mixdown(stems, GAIN, { stemDir: process.env.STEMS ? out : null });
MIX.highpass(mix, 30);
MIX.fadeOut(mix, DURATION - 2.0, DURATION);
const M = MIX.master(mix, 0.8, undefined, { lufs: process.env.LUFS ? parseFloat(process.env.LUFS) : -14 });
MIX.writeWav(path.join(out, 'music.wav'), mix);
console.log(`wrote out/music.wav (${DURATION.toFixed(2)}s, ${M.lufs !== undefined ? M.lufs.toFixed(1) + ' LUFS' : ''})`);
