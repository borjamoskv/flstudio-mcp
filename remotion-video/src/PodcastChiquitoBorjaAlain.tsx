import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import podcastData from "../public/chiquito_podcast_data.json";

export const PodcastChiquitoBorjaAlain: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Clamp frame to precomputed audio & mouth flap data
  const frameIdx = Math.min(frame, podcastData.frames.length - 1);
  const data = podcastData.frames[frameIdx] || {
    rms: 0,
    activeSpeaker: "none",
    speakerName: "",
    alainTalking: false,
    alainFlapGap: 0,
    borjaTalking: false,
    borjaFlapGap: 0,
    text: "",
  };

  const {
    rms,
    activeSpeaker,
    speakerName,
    alainTalking,
    alainFlapGap,
    borjaTalking,
    borjaFlapGap,
    text,
  } = data;

  // Paper cut-out animation wobbles
  const alainWobble = Math.sin(frame * 0.45) * 0.8 + (alainTalking ? Math.sin(frame * 1.2) * 1.5 : 0);
  const borjaWobble = Math.sin(frame * 0.35) * 0.7 + (borjaTalking ? Math.sin(frame * 1.4) * 2.0 : 0);
  
  // Chiquito gesture / bodily accent on punchlines when Borja talks
  const borjaBob = borjaTalking ? Math.abs(Math.sin(frame * 0.6)) * 8 : 0;
  const alainBob = alainTalking ? Math.abs(Math.sin(frame * 0.5)) * 6 : 0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#d2e6f5",
        overflow: "hidden",
        fontFamily: "'Comic Sans MS', 'Chalkboard SE', 'Arial Black', sans-serif",
      }}
    >
      {/* 1. MASTER AUDIO TRACK */}
      <Audio src={staticFile("chiquito_podcast_audio.mp3")} />

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

        {/* Studio Wall Banner */}
        <div
          style={{
            position: "absolute",
            top: 135,
            left: "50%",
            transform: "translateX(-50%)",
            textAlign: "center",
            zIndex: 5,
            backgroundColor: "rgba(18, 22, 32, 0.92)",
            padding: "12px 36px",
            borderRadius: 16,
            border: "4px solid #f6c83b",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.6)",
          }}
        >
          <div
            style={{
              fontSize: 36,
              fontWeight: 900,
              color: "#ffffff",
              letterSpacing: "0.08em",
              textShadow: "3px 3px 0 #000, -2px -2px 0 #000",
            }}
          >
            CORTEZAS Y CONCERTAS
          </div>
          <div
            style={{
              fontSize: 20,
              fontWeight: 800,
              color: "#00f0ff",
              marginTop: 4,
              letterSpacing: "0.05em",
              textShadow: "1px 1px 0 #000",
            }}
          >
            BORJA MOSKV feat. ALAIN ELEKTRONISCHE · EDICIÓN KREMLIN
          </div>
        </div>
      </AbsoluteFill>

      {/* 3. CHARACTERS BEHIND DESK */}

      {/* LEFT CHARACTER: BORJA MOSKV (HOST / MODO SOUTH PARK / CHIQUITO) */}
      <div
        style={{
          position: "absolute",
          left: 190,
          bottom: 180 - borjaBob,
          width: 440,
          height: 620,
          zIndex: 15,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: `rotate(${borjaWobble}deg)`,
          transformOrigin: "bottom center",
          transition: "transform 0.05s ease-out",
        }}
      >
        {/* BORJA FLAP-MOUTH HEAD ASSEMBLY */}
        <div
          style={{
            position: "relative",
            width: 380,
            height: 250,
            zIndex: 10,
            filter: "drop-shadow(0 14px 22px rgba(0, 0, 0, 0.45))",
          }}
        >
          {/* A. Dark Mouth Cavity with Tongue */}
          <div
            style={{
              position: "absolute",
              top: 160,
              left: 135,
              width: 110,
              height: 55,
              backgroundColor: "#180505",
              borderRadius: "50%",
              zIndex: 0,
              overflow: "hidden",
              border: "3px solid #000000",
            }}
          >
            <div
              style={{
                position: "absolute",
                bottom: 2,
                left: 25,
                width: 60,
                height: 30,
                backgroundColor: "#ff3366",
                borderRadius: "50%",
                border: "2px solid #880e28",
              }}
            />
          </div>

          {/* B. Borja Lower Jaw (Fixed base of head) */}
          <Img
            src={staticFile("sp_borja_head_jaw.png")}
            style={{
              position: "absolute",
              top: 195,
              left: 0,
              width: "100%",
              height: "auto",
              zIndex: 5,
            }}
          />

          {/* C. Borja Upper Head (Flaps up on speech RMS) */}
          <Img
            src={staticFile("sp_borja_head_top.png")}
            style={{
              position: "absolute",
              top: -borjaFlapGap,
              left: 0,
              width: "100%",
              height: "auto",
              zIndex: 10,
              transformOrigin: "bottom left",
              transform: `rotate(${borjaFlapGap * 0.35}deg)`,
            }}
          />
        </div>

        {/* D. Borja Body */}
        <div
          style={{
            position: "relative",
            width: 440,
            zIndex: 1,
            marginTop: -35,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <Img
            src={staticFile("sp_borja_body.png")}
            style={{
              width: "100%",
              height: "auto",
              filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.4))",
            }}
          />
        </div>

        {/* Borja Moskv Name Badge */}
        <div
          style={{
            position: "absolute",
            bottom: -22,
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: borjaTalking ? "#00f0ff" : "#1a1d26",
            color: borjaTalking ? "#000000" : "#ffffff",
            padding: "8px 20px",
            borderRadius: 10,
            border: "3px solid #00f0ff",
            fontSize: 18,
            fontWeight: 900,
            whiteSpace: "nowrap",
            boxShadow: borjaTalking
              ? "0 0 25px rgba(0, 240, 255, 0.8), 0 5px 15px rgba(0,0,0,0.5)"
              : "0 4px 12px rgba(0,0,0,0.5)",
            transition: "all 0.1s ease",
          }}
        >
          🎙️ BORJA MOSKV (HOST)
        </div>
      </div>

      {/* RIGHT CHARACTER: ALAIN ELEKTRONISCHE (SOUTH PARK FLAP-MOUTH) */}
      <div
        style={{
          position: "absolute",
          right: 190,
          bottom: 180 - alainBob,
          width: 440,
          height: 620,
          zIndex: 15,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: `rotate(${alainWobble}deg)`,
          transformOrigin: "bottom center",
          transition: "transform 0.05s ease-out",
        }}
      >
        {/* ALAIN FLAP-MOUTH HEAD ASSEMBLY */}
        <div
          style={{
            position: "relative",
            width: 380,
            height: 250,
            zIndex: 10,
            filter: "drop-shadow(0 14px 22px rgba(0, 0, 0, 0.45))",
          }}
        >
          {/* A. Dark Mouth Cavity with Tongue */}
          <div
            style={{
              position: "absolute",
              top: 160,
              left: 135,
              width: 110,
              height: 55,
              backgroundColor: "#180505",
              borderRadius: "50%",
              zIndex: 0,
              overflow: "hidden",
              border: "3px solid #000000",
            }}
          >
            <div
              style={{
                position: "absolute",
                bottom: 2,
                left: 25,
                width: 60,
                height: 30,
                backgroundColor: "#ff4d6d",
                borderRadius: "50%",
                border: "2px solid #991b35",
              }}
            />
          </div>

          {/* B. Alain Lower Jaw */}
          <Img
            src={staticFile("sp_alain_head_jaw.png")}
            style={{
              position: "absolute",
              top: 195,
              left: 0,
              width: "100%",
              height: "auto",
              zIndex: 5,
            }}
          />

          {/* C. Alain Upper Head (Flaps up on speech RMS) */}
          <Img
            src={staticFile("sp_alain_head_top.png")}
            style={{
              position: "absolute",
              top: -alainFlapGap,
              left: 0,
              width: "100%",
              height: "auto",
              zIndex: 10,
              transformOrigin: "bottom right",
              transform: `rotate(${-alainFlapGap * 0.35}deg)`,
            }}
          />
        </div>

        {/* D. Alain Torso (Sitting behind desk) */}
        <div
          style={{
            position: "relative",
            width: 440,
            zIndex: 1,
            marginTop: -35,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <Img
            src={staticFile("sp_alain_torso.png")}
            style={{
              width: "100%",
              height: "auto",
              filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.4))",
            }}
          />
        </div>

        {/* Alain Name Badge */}
        <div
          style={{
            position: "absolute",
            bottom: -22,
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: alainTalking ? "#f6c83b" : "#1a1d26",
            color: alainTalking ? "#000000" : "#ffffff",
            padding: "8px 20px",
            borderRadius: 10,
            border: "3px solid #f6c83b",
            fontSize: 18,
            fontWeight: 900,
            whiteSpace: "nowrap",
            boxShadow: alainTalking
              ? "0 0 25px rgba(246, 200, 59, 0.8), 0 5px 15px rgba(0,0,0,0.5)"
              : "0 4px 12px rgba(0,0,0,0.5)",
            transition: "all 0.1s ease",
          }}
        >
          🎧 ALAIN ELEKTRONISCHE (INVITADO)
        </div>
      </div>

      {/* 4. FOREGROUND: DESK, MICS & HILARIOUS PROPS */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: 1920,
          height: 380,
          zIndex: 25,
          pointerEvents: "none",
        }}
      >
        <Img
          src={staticFile("sp_desk_mics.png")}
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
            filter: "drop-shadow(0 -8px 15px rgba(0,0,0,0.3))",
          }}
        />

        {/* PROP 1: CONCERTA BOTTLE ON ALAIN'S SIDE */}
        <div
          style={{
            position: "absolute",
            bottom: 135,
            right: 490,
            width: 95,
            transform: "rotate(6deg)",
            filter: "drop-shadow(0 8px 12px rgba(0,0,0,0.5))",
          }}
        >
          <Img src={staticFile("sp_prop_concerta.png")} style={{ width: "100%" }} />
        </div>

        {/* PROP 2: KREMLIN SPIZ BAGGIE ON DESK */}
        <div
          style={{
            position: "absolute",
            bottom: 125,
            left: "50%",
            transform: "translateX(-50%) rotate(-4deg)",
            width: 105,
            filter: "drop-shadow(0 8px 12px rgba(0,0,0,0.5))",
          }}
        >
          <Img src={staticFile("sp_prop_spiz.png")} style={{ width: "100%" }} />
        </div>

        {/* PROP 3: BORJA'S COFFEE MUG (C5 / MOSKV-1) */}
        <div
          style={{
            position: "absolute",
            bottom: 135,
            left: 490,
            backgroundColor: "#202025",
            border: "3px solid #00f0ff",
            borderRadius: "6px 6px 14px 14px",
            padding: "6px 16px",
            color: "#ffffff",
            fontWeight: 900,
            fontSize: 18,
            transform: "rotate(-8deg)",
            boxShadow: "0 8px 15px rgba(0,0,0,0.5)",
          }}
        >
          ⚡ MOSKV-1
        </div>
      </div>

      {/* 5. SUBTITLE / LOWER-THIRD BROADCAST BANNER */}
      {text && (
        <div
          style={{
            position: "absolute",
            bottom: 35,
            left: "50%",
            transform: "translateX(-50%)",
            width: 1550,
            backgroundColor: "rgba(10, 14, 22, 0.94)",
            border: `4px solid ${activeSpeaker === "borja" ? "#00f0ff" : "#f6c83b"}`,
            borderRadius: 20,
            padding: "16px 32px",
            boxShadow: `0 12px 35px rgba(0, 0, 0, 0.75), 0 0 30px ${
              activeSpeaker === "borja" ? "rgba(0, 240, 255, 0.4)" : "rgba(246, 200, 59, 0.4)"
            }`,
            zIndex: 40,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 20,
              fontWeight: 900,
              color: activeSpeaker === "borja" ? "#00f0ff" : "#f6c83b",
              letterSpacing: "0.1em",
              marginBottom: 6,
              textTransform: "uppercase",
            }}
          >
            {activeSpeaker === "borja" ? "🎙️ BORJA MOSKV (EXPLICACIÓN C5-REAL)" : "🎧 ALAIN ELEKTRONISCHE (SENSACIÓN REAL)"}
          </div>
          <div
            style={{
              fontSize: 27,
              fontWeight: 800,
              color: "#ffffff",
              lineHeight: 1.35,
              textShadow: "2px 2px 0 #000, -1px -1px 0 #000",
            }}
          >
            «{text}»
          </div>
        </div>
      )}

      {/* 6. TOP REC STATUS BADGE */}
      <div
        style={{
          position: "absolute",
          top: 30,
          left: 40,
          display: "flex",
          alignItems: "center",
          gap: 12,
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          padding: "8px 18px",
          borderRadius: 25,
          border: "2px solid rgba(255, 255, 255, 0.2)",
          zIndex: 50,
        }}
      >
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: "50%",
            backgroundColor: "#ff3333",
            boxShadow: Math.sin(frame * 0.1) > 0 ? "0 0 12px #ff3333" : "none",
          }}
        />
        <span
          style={{
            color: "#ffffff",
            fontSize: 16,
            fontWeight: 800,
            letterSpacing: "0.08em",
          }}
        >
          REC · EPISODIO #01
        </span>
      </div>

      <div
        style={{
          position: "absolute",
          top: 30,
          right: 40,
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          padding: "8px 18px",
          borderRadius: 25,
          border: "2px solid #00f0ff",
          color: "#00f0ff",
          fontSize: 16,
          fontWeight: 900,
          zIndex: 50,
          letterSpacing: "0.08em",
        }}
      >
        C5-REAL BROADCAST
      </div>
    </AbsoluteFill>
  );
};
