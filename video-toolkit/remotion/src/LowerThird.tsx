import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing, OffthreadVideo, staticFile } from "remotion";
import "./fonts";

// Rótulo de nombre (lower third) animado. Pon videoSrc para verlo sobre tu video.
type Props = { name: string; role: string; accent: string; videoSrc: string };

export const LowerThird: React.FC<Props> = ({ name, role, accent, videoSrc }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width } = useVideoConfig();
  const inn = spring({ frame, fps, config: { damping: 200 } });
  const out = spring({ frame: frame - (durationInFrames - 20), fps, config: { damping: 200 } });
  const p = inn - out;
  const bar = interpolate(p, [0, 1], [0, 1], { easing: Easing.bezier(0.83, 0, 0.17, 1) });
  const textIn = spring({ frame: frame - 8, fps, config: { damping: 18 } }) - out;
  const s = width / 1920;
  return (
    <AbsoluteFill style={{ background: videoSrc ? "black" : "#2b2d42" }}>
      {videoSrc ? <OffthreadVideo src={staticFile(videoSrc)} /> : null}
      <div style={{ position: "absolute", left: 120 * s, bottom: 160 * s }}>
        <div style={{ position: "absolute", left: -24 * s, top: 0, width: 10 * s, height: 170 * s * bar, background: accent }} />
        <div style={{ overflow: "hidden", background: "rgba(10,12,20,.82)", backdropFilter: "blur(8px)", padding: `${18 * s}px ${36 * s}px`,
          clipPath: `inset(0 ${100 - bar * 100}% 0 0)` }}>
          <div style={{ fontFamily: "Anton", fontSize: 84 * s, color: "white", lineHeight: 1.05, transform: `translateY(${(1 - textIn) * 60}px)`, opacity: textIn }}>{name}</div>
          <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 34 * s, color: accent, letterSpacing: 4 * s, textTransform: "uppercase",
            transform: `translateY(${(1 - textIn) * 40}px)`, opacity: textIn }}>{role}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
