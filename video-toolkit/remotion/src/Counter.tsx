import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { Starburst } from "@remotion/starburst";
import "./fonts";

// Número que sube con fuerza (estadísticas, suscriptores, ventas...)
type Props = { to: number; prefix: string; suffix: string; label: string; accent: string };

export const Counter: React.FC<Props> = ({ to, prefix, suffix, label, accent }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = interpolate(frame, [10, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.exp) });
  const value = Math.round(to * t).toLocaleString("es-ES");
  const punch = spring({ frame: frame - 70, fps, config: { damping: 8, stiffness: 180 } });
  const size = Math.min(width, height) * 0.24;
  return (
    <AbsoluteFill style={{ background: "#0b0b12", alignItems: "center", justifyContent: "center" }}>
      <AbsoluteFill style={{ opacity: 0.18, transform: `rotate(${frame * 0.3}deg) scale(1.6)` }}>
        <Starburst rays={18} colors={[accent, "#0b0b12"]} />
      </AbsoluteFill>
      <div style={{ fontFamily: "Anton", fontSize: size, color: "white", transform: `scale(${1 + punch * 0.08 - (frame > 70 ? 0.08 * Math.min(1, (frame - 70) / 20) : 0)})`,
        textShadow: `0 0 ${40 * punch}px ${accent}` }}>
        {prefix}{value}{suffix}
      </div>
      <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: size * 0.18, color: accent, letterSpacing: 8, textTransform: "uppercase",
        opacity: interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{label}</div>
    </AbsoluteFill>
  );
};
