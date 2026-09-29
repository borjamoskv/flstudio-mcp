import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import spData from "../public/southpark_data.json";

// South Park authentic cut-out talking mouth
const SouthParkMouth: React.FC<{ isOpen: boolean; rms: number; width?: number }> = ({
  isOpen,
  rms,
  width = 36,
}) => {
  if (!isOpen) return null;
  const mouthH = Math.max(10, Math.min(28, rms * 95));
  return (
    <div
      style={{
        width,
        height: mouthH,
        backgroundColor: "#1a0505",
        borderRadius: "50%",
        border: "2.5px solid #000000",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 2px 5px rgba(0,0,0,0.5)",
      }}
    >
      {/* Upper teeth */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 4,
          right: 4,
          height: 4,
          backgroundColor: "#ffffff",
          borderRadius: "0 0 3px 3px",
        }}
      />
      {/* Tongue */}
      <div
        style={{
          position: "absolute",
          bottom: -2,
          left: "50%",
          transform: "translateX(-50%)",
          width: width * 0.55,
          height: mouthH * 0.55,
          backgroundColor: "#ff4d6d",
          borderRadius: "50%",
          border: "1.5px solid #a81d37",
        }}
      />
    </div>
  );
};

export const PodcastSouthParkAlain: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Clamp frame to precomputed data
  const frameIdx = Math.min(frame, spData.frames.length - 1);
  const data = (spData.frames[frameIdx] as any) || {
    speaker: "none",
    rms: 0,
    isTalking: false,
    flapGap: 0,
    dianaTalking: false,
    borjaTalking: false,
    text: "",
  };

  const { speaker, rms, isTalking, flapGap, dianaTalking, borjaTalking, text } = data;

  // South Park paper wobble animations
  const paperWobble = Math.sin(frame * 0.5) * 0.8;
  const borjaNod = borjaTalking
    ? Math.sin(frame * 0.8) * 3.0
    : Math.sin(frame * 0.15) * 1.2;
  const dianaWobble = dianaTalking
    ? Math.sin(frame * 0.75) * 2.5
    : Math.cos(frame * 0.18) * 1.0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#d2e6f5",
        overflow: "hidden",
        fontFamily: "'Comic Sans MS', 'Chalkboard SE', 'Arial Black', sans-serif",
      }}
    >
      {/* 1. AUDIO: BROADCAST-MASTERED VOICE ONLY (-13 LUFS, -0.5 dBFS TP) */}
      <Audio src={staticFile("southpark_audio.mp3")} />

      {/* 2. BACKGROUND: SOUTH PARK SNOWY STUDIO */}
      <AbsoluteFill>
        <Img
          src={staticFile("sp_studio_bg.png")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />

        {/* Studio Wall Banner Text (Top: 40px) */}
        <div
          style={{
            position: "absolute",
            top: 40,
            left: "50%",
            transform: "translateX(-50%)",
            textAlign: "center",
            zIndex: 5,
          }}
        >
          <div
            style={{
              fontSize: 38,
              fontWeight: 900,
              color: "#ffffff",
              letterSpacing: "0.08em",
              textShadow: "3px 3px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000",
            }}
          >
            CONCERTA CON CERDA
          </div>
          <div
            style={{
              fontSize: 19,
              fontWeight: 800,
              color: "#ffee55",
              marginTop: 4,
              textShadow: "2px 2px 0 #000, -2px -2px 0 #000",
              letterSpacing: "0.04em",
            }}
          >
            EL PODCAST · BORJA · DIANA · ALAIN ELEKTRONISCHE
          </div>
        </div>
      </AbsoluteFill>

      {/* 3. CHARACTERS SEATED BEHIND DESK */}

      {/* LEFT CHARACTER: BORJA (HOST) */}
      <div
        style={{
          position: "absolute",
          left: 140,
          bottom: 120,
          width: 360,
          height: 480,
          zIndex: 15,
          transform: `rotate(${borjaNod}deg)`,
          transformOrigin: "bottom center",
        }}
      >
        <Img
          src={staticFile("sp_borja_host.png")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.45))",
          }}
        />

        {/* Animated Mouth for Borja */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "35.4%",
            transform: "translate(-50%, -50%)",
            zIndex: 20,
          }}
        >
          <SouthParkMouth isOpen={borjaTalking} rms={rms} width={34} />
        </div>
      </div>

      {/* CENTER CHARACTER: DIANA RUIZ LORENTE (DI) */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          transform: `translateX(-50%) rotate(${dianaWobble}deg)`,
          bottom: 40,
          width: 340,
          height: 810,
          zIndex: 14,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transformOrigin: "bottom center",
        }}
      >
        <Img
          src={staticFile("sp_diana_character.png")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.4))",
          }}
        />

        {/* Animated Mouth for Diana */}
        <div
          style={{
            position: "absolute",
            left: "51.4%",
            top: "30.9%",
            transform: "translate(-50%, -50%)",
            zIndex: 20,
          }}
        >
          <SouthParkMouth isOpen={dianaTalking} rms={rms} width={38} />
        </div>
      </div>

      {/* RIGHT CHARACTER: ALAIN ELEKTRONISCHE (SOUTH PARK FLAP-MOUTH SOTA) */}
      <div
        style={{
          position: "absolute",
          right: 140,
          bottom: 90,
          width: 440,
          zIndex: 15,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: `rotate(${paperWobble}deg)`,
          transformOrigin: "bottom center",
        }}
      >
        {/* FLAP-MOUTH HEAD ASSEMBLY */}
        <div
          style={{
            position: "relative",
            width: 380,
            height: 295,
            zIndex: 10,
            filter: "drop-shadow(0 12px 20px rgba(0, 0, 0, 0.4))",
          }}
        >
          {/* A. Dark Mouth Cavity (Behind both layers, full jaw span) */}
          <div
            style={{
              position: "absolute",
              top: 195,
              left: 55,
              width: 270,
              height: 75,
              backgroundColor: "#1a0505",
              borderRadius: "40px",
              zIndex: 0,
              overflow: "hidden",
              border: "3px solid #000000",
            }}
          >
            {/* South Park Pink Tongue */}
            <div
              style={{
                position: "absolute",
                bottom: 2,
                left: 100,
                width: 70,
                height: 35,
                backgroundColor: "#ff4d6d",
                borderRadius: "50%",
                border: "2px solid #991b35",
              }}
            />
          </div>

          {/* B. Lower Jaw (Fixed base of head) */}
          <Img
            src={staticFile("sp_alain_head_jaw.png")}
            style={{
              position: "absolute",
              top: 240,
              left: 0,
              width: 380,
              height: "auto",
              zIndex: 5,
            }}
          />

          {/* C. Upper Head (Flaps up on speech RMS) */}
          <Img
            src={staticFile("sp_alain_head_top.png")}
            style={{
              position: "absolute",
              top: -flapGap,
              left: 0,
              width: 380,
              height: "auto",
              zIndex: 10,
              transformOrigin: "bottom right",
              transform: `rotate(${-flapGap * 0.35}deg)`,
            }}
          />
        </div>

        {/* D. Torso / Body (Headphones & vintage shirt, broad shoulders) */}
        <div
          style={{
            position: "relative",
            width: 440,
            zIndex: 1,
            marginTop: -55,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <Img
            src={staticFile("sp_alain_body.png")}
            style={{
              width: "100%",
              height: "auto",
              filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.35))",
            }}
          />
        </div>
      </div>

      {/* 4. FOREGROUND: PODCAST WOODEN DESK & MICS */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 320,
          zIndex: 25,
          pointerEvents: "none",
        }}
      >
        <Img
          src={staticFile("sp_desk_mics.png")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "fill",
            filter: "drop-shadow(0 -8px 20px rgba(0, 0, 0, 0.4))",
          }}
        />

        {/* Center Mic (Diana) */}
        <div
          style={{
            position: "absolute",
            bottom: 95,
            left: "50%",
            transform: "translateX(-50%)",
            width: 24,
            height: 70,
            backgroundColor: "#222222",
            border: "3px solid #000000",
            borderRadius: 6,
          }}
        />

        {/* Props on Desk */}
        {/* Left Mug (Borja) */}
        <div
          style={{
            position: "absolute",
            bottom: 75,
            left: 510,
            backgroundColor: "#ffffff",
            border: "3px solid #000000",
            borderRadius: "4px 4px 10px 10px",
            width: 48,
            height: 56,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            fontWeight: 900,
            color: "#000000",
            transform: "rotate(-4deg)",
          }}
        >
          C5
        </div>

        {/* Center Prop (Diana: Beckett Thesis Notebook) */}
        <div
          style={{
            position: "absolute",
            bottom: 70,
            left: "50%",
            transform: "translateX(-50%) rotate(3deg)",
            backgroundColor: "#d97736",
            border: "3px solid #000000",
            borderRadius: "4px 8px 8px 4px",
            padding: "8px 14px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            fontWeight: 900,
            color: "#ffffff",
            boxShadow: "0 4px 8px rgba(0,0,0,0.4)",
          }}
        >
          📖 BECKETT
        </div>

        {/* Right Mug (Alain) */}
        <div
          style={{
            position: "absolute",
            bottom: 75,
            right: 510,
            backgroundColor: "#ffe600",
            border: "3px solid #000000",
            borderRadius: "4px 4px 10px 10px",
            width: 52,
            height: 58,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 9,
            fontWeight: 900,
            color: "#000000",
            transform: "rotate(6deg)",
          }}
        >
          SPIZ
        </div>

        {/* NAME BADGES MOUNTED ON DESK LIP WITH ACTIVE TALKING GLOW */}
        {/* Badge 1: Borja */}
        <div
          style={{
            position: "absolute",
            bottom: 25,
            left: 280,
            backgroundColor: "#20222a",
            color: "#ffffff",
            padding: "6px 18px",
            borderRadius: 8,
            border: borjaTalking ? "3px solid #00f0ff" : "2px solid #555566",
            fontSize: 16,
            fontWeight: 900,
            whiteSpace: "nowrap",
            boxShadow: borjaTalking ? "0 0 15px #00f0ff" : "0 4px 10px rgba(0,0,0,0.5)",
            transition: "all 0.15s ease",
          }}
        >
          {borjaTalking ? "🗣️ BORJA (HOST)" : "BORJA (HOST)"}
        </div>

        {/* Badge 2: Diana */}
        <div
          style={{
            position: "absolute",
            bottom: 25,
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "#3d1f1f",
            color: "#ffffff",
            padding: "6px 18px",
            borderRadius: 8,
            border: dianaTalking ? "3px solid #ff9f43" : "2px solid #555566",
            fontSize: 16,
            fontWeight: 900,
            whiteSpace: "nowrap",
            boxShadow: dianaTalking ? "0 0 15px #ff9f43" : "0 4px 10px rgba(0,0,0,0.5)",
            transition: "all 0.15s ease",
          }}
        >
          {dianaTalking ? "🗣️ DIANA RUIZ LORENTE (DI)" : "DIANA RUIZ LORENTE (DI)"}
        </div>

        {/* Badge 3: Alain */}
        <div
          style={{
            position: "absolute",
            bottom: 25,
            right: 280,
            backgroundColor: "#2a1515",
            color: "#ffffff",
            padding: "6px 18px",
            borderRadius: 8,
            border: isTalking && speaker === "alain" ? "3px solid #ffd700" : "2px solid #555566",
            boxShadow:
              isTalking && speaker === "alain" ? "0 0 15px #ffd700" : "0 4px 10px rgba(0,0,0,0.5)",
            fontSize: 16,
            fontWeight: 900,
            whiteSpace: "nowrap",
            transition: "all 0.15s ease",
          }}
        >
          {isTalking && speaker === "alain" ? "🗣️ ALAIN ELEKTRONISCHE" : "ALAIN ELEKTRONISCHE"}
        </div>
      </div>

      {/* 5. SOUTH PARK COMIC SUBTITLES (ABOVE DESK) */}
      <div
        style={{
          position: "absolute",
          bottom: 145,
          left: 120,
          right: 120,
          textAlign: "center",
          zIndex: 40,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            display: "inline-block",
            backgroundColor: text ? "rgba(0, 0, 0, 0.88)" : "transparent",
            padding: text ? "10px 28px" : "0",
            borderRadius: 14,
            border: text ? "3px solid #ffee00" : "none",
            boxShadow: text ? "0 6px 20px rgba(0,0,0,0.7)" : "none",
            fontSize: 30,
            fontWeight: 900,
            color: "#fff200",
            letterSpacing: "0.02em",
            textShadow: "3px 3px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000",
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
