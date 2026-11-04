import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  staticFile,
  useCurrentFrame,
} from "remotion";
import telemetry from "../public/tuba_caniche_telemetry.json";

export const VideoclipTubaCanicheAlain: React.FC = () => {
  const frame = useCurrentFrame();

  const frameIdx = Math.min(frame, telemetry.frames.length - 1);
  const data = telemetry.frames[frameIdx] || {
    frame: 0,
    time: 0,
    bar: 0,
    rms: 0,
    sub: 0,
    mid: 0,
    high: 0,
    bands: new Array(16).fill(0),
    section: "INTRO_QUEJIO",
    speaker: "Cantaor Jondo",
    text: "",
    isCaniche: false,
    isNegativeHarmony: false,
    isOuroboros: true,
    headbob: 0,
  };

  const {
    bar,
    rms,
    sub,
    mid,
    high,
    bands,
    speaker,
    text,
    isCaniche,
    isNegativeHarmony,
    isOuroboros,
    headbob,
  } = data;

  const isAlainTalking = speaker.includes("Alain");
  const isMariLupe = speaker.includes("Mari Lupe");

  // Camera Shake on Sub-Bass & Pad-Kick
  const shakeIntensity = sub > 0.5 ? (sub - 0.5) * 28 : 0;
  const shakeX = Math.sin(frame * 2.3) * shakeIntensity;
  const shakeY = Math.cos(frame * 1.9) * shakeIntensity;

  // Background zoom on beat
  const bgScale = 1.0 + sub * 0.08 + rms * 0.04;

  // South park mouth flap for Alain
  const flapGap = isAlainTalking ? Math.max(0, Math.sin(frame * 1.6) * (20 + rms * 60)) : 0;

  // Happy poodle delay echoes
  const delayEchoes = [0, 1, 2, 3, 4, 5, 6, 7];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: isNegativeHarmony ? "#f5f0e6" : "#05060a",
        overflow: "hidden",
        fontFamily: "'Impact', 'Chalkboard SE', 'Arial Black', sans-serif",
        filter: isNegativeHarmony ? "invert(0.92) hue-rotate(180deg)" : "none",
        transition: "filter 0.3s ease",
      }}
    >
      {/* 1. MASTER AUDIO TRACK */}
      <Audio src={staticFile("tuba_caniche_track.mp3")} />

      {/* 2. BACKGROUND VISUAL GRID & NEON ATMOSPHERE */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translate(${shakeX}px, ${shakeY}px)`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {/* Radial Energy Burst */}
        <div
          style={{
            position: "absolute",
            width: 1400,
            height: 1400,
            borderRadius: "50%",
            background: isNegativeHarmony
              ? "radial-gradient(circle, rgba(0,255,200,0.3) 0%, rgba(255,0,128,0) 70%)"
              : "radial-gradient(circle, rgba(255,140,0,0.25) 0%, rgba(0,20,50,0) 70%)",
            transform: `scale(${1.0 + sub * 0.4})`,
            filter: "blur(40px)",
          }}
        />

        {/* 16-Band Audio Reactive Spectrum Bar Floor */}
        <div
          style={{
            position: "absolute",
            bottom: 40,
            left: 80,
            right: 80,
            height: 180,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            zIndex: 5,
            opacity: 0.75,
          }}
        >
          {bands.map((b: number, idx: number) => {
            const barH = Math.max(8, b * 170);
            const hue = (idx * 22 + frame * 2) % 360;
            return (
              <div
                key={idx}
                style={{
                  width: `${100 / 18}%`,
                  height: `${barH}px`,
                  backgroundColor: `hsl(${hue}, 90%, 55%)`,
                  borderRadius: "6px 6px 0 0",
                  boxShadow: `0 0 15px hsl(${hue}, 90%, 55%)`,
                  transform: `scaleY(${1.0 + rms * 0.3})`,
                  transformOrigin: "bottom",
                }}
              />
            );
          })}
        </div>
      </AbsoluteFill>

      {/* 3. OUROBOROS COSMIC RING (INTRO & EPÍLOGO) */}
      {isOuroboros && (
        <AbsoluteFill
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 8,
          }}
        >
          <div
            style={{
              width: 520,
              height: 520,
              borderRadius: "50%",
              border: "12px dashed #ffb703",
              boxShadow: "0 0 50px #fb8500, inset 0 0 50px #fb8500",
              transform: `rotate(${frame * 1.5}deg) scale(${1.0 + mid * 0.25})`,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <div
              style={{
                color: "#ffb703",
                fontSize: 34,
                letterSpacing: 6,
                textTransform: "uppercase",
                textAlign: "center",
                textShadow: "0 0 20px #fb8500",
              }}
            >
              OUROBOROS JONDO
              <br />
              <span style={{ fontSize: 20, color: "#fff" }}>QUEJÍO INMUTABLE</span>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* 4. GIANT TUBA WITH CHORUS VIBRATION (LEFT SIDE) */}
      <div
        style={{
          position: "absolute",
          left: 120,
          bottom: 160,
          width: 320,
          height: 480,
          zIndex: 12,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "flex-end",
          transform: `scale(${1.0 + sub * 0.22}) translateY(${headbob * 12}px)`,
          transformOrigin: "bottom center",
        }}
      >
        {/* Tuba Flare / Bell */}
        <div
          style={{
            width: 240,
            height: 140,
            borderRadius: "50% 50% 10% 10%",
            background: "linear-gradient(135deg, #ffd700 0%, #b8860b 50%, #4a3500 100%)",
            boxShadow: `0 0 ${30 + sub * 50}px #ffd700`,
            border: "4px solid #fff",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              width: 160,
              height: 70,
              borderRadius: "50%",
              background: "#1a1200",
              boxShadow: "inset 0 0 25px #000",
            }}
          />
        </div>
        {/* Tuba Tubing coils */}
        <div
          style={{
            width: 180,
            height: 220,
            border: "28px solid #d4af37",
            borderRadius: "60px",
            marginTop: -20,
            boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          }}
        />
        <div
          style={{
            color: "#ffd700",
            fontSize: 22,
            marginTop: 10,
            textShadow: "0 0 10px #ffd700",
            letterSpacing: 2,
          }}
        >
          TUBA EN MENOR (CHORUS)
        </div>
      </div>

      {/* 5. SOUTH PARK ALAIN SOTA CHARACTER (RIGHT SIDE) */}
      <div
        style={{
          position: "absolute",
          right: 180,
          bottom: 120,
          width: 380,
          zIndex: 15,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: `scale(${1.0 + rms * 0.12}) translateY(${headbob * 15}px)`,
          transformOrigin: "bottom center",
        }}
      >
        {/* ALAIN HEAD ASSEMBLY (FLAPPING JAW) */}
        <div
          style={{
            position: "relative",
            width: 320,
            height: 260,
            zIndex: 10,
          }}
        >
          {/* Mouth Cavity */}
          <div
            style={{
              position: "absolute",
              top: 160,
              left: 55,
              width: 210,
              height: 55,
              backgroundColor: "#780016",
              borderRadius: "0 0 40px 40px",
              zIndex: 2,
            }}
          >
            {/* Tongue */}
            <div
              style={{
                position: "absolute",
                bottom: 4,
                left: "30%",
                width: 80,
                height: 25,
                backgroundColor: "#ff4d6d",
                borderRadius: "50%",
              }}
            />
          </div>

          {/* Alain Top Head (Flaps up on speech) */}
          <div
            style={{
              position: "absolute",
              top: -flapGap,
              left: 0,
              width: "100%",
              height: 190,
              zIndex: 4,
              transition: "top 0.05s ease-out",
            }}
          >
            <Img
              src={staticFile("sp_alain_head_top.png")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                filter: "drop-shadow(0 10px 15px rgba(0,0,0,0.5))",
              }}
            />
          </div>

          {/* Alain Jaw (Static anchor) */}
          <div
            style={{
              position: "absolute",
              top: 150,
              left: 0,
              width: "100%",
              height: 100,
              zIndex: 3,
            }}
          >
            <Img
              src={staticFile("sp_alain_head_jaw.png")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                filter: "drop-shadow(0 10px 15px rgba(0,0,0,0.5))",
              }}
            />
          </div>
        </div>

        {/* Alain Body */}
        <div
          style={{
            width: 340,
            height: 300,
            marginTop: -30,
            zIndex: 5,
          }}
        >
          <Img
            src={staticFile("sp_alain_body.png")}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
            }}
          />
        </div>
      </div>

      {/* 6. HAPPY POODLE DELAY COLLAPSE (BRIDGE & CENTER COLLAPSE) */}
      {isCaniche && (
        <AbsoluteFill
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 20,
            pointerEvents: "none",
          }}
        >
          {delayEchoes.map((echoIdx) => {
            const echoGain = Math.pow(0.58, echoIdx);
            const echoPan = echoIdx % 2 === 1 ? 160 * echoIdx : -160 * echoIdx;
            const bounce = Math.abs(Math.sin((frame + echoIdx * 4) * 0.4)) * 70;

            return (
              <div
                key={echoIdx}
                style={{
                  position: "absolute",
                  transform: `translate(${echoPan}px, ${-bounce}px) scale(${1.2 * echoGain})`,
                  opacity: Math.max(0.2, echoGain),
                  filter: `drop-shadow(0 0 ${20 * echoGain}px #ff007f)`,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                {/* Stylized Happy Poodle SVG */}
                <svg width="220" height="220" viewBox="0 0 200 200">
                  {/* Fluffy Curly Body */}
                  <circle cx="100" cy="120" r="45" fill="#ffffff" stroke="#ff007f" strokeWidth="4" />
                  <circle cx="70" cy="110" r="25" fill="#ffffff" />
                  <circle cx="130" cy="110" r="25" fill="#ffffff" />
                  <circle cx="85" cy="145" r="20" fill="#ffffff" />
                  <circle cx="115" cy="145" r="20" fill="#ffffff" />
                  {/* Fluffy Head */}
                  <circle cx="100" cy="65" r="35" fill="#ffffff" stroke="#ff007f" strokeWidth="4" />
                  <circle cx="80" cy="45" r="20" fill="#ffffff" />
                  <circle cx="120" cy="45" r="20" fill="#ffffff" />
                  <circle cx="100" cy="35" r="22" fill="#ffffff" />
                  {/* Floppy Ears */}
                  <ellipse cx="65" cy="70" rx="16" ry="32" fill="#ffb6c1" stroke="#ff007f" strokeWidth="3" />
                  <ellipse cx="135" cy="70" rx="16" ry="32" fill="#ffb6c1" stroke="#ff007f" strokeWidth="3" />
                  {/* Party Sunglasses */}
                  <rect x="75" y="55" width="22" height="15" rx="4" fill="#111" stroke="#00f0ff" strokeWidth="3" />
                  <rect x="103" y="55" width="22" height="15" rx="4" fill="#111" stroke="#00f0ff" strokeWidth="3" />
                  <line x1="97" y1="62" x2="103" y2="62" stroke="#00f0ff" strokeWidth="3" />
                  {/* Happy Tongue */}
                  <ellipse cx="100" cy="85" rx="8" ry="12" fill="#ff1493" />
                  {/* Wagging Tail with Puff */}
                  <circle cx="160" cy="95" r="18" fill="#ffffff" stroke="#ff007f" strokeWidth="3" />
                </svg>
                <div
                  style={{
                    color: "#ff007f",
                    fontSize: 26,
                    fontWeight: 900,
                    textShadow: "0 0 10px #ff007f",
                  }}
                >
                  ¡GUAU! (3/16 DUB DELAY)
                </div>
              </div>
            );
          })}
        </AbsoluteFill>
      )}

      {/* 7. TEETH CHATTERING BITING VISUALIZER (HIGH FREQUENCIES) */}
      {high > 0.4 && (
        <div
          style={{
            position: "absolute",
            top: 140,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 18,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <div
            style={{
              color: "#00f0ff",
              fontSize: 18,
              letterSpacing: 4,
              marginBottom: 6,
              textShadow: "0 0 10px #00f0ff",
            }}
          >
            [CHASQUIDO DE DIENTES · 7.6 kHz]
          </div>
          {/* Top teeth */}
          <div style={{ display: "flex", gap: 6, transform: `translateY(${high * 8}px)` }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: 18,
                  height: 24,
                  backgroundColor: "#ffffff",
                  borderRadius: "2px 2px 8px 8px",
                  boxShadow: "0 0 10px #00f0ff",
                }}
              />
            ))}
          </div>
          {/* Bottom teeth */}
          <div style={{ display: "flex", gap: 6, marginTop: 4, transform: `translateY(${-high * 8}px)` }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: 18,
                  height: 24,
                  backgroundColor: "#ffffff",
                  borderRadius: "8px 8px 2px 2px",
                  boxShadow: "0 0 10px #00f0ff",
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* 8. KINETIC TYPOGRAPHY & LIBRETTO DISPLAY */}
      <div
        style={{
          position: "absolute",
          bottom: 240,
          left: 0,
          right: 0,
          textAlign: "center",
          zIndex: 25,
        }}
      >
        <div
          style={{
            fontSize: 22,
            letterSpacing: 4,
            color: isAlainTalking ? "#ffd700" : (isMariLupe ? "#00f0ff" : "#ff4d6d"),
            textTransform: "uppercase",
            marginBottom: 8,
            textShadow: "0 0 10px rgba(0,0,0,0.8)",
          }}
        >
          {speaker}
        </div>
        <div
          style={{
            fontSize: isCaniche ? 64 : (isAlainTalking ? 52 : 44),
            fontWeight: 900,
            color: isNegativeHarmony ? "#0a0a0a" : "#ffffff",
            textShadow: isNegativeHarmony
              ? "0 0 25px #00f0ff"
              : "0 0 30px #ff0055, 0 0 60px #ffb703",
            transform: `scale(${1.0 + rms * 0.25})`,
            transition: "transform 0.08s ease-out",
            padding: "0 60px",
          }}
        >
          {text}
        </div>
      </div>

      {/* 9. TOP HUD: 121-AGENT SWARM METRICS */}
      <div
        style={{
          position: "absolute",
          top: 30,
          left: 40,
          right: 40,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          zIndex: 30,
          color: isNegativeHarmony ? "#111" : "#aaa",
          fontSize: 15,
          letterSpacing: 2,
          borderBottom: "1px solid rgba(255,255,255,0.2)",
          paddingBottom: 15,
        }}
      >
        <div>
          <span style={{ color: "#ffd700", fontWeight: "bold" }}>MOSKV-1 feat. ALAIN</span> · TUBA MENOR CON CHORUS & PADS
        </div>
        <div>
          MATRIZ <span style={{ color: "#00f0ff", fontWeight: "bold" }}>121 AGENTES</span> · BPM: 122 · COMPÁS: {bar}/68
        </div>
        <div>
          EBU R128: <span style={{ color: "#39ff14", fontWeight: "bold" }}>-14.0 LUFS</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
