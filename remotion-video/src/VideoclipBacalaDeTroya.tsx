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
import audioData from "../public/audio_data.json";

export const VideoclipBacalaDeTroya: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Clamp frame to precomputed audio data range
  const frameIdx = Math.min(frame, audioData.frames.length - 1);
  const data = audioData.frames[frameIdx] || {
    rms: 0,
    sub: 0,
    mid: 0,
    high: 0,
    bands: new Array(16).fill(0),
    section: "INTRO",
    text: "BAR JUANMA",
    bar: 0,
  };

  const { sub, mid, high, rms, bands, section, text, bar } = data;

  // Camera Shake driven by Sub-Bass & Kick
  const shakeIntensity = sub > 0.55 ? (sub - 0.55) * 35 : 0;
  const shakeX = Math.sin(frame * 1.8) * shakeIntensity;
  const shakeY = Math.cos(frame * 2.1) * shakeIntensity;

  // Background slow zoom + pulse
  const baseZoom = 1.0 + (frame / 1828) * 0.12;
  const pulseZoom = baseZoom + sub * 0.05;

  // Mitxu Character Scale Pulse
  const mitxuScale = 1.0 + sub * 0.14 + mid * 0.06;

  // Glitch trigger on high frequencies (snares/claps/open hats)
  const isGlitch = high > 0.75 && frame % 4 === 0;

  // Switch between Mitxu character, face close-up, and David Landina based on section
  const isDavidTurn = bar >= 5 && bar < 8 && frame % 30 < 14;
  const isMitxuCloseup = bar >= 9 && bar < 13 && frame % 20 < 10;

  // Colors
  const neonYellow = "#F7B928";
  const neonCyan = "#00F0FF";
  const bloodRed = "#FA383E";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#050505",
        overflow: "hidden",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* 1. AUDIO TRACK */}
      <Audio src={staticFile("track.mp3")} />

      {/* 2. BACKGROUND POSTER WITH AUDIO-REACTIVE KEN BURNS */}
      <AbsoluteFill
        style={{
          transform: `scale(${pulseZoom}) translate(${shakeX}px, ${shakeY}px)`,
          filter: `brightness(${0.45 + rms * 0.25}) contrast(1.25) saturate(1.2)`,
        }}
      >
        <Img
          src={staticFile("poster.jpg")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>

      {/* 3. COLOR GRADE OVERLAY & NEON STROBES */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 40%, rgba(247, 185, 40, ${mid * 0.22}), rgba(5, 5, 5, 0.75) 75%)`,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      />

      {/* Sub-bass red flash vignette on heavy drop hits */}
      {sub > 0.8 && (
        <AbsoluteFill
          style={{
            backgroundColor: "rgba(250, 56, 62, 0.18)",
            mixBlendMode: "color-dodge",
            pointerEvents: "none",
          }}
        />
      )}

      {/* 4. HERO CHARACTER FOCUS: MITXU / BACALA DE TROYA */}
      <div
        style={{
          position: "absolute",
          top: "22%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${mitxuScale})`,
          width: 540,
          height: 540,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 10,
        }}
      >
        {/* Pulsing neon circular frame */}
        <div
          style={{
            position: "absolute",
            width: 480 + sub * 70,
            height: 480 + sub * 70,
            borderRadius: "50%",
            border: `4px solid ${bar % 2 === 0 ? neonYellow : neonCyan}`,
            boxShadow: `0 0 ${25 + sub * 40}px ${bar % 2 === 0 ? neonYellow : neonCyan}`,
            opacity: 0.85,
            transition: "all 0.05s ease-out",
          }}
        />

        {/* Dynamic Image cut: Mitxu Face vs Mitxu Character with knife */}
        <div
          style={{
            width: 440,
            height: 440,
            borderRadius: "50%",
            overflow: "hidden",
            border: "4px solid #FFFFFF",
            boxShadow: "0 15px 35px rgba(0,0,0,0.8)",
            position: "relative",
            filter: isGlitch ? "invert(0.8) hue-rotate(90deg)" : "none",
          }}
        >
          <Img
            src={
              isDavidTurn
                ? staticFile("david_char.jpg")
                : isMitxuCloseup
                ? staticFile("mitxu_face.jpg")
                : staticFile("mitxu_char.jpg")
            }
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: isGlitch ? "scale(1.1) translateX(10px)" : "scale(1.0)",
            }}
          />

          {/* Character Tag Pill */}
          <div
            style={{
              position: "absolute",
              bottom: 15,
              left: "50%",
              transform: "translateX(-50%)",
              backgroundColor: isDavidTurn ? "rgba(0,0,0,0.85)" : "#00F0FF",
              color: isDavidTurn ? neonYellow : "#000000",
              fontWeight: 900,
              fontSize: 16,
              letterSpacing: 2,
              padding: "6px 16px",
              borderRadius: 20,
              whiteSpace: "nowrap",
              boxShadow: "0 4px 12px rgba(0,0,0,0.6)",
              border: isDavidTurn ? `1px solid ${neonYellow}` : "none",
            }}
          >
            {isDavidTurn ? "DJ DAVID LANDINA (VIEJA ESCUELA)" : "BACALA DE TROYA (NUEVA ESCUELA)"}
          </div>
        </div>
      </div>

      {/* 5. DYNAMIC IMPACT STREET TYPOGRAPHY */}
      <div
        style={{
          position: "absolute",
          top: "52%",
          left: 0,
          right: 0,
          textAlign: "center",
          padding: "0 40px",
          zIndex: 15,
        }}
      >
        {/* Main Kinetic Text */}
        <div
          style={{
            fontSize: 48 + sub * 12,
            fontWeight: 950,
            color: sub > 0.7 ? "#FFFFFF" : neonYellow,
            textShadow: `0 0 20px ${neonYellow}, 0 0 40px rgba(0,0,0,0.9)`,
            letterSpacing: 3 + sub * 2,
            lineHeight: 1.1,
            textTransform: "uppercase",
            transform: `skew(${Math.sin(frame * 0.2) * 4}deg)`,
          }}
        >
          {text}
        </div>

        {/* Subtitle / Battle Lore */}
        <div
          style={{
            marginTop: 14,
            fontSize: 22,
            fontWeight: 700,
            color: "#FFFFFF",
            letterSpacing: 4,
            opacity: 0.9,
            textShadow: "0 2px 8px rgba(0,0,0,0.8)",
          }}
        >
          {bar < 8
            ? "FUERA DEL BAR JUANMA • VIERNES 12:00"
            : bar < 16
            ? "SUBBASS 43.65 Hz • TUBA & TROMBONES"
            : bar < 24
            ? "SOLO UNO PUEDE MANDAR EN URIBARRI"
            : "CHICAGO SOUL ELECTRO • BILBAO 48007"}
        </div>
      </div>

      {/* 6. AUDIO SPECTRUM VISUALIZER BARS (16 BANDS) */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 60,
          right: 60,
          height: 140,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          zIndex: 20,
        }}
      >
        {bands.map((val: number, i: number) => {
          const barHeight = Math.max(12, val * 135);
          const isTubaBand = i <= 3; // Low bass / tuba
          const isTromboneBand = i >= 4 && i <= 8; // Brass mids

          return (
            <div
              key={i}
              style={{
                width: 22,
                height: `${barHeight}px`,
                backgroundColor: isTubaBand
                  ? neonYellow
                  : isTromboneBand
                  ? neonCyan
                  : "#FFFFFF",
                borderRadius: "6px 6px 2px 2px",
                boxShadow: `0 0 12px ${
                  isTubaBand ? neonYellow : isTromboneBand ? neonCyan : "#FFFFFF"
                }`,
                transition: "height 0.04s ease-out",
                opacity: 0.9,
              }}
            />
          );
        })}
      </div>

      {/* 7. HUD TELEMETRY OVERLAYS */}
      {/* Top Bar */}
      <div
        style={{
          position: "absolute",
          top: 50,
          left: 45,
          right: 45,
          display: "flex",
          justifyContent: "space-between",
          color: "rgba(255, 255, 255, 0.75)",
          fontSize: 15,
          fontWeight: 700,
          letterSpacing: 2,
          fontFamily: "monospace",
          zIndex: 25,
        }}
      >
        <div>
          <span style={{ color: neonYellow }}>● REC</span> 126.0 BPM // CHIC-ELECTRO
        </div>
        <div style={{ color: neonCyan }}>
          SECTION: [{section}] // BAR: {bar + 1}/32
        </div>
      </div>

      {/* Bottom Bar Info */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          left: 45,
          right: 45,
          display: "flex",
          justifyContent: "space-between",
          color: "rgba(255, 255, 255, 0.65)",
          fontSize: 14,
          fontWeight: 600,
          letterSpacing: 1.5,
          fontFamily: "monospace",
          zIndex: 25,
        }}
      >
        <div>VOX: MITXU // TUBA + TROMBONES</div>
        <div>C5-REAL AUDIO-REACTIVE ENGINE</div>
      </div>

      {/* 8. CRT SCANLINE EFFECT */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)",
          backgroundSize: "100% 4px",
          pointerEvents: "none",
          opacity: 0.6,
          zIndex: 30,
        }}
      />
    </AbsoluteFill>
  );
};
