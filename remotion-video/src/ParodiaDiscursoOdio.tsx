import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Audio,
  Img,
  staticFile,
  AbsoluteFill,
  Series,
  Easing,
} from 'remotion';

// Import JSON structure for UCVH Hate Speech Satire
import estructuraUcvh from '../public/ucvh_odio.json';

interface EscenaUCVH {
  id: number;
  bloque: string;
  durationInSeconds: number;
  durationInFrames: number;
  audioTexto: string;
  subtitulo: string;
  warning: string;
  geminiPrompt: string;
  clipVideo: string;
  keyframeFallback: string;
}

const ModerationWarningBox: React.FC<{ warningText: string }> = ({ warningText }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 275, 290], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const translateX = interpolate(frame, [0, 20], [30, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });

  // Pulse effect
  const pulseScale = 1 + 0.02 * Math.sin(frame * 0.15);

  return (
    <div
      style={{
        position: 'absolute',
        top: 80,
        right: 60,
        width: 440,
        backgroundColor: 'rgba(24, 24, 27, 0.92)', // zinc-900
        border: '1.5px solid #D97706', // amber-600
        padding: '16px 22px',
        borderRadius: 12,
        boxShadow: '0 20px 40px rgba(0,0,0,0.7), 0 0 25px rgba(217, 119, 6, 0.2)',
        backdropFilter: 'blur(10px)',
        opacity,
        transform: `translateX(${translateX}px) scale(${pulseScale})`,
        zIndex: 40,
      }}
    >
      <div
        style={{
          color: '#F59E0B', // amber-500
          fontWeight: 700,
          fontSize: 13,
          letterSpacing: 1.5,
          fontFamily: "'Inter', sans-serif",
          textTransform: 'uppercase',
          marginBottom: 6,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span>⚠️</span> AVISO DE MODERACIÓN Y SESGO
      </div>
      <div
        style={{
          color: '#D4D4D8', // zinc-300
          fontSize: 13,
          fontFamily: "'Inter', sans-serif",
          lineHeight: 1.45,
          fontWeight: 400,
        }}
      >
        {warningText}
      </div>
    </div>
  );
};

const SubtituloUCVH: React.FC<{ subtitulo: string; bloque: string }> = ({
  subtitulo,
  bloque,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 280, 295], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const translateY = interpolate(frame, [0, 15], [15, 0], {
    easing: Easing.out(Easing.quad),
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Top Left Badge: Channel branding */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 50,
          backgroundColor: 'rgba(9, 9, 11, 0.85)',
          color: '#E4E4E7',
          padding: '10px 22px',
          borderRadius: 8,
          border: '1px solid rgba(161, 161, 170, 0.3)',
          fontFamily: "'Inter', sans-serif",
          fontSize: 15,
          fontWeight: 700,
          letterSpacing: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          backdropFilter: 'blur(8px)',
        }}
      >
        <span style={{ color: '#22C55E' }}>🐊 UCVH</span>
        <span style={{ color: '#71717A', fontWeight: 400 }}>|</span>
        <span style={{ fontSize: 13, color: '#A1A1AA', fontWeight: 500 }}>
          {bloque}
        </span>
      </div>

      {/* Bottom Subtitle Banner: Essay Editorial Style */}
      <div
        style={{
          position: 'absolute',
          bottom: 60,
          left: 80,
          right: 80,
          display: 'flex',
          justifyContent: 'center',
          opacity,
          transform: `translateY(${translateY}px)`,
          zIndex: 30,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(9, 9, 11, 0.94)', // zinc-950
            color: '#F4F4F5', // zinc-100
            fontFamily: "Georgia, 'Times New Roman', serif", // Video Essay Editorial Font
            fontSize: 28,
            fontWeight: 400,
            textAlign: 'center',
            padding: '22px 42px',
            borderRadius: 10,
            maxWidth: 1300,
            border: '1px solid rgba(63, 63, 70, 0.7)', // zinc-700
            boxShadow: '0 15px 35px rgba(0,0,0,0.85)',
            lineHeight: 1.4,
          }}
        >
          "{subtitulo}"
        </div>
      </div>
    </>
  );
};

export const ParodiaDiscursoOdio: React.FC = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: '#0D0D11' }}>
      {/* Background Audio Track */}
      <Audio src={staticFile('Satin_Maceo_AIR_Flow_Master.wav')} loop volume={0.25} />

      {/* Series loop for the 120 scenes */}
      <Series>
        {estructuraUcvh.scenes.map((escena: EscenaUCVH) => {
          return (
            <Series.Sequence
              key={escena.id}
              durationInFrames={escena.durationInFrames}
            >
              <AbsoluteFill style={{ backgroundColor: '#0D0D11' }}>
                {/* Visual Background Layer */}
                <Img
                  src={staticFile(escena.keyframeFallback)}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    opacity: 0.85,
                  }}
                />

                {/* Moderation Warning Card Overlay (Alternating scenes) */}
                <ModerationWarningBox warningText={escena.warning} />

                {/* Editorial Subtitle Banner & Branding */}
                <SubtituloUCVH
                  subtitulo={escena.subtitulo}
                  bloque={escena.bloque}
                />
              </AbsoluteFill>
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
