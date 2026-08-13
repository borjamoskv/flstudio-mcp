import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
  Audio,
  Img,
  staticFile,
  Easing,
  AbsoluteFill,
  Series,
} from 'remotion';

// Import narrative metadata JSON
import narrativeData from '../public/narrative_20min.json';

interface SceneData {
  id: number;
  loopIndex: number;
  act: string;
  description: string;
  startSeconds: number;
  durationSeconds: number;
  durationFrames: number;
  colorToken: string;
  colorHex: string;
  keyframeImage: string;
  audioTrack: string;
  typography: {
    title: string;
    subtitle: string;
    font: string;
  };
}

const SceneTitle: React.FC<{ title: string; subtitle: string; color: string }> = ({
  title,
  subtitle,
  color,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 45, 60], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const translateY = interpolate(frame, [0, 20], [20, 0], {
    easing: Easing.out(Easing.quad),
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 70,
        left: 70,
        fontFamily: "'Inter', sans-serif",
        color: '#FFFFFF',
        opacity,
        transform: `translateY(${translateY}px)`,
        textShadow: '0 4px 20px rgba(0,0,0,0.8)',
      }}
    >
      <div
        style={{
          fontSize: 24,
          fontWeight: 700,
          letterSpacing: 6,
          textTransform: 'uppercase',
          color,
          marginBottom: 8,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 14,
          fontWeight: 400,
          letterSpacing: 2,
          color: 'rgba(255, 255, 255, 0.7)',
        }}
      >
        {subtitle}
      </div>
    </div>
  );
};

export const CyberEpistemology20Min: React.FC = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: '#0A0A0F' }}>
      {/* Master Audio Track (loops continuously) */}
      <Audio src={staticFile('Satin_Maceo_AIR_Flow_Master.wav')} loop />

      {/* Film Grain & Vignette Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 50,
          background:
            'radial-gradient(circle at center, transparent 40%, rgba(10, 10, 15, 0.75) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Data-Driven Series Composition (74 Scenes = 20 Minutes) */}
      <Series>
        {narrativeData.scenes.map((scene: SceneData) => {
          const durationFrames = Math.round(scene.durationSeconds * fps);

          return (
            <Series.Sequence key={scene.id} durationInFrames={durationFrames}>
              <AbsoluteFill style={{ backgroundColor: '#0A0A0F' }}>
                {/* Background Keyframe Image */}
                <Img
                  src={staticFile(scene.keyframeImage)}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />

                {/* Typography Overlay */}
                <SceneTitle
                  title={scene.typography.title}
                  subtitle={scene.typography.subtitle}
                  color={scene.colorHex}
                />
              </AbsoluteFill>
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
