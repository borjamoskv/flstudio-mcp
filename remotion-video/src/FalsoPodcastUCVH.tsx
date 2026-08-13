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

// Import Falso Podcast JSON dataset
import podcastData from '../public/ucvh_podcast.json';

interface EscenaPodcast {
  id: number;
  durationInSeconds: number;
  durationInFrames: number;
  audioTexto: string;
  subtitulo: string;
  silenceDuration: number;
  geminiPrompt: string;
  clipVideo: string;
  audioSpeech: string;
  keyframeFallback: string;
}

// Minimalist Subtitle Component (YouTube Essay Style - Clean & Dark)
const SubtituloMinimalista: React.FC<{ subtitulo: string }> = ({ subtitulo }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 10, 285, 295], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 70,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        opacity,
        zIndex: 30,
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(10, 10, 10, 0.92)', // neutral-950
          color: '#E5E5E5', // neutral-200
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          fontSize: 26,
          fontWeight: 500,
          letterSpacing: '0.02em',
          textAlign: 'center',
          padding: '16px 36px',
          borderRadius: 8,
          maxWidth: 1100,
          border: '1px solid rgba(38, 38, 38, 0.8)', // neutral-800
          boxShadow: '0 10px 25px rgba(0,0,0,0.7)',
          lineHeight: 1.4,
        }}
      >
        {subtitulo}
      </div>
    </div>
  );
};

export const FalsoPodcastUCVH: React.FC = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: '#0A0A0A' }}>
      {/* ⚠️ RAW MINIMALIST FALSO PODCAST: ZERO MUSIC LAYER */}

      <Series>
        {podcastData.scenes.map((escena: EscenaPodcast) => {
          return (
            <Series.Sequence
              key={escena.id}
              durationInFrames={escena.durationInFrames}
            >
              <AbsoluteFill style={{ backgroundColor: '#0A0A0A' }}>
                {/* 1. Static medium shot of crocodile in dark studio */}
                <Img
                  src={staticFile(escena.keyframeFallback)}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />

                {/* 2. Subtítulos minimalistas limpias estilo YouTube Ensayo */}
                <SubtituloMinimalista subtitulo={escena.subtitulo} />
              </AbsoluteFill>
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
