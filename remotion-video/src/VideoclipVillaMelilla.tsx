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
import videoData from "../public/villamelilla_telemetry.json";

export const VideoclipVillaMelilla: React.FC = () => {
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
    scene: "resort",
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
  const subShake = (isDrop ? sub * 28 : sub * 12) * (frame % 2 === 0 ? 1 : -1);

  // -------------------------------------------------------------
  // DYNAMIC MULTI-ANGLE BACKGROUND STAGE SELECTION
  // -------------------------------------------------------------
  let activeBg = "bg/villa_melilla_resort.jpg";
  let bgFilter = "brightness(0.90) contrast(1.18)";

  if (timeSec < 15.8) {
    // Alain: Villa Melilla Resort Sunset & Marina
    activeBg = "bg/villa_melilla_resort.jpg";
    bgFilter = `brightness(${0.88 + beatPulse * 0.15}) contrast(1.22)`;
  } else if (timeSec < 27.0) {
    // Borja part 1: 120 km/h en el coche de Alain / Cyber Highway
    activeBg = "bg/retro_rave_crt.jpg";
    bgFilter = "brightness(0.95) contrast(1.30)";
  } else if (timeSec < 39.2) {
    // Borja part 2: Llegada del Superyate a Villa Melilla
    activeBg = "bg/villa_melilla_yacht_party.jpg";
    bgFilter = `brightness(${0.88 + beatPulse * 0.18}) contrast(1.25)`;
  } else if (timeSec < 53.0) {
    // Chiquito: Superyacht VIP Deck Pool Party
    activeBg = "bg/villa_melilla_yacht_party.jpg";
    bgFilter = `brightness(${0.92 + (frame % 10 < 3 ? 0.35 : 0)}) contrast(1.32)`;
  } else if (timeSec < 67.0) {
    // Echenique: Floating Casino & Cyber Highway
    activeBg = "bg/retro_rave_crt.jpg";
    bgFilter = `brightness(${0.90 + beatPulse * 0.22}) contrast(1.35)`;
  } else if (timeSec < 78.0) {
    // Lander / MacGyver: Zorroza Nave & Casco Viejo Terrace
    activeBg = "bg/casco_viejo_terrace.jpg";
    bgFilter = "brightness(0.85) contrast(1.20)";
  } else if (timeSec < 100.0) {
    // Mitxu part 1: Derrick May 1999 Yacht Festival Stage
    activeBg = "bg/villa_melilla_yacht_party.jpg";
    bgFilter = `brightness(${0.90 + (frame % 12 < 4 ? 0.3 : 0)}) contrast(1.30)`;
  } else if (timeSec < 125.4) {
    // Mitxu part 2: "¡Pásale los bombos!" Rave Crowd Hands
    activeBg = "bg/rave_crowd_hands.jpg";
    bgFilter = `brightness(${0.88 + sub * 0.3}) contrast(1.30)`;
  } else if (timeSec < 132.2) {
    // Borja final cue: "¡Microchip y chuletón en Villa Melilla!" Hyperspace
    activeBg = "bg/dj_drop_hyperspace.jpg";
    bgFilter = "brightness(1.05) contrast(1.45)";
  } else {
    // DROP CLIMAX: Multi-angle cut every 4 bars (72 frames)
    const dropCut = Math.floor((frame - DROP_FRAME) / 72) % 4;
    if (dropCut === 0) {
      activeBg = "bg/villa_melilla_yacht_party.jpg";
      bgFilter = `brightness(${0.92 + sub * 0.35}) contrast(1.28)`;
    } else if (dropCut === 1) {
      activeBg = "bg/club_rave_lasers.jpg";
      bgFilter = `brightness(${0.95 + (frame % 8 < 2 ? 0.45 : 0)}) contrast(1.40)`;
    } else if (dropCut === 2) {
      activeBg = "bg/dj_drop_hyperspace.jpg";
      bgFilter = `brightness(1.08) contrast(1.50)`;
    } else {
      activeBg = "bg/rave_crowd_hands.jpg";
      bgFilter = `brightness(${0.90 + beatPulse * 0.3}) contrast(1.32)`;
    }
  }

  // -------------------------------------------------------------
  // DYNAMIC CAMERA DIRECTOR (Bounded to prevent edge cutoffs)
  // -------------------------------------------------------------
  let camX = 0;
  let camY = 0;
  let camZoom = 1.0 + kickPunch;
  let camRot = Math.sin(frame * 0.05) * 1.2;

  if (speaker === "alain") {
    camX = -65;
    camY = 5;
    camZoom = 1.12 + kickPunch;
    camRot = Math.sin(frame * 0.12) * 1.2;
  } else if (speaker === "borja" && timeSec < 27.0) {
    camX = 65;
    camY = -12;
    camZoom = 1.14 + kickPunch * 1.2;
    camRot = -1.2;
  } else if (speaker === "borja" && timeSec >= 27.0 && timeSec < 39.2) {
    camX = 55;
    camY = -15;
    camZoom = 1.16 + kickPunch * 1.3;
    camRot = Math.sin(frame * 0.15) * 1.6;
  } else if (speaker === "chiquito") {
    camX = Math.sin(frame * 0.3) * 45;
    camY = -15 + Math.abs(Math.sin(frame * 0.5)) * 14;
    camZoom = 1.20 + kickPunch * 1.4;
    camRot = Math.sin(frame * 0.25) * 2.5;
  } else if (speaker === "echenique") {
    camX = 35 + Math.sin(frame * 0.15) * 35;
    camY = -8;
    camZoom = 1.14 + kickPunch;
    camRot = Math.cos(frame * 0.15) * 1.6;
  } else if (speaker === "macgyver") {
    camX = 65;
    camY = -12;
    camZoom = 1.14 + kickPunch;
    camRot = -1.3;
  } else if (speaker === "mitxu") {
    camX = -50 + Math.sin(frame * 0.15) * 25;
    camY = -15;
    camZoom = 1.18 + kickPunch * 1.4;
    camRot = Math.sin(frame * 0.16) * 2.0;
  } else if (speaker === "borja" && timeSec >= 125.4) {
    camX = 0;
    camY = -22;
    camZoom = 1.24 + kickPunch * 1.6;
    camRot = Math.sin(frame * 0.2) * 2.2;
  } else if (isDrop) {
    camX = Math.sin(frame * 0.08) * 35;
    camY = Math.cos(frame * 0.1) * 20;
    camZoom = 1.06 + kickPunch * 1.6;
    camRot = Math.sin(frame * 0.06) * 1.8;
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#020617",
        overflow: "hidden",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <Audio src={staticFile("villamelilla_master_audio.mp3")} />

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

        {/* SWEEPING RESORT & YACHT LASERS */}
        {(isDrop || speaker === "chiquito" || speaker === "mitxu" || (speaker === "borja" && timeSec >= 125.4)) && (
          <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", overflow: "hidden" }}>
            <div
              style={{
                position: "absolute",
                top: "-50%",
                left: "-50%",
                width: "200%",
                height: "200%",
                transform: `rotate(${frame * 2.0}deg)`,
                background:
                  "conic-gradient(from 0deg, transparent 0deg, rgba(56, 189, 248, 0.3) 20deg, transparent 40deg, rgba(244, 63, 94, 0.32) 90deg, transparent 110deg, rgba(250, 204, 21, 0.35) 180deg, transparent 200deg, rgba(34, 197, 94, 0.3) 270deg, transparent 290deg)",
                opacity: 0.65 + sub * 0.45,
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
        {/* CHARACTER 1: ALAIN ELEKTROCANICHE (NEXUS SOVEREIGN)       */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: isDrop ? "10%" : "13%",
            transform: `scale(${alainTalking ? 1.14 + Math.sin(frame * 0.4) * 0.04 : 0.94}) rotate(${alainTalking ? Math.sin(frame * 0.25) * 3 : 0}deg)`,
            transformOrigin: "bottom center",
            zIndex: alainTalking ? 32 : 18,
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
              backgroundColor: "#eab308",
              color: "#000",
              padding: "6px 20px",
              borderRadius: 20,
              fontSize: 15,
              fontWeight: 900,
              marginBottom: 6,
              border: "2px solid #000",
              boxShadow: "0 0 25px rgba(234, 179, 8, 0.95)",
            }}
          >
            ALAIN ELEKTRO 🐩⚡
          </div>

          {/* Animated Flap-Jaw Head */}
          <div style={{ position: "relative", width: 220, height: 198 }}>
            {/* Dark mouth cavity behind the split */}
            <div
              style={{
                position: "absolute",
                top: 146,
                left: 62,
                width: 96,
                height: 18,
                backgroundColor: "#22080a",
                borderRadius: "0 0 8px 8px",
                zIndex: 20,
              }}
            />
            {/* Jaw with flapGap (rendered underneath top) */}
            <Img
              src={staticFile("faces/alain_jaw.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 220,
                height: "auto",
                transform: `translateY(${alainTalking ? flapGap * 0.45 : 0}px)`,
                zIndex: 21,
                transition: "transform 0.03s linear",
              }}
            />
            {/* Head Top */}
            <Img
              src={staticFile("faces/alain_top.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 220,
                height: "auto",
                zIndex: 22,
              }}
            />
          </div>

          {/* Alain Body */}
          <Img
            src={staticFile("faces/alain_electro_body.png")}
            style={{
              width: 175,
              height: "auto",
              marginTop: -18,
              zIndex: 19,
              display: "block",
            }}
          />
        </div>

        {/* ========================================================= */}
        {/* CHARACTER 2: BORJA MOSKV                                  */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            right: isDrop ? "10%" : "13%",
            transform: `scale(${borjaTalking ? 1.15 + Math.sin(frame * 0.4) * 0.04 : 0.95}) rotate(${borjaTalking ? Math.sin(frame * 0.25) * 3 : 0}deg)`,
            transformOrigin: "bottom center",
            zIndex: borjaTalking ? 32 : 19,
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
              fontSize: 15,
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
            {/* Laser eyes during high-exergy drop lines */}
            {borjaTalking && timeSec >= 125.4 && (
              <div style={{ position: "absolute", top: 82, left: 0, right: 0, height: 10, zIndex: 32, pointerEvents: "none" }}>
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
            {/* Cyber Pixel Sunglasses */}
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
        {/* CHARACTER 3: MITXU LUCHADOR (BILBAO)                      */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: isDrop ? "25%" : "28%",
            transform: `scale(${mitxuTalking ? 1.15 + Math.sin(frame * 0.4) * 0.05 : 0.94}) rotate(${mitxuTalking ? Math.cos(frame * 0.25) * 4 : 0}deg)`,
            transformOrigin: "bottom center",
            zIndex: mitxuTalking ? 31 : 20,
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
              fontSize: 15,
              fontWeight: 900,
              marginBottom: 6,
              border: "2px solid #000",
              boxShadow: "0 0 25px rgba(234, 88, 12, 0.95)",
            }}
          >
            MITXU LUCHADOR 🇲🇽
          </div>

          {/* Masked Head */}
          <div style={{ position: "relative", width: 220, height: 228 }}>
            {/* Jaw underneath */}
            <Img
              src={staticFile("faces/mitxu_lucha_jaw.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: 220,
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
                width: 220,
                height: "auto",
                zIndex: 22,
              }}
            />
          </div>

          {/* Body */}
          <div
            style={{
              width: 165,
              height: 115,
              backgroundColor: "#c2410c",
              borderRadius: "45px 45px 0 0",
              border: "4px solid #000",
              marginTop: -16,
              zIndex: 19,
            }}
          />
        </div>

        {/* ========================================================= */}
        {/* CHARACTER 4: CHIQUITO DE LA CALZADA (SPECIAL GUEST!)       */}
        {/* ========================================================= */}
        {(speaker === "chiquito" || isDrop) && (
          <div
            style={{
              position: "absolute",
              bottom: 90,
              left: isDrop
                ? `${interpolate(Math.sin(frame * 0.07), [-1, 1], [38, 58])}%`
                : "50%",
              transform: `translate(-50%, ${chiquitoTalking ? -Math.abs(Math.sin(frame * 0.5)) * 26 : 0}px) scale(${1.05 + (chiquitoTalking ? 0.12 : 0)}) rotate(${chiquitoTalking ? Math.sin(frame * 0.4) * 4 : 0}deg)`,
              zIndex: 28,
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
                fontSize: 15,
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
              style={{ width: 245, height: "auto", display: "block" }}
            />
          </div>
        )}

        {/* ========================================================= */}
        {/* CHARACTER 5: ECHENIQUE CYBER-RACER (SPECIAL GUEST!)        */}
        {/* ========================================================= */}
        {(speaker === "echenique" || isDrop) && (
          <div
            style={{
              position: "absolute",
              bottom: 80,
              left: isDrop
                ? `${interpolate(Math.cos(frame * 0.06), [-1, 1], [22, 78])}%`
                : `${interpolate(Math.sin(frame * 0.12), [-1, 1], [34, 48])}%`,
              transform: `translate(-50%, 0) scale(${1.02 + (echeniqueTalking ? 0.12 : 0)}) rotate(${Math.sin(frame * 0.25) * 3}deg)`,
              zIndex: 26,
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
              style={{ width: 275, height: "auto", display: "block" }}
            />
          </div>
        )}

        {/* ========================================================= */}
        {/* CHARACTER 6: LANDERGROUND & MACGYVER                      */}
        {/* ========================================================= */}
        {(speaker === "macgyver" || isDrop) && (
          <div
            style={{
              position: "absolute",
              bottom: 85,
              right: isDrop ? "25%" : "28%",
              transform: `translate(50%, 0) rotate(${Math.cos(frame * 0.3) * 4}deg) scale(${1.0 + (macgyverTalking ? 0.14 : 0)})`,
              zIndex: 24,
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
              style={{ width: 235, height: "auto", display: "block" }}
            />
          </div>
        )}
      </AbsoluteFill>

      {/* ========================================================= */}
      {/* 2. DYNAMIC KINETIC BADGES / PUNCHLINE STAMPS              */}
      {/* ========================================================= */}
      {/* Alain: BOT EN HACIENDA STAMP */}
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
          <div style={{ color: "#facc15", fontSize: 22, fontWeight: 900 }}>⚡ BOT EN HACIENDA</div>
          <div style={{ color: "#38bdf8", fontSize: 15, fontWeight: 800 }}>LOS REVIENTA // 0% TAX MELILLA</div>
        </div>
      )}

      {/* Borja: 120 KM/H YATE STAMP */}
      {speaker === "borja" && timeSec < 39.2 && (
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
          <div style={{ color: "#38bdf8", fontSize: 24, fontWeight: 900 }}>🚗 FELIZ A 120 KM/H</div>
          <div style={{ color: "#facc15", fontSize: 16, fontWeight: 800 }}>ATRACAMOS EL YATE EN MELILLA</div>
        </div>
      )}

      {/* Chiquito: ¡SIETE CABALLOS DE BONANZA! STAMP */}
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
          <div style={{ color: "#000", fontSize: 26, fontWeight: 900 }}>🐴 ¡SIETE CABALLOS DE BONANZA!</div>
          <div style={{ color: "#dc2626", fontSize: 16, fontWeight: 900 }}>¡AL ATAQUERL EN MELILLA!</div>
        </div>
      )}

      {/* Echenique: PLUSVALÍA TERMODINÁMICA STAMP */}
      {speaker === "echenique" && (
        <div
          style={{
            position: "absolute",
            top: 230,
            left: 90,
            transform: `scale(${1.0 + Math.sin(frame * 0.35) * 0.08}) rotate(${Math.cos(frame * 0.2) * 4}deg)`,
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            border: "3px solid #38bdf8",
            boxShadow: "0 0 35px rgba(56, 189, 248, 0.9)",
            borderRadius: 20,
            padding: "14px 28px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#38bdf8", fontSize: 22, fontWeight: 900 }}>🎰 CASINO FLOTANTE 180 KM/H</div>
          <div style={{ color: "#22c55e", fontSize: 15, fontWeight: 800 }}>MINADO BITCOIN CERO FRICCIÓN</div>
        </div>
      )}

      {/* Lander: VODAFONE SUSPENDIDO STAMP */}
      {speaker === "macgyver" && (
        <div
          style={{
            position: "absolute",
            top: 240,
            right: 80,
            transform: `scale(${1.0 + Math.cos(frame * 0.3) * 0.08}) rotate(${Math.sin(frame * 0.25) * 4}deg)`,
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            border: "3px solid #ef4444",
            boxShadow: "0 0 35px rgba(239, 68, 68, 0.9)",
            borderRadius: 20,
            padding: "14px 28px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#ef4444", fontSize: 22, fontWeight: 900 }}>📱 VODAFONE SUSPENDIDO</div>
          <div style={{ color: "#facc15", fontSize: 15, fontWeight: 800 }}>CHIP CEREBRAL ZORROZA</div>
        </div>
      )}

      {/* Mitxu: DERRICK MAY 1999 STAMP */}
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
          <div style={{ color: "#ea580c", fontSize: 24, fontWeight: 900 }}>🎧 DERRICK MAY 1999</div>
          <div style={{ color: "#38bdf8", fontSize: 15, fontWeight: 800 }}>¡YO NO VOY TRAUMADO! ¡BOMBOS!</div>
        </div>
      )}

      {/* Borja: CHULETÓN VILLA MELILLA STAMP */}
      {speaker === "borja" && timeSec >= 125.4 && (
        <div
          style={{
            position: "absolute",
            top: 220,
            left: "50%",
            transform: `translateX(-50%) scale(${1.05 + Math.sin(frame * 0.4) * 0.08}) rotate(${Math.sin(frame * 0.2) * 4}deg)`,
            backgroundColor: "rgba(15, 23, 42, 0.96)",
            border: "3px solid #22c55e",
            boxShadow: "0 0 40px rgba(34, 197, 94, 0.9)",
            borderRadius: 20,
            padding: "14px 32px",
            zIndex: 55,
            textAlign: "center",
          }}
        >
          <div style={{ color: "#22c55e", fontSize: 24, fontWeight: 900 }}>🥩 CHULETÓN EN VILLA MELILLA</div>
          <div style={{ color: "#facc15", fontSize: 16, fontWeight: 800 }}>¡APARCO EL MICROCHIP!</div>
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
            ? "🌴 VILLA MELILLA CIUDAD VACACIONAL: DROP KATANA 100 BPM (-40 BPM)"
            : "🏖️ VILLA MELILLA: CIUDAD VACACIONAL // 0% TAX // NEGOCIODAD 2026"}
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
                : speaker === "alain"
                ? "#3b2a05"
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
                : speaker === "alain"
                ? "#eab308"
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
                  : speaker === "alain"
                  ? "#fde047"
                  : "#f87171",
              marginBottom: 6,
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>
              💬 {speaker === "borja" && "Borja Moskv (Bilbao // Voz Real)"}
              {speaker === "mitxu" && "Mitxu (Bilbao // Voz Real)"}
              {speaker === "alain" && "Alain Elektro (Nexus // Voz Real)"}
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

      {/* GIANT CENTER DROP BANNER */}
      {isDrop && frame >= DROP_FRAME && frame < DROP_FRAME + 200 && (
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
              fontSize: 40,
              fontWeight: 900,
              color: "#facc15",
              letterSpacing: 3,
              textShadow: "0 0 20px rgba(250, 204, 21, 0.8)",
            }}
          >
            🌴 VILLA MELILLA: CIUDAD VACACIONAL 🌴
          </div>
          <div style={{ fontSize: 20, fontWeight: 900, color: "#38bdf8", marginTop: 8 }}>
            SUPER-YATE DROP: BORJA + ALAIN + MITXU + CHIQUITO + ECHENIQUE + MACGYVER @ 100 BPM
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
        <div style={{ color: "#facc15" }}>🏖️ MELILLA VACATION INDEX: +420%</div>
        <div>BTC: €80,000</div>
        <div style={{ color: "#38bdf8" }}>MARINA SOVEREIGN: 0% TAX</div>
        <div style={{ color: "#22c55e" }}>TEMPO: 100.0 BPM (-40 BPM)</div>
        <div style={{ color: "#f43f5e" }}>EXERGÍA: 100%</div>
      </div>
    </AbsoluteFill>
  );
};
