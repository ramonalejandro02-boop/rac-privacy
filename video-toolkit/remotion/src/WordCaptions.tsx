import { AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, delayRender, continueRender } from "remotion";
import { useEffect, useState } from "react";
import "./fonts";
const fontFamily = "Montserrat";

// captions.json: [{ "text": "hola", "startMs": 0, "endMs": 400 }, ...]  (lo genera scripts/subtitles.py)
type Word = { text: string; startMs: number; endMs: number };
type Props = { videoSrc: string; captionsFile: string; highlight: string };

export const WordCaptions: React.FC<Props> = ({ videoSrc, captionsFile, highlight }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [words, setWords] = useState<Word[]>([]);
  const [handle] = useState(() => delayRender("captions"));
  useEffect(() => {
    fetch(staticFile(captionsFile)).then((r) => r.json()).then((w) => { setWords(w); continueRender(handle); })
      .catch(() => continueRender(handle));
  }, [captionsFile, handle]);

  const ms = (frame / fps) * 1000;
  const idx = words.findIndex((w) => ms >= w.startMs && ms < w.endMs);
  const page = idx < 0 ? [] : words.slice(Math.floor(idx / 3) * 3, Math.floor(idx / 3) * 3 + 3);

  return (
    <AbsoluteFill style={{ background: "black" }}>
      {videoSrc ? <OffthreadVideo src={staticFile(videoSrc)} /> : null}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: "22%" }}>
        <div style={{ fontFamily, fontWeight: 900, fontSize: 92, textAlign: "center", textTransform: "uppercase", padding: "0 60px" }}>
          {page.map((w) => {
            const active = ms >= w.startMs && ms < w.endMs;
            const pop = spring({ frame: frame - Math.round((w.startMs / 1000) * fps), fps, config: { damping: 10 } });
            return (
              <span key={w.startMs} style={{ display: "inline-block", margin: "0 14px", color: active ? highlight : "white",
                transform: `scale(${active ? 1 + 0.15 * pop : 1})`, WebkitTextStroke: "6px black", paintOrder: "stroke",
                textShadow: "0 8px 24px rgba(0,0,0,.6)" }}>{w.text}</span>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
