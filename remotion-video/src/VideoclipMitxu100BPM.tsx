import React, { useMemo } from "react";
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
import videoData from "../public/mitxu_videoclip_data.json";

export const VideoclipMitxu100BPM: React.FC = () => {
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
    msgId: "",
    mitxuTalking: false,
    borjaTalking: false,
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
    msgId,
    mitxuTalking,
    borjaTalking,
    flapGap,
    isDrop,
  } = data;

  // ==========================================
  // 1. DYNAMIC VIRTUAL CAMERA & SCENE DIRECTOR
  // ==========================================
  let camTargetX = 0;
  let camTargetY = 0;
  let camTargetZoom = 1.0;
  let camTargetRot = 0;
  let activeSceneName = "intro_club";

  // 100 BPM rhythm physics: 100 BPM = 1.666 Hz -> 18 frames per beat at 30 fps
  const beatPhase = (frame % 18) / 18;
  const kickPulse = isDrop ? Math.exp(-beatPhase * 4.5) * (0.05 + sub * 0.08) : 0;
  const subShake = isDrop && sub > 0.4 ? (sub - 0.4) * 24 : 0;

  // Narrative Timeline & Dynamic Camera Routing:
  // Drop starts around frame 974 in the newly mastered real-voice audio
  const DROP_FRAME = 974;

  if (frame < 260) {
    // SCENE 1: Underground Club - Mitxu Roast ("mira qué mierda de música...") & ("¡Es tu cabeza! Jajaja")
    activeSceneName = "club_rave";
    if (frame < 30) {
      camTargetX = 0;
      camTargetY = 0;
      camTargetZoom = 1.02;
    } else if (frame < 196) {
      // Zoom into Mitxu
      const p = interpolate(frame, [30, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      camTargetX = 260 * p;
      camTargetY = -25 * p;
      camTargetZoom = 1.02 + 0.32 * p;
      camTargetRot = -1.5 * p;
    } else {
      // Laughing reaction cam (punch zoom during "¡Es tu cabeza!")
      camTargetX = 290;
      camTargetY = -40;
      camTargetZoom = 1.42;
      camTargetRot = Math.sin(frame * 0.4) * 2.0;
    }
  } else if (frame < 272) {
    // WHIP-PAN TRANSITION 1: Mitxu -> Borja Moskv
    activeSceneName = "whip_mitxu_to_borja";
    const p = interpolate(frame, [260, 272], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    camTargetX = interpolate(p, [0, 1], [290, -280]);
    camTargetY = interpolate(p, [0, 1], [-40, -30]);
    camTargetZoom = interpolate(p, [0, 0.5, 1], [1.42, 0.95, 1.36]);
    camTargetRot = interpolate(p, [0, 0.5, 1], [-2, 4, 1.2]);
  } else if (frame < 376) {
    // SCENE 2: Borja Moskv Real Voice ("Eso le bajas 40 BPMs y pelotazo...")
    activeSceneName = "borja_thug";
    camTargetX = -280;
    camTargetY = -30;
    camTargetZoom = 1.36;
    camTargetRot = 1.2;
  } else if (frame < 385) {
    // FAST CUT TRANSITION 2
    activeSceneName = "cut_to_crt";
    const p = interpolate(frame, [376, 385], [0, 1]);
    camTargetX = interpolate(p, [0, 1], [-280, 160]);
    camTargetZoom = interpolate(p, [0, 1], [1.36, 1.20]);
  } else if (frame < 585) {
    // SCENE 3: Mitxu Piccicatera Counter (Retro CRT Rave Screens)
    activeSceneName = "retro_crt";
    camTargetX = 160;
    camTargetY = -20;
    camTargetZoom = 1.22;
    camTargetRot = -1.2;
  } else if (frame < 594) {
    // TRANSITION 3: Whip into Casco Viejo Bar
    activeSceneName = "whip_to_bar";
    const p = interpolate(frame, [585, 594], [0, 1]);
    camTargetX = interpolate(p, [0, 1], [160, -220]);
    camTargetZoom = interpolate(p, [0, 1], [1.22, 1.30]);
  } else if (frame < 628) {
    // SCENE 4A: Casco Viejo Pintxos Bar Interior - Borja ("¿Qué es eso?") + Pancarta Las Cortes
    activeSceneName = "casco_bar_interior";
    camTargetX = -220;
    camTargetY = -25;
    camTargetZoom = 1.30;
    camTargetRot = 1.0;
  } else if (frame < 865) {
    // SCENE 4B: Casco Viejo Terrace - Mitxu ("¿Y la de que es de estas de bar de lo viejo... Bob Sinclar?")
    activeSceneName = "casco_terrace";
    camTargetX = 240;
    camTargetY = -25;
    camTargetZoom = 1.34;
    camTargetRot = Math.sin(frame * 0.08) * 1.5;
  } else if (frame < DROP_FRAME) {
    // SCENE 5: DJ Cockpit Build-up - Borja ("¡Katana a cien BPMs, puro trance ralentizado!")
    activeSceneName = "buildup_decks";
    const p = interpolate(frame, [865, DROP_FRAME], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    camTargetX = interpolate(p, [0, 1], [240, 0]);
    camTargetY = interpolate(p, [0, 1], [-25, 20]);
    camTargetZoom = interpolate(p, [0, 1], [1.34, 1.65]);
    camTargetRot = Math.sin(frame * 0.3) * (p * 3);
  } else {
    // SCENE 6: THE 100 BPM MEGA DROP (Frames 974 - 1692)
    // Multi-Angle Director switching every 64 frames (~2.1 seconds)
    activeSceneName = "megarave_drop";
    const dropFrame = frame - DROP_FRAME;
    const shotIdx = Math.floor(dropFrame / 64) % 4;

    if (shotIdx === 0) {
      // Angle 0: Massive Stadium Festival Crowd (rave_crowd_hands)
      camTargetX = 0;
      camTargetY = 0;
      camTargetZoom = 1.05;
      camTargetRot = 0;
    } else if (shotIdx === 1) {
      // Angle 1: Borja Moskv DJ Master Cam (dj_drop_hyperspace)
      camTargetX = -275;
      camTargetY = -35;
      camTargetZoom = 1.38;
      camTargetRot = 1.5;
    } else if (shotIdx === 2) {
      // Angle 2: Mitxu Mexican Luchador Dancing Rave Cam (retro_rave_crt)
      camTargetX = 275;
      camTargetY = -35;
      camTargetZoom = 1.38;
      camTargetRot = -1.5;
    } else {
      // Angle 3: Macro Decks & Spectrum Cam (club_rave_lasers)
      camTargetX = 0;
      camTargetY = 110;
      camTargetZoom = 1.50;
      camTargetRot = Math.sin(frame * 0.15) * 1.8;
    }
  }

  // Camera Shake & Kick Physics
  const camShakeX = Math.sin(frame * 2.1) * subShake;
  const camShakeY = Math.cos(frame * 2.5) * subShake;
  const currentCamX = camTargetX + camShakeX;
  const currentCamY = camTargetY + camShakeY;
  const currentCamZoom = camTargetZoom + kickPulse;
  const currentCamRot = camTargetRot;

  // Strobe & Transition Flashes
  const dropFlash = frame >= DROP_FRAME && frame <= DROP_FRAME + 12 ? 1.0 - (frame - DROP_FRAME) / 12 : 0;
  const sceneTransitionFlash =
    (frame >= 259 && frame <= 263) ||
    (frame >= 374 && frame <= 378) ||
    (frame >= 583 && frame <= 587) ||
    (frame >= 626 && frame <= 630) ||
    (frame >= 863 && frame <= 867)
      ? 0.75 - Math.abs(frame % 4) * 0.15
      : 0;

  // Character Wobbles & Headbang
  const mitxuWobble = mitxuTalking ? Math.sin(frame * 0.85) * 5.0 : Math.sin(frame * 0.2) * 1.5;
  const borjaWobble = borjaTalking ? Math.sin(frame * 0.85) * 4.5 : Math.cos(frame * 0.18) * 1.2;
  const headbang = isDrop ? Math.sin((frame / 18) * Math.PI * 2) * 18 : 0;
  const armDance = isDrop ? Math.cos((frame / 18) * Math.PI * 2) * 24 : 0;

  // Vinyl rotation: 100 BPM = 1.666 rev/s
  const vinylRotation = frame * (isDrop ? 22 : 9);

  // ==========================================
  // 2. BACKGROUND SELECTION & OPACITIES (6 BGs)
  // ==========================================
  // 1. club_rave_lasers.jpg: frames 0 - 260, and drop shot 3
  // 2. dj_drop_hyperspace.jpg: frames 260 - 376, frames 865 - DROP_FRAME, and drop shot 1
  // 3. retro_rave_crt.jpg: frames 376 - 585, and drop shot 2
  // 4. casco_viejo_bar.jpg: frames 585 - 628 (with Pancarta Las Cortes)
  // 5. casco_viejo_terrace.jpg: frames 628 - 865
  // 6. rave_crowd_hands.jpg: drop shot 0

  const dropShotIdx = isDrop ? Math.floor((frame - DROP_FRAME) / 64) % 4 : -1;

  let bg1Club = 0;
  let bg2Hyperspace = 0;
  let bg3RetroCrt = 0;
  let bg4CascoBar = 0;
  let bg5CascoTerrace = 0;
  let bg6CrowdHands = 0;

  if (frame < 260) {
    bg1Club = 1;
  } else if (frame < 376) {
    bg2Hyperspace = 1;
  } else if (frame < 585) {
    bg3RetroCrt = 1;
  } else if (frame < 628) {
    bg4CascoBar = 1;
  } else if (frame < 865) {
    bg5CascoTerrace = 1;
  } else if (frame < DROP_FRAME) {
    bg2Hyperspace = 1;
  } else {
    // DROP MULTI-ANGLE BACKGROUNDS:
    if (dropShotIdx === 0) bg6CrowdHands = 1;
    else if (dropShotIdx === 1) bg2Hyperspace = 1;
    else if (dropShotIdx === 2) bg3RetroCrt = 1;
    else bg1Club = 1;
  }

  // Specific event triggers:
  const showYoutubeCard = frame >= 25 && frame < 196;
  const showEmojis = frame >= 208 && frame <= 259;
  const showPiccicatera = frame >= 400 && frame < 585;
  const showBobSinclar = frame >= 632 && frame < 865;
  const showPitchFader = frame >= 865 && frame < DROP_FRAME;

  // Digital Pitch Fader calculation (140 BPM -> 100 BPM)
  const pitchProgress = interpolate(frame, [875, DROP_FRAME - 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const currentBpmDisplay = (140.0 - pitchProgress * 40.0).toFixed(1);
  const pitchPercentDisplay = (-pitchProgress * 28.6).toFixed(1);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#030712",
        overflow: "hidden",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* 1. MASTER AUDIO TRACK */}
      <Audio src={staticFile("mitxu_videoclip_audio.mp3")} />

      {/* 2. DYNAMIC CAMERA CONTAINER (PANS, ZOOMS, WHIP BLUR) */}
      <AbsoluteFill
        style={{
          transformOrigin: "center center",
          transform: `scale(${currentCamZoom}) translate(${currentCamX}px, ${currentCamY}px) rotate(${currentCamRot}deg)`,
          transition: "transform 0.05s ease-out",
        }}
      >
        {/* ========================================================= */}
        {/* A. 6 CINEMATIC GEMINI BACKGROUNDS                         */}
        {/* ========================================================= */}

        {/* BG 1: Underground Club Lasers */}
        {bg1Club > 0 && (
          <AbsoluteFill style={{ opacity: bg1Club }}>
            <Img
              src={staticFile("bg/club_rave_lasers.jpg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${1.08 + Math.sin(frame * 0.015) * 0.04})`,
                filter: "brightness(0.72) contrast(1.18)",
              }}
            />
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 50%, rgba(2,6,23,0.3) 30%, rgba(2,6,23,0.92) 100%)" }} />
          </AbsoluteFill>
        )}

        {/* BG 2: DJ Cockpit & Hyperspace Drop */}
        {bg2Hyperspace > 0 && (
          <AbsoluteFill style={{ opacity: bg2Hyperspace }}>
            <Img
              src={staticFile("bg/dj_drop_hyperspace.jpg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${1.08 + (isDrop ? sub * 0.12 : 0)})`,
                filter: isDrop
                  ? `brightness(${0.85 + sub * 0.3}) contrast(1.25) saturate(1.2)`
                  : "brightness(0.7) contrast(1.15)",
              }}
            />
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 50%, rgba(14,165,233,0.2), rgba(2,6,23,0.88) 85%)" }} />
          </AbsoluteFill>
        )}

        {/* BG 3: Retro 90s CRT Rave Screens (Berlin Acid & Green Oscilloscopes) */}
        {bg3RetroCrt > 0 && (
          <AbsoluteFill style={{ opacity: bg3RetroCrt }}>
            <Img
              src={staticFile("bg/retro_rave_crt.jpg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${1.07 + Math.sin(frame * 0.02) * 0.03})`,
                filter: "brightness(0.75) contrast(1.22) saturate(1.1)",
              }}
            />
            {/* CRT SCANLINES & PHOSPHOR HORIZONTAL LINES */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                backgroundImage:
                  "repeating-linear-gradient(0deg, rgba(0, 0, 0, 0.45) 0px, rgba(0, 0, 0, 0.45) 2px, transparent 2px, transparent 4px)",
                pointerEvents: "none",
                opacity: 0.75,
              }}
            />
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 50%, rgba(2,6,23,0.25) 30%, rgba(2,6,23,0.92) 100%)" }} />
          </AbsoluteFill>
        )}

        {/* BG 4: Casco Viejo Pintxos Bar Interior */}
        {bg4CascoBar > 0 && (
          <AbsoluteFill style={{ opacity: bg4CascoBar }}>
            <Img
              src={staticFile("bg/casco_viejo_bar.jpg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${1.06 + Math.cos(frame * 0.015) * 0.03})`,
                filter: "brightness(0.7) contrast(1.15)",
              }}
            />
            {/* Balcón Pancarta Las Cortes (Queremos Putas / Tranquilidad Fuera) */}
            <div
              style={{
                position: "absolute",
                top: 230,
                right: 180,
                width: 500,
                transform: `rotate(-1.5deg) scale(${1.0 + Math.sin(frame * 0.04) * 0.012})`,
                boxShadow: "0 20px 50px rgba(0,0,0,0.95), 0 0 25px rgba(250, 204, 21, 0.4)",
                border: "3px solid #facc15",
                borderRadius: 10,
                overflow: "hidden",
                zIndex: 10,
              }}
            >
              <Img
                src={staticFile("pancarta_las_cortes.jpg")}
                style={{ width: "100%", height: "auto", display: "block" }}
              />
              <div
                style={{
                  position: "absolute",
                  bottom: 4,
                  right: 8,
                  backgroundColor: "rgba(0,0,0,0.85)",
                  color: "#facc15",
                  fontSize: 10,
                  fontWeight: 900,
                  padding: "2px 6px",
                  borderRadius: 4,
                  letterSpacing: 1,
                }}
              >
                CALLE CORTES // BILBAO
              </div>
            </div>
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 50%, rgba(15,23,42,0.3) 20%, rgba(2,6,23,0.92) 100%)" }} />
          </AbsoluteFill>
        )}

        {/* BG 5: Casco Viejo Summer Outdoor Terrace */}
        {bg5CascoTerrace > 0 && (
          <AbsoluteFill style={{ opacity: bg5CascoTerrace }}>
            <Img
              src={staticFile("bg/casco_viejo_terrace.jpg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${1.08 + Math.sin(frame * 0.012) * 0.03})`,
                filter: "brightness(0.72) contrast(1.16)",
              }}
            />
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 50%, rgba(2,6,23,0.25) 25%, rgba(2,6,23,0.90) 100%)" }} />
          </AbsoluteFill>
        )}

        {/* BG 6: Massive Festival Crowd Jumping with 100 BPM Screens */}
        {bg6CrowdHands > 0 && (
          <AbsoluteFill style={{ opacity: bg6CrowdHands }}>
            <Img
              src={staticFile("bg/rave_crowd_hands.jpg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${1.08 + (isDrop ? sub * 0.15 : 0)})`,
                filter: `brightness(${0.85 + sub * 0.35}) contrast(1.28) saturate(1.25)`,
              }}
            />
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 50%, rgba(14,165,233,0.25), rgba(2,6,23,0.85) 80%)" }} />
          </AbsoluteFill>
        )}

        {/* Dynamic Rave Lasers during Drop */}
        {isDrop && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              pointerEvents: "none",
              opacity: 0.35 + sub * 0.45,
              background: `repeating-linear-gradient(${frame * 1.5}deg, transparent, transparent 70px, rgba(56, 189, 248, 0.25) 70px, rgba(234, 88, 12, 0.2) 74px)`,
              mixBlendMode: "screen",
            }}
          />
        )}

        {/* Cyber Floor Grid */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: "40%",
            backgroundImage:
              "linear-gradient(rgba(56, 189, 248, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.08) 1px, transparent 1px)",
            backgroundSize: "60px 40px",
            transform: "perspective(600px) rotateX(60deg)",
            transformOrigin: "bottom center",
            pointerEvents: "none",
          }}
        />

        {/* BASS DROP SONIC SHOCKWAVE (Radiates on every 100 BPM kick) */}
        {isDrop && (
          <div
            style={{
              position: "absolute",
              top: "48%",
              left: "50%",
              transform: `translate(-50%, -50%) scale(${1.0 + beatPhase * 1.6})`,
              width: 530,
              height: 530,
              borderRadius: "50%",
              border: `4px solid rgba(56, 189, 248, ${(1.0 - beatPhase) * (0.3 + sub * 0.7)})`,
              boxShadow: `0 0 35px rgba(56, 189, 248, ${(1.0 - beatPhase) * 0.8})`,
              pointerEvents: "none",
              zIndex: 5,
            }}
          />
        )}

        {/* ========================================================= */}
        {/* B. CENTER ROTATING TURNTABLE (-40 BPM // 100.0 BPM)       */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            top: isDrop ? "48%" : "50%",
            left: "50%",
            transform: `translate(-50%, -50%) scale(${isDrop ? 1.15 + sub * 0.15 : 0.95})`,
            width: 530,
            height: 530,
            borderRadius: "50%",
            backgroundColor: "#030712",
            border: isDrop ? "10px solid #38bdf8" : "8px solid #334155",
            boxShadow: isDrop
              ? `0 0 ${50 + sub * 80}px rgba(56, 189, 248, 0.8), inset 0 0 60px rgba(0,0,0,0.98)`
              : "0 20px 50px rgba(0,0,0,0.9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 6,
          }}
        >
          {/* Rotating Vinyl Grooves */}
          <div
            style={{
              width: "100%",
              height: "100%",
              borderRadius: "50%",
              position: "relative",
              transform: `rotate(${vinylRotation}deg)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ position: "absolute", width: 470, height: 470, borderRadius: "50%", border: "1px dashed rgba(255,255,255,0.08)" }} />
            <div style={{ position: "absolute", width: 390, height: 390, borderRadius: "50%", border: "1px dashed rgba(56,189,248,0.25)" }} />
            <div style={{ position: "absolute", width: 310, height: 310, borderRadius: "50%", border: "1px dashed rgba(255,255,255,0.12)" }} />

            {/* Dynamic Conic Light Reflection Sheen */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "50%",
                background: `conic-gradient(from ${vinylRotation * 0.4}deg, transparent 0deg, rgba(255,255,255,0.14) 45deg, transparent 90deg, rgba(255,255,255,0.08) 225deg, transparent 270deg)`,
                pointerEvents: "none",
              }}
            />

            {/* Center Record Galleta */}
            <div
              style={{
                width: 200,
                height: 200,
                borderRadius: "50%",
                backgroundColor: isDrop ? "#0284c7" : "#0f172a",
                border: "6px solid #000",
                boxShadow: "0 0 30px rgba(0,0,0,0.95)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                padding: 10,
                color: "#fff",
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 900, letterSpacing: 2.5, color: "#38bdf8" }}>
                KATANA
              </div>
              <div style={{ fontSize: 11, fontWeight: 800, marginTop: 2, color: "#ffffff" }}>
                SILENCE (ANTIC REMIX)
              </div>
              <div
                style={{
                  marginTop: 6,
                  padding: "4px 14px",
                  backgroundColor: "#000",
                  borderRadius: 14,
                  fontSize: 11,
                  fontWeight: 900,
                  color: "#facc15",
                  border: "1.5px solid #facc15",
                  boxShadow: "0 0 10px rgba(250, 204, 21, 0.5)",
                }}
              >
                100.0 BPM (-40)
              </div>
            </div>
          </div>
        </div>

        {/* PIONEER DJ TONEARM (Realistic needle tracking the record) */}
        <div
          style={{
            position: "absolute",
            top: isDrop ? "26%" : "28%",
            left: "62%",
            width: 140,
            height: 220,
            pointerEvents: "none",
            zIndex: 8,
            transform: `rotate(${interpolate(frame, [0, 1693], [-14, 8], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}deg)`,
            transformOrigin: "top right",
          }}
        >
          {/* Tonearm Base Pivot */}
          <div
            style={{
              position: "absolute",
              top: 0,
              right: 0,
              width: 38,
              height: 38,
              borderRadius: "50%",
              backgroundColor: "#475569",
              border: "3px solid #1e293b",
              boxShadow: "0 4px 12px rgba(0,0,0,0.8)",
            }}
          />
          {/* Metallic Arm Rod */}
          <div
            style={{
              position: "absolute",
              top: 18,
              right: 17,
              width: 6,
              height: 180,
              backgroundColor: "#cbd5e1",
              boxShadow: "0 0 4px rgba(0,0,0,0.6)",
              borderRadius: 3,
            }}
          />
          {/* Cartridge & Stylus Head */}
          <div
            style={{
              position: "absolute",
              bottom: 0,
              right: 12,
              width: 16,
              height: 28,
              backgroundColor: "#0284c7",
              borderRadius: 4,
              border: "1.5px solid #fff",
              boxShadow: "0 0 8px #0284c7",
            }}
          />
        </div>

        {/* ========================================================= */}
        {/* C. 16-BAND AUDIO SPECTRUM VISUALIZER WITH PEAK GLOW       */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 120,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            gap: 12,
            alignItems: "flex-end",
            height: 160,
            zIndex: 8,
          }}
        >
          {bands.map((val: number, idx: number) => {
            const barHeight = Math.max(12, val * 155);
            const isBass = idx < 4;
            return (
              <div
                key={idx}
                style={{
                  width: 24,
                  height: barHeight,
                  borderRadius: "6px 6px 0 0",
                  backgroundColor: isDrop
                    ? isBass
                      ? "#f43f5e"
                      : idx < 10
                      ? "#38bdf8"
                      : "#a855f7"
                    : "#64748b",
                  boxShadow: isDrop
                    ? `0 0 20px ${isBass ? "rgba(244, 63, 94, 0.9)" : "rgba(56, 189, 248, 0.9)"}`
                    : "none",
                  transition: "height 0.04s ease-out",
                }}
              />
            );
          })}
        </div>

        {/* ========================================================= */}
        {/* D. CHARACTER LEFT: MITXU (SOUTH PARK STYLE CUTOUT)        */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 85,
            left: 120,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            zIndex: 15,
            transform: `rotate(${mitxuWobble + headbang}deg) scale(${mitxuTalking ? 1.10 : 1.0})`,
            transition: "transform 0.05s ease-out",
          }}
        >
          {/* Name Badge */}
          <div
            style={{
              backgroundColor: isDrop ? "#0284c7" : mitxuTalking ? "#ea580c" : "#1e293b",
              color: "#fff",
              padding: "6px 20px",
              borderRadius: 20,
              fontSize: 16,
              fontWeight: 900,
              marginBottom: 8,
              border: "2px solid #000",
              boxShadow: isDrop ? "0 0 25px rgba(2, 132, 199, 0.95)" : mitxuTalking ? "0 0 20px rgba(234, 88, 12, 0.95)" : "none",
            }}
          >
            {isDrop ? "MITXU LUCHADOR 🇲🇽" : `MITXU ${mitxuTalking ? "🗣️" : ""}`}
          </div>

          {/* Head with Animated Cutout Jaw */}
          <div
            style={{
              position: "relative",
              width: 220,
              height: 228,
              filter: "drop-shadow(0 14px 22px rgba(0,0,0,0.8))",
            }}
          >
            {/* Top of head */}
            <div
              style={{
                position: "absolute",
                top: mitxuTalking ? -flapGap : 0,
                left: 0,
                width: "100%",
                height: "100%",
                zIndex: 2,
                transition: "top 0.04s ease-out",
              }}
            >
              <Img
                src={staticFile(isDrop ? "faces/mitxu_lucha_top.png" : "faces/mitxu_hood_top.png")}
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
              />
            </div>

            {/* Bottom jaw */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                zIndex: 1,
              }}
            >
              <Img
                src={staticFile(isDrop ? "faces/mitxu_lucha_jaw.png" : "faces/mitxu_hood_jaw.png")}
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
              />
            </div>
          </div>

          {/* South Park Body (Orange Coat) + Dancing Arms */}
          <div
            style={{
              width: 170,
              height: 155,
              backgroundColor: "#ea580c",
              border: "5px solid #000",
              borderRadius: "38px 38px 0 0",
              marginTop: -10,
              position: "relative",
              display: "flex",
              justifyContent: "center",
            }}
          >
            {/* Left Dancing Arm */}
            <div
              style={{
                position: "absolute",
                top: 35,
                left: -25,
                width: 35,
                height: 75,
                backgroundColor: "#c2410c",
                border: "4px solid #000",
                borderRadius: 20,
                transform: `rotate(${armDance - 20}deg)`,
                transformOrigin: "top right",
              }}
            />
            {/* Right Arm holding beer */}
            <div
              style={{
                position: "absolute",
                top: 35,
                right: -25,
                width: 35,
                height: 75,
                backgroundColor: "#c2410c",
                border: "4px solid #000",
                borderRadius: 20,
                transform: `rotate(${-armDance + 25}deg)`,
                transformOrigin: "top left",
              }}
            />
            <div
              style={{
                width: 55,
                height: 38,
                backgroundColor: "#c2410c",
                borderRadius: "0 0 28px 28px",
                borderBottom: "4px solid #000",
                marginTop: 10,
              }}
            />
          </div>
        </div>

        {/* ========================================================= */}
        {/* E. CHARACTER RIGHT: BORJA MOSKV (REAL PHOTO CUTOUT)       */}
        {/* ========================================================= */}
        <div
          style={{
            position: "absolute",
            bottom: 85,
            right: 120,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            zIndex: 15,
            transform: `rotate(${borjaWobble - headbang}deg) scale(${borjaTalking ? 1.10 : 1.0})`,
            transition: "transform 0.05s ease-out",
          }}
        >
          {/* Name Badge */}
          <div
            style={{
              backgroundColor: borjaTalking ? "#0284c7" : "#1e293b",
              color: "#fff",
              padding: "6px 20px",
              borderRadius: 20,
              fontSize: 16,
              fontWeight: 900,
              marginBottom: 8,
              border: "2px solid #000",
              boxShadow: borjaTalking ? "0 0 20px rgba(2, 132, 199, 0.95)" : "none",
            }}
          >
            BORJA MOSKV {borjaTalking && "🗣️"}
          </div>

          {/* Head with Animated Cutout Jaw (Real Borja Moskv) */}
          <div
            style={{
              position: "relative",
              width: 210,
              height: 210,
              filter: "drop-shadow(0 14px 22px rgba(0,0,0,0.8))",
            }}
          >
            {/* Top of head */}
            <div
              style={{
                position: "absolute",
                top: borjaTalking ? -flapGap : 0,
                left: 0,
                width: "100%",
                height: "100%",
                zIndex: 2,
                transition: "top 0.04s ease-out",
              }}
            >
              <Img
                src={staticFile("faces/borja_photo_top.png")}
                style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: 16 }}
              />
              {/* THUG LIFE PIXEL SUNGLASSES (Drop on frame 272) */}
              {frame >= 272 && (
                <div
                  style={{
                    position: "absolute",
                    top: interpolate(frame, [272, 292], [-120, 78], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                    }),
                    left: "50%",
                    transform: "translateX(-50%)",
                    width: 145,
                    zIndex: 10,
                    filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.85))",
                  }}
                >
                  <Img
                    src={staticFile("faces/pixel_sunglasses.png")}
                    style={{ width: "100%", height: "auto" }}
                  />
                </div>
              )}
            </div>

            {/* Bottom jaw (Real Borja Moskv Beard/Mouth) */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                zIndex: 1,
              }}
            >
              <Img
                src={staticFile("faces/borja_photo_jaw.png")}
                style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: 16 }}
              />
            </div>
          </div>

          {/* Body (Dark Blue Cyber Coat) + Arms */}
          <div
            style={{
              width: 170,
              height: 155,
              backgroundColor: "#0369a1",
              border: "5px solid #000",
              borderRadius: "38px 38px 0 0",
              marginTop: -10,
              position: "relative",
              display: "flex",
              justifyContent: "center",
            }}
          >
            {/* Left Arm */}
            <div
              style={{
                position: "absolute",
                top: 35,
                left: -25,
                width: 35,
                height: 75,
                backgroundColor: "#0284c7",
                border: "4px solid #000",
                borderRadius: 20,
                transform: `rotate(${-armDance - 20}deg)`,
                transformOrigin: "top right",
              }}
            />
            {/* Right Arm */}
            <div
              style={{
                position: "absolute",
                top: 35,
                right: -25,
                width: 35,
                height: 75,
                backgroundColor: "#0284c7",
                border: "4px solid #000",
                borderRadius: 20,
                transform: `rotate(${armDance + 20}deg)`,
                transformOrigin: "top left",
              }}
            />
            <div
              style={{
                width: 55,
                height: 38,
                backgroundColor: "#075985",
                borderRadius: "0 0 28px 28px",
                borderBottom: "4px solid #000",
                marginTop: 10,
              }}
            />
          </div>
        </div>
      </AbsoluteFill>

      {/* ========================================================= */}
      {/* 3. STATIC / HUD OVERLAYS (UNAFFECTED BY CAMERA SHAKE)    */}
      {/* ========================================================= */}

      {/* TOP HEADER: NEXUS STATUS */}
      <div
        style={{
          position: "absolute",
          top: 46,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          alignItems: "center",
          gap: 16,
          zIndex: 52,
          backgroundColor: "rgba(15, 23, 42, 0.94)",
          backdropFilter: "blur(16px)",
          padding: "8px 26px",
          borderRadius: 40,
          border: isDrop ? "2px solid #38bdf8" : "2px solid rgba(56, 189, 248, 0.4)",
          boxShadow: isDrop ? "0 0 30px rgba(56, 189, 248, 0.6)" : "0 10px 30px rgba(0,0,0,0.6)",
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
            ? "🔥 PELOTAZO CONFIRMADO: KATANA SILENCE A 100 BPM (-40 BPM)"
            : "🎙️ NEXUS WHATSAPP TRINCHERA: MITXU vs. BORJA MOSKV (VOZ REAL)"}
        </div>
      </div>

      {/* AUTHENTIC WHATSAPP POPUP BUBBLE (STAGE CENTER) */}
      <div
        style={{
          position: "absolute",
          top: 104,
          left: "50%",
          transform: "translateX(-50%)",
          width: "72%",
          maxWidth: 1050,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 52,
        }}
      >
        {text ? (
          <div
            style={{
              backgroundColor: speaker === "mitxu" ? "#202c33" : "#005c4b",
              border: `2.5px solid ${speaker === "mitxu" ? "#fb923c" : "#25d366"}`,
              borderRadius: "22px 22px 22px 4px",
              padding: "16px 28px",
              boxShadow: "0 16px 40px rgba(0,0,0,0.9)",
              textAlign: "left",
              maxWidth: 900,
              position: "relative",
              animation: "fadeIn 0.2s ease-out",
            }}
          >
            <div
              style={{
                fontSize: 13,
                fontWeight: 900,
                letterSpacing: 1.5,
                color: speaker === "mitxu" ? "#fb923c" : "#53bdeb",
                marginBottom: 6,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>💬 {speaker === "mitxu" ? "Mitxu [21:09]" : "Borja Moskv [21:15]"}</span>
              <span style={{ fontSize: 11, color: "#8696a0" }}>✓✓ Entregado</span>
            </div>
            <div
              style={{
                fontSize: 24,
                fontWeight: 800,
                color: "#e9edef",
                lineHeight: 1.35,
                textShadow: "0 2px 8px rgba(0,0,0,0.85)",
              }}
            >
              {text}
            </div>
          </div>
        ) : null}
      </div>

      {/* POPUP 1: YOUTUBE CARD (Frames 30 - 185) */}
      {showYoutubeCard && (
        <div
          style={{
            position: "absolute",
            top: 215,
            right: 90,
            width: 320,
            backgroundColor: "#0f172a",
            border: "2px solid #ef4444",
            borderRadius: 16,
            overflow: "hidden",
            boxShadow: "0 14px 40px rgba(0,0,0,0.9)",
            zIndex: 40,
          }}
        >
          <div style={{ position: "relative", width: "100%", height: 160 }}>
            <Img
              src={staticFile("katana_thumb.jpg")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                backgroundColor: "rgba(239, 68, 68, 0.95)",
                borderRadius: "50%",
                width: 48,
                height: 48,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 22,
                boxShadow: "0 0 18px rgba(239, 68, 68, 0.9)",
              }}
            >
              ▶
            </div>
          </div>
          <div style={{ padding: "10px 14px", color: "#fff" }}>
            <div style={{ fontSize: 12, fontWeight: 900, color: "#ef4444" }}>YOUTUBE // 140 BPM</div>
            <div style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>Katana - Silence (Antic Remix)</div>
            <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>"Progresivo de los 90 para guiris"</div>
          </div>
        </div>
      )}

      {/* POPUP 2: SPOTIFY VERIFIED ARTIST // BORJA MOSKV (Frames 272 - 376) */}
      {frame >= 272 && frame < 376 && (
        <div
          style={{
            position: "absolute",
            top: 215,
            right: 90,
            width: 330,
            backgroundColor: "#121212",
            border: "2px solid #1db954",
            borderRadius: 16,
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: 14,
            boxShadow: "0 14px 40px rgba(0,0,0,0.9)",
            zIndex: 40,
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: "50%",
              overflow: "hidden",
              border: "2.5px solid #1db954",
              flexShrink: 0,
            }}
          >
            <Img
              src={staticFile("faces/borja_moskv_real_portrait.png")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 900, color: "#1db954", letterSpacing: 1.5 }}>
              VERIFIED ARTIST ✓
            </div>
            <div style={{ fontSize: 17, fontWeight: 900, color: "#fff", marginTop: 2 }}>
              Borja Moskv
            </div>
            <div style={{ fontSize: 11, color: "#a7a7a7", marginTop: 2 }}>
              Basques on Decks // Spotify
            </div>
          </div>
        </div>
      )}

      {/* POPUP 3: LAUGHING EMOJIS (Frames 140 - 184) */}
      {showEmojis && (
        <div
          style={{
            position: "absolute",
            top: "38%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            display: "flex",
            gap: 22,
            fontSize: 74,
            zIndex: 45,
            filter: "drop-shadow(0 12px 24px rgba(0,0,0,0.85))",
          }}
        >
          {["🤣", "🤣", "🤣", "🤣", "🤣"].map((emoji, i) => (
            <div
              key={i}
              style={{
                transform: `translateY(${Math.sin((frame + i * 8) * 0.45) * 35}px) scale(${1.0 + Math.sin(frame * 0.5) * 0.22})`,
              }}
            >
              {emoji}
            </div>
          ))}
        </div>
      )}

      {/* POPUP 4: PICCICATERA CARD (Frames 330 - 445) */}
      {showPiccicatera && (
        <div
          style={{
            position: "absolute",
            top: 215,
            left: 90,
            width: 350,
            backgroundColor: "#422006",
            border: "3px solid #facc15",
            borderRadius: 18,
            padding: "16px 22px",
            boxShadow: "0 16px 40px rgba(0,0,0,0.9)",
            zIndex: 40,
            color: "#fef08a",
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 900, letterSpacing: 1.5, color: "#facc15" }}>
            📖 DICCIONARIO BILBAÍNO
          </div>
          <div style={{ fontSize: 21, fontWeight: 900, color: "#fff", marginTop: 4 }}>
            "PICCICATERA"
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#fef08a", marginTop: 6, lineHeight: 1.45 }}>
            Persona que ahorra hasta en el tempo del vinilo. Si el progresivo iba a 140 BPM, ella lo exige a 100 para no desgastar la aguja.
          </div>
        </div>
      )}

      {/* POPUP 5: CASCO VIEJO BAR / BOB SINCLAR (Frames 490 - 645) */}
      {showBobSinclar && (
        <div
          style={{
            position: "absolute",
            top: 215,
            left: 90,
            width: 360,
            backgroundColor: "#064e3b",
            border: "3px solid #34d399",
            borderRadius: 18,
            padding: "16px 22px",
            boxShadow: "0 16px 40px rgba(0,0,0,0.9)",
            zIndex: 40,
            color: "#a7f3d0",
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 900, letterSpacing: 1.5, color: "#34d399" }}>
            🍹 BAR DE LO VIEJO // GUIRIS
          </div>
          <div style={{ fontSize: 19, fontWeight: 900, color: "#fff", marginTop: 4 }}>
            "Estilo Bob Sinclar para el verano"
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#d1fae5", marginTop: 6, lineHeight: 1.45 }}>
            Mitxu diagnosticando house comercial de terraza para extranjeros en el Casco Viejo de Bilbao con pintxos y txakoli.
          </div>
        </div>
      )}

      {/* POPUP 6: DIGITAL PITCH FADER HUD (Frames 645 - DROP_FRAME) */}
      {showPitchFader && (
        <div
          style={{
            position: "absolute",
            top: "40%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            backdropFilter: "blur(18px)",
            border: "3px solid #ef4444",
            borderRadius: 24,
            padding: "24px 36px",
            boxShadow: "0 0 50px rgba(239, 68, 68, 0.8)",
            zIndex: 45,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            width: 480,
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 900, color: "#ef4444", letterSpacing: 2 }}>
            ⚠️ PIONEER CDJ-3000 PITCH OVERRIDE
          </div>
          <div style={{ fontSize: 36, fontWeight: 900, color: "#fff", marginTop: 8 }}>
            {currentBpmDisplay} <span style={{ fontSize: 20, color: "#facc15" }}>BPM</span>
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: "#38bdf8", marginTop: 2 }}>
            Pitch: {pitchPercentDisplay}% (-40 BPM)
          </div>

          {/* Graphical Fader Track */}
          <div
            style={{
              width: "100%",
              height: 18,
              backgroundColor: "#1e293b",
              borderRadius: 9,
              marginTop: 16,
              position: "relative",
              overflow: "hidden",
              border: "1px solid #475569",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                bottom: 0,
                width: `${pitchProgress * 100}%`,
                backgroundColor: "#ef4444",
                boxShadow: "0 0 14px #ef4444",
              }}
            />
          </div>
          <div style={{ fontSize: 13, fontWeight: 800, color: "#fca5a5", marginTop: 12 }}>
            "¡Pues ahí te va, Mitxu: Katana a 100 BPMs, puro trance ralentizado!"
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* KINETIC TYPOGRAPHY IMPACT BADGES (PUNCH HIGHLIGHTS)       */}
      {/* ========================================================= */}

      {/* 1. MITXU ROAST IMPACT: "¡ES TU CABEZA!" (Frames 210 - 258) */}
      {frame >= 210 && frame < 258 && (
        <div
          style={{
            position: "absolute",
            top: "46%",
            left: "50%",
            transform: `translate(-50%, -50%) rotate(${Math.sin(frame * 0.5) * 3}deg) scale(${1.02 + Math.sin(frame * 0.4) * 0.08})`,
            backgroundColor: "rgba(234, 88, 12, 0.96)",
            border: "4px solid #fff",
            boxShadow: "0 0 45px rgba(234, 88, 12, 0.95), 0 20px 50px rgba(0,0,0,0.9)",
            borderRadius: 24,
            padding: "16px 36px",
            zIndex: 48,
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: 38, fontWeight: 900, color: "#fff", textShadow: "0 4px 14px rgba(0,0,0,0.9)" }}>
            💥 ¡ES TU CABEZA! 🤯
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: "#fef08a", marginTop: 4 }}>
            "House para guiris y progresivo de los 90"
          </div>
        </div>
      )}

      {/* 2. BORJA PROPOSAL: "-40 BPM = PELOTAZO" (Frames 275 - 345) */}
      {frame >= 275 && frame < 345 && (
        <div
          style={{
            position: "absolute",
            top: "46%",
            left: "50%",
            transform: `translate(-50%, -50%) rotate(${Math.cos(frame * 0.4) * 2}deg) scale(${1.04 + Math.sin(frame * 0.3) * 0.05})`,
            backgroundColor: "rgba(2, 132, 199, 0.96)",
            border: "4px solid #38bdf8",
            boxShadow: "0 0 50px rgba(56, 189, 248, 0.95), 0 20px 50px rgba(0,0,0,0.9)",
            borderRadius: 24,
            padding: "16px 40px",
            zIndex: 48,
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: 36, fontWeight: 900, color: "#fff", letterSpacing: 1.5 }}>
            ⚡ -40 BPM = PELOTAZO ⚡
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: "#e0f2fe", marginTop: 4 }}>
            "Eso le bajas 40 BPMs y pelotazo... Lo voy a hacer"
          </div>
        </div>
      )}

      {/* 3. PICCICATERA CERTIFIED BADGE (Frames 415 - 490) */}
      {frame >= 415 && frame < 490 && (
        <div
          style={{
            position: "absolute",
            top: "46%",
            left: "50%",
            transform: `translate(-50%, -50%) rotate(-2deg) scale(1.05)`,
            backgroundColor: "rgba(202, 138, 4, 0.96)",
            border: "4px solid #fef08a",
            boxShadow: "0 0 45px rgba(250, 204, 21, 0.9), 0 20px 50px rgba(0,0,0,0.9)",
            borderRadius: 24,
            padding: "16px 36px",
            zIndex: 48,
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: 34, fontWeight: 900, color: "#fff" }}>
            🏆 CERTIFIED PICCICATERA 🏆
          </div>
          <div style={{ fontSize: 15, fontWeight: 800, color: "#fef9c3", marginTop: 4 }}>
            "Coge la chunga esa de progresivo y la baja de velocidad"
          </div>
        </div>
      )}

      {/* 4. BOB SINCLAR SUMMER HOUSE (Frames 645 - 725) */}
      {frame >= 645 && frame < 725 && (
        <div
          style={{
            position: "absolute",
            top: "46%",
            left: "50%",
            transform: `translate(-50%, -50%) rotate(2deg) scale(1.05)`,
            backgroundColor: "rgba(5, 150, 105, 0.96)",
            border: "4px solid #6ee7b7",
            boxShadow: "0 0 45px rgba(52, 211, 153, 0.9), 0 20px 50px rgba(0,0,0,0.9)",
            borderRadius: 24,
            padding: "16px 36px",
            zIndex: 48,
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: 32, fontWeight: 900, color: "#fff" }}>
            🌴 BAR DE LO VIEJO // BOB SINCLAR 🍹
          </div>
          <div style={{ fontSize: 15, fontWeight: 800, color: "#d1fae5", marginTop: 4 }}>
            "Estilo las chungas de Bob Sinclar para el verano de los guiris"
          </div>
        </div>
      )}

      {/* 5. COUNTDOWN WARNING: 100 BPM INMINENTE (Frames 880 - 960) */}
      {frame >= 880 && frame < 960 && (
        <div
          style={{
            position: "absolute",
            top: "46%",
            left: "50%",
            transform: `translate(-50%, -50%) scale(${1.08 + Math.sin(frame * 0.8) * 0.06})`,
            backgroundColor: "rgba(220, 38, 38, 0.96)",
            border: "4px solid #fecaca",
            boxShadow: "0 0 55px rgba(239, 68, 68, 0.95), 0 20px 50px rgba(0,0,0,0.9)",
            borderRadius: 24,
            padding: "16px 42px",
            zIndex: 48,
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: 36, fontWeight: 900, color: "#fff", letterSpacing: 2 }}>
            🚨 100.0 BPM INMINENTE 🚨
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: "#fee2e2", marginTop: 4 }}>
            "¡Katana a cien BPMs, puro trance ralentizado!"
          </div>
        </div>
      )}

      {/* 6. DROP IMPACT: DROP THE BASS (Frames 974 - 1080) */}
      {isDrop && frame >= DROP_FRAME && frame < DROP_FRAME + 110 && (
        <div
          style={{
            position: "absolute",
            top: "43%",
            left: "50%",
            transform: `translate(-50%, -50%) scale(${1.12 + sub * 0.18})`,
            backgroundColor: "rgba(15, 23, 42, 0.96)",
            border: "4px solid #38bdf8",
            boxShadow: "0 0 65px rgba(56, 189, 248, 0.95), 0 20px 60px rgba(0,0,0,0.95)",
            borderRadius: 28,
            padding: "20px 48px",
            zIndex: 48,
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: 40, fontWeight: 900, color: "#facc15", letterSpacing: 3 }}>
            🔊 DROP THE BASS // 100 BPM 🔊
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: "#38bdf8", marginTop: 6 }}>
            KATANA - SILENCE (ANTIC REMIX @ 100.0 BPM)
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 4. TRANSITION EFFECTS: STROBE FLASH & CINEMATIC BARS      */}
      {/* ========================================================= */}

      {/* DROP EXPLOSION STROBE FLASH */}
      {dropFlash > 0 && (
        <AbsoluteFill
          style={{
            backgroundColor: `rgba(255, 255, 255, ${dropFlash * 0.94})`,
            pointerEvents: "none",
            zIndex: 60,
          }}
        />
      )}

      {/* SCENE TRANSITION FLASH */}
      {sceneTransitionFlash > 0 && (
        <AbsoluteFill
          style={{
            backgroundColor: `rgba(255, 255, 255, ${sceneTransitionFlash})`,
            pointerEvents: "none",
            zIndex: 55,
          }}
        />
      )}

      {/* CINEMATIC ANAMORPHIC LETTERBOX BARS (2.35:1) */}
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

      {/* FOOTER TELEMETRY HUD */}
      <div
        style={{
          position: "absolute",
          bottom: 12,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 36,
          color: "#94a3b8",
          fontSize: 13,
          fontWeight: 800,
          fontFamily: "monospace",
          zIndex: 52,
        }}
      >
        <div>TRACK: KATANA - SILENCE (ANTIC REMIX)</div>
        <div>ORIGINAL: 140.0 BPM</div>
        <div style={{ color: "#38bdf8" }}>TARGET: 100.0 BPM (-40 BPM)</div>
        <div style={{ color: "#facc15" }}>VARISPEED VINYL SLOWDOWN</div>
      </div>
    </AbsoluteFill>
  );
};
