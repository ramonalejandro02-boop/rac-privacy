import { AbsoluteFill, Img, OffthreadVideo, staticFile, useCurrentFrame, interpolate } from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { fade } from "@remotion/transitions/fade";
import { LightLeak } from "@remotion/light-leaks";
import "./fonts";

// Montaje con transiciones + light leaks. clips: archivos en public/ (mp4, jpg, png).
type Props = { clips: string[]; clipSeconds: number; transition: "mix" | "slide" | "wipe" | "flip" | "clock" | "fade"; lightLeaks: boolean };

const Clip: React.FC<{ src: string; i: number }> = ({ src, i }) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 120], [1.08, 1.0]); // Ken Burns
  const style = { width: "100%", height: "100%", objectFit: "cover" as const, transform: `scale(${zoom})` };
  if (!src) {
    const hues = [12, 200, 280, 140, 40];
    return <AbsoluteFill style={{ background: `linear-gradient(135deg, hsl(${hues[i % 5]} 80% 55%), hsl(${hues[(i + 2) % 5]} 70% 25%))`, alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontFamily: "Anton", fontSize: 260, color: "white", transform: `scale(${zoom})` }}>{`CLIP ${i + 1}`}</div></AbsoluteFill>;
  }
  return /\.(mp4|mov|webm)$/i.test(src) ? <OffthreadVideo src={staticFile(src)} style={style} muted /> : <Img src={staticFile(src)} style={style} />;
};

const pick = (t: Props["transition"], i: number, w: number, h: number) => {
  const all = [slide({ direction: "from-right" }), wipe({ direction: "from-top-left" }), flip({ direction: "from-left" }), clockWipe({ width: w, height: h }), fade()];
  const map = { slide: 0, wipe: 1, flip: 2, clock: 3, fade: 4 } as const;
  return t === "mix" ? all[i % all.length] : all[map[t]];
};

export const TransitionsReel: React.FC<Props & { width?: number }> = ({ clips, clipSeconds, transition, lightLeaks }) => {
  const list = clips.length ? clips : ["", "", "", ""];
  const dur = Math.round(clipSeconds * 30);
  return (
    <AbsoluteFill style={{ background: "black" }}>
      <TransitionSeries>
        {list.flatMap((c, i) => {
          const items = [<TransitionSeries.Sequence key={`s${i}`} durationInFrames={dur}><Clip src={c} i={i} /></TransitionSeries.Sequence>];
          if (i < list.length - 1) {
            // Una transición o un light leak en cada corte (Remotion no permite ambos en el mismo corte)
            if (lightLeaks && i % 2 === 1) {
              items.push(<TransitionSeries.Overlay key={`o${i}`} durationInFrames={30}><LightLeak seed={i + 3} hueShift={i * 40} /></TransitionSeries.Overlay>);
            } else {
              items.push(<TransitionSeries.Transition key={`t${i}`} presentation={pick(transition, i, 1920, 1080) as never}
                timing={i % 4 === 2 ? springTiming({ config: { damping: 200 }, durationInFrames: 20 }) : linearTiming({ durationInFrames: 20 })} />);
            }
          }
          return items;
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
};

// Duración total: los cortos con transición se solapan 20 fotogramas; los light leaks no restan tiempo.
export const reelDuration = (n: number, sec: number, lightLeaks = true) => {
  const k = Math.max(1, n || 4);
  let cuts = 0;
  for (let i = 0; i < k - 1; i++) if (!(lightLeaks && i % 2 === 1)) cuts++;
  return k * Math.round(sec * 30) - cuts * 20;
};
