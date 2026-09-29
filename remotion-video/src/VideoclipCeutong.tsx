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
import videoData from "../public/ceutong_telemetry.json";

export const VideoclipCeutong: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const frameIdx = Math.min(frame, videoData.frames.length - 1);
  const data = (videoData.frames[frameIdx] as any) || {
    rms: 0,
    sub: 0,
    mid: 0,
    high: 0,
    bands: new Array(16).fill(0),
    speaker: "none",
    text: "",
    scene: "skyline",
    borjaTalking: false,
    mitxuTalking: false,
    alainTalking: false,
    chiquitoTalking: false,
    echeniqueTalking: false,
    macgyverTalking: false,
    flapGap: 0,
    isDrop: false,
  };

  const {
    rms,
    sub,
    mid,
    high,
    bands,
    speaker,
    text,
    borjaTalking,
    mitxuTalking,
    alainTalking,
    chiquitoTalking,
    echeniqueTalking,
    macgyverTalking,
    flapGap,
    isDrop,
  } = data;

  const DROP_FRAME = videoData.metadata.dropFrame;
  const timeSec = frame / fps;

  // 100 BPM rhythm timing (1 beat = 0.60s = 18 frames)
  const BEAT_FRAMES = 18;
  const beatProgress = (frame % BEAT_FRAMES) / BEAT_FRAMES;
  const beatPulse = Math.exp(-beatProgress * 4.2);
  const kickPunch = isDrop ? beatPulse * 0.12 : beatPulse * 0.05;
  const subShake = (isDrop ? sub * 32 : sub * 14) * (frame % 2 === 0 ? 1 : -1);

  // -------------------------------------------------------------
  // DYNAMIC MULTI-ANGLE BACKGROUND STAGE SELECTION
  // -------------------------------------------------------------
  let activeBg = "bg/ceutong_skyline.jpg";
  let bgFilter = "brightness(0.85) contrast(1.18)";

  if (timeSec < 6.7) {
    // Borja part 1: Opening pitch in Ceutong skyline
    activeBg = "bg/ceutong_skyline.jpg";
  } else if (timeSec < 16.2) {
    // Borja part 2: Cyber termodinámica & cibernética
    activeBg = "bg/dj_drop_hyperspace.jpg";
    bgFilter = "brightness(0.95) contrast(1.30)";
  } else if (timeSec < 23.5) {
    // Alain part 1: Casco Viejo Bar
    activeBg = "bg/casco_viejo_bar.jpg";
    bgFilter = "brightness(0.82) contrast(1.15)";
  } else if (timeSec < 32.4) {
    // Alain part 2: BMW M3 / Hacienda
    activeBg = "bg/ceutong_skyline.jpg";
    bgFilter = "brightness(0.88) contrast(1.25)";
  } else if (timeSec < 46.0) {
    // Chiquito: Rooftop VIP Party
    activeBg = "bg/ceutong_party.jpg";
    bgFilter = `brightness(${0.85 + beatPulse * 0.25}) contrast(1.25)`;
  } else if (timeSec < 60.0) {
    // Echenique: Retro CRT / Cyber Highway
    activeBg = "bg/retro_rave_crt.jpg";
    bgFilter = "brightness(0.92) contrast(1.35)";
  } else if (timeSec < 71.1) {
    // Lander / MacGyver: Casco Viejo Terrace / Zorroza
    activeBg = "bg/casco_viejo_terrace.jpg";
    bgFilter = "brightness(0.82) contrast(1.18)";
  } else if (timeSec < 85.0) {
    // Mitxu part 1: Legendary Gaupa 110 BPM Lasers
    activeBg = "bg/club_rave_lasers.jpg";
    bgFilter = `brightness(${0.90 + (frame % 12 < 4 ? 0.35 : 0)}) contrast(1.35)`;
  } else if (timeSec < 99.0) {
    // Mitxu part 2: Rave Crowd Hands ("¡Pásale los bombos!")
    activeBg = "bg/rave_crowd_hands.jpg";
    bgFilter = "brightness(0.88) contrast(1.28)";
  } else if (timeSec < 106.0) {
    // Borja final cue: "¡Microchip y chuletón!"
    activeBg = "bg/dj_drop_hyperspace.jpg";
    bgFilter = "brightness(1.0) contrast(1.40)";
  } else {
    // DROP CLIMAX: Multi-angle cut every 4 bars (72 frames)
    const dropCut = Math.floor((frame - DROP_FRAME) / 72) % 3;
    if (dropCut === 0) {
      activeBg = "bg/ceuton_festival_mitxu.jpg";
      bgFilter = `brightness(${0.88 + sub * 0.25}) contrast(1.22)`;
    } else if (dropCut === 1) {
      activeBg = "bg/club_rave_lasers.jpg";
      bgFilter = `brightness(${0.92 + (frame % 8 < 2 ? 0.4 : 0)}) contrast(1.35)`;
    } else {
      activeBg = "bg/dj_drop_hyperspace.jpg";
      bgFilter = "brightness(1.0) contrast(1.45)";
    }
  }

  // -------------------------------------------------------------
  // DYNAMIC CAMERA DIRECTOR
  // -------------------------------------------------------------
  let camX = 0;
  let camY = 0;
  let camZoom = 1.0 + kickPunch;
  let camRot = Math.sin(frame * 0.06) * 1.5;

  if (speaker === "borja" && timeSec < 6.7) {
    camX = -140;
    camY = -15;
    camZoom = 1.15 + kickPunch;
    camRot = -1.2;
  } else if (speaker === "borja" && timeSec >= 6.7 && timeSec < 17) {
    // Zoom in on laser eyes Borja
    camX = -80;
    camY = -25;
    camZoom = 1.25 + kickPunch * 1.4;
    camRot = Math.sin(frame * 0.15) * 2.0;
  } else if (speaker === "alain") {
    camX = 0;
    camY = 10;
    camZoom = 1.12 + kickPunch;
    camRot = 0.8;
  } else if (speaker === "chiquito") {
    camX = Math.sin(frame * 0.35) * 75;
    camY = -20 + Math.abs(Math.sin(frame * 0.5)) * 15;
    camZoom = 1.22 + kickPunch * 1.5;
    camRot = Math.sin(frame * 0.28) * 3.0;
  } else if (speaker === "echenique") {
    camX = -60 + Math.sin(frame * 0.18) * 60;
    camY = -10;
    camZoom = 1.18 + kickPunch;
    camRot = Math.cos(frame * 0.15) * 1.8;
  } else if (speaker === "macgyver") {
    camX = 120;
    camY = -15;
    camZoom = 1.18 + kickPunch;
    camRot = -1.5;
  } else if (speaker === "mitxu") {
    camX = 160 + Math.sin(frame * 0.2) * 30;
    camY = -20;
    camZoom = 1.24 + kickPunch * 1.5;
    camRot = Math.sin(frame * 0.18) * 2.5;
  } else if (isDrop) {
    camX = Math.sin(frame * 0.08) * 45;
    camY = Math.cos(frame * 0.12) * 25;
    camZoom = 1.08 + kickPunch * 1.8;
    camRot = Math.sin(frame * 0.07) * 2.2;
  }

  // Floating particles / confetti phase
  const confettiY = (frame * 12) % height;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#020617",
        overflow: "hidden",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <Audio src={staticFile("ceutong_master_audio.mp3")} />

      {/* ========================================================= */}
      {/* 1. VIRTUAL CAMERA CONTAINER                               */}
      {/* ========================================================= */}
      <AbsoluteFill
        style={{
          transform: `translate(${camX}px, ${camY + subShake}px) scale(${camZoom}) rotate(${camRot}deg)`,
          transformOrigin: "center center",
          transition: "transform 0.06s ease-out",
        }}
      >
        {/* ACTIVE DYNAMIC BACKGROUND */}
        <AbsoluteFill>
          <Img
            src={staticFile(activeBg)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${1.06 + Math.sin(frame * 0.02) * 0.03})`,
              filter: bgFilter,
              transition: "filter 0.15s ease-out",
            }}
          />
          {/* Cinematic Vignette */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "radial-gradient(circle at 50% 50%, rgba(2,6,23,0.05) 30%, rgba(2,6,23,0.88) 95%)",
            }}
          />
        </AbsoluteFill>

        {/* SWEEPING DISCO LASERS */}
        {(isDrop || speaker === "chiquito" || speaker === "mitxu" || (speaker === "borja" && timeSec >= 6.7)) && (
          <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", overflow: "hidden" }}>
            <div
              style={{
                position: "absolute",
                top: "-50%",
                left: "-50%",
                width: "200%",
                height: "200%",
                transform: `rotate(${frame * 1.8}deg)`,
                background:
                  "conic-gradient(from 0deg, transparent 0deg, rgba(56, 189, 248, 0.25) 20deg, transparent 40deg, rgba(244, 63, 94, 0.28) 90deg, transparent 110deg, rgba(250, 204, 21, 0.30) 180deg, transparent 200deg, rgba(34, 197, 94, 0.25) 270deg, transparent 290deg)",
                opacity: 0.55 + sub * 0.4,
              }}
            />
          </AbsoluteFill>
        )}

        {/* BASS SHOCKWAVE EXPANSIONS */}
        {isDrop && (
          <div
            style={{
              position: "absolute",
              top: "48%",
              left: "50%",
              transform: `translate(-50%, -50%) scale(${1.0 + beatProgress * 2.2})`,
              width: 580,
              height: 580,
              borderRadius: "50%",
              border: `6px solid rgba(56, 189, 248, ${(1.0 - beatProgress) * 0.9})`,
              boxShadow: `0 0 50px rgba(244, 63, 94, ${(1.0 - beatProgress) * 0.95})`,
              pointerEvents: "none",
            }}
          />
        )}

        {/* 16-BAND SPECTRUM VISUALIZER (BOTTOM CENTER) */}
        <div
          style={{
            position: "absolute",
            bottom: 100,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            gap: 10,
            alignItems: "flex-end",
            height: 160,
            zIndex: 10,
          }}
        >
          {bands.map((val: number, idx: number) => {
            const barH = Math.max(14, val * 155);
            const isBass = idx < 4;
            return (
              <div
                key={idx}
                style={{
                  width: 24,
                  height: barH,
                  borderRadius: "6px 6px 0 0",
                  backgroundColor: isDrop
                    ? isBass
                      ? "#f43f5e"
                      : idx < 10
                      ? "#38bdf8"
                      : "#facc15"
                    : idx < 6
                    ? "#38bdf8"
                    : "#64748b",
                  boxShadow: isDrop
                    ? `0 0 20px ${isBass ? "rgba(244, 63, 94, 0.95)" : "rgba(56, 189, 248, 0.9)"}`
                    : "0 0 8px rgba(56, 189, 248, 0.4)",
                  transition: "height 0.03s ease-out",
                }}
              />
            );
          })}
        </div>

        {/* ========================================================= */}
        {/* CHARACTER 1: BORJA MOSKV                                  */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            right: isDrop ? "14%" : "18%",
            transform: `scale(${borjaTalking ? 1.14 + Math.sin(frame * 0.4) * 0.04 : 0.96}) rotate(${borjaTalking ? Math.sin(frame * 0.25) * 3 : 0}deg)`,
            transformOrigin: "bottom center",
            zIndex: borjaTalking ? 30 : 20,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.95))",
            transition: "transform 0.08s ease-out",
          }}
        >
          {/* Speaker Badge */}
          <div
            style={{
              backgroundColor: "#0284c7",
              color: "#fff",
              padding: "6px 20px",
              borderRadius: 20,
              fontSize: 16,
              fontWeight: 900,
              marginBottom: 6,
              border: "2px solid #000",
              boxShadow: "0 0 25px rgba(2, 132, 199, 0.95)",
            }}
          >
            BORJA MOSKV 🛸
          </div>

          {/* Animated Flap-Jaw Head */}
          <div style={{ position: "relative", width: 230, height: 206 }}>
            {/* LASER EYES EFFECT (When talking about termodinámica / cibernética) */}
            {borjaTalking && timeSec >= 6.7 && timeSec < 16.2 && (
              <div style={{ position: "absolute", top: 82, left: 0, right: 0, height: 10, zIndex: 32, pointerEvents: "none" }}>
                {/* Left eye beam */}
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 87,
                    width: 480,
                    height: 8,
                    background: "linear-gradient(90deg, #f43f5e 0%, #facc15 50%, transparent 100%)",
                    transform: `rotate(${Math.sin(frame * 0.4) * 8 - 14}deg)`,
                    transformOrigin: "left center",
                    boxShadow: "0 0 25px #f43f5e, 0 0 40px #facc15",
                    borderRadius: 4,
                  }}
                />
                {/* Right eye beam */}
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 143,
                    width: 480,
                    height: 8,
                    background: "linear-gradient(90deg, #38bdf8 0%, #22c55e 50%, transparent 100%)",
                    transform: `rotate(${Math.cos(frame * 0.4) * 8 - 10}deg)`,
                    transformOrigin: "left center",
                    boxShadow: "0 0 25px #38bdf8, 0 0 40px #22c55e",
                    borderRadius: 4,
                  }}
                />
              </div>
            )}

            {/* Jaw with flapGap (rendered underneath top) */}
            <Img
              src={staticFile("faces/borja_hd_jaw.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 230,
                height: "auto",
                transform: `translateY(${borjaTalking ? flapGap * 0.75 : 0}px)`,
                zIndex: 21,
                transition: "transform 0.03s linear",
              }}
            />
            {/* Head Top with natural portrait */}
            <Img
              src={staticFile("faces/borja_hd_top.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 230,
                height: "auto",
                zIndex: 22,
              }}
            />
            {/* Thug Life / Cyber Pixel Sunglasses */}
            <Img
              src={staticFile("faces/pixel_sunglasses.png")}
              style={{
                position: "absolute",
                top: 76,
                left: 70,
                width: 96,
                height: "auto",
                zIndex: 26,
                filter: "drop-shadow(0 4px 10px rgba(0,0,0,0.85))",
              }}
            />
          </div>

          {/* Body */}
          <div
            style={{
              width: 170,
              height: 120,
              backgroundColor: "#0369a1",
              borderRadius: "45px 45px 0 0",
              border: "4px solid #000",
              marginTop: -16,
              zIndex: 19,
            }}
          />
        </div>

        {/* ========================================================= */}
        {/* CHARACTER 2: MITXU LUCHADOR (BILBAO)                      */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: isDrop ? "14%" : "18%",
            transform: `scale(${mitxuTalking ? 1.15 + Math.sin(frame * 0.4) * 0.05 : 0.96}) rotate(${mitxuTalking ? Math.cos(frame * 0.25) * 4 : 0}deg)`,
            transformOrigin: "bottom center",
            zIndex: mitxuTalking ? 30 : 20,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.95))",
            transition: "transform 0.08s ease-out",
          }}
        >
          {/* Speaker Badge */}
          <div
            style={{
              backgroundColor: "#ea580c",
              color: "#fff",
              padding: "6px 20px",
              borderRadius: 20,
              fontSize: 16,
              fontWeight: 900,
              marginBottom: 6,
              border: "2px solid #000",
              boxShadow: "0 0 25px rgba(234, 88, 12, 0.95)",
            }}
          >
            MITXU LUCHADOR 🇲🇽
          </div>

          {/* Masked Head */}
          <div style={{ position: "relative", width: 230, height: 238 }}>
            {/* Jaw underneath */}
            <Img
              src={staticFile("faces/mitxu_lucha_jaw.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 230,
                height: "auto",
                transform: `translateY(${mitxuTalking ? flapGap * 0.75 : 0}px)`,
                zIndex: 21,
                transition: "transform 0.03s linear",
              }}
            />
            {/* Mask Top */}
            <Img
              src={staticFile("faces/mitxu_lucha_top.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 230,
                height: "auto",
                zIndex: 22,
              }}
            />
          </div>

          {/* Body */}
          <div
            style={{
              width: 170,
              height: 120,
              backgroundColor: "#c2410c",
              borderRadius: "45px 45px 0 0",
              border: "4px solid #000",
              marginTop: -16,
              zIndex: 19,
            }}
          />
        </div>

        {/* ========================================================= */}
        {/* CHARACTER 3: CHIQUITO DE LA CALZADA (SPECIAL GUEST!)       */}
        {/* ========================================================= */}
        {(speaker === "chiquito" || isDrop) && (
          <div
            style={{
              position: "absolute",
              bottom: 90,
              left: isDrop
                ? `${interpolate(Math.sin(frame * 0.07), [-1, 1], [35, 65])}%`
                : "50%",
              transform: `translate(-50%, ${chiquitoTalking ? -Math.abs(Math.sin(frame * 0.5)) * 28 : 0}px) scale(${1.05 + (chiquitoTalking ? 0.12 : 0)}) rotate(${chiquitoTalking ? Math.sin(frame * 0.4) * 4 : 0}deg)`,
              zIndex: 25,
              filter: "drop-shadow(0 16px 30px rgba(250, 204, 21, 0.85))",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              transition: "transform 0.05s ease-out",
            }}
          >
            <div
              style={{
                backgroundColor: "#facc15",
                color: "#000",
                padding: "6px 20px",
                borderRadius: 20,
                fontSize: 16,
                fontWeight: 900,
                marginBottom: 6,
                border: "2px solid #000",
                boxShadow: "0 0 25px rgba(250, 204, 21, 0.95)",
              }}
            >
              CHIQUITO DE LA CALZADA 💃
            </div>
            <Img
              src={staticFile("faces/chiquito_dancer.png")}
              style={{ width: 250, height: "auto", display: "block" }}
            />
          </div>
        )}

        {/* ========================================================= */}
        {/* CHARACTER 4: ECHENIQUE CYBER-RACER (SPECIAL GUEST!)        */}
        {/* ========================================================= */}
        {(speaker === "echenique" || isDrop) && (
          <div
            style={{
              position: "absolute",
              bottom: 80,
              left: isDrop
                ? `${interpolate(Math.cos(frame * 0.06), [-1, 1], [22, 78])}%`
                : `${interpolate(Math.sin(frame * 0.12), [-1, 1], [26, 44])}%`,
              transform: `translate(-50%, 0) scale(${1.02 + (echeniqueTalking ? 0.12 : 0)}) rotate(${Math.sin(frame * 0.25) * 3}deg)`,
              zIndex: 24,
              filter: "drop-shadow(0 16px 35px rgba(56, 189, 248, 0.95))",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              transition: "transform 0.05s ease-out",
            }}
          >
            {/* Speedometer Badge */}
            <div
              style={{
                backgroundColor: "#38bdf8",
                color: "#000",
                padding: "6px 20px",
                borderRadius: 20,
                fontSize: 15,
                fontWeight: 900,
                marginBottom: 6,
                border: "2px solid #000",
                boxShadow: "0 0 25px rgba(56, 189, 248, 0.95)",
                display: "flex",
                gap: 8,
                alignItems: "center",
              }}
            >
              <span>ECHENIQUE CYBER-RACER 🏎️</span>
              <span style={{ color: "#dc2626", fontWeight: 900 }}>180 KM/H</span>
            </div>
            <Img
              src={staticFile("faces/echenique_cyber_racer.png")}
              style={{ width: 285, height: "auto", display: "block" }}
            />
          </div>
        )}

        {/* ========================================================= */}
        {/* CHARACTER 5: LANDERGROUND & MACGYVER                      */}
        {/* ========================================================= */}
        {(speaker === "macgyver" || isDrop) && (
          <div
            style={{
              position: "absolute",
              bottom: 85,
              right: isDrop ? "28%" : "30%",
              transform: `translate(50%, 0) rotate(${Math.cos(frame * 0.3) * 4}deg) scale(${1.0 + (macgyverTalking ? 0.14 : 0)})`,
              zIndex: 23,
              filter: "drop-shadow(0 16px 25px rgba(0,0,0,0.9))",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                backgroundColor: "#ef4444",
                color: "#fff",
                padding: "6px 20px",
                borderRadius: 20,
                fontSize: 15,
                fontWeight: 900,
                marginBottom: 6,
                border: "2px solid #000",
                boxShadow: "0 0 25px rgba(239, 68, 68, 0.95)",
              }}
            >
              LANDERGROUND & MACGYVER // ZORROZA 🎧🔧
            </div>
            <Img
              src={staticFile("faces/macgyver_hero.png")}
              style={{ width: 240, height: "auto", display: "block" }}
            />
          </div>
        )}
      </AbsoluteFill>

      {/* ========================================================= */}
      {/* 2. DYNAMIC KINETIC BADGES / PUNCHLINE STAMPS              */}
      {/* ========================================================= */}
      {/* Borja: TERMODINÁMICA Y CIBERNÉTICA STAMP */}
      {speaker === "borja" && timeSec >= 6.7 && timeSec < 16.2 && (
        <div
          style={{
            position: "absolute",
            top: 230,
            right: 80,
            transform: `scale(${1.0 + Math.sin(frame * 0.4) * 0.08}) rotate(${Math.sin(frame * 0.2) * 5}deg)`,
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            border: "3px solid #38bdf8",
            boxShadow: "0 0 35px rgba(56, 189, 248, 0.9)",
            borderRadius: 20,
            padding: "14px 28px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#38bdf8", fontSize: 24, fontWeight: 900 }}>⚡ JARANA CUÁNTICA</div>
          <div style={{ color: "#facc15", fontSize: 16, fontWeight: 800 }}>TERMODINÁMICA AL 100%</div>
        </div>
      )}

      {/* Alain: BMW M3 & CHULETONAS STAMP */}
      {speaker === "alain" && (
        <div
          style={{
            position: "absolute",
            top: 240,
            left: 80,
            transform: `scale(${1.0 + Math.cos(frame * 0.35) * 0.07}) rotate(${Math.cos(frame * 0.2) * 4}deg)`,
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            border: "3px solid #facc15",
            boxShadow: "0 0 35px rgba(250, 204, 21, 0.85)",
            borderRadius: 20,
            padding: "14px 28px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#facc15", fontSize: 22, fontWeight: 900 }}>🥩 CHULETONAS AUDITADAS</div>
          <div style={{ color: "#38bdf8", fontSize: 15, fontWeight: 800 }}>BMW M3 // MATERIAL DE OFICINA</div>
        </div>
      )}

      {/* Chiquito: ¡SIETE CABALLOS! STAMP */}
      {speaker === "chiquito" && (
        <div
          style={{
            position: "absolute",
            top: 220,
            right: 90,
            transform: `scale(${1.08 + Math.abs(Math.sin(frame * 0.5)) * 0.12}) rotate(${Math.sin(frame * 0.3) * 6}deg)`,
            backgroundColor: "#facc15",
            border: "4px solid #000",
            boxShadow: "0 0 40px rgba(250, 204, 21, 0.95)",
            borderRadius: 24,
            padding: "16px 32px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#000", fontSize: 26, fontWeight: 900 }}>🐴 ¡SIETE CABALLOS!</div>
          <div style={{ color: "#dc2626", fontSize: 16, fontWeight: 900 }}>¡AL ATAQUERL!</div>
        </div>
      )}

      {/* Mitxu: 110 BPM APOTEÓSICO STAMP */}
      {speaker === "mitxu" && (
        <div
          style={{
            position: "absolute",
            top: 240,
            left: 80,
            transform: `scale(${1.0 + Math.sin(frame * 0.3) * 0.08}) rotate(${Math.sin(frame * 0.25) * 5}deg)`,
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            border: "3px solid #ea580c",
            boxShadow: "0 0 35px rgba(234, 88, 12, 0.9)",
            borderRadius: 20,
            padding: "14px 28px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#ea580c", fontSize: 24, fontWeight: 900 }}>🔥 SESIÓN GAUPA: 110 BPM</div>
          <div style={{ color: "#38bdf8", fontSize: 15, fontWeight: 800 }}>¡APOTEÓSICO EN BILBAO!</div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 3. STATIC / HUD OVERLAYS                                  */}
      {/* ========================================================= */}
      {/* TOP STATUS BAR */}
      <div
        style={{
          position: "absolute",
          top: 48,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          alignItems: "center",
          gap: 16,
          zIndex: 52,
          backgroundColor: "rgba(15, 23, 42, 0.94)",
          backdropFilter: "blur(16px)",
          padding: "8px 28px",
          borderRadius: 40,
          border: isDrop ? "2px solid #facc15" : "2px solid #38bdf8",
          boxShadow: isDrop ? "0 0 30px rgba(250, 204, 21, 0.7)" : "0 10px 30px rgba(0,0,0,0.6)",
        }}
      >
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: "50%",
            backgroundColor: isDrop ? "#22c55e" : "#f59e0b",
            boxShadow: `0 0 14px ${isDrop ? "#22c55e" : "#f59e0b"}`,
          }}
        />
        <div style={{ color: "#fff", fontSize: 16, fontWeight: 900, letterSpacing: 1.5 }}>
          {isDrop
            ? "🔥 FESTIVAL CEUTÓN: DROP KATANA 100 BPM CON CHIQUITO, ECHENIQUE Y MACGYVER"
            : "🏙️ CEUTONG: EL HONG KONG DEL ESTRECHO // NEGOCIODAD 2026"}
        </div>
      </div>

      {/* AUTHENTIC WHATSAPP SUBTITLE POPUP (CENTER TOP) */}
      {text && (
        <div
          style={{
            position: "absolute",
            top: 104,
            left: "50%",
            transform: `translateX(-50%) scale(${1.0 + Math.sin(frame * 0.2) * 0.015})`,
            width: "74%",
            maxWidth: 1080,
            zIndex: 52,
            backgroundColor:
              speaker === "mitxu"
                ? "#202c33"
                : speaker === "borja"
                ? "#005c4b"
                : speaker === "chiquito"
                ? "#422006"
                : speaker === "echenique"
                ? "#082f49"
                : "#450a0a",
            border: `2.5px solid ${
              speaker === "mitxu"
                ? "#fb923c"
                : speaker === "borja"
                ? "#25d366"
                : speaker === "chiquito"
                ? "#facc15"
                : speaker === "echenique"
                ? "#38bdf8"
                : "#ef4444"
            }`,
            borderRadius: 22,
            padding: "16px 28px",
            boxShadow: "0 16px 40px rgba(0,0,0,0.9)",
          }}
        >
          <div
            style={{
              fontSize: 13,
              fontWeight: 900,
              letterSpacing: 1.5,
              color:
                speaker === "mitxu"
                  ? "#fb923c"
                  : speaker === "borja"
                  ? "#53bdeb"
                  : speaker === "chiquito"
                  ? "#facc15"
                  : speaker === "echenique"
                  ? "#38bdf8"
                  : "#f87171",
              marginBottom: 6,
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>
              💬 {speaker === "borja" && "Borja Moskv (Bilbao // Voz Real)"}
              {speaker === "mitxu" && "Mitxu (Bilbao // Voz Real)"}
              {speaker === "alain" && "Alain Electro (Nexus // Voz Real)"}
              {speaker === "chiquito" && "Chiquito de la Calzada (Málaga // ¡Fistro!)"}
              {speaker === "echenique" && "Echenique (Cyber-Tuning 180 km/h)"}
              {speaker === "macgyver" && "Landerground & MacGyver (Zorroza // Voz Real)"}
            </span>
            <span style={{ fontSize: 11, color: "#94a3b8" }}>✓✓ 100% Audio Real WhatsApp</span>
          </div>
          <div
            style={{
              fontSize: 23,
              fontWeight: 800,
              color: "#fff",
              lineHeight: 1.35,
              textShadow: "0 2px 8px rgba(0,0,0,0.85)",
            }}
          >
            {text}
          </div>
        </div>
      )}

      {/* POPUP: NEXUS CHAT SCREENSHOT CARD (When Alain speaks) */}
      {speaker === "alain" && (
        <div
          style={{
            position: "absolute",
            top: 230,
            right: 60,
            width: 380,
            zIndex: 54,
            borderRadius: 20,
            overflow: "hidden",
            border: "3px solid #38bdf8",
            boxShadow: "0 16px 40px rgba(0,0,0,0.9), 0 0 35px rgba(56, 189, 248, 0.6)",
            transform: `rotate(${Math.sin(frame * 0.15) * 2}deg) scale(${1.0 + Math.sin(frame * 0.3) * 0.03})`,
            transition: "transform 0.1s ease-out",
          }}
        >
          <Img
            src={staticFile("nexus_ceutong_chat.jpg")}
            style={{ width: "100%", height: "auto", display: "block" }}
          />
          <div
            style={{
              backgroundColor: "rgba(15, 23, 42, 0.95)",
              color: "#38bdf8",
              padding: "10px 16px",
              fontSize: 14,
              fontWeight: 900,
              textAlign: "center",
            }}
          >
            📱 NEXUS LIVE CHAT: "NEGOCIODAD : CEUTONG"
          </div>
        </div>
      )}

      {/* GIANT CENTER DROP BANNER */}
      {isDrop && frame >= DROP_FRAME && frame < DROP_FRAME + 180 && (
        <div
          style={{
            position: "absolute",
            top: "42%",
            left: "50%",
            transform: `translate(-50%, -50%) scale(${1.15 + sub * 0.18 + beatPulse * 0.08})`,
            backgroundColor: "rgba(15, 23, 42, 0.96)",
            border: "4px solid #facc15",
            boxShadow:
              "0 0 75px rgba(250, 204, 21, 0.95), 0 25px 70px rgba(0,0,0,0.95)",
            borderRadius: 30,
            padding: "24px 56px",
            zIndex: 60,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 42,
              fontWeight: 900,
              color: "#facc15",
              letterSpacing: 3,
              textShadow: "0 0 20px rgba(250, 204, 21, 0.8)",
            }}
          >
            🔊 CEUTÓN 2026 // PELOTAZO DROP 🔊
          </div>
          <div style={{ fontSize: 20, fontWeight: 900, color: "#38bdf8", marginTop: 8 }}>
            MITXU LUCHADOR + CHIQUITO + ECHENIQUE + MACGYVER @ 100 BPM
          </div>
        </div>
      )}

      {/* CINEMATIC LETTERBOX BARS (2.35:1) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 38,
          backgroundColor: "#000",
          zIndex: 50,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 38,
          backgroundColor: "#000",
          zIndex: 50,
        }}
      />

      {/* FOOTER TICKER */}
      <div
        style={{
          position: "absolute",
          bottom: 12,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 32,
          color: "#94a3b8",
          fontSize: 13,
          fontWeight: 800,
          fontFamily: "monospace",
          zIndex: 52,
        }}
      >
        <div style={{ color: "#facc15" }}>📈 CEUTONG INDEX: +340%</div>
        <div>BTC: €80,000</div>
        <div style={{ color: "#38bdf8" }}>ZONA FRANCA SHENZHEN-TETUÁN: 0% TAX</div>
        <div style={{ color: "#22c55e" }}>TEMPO: 100.0 BPM (-40 BPM)</div>
        <div style={{ color: "#f43f5e" }}>EXERGÍA: 100%</div>
      </div>
    </AbsoluteFill>
  );
};
