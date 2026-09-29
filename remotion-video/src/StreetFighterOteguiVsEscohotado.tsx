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

export const StreetFighterOteguiVsEscohotado: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // 135 BPM sub-bass pulse (approx 13.3 frames per beat)
  const pumpSub = interpolate(frame % 13, [0, 6, 12], [1, 1.07, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Dynamic Camera Shake & Flash
  let camShakeX = 0;
  let camShakeY = 0;
  let camZoom = 1.0;
  let flashWhite = 0;

  // Health Points (Start: 1000)
  let oteHP = 1000;
  let escoHP = 1000;

  // Fighter States
  let oteState: "idle" | "shuriken" | "excel" | "super" | "hit" | "ko" = "idle";
  let escoState: "idle" | "book" | "laser" | "super" | "hit" | "ko" = "idle";

  // Subtitles & Dialogue Speech Bubbles
  let oteDialogue: string | null = null;
  let escoDialogue: string | null = null;
  let oteTalking = false;
  let escoTalking = false;

  // Projectiles & Special FX
  let projectile:
    | { type: "vinyl_shuriken"; x: number; y: number; rot: number }
    | { type: "book_tomo"; x: number; y: number; rot: number }
    | { type: "excel_macro"; x: number; y: number }
    | { type: "laser_beam"; progress: number }
    | { type: "super_clash"; progress: number }
    | null = null;

  let damagePopup: { text: string; x: number; y: number; color: string } | null = null;
  let announceBanner: { text: string; sub: string; color: string } | null = null;

  // --- TIMELINE CONTROLLER (Frames @ 30fps) ---

  // 0..75: Intro Announcement
  if (frame < 75) {
    announceBanner = { text: "ROUND 1", sub: "FIGHT!", color: "#facc15" };
  }

  // 75..240: Otegui Intro Speech
  if (frame >= 75 && frame < 240) {
    oteDialogue = "¡Escohotado, deja de filosofar, que el calor de Praga me está doblando los vinilos de 180 gramos!";
    oteTalking = true;
  }

  // 240..435: Escohotado Intro Speech
  if (frame >= 240 && frame < 435) {
    escoDialogue = "Gorka, querido amigo... el comercio no tiene enemigos; el miedo es la única prisión.";
    escoTalking = true;
  }

  // 435..580: Otegui Attack 1: VINYL SHURIKEN
  if (frame >= 435 && frame < 580) {
    oteDialogue = "¡Aupa Borja, me dice Mario que me habéis metido a pelear en Street Fighter contra Escohotado!";
    oteTalking = frame < 520;
    if (frame >= 490 && frame < 555) {
      oteState = "shuriken";
      const p = (frame - 490) / 65;
      projectile = {
        type: "vinyl_shuriken",
        x: interpolate(p, [0, 1], [460, 1460]),
        y: interpolate(p, [0, 0.5, 1], [640, 580, 630]),
        rot: frame * 45,
      };
      if (frame >= 548) {
        escoState = "hit";
        camShakeX = Math.sin(frame * 2.5) * 16;
        camShakeY = Math.cos(frame * 2.5) * 10;
        damagePopup = { text: "-140 HP VINILAZO 180G!", x: 1460, y: 520, color: "#f59e0b" };
      }
    }
  }
  if (frame >= 550) escoHP -= 140;

  // 630..780: Escohotado Attack 1: TOMO III HISTORIA GENERAL DE LAS DROGAS
  if (frame >= 630 && frame < 790) {
    escoDialogue = "¡Siente la gravedad del Tomo Tres de la Historia de las Drogas!";
    escoTalking = frame < 730;
    if (frame >= 700 && frame < 765) {
      escoState = "book";
      const p = (frame - 700) / 65;
      projectile = {
        type: "book_tomo",
        x: interpolate(p, [0, 1], [1460, 460]),
        y: interpolate(p, [0, 0.4, 1], [620, 500, 640]),
        rot: frame * 25,
      };
      if (frame >= 758) {
        oteState = "hit";
        camShakeX = Math.sin(frame * 3) * 18;
        camShakeY = Math.cos(frame * 3) * 12;
        damagePopup = { text: "-160 HP TOMO III!", x: 460, y: 520, color: "#eab308" };
      }
    }
  }
  if (frame >= 760) oteHP -= 160;

  // 840..1000: Otegui Attack 2: MACRO DE EXCEL ASESINA
  if (frame >= 840 && frame < 1000) {
    oteDialogue = "¡Pero a ver, ¿qué coño me estás contando?! ¡Si estoy aquí liado con los albaranes de Busca Records!";
    oteTalking = frame < 940;
    if (frame >= 910 && frame < 975) {
      oteState = "excel";
      const p = (frame - 910) / 65;
      projectile = {
        type: "excel_macro",
        x: interpolate(p, [0, 1], [460, 1460]),
        y: 630,
      };
      if (frame >= 968) {
        escoState = "hit";
        camShakeX = Math.sin(frame * 3) * 20;
        damagePopup = { text: "-220 HP ERROR REF CIRCULAR!", x: 1440, y: 500, color: "#10b981" };
      }
    }
  }
  if (frame >= 970) escoHP -= 220;

  // 1050..1200: Escohotado Attack 2: RAYO DE EMPIRISMO PURO
  if (frame >= 1050 && frame < 1200) {
    escoDialogue = "¡Rayo de empirismo puro! Cero dogma, cien por cien principio activo.";
    escoTalking = frame < 1130;
    if (frame >= 1110 && frame < 1175) {
      escoState = "laser";
      const p = (frame - 1110) / 65;
      projectile = {
        type: "laser_beam",
        progress: p,
      };
      if (frame >= 1150) {
        oteState = "hit";
        flashWhite = interpolate(frame, [1150, 1155, 1175], [0.35, 0.4, 0]);
        camShakeX = Math.sin(frame * 4) * 24;
        camShakeY = Math.cos(frame * 4) * 18;
        damagePopup = { text: "-240 HP DOSIS EMPÍRICA!", x: 460, y: 490, color: "#38bdf8" };
      }
    }
  }
  if (frame >= 1160) oteHP -= 240;

  // 1200..1375: SUPER CLASH (Furia de Landauer vs Enemigos del Comercio)
  if (frame >= 1200 && frame < 1375) {
    if (frame < 1260) {
      oteDialogue = "¡Y el calor de Praga me va a doblar los vinilos de ciento ochenta gramos, cagüendios!";
      oteTalking = true;
    } else if (frame < 1320) {
      escoDialogue = "¡El comercio libre entre hombres despiertos jamás será vencido!";
      escoTalking = true;
    }

    if (frame >= 1320 && frame < 1375) {
      oteState = "super";
      escoState = "super";
      camZoom = interpolate(frame, [1320, 1370], [1.0, 1.25]);
      announceBanner = { text: "SUPER COMBO", sub: "MID-AIR IMPACT!", color: "#ef4444" };
      projectile = {
        type: "super_clash",
        progress: (frame - 1320) / 55,
      };
    }
  }

  // 1375..1500: NUCLEAR COLLISION & DOUBLE K.O.
  if (frame >= 1375) {
    oteHP = 0;
    escoHP = 0;
    oteState = "ko";
    escoState = "ko";
    if (frame < 1400) {
      flashWhite = interpolate(frame, [1375, 1380, 1400], [0.5, 0.4, 0]);
      camShakeX = Math.sin(frame * 5) * 35;
      camShakeY = Math.cos(frame * 5) * 30;
    }
    announceBanner = { text: "DOUBLE K.O.!!", sub: "VINYLS & COMMERCE PRESERVED", color: "#ef4444" };
  }

  // Fighter X Positions
  let otePosX = 360;
  let escoPosX = 360; // Distance from right

  if (oteState === "super") {
    otePosX = interpolate(frame, [1320, 1370], [360, 840]);
  } else if (oteState === "ko") {
    otePosX = 240;
  }

  if (escoState === "super") {
    escoPosX = interpolate(frame, [1320, 1370], [360, 840]);
  } else if (escoState === "ko") {
    escoPosX = 240;
  }

  // Mouth flapping animations
  const oteMouthOpen = oteTalking ? Math.abs(Math.sin(frame * 0.9)) * 14 : 0;
  const escoMouthOpen = escoTalking ? Math.abs(Math.sin(frame * 0.75)) * 16 : 0;

  // Stance bouncing
  const oteBounce = oteState === "ko" ? 0 : Math.sin(frame * 0.25) * 6;
  const escoBounce = escoState === "ko" ? 0 : Math.cos(frame * 0.22) * 5;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#09090b",
        overflow: "hidden",
        fontFamily: "'Impact', 'Arial Black', sans-serif",
        transform: `scale(${camZoom}) translate(${camShakeX}px, ${camShakeY}px)`,
        transformOrigin: "center center",
      }}
    >
      {/* MASTER STEREO AUDIO */}
      <Audio src={staticFile("sf_otegui_escohotado_master.mp3")} />

      {/* BACKGROUND STAGE: RETRO ARCADE PRAGA VINYL PRESSING PLANT */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(circle at 50% 35%, #271d3b 0%, #11101d 60%, #08070d 100%)",
        }}
      >
        {/* Neon City / Pressing Plant Grid */}
        <div
          style={{
            position: "absolute",
            top: 60,
            left: 0,
            right: 0,
            height: 380,
            background: "linear-gradient(180deg, rgba(245,158,11,0.06) 0%, transparent 100%)",
            display: "flex",
            justifyContent: "space-around",
            alignItems: "flex-end",
            opacity: 0.35,
          }}
        >
          {/* Neon Signs */}
          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <span style={{ fontSize: 26, color: "#f59e0b", letterSpacing: 8, textShadow: "0 0 20px #f59e0b" }}>
              BUSCA RECORDS · PRAGA PRESSING PLANT
            </span>
            <br />
            <span style={{ fontSize: 14, color: "#eab308", letterSpacing: 4 }}>
              180 GRAMS AUDIOPHILE VINYL FOUNDRY
            </span>
          </div>
        </div>

        {/* Backdrop Bookshelves & Vinyl Crates Silhouette */}
        <div
          style={{
            position: "absolute",
            bottom: 120,
            left: 0,
            right: 0,
            height: 300,
            background: "linear-gradient(0deg, #181824 0%, transparent 100%)",
            borderBottom: "4px solid #3f3f5a",
            display: "flex",
            justifyContent: "space-between",
            padding: "0 80px",
            alignItems: "flex-end",
            color: "#525266",
            fontSize: 13,
            letterSpacing: 2,
          }}
        >
          <div>📦 180G VINYL WAREHOUSE (38°C)</div>
          <div>📚 HISTORIA GENERAL ARCHIVES</div>
          <div>⚖️ EMPIRISMO PURO SECTOR</div>
        </div>

        {/* Industrial Stage Floor with Hazard Lines */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 120,
            background: "linear-gradient(0deg, #0f0f15 0%, #1f1f2e 100%)",
            borderTop: "6px solid #eab308",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0 60px",
            color: "#a1a1aa",
            fontSize: 15,
            fontWeight: "bold",
            letterSpacing: 2,
          }}
        >
          <span style={{ color: "#f59e0b" }}>P1: GORKA OTEGUI [BUSCA RECORDS]</span>
          <span style={{ color: "#facc15" }}>STAGE: PRAGA FOUNDRY // BATTLE OF THE ARCHIVE</span>
          <span style={{ color: "#38bdf8" }}>P2: ANTONIO ESCOHOTADO [EMPIRISMO]</span>
        </div>
      </div>

      {/* TOP STREET FIGHTER HUD */}
      <div style={{ position: "absolute", top: 25, left: 40, right: 40, height: 110, zIndex: 60 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 180px 1fr", alignItems: "center", gap: 24 }}>
          {/* P1: GORKA OTEGUI */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <Img
                  src={staticFile("faces/otegui_sf_portrait.png")}
                  style={{
                    width: 50,
                    height: 50,
                    borderRadius: 6,
                    border: "3px solid #f59e0b",
                    boxShadow: "0 0 15px rgba(245,158,11,0.7)",
                    backgroundColor: "#18181b",
                  }}
                />
                <div>
                  <div style={{ fontSize: 26, fontWeight: "900", color: "#f59e0b", letterSpacing: 2 }}>
                    GORKA OTEGUI
                  </div>
                  <div style={{ fontSize: 11, color: "#d97706", letterSpacing: 2 }}>"OTE" · BUSCA RECORDS</div>
                </div>
              </div>
              <span style={{ fontSize: 22, color: "#fef08a", fontWeight: "900" }}>{oteHP} / 1000</span>
            </div>
            {/* Health Bar Background */}
            <div style={{ width: "100%", height: 32, background: "#1c1917", border: "3px solid #78716c", position: "relative" }}>
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  right: 0,
                  height: "100%",
                  width: `${(oteHP / 1000) * 100}%`,
                  background: "linear-gradient(270deg, #f59e0b, #d97706, #b45309)",
                  boxShadow: "0 0 15px rgba(245,158,11,0.8)",
                  transition: "width 0.15s ease-out",
                }}
              />
            </div>
          </div>

          {/* CENTER: ARCADE TIMER & ROUND */}
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 14, color: "#ef4444", fontWeight: "900", letterSpacing: 3 }}>ROUND 1</div>
            <div
              style={{
                fontSize: 56,
                fontWeight: "900",
                color: "#fef08a",
                background: "#000",
                border: "3px solid #eab308",
                borderRadius: 10,
                padding: "0 14px",
                margin: "2px 0",
                boxShadow: "0 0 25px rgba(234,179,8,0.7)",
                display: "inline-block",
              }}
            >
              {Math.max(0, Math.floor(99 - (frame / 30) * 2))}
            </div>
            <div style={{ fontSize: 11, color: "#a1a1aa", letterSpacing: 3 }}>PRAGA 135 BPM</div>
          </div>

          {/* P2: ANTONIO ESCOHOTADO */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
              <span style={{ fontSize: 22, color: "#fef08a", fontWeight: "900" }}>{escoHP} / 1000</span>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 26, fontWeight: "900", color: "#38bdf8", letterSpacing: 2 }}>
                    A. ESCOHOTADO
                  </div>
                  <div style={{ fontSize: 11, color: "#0284c7", letterSpacing: 2 }}>EMPIRISMO RADICAL</div>
                </div>
                <Img
                  src={staticFile("faces/escohotado_sf_portrait.png")}
                  style={{
                    width: 50,
                    height: 50,
                    borderRadius: 6,
                    border: "3px solid #38bdf8",
                    boxShadow: "0 0 15px rgba(56,189,248,0.7)",
                    backgroundColor: "#18181b",
                  }}
                />
              </div>
            </div>
            {/* Health Bar Background */}
            <div style={{ width: "100%", height: 32, background: "#1c1917", border: "3px solid #78716c", position: "relative" }}>
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  height: "100%",
                  width: `${(escoHP / 1000) * 100}%`,
                  background: "linear-gradient(90deg, #38bdf8, #0284c7, #0369a1)",
                  boxShadow: "0 0 15px rgba(56,189,248,0.8)",
                  transition: "width 0.15s ease-out",
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* FLYING PROJECTILES IN AIR */}
      {projectile && (
        <>
          {/* Vinyl Shuriken (180g Spinning Disc with Yellow Label) */}
          {projectile.type === "vinyl_shuriken" && (
            <div
              style={{
                position: "absolute",
                left: projectile.x,
                top: projectile.y,
                width: 100,
                height: 100,
                borderRadius: "50%",
                background: "radial-gradient(circle, #f59e0b 22%, #000 23%, #18181b 80%, #000 100%)",
                border: "3px solid #facc15",
                boxShadow: "0 0 35px #f59e0b",
                transform: `rotate(${projectile.rot}deg)`,
                zIndex: 70,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#000", border: "1px solid #fff" }} />
              <div
                style={{
                  position: "absolute",
                  fontSize: 9,
                  fontWeight: "bold",
                  color: "#000",
                  letterSpacing: 1,
                  transform: "rotate(45deg)",
                }}
              >
                180G
              </div>
            </div>
          )}

          {/* Tomo III Historia de las Drogas (Flying Massive Book) */}
          {projectile.type === "book_tomo" && (
            <div
              style={{
                position: "absolute",
                left: projectile.x,
                top: projectile.y,
                width: 120,
                height: 80,
                background: "linear-gradient(135deg, #78350f 0%, #451a03 100%)",
                border: "3px solid #facc15",
                borderRadius: 8,
                boxShadow: "0 0 40px rgba(250,204,21,0.8)",
                transform: `rotate(${projectile.rot}deg)`,
                zIndex: 70,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: 4,
                color: "#fef08a",
              }}
            >
              <span style={{ fontSize: 13, fontWeight: "900", letterSpacing: 1 }}>TOMO III</span>
              <span style={{ fontSize: 9, color: "#facc15" }}>HISTORIA DROGAS</span>
              <div style={{ width: "90%", height: 3, background: "#facc15", marginTop: 4 }} />
            </div>
          )}

          {/* Excel Macro Cascade (Glowing Green Matrix) */}
          {projectile.type === "excel_macro" && (
            <div
              style={{
                position: "absolute",
                left: projectile.x,
                top: projectile.y,
                width: 150,
                height: 90,
                background: "rgba(16, 185, 129, 0.25)",
                border: "3px solid #10b981",
                borderRadius: 8,
                boxShadow: "0 0 40px #10b981",
                zIndex: 70,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-around",
                padding: "6px 12px",
                color: "#a7f3d0",
                fontSize: 13,
                fontWeight: "900",
                transform: `rotate(${Math.sin(frame * 0.5) * 10}deg)`,
              }}
            >
              <div>=VLOOKUP(OTE, A1:Z99, 2)</div>
              <div style={{ color: "#ef4444" }}>#REF! CIRCULAR ERROR</div>
              <div>=SUM(PRAGA:180G)</div>
            </div>
          )}

          {/* Rayo de Empirismo Puro (Screen-Crossing Golden/Cyan Laser) */}
          {projectile.type === "laser_beam" && (
            <div
              style={{
                position: "absolute",
                left: 380,
                top: 610,
                width: 1160,
                height: 38,
                background: "linear-gradient(90deg, #38bdf8 0%, #facc15 50%, #ffffff 100%)",
                boxShadow: "0 0 50px #38bdf8, 0 0 80px #facc15",
                borderRadius: 20,
                zIndex: 75,
                opacity: interpolate(projectile.progress, [0, 0.3, 0.8, 1], [0, 1, 1, 0]),
              }}
            />
          )}

          {/* Super Clash Particle Vortex */}
          {projectile.type === "super_clash" && (
            <div
              style={{
                position: "absolute",
                left: 960 - 150,
                top: 550,
                width: 300,
                height: 300,
                borderRadius: "50%",
                background: "radial-gradient(circle, #ffffff 10%, #facc15 35%, #ef4444 70%, transparent 100%)",
                boxShadow: "0 0 100px #facc15, 0 0 150px #ef4444",
                transform: `scale(${interpolate(projectile.progress, [0, 1], [0.4, 2.2])})`,
                zIndex: 80,
              }}
            />
          )}
        </>
      )}

      {/* FLOATING DAMAGE POPUP */}
      {damagePopup && (
        <div
          style={{
            position: "absolute",
            left: damagePopup.x - 120,
            top: damagePopup.y,
            zIndex: 85,
            background: "rgba(0,0,0,0.92)",
            border: `3px solid ${damagePopup.color}`,
            padding: "8px 18px",
            borderRadius: 10,
            boxShadow: `0 0 35px ${damagePopup.color}`,
          }}
        >
          <span style={{ fontSize: 24, fontWeight: "900", color: damagePopup.color, letterSpacing: 2 }}>
            {damagePopup.text}
          </span>
        </div>
      )}

      {/* ARCADE BANNER OVERLAY (ROUND 1, SUPER COMBO, DOUBLE KO) */}
      {announceBanner && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 90,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              fontSize: 96,
              fontWeight: "900",
              color: announceBanner.color,
              letterSpacing: 6,
              textShadow: `0 0 50px ${announceBanner.color}, 0 0 100px #000`,
              textAlign: "center",
            }}
          >
            {announceBanner.text}
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: "bold",
              color: "#fff",
              letterSpacing: 4,
              textShadow: "0 0 25px #000",
              marginTop: 12,
            }}
          >
            {announceBanner.sub}
          </div>
        </div>
      )}

      {/* FIGHTER 1: GORKA OTEGUI («OTE») */}
      <div
        style={{
          position: "absolute",
          bottom: 110 + oteBounce,
          left: otePosX,
          zIndex: 40,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: oteState === "hit" ? "scale(1.08) rotate(-8deg)" : oteState === "ko" ? "rotate(-85deg) translateY(120px)" : "scale(1.0)",
          transition: "left 0.1s, transform 0.1s",
        }}
      >
        {/* Dialogue Bubble */}
        {oteDialogue && (
          <div
            style={{
              background: "#18181b",
              border: "3px solid #f59e0b",
              borderRadius: 14,
              padding: "10px 18px",
              maxWidth: 380,
              marginBottom: 16,
              boxShadow: "0 0 25px rgba(245,158,11,0.7)",
              textAlign: "center",
            }}
          >
            <span style={{ color: "#fef08a", fontSize: 17, fontWeight: "bold", lineHeight: 1.25 }}>
              {oteDialogue}
            </span>
          </div>
        )}

        {/* Character Head & Body */}
        <div style={{ position: "relative", width: 280, height: 420, display: "flex", flexDirection: "column", alignItems: "center" }}>
          {/* Real Photo Head with Animated Jaw */}
          <div
            style={{
              position: "relative",
              width: 190,
              height: 220,
              filter: oteState === "hit" ? "brightness(3) contrast(2)" : "drop-shadow(0 0 25px rgba(245,158,11,0.6))",
              zIndex: 10,
            }}
          >
            {/* Top Head (Cap, Sunglasses, Nose) */}
            <Img
              src={staticFile("faces/otegui_real_top.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                objectFit: "contain",
              }}
            />
            {/* Lower Jaw & Beard (Opens/Flaps when speaking!) */}
            <Img
              src={staticFile("faces/otegui_real_jaw.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                objectFit: "contain",
                transform: `translateY(${oteMouthOpen}px)`,
              }}
            />
          </div>

          {/* Fighter Body: Athletic Martial Stance with DJ/Vinyl Belts */}
          <div
            style={{
              position: "absolute",
              top: 170,
              width: 220,
              height: 250,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              zIndex: 5,
            }}
          >
            {/* Torso & Black Athletic Shirt with Fighting Arms */}
            <div style={{ position: "relative", width: 280, display: "flex", justifyContent: "center" }}>
              {/* Left Guard Arm (Boxing Stance) */}
              <div
                style={{
                  position: "absolute",
                  left: 10,
                  top: 10,
                  width: 36,
                  height: 100,
                  background: "#18181b",
                  border: "3px solid #f59e0b",
                  borderRadius: 18,
                  transform: `rotate(${Math.sin(frame * 0.2) * 8 - 35}deg)`,
                  transformOrigin: "top center",
                  boxShadow: "0 0 15px rgba(245,158,11,0.5)",
                }}
              >
                {/* Yellow Boxing Fist */}
                <div
                  style={{
                    position: "absolute",
                    bottom: -15,
                    left: -6,
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "#f59e0b",
                    border: "3px solid #000",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 18,
                  }}
                >
                  👊
                </div>
              </div>

              {/* Main Torso */}
              <div
                style={{
                  width: 180,
                  height: 145,
                  background: "linear-gradient(180deg, #18181b 0%, #27272a 100%)",
                  borderRadius: "20px 20px 8px 8px",
                  border: "3px solid #f59e0b",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 25px rgba(0,0,0,0.8)",
                  position: "relative",
                  zIndex: 2,
                }}
              >
                <span style={{ fontSize: 14, fontWeight: "900", color: "#f59e0b", letterSpacing: 2 }}>
                  BUSCA RECORDS
                </span>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "#f59e0b",
                    marginTop: 6,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    border: "2px solid #fff",
                  }}
                >
                  <span style={{ fontSize: 20 }}>💿</span>
                </div>
              </div>

              {/* Right Lead Arm (Punch Ready) */}
              <div
                style={{
                  position: "absolute",
                  right: 10,
                  top: 10,
                  width: 36,
                  height: 100,
                  background: "#18181b",
                  border: "3px solid #f59e0b",
                  borderRadius: 18,
                  transform: `rotate(${Math.cos(frame * 0.2) * 8 + 35}deg)`,
                  transformOrigin: "top center",
                  boxShadow: "0 0 15px rgba(245,158,11,0.5)",
                }}
              >
                {/* Yellow Boxing Fist */}
                <div
                  style={{
                    position: "absolute",
                    bottom: -15,
                    left: -6,
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "#f59e0b",
                    border: "3px solid #000",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 18,
                  }}
                >
                  👊
                </div>
              </div>
            </div>

            {/* Belt & Turntable Buckle */}
            <div
              style={{
                width: 190,
                height: 28,
                background: "#09090b",
                border: "2px solid #78716c",
                borderRadius: 4,
                marginTop: -4,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 2,
              }}
            >
              <div style={{ width: 22, height: 22, borderRadius: "50%", background: "#f59e0b", border: "2px solid #fff" }} />
            </div>

            {/* Fighting Stance Legs */}
            <div style={{ display: "flex", gap: 42, marginTop: 4, zIndex: 2 }}>
              <div style={{ width: 48, height: 100, background: "#18181b", border: "2px solid #f59e0b", borderRadius: "6px 6px 14px 14px", transform: "rotate(-12deg)" }} />
              <div style={{ width: 48, height: 100, background: "#18181b", border: "2px solid #f59e0b", borderRadius: "6px 6px 14px 14px", transform: "rotate(12deg)" }} />
            </div>
          </div>
        </div>

        {/* Character Title Plate */}
        <div
          style={{
            background: "rgba(0,0,0,0.88)",
            border: "2px solid #f59e0b",
            padding: "4px 16px",
            marginTop: 8,
            fontSize: 14,
            fontWeight: "900",
            color: "#f59e0b",
            letterSpacing: 2,
          }}
        >
          GORKA OTEGUI · BILBAO
        </div>
      </div>

      {/* FIGHTER 2: ANTONIO ESCOHOTADO */}
      <div
        style={{
          position: "absolute",
          bottom: 110 + escoBounce,
          right: escoPosX,
          zIndex: 40,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: escoState === "hit" ? "scale(1.08) rotate(8deg)" : escoState === "ko" ? "rotate(85deg) translateY(120px)" : "scale(1.0)",
          transition: "right 0.1s, transform 0.1s",
        }}
      >
        {/* Dialogue Bubble */}
        {escoDialogue && (
          <div
            style={{
              background: "#09090b",
              border: "3px solid #38bdf8",
              borderRadius: 14,
              padding: "10px 18px",
              maxWidth: 380,
              marginBottom: 16,
              boxShadow: "0 0 25px rgba(56,189,248,0.7)",
              textAlign: "center",
            }}
          >
            <span style={{ color: "#bae6fd", fontSize: 17, fontWeight: "bold", lineHeight: 1.25 }}>
              {escoDialogue}
            </span>
          </div>
        )}

        {/* Character Head & Body */}
        <div style={{ position: "relative", width: 280, height: 420, display: "flex", flexDirection: "column", alignItems: "center" }}>
          {/* Real Photo Head with Animated Jaw */}
          <div
            style={{
              position: "relative",
              width: 200,
              height: 220,
              filter: escoState === "hit" ? "brightness(3) contrast(2)" : "drop-shadow(0 0 25px rgba(56,189,248,0.6))",
              zIndex: 10,
            }}
          >
            {/* Top Head */}
            <Img
              src={staticFile("faces/escohotado_top.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                objectFit: "contain",
              }}
            />
            {/* Lower Jaw & Beard (Opens/Flaps when speaking!) */}
            <Img
              src={staticFile("faces/escohotado_jaw.png")}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                objectFit: "contain",
                transform: `translateY(${escoMouthOpen}px)`,
              }}
            />
          </div>

          {/* Fighter Body: Sage Gi / Linen Robe with Amber Belt */}
          <div
            style={{
              position: "absolute",
              top: 170,
              width: 220,
              height: 250,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              zIndex: 5,
            }}
          >
            {/* Torso & Linen Tunic with Sage Martial Arms */}
            <div style={{ position: "relative", width: 280, display: "flex", justifyContent: "center" }}>
              {/* Left Sage Arm (Philosophical Guard) */}
              <div
                style={{
                  position: "absolute",
                  left: 10,
                  top: 10,
                  width: 36,
                  height: 100,
                  background: "#f4f4f5",
                  border: "3px solid #38bdf8",
                  borderRadius: 18,
                  transform: `rotate(${Math.sin(frame * 0.18) * 8 - 30}deg)`,
                  transformOrigin: "top center",
                  boxShadow: "0 0 15px rgba(56,189,248,0.5)",
                }}
              >
                {/* Sage Open Palm */}
                <div
                  style={{
                    position: "absolute",
                    bottom: -15,
                    left: -6,
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "#38bdf8",
                    border: "3px solid #fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 18,
                  }}
                >
                  ✋
                </div>
              </div>

              {/* Main Torso */}
              <div
                style={{
                  width: 180,
                  height: 145,
                  background: "linear-gradient(180deg, #f4f4f5 0%, #e4e4e7 100%)",
                  borderRadius: "20px 20px 8px 8px",
                  border: "3px solid #38bdf8",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 25px rgba(0,0,0,0.8)",
                  position: "relative",
                  zIndex: 2,
                }}
              >
                <span style={{ fontSize: 14, fontWeight: "900", color: "#0369a1", letterSpacing: 2 }}>
                  HISTORIA GENERAL
                </span>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "#38bdf8",
                    marginTop: 6,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    border: "2px solid #0284c7",
                  }}
                >
                  <span style={{ fontSize: 20 }}>⚖️</span>
                </div>
              </div>

              {/* Right Sage Arm (Open Palm Strike) */}
              <div
                style={{
                  position: "absolute",
                  right: 10,
                  top: 10,
                  width: 36,
                  height: 100,
                  background: "#f4f4f5",
                  border: "3px solid #38bdf8",
                  borderRadius: 18,
                  transform: `rotate(${Math.cos(frame * 0.18) * 8 + 30}deg)`,
                  transformOrigin: "top center",
                  boxShadow: "0 0 15px rgba(56,189,248,0.5)",
                }}
              >
                {/* Sage Open Palm */}
                <div
                  style={{
                    position: "absolute",
                    bottom: -15,
                    left: -6,
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "#38bdf8",
                    border: "3px solid #fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 18,
                  }}
                >
                  ✋
                </div>
              </div>
            </div>

            {/* Amber Sash */}
            <div
              style={{
                width: 190,
                height: 28,
                background: "#d97706",
                border: "2px solid #b45309",
                borderRadius: 4,
                marginTop: -4,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 2,
              }}
            >
              <div style={{ width: 22, height: 22, borderRadius: "50%", background: "#facc15", border: "2px solid #fff" }} />
            </div>

            {/* Fighting Stance Legs */}
            <div style={{ display: "flex", gap: 42, marginTop: 4, zIndex: 2 }}>
              <div style={{ width: 48, height: 100, background: "#f4f4f5", border: "2px solid #38bdf8", borderRadius: "6px 6px 14px 14px", transform: "rotate(-12deg)" }} />
              <div style={{ width: 48, height: 100, background: "#f4f4f5", border: "2px solid #38bdf8", borderRadius: "6px 6px 14px 14px", transform: "rotate(12deg)" }} />
            </div>
          </div>
        </div>

        {/* Character Title Plate */}
        <div
          style={{
            background: "rgba(0,0,0,0.88)",
            border: "2px solid #38bdf8",
            padding: "4px 16px",
            marginTop: 8,
            fontSize: 14,
            fontWeight: "900",
            color: "#38bdf8",
            letterSpacing: 2,
          }}
        >
          ANTONIO ESCOHOTADO · MADRID
        </div>
      </div>

      {/* WHITE FLASH SCREEN ON IMPACT */}
      {flashWhite > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "#fff",
            opacity: flashWhite,
            pointerEvents: "none",
            zIndex: 95,
          }}
        />
      )}

      {/* CRT SCANLINE & ARCADE BEZEL OVERLAY */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.28) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03))",
          backgroundSize: "100% 4px, 4px 100%",
          pointerEvents: "none",
          zIndex: 96,
        }}
      />
    </AbsoluteFill>
  );
};
