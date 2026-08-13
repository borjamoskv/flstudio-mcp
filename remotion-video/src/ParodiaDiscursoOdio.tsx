import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Img,
  staticFile,
  AbsoluteFill,
  Series,
  Easing,
} from 'remotion';

// Import updated UCVH v2.0 JSON dataset
import estructuraUcvh from '../public/ucvh_odio.json';

interface EscenaUCVH {
  id: number;
  bloque: string;
  durationInSeconds: number;
  durationInFrames: number;
  audioTexto: string;
  subtitulo: string;
  warning: string;
  chartData: {
    title: string;
    stat: string;
  };
  geminiPrompt: string;
  clipVideo: string;
  keyframeFallback: string;
}

// Moderation Warning Box (Upper Right)
const ModerationWarningBox: React.FC<{ warningText: string }> = ({ warningText }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 275, 290], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const translateX = interpolate(frame, [0, 20], [30, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });

  const pulseScale = 1 + 0.015 * Math.sin(frame * 0.12);

  return (
    <div
      style={{
        position: 'absolute',
        top: 80,
        right: 60,
        width: 450,
        backgroundColor: 'rgba(24, 24, 27, 0.94)',
        border: '1.5px solid #D97706',
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
          color: '#F59E0B',
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
          color: '#D4D4D8',
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

// Holographic Data Chart Box (Upper Left)
const HolographicChartBox: React.FC<{ title: string; stat: string }> = ({
  title,
  stat,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [15, 30, 260, 280], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const barWidth = interpolate(frame, [30, 80], [0, 100], {
    easing: Easing.out(Easing.quad),
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 60,
        width: 420,
        backgroundColor: 'rgba(9, 9, 11, 0.9)',
        border: '1px solid rgba(0, 206, 209, 0.5)',
        padding: '20px 24px',
        borderRadius: 14,
        boxShadow: '0 0 30px rgba(0, 206, 209, 0.2)',
        backdropFilter: 'blur(12px)',
        opacity,
        zIndex: 45,
      }}
    >
      <div
        style={{
          color: '#00CED1',
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: 2,
          fontFamily: "'Inter', sans-serif",
          textTransform: 'uppercase',
          marginBottom: 8,
        }}
      >
        📊 ESTADÍSTICA DE TRINCHERA REPTILIANA
      </div>
      <div
        style={{
          color: '#FFFFFF',
          fontSize: 16,
          fontWeight: 600,
          fontFamily: "'Inter', sans-serif",
          marginBottom: 12,
        }}
      >
        {title}
      </div>

      {/* Progress Bar */}
      <div
        style={{
          width: '100%',
          height: 10,
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          borderRadius: 5,
          overflow: 'hidden',
          marginBottom: 10,
        }}
      >
        <div
          style={{
            width: `${barWidth}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #00CED1, #E01882)',
            borderRadius: 5,
          }}
        />
      </div>

      <div
        style={{
          color: '#FFB347',
          fontSize: 22,
          fontWeight: 800,
          fontFamily: "'Inter', sans-serif",
        }}
      >
        {stat}
      </div>
    </div>
  );
};

// Podcast Style Subtitle Banner (Bottom Center — NO MUSIC / RAW PODCAST)
const SubtituloFalsoPodcast: React.FC<{ subtitulo: string; bloque: string }> = ({
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
      {/* Top Left Badge: Fake Podcast LIVE Streaming Status */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 60,
          backgroundColor: 'rgba(9, 9, 11, 0.92)',
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
          gap: 12,
          backdropFilter: 'blur(8px)',
        }}
      >
        <span style={{ color: '#EF4444', animation: 'pulse 1s infinite' }}>🔴 EN DIRECTO</span>
        <span style={{ color: '#71717A', fontWeight: 400 }}>|</span>
        <span style={{ color: '#22C55E' }}>🐊 UCVH FALSO PODCAST</span>
        <span style={{ color: '#71717A', fontWeight: 400 }}>|</span>
        <span style={{ fontSize: 13, color: '#A1A1AA', fontWeight: 500 }}>
          {bloque}
        </span>
      </div>

      {/* Bottom Subtitle Banner: Dry Monologue Style */}
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
            backgroundColor: 'rgba(9, 9, 11, 0.96)',
            color: '#F4F4F5',
            fontFamily: "Georgia, 'Times New Roman', serif",
            fontSize: 28,
            fontWeight: 400,
            textAlign: 'center',
            padding: '22px 42px',
            borderRadius: 10,
            maxWidth: 1300,
            border: '1px solid rgba(63, 63, 70, 0.7)',
            boxShadow: '0 15px 35px rgba(0,0,0,0.9)',
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
      {/* ⚠️ FALSO PODCAST: ZERO MUSIC LAYER (NO BACKGROUND MUSIC) */}

      {/* Series Loop for the 120 Scenes */}
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
                    opacity: 0.95,
                  }}
                />

                {/* Holographic Chart Data Overlay */}
                {escena.chartData && (
                  <HolographicChartBox
                    title={escena.chartData.title}
                    stat={escena.chartData.stat}
                  />
                )}

                {/* Moderation Warning Card Overlay */}
                <ModerationWarningBox warningText={escena.warning} />

                {/* Subtitles & Fake Podcast LIVE Branding */}
                <SubtituloFalsoPodcast
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
