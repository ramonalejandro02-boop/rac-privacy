import { Composition } from "remotion";
import { KineticTitle } from "./KineticTitle";
import { WordCaptions } from "./WordCaptions";

export const Root: React.FC = () => (
  <>
    {/* Título animado: 16:9 */}
    <Composition id="KineticTitle" component={KineticTitle} durationInFrames={120} fps={30} width={1920} height={1080}
      defaultProps={{ title: "TU TÍTULO AQUÍ", subtitle: "Motion graphics con Remotion", accent: "#ffb703" }} />
    {/* Título animado vertical: Reels / TikTok */}
    <Composition id="KineticTitleVertical" component={KineticTitle} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{ title: "TU TÍTULO AQUÍ", subtitle: "Formato vertical", accent: "#ffb703" }} />
    {/* Subtítulos palabra por palabra sobre un video (public/video.mp4) */}
    <Composition id="WordCaptions" component={WordCaptions} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ videoSrc: "", captionsFile: "captions.json", highlight: "#ffd60a" }} />
  </>
);
