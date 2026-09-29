import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import telemetry from "../public/universal_video_telemetry.json";

interface CharConfig {
  top: string;
  jaw: string;
  body: string;
  name: string;
  color: string;
}

const CHARACTERS: Record<string, CharConfig> = {
  alain: {
    top: "sp_alain_head_top.png",
    jaw: "sp_alain_head_jaw.png",
    body: "sp_alain_seated_body.png",
    name: "ALAIN ELEKTRONISCHE",
    color: "#00ffcc",
  },
  borja: {
    top: "faces/borja_hd_top.png",
    jaw: "faces/borja_hd_jaw.png",
    body: "sp_borja_body.png",
    name: "BORJA MOSKV",
    color: "#00f0ff",
  },
  chiquito: {
    top: "faces/chiquito_top.png",
    jaw: "faces/chiquito_jaw.png",
    body: "sp_hawaiian_body.png",
    name: "CHIQUITO DE LA CALZADA",
    color: "#ffea00",
  },
  echenique: {
    top: "faces/echenique_top.png",
    jaw: "faces/echenique_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "ECHENIQUE CYBER-RACER",
    color: "#ff007f",
  },
  eddie_fenwick: {
    top: "faces/eddie_fenwick_top.png",
    jaw: "faces/eddie_fenwick_jaw.png",
    body: "sp_suit_navy.png",
    name: "EDDIE FENWICK",
    color: "#ff9900",
  },
  elon_musk: {
    top: "faces/elon_musk_top.png",
    jaw: "faces/elon_musk_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "ELON MUSK",
    color: "#ffffff",
  },
  escohotado: {
    top: "faces/escohotado_top.png",
    jaw: "faces/escohotado_jaw.png",
    body: "sp_hawaiian_body.png",
    name: "ANTONIO ESCOHOTADO",
    color: "#a3e635",
  },
  fernan_gomez: {
    top: "faces/fernan_gomez_top.png",
    jaw: "faces/fernan_gomez_jaw.png",
    body: "sp_suit_black.png",
    name: "FERNANDO FERNÁN GÓMEZ",
    color: "#f87171",
  },
  inspector_hacienda: {
    top: "faces/inspector_hacienda_top.png",
    jaw: "faces/inspector_hacienda_jaw.png",
    body: "sp_suit_black.png",
    name: "INSPECTOR HACIENDA (AEAT)",
    color: "#ef4444",
  },
  julio_iglesias: {
    top: "faces/julio_iglesias_top.png",
    jaw: "faces/julio_iglesias_jaw.png",
    body: "sp_suit_white.png",
    name: "JULIO IGLESIAS",
    color: "#fbbf24",
  },
  lander: {
    top: "faces/lander_southpark_head_top.png",
    jaw: "faces/lander_southpark_head_jaw.png",
    body: "sp_lander_seated_body.png",
    name: "LANDER (EL MINERO)",
    color: "#38bdf8",
  },
  luengo: {
    top: "faces/luengo_tigre_top.png",
    jaw: "faces/luengo_tigre_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "LUENGO (TIGRE MÁQUINA)",
    color: "#f97316",
  },
  mitxu: {
    top: "faces/mitxu_top.png",
    jaw: "faces/mitxu_jaw.png",
    body: "sp_mitxu_seated_body.png",
    name: "MITXU (EL FILÓSOFO)",
    color: "#c084fc",
  },
  moskv1: {
    top: "faces/moskv1_top.png",
    jaw: "faces/moskv1_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "MOSKV-1 HYPERVISOR",
    color: "#00ffff",
  },
  nacho: {
    top: "faces/nacho_top.png",
    jaw: "faces/nacho_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "NACHO ZURITA (POIO)",
    color: "#ec4899",
  },
  pedro_sanchez: {
    top: "faces/pedro_sanchez_top.png",
    jaw: "faces/pedro_sanchez_jaw.png",
    body: "sp_suit_black.png",
    name: "PEDRO SÁNCHEZ",
    color: "#e11d48",
  },
  rajoy: {
    top: "faces/rajoy_top.png",
    jaw: "faces/rajoy_jaw.png",
    body: "sp_suit_navy.png",
    name: "MARIANO RAJOY",
    color: "#3b82f6",
  },
  sam_altman: {
    top: "faces/sam_altman_top.png",
    jaw: "faces/sam_altman_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "SAM ALTMAN",
    color: "#10b981",
  },
  tati_centollo: {
    top: "faces/tati_centollo_top.png",
    jaw: "faces/tati_centollo_jaw.png",
    body: "sp_hawaiian_body.png",
    name: "TATI CENTOLLO",
    color: "#f43f5e",
  },
  torrente: {
    top: "faces/torrente_top.png",
    jaw: "faces/torrente_jaw.png",
    body: "sp_hawaiian_body.png",
    name: "JOSÉ LUIS TORRENTE",
    color: "#84cc16",
  },
  xabi: {
    top: "faces/xabi_top.png",
    jaw: "faces/xabi_jaw.png",
    body: "sp_suit_navy.png",
    name: "XABI CABEZA GIGANTE",
    color: "#818cf8",
  },
  mer: {
    top: "faces/mer_top.png",
    jaw: "faces/mer_jaw.png",
    body: "sp_mer_seated_body.png",
    name: "MER (MARIO SÁNCHEZ)",
    color: "#10b981",
  },
  karletes: {
    top: "faces/karletes_top.png",
    jaw: "faces/karletes_jaw.png",
    body: "sp_hawaiian_body.png",
    name: "KARLETES",
    color: "#f59e0b",
  },
  otegui: {
    top: "faces/otegui_top.png",
    jaw: "faces/otegui_jaw.png",
    body: "sp_suit_navy.png",
    name: "GORKA OTEGUI (BUSCA)",
    color: "#94a3b8",
  },
  patxi: {
    top: "faces/lander_southpark_head_top.png",
    jaw: "faces/lander_southpark_head_jaw.png",
    body: "sp_hawaiian_body.png",
    name: "PATXI URIBARRI",
    color: "#0284c7",
  },
  hugo: {
    top: "faces/sam_altman_top.png",
    jaw: "faces/sam_altman_jaw.png",
    body: "sp_suit_navy.png",
    name: "HUGO (MY PINK FRIEND)",
    color: "#ec4899",
  },
  kapi: {
    top: "faces/chiquito_top.png",
    jaw: "faces/chiquito_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "KAPI (CON K)",
    color: "#eab308",
  },
  eder: {
    top: "faces/eddie_fenwick_top.png",
    jaw: "faces/eddie_fenwick_jaw.png",
    body: "sp_suit_black.png",
    name: "EDER",
    color: "#8b5cf6",
  },
  xabi_monas: {
    top: "faces/nacho_top.png",
    jaw: "faces/nacho_jaw.png",
    body: "sp_cyber_hoodie.png",
    name: "XABI MOÑAS",
    color: "#06b6d4",
  },
  tosso: {
    top: "faces/mer_top.png",
    jaw: "faces/mer_jaw.png",
    body: "sp_mer_seated_body.png",
    name: "TOSSO (ATHLETIC)",
    color: "#dc2626",
  },
};

const SouthParkCharacter: React.FC<{
  charKey: string;
  isLeft: boolean;
  isTalking: boolean;
  flapGap: number;
  rms: number;
  wobble: number;
}> = ({ charKey, isLeft, isTalking, flapGap, rms, wobble }) => {
  const cfg = CHARACTERS[charKey] || CHARACTERS.borja;

  const mouthOpen = isTalking && flapGap > 1.5;
  const effectiveGap = isTalking ? Math.min(26, flapGap * 1.8) : 0;

  return (
    <div
      style={{
        position: "absolute",
        left: isLeft ? 150 : undefined,
        right: !isLeft ? 150 : undefined,
        bottom: 85,
        width: 440,
        zIndex: 15,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        transform: `rotate(${wobble}deg) scale(${isTalking ? 1.02 : 1.0})`,
        transformOrigin: "bottom center",
        transition: "transform 0.05s ease-out",
      }}
    >
      {/* Head Assembly */}
      <div
        style={{
          position: "relative",
          width: 380,
          height: 310,
          zIndex: 10,
          filter: "drop-shadow(0 14px 22px rgba(0, 0, 0, 0.45))",
        }}
      >
        {/* Mouth cavity behind cutouts */}
        {mouthOpen && (
          <div
            style={{
              position: "absolute",
              top: 170,
              left: 70,
              width: 240,
              height: 70,
              backgroundColor: "#180303",
              borderRadius: "40px",
              zIndex: 1,
              overflow: "hidden",
              border: "3px solid #000000",
            }}
          >
            {/* Tongue */}
            <div
              style={{
                position: "absolute",
                bottom: 2,
                left: 85,
                width: 70,
                height: 35,
                backgroundColor: "#ff4d6d",
                borderRadius: "50%",
                border: "2px solid #991b35",
              }}
            />
          </div>
        )}

        {/* Lower Jaw (Anchored base) */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            zIndex: 4,
          }}
        >
          <Img
            src={staticFile(cfg.jaw)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
            }}
          />
        </div>

        {/* Upper Head (Flaps up on speech RMS) */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            zIndex: 6,
            transformOrigin: isLeft ? "bottom right" : "bottom left",
            transform: `translateY(${-effectiveGap}px) rotate(${
              isLeft ? -effectiveGap * 0.4 : effectiveGap * 0.4
            }deg)`,
            transition: "transform 0.04s ease-out",
          }}
        >
          <Img
            src={staticFile(cfg.top)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
            }}
          />
        </div>
      </div>

      {/* Torso / Body */}
      <div
        style={{
          position: "relative",
          width: 440,
          zIndex: 1,
          marginTop: -60,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Img
          src={staticFile(cfg.body)}
          style={{
            width: "100%",
            height: "auto",
            filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.35))",
          }}
        />
      </div>
    </div>
  );
};

export const UniversalSouthParkVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const safeFrame = Math.min(frame, telemetry.frames.length - 1);
  const frameData = telemetry.frames[safeFrame] || {
    r: 0,
    g: 0,
    t: 0,
    b: [0, 0, 0, 0, 0, 0, 0, 0],
  };

  // Find active scene by frame bounds or fallback to index
  const activeScene =
    telemetry.scenes.find(
      (s: any) =>
        s.startFrame !== undefined &&
        safeFrame >= s.startFrame &&
        safeFrame <= s.endFrame
    ) ||
    telemetry.scenes[
      Math.min(
        Math.floor((safeFrame / telemetry.frames.length) * telemetry.scenes.length),
        telemetry.scenes.length - 1
      )
    ];

  const speaker = activeScene.speaker || "borja";
  const guest = activeScene.guest || "alain";
  const isTalking = frameData.t === 1;
  const rms = frameData.r;
  const flapGap = frameData.g;

  // Pairing: Left vs Right
  let charLeft = "borja";
  let charRight = guest;

  if (speaker === "borja" || guest === "borja") {
    charLeft = "borja";
    charRight = speaker === "borja" ? guest : speaker;
  } else {
    charLeft = guest;
    charRight = speaker;
  }

  const leftTalking = isTalking && speaker === charLeft;
  const rightTalking = isTalking && speaker === charRight;

  const leftCfg = CHARACTERS[charLeft] || CHARACTERS.borja;
  const rightCfg = CHARACTERS[charRight] || CHARACTERS.alain;
  const speakerCfg = CHARACTERS[speaker] || leftCfg;

  const leftWobble = leftTalking
    ? Math.sin(frame * 0.8) * 3.2
    : Math.sin(frame * 0.2) * 1.0;
  const rightWobble = rightTalking
    ? Math.sin(frame * 0.8) * 3.2
    : Math.cos(frame * 0.22) * 1.0;

  const title = telemetry.metadata.title || "JARANA CAST // SOUTH PARK";
  const subtitle =
    telemetry.metadata.subtitle || "BILBAO SOTA // 3 A 4 MINUTOS DE DELIRIO";
  const audioFile = telemetry.metadata.audioFile || "universal_video_master.mp3";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#9cc4e4",
        overflow: "hidden",
        fontFamily:
          "'Comic Sans MS', 'Chalkboard SE', 'Arial Black', sans-serif",
      }}
    >
      {/* 1. MASTER AUDIO TRACK */}
      <Audio src={staticFile(audioFile)} />

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

        {/* Top Studio Sign Banner */}
        <div
          style={{
            position: "absolute",
            top: 25,
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
              textShadow:
                "4px 4px 0 #000, -4px -4px 0 #000, 4px -4px 0 #000, -4px 4px 0 #000",
            }}
          >
            {title}
          </div>
          <div
            style={{
              display: "inline-block",
              marginTop: 4,
              backgroundColor: "rgba(0, 0, 0, 0.75)",
              padding: "4px 18px",
              borderRadius: 20,
              border: "2px solid #ffee55",
              fontSize: 16,
              fontWeight: 800,
              color: "#ffee55",
              letterSpacing: "0.04em",
            }}
          >
            {subtitle}
          </div>
        </div>

        {/* Center Studio CRT Monitor (Dynamic Evidence Display) */}
        <div
          style={{
            position: "absolute",
            top: 510,
            left: "50%",
            transform: "translateX(-50%)",
            width: 480,
            height: 190,
            backgroundColor: "#101216",
            border: "5px solid #2d303a",
            borderRadius: 12,
            overflow: "hidden",
            boxShadow:
              "0 12px 30px rgba(0,0,0,0.65), inset 0 0 15px rgba(0,0,0,0.8)",
            zIndex: 8,
          }}
        >
          <Img
            src={staticFile(
              `monitor_slides/${(activeScene as any).slide || "bar.jpg"}`
            )}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              filter: "contrast(1.08) brightness(0.96)",
            }}
          />
          {/* CRT Scanline overlay */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background:
                "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.35) 50%)",
              backgroundSize: "100% 4px",
              pointerEvents: "none",
            }}
          />
          {/* Live Evidence Badge */}
          <div
            style={{
              position: "absolute",
              top: 8,
              left: 10,
              backgroundColor: "rgba(0, 0, 0, 0.85)",
              color: "#00f0ff",
              border: "1.5px solid #00f0ff",
              fontSize: 11,
              fontWeight: 900,
              padding: "2px 8px",
              borderRadius: 4,
              letterSpacing: "0.08em",
            }}
          >
            🔴 EVIDENCIA TERRITORIAL
          </div>
        </div>
      </AbsoluteFill>

      {/* 3. CHARACTERS SEATED BEHIND DESK */}
      <SouthParkCharacter
        charKey={charLeft}
        isLeft={true}
        isTalking={leftTalking}
        flapGap={flapGap}
        rms={rms}
        wobble={leftWobble}
      />

      <SouthParkCharacter
        charKey={charRight}
        isLeft={false}
        isTalking={rightTalking}
        flapGap={flapGap}
        rms={rms}
        wobble={rightWobble}
      />

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

        {/* Props on Desk */}
        {/* Left Mug */}
        <div
          style={{
            position: "absolute",
            bottom: 75,
            left: 520,
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
            boxShadow: "0 4px 8px rgba(0,0,0,0.3)",
          }}
        >
          C5
        </div>

        {/* Dynamic Center Spectrum EQ Visualizer */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            alignItems: "flex-end",
            gap: 6,
            height: 45,
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            padding: "6px 14px",
            borderRadius: 8,
            border: "2px solid #555566",
            boxShadow: "inset 0 0 10px rgba(0, 240, 255, 0.3)",
          }}
        >
          {frameData.b.map((val: number, idx: number) => {
            const h = Math.max(4, Math.min(32, val * 32));
            const barCol =
              idx < 3 ? "#00ffcc" : idx < 6 ? "#ffee00" : "#ff0055";
            return (
              <div
                key={idx}
                style={{
                  width: 8,
                  height: h,
                  backgroundColor: barCol,
                  borderRadius: 2,
                  boxShadow: `0 0 6px ${barCol}`,
                }}
              />
            );
          })}
        </div>

        {/* Right Mug / Prop */}
        <div
          style={{
            position: "absolute",
            bottom: 75,
            right: 520,
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
            boxShadow: "0 4px 8px rgba(0,0,0,0.3)",
          }}
        >
          SPIZ
        </div>

        {/* NAME BADGES MOUNTED ON DESK LIP */}
        <div
          style={{
            position: "absolute",
            bottom: 25,
            left: 240,
            backgroundColor: "#20222a",
            color: "#ffffff",
            padding: "8px 22px",
            borderRadius: 8,
            border: leftTalking
              ? `3.5px solid ${leftCfg.color}`
              : "2.5px solid #555566",
            fontSize: 16,
            fontWeight: 900,
            whiteSpace: "nowrap",
            boxShadow: leftTalking
              ? `0 0 20px ${leftCfg.color}`
              : "0 4px 10px rgba(0,0,0,0.5)",
            transition: "all 0.1s ease",
          }}
        >
          {leftTalking ? `🗣️ ${leftCfg.name}` : leftCfg.name}
        </div>

        <div
          style={{
            position: "absolute",
            bottom: 25,
            right: 240,
            backgroundColor: "#20222a",
            color: "#ffffff",
            padding: "8px 22px",
            borderRadius: 8,
            border: rightTalking
              ? `3.5px solid ${rightCfg.color}`
              : "2.5px solid #555566",
            fontSize: 16,
            fontWeight: 900,
            whiteSpace: "nowrap",
            boxShadow: rightTalking
              ? `0 0 20px ${rightCfg.color}`
              : "0 4px 10px rgba(0,0,0,0.5)",
            transition: "all 0.1s ease",
          }}
        >
          {rightTalking ? `🗣️ ${rightCfg.name}` : rightCfg.name}
        </div>
      </div>

      {/* 5. SOUTH PARK SUBTITLES BOX */}
      <div
        style={{
          position: "absolute",
          bottom: 145,
          left: 100,
          right: 100,
          textAlign: "center",
          zIndex: 40,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            display: "inline-block",
            maxWidth: "85%",
            backgroundColor: "rgba(10, 10, 15, 0.92)",
            padding: "12px 32px",
            borderRadius: 16,
            border: `3.5px solid ${speakerCfg.color}`,
            boxShadow: `0 8px 25px rgba(0,0,0,0.8), 0 0 15px ${speakerCfg.color}40`,
          }}
        >
          <div
            style={{
              fontSize: 18,
              fontWeight: 900,
              color: speakerCfg.color,
              marginBottom: 4,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}
          >
            🎙️ {speakerCfg.name}
          </div>
          <div
            style={{
              fontSize: 27,
              fontWeight: 900,
              color: "#ffffff",
              lineHeight: 1.3,
              letterSpacing: "0.02em",
              textShadow:
                "2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000",
            }}
          >
            "{activeScene.text}"
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
