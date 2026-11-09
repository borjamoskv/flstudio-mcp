# Protocolo RAE de Producción Musical Humana en FL Studio 2025: Las 14 Leyes, FLEX, Kicks, Sidechain y Build-Ups Largos

**Autor:** Borja Fernández Angulo (*Investigador en Sistemas Complejos*)

---

## 1. Las 14 Leyes RAE del Productor Humano (Por Qué una IA Suena Mecánica y Cómo Humanizarla)
La diferencia entre una pista generada por un secuenciador rígido y una obra producida por un humano reside en **catorce invariantes físicas e involuntarias**:
1. **Micro-Tiempo Diferencial (*Differential Pocket*), *Ghost Notes* y *Clap Flams*:** El **Kick** ancla el pulso ($0\text{ ms}$), el **Bajo** se recuesta detrás del pulso ($+6.8\text{ ms}$, *laid-back pocket*), los **Claps** llevan un *pre-snap flam* de $-11\text{ ms}$ en los tiempos 2 y 4, y las semicorcheas débiles incorporan *ghost notes* de caja a baja velocidad ($v \approx 36$).
2. **Micro-Rasgueo Polifónico (*Chord Strumming*) y *Top-Note Voicing*:** En `FLEX`, `Kepler Exo`, `FL Keys` y `Sakura`, las notas del acorde se despliegan con $+12\text{ ms}$ de grave a agudo y la nota superior (la melodía del acorde) recibe un $+28\%$ de presencia frente a las voces internas.
3. **Respiración de los 8 Macros y *Call & Response Delay Throws*:** Los 8 Macros de `FLEX` siguen arcos de frase + deriva $1/f$; cuando el *lead* melódico calla en la segunda mitad del compás, el envío hacia `Fruity Delay 3` y `LuxeVerb` se abre automáticamente (efecto *Call & Response*).
4. **Escultura de Kick con Fase Anclada ($0\text{ rad}$) y Sidechain Multibanda a $140\text{ Hz}$:** El subgrave ($<140\text{ Hz}$) se agacha un $92\%$ acoplado a la caída del Kick, mientras los acordes y armónicos ($\ge 140\text{ Hz}$) solo se agachan un $20\%$.
5. **Mutación cada 4/8 Compases (*Ear Candy*, *Reverse Reverb Swells* y *Turnaround Fills*):** Antes del cambio armónico del compás 5 entra una cola de reverberación invertida (*Reverse Swell*) que aspira al oyente hacia el acorde, y en el compás 8 entra un *fill* panorámico de toms.
6. **Física de Build-Ups Largos y *The Pre-Drop Vacuum*:** Lavado paso-alto de subgraves ($30 \to 260\text{ Hz}$), aceleración geométrica ($1/4 \to 1/32$), contracción estéreo y 2 tiempos de *Silencio Cálido* antes del impacto del Drop.
7. **Imperfección Analógica ($\pm 3.5\text{ cents}$) y Masterización Anti-Squash:** Cama térmica analógica a $-44\text{ dBFS}$ y *Soft Clipping* tangencial ($\tanh$) que preserva un *Crest Factor* $\ge 9.5\text{ dB}$ (`EXERGÍA PURA`).
8. **Foley Orgánico Fuera de Rejilla (*Found-Sound Micro-Percussion* en `Slicex`/`DirectWave`):** Texturas percusivas de madera, metal y llaves desplazadas $\pm 14\text{ ms}$ fuera de la rejilla matemática.
9. **Respiración de Envolvente de Batería (*Hi-Hat Decay Morphing*):** El *decay* del charles se abre progresivamente de $11\text{ ms} \to 58\text{ ms}$ al acercarse al clímax de cada frase de 4 compases.
10. **Truco Pultec de Subgrave (`Fruity Parametric EQ 2`):** Realce simultáneo en la fundamental ($49\text{ Hz}$) y atenuación en el segundo armónico ($98\text{–}110\text{ Hz}$) para separar el peso del Kick de la articulación del bajo.
11. **Compresión Paralela Nueva York (`Maximus` + `Distructor`):** Mezcla del $82\%$ del bus de batería transitorio intacto con un $18\%$ de bus paralelo hiper-saturado ($\tanh$).
12. **Micro-Modulación de Tempo Humana (*Rubato* de Conducción):** Ligero empuje del pulso ($-6\text{ ms}$) hacia el clímax de frase y relajación al resolver el compás.
13. **Nota Pedal Aguda con *Delayed Vibrato* (`Sakura`/`FLEX`):** Quinta justa sostenida donde el vibrato de $5.4\text{ Hz}$ entra progresivamente $180\text{ ms}$ después del ataque.
14. **Sidechain Espectral Dinámico en $2\text{ kHz}$ (`Fruity Peak Controller` + `Parametric EQ 2`):** Cuando el *lead* canta, excava dinámicamente $-2.8\text{ dB}$ en la banda de presencia de los acordes de `FLEX`.

---

## 2. Dominio de `FLEX` y los Plugins Nativos por el Agente FL

| Macro de `FLEX` | CC MIDI | Función Tímbrica RAE | Curva de Automatización Humana |
| :--- | :---: | :--- | :--- |
| **Macro 1 (Cutoff / Timbre Brightness)** | `CC #1` | Macro-articulador 1 | `Phrase Arc + Velocity Coupling (0.28 -> 0.82)` |
| **Macro 2 (Filter Resonance / Formant)** | `CC #2` | Macro-articulador 2 | `Inverse Crest Tension (0.20 -> 0.58)` |
| **Macro 3 (Envelope Modulation Depth)** | `CC #12` | Macro-articulador 3 | `Syncopated Accent Boost (+18% on offbeats)` |
| **Macro 4 (Amp/Filter Decay & Release)** | `CC #13` | Macro-articulador 4 | `Legato Phrasing Breathing (0.35 -> 0.75)` |
| **Macro 5 (Analog Detune / Vibrato Drift)** | `CC #14` | Macro-articulador 5 | `1/f Voss-Clarke Thermal Drift (0.12 -> 0.28)` |
| **Macro 6 (BPM Delay Send)** | `CC #15` | Macro-articulador 6 | `Phrase-End Tail Bloom (ducks during notes, blooms on rests)` |
| **Macro 7 (Luxe Space Reverb)** | `CC #16` | Macro-articulador 7 | `Pre-Drop Evacuation (opens to 0.70 then cuts at drop)` |
| **Macro 8 (Warmth / Soft Limiter Drive)** | `CC #17` | Macro-articulador 8 | `Dynamic Saturation Tracking (0.35 -> 0.65)` |

### Reglas de Oro RAE por Plugin Nativo

- **`BassDrum`** (*Síntesis de Bombo Principal Afinado a la Tónica con Fase Bloqueada*):
  - **Ecuación RAE:** `y[n] = tanh(g_drv * (A(n)*sin(2*pi * integral(f_base + Delta_f*exp(-t/tau_p)) dt) + Click(n) + Sample(n)))`
  - Afinar siempre Base Freq a la fundamental exacta de la escala (ej. F1 = 43.65 Hz, G1 = 49.00 Hz, A1 = 55.00 Hz).
  - Ajustar Slide Time entre 8 ms y 14 ms para pegada de pecho en 95-110 Hz sin invadir la voz o el bajo medio.
  - Aplicar micro-variación humana de velocidad (-4% en tiempos 2 y 4; +3% en el tiempo 1 del compás).
- **`Transistor Bass`** (*Línea Ácida / Sub-bajo Analógico con Ligaduras (Slide) y Acentos Acoplados*):
  - **Ecuación RAE:** `y[n] = Dist_Pedal(DiodeLadder_18dB(Osc_{Saw/Sq}[n], f_c + E_env(Accent)*Mod, Q_res))`
  - Activar Slide únicamente en transiciones de semitono o cuarta/octava para emular el portamento RC real del TB-303.
  - Acoplar Accent (>100 vel) con apertura simultánea de Cutoff (CC #74) y Env Mod (CC #12).
- **`Kepler Exo`** (*Colchones Analógicos (Pads Juno/Jupiter) y Arpegios con Deriva Térmica*):
  - **Ecuación RAE:** `y[n] = FX_Chain(ZDF_VCF(DCO_1(n) + DCO_2(n, Sync, XMod) + Sub(n)))`
  - Desplazar ligeramente el inicio de las notas de cada acorde (micro-strumming de 8 a 15 ms de grave a agudo).
  - Activar Hyper Chorus al 35-45% cortando los graves laterales por debajo de 130 Hz con Fruity Parametric EQ 2.
- **`Sytrus`** (*Bajos FM Metálicos, Campanas Microtonales y Leads Expresivos*):
  - **Ecuación RAE:** `Op_i(t) = A_i(t) * Wave_i(2*pi*f_i*t + sum_{j=1}^6 M^{FM}_{j,i}*Op_j(t)) * prod_{j=1}^6 (1 + M^{RM}_{j,i}*Op_j(t))`
  - Vincular la velocidad de cada nota (Note Velocity) y Mod X al índice de modulación FM (Op 2 -> Op 1) para que solo los golpes fuertes brillen.
  - Usar Fine Pitch por nota (Evento 0xEE) para inflexiones microtonales y portamentos vocales.
- **`Harmor`** (*Resíntesis Vocal, Texturas Orgánicas y Bajos con Desplazamiento de Formantes*):
  - **Ecuación RAE:** `y(t) = sum_{p in {A,B}} sum_{k=1}^{516} 10^(M_amp(k, t)/20) * sin(2*pi * integral(f_0 * M_freq(k, t)) dtau + phi_{p,k})`
  - Modular el parámetro Prism y Blur levemente con un LFO lento no cuantizado para romper la rigidez estática de los 516 parciales.
- **`Fruity Limiter`** (*Compresión por Cadena Lateral (Sidechain) Sensible al Programa y Limitación True-Peak*):
  - **Ecuación RAE:** `y[n] = x[n - L_att] * min(g_comp(E_sc[n]), g_lim(max_{k in [0, L_att]} |x[n-k]|, Ceiling))`
  - En modo COMP con Sidechain del Kick: Attack = 0.5 ms, Ahead = 1.0 ms, Release = (60000 / BPM) * 0.38 ms con Curve = 3..4 (recuperación sigmoidal orgánica).
- **`Frequency Splitter`** (*Separador Multibanda para Sidechain Quirúrgico Transparente*):
  - **Ecuación RAE:** `H_low(z) + H_mid(z) + H_high(z) = z^(-D) (reconstrucción de magnitud y fase unitaria exacta).`
  - Cruzar en 140 Hz (Linear Phase ON): enviar la banda Low (<140 Hz) a un Sidechain profundo (-12 a -18 dB) y la banda Mid/High (>=140 Hz) a un Sidechain suave (-2.5 dB) para que los acordes y el carácter del bajo no bombeen artificialmente.
- **`Fruity Soft Clipper`** (*Recortador Tangencial de Crestas Pre-Limitador*):
  - **Ecuación RAE:** `y[n] = G_post * x[n] si |x[n]| <= T; G_post * sgn(x[n]) * (T + (1 - T)*tanh((|x[n]| - T)/(1 - T))) si |x[n]| > T.`
  - Colocar siempre en el bus de Batería y en el Master antes de Fruity Limiter (Threshold = -2.2 dBFS) para afeitar picos de caja y bombo conservando el impacto humano.
- **`LuxeVerb`** (*Espacio Acústico con Agachamiento Automático (Auto-Ducking Envelope Follower)*):
  - **Ecuación RAE:** `Tail[n] = FDN(x[n] + fb * PitchShift(Tail[n - D], +12 st)) * (1 - Duck(Env(x[n])))`
  - Activar el Envelope Follower interno modulando inversamente el nivel Wet: mientras la melodía toca, la reverberación baja -6 dB; al callar la frase, la cola Shimmer florece limpiamente.

---

## 3. Control Físico del Kick (`BassDrum` / Síntesis de Fase Bloqueada)
Para que el Kick tenga pegada de club humana sin enturbiar la mezcla:
1. **Afinación Exacta a la Fundamental ($f_{\text{sub}}$):** Se sintoniza la cola del Kick con la nota raíz del tema (ej. `F1 = 43.65 Hz`, `G1 = 49.00 Hz`, `A1 = 55.00 Hz`).
2. **Bloqueo de Fase a $0\text{ rad}$:** Cada golpe reinicia el integrador de fase en $\phi(0) = 0$ para que la excursión inicial del cono sea idéntica.
3. **Barrido Exponencial Doble:**
   $$f(t) = f_{\text{sub}} + (f_{\text{punch}} - f_{\text{sub}})e^{-t/\tau_{\text{punch}}} + (f_{\text{click}} - f_{\text{punch}})e^{-t/\tau_{\text{click}}}$$
4. **Vaciado Quirúrgico del Barro (`195 Hz Notch`):** Se atenúa $-3.5\text{ dB}$ en $190\text{–}210\text{ Hz}$ (`Fruity Parametric EQ 2`) y se afeita la cresta con `Fruity Soft Clipper` ($\tanh$).

---

## 4. Las 3 Arquitecturas de Sidechain Quirúrgico (Cero Bombeo Artificial)
1. **Sidechain Acoplado a la Constante de Caída del Kick ($\tau_{\text{body}}$):** La curva de recuperación sigmoidal devuelve el subbajo exactamente cuando el Kick cae a $-6\text{ dB}$:
   $$G_{\text{sub}}(t) = 1 - D_{\text{sub}} \cdot \exp\!\left(-\frac{1.35\,t}{0.85\,\tau_{\text{body}}}\right)$$
2. **Sidechain Multibanda con `Frequency Splitter` (Cruce Lineal en $140\text{ Hz}$):**
   - **Banda Subgrave ($<140\text{ Hz}$, 100% Mono):** Agachamiento profundo ($90\text{–}95\%$) para dejar espacio físico total al Kick.
   - **Banda Media-Aguda ($\ge 140\text{ Hz}$, Estéreo):** Agachamiento sutil ($18\text{–}25\%$) solo durante el clic inicial ($\tau_{\text{punch}}$), logrando que los acordes de `FLEX` y el carácter del bajo suenen continuos y orgánicos.
3. **Sidechain Espacial en `LuxeVerb` y `Fruity Delay 3`:** El seguidor de envolvente interno atenúa la cola de reverberación mientras la voz o el *lead* están activos, abriendo el espacio únicamente en los silencios de frase.

---

## 5. Estructuras Complejas en 6 Actos y Física de Build-Ups Largos
Para construir canciones largas que mantengan la tensión hipnótica sin sonar a bucle repetitivo, el motor `synthesize_complex_arrangement_and_long_buildup` coordina **cinco mecanismos físicos simultáneos** durante el Build-Up:
1. **Lavado Progresivo de Subgraves (*High-Pass Bass Washout* en `Fruity Parametric EQ 2`):**
   $$f_{\text{HPF}}(u) = 30 \cdot \left(\frac{260}{30}\right)^{u^{1.6}}\text{ Hz}, \quad u \in [0, 1]$$
   Al eliminar gradualmente la energía debajo de $260\text{ Hz}$ durante 16 compases y restaurarla instantáneamente a $20\text{ Hz}$ en el primer pulso del Drop, el impacto físico del subgrave se multiplica sin necesidad de subir el volumen maestro.
2. **Aceleración Geométrica de Redoble (*Snare/Clap Subdivision Roll*):**
   La densidad rítmica duplica su subdivisión por tramos ($1/4 \to 1/8 \to 1/16 \to 1/32$) combinada con una rampa exponencial de velocidad y acentos métricos cada 4 golpes para evitar el efecto ametralladora.
3. **Rampa de 8 Macros en `FLEX` + Glissando Infinito Shepard-Risset (`Harmor`/`Sytrus`):**
   Apertura simultánea de *Filter Cutoff* (`Macro 1` de $0.28 \to 0.96$), *Resonance* (`Macro 2`) y *Reverb Tail* (`LuxeVerb`), acompañada de un oscilador Shepard-Risset de ascenso continuo.
4. **Contracción Estéreo Pre-Impacto (`Fruity Stereo Shaper`):**
   En los últimos 4 compases del Build-Up, la anchura estéreo se estrecha un $35\%$ hacia el centro para que el Drop se abra al $100\%$ en las frecuencias medias/altas.
5. **El Silencio Cálido Pre-Drop (*The Pre-Drop Vacuum*):**
   En los últimos 2 tiempos del compás final del Build-Up, se cortan en seco todas las colas de reverberación, *risers* y redobles, dejando un golpe focal seco antes de que explote el `Kick` en el tick `0` del Drop.
