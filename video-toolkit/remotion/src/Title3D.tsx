import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { Text, MeshDistortMaterial, Environment, Lightformer } from "@react-three/drei";
import { EffectComposer, Bloom, ChromaticAberration, Vignette, Noise } from "@react-three/postprocessing";
import { Vector2 } from "three";

// Título 3D con bloom, aberración cromática y grano (estilo tráiler).
type Props = { title: string; subtitle: string; accent: string };

const Scene: React.FC<Props> = ({ title, subtitle, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inn = spring({ frame, fps, config: { damping: 20, mass: 1.4 } });
  const z = interpolate(inn, [0, 1], [-12, 0]);
  const rot = interpolate(frame, [0, 150], [0.35, -0.08]);
  return (
    <>
      <color attach="background" args={["#030308"]} />
      <ambientLight intensity={0.3} />
      <pointLight position={[4, 3, 5]} intensity={60} color={accent} />
      <pointLight position={[-5, -2, 4]} intensity={40} color="#4cc9f0" />
      <Environment resolution={64}>
        <Lightformer intensity={3} position={[0, 2, 5]} scale={[10, 2, 1]} />
      </Environment>
      <group position={[0, 0.2, z]} rotation={[0, rot, 0]}>
        <Text font={staticFile("fonts/Anton-400.ttf")} fontSize={Math.min(1.5, 11 / Math.max(1, title.length))} letterSpacing={0.02} anchorX="center" anchorY="middle">
          {title}
          <meshStandardMaterial color="white" emissive={accent} emissiveIntensity={0.6 * inn} metalness={0.6} roughness={0.25} />
        </Text>
        <Text font={staticFile("fonts/Inter-600.ttf")} position={[0, -1.25, 0]} fontSize={0.32} letterSpacing={0.3} anchorX="center"
          fillOpacity={interpolate(frame, [30, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
          {subtitle.toUpperCase()}
          <meshBasicMaterial color="#cfd8e3" transparent />
        </Text>
      </group>

        <mesh position={[0, 0, -6]} scale={4 + inn}>
          <icosahedronGeometry args={[1, 12]} />
          <MeshDistortMaterial color={accent} distort={0.35} speed={0} time={frame / 30} wireframe opacity={0.25} transparent />
        </mesh>

      <EffectComposer>
        <Bloom intensity={1.4} luminanceThreshold={0.15} mipmapBlur />
        <ChromaticAberration offset={new Vector2(0.0015 * (1 - inn) + 0.0004, 0.0004)} radialModulation={false} modulationOffset={0} />
        <Noise opacity={0.06} />
        <Vignette darkness={0.7} offset={0.25} />
      </EffectComposer>
    </>
  );
};

export const Title3D: React.FC<Props> = (props) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, 6], fov: 45 }}>
        <Scene {...props} />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
