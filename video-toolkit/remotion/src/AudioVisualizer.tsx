import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, Img } from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import "./fonts";

// Visualizador de audio (podcast, música): barras circulares que reaccionan al sonido.
type Props = { audioSrc: string; title: string; coverSrc: string; accent: string };

const bars = 96;

const WithAudio: React.FC<Props> = (p) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const data = useAudioData(staticFile(p.audioSrc));
  const vals = data ? visualizeAudio({ fps, frame, audioData: data, numberOfSamples: 128, optimizeFor: "speed" }).slice(0, bars) : new Array(bars).fill(0);
  return <View {...p} vals={vals} />;
};

// Sin audio: datos simulados para previsualizar el diseño
const Demo: React.FC<Props> = (p) => {
  const frame = useCurrentFrame();
  const vals = Array.from({ length: bars }, (_, i) => Math.max(0, 0.12 + 0.12 * Math.sin(frame / 4 + i / 5) * Math.cos(frame / 9 - i / 11) + (i < 8 ? 0.15 * Math.abs(Math.sin(frame / 7.5 * Math.PI)) : 0)));
  return <View {...p} vals={vals} />;
};

export const AudioVisualizer: React.FC<Props> = (p) => (p.audioSrc ? <WithAudio {...p} /> : <Demo {...p} />);

const View: React.FC<Props & { vals: number[] }> = ({ audioSrc, title, coverSrc, accent, vals }) => {
  const { width, height } = useVideoConfig();
  const bass = vals.slice(0, 6).reduce((a, b) => a + b, 0) / 6;
  const R = Math.min(width, height) * 0.22;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle, #1a1030 0%, #050308 70%)`, alignItems: "center", justifyContent: "center" }}>
      {audioSrc ? <Audio src={staticFile(audioSrc)} /> : null}
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {vals.map((v, i) => {
          const a = (i / bars) * Math.PI * 2 - Math.PI / 2;
          const len = 10 + Math.min(1, v * 3) * R * 0.9;
          const cx = width / 2, cy = height / 2;
          return <line key={i} x1={cx + Math.cos(a) * (R + 10)} y1={cy + Math.sin(a) * (R + 10)} x2={cx + Math.cos(a) * (R + 10 + len)} y2={cy + Math.sin(a) * (R + 10 + len)}
            stroke={accent} strokeWidth={6} strokeLinecap="round" opacity={0.5 + v} />;
        })}
      </svg>
      <div style={{ width: R * 2, height: R * 2, borderRadius: "50%", overflow: "hidden", transform: `scale(${1 + bass * 0.25})`, boxShadow: `0 0 ${60 + bass * 200}px ${accent}`, background: "#222" }}>
        {coverSrc ? <Img src={staticFile(coverSrc)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      </div>
      <div style={{ position: "absolute", bottom: height * 0.1, fontFamily: "Anton", fontSize: R * 0.35, color: "white" }}>{title}</div>
    </AbsoluteFill>
  );
};
