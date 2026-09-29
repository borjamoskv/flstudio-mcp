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

export const StreetFighterBerghain: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Active Round: 1 (Feto Infinito) for frames 0..2700, 2 (Niña Kravitz) for frames 2700..5400
  const isRound1 = frame < 2700;
  const roundFrame = isRound1 ? frame : frame - 2700;

  // 140 BPM Sub-bass pumping (13 frames per beat)
  const pumpSub = interpolate(frame % 13, [0, 6, 12], [1, 1.09, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- FIGHT TIMELINE & ACTION STATES ---
  // Physical animations synchronized with the master audio dialogue & hits:
  // Round 1:
  // - 0..400: Intro & dialogue
  // - 400..450: CZ Hick Hack attack (dash + projectile)
  // - 700..900: Feto dialogue
  // - 900..950: Feto Placenta Acida attack (projectile spit)
  // - 1400..1500: Feto Latigo Nucleico (whip lash)
  // - 1800..1900: CZ Sidechain de la Muerte (suction vortex)
  // - 2450..2600: CZ Falso Drop (silence + nuclear explosion)
  // - 2600..2700: Double KO fall

  // Round 2:
  // - 2700..3100: Intro & dialogue
  // - 3300..3380: Nina TB-303 Acid Blast
  // - 3650..3750: CZ Hick Hack counter
  // - 3950..4150: Nina Ghetto Whisper Stun
  // - 4400..4520: Nina Bathtub Teleport Dropkick
  // - 4950..5250: CZ Final Falso Drop & Mid-Air Collision
  // - 5250..5400: Double KO fall

  let czAttackState: "idle" | "hickhack" | "sidechain" | "falsodrop" | "hit" | "ko" = "idle";
  let rivalAttackState: "idle" | "placenta" | "latigo" | "acid303" | "ghetto" | "bathtub" | "hit" | "ko" = "idle";
  let damagePopup: { text: string; x: number; y: number; color: string } | null = null;
  let projectile: { type: "hickhack" | "placenta" | "whip" | "acid303" | "bathtub"; x: number; y: number } | null = null;

  // Screen shake & camera zoom
  let camShakeX = 0;
  let camShakeY = 0;
  let camZoom = 1.0;

  // Health tracking
  let czHP = 1000;
  let rivalHP = 1000;

  if (isRound1) {
    if (roundFrame >= 420 && roundFrame < 450) {
      czAttackState = "hickhack";
      const p = (roundFrame - 420) / 30;
      projectile = { type: "hickhack", x: interpolate(p, [0, 1], [400, 1450]), y: 650 };
      if (roundFrame > 438) {
        rivalAttackState = "hit";
        camShakeX = Math.sin(roundFrame * 2) * 10;
        damagePopup = { text: "-70 HP HICK-HACK!", x: 1450, y: 550, color: "#facc15" };
      }
    }
    if (roundFrame >= 440) rivalHP -= 70;

    if (roundFrame >= 920 && roundFrame < 960) {
      rivalAttackState = "placenta";
      const p = (roundFrame - 920) / 40;
      projectile = { type: "placenta", x: interpolate(p, [0, 1], [1400, 450]), y: interpolate(p, [0, 0.5, 1], [600, 500, 750]) };
      if (roundFrame > 948) {
        czAttackState = "hit";
        camShakeY = Math.cos(roundFrame * 2) * 8;
        damagePopup = { text: "-85 HP PLACENTA!", x: 450, y: 550, color: "#22c55e" };
      }
    }
    if (roundFrame >= 950) czHP -= 85;

    if (roundFrame >= 1470 && roundFrame < 1510) {
      rivalAttackState = "latigo";
      projectile = { type: "whip", x: 1400, y: 620 };
      czAttackState = "hit";
      camShakeX = Math.sin(roundFrame * 3) * 14;
      damagePopup = { text: "-120 HP LÁTIGO!", x: 450, y: 530, color: "#a855f7" };
    }
    if (roundFrame >= 1500) czHP -= 120;

    if (roundFrame >= 1830 && roundFrame < 1880) {
      czAttackState = "sidechain";
      camZoom = 1.08;
      if (roundFrame > 1850) {
        rivalAttackState = "hit";
        camShakeX = Math.sin(roundFrame * 3) * 16;
        damagePopup = { text: "-130 HP SIDECHAIN CRUSH!", x: 1350, y: 500, color: "#facc15" };
      }
    }
    if (roundFrame >= 1860) rivalHP -= 130;

    if (roundFrame >= 2480 && roundFrame < 2600) {
      czAttackState = "falsodrop";
      camZoom = interpolate(roundFrame, [2480, 2520, 2540], [1.0, 1.2, 1.05]);
      if (roundFrame > 2510) {
        camShakeX = Math.sin(roundFrame * 4) * 25;
        camShakeY = Math.cos(roundFrame * 4) * 20;
        damagePopup = { text: "-715 HP ULTRA FALSO DROP!!", x: 1350, y: 450, color: "#ef4444" };
        rivalAttackState = "hit";
        rivalHP = 0;
        czHP = 0;
      }
    }

    if (roundFrame >= 2600) {
      czAttackState = "ko";
      rivalAttackState = "ko";
      czHP = 0;
      rivalHP = 0;
    }
  } else {
    // --- ROUND 2 (NIÑA KRAVITZ) ---
    if (roundFrame >= 3330 - 2700 && roundFrame < 3380 - 2700) {
      rivalAttackState = "acid303";
      const p = (roundFrame - 630) / 50;
      projectile = { type: "acid303", x: interpolate(p, [0, 1], [1400, 450]), y: 640 };
      if (roundFrame > 665) {
        czAttackState = "hit";
        camShakeX = Math.sin(roundFrame * 2) * 12;
        damagePopup = { text: "-90 HP ACID 303!", x: 450, y: 550, color: "#ec4899" };
      }
    }
    if (roundFrame >= 670) czHP -= 90;

    if (roundFrame >= 3660 - 2700 && roundFrame < 3710 - 2700) {
      czAttackState = "hickhack";
      const p = (roundFrame - 960) / 50;
      projectile = { type: "hickhack", x: interpolate(p, [0, 1], [400, 1450]), y: 640 };
      if (roundFrame > 995) {
        rivalAttackState = "hit";
        camShakeX = Math.sin(roundFrame * 2) * 10;
        damagePopup = { text: "-80 HP SÍNCOPA!", x: 1450, y: 550, color: "#facc15" };
      }
    }
    if (roundFrame >= 1000) rivalHP -= 80;

    if (roundFrame >= 3960 - 2700 && roundFrame < 4060 - 2700) {
      rivalAttackState = "ghetto";
      czAttackState = "hit";
      damagePopup = { text: "STUNNED! GHETTO ASMR (-110 HP)", x: 450, y: 480, color: "#f472b6" };
    }
    if (roundFrame >= 1280) czHP -= 110;

    if (roundFrame >= 4420 - 2700 && roundFrame < 4490 - 2700) {
      rivalAttackState = "bathtub";
      projectile = { type: "bathtub", x: 600, y: 400 };
      if (roundFrame > 1750) {
        czAttackState = "hit";
        camShakeY = Math.sin(roundFrame * 3) * 18;
        damagePopup = { text: "-145 HP BAÑERA DROPKICK!", x: 450, y: 520, color: "#38bdf8" };
      }
    }
    if (roundFrame >= 1770) czHP -= 145;

    if (roundFrame >= 4950 - 2700 && roundFrame < 5250 - 2700) {
      czAttackState = "falsodrop";
      rivalAttackState = "acid303";
      camZoom = interpolate(roundFrame, [2250, 2480, 2520], [1.0, 1.25, 1.05]);
      if (roundFrame > 2480) {
        camShakeX = Math.sin(roundFrame * 5) * 30;
        camShakeY = Math.cos(roundFrame * 5) * 25;
        damagePopup = { text: "-655 HP DOUBLE EXPLOSION!!", x: 960, y: 400, color: "#ef4444" };
        czHP = 0;
        rivalHP = 0;
      }
    }

    if (roundFrame >= 5250 - 2700) {
      czAttackState = "ko";
      rivalAttackState = "ko";
      czHP = 0;
      rivalHP = 0;
    }
  }

  // Conde Cero Physical Position & Sprite Transform
  let czPosX = 220;
  let czPosY = 110;
  let czRot = 0;
  let czScale = 1.0;

  if (czAttackState === "hickhack") {
    czPosX = 340; // Lunge forward!
  } else if (czAttackState === "sidechain") {
    czPosX = 420;
    czPosY = 160; // Jump up on decks
    czScale = 1.1;
  } else if (czAttackState === "hit") {
    czPosX = 140; // Knocked back
    czRot = -12;
  } else if (czAttackState === "ko") {
    czPosX = 180;
    czPosY = 40;
    czRot = -75; // Knocked out on concrete
  } else {
    czPosY += Math.sin(frame * 0.2) * 6; // Idle breathing
  }

  // Rival Physical Position & Sprite Transform
  let rivalPosX = 220;
  let rivalPosY = 120;
  let rivalRot = 0;
  let rivalScale = 1.0;

  if (rivalAttackState === "placenta" || rivalAttackState === "acid303") {
    rivalPosX = 320; // Lunge forward
  } else if (rivalAttackState === "bathtub") {
    rivalPosX = 480; // Teleported right next to CZ
    rivalPosY = 220;
    rivalScale = 1.15;
  } else if (rivalAttackState === "hit") {
    rivalPosX = 140; // Knocked back
    rivalRot = 15;
  } else if (rivalAttackState === "ko") {
    rivalPosX = 180;
    rivalPosY = 30;
    rivalRot = 70; // Knocked out on floor
    rivalScale = 0.8;
  } else {
    rivalPosY += Math.sin(frame * 0.18) * 10;
  }

  // Dialogues & Action banners
  let dialogueCZ = "";
  let dialogueRival = "";

  if (isRound1) {
    if (roundFrame >= 150 && roundFrame < 380) dialogueCZ = "¡Aupa ahí, aborto mal cerrao! ¿Qué vienes a asustar en Berghain?";
    if (roundFrame >= 450 && roundFrame < 680) dialogueCZ = "¡Toma Hick Hack Asincopao, cagüendios! ¡Aprende compás!";
    if (roundFrame >= 700 && roundFrame < 900) dialogueRival = "GLZZZTT... MATRIZ OBSOLETA... SIENTE EL FLUIDO PRIMIGENIO...";
    if (roundFrame >= 1050 && roundFrame < 1300) dialogueCZ = "¡Aibalaostia! ¡Mírale el escupitajo! ¡Parece grasa de macarrones!";
    if (roundFrame >= 1350 && roundFrame < 1550) dialogueRival = "LÁTIGO NUCLEICO... MUTACIÓN EN EL DARKROOM...";
    if (roundFrame >= 1650 && roundFrame < 1950) dialogueCZ = "¡Sidechain de la muerte! ¡Te chupo los graves y la pensión!";
    if (roundFrame >= 2050 && roundFrame < 2300) dialogueRival = "COLAPSO TOTAL... MORIREMOS EN EL HORMIGÓN...";
    if (roundFrame >= 2350 && roundFrame < 2550) dialogueCZ = "¡Falso drop de CruEL Label! ¡Silencio sepulcral y a mamar bombo!";
  } else {
    if (roundFrame >= 150 && roundFrame < 380) dialogueCZ = "¡Aupa Nina! ¡A mí con susurritos de siberiana friolera no me vengas!";
    if (roundFrame >= 400 && roundFrame < 620) dialogueRival = "You don't understand underground... my 303 comes from Siberia...";
    if (roundFrame >= 720 && roundFrame < 950) dialogueCZ = "¡Toma síncopa de Bilbao, a ver si cuadras sin Rekordbox!";
    if (roundFrame >= 1050 && roundFrame < 1250) dialogueRival = "Ghetto Kraviz... trip recordings... you are hypnotized...";
    if (roundFrame >= 1350 && roundFrame < 1550) dialogueRival = "Bathtub teleport! From Irkutsk with love! Spasiba!";
    if (roundFrame >= 1600 && roundFrame < 1850) dialogueCZ = "¡Mucho postureo en la bañera, pero en Bilbao te habrías metido un pintxo de tortilla!";
    if (roundFrame >= 2100 && roundFrame < 2400) dialogueCZ = "¡Falso drop definitivo a máxima presión! ¡Aquí no hay after que valga!";
  }

  const showDoubleKO = roundFrame >= 2580;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#050505",
        fontFamily: "'Courier New', Courier, monospace",
        color: "#ffffff",
        overflow: "hidden",
        transform: `scale(${camZoom}) translate(${camShakeX}px, ${camShakeY}px)`,
      }}
    >
      {/* SYNCHRONIZED MASTER AUDIO WITH REAL VOICES, FIGHT SFX & DEBUSSY MUSIC */}
      <Audio src={staticFile("street_fighter_master_audio.mp3")} />

      {/* BERGHAIN BRUTALIST ARENA */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(180deg, #111116 0%, #0a0a0c 60%, #15151a 100%)",
        }}
      >
        {/* Concrete pillars */}
        <div style={{ position: "absolute", left: 140, top: 0, bottom: 0, width: 90, background: "rgba(35,35,45,0.7)", borderRight: "2px solid rgba(60,60,75,0.5)" }} />
        <div style={{ position: "absolute", left: 380, top: 0, bottom: 0, width: 70, background: "rgba(30,30,40,0.5)", borderRight: "1px solid rgba(50,50,65,0.3)" }} />
        <div style={{ position: "absolute", right: 380, top: 0, bottom: 0, width: 70, background: "rgba(30,30,40,0.5)", borderLeft: "1px solid rgba(50,50,65,0.3)" }} />
        <div style={{ position: "absolute", right: 140, top: 0, bottom: 0, width: 90, background: "rgba(35,35,45,0.7)", borderLeft: "2px solid rgba(60,60,75,0.5)" }} />

        {/* Industrial Catwalks */}
        <div style={{ position: "absolute", top: 120, left: 0, right: 0, height: 16, background: "#222228", borderBottom: "2px solid #333340" }} />

        {/* Funktion-One Left */}
        <div
          style={{
            position: "absolute",
            left: 40,
            bottom: 120,
            width: 140,
            transform: `scale(${pumpSub})`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <div style={{ width: 100, height: 90, background: "#181822", border: "4px solid #7e22ce", borderRadius: "8px 8px 0 0", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 50, height: 50, borderRadius: "50%", background: "#581c87", border: "3px solid #a855f7" }} />
          </div>
          <div style={{ width: 120, height: 130, background: "#0c0c12", border: "3px solid #3f3f4e", marginTop: 4, display: "flex", flexDirection: "column", justifyContent: "space-around", alignItems: "center" }}>
            <div style={{ width: 80, height: 40, borderRadius: "50%", background: "#272733" }} />
            <div style={{ width: 80, height: 40, borderRadius: "50%", background: "#272733" }} />
          </div>
          <span style={{ fontSize: 13, color: "#c084fc", fontWeight: "bold", marginTop: 6, letterSpacing: 2 }}>FUNKTION-1</span>
        </div>

        {/* Funktion-One Right */}
        <div
          style={{
            position: "absolute",
            right: 40,
            bottom: 120,
            width: 140,
            transform: `scale(${pumpSub})`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <div style={{ width: 100, height: 90, background: "#181822", border: "4px solid #7e22ce", borderRadius: "8px 8px 0 0", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 50, height: 50, borderRadius: "50%", background: "#581c87", border: "3px solid #a855f7" }} />
          </div>
          <div style={{ width: 120, height: 130, background: "#0c0c12", border: "3px solid #3f3f4e", marginTop: 4, display: "flex", flexDirection: "column", justifyContent: "space-around", alignItems: "center" }}>
            <div style={{ width: 80, height: 40, borderRadius: "50%", background: "#272733" }} />
            <div style={{ width: 80, height: 40, borderRadius: "50%", background: "#272733" }} />
          </div>
          <span style={{ fontSize: 13, color: "#c084fc", fontWeight: "bold", marginTop: 6, letterSpacing: 2 }}>FUNKTION-1</span>
        </div>

        {/* Sven Marquardt in center */}
        <div style={{ position: "absolute", left: "50%", transform: "translateX(-50%)", bottom: 130, display: "flex", flexDirection: "column", alignItems: "center", opacity: 0.85 }}>
          <div style={{ width: 70, height: 75, background: "#1c1c24", borderRadius: "50% 50% 10% 10%", border: "2px solid #525264", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 24 }}>⛓️</span>
          </div>
          <div style={{ width: 110, height: 90, background: "#111116", borderTop: "3px solid #525264", textAlign: "center", paddingTop: 4 }}>
            <span style={{ fontSize: 11, color: "#a1a1aa", fontWeight: "bold", letterSpacing: 3 }}>SVEN</span>
          </div>
          <div style={{ background: "rgba(0,0,0,0.85)", border: "1px solid #7f1d1d", padding: "2px 8px", marginTop: 4 }}>
            <span style={{ color: "#ef4444", fontSize: 11, fontWeight: "bold" }}>HEUTE LEIDER NICHT</span>
          </div>
        </div>

        {/* Stage Floor */}
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 110, background: "linear-gradient(0deg, #18181f 0%, #25252f 100%)", borderTop: "4px solid #4a4a5a", display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0 60px", color: "#71717a", fontSize: 14 }}>
          <span>CRUEL LABEL [CONDE CERO · BILBAO]</span>
          <span>STAGE: {isRound1 ? "BERGHAIN MAIN FLOOR (DARKROOM)" : "PANORAMA BAR (08:30 AM)"}</span>
          <span>140 BPM STEREO MASTER</span>
        </div>
      </div>

      {/* TOP STREET FIGHTER HUD */}
      <div style={{ position: "absolute", top: 30, left: 40, right: 40, height: 100, zIndex: 50 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 180px 1fr", alignItems: "center", gap: 24 }}>
          {/* P1: CONDE CERO */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Img src={staticFile("condecero_logo.jpg")} style={{ width: 34, height: 34, borderRadius: 4, border: "1px solid #eab308" }} />
                <span style={{ fontSize: 24, fontWeight: "900", color: "#facc15", letterSpacing: 2 }}>CONDE CERO</span>
              </div>
              <span style={{ fontSize: 18, color: "#a1a1aa" }}>{czHP} / 1000</span>
            </div>
            <div style={{ width: "100%", height: 30, background: "#27272a", border: "3px solid #71717a", position: "relative" }}>
              <div style={{ position: "absolute", top: 0, right: 0, height: "100%", width: `${(czHP / 1000) * 100}%`, background: "linear-gradient(270deg, #facc15, #eab308, #ca8a04)", transition: "width 0.1s" }} />
            </div>
          </div>

          {/* CENTER: TIMER */}
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 14, color: "#ef4444", fontWeight: "bold", letterSpacing: 2 }}>
              {isRound1 ? "ROUND 1" : "ROUND 2"}
            </div>
            <div style={{ fontSize: 52, fontWeight: "900", color: "#fef08a", background: "#000", border: "3px solid #eab308", borderRadius: 8, padding: "0 10px", margin: "4px 0", boxShadow: "0 0 20px rgba(234,179,8,0.6)" }}>
              {Math.max(0, Math.floor(180 - (roundFrame / 30) * 2))}
            </div>
            <div style={{ fontSize: 11, color: "#a1a1aa", letterSpacing: 3 }}>BERGHAIN</div>
          </div>

          {/* P2: RIVAL */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
              <span style={{ fontSize: 18, color: "#a1a1aa" }}>{rivalHP} / 1000</span>
              <span style={{ fontSize: 24, fontWeight: "900", color: isRound1 ? "#4ade80" : "#f472b6", letterSpacing: 2 }}>
                {isRound1 ? "FETO INFINITO" : "NIÑA KRAVITZ"}
              </span>
            </div>
            <div style={{ width: "100%", height: 30, background: "#27272a", border: "3px solid #71717a", position: "relative" }}>
              <div style={{ position: "absolute", top: 0, left: 0, height: "100%", width: `${(rivalHP / 1000) * 100}%`, background: isRound1 ? "linear-gradient(90deg, #4ade80, #22c55e, #15803d)" : "linear-gradient(90deg, #f472b6, #ec4899, #be185d)", transition: "width 0.1s" }} />
            </div>
          </div>
        </div>
      </div>

      {/* FLYING PROJECTILES IN AIR */}
      {projectile && (
        <div style={{ position: "absolute", left: projectile.x, top: projectile.y, zIndex: 60 }}>
          {projectile.type === "hickhack" && (
            <div style={{ width: 80, height: 80, borderRadius: "50%", background: "conic-gradient(from 0deg, #facc15, #ca8a04, transparent, #facc15)", border: "3px solid #fef08a", boxShadow: "0 0 30px #facc15", transform: `rotate(${frame * 35}deg)` }} />
          )}
          {projectile.type === "placenta" && (
            <div style={{ width: 70, height: 70, borderRadius: "40% 60% 70% 30%", background: "#22c55e", boxShadow: "0 0 35px #4ade80", filter: "blur(2px)", transform: `rotate(${frame * 20}deg)` }} />
          )}
          {projectile.type === "whip" && (
            <div style={{ position: "absolute", right: 0, top: 0, width: 900, height: 12, background: "linear-gradient(90deg, #a855f7, #22c55e, #c084fc)", boxShadow: "0 0 25px #a855f7", transformOrigin: "right center", transform: `rotate(${Math.sin(frame * 2) * 15}deg)` }} />
          )}
          {projectile.type === "acid303" && (
            <div style={{ width: 120, height: 16, background: "linear-gradient(90deg, #ec4899, #38bdf8)", boxShadow: "0 0 30px #ec4899", borderRadius: 8 }} />
          )}
          {projectile.type === "bathtub" && (
            <div style={{ width: 120, height: 60, background: "rgba(56, 189, 248, 0.4)", border: "3px solid #38bdf8", borderRadius: 30, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>
              🛁
            </div>
          )}
        </div>
      )}

      {/* FLOATING DAMAGE POPUP */}
      {damagePopup && (
        <div style={{ position: "absolute", left: damagePopup.x, top: damagePopup.y, zIndex: 70, background: "rgba(0,0,0,0.9)", border: `2px solid ${damagePopup.color}`, padding: "6px 14px", borderRadius: 8, boxShadow: `0 0 25px ${damagePopup.color}`, animation: "bounce 0.2s" }}>
          <span style={{ fontSize: 22, fontWeight: "900", color: damagePopup.color, letterSpacing: 2 }}>{damagePopup.text}</span>
        </div>
      )}

      {/* FIGHTER 1: CONDE CERO (BILBAO) */}
      <div
        style={{
          position: "absolute",
          bottom: czPosY,
          left: czPosX,
          transform: `scale(${czScale}) rotate(${czRot}deg)`,
          transition: "left 0.1s, bottom 0.1s, transform 0.1s",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 35,
        }}
      >
        {dialogueCZ && (
          <div style={{ background: "#18181b", border: "3px solid #facc15", borderRadius: 12, padding: "10px 16px", maxWidth: 340, marginBottom: 16, boxShadow: "0 0 20px rgba(234,179,8,0.6)" }}>
            <span style={{ color: "#fef08a", fontSize: 16, fontWeight: "bold", lineHeight: 1.2 }}>{dialogueCZ}</span>
          </div>
        )}

        <div style={{ position: "relative" }}>
          <Img
            src={staticFile("conde_cero_fighter.jpg")}
            style={{
              width: 320,
              filter: czAttackState === "hit" ? "brightness(3) contrast(2)" : "drop-shadow(0 0 35px rgba(234,179,8,0.7)) contrast(1.2)",
            }}
          />
          {/* DJ Mixer */}
          <div style={{ position: "absolute", bottom: -10, left: -20, right: -20, height: 60, background: "#09090b", border: "3px solid #3f3f46", borderRadius: 8, display: "flex", justifyContent: "space-around", alignItems: "center", padding: "0 14px" }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "#27272a", border: "2px solid #eab308", transform: `rotate(${frame * 6}deg)` }} />
            <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
              <div style={{ width: 45, height: 4, background: "#ef4444" }} />
              <div style={{ width: 45, height: 4, background: "#facc15" }} />
              <div style={{ width: 45, height: 4, background: "#22c55e" }} />
            </div>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "#27272a", border: "2px solid #38bdf8", transform: `rotate(${frame * 6}deg)` }} />
          </div>
        </div>
        <div style={{ background: "rgba(0,0,0,0.85)", border: "2px solid #eab308", padding: "4px 14px", marginTop: 18, fontSize: 14, fontWeight: "bold", color: "#facc15", letterSpacing: 2 }}>
          CONDE CERO · BILBAO
        </div>
      </div>

      {/* FIGHTER 2: RIVAL */}
      <div
        style={{
          position: "absolute",
          bottom: rivalPosY,
          right: rivalPosX,
          transform: `scale(${rivalScale}) rotate(${rivalRot}deg)`,
          transition: "right 0.1s, bottom 0.1s, transform 0.1s",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 35,
        }}
      >
        {dialogueRival && (
          <div style={{ background: "#09090b", border: `3px solid ${isRound1 ? "#4ade80" : "#f472b6"}`, borderRadius: 12, padding: "10px 16px", maxWidth: 340, marginBottom: 16, boxShadow: `0 0 20px ${isRound1 ? "rgba(34,197,94,0.6)" : "rgba(244,63,94,0.6)"}` }}>
            <span style={{ color: isRound1 ? "#86efac" : "#fbcfe8", fontSize: 16, fontWeight: "bold", lineHeight: 1.2 }}>{dialogueRival}</span>
          </div>
        )}

        {isRound1 ? (
          <div style={{ position: "relative" }}>
            <Img
              src={staticFile("feto_infinito.jpg")}
              style={{
                width: 290,
                borderRadius: 24,
                filter: rivalAttackState === "hit" ? "brightness(3) contrast(2)" : "drop-shadow(0 0 35px rgba(34,197,94,0.8)) saturate(1.4)",
                border: "4px solid rgba(34,197,94,0.4)",
              }}
            />
            <div style={{ background: "rgba(0,0,0,0.85)", border: "2px solid #22c55e", padding: "4px 14px", marginTop: 18, fontSize: 14, fontWeight: "bold", color: "#4ade80", letterSpacing: 2, textAlign: "center" }}>
              FETO INFINITO · DARKROOM
            </div>
          </div>
        ) : (
          <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ width: 280, height: 380, background: "linear-gradient(180deg, #18181b 0%, #000 100%)", borderRadius: 24, border: "4px solid #ec4899", boxShadow: "0 0 40px rgba(236,72,153,0.7)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "space-between", padding: 18, filter: rivalAttackState === "hit" ? "brightness(3) contrast(2)" : "none" }}>
              <div style={{ width: 140, height: 140, borderRadius: "50%", background: "#27272a", border: "4px solid #f472b6", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 65 }}>
                👩🏻‍🎤
              </div>
              <div style={{ width: "90%", height: 60, background: "#d4d4d8", borderRadius: 6, border: "2px solid #71717a", display: "flex", alignItems: "center", justifyContent: "space-around", padding: "0 8px", color: "#000", fontWeight: "900", fontSize: 13 }}>
                <span>ROLAND TB-303</span>
                <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#ef4444" }} />
              </div>
              <span style={{ fontSize: 14, color: "#f472b6", fontWeight: "bold", letterSpacing: 2 }}>TRIP RECORDINGS</span>
            </div>
            <div style={{ background: "rgba(0,0,0,0.85)", border: "2px solid #ec4899", padding: "4px 14px", marginTop: 18, fontSize: 14, fontWeight: "bold", color: "#f472b6", letterSpacing: 2 }}>
              NIÑA KRAVITZ · SIBERIA
            </div>
          </div>
        )}
      </div>

      {/* DOUBLE KO OVERLAY */}
      {showDoubleKO && (
        <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.88)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <h1 style={{ fontSize: 92, fontWeight: "900", color: "#ef4444", letterSpacing: 6, textShadow: "0 0 40px rgba(239,68,68,1)", margin: 0 }}>
            DOUBLE K.O.!!
          </h1>
          <p style={{ fontSize: 32, fontWeight: "bold", color: "#facc15", letterSpacing: 4, marginTop: 16 }}>
            {isRound1 ? "BERGHAIN IS CLOSED · HEUTE LEIDER NICHT" : "PANORAMA BAR IS DESTROYED · HEUTE LEIDER NICHT"}
          </p>
        </div>
      )}

      {/* CRT SCANLINE OVERLAY */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03))",
          backgroundSize: "100% 4px, 4px 100%",
          pointerEvents: "none",
          zIndex: 80,
        }}
      />
    </AbsoluteFill>
  );
};
