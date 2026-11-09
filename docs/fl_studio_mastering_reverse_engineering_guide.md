# Tratado de Ingeniería Inversa: Masterización Profesional en FL Studio 2025 (C5-REAL SOTA)

---

## 1. Introducción y Fundamentos Epistémicos
La masterización en estaciones de trabajo de audio digital (DAWs) ha estado históricamente rodeada de mitología retórica y *vibe coding* acústico. Este documento formaliza la ingeniería inversa del motor de masterización de **FL Studio 2025**, deconstruyendo:
1. El motor **FL Cloud AI Mastering** (basado en procesadores de precisión de **Tokyo Dawn Records**).
2. El procesador estrella nativo **Maximus** y su macro simplificado **Soundgoodizer**.
3. El paradigma moderno de **Soft Clipper previo a la Limitación** para maximizar sonoridad sin distorsión audible.
4. La verificación determinista de la señal mediante el **Linter Acústico Rubin** (Factor de Cresta, Planitud Espectral de Wiener y Coherencia de Fase).

---

## 2. Disección Forense de FL Cloud AI Mastering (Tokyo Dawn Records)
El análisis del binario de configuración interna `/Applications/FL Studio 2025.app/Contents/Resources/FL/System/Config/Master/references.txt` revela que el servicio de masterización inteligente de FL Studio integra un motor modular de 8 etapas gobernado por procesadores de Tokyo Dawn Records (TDR):

```
                        TOPOLOGÍA DE REFERENCIA TDR / FL CLOUD
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                                                                                  │
 │   Señal Mix ──► [1. TDR SlickEQ M] ──────► [2. TDR Kotelnikov GE]               │
 │                   • M/S Filtering            • Wideband RMS/Peak Glue            │
 │                   • Sub-Bass Cut (30-40Hz)   • Attack: 1-5ms / Release: 40-180ms  │
 │                   • Center Filter On                                             │
 │                            │                                                     │
 │                            ▼                                                     │
 │                 [3 & 4. TDR Nova GE] ─────► [5, 6, 7. Kotelnikov Stages]         │
 │                   • Multiband Dynamic Split  • Non-linear release shaping        │
 │                   • 3-band resonance taming                                      │
 │                            │                                                     │
 │                            ▼                                                     │
 │                 [8. TDR Limiter 6 GE] ───► Master Final EBU R128                 │
 │                   • Clipper Stage (1-2dB)    • Target: -8.5 a -14 LUFS           │
 │                   • HF Limiter (De-harsh)    • Ceiling: -0.3 a -1.0 dBTP         │
 │                   • True Peak 4x Oversample                                      │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

### Isomorfismo con la Cadena Nativa de FL Studio (Stock Plugins)
Para alcanzar resultados de nivel comercial sin recurrir a plugins de terceros o servicios en la nube, la topología TDR se mapea 1:1 sobre los procesadores nativos de FL Studio:

| Etapa TDR | Procesador FL Studio Nativo | Parámetros y Función Exacta |
| :--- | :--- | :--- |
| **TDR SlickEQ M** | **Fruity Parametric EQ 2** | Modo *Linear Phase* activado (evita dispersión de fase). Corte infrasónico a 25–35 Hz. Procesamiento Mid/Side cortando en Side frecuencias <120 Hz para forzar subgraves 100% mono. |
| **TDR Kotelnikov GE** | **Maximus (Master Band)** | Compresión de pegamento (Glue). Ratio suave 1.4:1 a 1.6:1, codo suave (*Soft Knee*), ataque de 2 a 5 ms y relajación adaptativa. |
| **TDR Nova GE** | **Maximus (Low / Mid / High)** | Crossovers en 120 Hz y 4.000 Hz. Banda Low con separación estéreo al 100% a la derecha (Mono). Banda Mid preservando dinámica de caja y voz. Banda High con ligera expansión o de-essing. |
| **TDR Limiter 6 GE (Clipper)** | **Fruity Soft Clipper** | Recorte armónico tangencial ($\tanh$) de los picos transitorios superiores a -2.5 dBFS. Afeita 1.5–2.5 dB de cresta antes de atacar el limitador. |
| **TDR Limiter 6 GE (Brickwall)** | **Fruity Limiter** | Techo de pico verdadero (*Ceiling*) configurado a -0.3 dBTP (club) o -1.0 dBTP (streaming). Lookahead de 2 a 4 ms para erradicar picos inter-muestra (ISP). |

---

## 3. Deconstrucción Matemática de Maximus y Soundgoodizer

### El Misterio de Soundgoodizer Resuelto
Soundgoodizer es un envoltorio (*wrapper*) gráfico de un canal de **Maximus** con curvas y factores de compresión/saturación preconfigurados:

1. **Preset A (Punch & Air):**
   * Curva de Maximus con expansión y compresión ascendente en medios-graves.
   * Realce en frecuencias bajas (80–120 Hz) y estante de agudos brillante (>10 kHz).
   * Separación estéreo abierta en frecuencias altas.
2. **Preset B (Warm Tape Saturation):**
   * Curva de saturación cálida no lineal en la banda media.
   * Reducción de armónicos impares estridentes, emulando la histéresis de cinta magnética de 1/2 pulgada.
3. **Preset C (Aggressive Density):**
   * Compresión multibanda agresiva con ratios altos (3:1 a 4:1) en medios y compresión paralela interna.
   * Ideal para guitarras pesadas, percusión industrial o rock/metal.
4. **Preset D (Transparent Master Glue):**
   * Curva más suave y lineal. Ratio 1.3:1 en medios, limitación muy suave en agudos y control estricto de excursión de subgraves.

### Configuración Quirúrgica de Maximus para Masterización
En la masterización profesional en FL Studio:
* **Banda LOW (0 a 120 Hz):**
  * `Stereo Separation`: Girar completamente a la derecha (`100% Merged / Mono`).
  * `Threshold`: Justo en el promedio del bombo/bajo.
  * `Attack`: Rápido (1.5 ms a 3 ms) para sujetar el subgrave.
  * `Release`: 25 ms a 40 ms para evitar vibraciones audibles de ciclo.
* **Banda MID (120 Hz a 4 kHz):**
  * `Stereo Separation`: 0% (neutro, preserva la imagen de la mezcla).
  * `Ratio`: 1.5:1 (compresión transparente de pegamento).
* **Banda HIGH (4 kHz a 20 kHz):**
  * `Stereo Separation`: 10% a 20% a la izquierda (`Expanded`) para aire tridimensional.
  * `De-Essing`: Umbral ajustado para amortiguar picos en 6–8 kHz (hi-hats agresivos o eses vocales).
* **Banda MASTER:**
  * Actúa como compresor final y clipper de rodilla suave. Curva con pendiente suave hacia el techo de 0 dBFS.

---

## 4. El Paradigma del "Soft Clipper antes del Limiter"
El error más común de los productores noveles en FL Studio es insertar únicamente **Fruity Limiter** en el Master y empujar el fader de ganancia. Esto provoca:
1. **Bombeo audible (*pumping*):** Los transitorios ultra-rápidos del bombo (1 a 5 ms) fuerzan al limitador a activar una reducción de ganancia severa (-4 a -6 dB), bajando el volumen de toda la pista durante 50 a 100 ms.
2. **Pérdida de pegada (*punch*):** Los transitorios pierden su filo y la percusión suena "aplastada".

### La Solución de Alta Exergía:
Al insertar **Fruity Soft Clipper** inmediatamente antes de **Fruity Limiter**:
* La función de transferencia tangencial del Soft Clipper:
  $$y = \begin{cases} x & \text{si } |x| \le T \\ T + (1 - T) \tanh\left(\frac{|x| - T}{1 - T}\right) \cdot \operatorname{sgn}(x) & \text{si } |x| > T \end{cases}$$
* Los picos que superan el umbral $T$ (ej. -2.5 dBFS) se redondean armónicamente en microsegundos, disipando la energía del pico en armónicos cálidos de orden superior sin modulación de envolvente.
* El limitador final recibe una señal con un factor de cresta controlado, necesitando realizar solo **0.5 a 1.0 dB de reducción de ganancia limpia** para asegurar el techo estricto de -0.3 dBTP.

---

## 5. Tabla de Estándares de Sonoridad por Destino

| Plataforma / Entorno | Sonoridad Integrada (LUFS) | Techo True Peak (dBTP) | Factor de Cresta (WCF) | Estrategia de Dinámica |
| :--- | :--- | :--- | :--- | :--- |
| **Club / Techno / EBM** | **-8.0 a -9.0 LUFS** | **-0.3 dBTP** | **8.5 a 10.5 dB** | Soft Clipper activo (+2 dB drive), pegada máxima en PA de club, subgrave mono estricto. |
| **Streaming (Spotify / Apple)** | **-14.0 LUFS** | **-1.0 dBTP** | **10.0 a 13.0 dB** | Dinámica abierta, cero distorsión inter-muestra (ISP), preservación de micro-detalles. |
| **Vinilo / Audiófilo** | **-16.0 LUFS** | **-1.5 dBTP** | **12.0 a 15.0 dB** | Cero clipping, preservación de agudos para evitar distorsión de aguja, corte subgrave a 35 Hz. |

---

## 6. Operación en Silicio (Scripts y Presets C5)

### A. Preset Nativo para el Mixer de FL Studio
El preset compilado se encuentra instalado en:
`~/Documents/Image-Line/FL Studio/Presets/Mixer presets/Master_C5_SOTA.fst`

**Para cargarlo en FL Studio:**
1. Abre el mezclador de FL Studio (`F9`).
2. Selecciona el canal **Master** (Insert 0).
3. Haz clic derecho sobre el canal $\to$ `File` $\to$ `Open mixer track state...`
4. Selecciona **`Master_C5_SOTA`**.
5. Los 5 plugins se cargarán automáticamente en los slots 1 a 5 con el ruteo calibrado.

### B. Motor Autónomo en Línea de Comandos (`scripts/mastering_reverse_engine_fl.py`)
Para masterizar cualquier archivo de audio de forma determinista y auditarlo contra el Linter Rubin:

```bash
# Masterización para Club / Techno / Dark Disco (-8.5 LUFS / -0.3 dBTP)
python3 scripts/mastering_reverse_engine_fl.py \
    --input ~/Music/Tu_Track.wav \
    --profile techno \
    --target-lufs -8.8 \
    --bits 24

# Masterización para Streaming EBU R128 (-14.0 LUFS / -1.0 dBTP)
python3 scripts/mastering_reverse_engine_fl.py \
    --input ~/Music/Tu_Track.wav \
    --profile streaming_sota \
    --bits 24
```
