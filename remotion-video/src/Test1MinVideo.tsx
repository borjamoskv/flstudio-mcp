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
  spring,
} from 'remotion';

// Timecode Formatter Helper
const formatTimecode = (frame: number, fps: number) => {
  const totalSeconds = frame / fps;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const milliseconds = Math.floor((totalSeconds % 1) * 100);
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(2, '0')}`;
};

// Animated Audio Waveform Visualizer Component
const SpectrumVisualizer: React.FC<{ color: string; frame: number }> = ({ color, frame }) => {
  const bars = 24;
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', height: 60 }}>
      {Array.from({ length: bars }).map((_, i) => {
        const height = interpolate(
          Math.sin((frame * 0.15) + i * 0.4) + Math.cos((frame * 0.25) - i * 0.2),
          [-2, 2],
          [8, 55],
          { extrapolateRight: 'clamp' }
        );
        return (
          <div
            key={i}
            style={{
              width: 6,
              height: `${height}px`,
              backgroundColor: color,
              borderRadius: 3,
              boxShadow: `0 0 10px ${color}`,
              transition: 'height 0.05s ease',
            }}
          />
        );
      })}
    </div>
  );
};

// HUD Header and Footer Overlay
const StudioHUD: React.FC<{ activeAct: string; color: string }> = ({ activeAct, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const timecode = formatTimecode(frame, fps);

  // Calculate exergy bar value
  const exergyPercent = Math.floor(interpolate(frame, [0, 1800], [88, 99.8]));

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 100, padding: 48 }}>
      {/* Top Bar */}
      <div
        style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          fontFamily: "'JetBrains Mono', 'Courier New', monospace",
          color: 'rgba(255, 255, 255, 0.9)',
          fontSize: 14,
          letterSpacing: 2,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 12px #EF4444',
              animation: 'pulse 1s infinite',
            }}
          />
          <span style={{ fontWeight: 700, color: '#FFFFFF' }}>FL STUDIO MCP 2025</span>
          <span style={{ color: 'rgba(255,255,255,0.4)' }}>|</span>
          <span style={{ color }}>{activeAct}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <span>48.0 kHz / 24-BIT</span>
          <span style={{ color: 'rgba(255,255,255,0.4)' }}>|</span>
          <span style={{ color: '#F59E0B', fontWeight: 700 }}>EXERGY: {exergyPercent}%</span>
        </div>
      </div>

      {/* Bottom Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 48,
          left: 48,
          right: 48,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          fontFamily: "'JetBrains Mono', 'Courier New', monospace",
        }}
      >
        <SpectrumVisualizer color={color} frame={frame} />

        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 4,
              textShadow: `0 0 20px ${color}`,
            }}
          >
            {timecode} <span style={{ fontSize: 18, color: 'rgba(255,255,255,0.5)' }}>/ 01:00.00</span>
          </div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 4, letterSpacing: 2 }}>
            FPS: 30.00 | ENGINE: SATIN-MACEO-AIR C5-REAL
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene Card Overlay Component
const SceneCard: React.FC<{
  actNumber: string;
  title: string;
  subtitle: string;
  description: string;
  color: string;
}> = ({ actNumber, title, subtitle, description, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const opacity = interpolate(frame, [0, 15, 410, 440], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const translateY = interpolate(entrance, [0, 1], [40, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 140,
        left: 48,
        maxWidth: 720,
        backgroundColor: 'rgba(10, 10, 18, 0.75)',
        backdropFilter: 'blur(16px)',
        border: `1px solid ${color}44`,
        borderRadius: 16,
        padding: '32px 40px',
        color: '#FFFFFF',
        fontFamily: "'Inter', system-ui, sans-serif",
        opacity,
        transform: `translateY(${translateY}px)`,
        boxShadow: `0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px ${color}22`,
      }}
    >
      <div
        style={{
          display: 'inline-block',
          backgroundColor: `${color}22`,
          color: color,
          border: `1px solid ${color}66`,
          padding: '4px 14px',
          borderRadius: 20,
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: 3,
          textTransform: 'uppercase',
          marginBottom: 12,
        }}
      >
        {actNumber}
      </div>

      <div style={{ fontSize: 36, fontWeight: 900, letterSpacing: -0.5, lineHeight: 1.1, marginBottom: 8 }}>
        {title}
      </div>

      <div style={{ fontSize: 18, fontWeight: 500, color: color, marginBottom: 12, letterSpacing: 1 }}>
        {subtitle}
      </div>

      <div style={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.75)', lineHeight: 1.6 }}>
        {description}
      </div>
    </div>
  );
};

export const Test1MinVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Act Colors
  const colors = {
    act1: '#38BDF8', // Cyan (Satin Jackets)
    act2: '#E056FD', // Neon Purple/Magenta (Maceo Plex)
    act3: '#34D399', // Emerald Teal (AIR)
    act4: '#F59E0B', // Amber Gold (C5-REAL Synthesis)
  };

  // Determine current active act for HUD
  let currentActName = 'ACT I: NU-DISCO FLOW';
  let currentColor = colors.act1;

  if (frame >= 450 && frame < 900) {
    currentActName = 'ACT II: INDUSTRIAL DSP SUB-BASS';
    currentColor = colors.act2;
  } else if (frame >= 900 && frame < 1350) {
    currentActName = 'ACT III: ORGANIC AMBIENT TEXTURES';
    currentColor = colors.act3;
  } else if (frame >= 1350) {
    currentActName = 'ACT IV: C5-REAL SYNTHESIS';
    currentColor = colors.act4;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: '#050508' }}>
      {/* Master Audio Track (60 Seconds Continuous) */}
      <Audio src={staticFile('Satin_Maceo_AIR_Flow_Master.wav')} volume={0.9} />

      {/* Global Studio HUD */}
      <StudioHUD activeAct={currentActName} color={currentColor} />

      {/* Cinematic Vignette & Ambient Radial Lighting */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 40,
          background: `radial-gradient(circle at 50% 50%, transparent 45%, rgba(5, 5, 8, 0.85) 100%)`,
          pointerEvents: 'none',
        }}
      />

      {/* 4 Acts Series Sequence (15 Seconds Each = 450 Frames * 4 = 1800 Frames / 60s) */}
      <Series>
        {/* ACT 1: Satin Jackets Nu-Disco Warmth */}
        <Series.Sequence durationInFrames={450}>
          <AbsoluteFill>
            {/* Ken Burns Zoom */}
            <Img
              src={staticFile('shot1_keyframe.png')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: `scale(${interpolate(frame, [0, 450], [1.0, 1.12], { extrapolateRight: 'clamp' })})`,
                filter: 'brightness(0.9) contrast(1.15)',
              }}
            />
            <SceneCard
              actNumber="ACT I / IV (00:00 - 00:15)"
              title="Nu-Disco Melodic Elegance"
              subtitle="Satin Jackets Aesthetic Matched with CoreMIDI Engine"
              description="Lush 7th chord progressions, silk electric piano layers, and pristine spatial width in 48kHz."
              color={colors.act1}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* ACT 2: Maceo Plex Industrial Sub-Bass Matrix */}
        <Series.Sequence durationInFrames={450}>
          <AbsoluteFill>
            <Img
              src={staticFile('shot3_keyframe.png')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: `scale(${interpolate(frame - 450, [0, 450], [1.1, 1.0], { extrapolateRight: 'clamp' })})`,
                filter: 'brightness(0.85) contrast(1.25) saturate(1.2)',
              }}
            />
            <SceneCard
              actNumber="ACT II / IV (00:15 - 00:30)"
              title="Industrial DSP Sub-Bass Matrix"
              subtitle="Maceo Plex Punch & Xenharmonic 24-TET Microtonality"
              description="Heavy FM kick synthesis, razor-sharp transient shaping, and pitch-bend automated macro sweeps."
              color={colors.act2}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* ACT 3: AIR Moon Safari Organic Ambient Textures */}
        <Series.Sequence durationInFrames={450}>
          <AbsoluteFill>
            <Img
              src={staticFile('shot5_keyframe.png')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: `scale(${interpolate(frame - 900, [0, 450], [1.0, 1.15], { extrapolateRight: 'clamp' })})`,
                filter: 'brightness(0.95) contrast(1.1)',
              }}
            />
            <SceneCard
              actNumber="ACT III / IV (00:30 - 00:45)"
              title="Organic Ambient Textures"
              subtitle="AIR Moon Safari Analog Warmth & Acoustic Resonance"
              description="Analog tape flutter simulation, Vocoder harmonics, and ethereal pad textures synthesized deterministically."
              color={colors.act3}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* ACT 4: C5-REAL Thermodynamic Convergence */}
        <Series.Sequence durationInFrames={450}>
          <AbsoluteFill>
            <Img
              src={staticFile('shot7_keyframe.png')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: `scale(${interpolate(frame - 1350, [0, 450], [1.08, 1.0], { extrapolateRight: 'clamp' })})`,
                filter: 'brightness(0.9) contrast(1.2)',
              }}
            />
            <SceneCard
              actNumber="ACT IV / IV (00:45 - 01:00)"
              title="Thermodynamic Convergence"
              subtitle="C5-REAL Zero-Anergy Master Delivery"
              description="Full hybrid spectrum integration, peak exergy optimization, and automated FL Studio Piano Roll export."
              color={colors.act4}
            />
          </AbsoluteFill>
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
