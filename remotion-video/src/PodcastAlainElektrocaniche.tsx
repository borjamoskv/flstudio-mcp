import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import podcastData from "../public/podcast_data.json";

export const PodcastAlainElektrocaniche: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Clamp frame to data length
  const frameIdx = Math.min(frame, podcastData.frames.length - 1);
  const data = podcastData.frames[frameIdx] || {
    rms: 0,
    sub: 0,
    mid: 0,
    high: 0,
    bands: new Array(16).fill(0),
    speaker: "ALAIN",
    text: "",
  };

  const { rms, sub, mid, high, bands, speaker, text } = data;

  // Camera subtle push-in
  const cameraZoom = interpolate(frame, [0, 2160], [1.0, 1.05], {
    extrapolateRight: "clamp",
  });

  // Speaker talking indicator
  const isTalking = text.length > 0 && rms > 0.08;

  // Guest avatar pulse
  const avatarScale = 1.0 + (isTalking ? rms * 0.08 : 0) + sub * 0.03;
  const avatarGlow = isTalking
    ? `0 0 ${25 + rms * 35}px rgba(255, 180, 0, 0.7)`
    : "0 0 15px rgba(0, 240, 255, 0.3)";

  // Subtitle spring animation on text change
  const textScale = spring({
    frame: frame % 90,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  // Ticker horizontal scroll
  const tickerOffset = (frame * 3.8) % 3600;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#06060c",
        overflow: "hidden",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        color: "#ffffff",
      }}
    >
      {/* 1. AUDIO TRACK */}
      <Audio src={staticFile("podcast_alain.mp3")} />

      {/* 2. BACKGROUND: CYBER STUDIO WITH RADIAL LIGHTS */}
      <AbsoluteFill
        style={{
          transform: `scale(${cameraZoom})`,
          transformOrigin: "center center",
        }}
      >
        {/* Ambient background image blurred */}
        <Img
          src={staticFile("alain_cosmic.jpg")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: `brightness(${0.18 + rms * 0.12}) blur(8px) saturate(1.4)`,
            transform: "scale(1.1)",
          }}
        />

        {/* Studio Neon Vignette Grid */}
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(circle at 50% 35%, rgba(106, 27, 130, 0.25) 0%, rgba(6, 6, 12, 0.85) 60%, rgba(3, 3, 6, 0.98) 100%)",
            mixBlendMode: "screen",
          }}
        />

        {/* Ambient Grid overlay */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
            opacity: 0.7,
          }}
        />
      </AbsoluteFill>

      {/* 3. TOP BROADCAST HEADER HUD */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 75,
          backgroundColor: "rgba(10, 10, 18, 0.88)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(255, 180, 0, 0.35)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 40px",
          zIndex: 50,
        }}
      >
        {/* Left: Live status */}
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              backgroundColor: frame % 30 < 18 ? "#ff2a3b" : "#661118",
              boxShadow: frame % 30 < 18 ? "0 0 12px #ff2a3b" : "none",
            }}
          />
          <span
            style={{
              fontWeight: 800,
              fontSize: 18,
              letterSpacing: "0.12em",
              color: "#ff2a3b",
            }}
          >
            EN DIRECTO
          </span>
          <span
            style={{
              fontSize: 14,
              letterSpacing: "0.08em",
              color: "rgba(255, 255, 255, 0.6)",
              marginLeft: 12,
            }}
          >
            BILBAO ⇄ TOKIO SATELLITE FEED · 4K 60FPS
          </span>
        </div>

        {/* Center: Podcast Title */}
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize: 20,
              fontWeight: 900,
              letterSpacing: "0.16em",
              color: "#F7B928",
              textTransform: "uppercase",
            }}
          >
            CORTEZAS Y CONCERTAS
          </div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: "0.14em",
              color: "#00F0FF",
            }}
          >
            EL PODCAST DE LA TRINCHERA TERMODINÁMICA
          </div>
        </div>

        {/* Right: Episode badge */}
        <div
          style={{
            backgroundColor: "rgba(247, 185, 40, 0.15)",
            border: "1px solid #F7B928",
            borderRadius: 6,
            padding: "6px 14px",
            fontSize: 13,
            fontWeight: 800,
            letterSpacing: "0.06em",
            color: "#F7B928",
          }}
        >
          EP 01: ELECTROCANICHE IN JAPAN
        </div>
      </div>

      {/* 4. MAIN STUDIO PODCAST LAYOUT: DUAL PANELS */}
      <div
        style={{
          position: "absolute",
          top: 105,
          left: 60,
          right: 60,
          bottom: 180,
          display: "grid",
          gridTemplateColumns: "1fr 1.6fr",
          gap: 40,
          zIndex: 20,
        }}
      >
        {/* PANEL 1: HOST (BORJA MOSKV) */}
        <div
          style={{
            backgroundColor: "rgba(14, 15, 25, 0.75)",
            backdropFilter: "blur(10px)",
            borderRadius: 16,
            border: "1px solid rgba(255, 255, 255, 0.12)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            position: "relative",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "16px 20px",
              backgroundColor: "rgba(0, 0, 0, 0.45)",
              borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: "#00F0FF",
                  boxShadow: "0 0 8px #00F0FF",
                }}
              />
              <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.08em", color: "#00F0FF" }}>
                HOST · ESTUDIO BILBAO
              </span>
            </div>
            <span style={{ fontSize: 12, color: "rgba(255, 255, 255, 0.5)" }}>C5-REAL HYPERVISOR</span>
          </div>

          {/* Body */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: 30,
              gap: 20,
            }}
          >
            {/* Host Graphic Card */}
            <div
              style={{
                width: 170,
                height: 170,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #1f1f38, #0b0c16)",
                border: "2px solid rgba(0, 240, 255, 0.5)",
                boxShadow: "0 0 30px rgba(0, 240, 255, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                position: "relative",
              }}
            >
              <div style={{ fontSize: 56 }}>🎙️</div>
              {/* Spinning rings */}
              <div
                style={{
                  position: "absolute",
                  inset: -12,
                  borderRadius: "50%",
                  border: "1px dashed rgba(0, 240, 255, 0.35)",
                  transform: `rotate(${frame * 0.8}deg)`,
                }}
              />
            </div>

            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 26, fontWeight: 900, letterSpacing: "0.04em", color: "#ffffff" }}>
                BORJA MOSKV
              </div>
              <div style={{ fontSize: 14, color: "rgba(255, 255, 255, 0.65)", marginTop: 4 }}>
                Sistemas Complejos & Producción Sónica
              </div>
            </div>

            {/* Host VU Meter */}
            <div
              style={{
                width: "80%",
                height: 12,
                backgroundColor: "rgba(255, 255, 255, 0.08)",
                borderRadius: 6,
                overflow: "hidden",
                marginTop: 10,
              }}
            >
              <div
                style={{
                  width: `${Math.min(100, (0.25 + sub * 0.45) * 100)}%`,
                  height: "100%",
                  background: "linear-gradient(90deg, #00F0FF, #F7B928)",
                  transition: "width 0.05s ease-out",
                }}
              />
            </div>
          </div>
        </div>

        {/* PANEL 2: GUEST (ALAIN ELEKTROCANICHE) - MAIN FOCUS */}
        <div
          style={{
            backgroundColor: "rgba(18, 16, 28, 0.85)",
            backdropFilter: "blur(14px)",
            borderRadius: 16,
            border: isTalking
              ? "2px solid rgba(247, 185, 40, 0.85)"
              : "1px solid rgba(255, 255, 255, 0.12)",
            boxShadow: isTalking
              ? "0 0 45px rgba(247, 185, 40, 0.25)"
              : "none",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            position: "relative",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "16px 24px",
              backgroundColor: "rgba(0, 0, 0, 0.55)",
              borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: isTalking ? "#00FF66" : "#F7B928",
                  boxShadow: isTalking ? "0 0 10px #00FF66" : "none",
                }}
              />
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 800,
                  letterSpacing: "0.08em",
                  color: "#F7B928",
                }}
              >
                INVITADO ESPECIAL · VÍA SATÉLITE
              </span>
            </div>
            <div
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: isTalking ? "#00FF66" : "rgba(255, 255, 255, 0.5)",
              }}
            >
              {isTalking ? "● MICRÓFONO TRANSMITIENDO" : "EN ESPERA"}
            </div>
          </div>

          {/* Main Guest Visual Box */}
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 30,
              gap: 40,
            }}
          >
            {/* Alain Avatar with Audio Pulse */}
            <div
              style={{
                position: "relative",
                width: 240,
                height: 240,
                borderRadius: 20,
                overflow: "hidden",
                border: "3px solid #F7B928",
                boxShadow: avatarGlow,
                transform: `scale(${avatarScale})`,
                transition: "transform 0.05s ease-out",
              }}
            >
              <Img
                src={staticFile("alain_avatar.jpg")}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
              {/* Live Overlay Badge */}
              <div
                style={{
                  position: "absolute",
                  bottom: 8,
                  left: 8,
                  right: 8,
                  backgroundColor: "rgba(0, 0, 0, 0.75)",
                  padding: "4px 8px",
                  borderRadius: 6,
                  textAlign: "center",
                  fontSize: 11,
                  fontWeight: 800,
                  color: "#F7B928",
                  letterSpacing: "0.06em",
                }}
              >
                ALAIN ELEKTROCANICHE
              </div>
            </div>

            {/* Guest Info & Big Quote */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <div style={{ fontSize: 32, fontWeight: 900, color: "#F7B928", letterSpacing: "0.02em" }}>
                  ALAIN ELEKTRONISCHE
                </div>
                <div style={{ fontSize: 16, color: "rgba(255, 255, 255, 0.7)", marginTop: 4 }}>
                  Investigador Periodístico & Filósofo de Cabina
                </div>
              </div>

              {/* Status Pills */}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <span
                  style={{
                    backgroundColor: "rgba(247, 185, 40, 0.15)",
                    border: "1px solid rgba(247, 185, 40, 0.4)",
                    color: "#F7B928",
                    padding: "4px 12px",
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  ⚡ Concerta & Spiz 126 BPM
                </span>
                <span
                  style={{
                    backgroundColor: "rgba(0, 240, 255, 0.15)",
                    border: "1px solid rgba(0, 240, 255, 0.4)",
                    color: "#00F0FF",
                    padding: "4px 12px",
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  🇯🇵 El País del Sol Naciente
                </span>
                <span
                  style={{
                    backgroundColor: "rgba(255, 42, 59, 0.15)",
                    border: "1px solid rgba(255, 42, 59, 0.4)",
                    color: "#ff2a3b",
                    padding: "4px 12px",
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  🔥 Moonwalk a las 6 AM
                </span>
              </div>

              {/* Live Audio Spectrum Bars (16 Bands) */}
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255, 255, 255, 0.4)", marginBottom: 6 }}>
                  FRECUENCIA DE SEÑAL / SPECTRUM DSP
                </div>
                <div style={{ display: "flex", alignItems: "flex-end", height: 38, gap: 5 }}>
                  {bands.map((bVal: number, i: number) => {
                    const barHeight = Math.max(4, bVal * 38);
                    const color = i < 4 ? "#ff2a3b" : i < 10 ? "#F7B928" : "#00F0FF";
                    return (
                      <div
                        key={i}
                        style={{
                          flex: 1,
                          height: barHeight,
                          backgroundColor: color,
                          borderRadius: 2,
                          boxShadow: `0 0 6px ${color}`,
                        }}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. DYNAMIC KINETIC SUBTITLES / TELEPROMPTER (LOWER THIRD) */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          left: 80,
          right: 80,
          height: 95,
          backgroundColor: "rgba(10, 10, 20, 0.92)",
          backdropFilter: "blur(16px)",
          borderRadius: 14,
          border: "2px solid #F7B928",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(247, 185, 40, 0.25)",
          display: "flex",
          alignItems: "center",
          padding: "0 35px",
          gap: 25,
          zIndex: 40,
        }}
      >
        {/* Speaker Tag */}
        <div
          style={{
            backgroundColor: "#F7B928",
            color: "#000000",
            fontWeight: 900,
            fontSize: 16,
            padding: "8px 18px",
            borderRadius: 6,
            letterSpacing: "0.08em",
            whiteSpace: "nowrap",
          }}
        >
          ALAIN
        </div>

        {/* Dynamic Spoken Text */}
        <div
          style={{
            flex: 1,
            fontSize: 26,
            fontWeight: 800,
            color: "#ffffff",
            letterSpacing: "0.01em",
            textShadow: "0 2px 8px rgba(0, 0, 0, 0.8)",
          }}
        >
          {text || "«... escuchando música de fondo y sintonizando el canal...»"}
        </div>
      </div>

      {/* 6. BOTTOM CRAWLER NEWS TICKER */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 36,
          backgroundColor: "#F7B928",
          color: "#000000",
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          fontWeight: 900,
          fontSize: 14,
          letterSpacing: "0.06em",
          zIndex: 60,
        }}
      >
        <div
          style={{
            whiteSpace: "nowrap",
            display: "inline-block",
            transform: `translateX(-${tickerOffset}px)`,
          }}
        >
          ● ÚLTIMA HORA: EL VIAJERO SECRETO AL PAÍS DEL SOL NACIENTE SIGUE EN PARADERO DESCONOCIDO ● CONCERTA + 3 TIROS DE SPIZ + 5 BIRRAS Y 2 TEQUILAS: FÓRMULA MÁGICA DE BILBAO ● LOS DISCOS SE PONEN HACIENDO EL MOONWALK A LAS 6 DE LA MAÑANA ● PEDRO SÁNCHEZ IDENTIFICADO COMO TERMINATOR T-900 ● SINDICATO DE INQUILINOS NOMBRADO MEJOR COMERCIAL DE AIRBNB EN ESPAÑA ● ESCOHOTADO: EL ORGASMO ES UNA BROMA AL LADO DEL CONOCIMIENTO ●
        </div>
      </div>
    </AbsoluteFill>
  );
};
