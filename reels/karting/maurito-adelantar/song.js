// THE SONG: an upbeat EDM-pop bed at 120 BPM under Maurito's voiceover (assets/voz.wav, pre-rendered).
// Every pop, whoosh and crash comes from an event in score.js.   node song.js
const path = require('path');
const { SR, Bus, reverb } = require('./engine/audio/dsp');
const I = require('./engine/audio/instruments');
const MIX = require('./engine/audio/mix');
const Genre = require('./engine/audio/genres');
const sc = require('./score');
const { T, BEAT, DURATION, m, ev, clock, chordAt, S } = sc;

const N = Math.ceil(DURATION * SR);
const bus = () => new Bus(N);
const drums = bus(), bass = bus(), pad = bus(), keys = bus(), fx = bus(), verb = bus();
const bar = (t) => Math.max(0, Math.round((t - 0.3) / (BEAT * 4)));

// groove: light under the intro, full for the steps, a breakdown under ¡OJO!, full again for the recap
const { kicks: k1 } = Genre.play('afrobeats', { clock, from: 0, to: bar(S.intro[1]), chordAt, buses: { drums, bass, pad, keys }, gain: 0.55 });
const { kicks: k2 } = Genre.play('afrobeats', { clock, from: bar(S.intro[1]), to: bar(S.ojo[0]), chordAt, buses: { drums, bass, pad, keys }, gain: 0.8 });
Genre.play('afrobeats', { clock, from: bar(S.ojo[0]), to: bar(S.resumen[0]), chordAt, buses: { drums, bass, pad, keys }, gain: 0.45, drums: false });
const { kicks: k3 } = Genre.play('afrobeats', { clock, from: bar(S.resumen[0]), to: Math.ceil((DURATION - 0.3) / (BEAT * 4)), chordAt, buses: { drums, bass, pad, keys }, gain: 0.9 });

// hits
fx.addMono(I.thud(70, 0.25), ev.land, 0.8); fx.addMono(I.boing(), ev.land + 0.02, 0.25);
for (const t of [ev.name, ev.rebufo, ev.vel, ev.dentro, ev.frena, ev.vertice, ev.metas, ev.r1, ev.r2, ev.r3, ev.todos]) fx.addMono(I.pop(1.1), t, 0.45);
fx.addMono(I.pop(0.8), ev.ask, 0.5); drums.addMono(I.crash(2), ev.ask, 0.25);
for (const t of sc.cuts) { fx.addMono(I.noiseSweep(0.35, 600, 5000, { q: 1, pink: true, shape: (x) => Math.sin(Math.PI * x) }), t - 0.3, 0.22); fx.addMono(I.thud(90, 0.12), t, 0.5); }
// air in the slipstream
fx.addMono(I.noiseSweep(1.6, 1500, 400, { q: 0.8, pink: true, shape: (x) => Math.sin(Math.PI * x) }), ev.aire, 0.12);
// the pass: a rising whoosh and a chime
fx.addMono(I.noiseSweep(0.8, 300, 4000, { q: 1.2, pink: true, shape: (x) => x }), ev.pass - 0.8, 0.18);
for (const n of [m('C6'), m('E6'), m('G6')]) fx.addMono(I.bell(440 * Math.pow(2, (n - 69) / 12), 0.8), ev.pass + (n - m('C6')) * 0.03, 0.12);
// ¡OJO!: an alarm blip, then the crash
fx.addMono(I.bwomp(), ev.ojo, 0.3);
fx.addMono(I.thwack(), ev.choque, 0.9); fx.addMono(I.subBoom(0.9, 80, 35), ev.choque, 0.5); fx.addMono(I.glass(3), ev.choque + 0.02, 0.3);
// checks in the recap
for (const t of [ev.r1, ev.r2, ev.r3]) fx.addMono(I.bell(1320, 0.4), t + 0.15, 0.12);
// finish: crash + whistle + claps
drums.addMono(I.crash(4), ev.meta, 0.5); fx.addMono(I.whistle(0.6), ev.meta + 0.1, 0.2);
for (let i = 0; i < 6; i++) drums.addMono(I.clap({ spread: 1.4 }), ev.meta + 0.5 + i * BEAT, 0.35);
verb.addMono(fx.L ? fx.L : new Float32Array(N), 0, 0.0);

// the voiceover
const voice = MIX.loadAudio(path.join(__dirname, 'assets', 'voz.wav'), { at: 0, gain: 1, length: DURATION });

const room = reverb(verb, { room: 0.5, damp: 0.4 });
const music = [drums, bass, pad, keys];
MIX.sidechain([bass, pad], [...k1, ...k2, ...k3], { depth: 0.35 });
MIX.duck(music, voice, { depth: 0.5 });
const stems = { drums, bass, pad, keys, fx, voice, verb: room };
const GAIN = { drums: 0.8, bass: 0.6, pad: 0.6, keys: 0.6, fx: 1, voice: 1.6, verb: 0.3 };
const mix = MIX.mixdown(stems, GAIN, { stemDir: process.env.STEMS ? path.join(__dirname, 'out') : null });
MIX.highpass(mix, 28);
MIX.fadeOut(mix, DURATION - 0.8, DURATION);
const res = MIX.master(mix, 0.8, undefined, { lufs: process.env.LUFS ? +process.env.LUFS : -14 });
MIX.writeWav(path.join(__dirname, 'out', 'music.wav'), mix);
console.log(`out/music.wav  ${DURATION.toFixed(1)}s  ${res.lufs.toFixed(1)} LUFS`);
