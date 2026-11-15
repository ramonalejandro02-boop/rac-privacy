import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import "./fonts";
import { noise2D } from "@remotion/noise";

const fontFamily = "Anton";
const inter = "Inter";

type Props = { title: string; subtitle: string; accent: string };

export const KineticTitle: React.FC<Props> = ({ title, subtitle, accent }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const letters = title.split("");
  const size = Math.min(width, height) * 0.16;

  const barW = interpolate(frame, [20, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const outro = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const camX = noise2D("x", frame / 60, 0) * 8;
  const camY = noise2D("y", 0, frame / 60) * 8;

  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #1d2a44 0%, #05070d 75%)", alignItems: "center", justifyContent: "center", opacity: outro }}>
      <div style={{ transform: `translate(${camX}px, ${camY}px)`, textAlign: "center" }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", fontFamily, fontSize: size, color: "white", lineHeight: 1 }}>
          {letters.map((ch, i) => {
            const s = spring({ frame: frame - i * 2, fps, config: { damping: 12, stiffness: 120 } });
            return (
              <span key={i} style={{ display: "inline-block", whiteSpace: "pre",
                transform: `translateY(${(1 - s) * 120}px) rotate(${(1 - s) * 25}deg) scale(${0.6 + 0.4 * s})`,
                opacity: s, filter: `blur(${(1 - s) * 12}px)` }}>{ch}</span>
            );
          })}
        </div>
        <div style={{ height: 10, width: `${barW * 70}%`, margin: "28px auto", background: accent, borderRadius: 5 }} />
        <div style={{ fontFamily: inter, fontWeight: 600, fontSize: size * 0.28, color: "#cfd8e3", letterSpacing: 6, textTransform: "uppercase",
          opacity: interpolate(frame, [35, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          transform: `translateY(${interpolate(frame, [35, 55], [30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}px)` }}>
          {subtitle}
        </div>
      </div>
    </AbsoluteFill>
  );
};
