import { AbsoluteFill, Series, Video, useVideoConfig } from "remotion";
import React from "react";
// Importamos el JSON asumiendo que lo copiamos a la carpeta public o está en un lugar accesible.
// Para Remix/Remotion normal, importarlo desde public si no lo bundlea webpack es mejor obtenerlo
// via staticFile o require. Aquí asumimos entorno webpack configurado por defecto.
import podcastData from "../../ucvh_pipeline/ucvh_podcast.json";

// Tipo estricto de los datos
type Scene = {
  id: number;
  audioTexto: string;
  subtitulo: string;
  geminiPrompt: string;
};

// Duración de cada clip según la especificación: 10 segundos a 30 fps = 300 frames.
const FRAMES_PER_SCENE = 300;

const SubtitleContainer: React.FC<{ text: string }> = ({ text }) => {
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "80px",
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(30, 30, 30, 0.85)",
          color: "#ffffff",
          fontFamily: "monospace, sans-serif",
          fontSize: "32px",
          fontWeight: 500,
          textAlign: "center",
          maxWidth: "80%",
          padding: "20px 40px",
          borderRadius: "12px",
          border: "2px solid rgba(255, 255, 255, 0.1)",
          boxShadow: "0px 10px 30px rgba(0, 0, 0, 0.5)",
          lineHeight: "1.4",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const UCVHPodcast: React.FC = () => {
  const { fps } = useVideoConfig();
  
  // podcastData.scenes ya tiene la lista
  const scenes: Scene[] = podcastData.scenes;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Series>
        {scenes.map((scene) => (
          <Series.Sequence
            key={scene.id}
            durationInFrames={FRAMES_PER_SCENE}
            name={`Scene-${scene.id}`}
          >
            {/* El video ya lleva el audio incrustado por Sync Labs para evitar desincronizaciones milimétricas */}
            <AbsoluteFill>
              {/* En desarrollo real, Remotion sirve archivos de la carpeta /public directamente */}
              {/* Se asume que el pipeline descargó los videos en /public/clips/ */}
              <Video 
                src={`/clips/ucvh_ready_${scene.id}.mp4`}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            </AbsoluteFill>

            {/* Subtítulos */}
            <SubtitleContainer text={scene.subtitulo} />
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
