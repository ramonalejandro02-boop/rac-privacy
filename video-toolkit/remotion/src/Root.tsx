import { Composition } from "remotion";
import { KineticTitle } from "./KineticTitle";
import { WordCaptions } from "./WordCaptions";
import { LowerThird } from "./LowerThird";
import { Counter } from "./Counter";
import { Title3D } from "./Title3D";
import { TransitionsReel, reelDuration } from "./TransitionsReel";
import { AudioVisualizer } from "./AudioVisualizer";

export const Root: React.FC = () => (
  <>
    {/* Título animado letra por letra */}
    <Composition id="KineticTitle" component={KineticTitle} durationInFrames={120} fps={30} width={1920} height={1080}
      defaultProps={{ title: "TU TÍTULO AQUÍ", subtitle: "Motion graphics con Remotion", accent: "#ffb703" }} />
    <Composition id="KineticTitleVertical" component={KineticTitle} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{ title: "TU TÍTULO AQUÍ", subtitle: "Formato vertical", accent: "#ffb703" }} />

    {/* Título 3D cinematográfico con bloom y aberración cromática */}
    <Composition id="Title3D" component={Title3D} durationInFrames={150} fps={30} width={1920} height={1080}
      defaultProps={{ title: "PRÓXIMAMENTE", subtitle: "Una historia real", accent: "#ff3d00" }} />

    {/* Rótulo de nombre */}
    <Composition id="LowerThird" component={LowerThird} durationInFrames={150} fps={30} width={1920} height={1080}
      defaultProps={{ name: "Nombre Apellido", role: "Cargo / Organización", accent: "#00d4ff", videoSrc: "" }} />

    {/* Contador de estadísticas */}
    <Composition id="Counter" component={Counter} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{ to: 25000, prefix: "+", suffix: "", label: "Personas ayudadas", accent: "#ffd60a" }} />

    {/* Montaje con transiciones y light leaks */}
    <Composition id="TransitionsReel" component={TransitionsReel} fps={30} width={1920} height={1080}
      durationInFrames={reelDuration(4, 3)}
      calculateMetadata={({ props }) => ({ durationInFrames: reelDuration(props.clips.length, props.clipSeconds, props.lightLeaks) })}
      defaultProps={{ clips: [] as string[], clipSeconds: 3, transition: "mix" as const, lightLeaks: true }} />

    {/* Visualizador de audio */}
    <Composition id="AudioVisualizer" component={AudioVisualizer} durationInFrames={300} fps={30} width={1080} height={1080}
      defaultProps={{ audioSrc: "", title: "EPISODIO 1", coverSrc: "", accent: "#b5179e" }} />

    {/* Subtítulos palabra por palabra sobre un video */}
    <Composition id="WordCaptions" component={WordCaptions} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ videoSrc: "", captionsFile: "captions.json", highlight: "#ffd60a" }} />
  </>
);
