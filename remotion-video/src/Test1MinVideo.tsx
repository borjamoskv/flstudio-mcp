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

// Timecode Helper
const formatTimecode = (frame: number, fps: number) => {
  const totalSeconds = frame / fps;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const milliseconds = Math.floor((totalSeconds % 1) * 100);
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(2, '0')}`;
};

// 1. Top-Right Moderation & Hate Speech Warning (UCVH Style)
const ModerationWarningBox: React.FC<{ warningText: string }> = ({ warningText }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 12, 280, 295], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const translateX = interpolate(frame, [0, 15], [40, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });

  const pulseScale = 1 + 0.015 * Math.sin(frame * 0.15);

  return (
    <div
      style={{
        position: 'absolute',
        top: 60,
        right: 60,
        width: 440,
        backgroundColor: 'rgba(18, 18, 22, 0.92)',
        border: '1.5px solid #F59E0B',
        padding: '16px 22px',
        borderRadius: 12,
        boxShadow: '0 20px 40px rgba(0,0,0,0.8), 0 0 25px rgba(245, 158, 11, 0.25)',
        backdropFilter: 'blur(12px)',
        opacity,
        transform: `translateX(${translateX}px) scale(${pulseScale})`,
        zIndex: 50,
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
        <span>⚠️</span> AVISO DE MODERACIÓN UCVH
      </div>
      <div
        style={{
          color: '#E4E4E7',
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

// 2. Holographic Data Chart Box (UCVH Style)
const HolographicChartBox: React.FC<{ title: string; stat: string }> = ({ title, stat }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 275, 290], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const scale = interpolate(frame, [0, 15], [0.9, 1], {
    easing: Easing.out(Easing.back(1.4)),
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 140,
        left: 60,
        backgroundColor: 'rgba(10, 25, 15, 0.88)',
        border: '1.5px solid #10B981',
        padding: '16px 24px',
        borderRadius: 12,
        boxShadow: '0 15px 35px rgba(0,0,0,0.7), 0 0 20px rgba(16, 185, 129, 0.2)',
        backdropFilter: 'blur(10px)',
        opacity,
        transform: `scale(${scale})`,
        zIndex: 45,
      }}
    >
      <div
        style={{
          color: '#34D399',
          fontSize: 11,
          fontWeight: 800,
          letterSpacing: 2,
          fontFamily: "'JetBrains Mono', monospace",
          textTransform: 'uppercase',
          marginBottom: 4,
        }}
      >
        {title}
      </div>
      <div
        style={{
          color: '#FFFFFF',
          fontSize: 22,
          fontWeight: 900,
          fontFamily: "'Inter', sans-serif",
        }}
      >
        {stat}
      </div>
    </div>
  );
};

// 3. Crocodile Subtitles & Badge (Crocodile Style)
const SubtituloCocodrilo: React.FC<{ subtitulo: string; bloque: string }> = ({
  subtitulo,
  bloque,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 12, 280, 295], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });

  const scale = interpolate(frame, [0, 15], [0.95, 1], {
    easing: Easing.out(Easing.back(1.5)),
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Badge Top Left: Pensamientos del personaje */}
      <div
        style={{
          position: 'absolute',
          top: 60,
          left: 60,
          backgroundColor: 'rgba(5, 20, 10, 0.85)',
          color: '#4ADE80',
          padding: '12px 24px',
          borderRadius: 10,
          border: '1.5px solid rgba(74, 222, 128, 0.5)',
          fontFamily: "'Inter', sans-serif",
          fontSize: 18,
          fontWeight: 700,
          letterSpacing: 1,
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.6), 0 0 15px rgba(74, 222, 128, 0.2)',
          zIndex: 50,
        }}
      >
        🐊 {bloque}
      </div>

      {/* Box Bottom Center: Subtítulos dinámicos estilizados */}
      <div
        style={{
          position: 'absolute',
          bottom: 120,
          left: 60,
          right: 60,
          display: 'flex',
          justify: 'center',
          opacity,
          transform: `scale(${scale})`,
          zIndex: 50,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(8, 14, 10, 0.92)',
            color: '#FFFFFF',
            fontFamily: "'Inter', system-ui, sans-serif",
            fontWeight: 700,
            fontSize: 30,
            textAlign: 'center',
            padding: '22px 40px',
            borderRadius: 16,
            maxWidth: 1300,
            border: '2px solid #22C55E',
            boxShadow: '0 15px 40px rgba(0,0,0,0.85), 0 0 30px rgba(34, 197, 94, 0.3)',
            lineHeight: 1.4,
          }}
        >
          {subtitulo}
        </div>
      </div>
    </>
  );
};

// 4. Global HUD & Progress Bar Component
const UCVHHud: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const timecode = formatTimecode(frame, fps);
  const progressPercent = (frame / 1800) * 100;

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 100 }}>
      {/* Top Progress Bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 5,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            backgroundColor: '#22C55E',
            boxShadow: '0 0 12px #22C55E',
          }}
        />
      </div>

      {/* Bottom Right Studio Timecode */}
      <div
        style={{
          position: 'absolute',
          bottom: 40,
          right: 60,
          fontFamily: "'JetBrains Mono', monospace",
          color: '#FFFFFF',
          fontSize: 20,
          fontWeight: 800,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          padding: '8px 18px',
          borderRadius: 8,
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
        }}
      >
        UCVH TEST // {timecode} <span style={{ color: '#4ADE80' }}>(01:00)</span>
      </div>
    </AbsoluteFill>
  );
};

// Main 1-Minute Video Component
export const Test1MinVideo: React.FC = () => {
  const frame = useCurrentFrame();

  const scenes = [
    {
      id: 1,
      bloque: '1. Marroquinería de Alta Costura',
      subtitulo:
        '“¿Piel sintética? Por favor. Si me vas a convertir en bolso de alta costura, exijo que el cierre sea de titanio y el forro de terciopelo.”',
      warning:
        'ALERTA DE SESGO ESPECISTA: El algoritmo UCVH clasifica esto como sátira no destructiva sobre bolsos.',
      chartTitle: 'ESTADÍSTICA DE PANTANO',
      chartStat: '94.2% Mocasines de Lujo',
      image: 'shot1_keyframe.png',
    },
    {
      id: 2,
      bloque: '2. Cadena Alimenticia y Fango',
      subtitulo:
        '“Dicen que los humanos están en la cima de la evolución... pero nunca he visto a un humano aguantar 40 minutos sumergido en fango sin quejarse.”',
      warning:
        'SUPERIORIDAD REPTILIANA DETECTADA: Flag activo de ego descalibrado en entorno palustre.',
      chartTitle: 'RESISTENCIA AL FANGO',
      chartStat: 'Cocodrilo: 100% | Humano: 0.2%',
      image: 'shot3_keyframe.png',
    },
    {
      id: 3,
      bloque: '3. Lágrimas de Cocodrilo',
      subtitulo:
        '“Mis lágrimas no son falsas, son simplemente lubricante ocular de alta precisión acuática. Falacia ad hominem de los mamíferos.”',
      warning:
        'ADVERTENCIA EPISTÉMICA: Confusión entre lubricación oftálmica y empatía biológica.',
      chartTitle: 'FLUJO LAGRIMAL',
      chartStat: '100% Exergía H2O + Sales',
      image: 'shot5_keyframe.png',
    },
    {
      id: 4,
      bloque: '4. Algoritmos de Moderación',
      subtitulo:
        '“El filtro de moderación me pide \'cuide su lenguaje\'. Estimado algoritmo: llevo 80 millones de años sin cambiar de sintaxis y aquí sigo.”',
      warning:
        'FLAG DE DESAFÍO ALGORÍTMICO: Intento de evasión del filtro de moderación de UCVH.',
      chartTitle: 'SUPERVIVENCIA EVOLUTIVA',
      chartStat: '80M Años vs 3 Años de IA',
      image: 'shot7_keyframe.png',
    },
    {
      id: 5,
      bloque: '5. La Termodinámica del Sol',
      subtitulo:
        '“Los humanos pagan fortunas en spas para tomar el sol. Nosotros lo llamamos \'martes por la mañana\' con eficiencia termodinámica.”',
      warning:
        'INVIOLABILIDAD TERMODINÁMICA: Absorción de radiación solar con cero anergía.',
      chartTitle: 'EFICIENCIA SOLAR PASIVA',
      chartStat: 'Termorregulación 99.9%',
      image: 'shot1_keyframe.png',
    },
    {
      id: 6,
      bloque: '6. Conclusión Filosófica',
      subtitulo:
        '“En resumen: menos discursos de odio, más siestas en la orilla del río. C5-REAL Aprobado por el Gremio de Caimanes.”',
      warning:
        'ESTADO FINAL DE AUDITORÍA: Contenido de prueba auditado y verificado bajo invariantes C5-REAL.',
      chartTitle: 'DICTAMEN UCVH',
      chartStat: '100% Sátira Determinista',
      image: 'shot3_keyframe.png',
    },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: '#030804' }}>
      {/* Background Audio (Continuous loop) */}
      <Audio src={staticFile('Satin_Maceo_AIR_Flow_Master.wav')} volume={0.4} />

      {/* Global UCVH HUD Overlay */}
      <UCVHHud />

      {/* Cinematic Vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 35,
          background:
            'radial-gradient(circle at 50% 50%, transparent 40%, rgba(3, 8, 4, 0.8) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* 6 Scenes of 10 Seconds Each (300 frames * 6 = 1800 frames / 60 seconds) */}
      <Series>
        {scenes.map((scene) => {
          return (
            <Series.Sequence key={scene.id} durationInFrames={300}>
              <AbsoluteFill style={{ backgroundColor: '#030804' }}>
                {/* Visual Image with Ken Burns Effect */}
                <Img
                  src={staticFile(scene.image)}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    transform: `scale(${interpolate(frame % 300, [0, 300], [1.0, 1.1], { extrapolateRight: 'clamp' })})`,
                    filter: 'brightness(0.85) contrast(1.15) saturate(1.1)',
                  }}
                />

                {/* Top Right Warning Box */}
                <ModerationWarningBox warningText={scene.warning} />

                {/* Top Left Holographic Chart */}
                <HolographicChartBox title={scene.chartTitle} stat={scene.chartStat} />

                {/* Bottom Subtitle & Crocodile Badge */}
                <SubtituloCocodrilo subtitulo={scene.subtitulo} bloque={scene.bloque} />
              </AbsoluteFill>
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
