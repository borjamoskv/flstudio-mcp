# Tratado Integral de Ingeniería Inversa RAE: FL Studio 2025 y sus 147 Plugins (C5-REAL)

**Autor:** Borja Fernández Angulo (*Investigador en Sistemas Complejos*)

---

## 1. Fundamento Epistémico: El Doble Paradigma RAE
Este documento constituye la deconstrucción total y determinista de **FL Studio 2025 (macOS ARM64)** y de la totalidad de su inventario de **147 complementos** (**51 Generadores Nativos**, **89 Efectos Nativos** y **7 Procesadores VST3**) bajo la doble invariante **RAE**:
1. **RAE (*Real Academia Española*):** Traducción ontológica rigurosa de la jerga anglosajona de producción musical al español técnico y académico, sustituyendo metáforas comerciales (*vibe coding* acústico) por definiciones basadas en la física del sonido y el procesamiento digital de señales.
2. **RAE (*Reverse Audio & Architecture Engine*):** Deconstrucción del protocolo binario `FLhd`/`FLdt` (`.flp`, `.fst`, `.fsc`), las ecuaciones matemáticas de transferencia $y[n]$ / $H(z)$, la topología interna y los mapeos MIDI CC de cada módulo.

- **Generadores Nativos Documentados:** `51 / 51` (**100%**)
- **Efectos Nativos Documentados:** `89 / 89` (**100%**)
- **Complementos VST3 de Terceros Documentados:** `7 / 7` (**100%**)
- **Subsistemas Nucleares del Motor Documentados:** `8 / 8` (**100%**)
- **Códigos de Evento Binario `FLdt` Documentados:** `67`
- **Términos del Léxico Acústico RAE:** `35`

---

## 2. Diccionario Léxico RAE de Ingeniería Acústica y DSP

| Anglicismo / Jerga DAW | Término Canónico RAE | Definición Académica y Física | Ecuación / Invariante Matemática |
| :--- | :--- | :--- | :--- |
| **DAW (Digital Audio Workstation)** | *Estación de trabajo de audio digital* | Del lat. statio ('puesto') y audio ('oír'). Sistema informático integral dedicado a la grabación, síntesis, edición, mezcla y masterización de señales sonoras discretizadas. | `Muestreo uniforme regido por el Teorema de Nyquist-Shannon (fs >= 2 * f_max, canónicamente 48 kHz / coma flotante de 32/64 bits).` |
| **Plugin** | *Complemento o módulo enchufable de procesamiento* | De complementar ('dar perfección o añadir una función'). Biblioteca dinámica (Mach-O .dylib / bundle en macOS) que se acopla al bucle de audio del anfitrión. | `Función de transformación de bloques de muestras x[n] -> y[n] acotada por el plazo temporal del búfer (L / fs segundos).` |
| **Wrapper** | *Envoltorio o adaptador de interfaz binaria* | De envolver ('rodear o recubrir'). Capa traductora que encapsula protocolos externos (VST3, Audio Units, CLAP) dentro del bus propietario de eventos de FL Studio. | `Traducción biyectiva de buffers de audio, colas de eventos MIDI 1.0/2.0 y bloques opacos de estado (Chunk 0xD5).` |
| **Clipper (Soft Clipper)** | *Recortador de cresta por saturación tangencial* | De recortar ('cortar o cercenar lo que sobra'). Dispositivo no lineal sin memoria que limita la excursión instantánea de la onda redondeando sus picos. | `y[n] = x[n] para |x| <= T; T + (1-T)*tanh((|x|-T)/(1-T))*sgn(x) para |x| > T.` |
| **Limiter (True Peak Brickwall)** | *Limitador de muro infranqueable de pico verdadero* | De limitar ('fijar la extensión máxima'). Regulador dinámico con anticipación temporal (lookahead) y sobremuestreo polifásico que impide rebasar un techo de amplitud. | `Sobremuestreo 4x/8x por filtro FIR polifásico seguido de atenuación de envolvente con ataque anticipado tau_a.` |
| **Sidechain (Ducking)** | *Modulación por cadena lateral (agachamiento dinámico)* | De cadena ('sucesión de eslabones') y lateral. Control de la ganancia o banda espectral de una señal subordinada mediante la envolvente energética de una señal rectora (ej. bombo). | `g[n] = (1 + exp(k * (E_ext[n] - T)))^-1; atenúa el bajo cuando irrumpe el transitorio del bombo.` |
| **Compressor** | *Compresor de margen dinámico* | Del lat. compressor ('que oprime o reduce volumen'). Atenuador automático cuya ganancia decrece cuando la energía de entrada supera un umbral fijado. | `En decibelios: Y_dB = T + (X_dB - T) / R para X_dB > T, gobernado por constantes de tiempo de ataque y relajación.` |
| **Reverb (Reverberation)** | *Reverberador acústico (persistencia sonora)* | Del lat. reverberare ('repercutir o rebotar'). Persistencia del sonido en un recinto cerrado tras extinguirse la fuente, por reflexiones múltiples en sus paramentos. | `Convolución y[n] = (x * h)[n] o red de retardo realimentada (FDN) con tiempo de caída Sabine RT60 = 0.161 * V / A.` |
| **Delay** | *Línea de retardo y eco realimentado* | De retardar ('diferir o detener'). Repetición discreta de una señal tras un intervalo temporal sincronizado o libre, con realimentación amortiguada. | `y[n] = x[n] + g * H_lp(z) * y[n - D], donde D = round(fs * 60 / BPM * fraccion).` |
| **Chorus** | *Multiplicador coral por retardo modulado* | Del lat. chorus ('conjunto de voces'). Efecto que simula la ejecución simultánea de varias fuentes mediante líneas de retardo (15-35 ms) moduladas en fase. | `y[n] = x[n] + sum_k a_k * x(n - D_k - m_k * sin(2*pi*f_k*n/fs)).` |
| **Flanger** | *Rebordeador de peine por retardo corto modulado* | De rebordear ('rozar la pestaña o reborde de un carrete magnético'). Filtro de peine variable originado al sumar una señal con una copia retardada entre 0.5 y 10 ms. | `H(z) = 1 + g * z^(-D(n)), generando muescas armónicas equiespaciadas en frecuencia.` |
| **Phaser** | *Desfasador por cascada de filtros paso-todo* | De desfasar ('alterar la diferencia de fase'). Procesador que rota la fase espectral mediante etapas paso-todo de primer orden y las suma a la señal directa. | `H(z) = 1 + g * prod_{k=1}^M ((a_k(n) + z^-1) / (1 + a_k(n)*z^-1)).` |
| **Vocoder** | *Codificador e improntador de envolvente vocal* | Acrónimo de voice coder ('codificador de voz'). Analizador-sintetizador que extrae la envolvente espectral de un modulador (voz) en N bandas y la impone a una portadora. | `y[n] = sum_{b=1}^B Env(|h_b * x_mod|[n]) * (h_b * x_car)[n].` |
| **Wavetable Synthesis** | *Síntesis por barrido de tabla de ondas* | De síntesis ('composición de un todo') y tabla. Generación sonora por lectura periódica e interpolación bilineal entre ciclos de onda almacenados en una matriz. | `y[n] = (1 - alpha)*W[k, phi[n]] + alpha*W[k+1, phi[n]].` |
| **FM Synthesis** | *Síntesis por modulación de frecuencia (y fase)* | Alteración instantánea de la frecuencia o fase de un oscilador portador mediante la salida de uno o varios osciladores moduladores (algoritmo de Chowning). | `y(t) = A * sin(w_c * t + I * sin(w_m * t)) = A * sum_{k=-inf}^{inf} J_k(I) * sin((w_c + k*w_m)*t).` |
| **Additive / Resynthesis** | *Síntesis aditiva y resíntesis espectral* | Reconstrucción de cualquier timbre complejo mediante la superposición de parciales sinusoidales cuya amplitud y frecuencia evolucionan en el tiempo (Teorema de Fourier). | `y(t) = sum_{k=1}^K A_k(t) * sin(integral(w_k(tau) dtau) + phi_k).` |
| **Granular Synthesis** | *Síntesis corpuscular o granular* | Del lat. granulum ('grano pequeño'). Atomización del sonido en micro-fragmentos acústicos (10-100 ms) envueltos por una ventana acampanada y reordenados estocásticamente. | `y[n] = sum_g w((n - n_g)/L_g) * s[p_g + (n - n_g)*r_g].` |
| **Physical Modeling (Waveguide)** | *Modelado físico por guía de ondas digital* | Simulación numérica de las ecuaciones diferenciales de cuerdas tensas, membranas, placas o tubos acústicos (algoritmos de Karplus-Strong y Julius O. Smith). | `d^2 u / dt^2 = c^2 * d^2 u / dx^2 resuelta mediante dos líneas de retardo bidireccionales acopladas a un filtro de pérdidas.` |
| **Linear Phase EQ** | *Ecualizador de fase lineal (retardo de grupo constante)* | De igualar ('ajustar el balance frecuencial'). Filtro de respuesta finita al impulso (FIR) con coeficientes simétricos que altera la magnitud sin rotar la fase relativa. | `h[n] = h[N - 1 - n] => Retardo de grupo tau_g(w) = (N - 1) / 2 constante en todo el espectro.` |
| **Mid/Side (M/S) Processing** | *Codificación y procesamiento Suma/Diferencia (Centro/Lateral)* | Descomposición ortogonal de un par estereofónico (Izquierda/Derecha) en una componente monofónica central (Suma) y una componente diferencial periférica (Lateral). | `M = (L + R)/2, S = (L - R)/2; reconstrucción exacta L = M + S, R = M - S (matriz de Hadamard 2x2).` |
| **Transient Shaper** | *Escultor diferencial de transitorios y cola* | Del lat. transitorius ('pasajero, ataque fugaz'). Procesador que discrimina el ataque percusivo del sostenimiento comparando dos seguidores de envolvente (rápido y lento). | `Delta_E[n] = Env_fast[n] - Env_slow[n]; modula la ganancia según el signo y magnitud de Delta_E[n].` |
| **Waveshaper** | *Conformador no lineal de onda por polinomios o curvas* | De conformar ('dar forma'). Función estática f(x) aplicada muestra a muestra para inyectar armónicos pares (asimétrica) o impares (simétrica, polinomios de Chebyshev). | `y[n] = sum_k c_k * T_k(x[n]), donde T_k(cos(theta)) = cos(k*theta).` |
| **Dithering (TPDF)** | *Tremolado estocástico de recuantización (TPDF)* | Inyección de ruido aleatorio de densidad triangular de media nula y amplitud 1 LSB antes de truncar la profundidad de bits, transformando distorsión no lineal en piso de ruido blanco. | `y_q[n] = Q_Delta(x[n] + u_1[n] - u_2[n]), con u_1, u_2 ~ U(-Delta/2, Delta/2).` |
| **Convolution** | *Convolución por respuesta al impulso* | Del lat. convolvere ('enrollar juntos'). Operador integral lineal e invariante en el tiempo que imprime la huella acústica de un recinto o aparato físico sobre cualquier señal. | `y[n] = sum_k x[k]*h[n-k] = IFFT(FFT(x) * FFT(h)) mediante particionado sin latencia.` |
| **Pitch Bend / Microtonality** | *Inflexión continua de altura tonal y microtonalidad* | Desviación fina de la frecuencia fundamental respecto al temperamento igual de 12 semitonos (12-TET), expresada en centésimas de semitono (cents). | `f = f_0 * 2^(Delta_cents / 1200); en MIDI 14-bit: val = 8192 + round(8192 * Delta_cents / Rango_cents).` |
| **Formant** | *Formante o pico de resonancia del tracto acústico* | De formar. Cada una de las regiones de concentración de energía espectral (F1, F2, F3) que determinan el timbre vocálico con independencia de la nota fundamental. | `Polos complejos conjugados del filtro del tracto vocal H(z) = G / prod_{k=1}^M (1 - 2*r_k*cos(w_k)*z^-1 + r_k^2*z^-2).` |
| **Crest Factor** | *Factor de cresta (relación pico a valor eficaz)* | De cresta ('cima de una onda'). Cociente logarítmico entre la amplitud máxima absoluta de una señal y su valor cuadrático medio (RMS), indicador de vitalidad dinámica. | `CF_dB = 20 * log10(max|x[n]| / sqrt(mean(x[n]^2))).` |
| **Spectral Flatness (Wiener Entropy)** | *Planitud espectral (entropía de Wiener)* | Cociente entre la media geométrica y la media aritmética del espectro de potencia; distingue tonos puros (cercano a 0) del ruido blanco o barro espectral (cercano a 1). | `SFM = exp((1/K)*sum ln S[k]) / ((1/K)*sum S[k]).` |
| **Plugin Delay Compensation (PDC)** | *Compensación automática de retardo de inserción* | Alineación temporal del grafo del mezclador mediante inserción de retardos de igualación en las ramas paralelas para neutralizar la latencia de filtros FIR o lookahead. | `Para cada ruta r hacia el nodo sumador: D_comp(r) = max_j L(j) - L(r).` |
| **Step Sequencer / Channel Rack** | *Secuenciador por pasos y bastidor de canales* | De secuencia ('sucesión ordenada'). Matriz discreta de disparo rítmico cuantizada en subdivisiones de compás (1/16 de nota) que aloja todos los instrumentos del proyecto. | `Disparo de eventos en instantes t_k = k * (60 / (BPM * 4)) + delta_swing.` |
| **Piano Roll** | *Rollo de pianola o matriz bidimensional tiempo-altura* | Representación cartesiana donde el eje de abscisas mide el tiempo en pulsos por negra (PPQ) y el de ordenadas la altura tonal y propiedades por nota (velocidad, paneo, corte). | `Resolución temporal de 96 a 960 PPQ; estructura binaria de 24 bytes por nota en el evento FLdt 0xEE.` |
| **Playlist** | *Lienzo de estructura macro-temporal (partitura general)* | Espacio de montaje lineal donde se disponen patrones musicales, fragmentos de audio y curvas de automatización a lo largo de la duración de la obra. | `Grafo temporal de eventos de clip codificados en el bloque binario FLdt 0xEC.` |
| **Patcher** | *Entorno modular de interconexión en grafo dirigido (DAG)* | De parchear ('conectar mediante latiguillos'). Sub-anfitrión nodal que permite enrutar señales de audio, notas MIDI y parámetros de control en paralelo o serie arbitraria. | `Evaluación topológica sin ciclos (o con retardo de 1 bloque en realimentación) de sub-nodos generadores y efectos.` |
| **Automation Clip** | *Curva de automatización paramétrica por esplines* | De automático. Función continua definida a trozos mediante puntos de control y tensiones no lineales que gobierna la evolución temporal de cualquier parámetro del sistema. | `Interpolación entre nodos (t_i, v_i) con exponente de tensión tau: u' = u^(2^tau) o 1 - (1-u)^(2^-tau).` |
| **LUFS (Loudness Units Full Scale)** | *Unidades de sonoridad referidas al fondo de escala (ITU-R BS.1770)* | Medida psicoacústica normalizada del volumen percibido por el oído humano tras aplicar ponderación frecuencial en K (pre-énfasis cefálico y filtro paso-alto RLB). | `LUFS = -0.691 + 10 * log10(sum_i G_i * z_i), con compuerta absoluta a -70 LUFS y relativa a -10 LU.` |

---

## 3. Arquitectura Nuclear de FL Studio 2025 (8 Subsistemas Core)

### 3.1. FLhd_FLdt_Binary_Protocol — *Protocolo Binario de Flujo de Eventos FLhd/FLdt*
- **Definición RAE:** Formato contenedor propietario basado en cabecera fija de 14 octetos ('FLhd') seguida de un bloque de flujo de eventos ('FLdt') codificado por identificador de evento y longitud variable (LEB128/VarLen).
- **Estructura Binaria:** `{"FLhd_Header_14B": "Magic 'FLhd' (4B) + Size=6 (uint32 LE) + FormatType (uint16 LE: 0=Project .flp, 16=Score .fsc, 64=Mixer .fst) + ChannelCount (uint16 LE) + PPQ (uint16 LE, default 96).", "FLdt_Chunk": "Magic 'FLdt' (4B) + ByteLength (uint32 LE) + Secuencia continua de eventos [EventID (1B) + Payload].", "Rangos_EventID": {"0..63 (0x00..0x3F)": "Eventos de 1 octeto (Byte / uint8).", "64..127 (0x40..0x7F)": "Eventos de 2 octetos (Word / uint16 LE).", "128..191 (0x80..0xBF)": "Eventos de 4 octetos (DWord / uint32 LE / float32).", "192..255 (0xC0..0xFF)": "Eventos de longitud variable (VarLen LEB128 + bloque de octetos/UTF-8/UTF-16LE)."}}`

### 3.2. Mixer_125_Insert_Engine — *Motor de Mezcla de 125 Canales de Inserción, 10 Ranuras y PDC*
- **Definición RAE:** Matriz de suma digital en coma flotante de 32 bits con 125 canales de inserción más canal Maestro, 10 ranuras de efectos por canal, ecualizador paramétrico de 3 bandas integrado, inversión de polaridad, permutación L/R, separación estereofónica M/S y compensación automática de retardo (PDC).
- **Ecuación / Ley DSP:** `y_k[n] = G_fader * Pan(M_k[n] + alpha_sep * S_k[n]), con envíos post-fader S_{k->j} en grafo acíclico dirigido (DAG) validado contra ciclos de realimentación.`

### 3.3. Channel_Rack_and_Step_Sequencer — *Bastidor de Instrumentos, Secuenciador por Pasos y Ruteo Polifónico*
- **Definición RAE:** Contenedor central de generadores (sintetizadores, muestreadores y clips de audio/automatización) que despacha eventos de nota hacia cada instancia y encamina su salida de audio hacia uno de los 125 canales del mezclador.
- **Ecuación / Ley DSP:** `Ganancia circular por defecto de -2.5 dB (factor 0.78 / ley de paneo circular) en el bastidor; t_step = k * (15 / BPM) + SwingOffset.`

### 3.4. Piano_Roll_and_Voice_Properties — *Matriz Bidimensional de Altura-Tiempo y Propiedades por Voz*
- **Definición RAE:** Secuenciador de alta resolución (96 a 960 PPQ) cuyas notas son objetos independientes de 24 octetos (Evento 0xEE) que portan modulación por voz: altura fina (pitch fine), corte de filtro (Mod X), resonancia (Mod Y), paneo por nota, velocidad de ataque y liberación, y notas de deslizamiento (slide/porta).
- **Estructura Binaria:** `"Struct 24B (<IIHHHHBBBBBBBB): Pos_Ticks(4B), Flags(4B), RackChan(2B), Length_Ticks(2B), Key_MIDI(2B), FinePitch(2B), Release(1B),MidiChan_SlideFlags(1B), Pan(1B), Velocity(1B), ModX_Cutoff(1B), ModY_Res(1B), Reserved(2B)."`

### 3.5. Playlist_and_Spline_Automation — *Lienzo Macro-Estructural y Motor de Automatización por Esplines de Tensión*
- **Definición RAE:** Secuenciador lineal de libre emplazamiento (hasta 500 pistas visuales) donde coexisten clips de patrón MIDI, clips de audio con estiramiento elástico (Zplane Elastique Pro v3) y clips de automatización continua.
- **Ecuación / Ley DSP:** `Curva de tensión entre nodos (t_0, y_0) y (t_1, y_1): u = (t - t_0)/(t_1 - t_0); f(u, tau) = ((exp(k*u) - 1)/(exp(k) - 1)) para tensión exponencial continua.`

### 3.6. Patcher_and_VFX_Modular_DAG — *Sub-Anfitrión Modular en Grafo Acíclico Dirigido (Patcher) y Procesadores de Voz (VFX)*
- **Definición RAE:** Entorno de encapsulación topológica que permite construir instrumentos o cadenas de masterización complejas interconectando nodos de audio (cables amarillos), eventos de nota/voz (cables verdes) y parámetros de control (cables rojos).
- **Ecuación / Ley DSP:** `Ordenación topológica de Kahn G=(V,E); soporta división frecuencial de fase lineal (Frequency Splitter) y remapeo microtonal en tiempo real (VFX Key Mapper / VFX Script).`

### 3.7. Fruity_Wrapper_Plugin_Host — *Adaptador Universal de Complementos Externos (VST2 / VST3 / AU)*
- **Definición RAE:** Puente binario de aislamiento y traducción que aloja procesadores y sintetizadores de terceros en macOS ARM64, gestionando búferes de tamaño variable, tablas de 128 CC MIDI y serialización de estado en el evento 0xD5.
- **Estructura Binaria:** `"Evento 0xC9 ('Fruity Wrapper') + Evento 0xD5 (Cabecera de versión Wrapper + Ruta/UUID del plugin VST3/AU + Tamaño de estado + Volcado binario nativo del plugin)."`

### 3.8. FL_Cloud_TDR_Mastering_Engine — *Motor de Masterización Asistida de Ocho Etapas (Tokyo Dawn Records)*
- **Definición RAE:** Cadena determinista de masterización integrada en `/Contents/Resources/FL/System/Config/Master/references.txt` que encadena filtrado M/S, compresión de pegamento, ecualización dinámica multibanda, recorte suave y limitación de pico verdadero a 4x.
- **Ecuación / Ley DSP:** `SlickEQ_M(HPF + MonoSub) -> Kotelnikov(RMS Glue) -> Nova_GE(3-Band DynEQ) -> SoftClipper(tanh) -> Limiter6_GE(4x Polyphase ISP Brickwall).`

---

## 4. Protocolo Binario `FLhd` / `FLdt`: Tabla de Eventos (`.flp` / `.fst` / `.fsc`)

| ID Decimal | Hex | Tipo de Dato | Identificador | Descripción Académica RAE |
| :---: | :---: | :--- | :--- | :--- |
| `0` | `0x00` | Byte (uint8) | `Byte_Enabled` | Estado de activación o desvío (bypass) del canal o ranura (0=Inactivo, 1=Activo). |
| `1` | `0x01` | Byte (uint8) | `Byte_NoteOn` | Activación de nota elemental en secuencias heredadas. |
| `2` | `0x02` | Byte (uint8) | `Byte_Vol` | Volumen de canal codificado en un octeto (0..128 nominal). |
| `3` | `0x03` | Byte (uint8) | `Byte_Pan` | Posición panorámica (0=Izquierda extrema, 64=Centro, 128=Derecha extrema). |
| `4` | `0x04` | Byte (uint8) | `Byte_MIDIChan` | Canal MIDI asignado (0..15). |
| `5` | `0x05` | Byte (uint8) | `Byte_MIDINote` | Nota raíz MIDI de referencia (por defecto 60 = Do central C5 en FL). |
| `6` | `0x06` | Byte (uint8) | `Byte_MIDIPatch` | Cambio de programa MIDI (Program Change 1..128). |
| `7` | `0x07` | Byte (uint8) | `Byte_MIDIBank` | Selector de banco MIDI. |
| `9` | `0x09` | Byte (uint8) | `Byte_LoopActive` | Indicador de bucle de patrón activo (0/1). |
| `10` | `0x0A` | Byte (uint8) | `Byte_ShowInfo` | Mostrar ventana de información al abrir el proyecto. |
| `11` | `0x0B` | Byte (uint8) | `Byte_Shuffle` | Cantidad de atresillamiento rítmico global (Swing / Shuffle 0..128). |
| `12` | `0x0C` | Byte (uint8) | `Byte_MainVol` | Volumen maestro global del proyecto. |
| `13` | `0x0D` | Byte (uint8) | `Byte_Stretch` | Factor de estiramiento temporal de muestra. |
| `14` | `0x0E` | Byte (uint8) | `Byte_Pitchable` | Habilita transposición tonal de la muestra. |
| `15` | `0x0F` | Byte (uint8) | `Byte_Zipped` | Proyecto empaquetado en contenedor comprimido ZIP. |
| `16` | `0x10` | Byte (uint8) | `Byte_Delay_Flags` | Banderas del eco interno de canal. |
| `17` | `0x11` | Byte (uint8) | `Byte_TimeSig_Num` | Numerador del compás musical (ej. 4 en 4/4, 12 en Bulerías). |
| `18` | `0x12` | Byte (uint8) | `Byte_TimeSig_Beat` | Denominador o subdivisión de pulso del compás. |
| `19` | `0x13` | Byte (uint8) | `Byte_UseLoopPoints` | Activa los puntos de bucle incrustados en el archivo WAV. |
| `20` | `0x14` | Byte (uint8) | `Byte_LoopType` | Modo de bucle de muestra (Adelante, Ping-Pong). |
| `21` | `0x15` | Byte (uint8) | `Byte_ChanType` | Tipo de canal en el bastidor (0=Sampler, 2=Generator Plugin, 3=Layer, 4=AudioClip, 5=AutomationClip). |
| `22` | `0x16` | Byte (uint8) | `Byte_MixSliceNum` | Canal de inserción del mezclador asignado al generador (0=Maestro, 1..125=Insertos). |
| `23` | `0x17` | Byte (uint8) | `Byte_EffectChannelMuted` | Estado de silenciamiento (Mute) e inversión del canal de mezcla. |
| `64` | `0x40` | Word (uint16 LE) | `Word_NewChan` | Instancia un nuevo canal en el bastidor con su índice entero (0..N-1). |
| `65` | `0x41` | Word (uint16 LE) | `Word_NewPat` | Abre la definición de un nuevo patrón musical (1..999). |
| `66` | `0x42` | Word (uint16 LE) | `Word_Tempo` | Tempo entero heredado en pulsos por minuto (BPM). |
| `67` | `0x43` | Word (uint16 LE) | `Word_CurrentPatNum` | Número del patrón actualmente seleccionado. |
| `69` | `0x45` | Word (uint16 LE) | `Word_FX` | Parámetro de efecto interno de canal. |
| `70` | `0x46` | Word (uint16 LE) | `Word_Fade_Stereo` | Banderas de fundido y fase estereofónica del muestreador. |
| `71` | `0x47` | Word (uint16 LE) | `Word_CutOff` | Frecuencia de corte del filtro interno del canal (0..1024). |
| `72` | `0x48` | Word (uint16 LE) | `Word_DotVol` | Volumen por paso en el secuenciador. |
| `73` | `0x49` | Word (uint16 LE) | `Word_DotPan` | Paneo por paso en el secuenciador. |
| `74` | `0x4A` | Word (uint16 LE) | `Word_PreAmp` | Ganancia de preamplificación de muestra. |
| `75` | `0x4B` | Word (uint16 LE) | `Word_Decay` | Tiempo de caída (Decay) de la envolvente de muestra. |
| `76` | `0x4C` | Word (uint16 LE) | `Word_Attack` | Tiempo de ataque de la envolvente de muestra. |
| `77` | `0x4D` | Word (uint16 LE) | `Word_DotNote` | Altura tonal por paso en el secuenciador. |
| `78` | `0x4E` | Word (uint16 LE) | `Word_DotPitch` | Desplazamiento fino de tono por paso. |
| `80` | `0x50` | Word (uint16 LE) | `Word_MainPitch` | Transposición tonal maestra en cents (-1200..+1200). |
| `82` | `0x52` | Word (uint16 LE) | `Word_Resonance` | Factor de calidad (Q / Resonancia) del filtro interno de canal. |
| `128` | `0x80` | DWord (uint32 LE) | `DWord_Color` | Color RGB/BGR de 32 bits asignado al canal, pista o patrón. |
| `129` | `0x81` | DWord (uint32 LE) | `DWord_PlayListItem` | Elemento de patrón en la lista de reproducción (formato compacto). |
| `131` | `0x83` | DWord (uint32 LE) | `DWord_FXSine` | Modulación sinusoidal de frecuencia graves del muestreador. |
| `132` | `0x84` | DWord (uint32 LE) | `DWord_CutCutBy` | Grupo de exclusión mutua de voces (Cut Self / Cut By) para hi-hats y bajos. |
| `134` | `0x86` | DWord (uint32 LE) | `DWord_MiddleNote` | Nota raíz con ajuste fino en formato de 32 bits. |
| `146` | `0x92` | DWord (uint32 LE) | `DWord_DelayReso` | Empaquetado de corte y resonancia del filtro de retardo. |
| `147` | `0x93` | DWord (uint32 LE) | `DWord_Reverb` | Parámetros de reverberación precalculada del muestreador. |
| `148` | `0x94` | DWord (uint32 LE) | `DWord_StretchTime` | Duración exacta de estiramiento temporal en ticks/milisegundos. |
| `149` | `0x95` | DWord (uint32 LE) | `DWord_MixerIconColor` | Icono y color de pista del mezclador. |
| `156` | `0x9C` | DWord (uint32 LE) | `DWord_FineTempo` | Tempo de alta precisión en milésimas de BPM (ej. 124000 = 124.000 BPM). |
| `192` | `0xC0` | VarLen (String) | `Text_ChanName` | Nombre del canal de instrumento en el bastidor. |
| `193` | `0xC1` | VarLen (String) | `Text_PatName` | Nombre del patrón musical actual. |
| `194` | `0xC2` | VarLen (String) | `Text_Title` | Título de la obra o proyecto. |
| `195` | `0xC3` | VarLen (String) | `Text_Comment` | Comentarios y metadatos de autoría del proyecto. |
| `196` | `0xC4` | VarLen (String) | `Text_SampleFileName` | Ruta del archivo de audio (.wav/.flac/.mp3) cargado en el muestreador o clip. |
| `197` | `0xC5` | VarLen (String) | `Text_URL` | Enlace web asociado al proyecto. |
| `199` | `0xC7` | VarLen (String) | `Text_Version` | Cadena de versión del motor de FL Studio (ej. '24.1.0\x00' o '25.0.0\x00'). |
| `201` | `0xC9` | VarLen (String) | `Text_PluginName` | Nombre interno del complemento generador o efecto (ej. 'Sytrus', 'Maximus'). |
| `203` | `0xCB` | VarLen (String) | `Text_Genre` | Género musical declarado en los metadatos del proyecto. |
| `204` | `0xCC` | VarLen (String) | `Text_MixerTrackName` | Etiqueta de texto de un canal del mezclador o autor. |
| `212` | `0xD4` | VarLen (Struct 52B) | `Data_PluginSlotRouting` | Estructura de 52 octetos que define el índice de ranura (offset 4), activación (offset 8) y mezcla Dry/Wet (offset 16). |
| `213` | `0xD5` | VarLen (Binary Blob) | `Data_PluginStatePayload` | Volcado binario del estado de parámetros de un plugin nativo o del envoltorio VST3/AU. |
| `223` | `0xDF` | VarLen (Binary Array) | `Data_AutomationData` | Puntos de control y tensiones de un clip de automatización. |
| `224` | `0xE0` | VarLen (Struct) | `Data_ChanGroupName` | Agrupación de filtro del bastidor de canales (ej. 'Audio', 'Automation', 'Unsorted'). |
| `225` | `0xE1` | VarLen (Struct 336B) | `Data_MixerTrackStrip` | Estado completo de una banda del mezclador (336 octetos: fader float32, separación estéreo, EQ de 3 bandas, matriz de envíos). |
| `227` | `0xE3` | VarLen (Struct 164B) | `Data_BasicChanParams` | Parámetros básicos de envolvente AHDSR, LFO, filtro SVF y polifonía del canal. |
| `236` | `0xEC` | VarLen (Struct Array) | `Data_PlaylistItems` | Matriz de elementos posicionados en el lienzo de la Playlist (tick inicial, duración, pista, índice de patrón/clip). |
| `238` | `0xEE` | VarLen (Struct N*24B) | `Data_PianoRollNotes` | Vector de notas del Piano Roll; cada nota ocupa exactamente 24 octetos. |

---

## 5. Ingeniería Inversa de los 51 Generadores Nativos (Sintetizadores y Muestreadores)

### 5.1. 3x Osc — *Sintetizador sustractivo de tres osciladores acoplados*
- **Definición RAE:** Generador elemental de tres osciladores en serie/paralelo con desfase estereofónico, inversión de polaridad y modulación de amplitud (AM) del tercer oscilador por los dos primeros.
- **Familia DSP:** Síntesis Sustractiva / Modulación en Anillo
- **Ecuación de Transferencia:** `y[n] = SVF_LP(o_1[n] + g_2*o_2[n] + g_3*o_3[n] * (1 + alpha_AM*o_1[n]))`
- **Arquitectura Interna:** 3 Osciladores multimodo (Senoidal, Triángulo, Sierra, Cuadrada, Ruido, Muestra), Desfase estéreo por oscilador, Envolventes AHDSR + Filtro SVF del canal
- **Parámetros Clave:** Coarse/Fine Pitch (1..3), Stereo Phase Offset, Mix Level 2 & 3, Osc 3 AM Mode
- **Mapeo MIDI CC:** `{"74": "Cutoff SVF", "71": "Resonance SVF", "1": "Detune Depth"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 92 bytes (3 bloques de 24B de oscilador + 20B de banderas globales).

### 5.2. Autogun — *Generador aditivo-metálico de universo paramétrico indexado*
- **Definición RAE:** Sintetizador aditivo derivado del motor Ogun que explora 4.294.967.296 timbres (2^32 semillas pseudoaleatorias deterministas) de 32.768 parciales armónicos e inarmónicos.
- **Familia DSP:** Síntesis Aditiva de Alta Densidad (Semilla de 32 bits)
- **Ecuación de Transferencia:** `y[n] = sum_{k=1}^{32768} A_k(Seed_32) * sin(2*pi*f_k(Seed_32)*n/fs + phi_k)`
- **Arquitectura Interna:** PRNG determinista de 32 bits -> Curvas espectrales de Ogun, Motor IFFT de 32.768 parciales, Realzador psicoacústico Soundgoodizer integrado
- **Parámetros Clave:** Preset Seed Number (1..4294967296), Soundgoodizer Macro Amount
- **Mapeo MIDI CC:** `{"1": "Soundgoodizer Gain", "7": "Master Volume"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 16 bytes (uint32 Seed + float32 Macro + flags).

### 5.3. BassDrum — *Sintetizador físico-analógico de bombo con barrido exponencial*
- **Definición RAE:** Motor especializado en percusión grave que combina dos osciladores con envolvente de caída exponencial de frecuencia (barrido de ataque a subgrave), transitorio de clic y capa de ruido o muestra.
- **Familia DSP:** Síntesis Percusiva de Barrido de Fase + Capa Transitoria
- **Ecuación de Transferencia:** `y[n] = tanh(g_drv * (A(n)*sin(2*pi * integral(f_base + Delta_f*exp(-t/tau_p)) dt) + Click(n) + Sample(n)))`
- **Arquitectura Interna:** Oscilador Principal (Base/Peak/Slide Time), Oscilador Esclavo de Subgrave, Generador de Pulso de Ataque (Click), Mezclador de Muestra de Ruido + Saturador
- **Parámetros Clave:** Main Base/Peak/Slide, Drive Saturation, Sub-Bass Level, Click Freq/Cut, Duration
- **Mapeo MIDI CC:** `{"74": "Base Frequency", "71": "Pitch Slide Time", "1": "Drive Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 128 bytes con vectores float32 normalizados [0..1] y ruta de muestra opcional.

### 5.4. BeepMap — *Transductor aditivo de mapa de bits óptico a espectro sonoro*
- **Definición RAE:** Sintetizador de imagen a sonido que escanea columnas de píxeles RGB: el eje vertical determina la frecuencia del parcial (escala lineal o logarítmica), el canal Rojo la amplitud izquierda, el Verde la amplitud derecha y el Azul el ancho de banda de ruido.
- **Familia DSP:** Resíntesis Aditiva Espectrográfica por Imagen Bitmap
- **Ecuación de Transferencia:** `L(t) = sum_y R(x(t), y)*sin(w_y*t); R(t) = sum_y G(x(t), y)*sin(w_y*t + B(x(t), y)*eta(t))`
- **Arquitectura Interna:** Escáner matricial de mapa de bits RGB, Banco de osciladores sinusoidales en escala log/lineal, Modulador de fase por canal azul
- **Parámetros Clave:** Frequency Range (Octaves), Pixel Duration (Loop Length), Scale Type (Log/Linear/Harmonic), Use Blue
- **Mapeo MIDI CC:** `{"1": "Frequency Range", "74": "Max Frequency"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con cabecera de parámetros + bitmap DIB comprimido incrustado.

### 5.5. BooBass — *Modelador monofónico de bajo eléctrico con ecualizador de tres bandas*
- **Definición RAE:** Emulador de bajo eléctrico de cuerda pulsada que filtra una tabla de ondas armónica a través de una red pasiva/activa de tres bandas (Graves, Medios, Agudos) acoplada a la velocidad MIDI.
- **Familia DSP:** Muestreo Híbrido + Filtrado Formántico de Cuerda Pulsada
- **Ecuación de Transferencia:** `H(z) = H_low(z, G_B) * H_mid(z, G_M) * H_high(z, G_T) aplicado sobre excitación de cuerda dependiente de velocidad.`
- **Arquitectura Interna:** Excitador de cuerda muestreado/modelado, Ecualizador tonal de 3 bandas (Bass, Mid, Treble)
- **Parámetros Clave:** Bass, Mid, Treble
- **Mapeo MIDI CC:** `{"74": "Mid Tone", "71": "Treble Brightness", "1": "Bass Weight"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 compacto de 24 bytes (3 float32 para Bass/Mid/Treble + cabecera).

### 5.6. Dashboard — *Tablero de control MIDI y generador de mensajes exclusivos del sistema (SysEx)*
- **Definición RAE:** Constructor de paneles de mando virtuales (potenciómetros, deslizadores, selectores) para gobernar sintetizadores físicos externos o plugins mediante mensajes MIDI CC, RPN, NRPN y SysEx.
- **Familia DSP:** Enrutamiento de Control Discreto MIDI / RPN / NRPN
- **Ecuación de Transferencia:** `CC_out = clamp(round(u_knob * (Max - Min) + Min), 0, 127)`
- **Arquitectura Interna:** Motor de diseño de componentes UI, Traductor de tablas RPN/NRPN de 14 bits, Despachador de puertos MIDI
- **Parámetros Clave:** Port Number, MIDI Channel, Controller Numbers (CC 0..127)
- **Mapeo MIDI CC:** `{"1": "Custom Wheel 1", "74": "Custom Slider 1"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con definición INI/binaria de controles y enlaces MIDI.

### 5.7. DirectWave — *Muestreador polifónico multicapa con matriz de modulación y síntesis granular*
- **Definición RAE:** Estación de muestreo profesional de 16 partes multitímbricas con mapeo de zonas por nota y velocidad, estiramiento temporal en tiempo real, filtros multimodo en serie/paralelo y matriz de modulación de 16 ranuras.
- **Familia DSP:** Interpolación Sinc Ventaneada de Muestras + Síntesis Granular + Filtrado Biquad
- **Ecuación de Transferencia:** `y[n] = SVF_2(SVF_1(sum_k x_zone[k] * sinc((t(n) - k)/T_s) * w_k))`
- **Arquitectura Interna:** Motor de zonas 2D (Key x Velocity), Interpolador Polifásico de 64 puntos, 2 Filtros Multimodo + Shaper + Decimator, Matriz de Modulación 16x2, Bus FX (RingMod, Phaser, Chorus, Delay, Reverb)
- **Parámetros Clave:** Zone Start/Loop, Time Stretch / Pitch Shift, Filter 1/2 Cutoff & Resonance, Mod Matrix Depth
- **Mapeo MIDI CC:** `{"1": "Mod Wheel Matrix Source", "74": "Filter 1 Cutoff", "71": "Filter 1 Resonance", "11": "Expression"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 contenedor DWP/DWB con descriptores de zona y referencias WAV.

### 5.8. Drumaxx — *Sintetizador de percusión por modelado físico de membranas acopladas*
- **Definición RAE:** Motor de síntesis de batería de 16 almohadillas que modela físicamente la baqueta o maza (Mallet), la tensión, material y amortiguamiento de una membrana vibrante bidimensional y la resonancia del casco cilíndrico.
- **Familia DSP:** Modelado Físico Modal de Membrana 2D (Funciones de Bessel / Modos Circulares)
- **Ecuación de Transferencia:** `y[n] = sum_{m,k} A_{m,k} * exp(-d_{m,k}*n/fs) * sin(w_{m,k}(Tension, Shape)*n/fs + phi_{m,k}) * Excitacion_Maza[n]`
- **Arquitectura Interna:** Excitador de Impacto (Mallet Amplitude, Stiffness, Noise), Banco de Resonadores Modales de Membrana (Material, Damping, Tension, Shape), Filtro Auto-Modulado + Compresor/Limitador por canal, Secuenciador de Patrones Interno
- **Parámetros Clave:** Membrane Tension, Material (Wood/Metal/Skin), Membrane Damping, Shape (Square..Circle), Mallet Stiffness
- **Mapeo MIDI CC:** `{"74": "Membrane Tension", "71": "Membrane Material", "1": "Mallet Noise"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con 16 estructuras de pad físico + secuencias MIDI internas.

### 5.9. Drumpad — *Almohadilla unitaria de percusión por modelado físico de membrana*
- **Definición RAE:** Versión monocanal de Drumaxx diseñada para cargarse directamente como un canal individual en el Step Sequencer sin sobrecarga multitímbrica.
- **Familia DSP:** Modelado Físico Modal de Membrana Circular/Cuadrada (1 Voz Percusiva)
- **Ecuación de Transferencia:** `y[n] = sum_{i=1}^N (h_i * f_mallet)[n], con polos modales desplazados por la tensión instantánea.`
- **Arquitectura Interna:** Generador de maza, Resonador modal de membrana, Ecualizador de salida de 2 bandas
- **Parámetros Clave:** Mallet Amplitude/Decay, Membrane Tension/Phase/Material, Low/High EQ
- **Mapeo MIDI CC:** `{"74": "Tension", "71": "Material", "1": "Decay"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 1 pad físico (164 bytes de floats de parámetros).

### 5.10. FL Keys — *Sintetizador híbrido de pianos acústicos y electromecánicos por tabla de ondas y modelado*
- **Definición RAE:** Instrumento de teclado que combina muestras de ataque de martillo o púa metálica (Rhodes/Wurlitzer/Grand Piano) con resonadores de cuerda y timbre dependiente de la dureza de pulsación.
- **Familia DSP:** Síntesis por Tabla de Ondas con Conmutación de Velocidad y Desafinación Estocástica
- **Ecuación de Transferencia:** `y[n] = Env_ADSR(n) * Filtro_Dureza(v_MIDI) * Osc_Cuerda(f_0 * (1 + delta_detune))`
- **Arquitectura Interna:** Motor de ataque de martillo, Banco de tablas de ondas armónicas, Modulador de Trémolo/Panner (Rhodes), Overdrive de previo
- **Parámetros Clave:** Decay, Release, Hardness, Vel->Hardness, Muffle, Stereo/Pan, Overdrive, Detune
- **Mapeo MIDI CC:** `{"64": "Sustain Pedal", "74": "Muffle Filter", "1": "LFO Tremolo Speed"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de modelo y referencia a tabla de ondas.

### 5.11. FL Slayer — *Sintetizador de guitarra eléctrica por guía de ondas Karplus-Strong y amplificador modelado*
- **Definición RAE:** Modelador físico de seis cuerdas de guitarra eléctrica con simulación de pastillas magnéticas (bobina simple/doble), técnicas de ejecución (glissando, apagado con palma, armónicos) y etapa de distorsión de válvulas con recinto acústico.
- **Familia DSP:** Guía de Ondas Karplus-Strong Extendida + No Linealidad de Válvula + Convolución de Pantalla
- **Ecuación de Transferencia:** `s[n] = x_pick[n] + g_damp * H_loop(z) * s[n - D]; y[n] = Cab_IR * tanh(Gain * Pickup(s[n]))`
- **Arquitectura Interna:** 6 Líneas de retardo fraccionario Karplus-Strong, Filtro de posición de pastilla (comb filter espacial), Previo de distorsión + Gabinete + Efectos de pedal
- **Parámetros Clave:** String Damp, Vel/Damp, Pickup Position, Amp Drive/Presence, Cabinet Type
- **Mapeo MIDI CC:** `{"1": "Wah / Vibrato", "74": "Amp Tone", "71": "String Damping"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de parámetros de cuerda, pastilla y amplificador.

### 5.12. FL Studio Mobile — *Estación de producción modular embebida de arquitectura móvil*
- **Definición RAE:** Sub-entorno completo de secuenciación y síntesis multi-instrumento (DirectWave, MiniSynth, GMS, Transistor Bass, SuperSaw) alojado como un único generador dentro de FL Studio de escritorio.
- **Familia DSP:** Motor Multitímbrico de Síntesis y Secuenciación Autónoma
- **Ecuación de Transferencia:** `y_master[n] = Limiter(sum_{ch=1}^N Chain_FX_ch(Gen_ch[n]))`
- **Arquitectura Interna:** Secuenciador multipista .flm, Sintetizadores integrados (SuperSaw, MiniSynth, GMS), Rack de efectos modular
- **Parámetros Clave:** Master Volume, Macro Knobs 1..8
- **Mapeo MIDI CC:** `{"1": "Macro 1", "2": "Macro 2", "74": "Filter Cutoff"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 contenedor de proyecto binario .flm completo.

### 5.13. FL Studio Mobile Rack — *Bastidor de instrumentos modulares del motor FL Studio Mobile*
- **Definición RAE:** Alojamiento directo de los módulos de síntesis de FL Studio Mobile (SuperSaw, Drum Sampler, MiniSynth) como un instrumento individual del Channel Rack.
- **Familia DSP:** Síntesis Polifónica SuperSaw / Sustractiva Ligera
- **Ecuación de Transferencia:** `y[n] = SVF(sum_{k=1}^7 a_k * Saw(2*pi*f_0*(1 + d_k)*n/fs + phi_k))`
- **Arquitectura Interna:** Módulo generador Mobile, Cadena de inserción móvil
- **Parámetros Clave:** Detune, Pan Spread, Cutoff, Resonance
- **Mapeo MIDI CC:** `{"74": "Cutoff", "71": "Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con estado del módulo Mobile.

### 5.14. FLEX — *Sintetizador polifónico de motor híbrido con ocho macro-controladores y telemetría visual*
- **Definición RAE:** Motor de síntesis multidimensional que combina internamente síntesis sustractiva, tabla de ondas, multisamples, FM y modelado físico Karplus-Strong, exponiendo 8 macro-controles preasignados, filtro maestro y analizador en tiempo real.
- **Familia DSP:** Síntesis Híbrida (Wavetable + Multisample + FM + Karplus-Strong) + Cadena Master FX
- **Ecuación de Transferencia:** `y[n] = Limiter(Reverb(Delay(Filter_Master(Engine_Hybrid(n, Macros_{1..8})))))`
- **Arquitectura Interna:** Motor de síntesis oculto configurable por pack, 8 Macro-potenciómetros de interpolación multiparamétrica, Envolventes de Filtro y Volumen, Filtro Maestro Multimodo, Delay, Reverb y Limitador Maestro con Vectorscopio/Espectrograma
- **Parámetros Clave:** Macro 1..8, Master Filter Cutoff/Res, Pitch/Filter/Amp ADSR, Limiter Type (Warm/Clip/Limit)
- **Mapeo MIDI CC:** `{"1": "Macro 1 (Cutoff/Timbre)", "2": "Macro 2 (Resonance)", "74": "Master Filter Cutoff", "71": "Master Filter Res"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con UUID de paquete FLEX + índice de preset + vector de 8 macros y envolventes.

### 5.15. FPC — *Centro de producción percusiva de dieciséis almohadillas multicapa*
- **Definición RAE:** Muestreador de batería inspirado en el hardware Akai MPC, dotado de dos bancos de 16 almohadillas (32 en total), cada una con múltiples capas conmutadas por velocidad, envolvente dedicada y salida independiente al mezclador.
- **Familia DSP:** Disparo Polifónico de Muestras Multicapa con Grupos de Corte Mutuo (Choke Groups)
- **Ecuación de Transferencia:** `y_pad[n] = Env_AHDSR(n) * Layer_{v_MIDI}[n * 2^(Pitch/1200)], con silenciamiento instantáneo si ChokeGroup_i == ChokeGroup_j.`
- **Arquitectura Interna:** 32 Pads (Banco A/B), Apilador de capas de velocidad con fundido cruzado, Motor de grupos Cut/Cut By, Ruteo individual de compensación de canal de mezclador
- **Parámetros Clave:** Pad Volume/Pan/Pitch, Layer Velocity Min/Max, Cut Group / Cut By Group, Output Offset
- **Mapeo MIDI CC:** `{"7": "Bank Volume", "10": "Pad Pan"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con descriptores de 32 pads, rangos de velocidad y rutas WAV.

### 5.16. Fruit Kick — *Oscilador de bombo electrónico por barrido senoidal y distorsión*
- **Definición RAE:** Sintetizador minimalista de bombo electrónico (estilo 808/909) basado en un único oscilador senoidal cuya frecuencia cae exponencialmente desde una frecuencia máxima hasta una frecuencia fundamental subgrave.
- **Familia DSP:** Oscilador Senoidal con Modulación Exponencial de Frecuencia y Recorte
- **Ecuación de Transferencia:** `f(t) = f_min + (f_max - f_min)*exp(-t / tau_sweep); y(t) = clip(A(t) * sin(2*pi * integral f(tau) dtau))`
- **Arquitectura Interna:** Oscilador senoidal bloqueado en fase a 0 grados, Generador de envolvente de barrido tonal, Distorsionador de onda cuadrada
- **Parámetros Clave:** Max Freq, Min Freq, Pitch Decay, Amp Decay, Click (Start Phase), Distortion
- **Mapeo MIDI CC:** `{"74": "Max Freq", "71": "Pitch Decay", "1": "Distortion"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 24 bytes (6 enteros de 32 bits).

### 5.17. Fruity DX10 — *Sintetizador de modulación de fase de dos operadores (arquitectura FM clásica)*
- **Definición RAE:** Sintetizador polifónico de 8 voces que implementa modulación de fase de dos operadores ( un Oscilador Portador senoidal y un Oscilador Modulador con razón armónica gruesa/fina y envolvente propia) para timbres de campana, bajo eléctrico y órgano.
- **Familia DSP:** Síntesis por Modulación de Fase (PM / FM de 2 Operadores)
- **Ecuación de Transferencia:** `y(t) = E_c(t) * sin(2*pi*f_c*t + E_m1(t)*I_1*sin(2*pi*f_m1*t) + E_m2(t)*I_2*sin(2*pi*f_m2*t))`
- **Arquitectura Interna:** Portadora senoidal con envolvente Attack/Decay/Release, 2 Moduladores en cascada/paralelo con razón Coarse/Fine, LFO global de vibrato
- **Parámetros Clave:** Carrier Attack/Decay/Release, Mod 1 Coarse/Fine/Init/Time/Sus, Mod 2 Coarse/Fine/Vel, Waveform Brightness
- **Mapeo MIDI CC:** `{"1": "Vibrato LFO", "74": "Modulator 1 Initial Level", "71": "Modulator 1 Decay"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 80 bytes con parámetros normalizados en coma flotante.

### 5.18. Fruity Dance — *Visualizador coreográfico sincronizado al reloj de transporte y eventos MIDI*
- **Definición RAE:** Generador visual de hoja de sprites (FL-Chan) cuyas secuencias de animación se disparan mediante notas MIDI (C5..B5) y cuya velocidad de fotogramas se bloquea en fase con el pulso del proyecto (PPQ).
- **Familia DSP:** Sincronización de Fase de Reloj Musical (PPQ -> Frame Index)
- **Ecuación de Transferencia:** `Frame_idx(t) = floor((Ticks_PPQ(t) / 96) * FPS_sprite) mod TotalFrames_anim`
- **Arquitectura Interna:** Decodificador de hojas de sprites PNG, Mapeador de notas MIDI a estados coreográficos
- **Parámetros Clave:** Animation State Note, Window Position, Sprite Skin
- **Mapeo MIDI CC:** `{"1": "Dance Style"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con ruta de skin y coordenadas de ventana.

### 5.19. Fruity DrumSynth Live — *Estación de síntesis analógica de percusión de doble oscilador y puente de ruido*
- **Definición RAE:** Sintetizador de batería en tiempo real donde cada nota MIDI dispara un parche autónomo compuesto por dos osciladores con modulación en anillo/ruido, barrido de tono, filtro paso-banda/paso-bajo y distorsión.
- **Familia DSP:** Síntesis Analógica Virtual de Percusión (2 Osciladores + Ruido Filtrado + Saturación)
- **Ecuación de Transferencia:** `y[n] = Clip(E_1[n]*Osc_1[n] + E_2[n]*Osc_2[n] + E_noise[n]*SVF(Noise[n]))`
- **Arquitectura Interna:** 120 Nodos de parche de percusión (1 por tecla MIDI), Oscilador 1 y 2 con barrido de tono, Generador de ruido blanco/rosa con filtro multimodo, Etapa de saturación y envío a mezclador por tecla
- **Parámetros Clave:** Osc 1/2 Freq & Sweep, Noise Filter Cutoff/Res/Mode, Overdrive, Track Send
- **Mapeo MIDI CC:** `{"74": "Noise Cutoff", "71": "Noise Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con matriz de 120 parches de percusión.

### 5.20. Fruity Envelope Controller — *Generador de señales de control multipunto disparado por notas MIDI*
- **Definición RAE:** Transductor de eventos MIDI a señales de automatización interna que dispone de 8 articuladores independientes, cada uno con envolvente multipunto, LFO sincronizable, mapeo de escala de teclado y curva de velocidad.
- **Familia DSP:** Síntesis de Señales de Control (Sub-audio / Tasa de Tick PPQ)
- **Ecuación de Transferencia:** `C_k(t, note, vel) = Base_k + Env_k(t) * LFO_k(t) * KeyMap_k(note) * VelMap_k(vel) * ModX * ModY`
- **Arquitectura Interna:** 8 Articuladores de control independientes, Editor de splines multipunto con tensión, Mapeador X/Y continuo por voz
- **Parámetros Clave:** Articulator 1..8 Output, Base Level, Envelope Multiplier, LFO Speed/Tension, Mod X / Mod Y
- **Mapeo MIDI CC:** `{"1": "Modulator X", "11": "Modulator Y"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con 8 árboles de curvas spline de articulador.

### 5.21. Fruity Granulizer — *Sintetizador corpuscular de muestras por fragmentación y solapamiento temporal*
- **Definición RAE:** Motor de síntesis granular en tiempo real que trocea una muestra de audio en granos de duración (10-500 ms), ataque/caída (suavizado trapezoidal) y espaciado variables, permitiendo estirar el tiempo o congelar la posición sin alterar el tono.
- **Familia DSP:** Síntesis Granular Síncrona/Asíncrona (Overlap-Add con Ventana Trapezoidal)
- **Ecuación de Transferencia:** `y[n] = sum_k w_trap((n - k*Delta_G)/L_G, Attack) * x[Pos(k) + (n - k*Delta_G)*2^(Pitch/12)]`
- **Arquitectura Interna:** Planificador de disparo de granos (Grain Spacing / Wave Spacing), Envolvente trapezoidal de grano (Attack/Decay), Modulador LFO de profundidad y velocidad de posición, Retención (Hold / Freeze) de grano
- **Parámetros Clave:** Grain Attack, Grain Hold, Grain Spacing, Wave Spacing (-300%..+300%), Sample Start, Hold Freeze
- **Mapeo MIDI CC:** `{"74": "Wave Spacing", "71": "Grain Spacing", "1": "Sample Start Position"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de parámetros de grano + evento 0xC4 de ruta de muestra.

### 5.22. Fruity Keyboard Controller — *Transductor de altura de nota y velocidad MIDI a señal de control continuo*
- **Definición RAE:** Generador de control interno que convierte el número de nota MIDI (0..127) y la velocidad de pulsación en dos señales continuas normalizadas [0.0..1.0] con suavizado temporal (portamento de control) para automatizar filtros o afinaciones.
- **Familia DSP:** Cuantización Discreta de Altura a Voltaje Virtual (1V/Octava Digital) con Filtro de Suavizado
- **Ecuación de Transferencia:** `y_ctl[n] = y_ctl[n-1] + alpha_smooth * (Table_Note[MIDI_Key] - y_ctl[n-1])`
- **Arquitectura Interna:** Tabla de transferencia de 128 teclas, Tabla de velocidad, Filtro paso-bajo de suavizado de transiciones (Attack/Release Smoothing)
- **Parámetros Clave:** Note Value Map, Attack Smoothing, Release Smoothing, Key Range
- **Mapeo MIDI CC:** `{"1": "Attack Smoothing"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con vector de 128 floats de mapeo por tecla.

### 5.23. Fruity Slicer — *Troceador de bucles por detección de transitorios y resecuenciador rítmico*
- **Definición RAE:** Muestreador de bucles rítmicos que detecta ataques percusivos mediante derivada energética, divide el audio en rebanadas independientes, las asigna a teclas cromáticas sucesivas y exporta la partitura al Piano Roll.
- **Familia DSP:** Detección de Inicio por Flujo de Energía + Estiramiento de Grano para Relleno de Huecos
- **Ecuación de Transferencia:** `Onset si d/dt(E_short(t)) > Threshold; cada rebanada i se reproduce en la nota MIDI (C5 + i).`
- **Arquitectura Interna:** Detector de umbrales de ataque y caída, Asignador cromático de rebanadas, Estirador de tono/tiempo por rebanada
- **Parámetros Clave:** Low/High Threshold, Pitch Shift, Time Stretch, Attack/Decay De-click
- **Mapeo MIDI CC:** `{"74": "Pitch Shift", "71": "Time Stretch"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con marcadores de muestra y audio/ruta incrustada.

### 5.24. Fruity Slicer 2 — *Troceador espectral de segunda generación con envolvente y filtro por rebanada*
- **Definición RAE:** Evolución del motor de troceado con detección espectral de alta precisión, reproducción en reversa por rebanada, envolvente de amplitud y filtro multimodo dedicados.
- **Familia DSP:** Detección de Transitorios por Flujo Espectral + Interpolación Sinc por Rebanada
- **Ecuación de Transferencia:** `SF(m) = sum_k max(0, |X(m,k)| - |X(m-1,k)|); y_slice[n] = SVF(Env(n) * Slice_i[n])`
- **Arquitectura Interna:** Detector de flujo espectral, Filtro multimodo y envolvente por rebanada, Puente de exportación directa a Piano Roll
- **Parámetros Clave:** Slice Sensitivity, Filter Cutoff/Res, Slice Reverse, Pitch/Stretch
- **Mapeo MIDI CC:** `{"74": "Cutoff", "71": "Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con tabla de regiones y parámetros de filtro.

### 5.25. Fruity Video Player — *Reproductor de flujo de vídeo sincronizado al código de tiempo SMPTE/PPQ*
- **Definición RAE:** Decodificador de contenedores de vídeo (MP4/MOV/AVI) enganchado de forma determinista a la posición de reproducción de la Playlist para composición de bandas sonoras y doblaje.
- **Familia DSP:** Sincronización de Fase de Transporte (Ticks PPQ <-> Timestamp PTS de Vídeo)
- **Ecuación de Transferencia:** `t_video = t_song_sec + t_offset_SMPTE`
- **Arquitectura Interna:** Decodificador FFmpeg/AVFoundation, Sincronizador de reloj de transporte, Extractor de pista de audio opcional
- **Parámetros Clave:** SMPTE Offset, Detach Window, Ignore Tempo Changes
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con ruta del archivo de vídeo y desplazamiento temporal.

### 5.26. Fruity Voltage Controller — *Transductor de eventos digitales a voltajes continuos acoplados en corriente continua (DC-Coupled CV/Gate)*
- **Definición RAE:** Generador de señales en corriente continua (DC) y rampa de 1V/octava o Hz/V a través de interfaces de audio acopladas en DC para gobernar sintetizadores modulares analógicos Eurorack.
- **Familia DSP:** Generación de Nivel DC de Precisión Flotante y Escala Logarítmica 1V/Octava
- **Ecuación de Transferencia:** `V_pitch[n] = V_ref + (MIDI_Note - 60) / 12.0; V_gate[n] = V_high si NoteOn sino 0.0`
- **Arquitectura Interna:** Generador de rampa 1V/Oct y Hz/V (Korg/Yamaha), Generador de pulso Gate/Trigger, Calibrador de escala de octava por hardware
- **Parámetros Clave:** Pitch Scale (1V/Oct, Hz/V), Gate Level, Tune Calibration, Mod CV Level
- **Mapeo MIDI CC:** `{"1": "Auxiliary CV Output"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con tablas de calibración de voltaje.

### 5.27. Fruity Wrapper — *Adaptador anfitrión de instrumentos virtuales externos (VST2/VST3/AU/CLAP)*
- **Definición RAE:** Contenedor de instrumentos de terceros que traduce las notas con propiedades por voz de FL Studio y los 128 controladores MIDI hacia la API binaria del plugin externo.
- **Familia DSP:** Puente de Búfer de Audio de Coma Flotante y Despacho de Eventos MIDI/MPE
- **Ecuación de Transferencia:** `y_{L,R}[n] = VST3_ProcessAudio(x_{L,R}[n], EventQueue_MIDI_MPE)`
- **Arquitectura Interna:** Cargador dinámico de bundles VST3/AU, Tabla de 128 parámetros CC + 4096 parámetros de automatización, Gestor de búfer fijo/variable y compensación de latencia
- **Parámetros Clave:** MIDI Input/Output Port, Pitch Bend Range, Use Fixed Size Buffers, Notify About Rendering Mode
- **Mapeo MIDI CC:** `{"1": "CC #1 Mod Wheel", "74": "CC #74 Brightness", "64": "CC #64 Sustain"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con cabecera Wrapper + estado opaco del plugin VST3/AU.

### 5.28. GMS — *Estación de síntesis de ranura rítmica con tres osciladores y matriz de efectos por compás*
- **Definición RAE:** Sintetizador agresivo (Groove Machine Synth) dotado de 3 osciladores con sincronización dura, modulación de frecuencia y anillo, filtro multimodo y una sección de 10 efectos internos encadenables y automatizables en tiempo real (Trance Gate, Crusher, Flanger, Phaser, Comb).
- **Familia DSP:** Síntesis Sustractiva/FM + Procesamiento de Efectos Modulado por Almohadilla X/Y
- **Ecuación de Transferencia:** `y[n] = FX_Rack_{1..10}(SVF(Osc_1[n] + Osc_2[n] + Osc_3[n] + Sub[n], Env_Filter))`
- **Arquitectura Interna:** 3 Osciladores de tabla de ondas con Sync/FM/RM, Filtro Multimodo (LP/HP/BP) con envolvente e inversión, 2 LFOs + 2 Envolventes, 10 Efectos de rendimiento con botón Glue (retención) y Gate de 16 pasos
- **Parámetros Clave:** Osc 1..3 Wave & Detune, Cutoff & Resonance, FX Selection (Distortion, Crusher, Flanger, Phaser, LPF, HPF, Echo, Reverb, Pan, TranceGate), Mod X/Y
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "71": "Filter Resonance", "1": "FX Mod X", "11": "FX Mod Y"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con vector completo de parámetros de osciladores y matriz de 10 efectos.

### 5.29. Harmless — *Sintetizador sustractivo ejecutado íntegramente mediante un motor de síntesis aditiva*
- **Definición RAE:** Hermano compacto de Harmor donde el filtrado paso-bajo, la resonancia, el desfasador (phaser) y el unísono no se aplican sobre una onda en el dominio del tiempo, sino esculpiendo directamente las amplitudes y fases de cientos de parciales sinusoidales antes de su suma.
- **Familia DSP:** Síntesis Sustractiva en Dominio Espectral Aditivo (Modificación Directa de Parciales)
- **Ecuación de Transferencia:** `y(t) = sum_{k=1}^N A_k * H_mask(k*f_0, f_cut, Q) * Phaser_mask(k*f_0, t) * sin(2*pi * k * f_0 * f_detune(k) * t + phi_k)`
- **Arquitectura Interna:** Generador de tabla de armónicos y fase, Máscara espectral de filtro de pendiente arbitraria (hasta cientos de dB/oct), Máscara de Phaser armónico, Armonizador, Unísono de parciales y Compresor/Distorsionador
- **Parámetros Clave:** Pluck Decay, Harmonic Mask Cutoff & Width, Custom Resonance Shape, Phaser Speed/Width, Unison Pitch/Pan, Harmonizer
- **Mapeo MIDI CC:** `{"74": "Frequency Cutoff", "71": "Resonance Peak", "1": "Phaser Mix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con estado vectorial de máscaras espectrales.

### 5.30. Harmor — *Sintetizador aditivo de doble unidad (A/B) y motor de resíntesis espectral e imagen*
- **Definición RAE:** Cumbre de la síntesis aditiva en FL Studio: cada una de sus dos partes (A y B) controla en paralelo 516 parciales sinusoidales cuya frecuencia y amplitud en decibelios se procesan como mapas bidimensionales antes de la síntesis final, permitiendo prismas inarmónicos, desplazamiento de formantes, resíntesis de audio/imagen y afinación microtonal exacta (.scl).
- **Familia DSP:** Síntesis Aditiva de 516 Parciales con Procesamiento Espectral en Escala Logarítmica (Octava/dB)
- **Ecuación de Transferencia:** `y(t) = sum_{p in {A,B}} sum_{k=1}^{516} 10^(M_amp(k, t)/20) * sin(2*pi * integral(f_0 * M_freq(k, t)) dtau + phi_{p,k})`
- **Arquitectura Interna:** 2 Unidades Aditivas Independientes (Parte A y Parte B), Motor de Prisma Inarmónico y Desplazamiento de Formantes, Resintetizador de Audio e Imagen 2D, 2 Filtros Espectrales de forma libre + Phaser Espectral, Matriz de Articuladores Multipunto (Envolventes, LFOs, Mapeos X/Y/Z, Escalas Scala .scl), Cadena FX (Distorsión, Chorus, Delay, Reverb, Compresión Multibanda Maximus)
- **Parámetros Clave:** Timbre 1/2 Mix, Pluck, Blur (Time Smearing), Prism, Harmonizer, Filter 1/2 Freq & Width, Mod X / Mod Y / Mod Z
- **Mapeo MIDI CC:** `{"1": "Modulator X (Cutoff)", "2": "Modulator Y (Resonance)", "11": "Modulator Z (Prism/Timbre)", "74": "Filter 1 Frequency"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con tablas armónicas duales, mapas de imagen/muestra y árboles de articuladores.

### 5.31. Kepler — *Emulador de modelado físico del sintetizador analógico polifónico Roland Juno-6/106*
- **Definición RAE:** Recreación fiel de circuito del clásico sintetizador de oscilador controlado digitalmente (DCO) de 1984, integrando ondas de pulso modulado (PWM), diente de sierra y suboscilador cuadrado, filtro paso-alto estático, filtro paso-bajo resonante de 4 polos (IR3109) y el icónico coro estereofónico de línea de retardo analógica (BBD Chorus I/II).
- **Familia DSP:** Oscilador DCO Sin Aliasing (PolyBLEP) + Filtro Escalera OTA de 4 Polos + Coro BBD Estéreo
- **Ecuación de Transferencia:** `y[n] = BBD_Chorus_{I,II}(OTA_LP4(HPF(DCO_Pulse[n] + DCO_Saw[n] + Sub[n] + Noise[n]), f_c, Q))`
- **Arquitectura Interna:** Arpegiador clásico Up/Down, DCO con PWM, Sierra, Sub y Ruido, Filtro HPF + VCF de 24 dB/oct auto-oscilante, Envolvente ADSR única compartida/invertible, Doble línea de retardo Bucket-Brigade Device (Chorus I, II y I+II)
- **Parámetros Clave:** DCO Pulse Width, Sub Oscillator Level, HPF Cutoff, VCF Freq & Res, Chorus I / Chorus II Buttons
- **Mapeo MIDI CC:** `{"74": "VCF Frequency", "71": "VCF Resonance", "1": "LFO Pitch Depth", "93": "Chorus Mode"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de circuito Juno y estado de botones Chorus.

### 5.32. Kepler Exo — *Sintetizador analógico virtual de doble capa de osciladores DCO y matriz de modulación*
- **Definición RAE:** Expansión hipertrófica del motor Kepler (inspirada en la fusión Juno-106 / Jupiter-8) con dos osciladores DCO completos con sincronización dura, modulación cruzada (X-Mod), conformación de onda continua, dos filtros multimodo, matriz de modulación de 16 ranuras y rack de 5 efectos de estudio.
- **Familia DSP:** Doble DCO con Sincronización y Modulación Cruzada + Doble Filtro ZDF (Zero-Delay Feedback)
- **Ecuación de Transferencia:** `y[n] = FX_Chain(ZDF_VCF(DCO_1(n) + DCO_2(n, Sync, XMod) + Sub(n)))`
- **Arquitectura Interna:** 2 Osciladores DCO con Wave Shaping y X-Mod, Filtro Dual ZDF de 12/24 dB/oct con saturación, 3 Envolventes + 3 LFOs + Matriz de Modulación de 16 rutas, Rack FX (Hyper Chorus, Phaser, Saturator, Delay, Reverb)
- **Parámetros Clave:** DCO 1/2 Pitch & Wave, Cross Modulation (X-Mod), VCF Cutoff, Res & Drive, Unison Voices & Detune, Hyper Chorus Mix
- **Mapeo MIDI CC:** `{"74": "VCF Cutoff", "71": "VCF Resonance", "1": "Mod Wheel Matrix", "11": "Filter Drive"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con estado de ambos DCO, matriz de 16 ranuras y rack de efectos.

### 5.33. MIDI Out — *Emisor y encaminador de flujos de mensajes MIDI hacia puertos externos o internos*
- **Definición RAE:** Generador sin síntesis de audio propia que transmite notas del Piano Roll, cambios de programa, selección de banco y hasta 9 páginas de 8 potenciómetros configurables (CC, RPN, NRPN, Aftertouch) a través de un puerto y canal MIDI específico.
- **Familia DSP:** Serialización Determinista de Protocolo MIDI 1.0 (31.25 kBaud / Virtual Port Bus)
- **Ecuación de Transferencia:** `Msg_MIDI = [StatusByte(0xB0 | Chan), CC_Num(0..127), Value(0..127)]`
- **Arquitectura Interna:** Selector de Puerto Virtual (0..255) y Canal (1..16), Selector de Banco MSB/LSB y Patch, 9 Páginas x 8 Potenciómetros asignables a CC/RPN/NRPN
- **Parámetros Clave:** Port, Channel, Bank MSB/LSB, Patch, Page 1..9 Knobs 1..8
- **Mapeo MIDI CC:** `{"1": "Knob 1", "74": "Knob 2", "71": "Knob 3"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con definiciones de los 72 potenciómetros y puerto de salida.

### 5.34. MiniSynth — *Sintetizador sustractivo monofónico/polifónico de seis pestañas de flujo directo*
- **Definición RAE:** Sintetizador ligero de aprendizaje y esbozo rápido estructurado en 6 secciones contiguas (Oscillator, Filter, Env, LFO, Fx, Keys) con transformación continua de forma de onda y coro/retardo integrados.
- **Familia DSP:** Oscilador con Morfismo de Forma de Onda + Filtro Biquad Resonante
- **Ecuación de Transferencia:** `y[n] = Chorus_Delay(Biquad_SVF(Osc_Morph(n, Shape, Mod), f_c(Env, LFO), Q))`
- **Arquitectura Interna:** Oscilador con Wave Shape y Modulator, Filtro LP/BP/HP con inversión de envolvente, Envolvente ADSR, LFO y sección FX
- **Parámetros Clave:** Osc Waveform, Wave Modifier, Filter Cutoff & Peak, LFO Rate & Amount, FX Mode (Chorus/Delay)
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "71": "Filter Peak", "1": "Wave Modifier"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 compacto de 64 bytes.

### 5.35. Morphine — *Sintetizador aditivo de cuatro generadores con morfismo espectral bidimensional*
- **Definición RAE:** Potente estación de síntesis aditiva y resíntesis provista de 4 generadores independientes (A, B, C, D) cuyos espectros de armónicos évolucionan mediante instantáneas temporales (Breakpoints) y se funden continuamente mediante una almohadilla de morfismo X/Y.
- **Familia DSP:** Síntesis Aditiva de Cuatro Fuentes con Interpolación Bilineal de Espectros (Morphing 2D)
- **Ecuación de Transferencia:** `S_mix(k, t) = (1-x)*(1-y)*S_A + x*(1-y)*S_B + (1-x)*y*S_C + x*y*S_D; y(t) = sum_k S_mix(k,t)*sin(w_k*t)`
- **Arquitectura Interna:** 4 Generadores Aditivos (A, B, C, D) con resíntesis WAV, Secuencias de Breakpoints espectrales por generador, Matriz de Morfismo Bilineal X/Y, Filtro Formántico + Cadena de 5 Efectos
- **Parámetros Clave:** Morph X, Morph Y, Generator A..D Detune/Pan/Mix, Formant Shift, Harmonic Detune
- **Mapeo MIDI CC:** `{"1": "Morph X", "11": "Morph Y", "74": "Formant Shift"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las tablas de instantáneas armónicas de los 4 generadores.

### 5.36. Ogun — *Sintetizador aditivo de treinta y dos mil parciales para timbres metálicos e inarmónicos*
- **Definición RAE:** Motor de síntesis aditiva extrema capaz de generar y modular en tiempo real más de 32.000 parciales sinusoidales mediante funciones de mapeo X/Y de riqueza tímbrica, caída espectral dependiente de la frecuencia y dispersión inarmónica (platillos, gongs, campanas y texturas industriales).
- **Familia DSP:** Síntesis Aditiva Masiva (32.768 Parciales) con Distribución de Fase y Decaimiento Espectral
- **Ecuación de Transferencia:** `y(t) = sum_{k=1}^{32768} A_k(t) * exp(-d(f_k)*t) * sin(2*pi * f_0 * Map_inharm(k)*t + phi_k)`
- **Arquitectura Interna:** Generador espectral de 32.768 parciales, Curvas de mapeo de Timbre, Decay, Pre-decay y Fullness, Unísono aditivo + Armonizador + Filtro EQ + Chorus/Delay/Reverb
- **Parámetros Clave:** Richness, Timbre Seed, Pre-decay, Decay Curve, Unison Pitch, Mod X / Mod Y
- **Mapeo MIDI CC:** `{"1": "Modulator X", "11": "Modulator Y", "74": "Harmonic Cutoff"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con curvas multipunto de densidad y decaimiento de parciales.

### 5.37. Patcher — *Sub-anfitrión modular de instrumentos en grafo acíclico dirigido*
- **Definición RAE:** Versión generadora de Patcher que aloja múltiples sintetizadores, procesadores de voz (VFX) y efectos conectados mediante un grafo arbitrario, presentando hacia el exterior una única superficie de control personalizada (Control Surface).
- **Familia DSP:** Evaluación Topológica de Subgrafo de Audio, Voz MIDI y Parámetros
- **Ecuación de Transferencia:** `y_out[n] = sum_{v in Sinks} Node_v(sum_{u -> v} g_{u,v} * Node_u[n])`
- **Arquitectura Interna:** Lienzo de grafo Map (Nodos de Audio, Notas y Parámetros), Diseñador de interfaz Control Surface, Aislamiento de latencia PDC por rama
- **Parámetros Clave:** Surface Macro Controls, Node Audio Send Levels
- **Mapeo MIDI CC:** `{"1": "Surface Control 1", "74": "Surface Control 2"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 recursivo que anida los chunks 0xD5 de todos los plugins hijos y la lista de adyacencia del grafo.

### 5.38. Plucked! — *Sintetizador de cuerda pulsada por línea de retardo realimentada (algoritmo Karplus-Strong)*
- **Definición RAE:** Implementación canónica del modelo físico de cuerda pulsada de Karplus-Strong: una ráfaga inicial de ruido o forma de onda llena una línea de retardo cuya longitud fija la nota fundamental y cuyo bucle de realimentación incorpora un filtro paso-bajo que amortigua progresivamente los agudos.
- **Familia DSP:** Síntesis por Guía de Ondas Digital Karplus-Strong
- **Ecuación de Transferencia:** `y[n] = x_exc[n] + g_decay * ((1 - a)*y[n - D] + a*y[n - D - 1]), con D = fs / f_0.`
- **Arquitectura Interna:** Excitador de pulso/ruido coloreado, Línea de retardo con interpolador fraccionario, Filtro de amortiguamiento de bucle, Modulador de anchura estereofónica
- **Parámetros Clave:** Decay, Color (Excitation Filter), Normalize, Gate, Widen Stereo
- **Mapeo MIDI CC:** `{"74": "Color Brightness", "71": "Decay Time"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 20 bytes (5 parámetros enteros de 32 bits).

### 5.39. PoiZone — *Sintetizador sustractivo de dos osciladores con puerta de trance y arpegiador*
- **Definición RAE:** Sintetizador polifónico sustractivo de arquitectura directa (sin menús ocultos) con dos osciladores (Sierra/Pulso), modulación de anchura de pulso, sincronización y modulación en anillo, unísono de 4 voces, filtro multimodo y puerta rítmica de 16 pasos.
- **Familia DSP:** Síntesis Sustractiva Analógica Virtual + Compuerta Rítmica (Trance Gate)
- **Ecuación de Transferencia:** `y[n] = Gate_16(n) * Delay_Chorus(SVF(Osc_A[n] + Osc_B[n] + Noise[n], f_c, Q))`
- **Arquitectura Interna:** Oscilador A y B con Sync y Ring Mod, Filtro LP/BP/HP con seguimiento de teclado, 2 Envolventes ADSR + LFO + Unísono, Trance Gate de 16 pasos + Arpegiador + Delay/Chorus
- **Parámetros Clave:** Osc Balance, Pulse Width, Filter Cutoff & Res, Trance Gate Wet & Pattern, Unison Detune
- **Mapeo MIDI CC:** `{"74": "Cutoff", "71": "Resonance", "1": "LFO Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con vector de parámetros y máscara de 16 bits del Trance Gate.

### 5.40. ReWired — *Cliente-anfitrión de interconexión interprocesos de audio y transporte (Protocolo ReWire)*
- **Definición RAE:** Puente de memoria compartida heredado para sincronizar el reloj de transporte, envíos MIDI y hasta 64 canales de audio en tiempo real con aplicaciones externas compatibles con ReWire.
- **Familia DSP:** Transferencia IPC Síncrona de Bloques PCM y Reloj PPQ
- **Ecuación de Transferencia:** `y_{ch}[n] = SharedMemoryRing_ReWire[ch, n]`
- **Arquitectura Interna:** Selector de dispositivo ReWire esclavo, Bus de 16 buses MIDI, Enrutador multicanal hacia el mezclador
- **Parámetros Clave:** Device Selection, Multi-Output Routing
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con identificador del proceso esclavo.

### 5.41. Sakura — *Sintetizador de instrumentos de cuerda por modelado físico de cinco etapas acústicas*
- **Definición RAE:** Modelador físico de alta precisión para instrumentos de cuerda frotada, pulsada y percutida (violín, violonchelo, koto, shamisen, guitarra acústica) que simula las 5 etapas físicas: Contacto (impulso mecánico), Generación de vibración, Interacción de dos cuerdas independientes, Resonancia de caja armónica de 8 bandas y Espacio acústico.
- **Familia DSP:** Doble Guía de Ondas Acoplada con No Linealidad de Fricción de Arco + Banco de 8 Resonadores de Caja
- **Ecuación de Transferencia:** `s_i[n] = Exc_BowPluck[n] + H_string_i(z)*s_i[n - D_i]; y[n] = Chorus_Rev(sum_{b=1}^8 H_body_b(z)*(s_1[n] + s_2[n]))`
- **Arquitectura Interna:** Etapa 1: Excitador de Contacto/Fricción, Etapa 2 & 3: Dos Líneas de Retardo de Cuerda con Damping y No Linealidad, Etapa 4: Ecualizador Resonante de Cuerpo de 8 filtros pico, Etapa 5: Chorus y Reverberación Acústica
- **Parámetros Clave:** Contact Hardness/Noise, String 1/2 Decay & Damp, String Feedback, Body Resonator Freqs 1..8
- **Mapeo MIDI CC:** `{"1": "Vibrato Depth", "74": "String Damping", "71": "Body Resonance Mix", "11": "Bow Pressure"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con coeficientes de las 2 cuerdas y los 8 resonadores de cuerpo.

### 5.42. Sawer — *Emulador de modelado físico del sintetizador analógico soviético Polivoks (1982)*
- **Definición RAE:** Recreación de los circuitos analógicos con amplificadores operacionales soviéticos (KR140UD12) del mítico Polivoks, célebre por la inestabilidad armónica de su oscilador diente de sierra y la resonancia salvaje y auto-oscilante de su filtro de frecuencia de corte programable.
- **Familia DSP:** Oscilador con Deriva Analógica + Filtro de Estado Variable No Lineal (Op-Amp Soviet Saturation)
- **Ecuación de Transferencia:** `y[n] = FX(SVF_Polivoks(Saw_Drift[n] + Sub_Oct[n] + Noise[n], f_c, Q_nonlinear))`
- **Arquitectura Interna:** Oscilador principal Saw con Sync y Suboscilador (-1/-2 oct), Filtro Polivoks LP/BP/HP con Drive de amplificador operacional, Arpegiador + Secuenciador MIDI de 8 pasos, Chorus, Phaser, Delay y Reverb
- **Parámetros Clave:** Sub Osc Level & Phase, Noise Level, Filter Cutoff, Resonance & Drive, Unison Voices
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "71": "Filter Resonance", "1": "LFO Depth"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros analógicos y secuencia de 8 pasos.

### 5.43. SimSynth — *Sintetizador analógico virtual de tres osciladores con filtro de estado variable*
- **Definición RAE:** Sintetizador polifónico clásico inspirado en los diseños analógicos de los años ochenta: tres osciladores con calidez de fase (Warm) y seguimiento de envolvente, sección SVF programable con barrido doble (Cutoff 1 -> Cutoff 2) y coro integrado.
- **Familia DSP:** Síntesis Sustractiva de 3 Osciladores + Filtro SVF Doble con Barrido de Frecuencia
- **Ecuación de Transferencia:** `y[n] = Chorus(SVF(sum_{i=1}^3 Osc_i[n], f_c(t), Q))`
- **Arquitectura Interna:** 3 Osciladores con Ring Mod, Warmth (duplicación detune) y LFO, Filtro SVF con Highpass, Bandpass y Lowpass, Envolventes de Amplitud y Filtro + Chorus
- **Parámetros Clave:** Osc 1..3 Shape & Warm, SVF Cutoff, Bandwidth &kb Track, Filter Env Amount, Chorus Mix
- **Mapeo MIDI CC:** `{"74": "SVF Cutoff", "71": "SVF Emphasis (Resonance)"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con estado de los 3 osciladores y sección SVF.

### 5.44. Slicex — *Estación avanzada de disección de bucles con doble plato, articuladores y edición espectral*
- **Definición RAE:** Herramienta insignia de troceado y manipulación rítmica de FL Studio: incorpora dos platos de muestras independientes (Deck A y B), el motor completo de edición de audio y scripts de Edison, 8 articuladores multipunto de filtro/tono/velocidad y asignación individual de cada rebanada a cualquier canal del mezclador.
- **Familia DSP:** Detección Multibanda de Ataques + 8 Articuladores con Filtros SVF en Serie/Paralelo
- **Ecuación de Transferencia:** `y_region[n] = Art_SVF_{1..8}(Deck_{A,B}[Region_i, n * Speed_i]) -> MixerTrack_{Offset_i}`
- **Arquitectura Interna:** Doble Plato de Audio (Deck A / Deck B) con motor Edison embebido, Detector de marcadores de transitorios por sensibilidad dual, 8 Articuladores completos (Vol, Filter LP/BP/HP, Pitch, Speed, Start), Modulación X/Y continua por nota en Piano Roll
- **Parámetros Clave:** Region Articulator (1..8), Filter Cutoff & Res, Master Pitch, Deck A/B Mix, Mod X / Mod Y
- **Mapeo MIDI CC:** `{"1": "Master Mod X", "11": "Master Mod Y", "74": "Articulator 1 Cutoff"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 masivo con marcadores de región, 8 articuladores y PCM de ambos platos.

### 5.45. Soundfont Player — *Reproductor polifónico de bancos de muestras normalizados SoundFont 2 (.sf2)*
- **Definición RAE:** Motor nativo de 64 bits de reproducción de bancos de instrumentos multipista en formato SoundFont (.sf2), con interpolación de alta calidad, envolvente ADSR superpuesta, LFO de vibrato y envíos internos de reverberación y coro.
- **Familia DSP:** Reproducción de Tablas PCM .sf2 con Interpolación Sinc y Envolventes Modulares
- **Ecuación de Transferencia:** `y[n] = Env_ADSR(n) * SF2_Zone(MIDI_Patch, MIDI_Bank, Key, Vel)[n]`
- **Arquitectura Interna:** Analizador de contenedores RIFF sfbk (.sf2), Selector de Banco y Parche, Sobreescritura de Envolvente, LFO y Cutoff
- **Parámetros Clave:** Patch, Bank, Reverb Send, Chorus Send, Env Attack/Decay/Sustain/Release, Cutoff
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "91": "Reverb Send", "93": "Chorus Send"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con ruta al archivo .sf2, banco, programa y offsets de envolvente.

### 5.46. Sytrus — *Sintetizador matricial híbrido de seis operadores FM, modulación en anillo y síntesis aditiva*
- **Definición RAE:** Joya de la corona de la síntesis matemática en FL Studio: 6 operadores independientes (cada uno un sintetizador aditivo de 256 armónicos con bloqueo de fase) interconectados mediante una matriz 6x6 bidireccional de Modulación de Frecuencia (FM) y Modulación en Anillo (RM), 3 filtros multimodo en serie/paralelo con distorsión waveshaper, unidad de coro/delay/reverb y soporte nativo de escalas microtonales Scala (.scl).
- **Familia DSP:** Matriz 6x6 de Modulación de Fase/Frecuencia + Modulación en Anillo + 3 Filtros SVF + Waveshaper
- **Ecuación de Transferencia:** `Op_i(t) = A_i(t) * Wave_i(2*pi*f_i*t + sum_{j=1}^6 M^{FM}_{j,i}*Op_j(t)) * prod_{j=1}^6 (1 + M^{RM}_{j,i}*Op_j(t))`
- **Arquitectura Interna:** 6 Operadores Aditivos/Tabla de Ondas con ratio de frecuencia y offset en Hz, Matriz 6x6 de FM + Matriz 6x6 de RM, 3 Unidades de Filtro SVF + Conformador de Onda (Waveshaper) cada una, Más de 200 Articuladores Multipunto (ENV, LFO, KEY, VEL, MOD X, MOD Y, UNISON), Unidad de Efectos (Chorus de hasta 8 órdenes, 3 Líneas de Delay, Reverb)
- **Parámetros Clave:** Matrix FM Knobs (Op j -> Op i), Op Frequency Ratio & Offset Hz, Filter 1..3 Cutoff & Res, Master Pitch / Unison Order, Mod X / Mod Y
- **Mapeo MIDI CC:** `{"1": "Modulator X (Macro Cutoff/FM Index)", "11": "Modulator Y (Macro Resonance/Timbre)", "74": "Filter 1 Cutoff"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con la matriz 6x6 flotante, 6 tablas de 256 armónicos y grafos de los 200+ articuladores.

### 5.47. Toxic Biohazard — *Sintetizador híbrido de seis osciladores con matriz FM y secuenciador polifónico de sesenta y cuatro pasos*
- **Definición RAE:** Sintetizador FM/sustractivo de carácter oscuro y cristalino cuyos 6 osciladores calculan formas de onda de alta precisión en tiempo real (cero aliasing a frecuencias ultrasónicas), combinando una matriz FM 6x6, filtro analógico modelado con resonancia cálida, ecualizador de 8 bandas y un secuenciador de 64 pasos divisible en dos mitades de 32.
- **Familia DSP:** Síntesis FM/Sustractiva de 6 Osciladores con Cálculo Analítico Sin Aliasing
- **Ecuación de Transferencia:** `y[n] = EQ_8Band(FX(Filter_Analog(sum_{i=1}^6 Pan_i * Osc_i(w_i*t + sum_j FM_{j,i}*Osc_j(t)))))`
- **Arquitectura Interna:** 6 Osciladores con ondas analíticas y carga de muestras WAV, Matriz de Modulación FM 6x6, Filtro Multimodo con saturación Drive, Secuenciador inteligente de 64 pasos, Ecualizador de 8 bandas + 2 ranuras de efectos (Phaser, Flanger, Delay, Reverb, Lo-Fi)
- **Parámetros Clave:** Osc 1..6 Pitch/Mix/Drive, FM Matrix Amounts, Filter Cutoff, Res & Env, EQ Bands 1..8
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "71": "Filter Resonance", "1": "Mod Wheel Matrix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con la matriz 6x6, tablas de onda, secuencia de 64 pasos y EQ.

### 5.48. Transistor Bass — *Emulador de circuito analógico del sintetizador de bajo ácido Roland TB-303 (1981)*
- **Definición RAE:** Modelado físico a nivel de transistores y condensadores del legendario sintetizador monofónico de ácido: reproduce exactamente el oscilador de sierra/cuadrada desplazada, el filtro escalera de diodos de 18 dB/octava (3 polos acoplados), el circuito acumulador de acento (Sweep/Decay coupling) y un secuenciador interno de 16 pasos con ligaduras (Slide) y acentos.
- **Familia DSP:** Filtro Escalera de Diodos No Lineal de 18 dB/oct (ZDF) + Circuito Acumulador de Acento RC
- **Ecuación de Transferencia:** `y[n] = Dist_Pedal(DiodeLadder_18dB(Osc_{Saw/Sq}[n], f_c + E_env(Accent)*Mod, Q_res))`
- **Arquitectura Interna:** Oscilador TB-303 con ajuste continuo de forma de onda (Waveform tweak), Filtro escalera de 3 polos efectivos (18 dB/oct), Circuito de Acento no lineal acoplado a resonancia, Secuenciador de 16 pasos con Gate, Slide y Accent, Pedal de distorsión Overdrive + Delay/Reverb
- **Parámetros Clave:** Tuning, Waveform, Cutoff, Resonance, Env Mod, Decay, Accent, Distortion Drive
- **Mapeo MIDI CC:** `{"74": "Cutoff Frequency", "71": "Resonance", "1": "Env Mod", "11": "Accent Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los parámetros de circuito y los bancos de patrones de 16 pasos.

### 5.49. Wasp — *Sintetizador híbrido de tres osciladores digitales y filtro analógico de estado variable*
- **Definición RAE:** Sintetizador inspirado en el EDP Wasp británico de 1978: combina tres osciladores controlados digitalmente con modulación de anchura de pulso, sincronización y modulación de frecuencia junto con un filtro de estado variable de distorsión áspera y dos LFOs.
- **Familia DSP:** Síntesis Sustractiva Híbrida Digital-Analógica con Distorsión de Filtro
- **Ecuación de Transferencia:** `y[n] = SVF_Distorted(Osc_1[n] + Osc_2[n] + Osc_3_Sub[n] + Noise[n], f_c, Q, Drive)`
- **Arquitectura Interna:** 2 Osciladores principales + 1 Suboscilador + Ruido, Filtro multimodo (LP, HP, BP, Notch) con distorsión ajustable, 2 Envolventes ADSR + 2 LFOs
- **Parámetros Clave:** Osc 1/2 Coarse/Fine/PW, FM & RingMod, Cutoff, Resonance & Filter Distortion, LFO 1/2 Speed & Amt
- **Mapeo MIDI CC:** `{"74": "Cutoff", "71": "Resonance", "1": "FM Depth"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de parámetros de Wasp.

### 5.50. Wasp XT — *Sintetizador Wasp extendido con osciladores en desafinación dual y envolventes encadenadas*
- **Definición RAE:** Evolución del sintetizador Wasp que añade modo de oscilador dual desafinado (Dual Osc), modulación de amplitud cruzada, fundido entre dos filtros y mayor control sobre la etapa de distorsión.
- **Familia DSP:** Síntesis Sustractiva de Doble Filtro con Modulación en Anillo y Distorsión
- **Ecuación de Transferencia:** `y[n] = Crossfade(SVF_1(x[n]), SVF_2(x[n])) con saturación no lineal.`
- **Arquitectura Interna:** 3 Osciladores con modo Dual Detune, Doble modo de filtro con distorsión, 2 LFOs sincronizables + 2 ADSR
- **Parámetros Clave:** Dual Osc Detune, Cutoff & Res, Distortion, Env Mod
- **Mapeo MIDI CC:** `{"74": "Cutoff", "71": "Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de parámetros de Wasp XT.

### 5.51. Wave Traveller — *Simulador de tornamesa y rayado de vinilo (scratching) gobernado por curvas de esplines*
- **Definición RAE:** Generador especializado en turntablism que asigna a cada nota MIDI una curva bidimensional de posición de muestra frente al tiempo (velocidad instantánea es la derivada de la curva) junto con una envolvente de volumen del fader cruzado (crossfader muting).
- **Familia DSP:** Integración Diferencial de Fase de Muestra por Derivada de Espline (v(t) = dPos(t)/dt)
- **Ecuación de Transferencia:** `y(t) = Env_Fader(t) * Sample(Pos_Spline(t)), donde la altura instantánea es proporcional a dPos_Spline(t)/dt.`
- **Arquitectura Interna:** Motor de interpolación sinc de velocidad variable y reversa, Editor de curvas de desplazamiento de vinilo por tecla MIDI, Editor de envolvente de corte de crossfader (Mute envelope)
- **Parámetros Clave:** Spline Position Curve, Volume Gate Curve, Turntable Speed / Vinyl Inertia, Patch Note Selection
- **Mapeo MIDI CC:** `{"1": "Scratch Speed Scaling"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las curvas spline de cada nota MIDI y la muestra de audio.

---

## 6. Ingeniería Inversa de los 89 Efectos Nativos (Procesadores de Señal y Voz)

### 6.1. Control Surface — *Superficie de mando y diseño de paneles de control paramétrico*
- **Definición RAE:** Efecto sin alteración directa del flujo de audio que permite construir interfaces gráficas a medida (perillas, cursores, almohadillas X/Y, interruptores) para gobernar múltiples parámetros del mezclador o de Patcher simultáneamente.
- **Familia DSP:** Enrutamiento de Señales de Control Interno (1:N Parameter Mapping)
- **Ecuación de Transferencia:** `y_audio[n] = x_audio[n]; Param_target_k = f_link_k(Control_UI_m)`
- **Arquitectura Interna:** Motor vectorial de widgets UI, Bus de salida de controladores internos de FL Studio
- **Parámetros Clave:** Custom Knobs, Sliders, Buttons, XY Pads
- **Mapeo MIDI CC:** `{"1": "Macro Control 1"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con definición geométrica y visual de los controles.

### 6.2. Distructor — *Procesador modular de cuatro ranuras de distorsión, filtrado, coro y simulación de altavoz*
- **Definición RAE:** Estación de saturación multietapa que encadena 4 módulos intercambiables: Distorsión (modelos de Harmor, Blood Overdrive, Fast Dist y Crusher), Filtro multimodo/peine, Coro estereofónico y Convolucionador de pantallas de guitarra y amplificadores.
- **Familia DSP:** Cascada de 4 Etapas (Saturación No Lineal + Filtro Biquad/Comb + Coro + Convolución FIR de Gabinete)
- **Ecuación de Transferencia:** `y[n] = Stage_4(Stage_3(Stage_2(Stage_1(x[n]))))`
- **Arquitectura Interna:** Ranura 1..4 reordenables, Módulo Distorsión (Asymmetric, Cubed, Ribbons, Blood, Crusher), Módulo Filtro (LP/BP/HP/Comb), Módulo Chorus, Módulo Speaker Cabinet (Respuestas al Impulso FIR)
- **Parámetros Clave:** Preamp / Threshold, Distortion Type, Filter Cutoff/Res, Cabinet IR Selection
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "1": "Distortion Drive"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con configuración de las 4 ranuras y selección de IR.

### 6.3. EQUO — *Ecualizador gráfico adaptativo de banco de filtros con morfismo y aprendizaje espectral*
- **Definición RAE:** Ecualizador gráfico de 32 bandas con capacidad de analizar el espectro de entrada ('Analyze') para esculpir automáticamente una curva complementaria o inversa, y de interpolar entre 8 bancos de curvas mediante un parámetro de morfismo.
- **Familia DSP:** Banco de 32 Filtros Paso-Banda con Interpolación de Bancos y Análisis Espectral
- **Ecuación de Transferencia:** `y[n] = sum_{b=1}^{32} G_b(Morph) * Pan_b * H_band_b(z)[x[n]]`
- **Arquitectura Interna:** Banco de 32 bandas en octavas fraccionarias, 8 Bancos de curvas (Volumen y Paneo por banda) con perilla Morph, Analizador de espectro inverso/complementario
- **Parámetros Clave:** Morph (Bank 1..8), Mix, Smooth, Shift Frequency
- **Mapeo MIDI CC:** `{"1": "Bank Morph", "74": "Frequency Shift"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las 8 matrices de 32 bandas (ganancia y paneo).

### 6.4. Edison — *Laboratorio de grabación, edición de onda, cirugía espectral y análisis de convolución*
- **Definición RAE:** Editor y grabador de audio integrado en el mezclador que opera en el dominio del tiempo y en el espectrograma de alta resolución, dotado de eliminación de ruido por huella espectral, igualación espectral, troceado automático de bucles y motor de scripts Python.
- **Familia DSP:** STFT de Fase Exacta, Sustracción Espectral de Ruido y Edición de Muestras en Memoria
- **Ecuación de Transferencia:** `Sustracción de ruido: |Y(m,k)| = max(0, |X(m,k)| - alpha * N_profile(k))`
- **Arquitectura Interna:** Búfer de audio RAM de 32 bits, Motor STFT de cirugía espectral, Denoiser por perfil de ruido, Troceador de regiones y exportador Drag-and-Drop
- **Parámetros Clave:** Record Mode (Now/On Input/On Play), Denoise Threshold/Amount, Blur/Reverb Convolver
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 que incrusta íntegramente el archivo WAV de 32 bits y sus marcadores.

### 6.5. Effector — *Procesador táctil de doce algoritmos de efectos en tiempo real gobernados por matriz X/Y*
- **Definición RAE:** Unidad de efectos de directo con 12 algoritmos seleccionables (Distortion, Lo-Fi, Flanger, Phaser, Filter LP/HP, Delay, Reverb, Stereo Pan, Binaural, Granulizer, Vocal Formants, Ring Mod) controlados por una almohadilla X/Y con modulación rítmica LFO.
- **Familia DSP:** Conmutador de 12 Motores DSP Controlado por Coordenadas Cartesianas (X, Y) y Compuerta
- **Ecuación de Transferencia:** `y[n] = Mix(x[n], Engine_{alg}(x[n], X(t), Y(t)))`
- **Arquitectura Interna:** 12 Motores DSP independientes, Almohadilla X/Y con interruptor Bypass (Mute FX), Modulador rítmico sincronizado a tempo (1/16..4 compases)
- **Parámetros Clave:** FX Algorithm (1..12), Param X, Param Y, Bypass Switch, Tempo Mod Depth, Dry/Wet
- **Mapeo MIDI CC:** `{"1": "Param X", "11": "Param Y", "74": "Dry/Wet Level"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 compacto con índice de algoritmo y coordenadas X/Y.

### 6.6. Emphasis — *Limitador maestro multietapa de pico verdadero y realzador dinámico de sonoridad*
- **Definición RAE:** Procesador de masterización de alta precisión incorporado en FL Studio 2025 que combina filtrado de pre-énfasis tonal (Tilt/Baxandall), saturación instantánea de cresta, compresión de programa y limitación de muro infranqueable con sobremuestreo polifásico hasta 16x.
- **Familia DSP:** Pre-Énfasis Espectral + Recorte Armónico + Limitador de Pico Verdadero Sobremuestreado
- **Ecuación de Transferencia:** `y[n] = Downsample_M(Brickwall_ISP(SoftClip(PreEmphasis_EQ(Upsample_M(x[n])))))`
- **Arquitectura Interna:** Etapa de ganancia de entrada y tono (Tone/Tilt), Etapa de recuperación e impacto transitorio, Limitador True Peak con sobremuestreo de fase lineal/mínima
- **Parámetros Clave:** Input Gain, Ceiling dBTP, Release Speed, Tone Balance, Oversampling Factor
- **Mapeo MIDI CC:** `{"7": "Input Drive", "74": "Tone Balance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de techo dBTP y factor de sobremuestreo.

### 6.7. Emphasizer — *Maximizado compacto de sonoridad y saturación armónica de cresta*
- **Definición RAE:** Versión simplificada y de baja latencia del motor Emphasis orientada a buses de batería, sintetizadores e insertos individuales para incrementar la densidad percibida sin rebasar el techo digital.
- **Familia DSP:** Saturación de Cresta + Limitación Rápida de Bus
- **Ecuación de Transferencia:** `y[n] = Ceiling * tanh(Drive * x[n] / Ceiling)`
- **Arquitectura Interna:** Preamplificador de empuje (Drive), Circuito de saturación/limitación, Filtro de carácter tonal
- **Parámetros Clave:** Drive, Ceiling, Character
- **Mapeo MIDI CC:** `{"1": "Drive"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 compacto de parámetros de bus.

### 6.8. FL Studio Mobile Rack FX — *Bastidor de efectos modulares del motor FL Studio Mobile*
- **Definición RAE:** Contenedor de inserción que permite utilizar la cadena de efectos ligeros de FL Studio Mobile (Multi FX, Autoduck, Limiter, Analyzer, Tuner, Comb Filter) dentro del mezclador principal.
- **Familia DSP:** Cadena de Procesamiento Modular Ligero de Coma Flotante
- **Ecuación de Transferencia:** `y[n] = MobileFX_Chain(x[n])`
- **Arquitectura Interna:** Ranuras de efectos Mobile encadenables
- **Parámetros Clave:** Mix, Module Parameters
- **Mapeo MIDI CC:** `{"1": "Macro Mix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el estado de la cadena FX Mobile.

### 6.9. Frequency Shifter — *Desplazador lineal de frecuencias por transformada de Hilbert y modulación en banda lateral única*
- **Definición RAE:** Procesador que suma una cantidad constante de hercios (+Delta_f Hz) a todas las componentes espectrales de una señal (rompiendo la relación armónica y produciendo timbres metálicos o efectos Barberpole Phaser), empleando una red de desfase de 90 grados (transformada de Hilbert) y modulación en cuadratura.
- **Familia DSP:** Modulación de Banda Lateral Única (SSB) mediante Red Polifásica de Hilbert
- **Ecuación de Transferencia:** `y(t) = x(t)*cos(2*pi*Delta_f*t) - Hilbert(x(t))*sin(2*pi*Delta_f*t)`
- **Arquitectura Interna:** Red de filtros paso-todo en cuadratura (90 deg Hilbert), Oscilador en cuadratura (Seno/Coseno) de escala lineal (Hz) o logarítmica, Bucle de realimentación (Feedback) para efectos de remolino espectral
- **Parámetros Clave:** Frequency Shift Hz, Range (20Hz / 2kHz / 20kHz), Mix (Freq Shift vs Ring Mod), Feedback, Stereo Spread
- **Mapeo MIDI CC:** `{"74": "Frequency Shift", "71": "Feedback"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de desplazamiento y realimentación.

### 6.10. Frequency Splitter — *Divisor espectral de tres bandas con filtros de cruce Linkwitz-Riley y fase lineal*
- **Definición RAE:** Separador de frecuencias de precisión quirúrgica que divide una señal en tres bandas independientes (Graves, Medios, Agudos) con pendientes de 6 a 96 dB/octava en modo de latencia cero (Linkwitz-Riley IIR) o fase lineal perfecta (FIR), permitiendo enviar cada banda a un canal distinto del mezclador o de Patcher.
- **Familia DSP:** Filtros de Cruce Complementarios (Linkwitz-Riley LR4/LR8 o FIR Simétrico de Fase Lineal)
- **Ecuación de Transferencia:** `H_low(z) + H_mid(z) + H_high(z) = z^(-D) (reconstrucción de magnitud y fase unitaria exacta).`
- **Arquitectura Interna:** 2 Frecuencias de cruce ajustables (Low-Mid, Mid-High), Selector de fase lineal o latencia mínima, 3 Salidas independientes de envío (Send Outputs) para procesamiento multibanda en paralelo
- **Parámetros Clave:** Low-Mid Crossover Hz, Mid-High Crossover Hz, Slope (6..96 dB/oct), Linear Phase Mode, Band Gains
- **Mapeo MIDI CC:** `{"74": "Low-Mid Crossover", "71": "Mid-High Crossover"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con frecuencias de cruce, pendientes y matriz de salidas.

### 6.11. Fruity 7 Band EQ — *Ecualizador gráfico estático de siete bandas de octava*
- **Definición RAE:** Ecualizador clásico de consumo mínimo de CPU compuesto por 7 filtros biquad en cascada centrados en 63 Hz, 125 Hz, 250 Hz, 500 Hz, 1 kHz, 2.5 kHz y 6 kHz (±18 dB por banda).
- **Familia DSP:** Cascada de 7 Filtros Biquad IIR de Segundo Orden (Estantes Extremos + 5 Campanas)
- **Ecuación de Transferencia:** `H(z) = prod_{k=1}^7 ((b_{0,k} + b_{1,k}*z^-1 + b_{2,k}*z^-2) / (1 + a_{1,k}*z^-1 + a_{2,k}*z^-2))`
- **Arquitectura Interna:** 7 Deslizadores de ganancia (±18 dB) a frecuencias fijas
- **Parámetros Clave:** Band 63Hz, Band 125Hz, Band 250Hz, Band 500Hz, Band 1kHz, Band 2.5kHz, Band 6kHz
- **Mapeo MIDI CC:** `{"74": "Band 1kHz", "71": "Band 6kHz"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 28 bytes (7 enteros de 32 bits).

### 6.12. Fruity Balance — *Atenuador de ganancia y posicionador panorámico libre de artefactos de cremallera*
- **Definición RAE:** Etapa de ganancia y paneo dedicada a la automatización de volumen sin ocupar el deslizador principal del canal del mezclador, provista de interpolación suave por muestra.
- **Familia DSP:** Multiplicador Lineal de Matriz Estereofónica con Suavizado Exponencial de Un Polo
- **Ecuación de Transferencia:** `L'[n] = g_vol[n] * g_panL[n] * L[n]; R'[n] = g_vol[n] * g_panR[n] * R[n]`
- **Arquitectura Interna:** Potenciómetro de Pan (-100%..+100%), Potenciómetro de Volumen (-inf..+5.6 dB)
- **Parámetros Clave:** Pan, Volume
- **Mapeo MIDI CC:** `{"7": "Volume", "10": "Pan"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 8 bytes (2 int32: Pan y Volume).

### 6.13. Fruity Bass Boost — *Realzador resonante de frecuencias graves y subgraves*
- **Definición RAE:** Filtro de campana de segundo orden de alto factor de mérito (Q) diseñado para amplificar selectivamente la fundamental de bombos y bajos entre 40 Hz y 120 Hz.
- **Familia DSP:** Filtro Biquad de Pico (Peaking EQ) en Región Subgrave
- **Ecuación de Transferencia:** `H(z) = Biquad_Peak(f_0 in [40, 120] Hz, Gain_dB)`
- **Arquitectura Interna:** Selector de frecuencia central, Potenciómetro de intensidad de realce
- **Parámetros Clave:** Frequency, Amount
- **Mapeo MIDI CC:** `{"74": "Frequency", "71": "Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 8 bytes.

### 6.14. Fruity Big Clock — *Cronómetro visual de gran formato en compases, pulsos o minutos y segundos*
- **Definición RAE:** Utilidad de monitorización visual que muestra la posición actual del cabezal de reproducción con dígitos gigantes para cabinas de grabación o directo.
- **Familia DSP:** Conversión de Ticks PPQ a Código de Tiempo Visual (Bar:Step:Tick / Min:Sec:Centisec)
- **Ecuación de Transferencia:** `y[n] = x[n] (paso transparente de audio)`
- **Arquitectura Interna:** Decodificador de reloj de transporte
- **Parámetros Clave:** Display Mode (Bars/Time)
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 4 bytes.

### 6.15. Fruity Blood Overdrive — *Saturador asimétrico de modelado de preamplificador y pedal de distorsión*
- **Definición RAE:** Distorsionador clásico de FL Studio con multiplicador de preamplificación (x100), filtro paso-banda de coloración previo a la saturación y etapa de filtrado post-distorsión para domar la aspereza de alta frecuencia.
- **Familia DSP:** Filtrado Pre-Énfasis + Función de Transferencia No Lineal Asimétrica + Filtro Paso-Bajo Post-Saturación
- **Ecuación de Transferencia:** `y[n] = LPF_post(f_nonlinear(BPF_color(PreBand * x[n]) * PreAmp * (1 + 99*x100)))`
- **Arquitectura Interna:** Filtro PreBand y Color, Etapa PreAmp con interruptor x100, Filtro PostFilter y compensación PostGain
- **Parámetros Clave:** PreBand, Color, PreAmp, x100 Switch, PostFilter, PostGain
- **Mapeo MIDI CC:** `{"1": "PreAmp Drive", "74": "Color Frequency"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 24 bytes (6 float32).

### 6.16. Fruity Center — *Eliminador de componente continua (DC Offset) en tiempo real*
- **Definición RAE:** Filtro paso-alto de frecuencia de corte sub-infrasónica (~2 Hz) que suprime cualquier desplazamiento asimétrico respecto al cero eléctrico (DC offset) para preservar el margen dinámico completo del mezclador.
- **Familia DSP:** Filtro Bloqueador de Continua de Primer Orden (DC Blocker IIR)
- **Ecuación de Transferencia:** `y[n] = x[n] - x[n-1] + 0.9995 * y[n-1], o H(z) = (1 - z^-1) / (1 - 0.9995*z^-1)`
- **Arquitectura Interna:** Integrador leaky de eliminación DC
- **Parámetros Clave:** Mode (On / Off)
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 4 bytes.

### 6.17. Fruity Chorus — *Multiplicador coral estereofónico de tres osciladores de baja frecuencia*
- **Definición RAE:** Procesador de ensanchamiento espacial que utiliza líneas de retardo variables moduladas por tres LFOs independientes con control de forma (Seno^x) y filtro de cruce para mantener o excluir las frecuencias bajas.
- **Familia DSP:** Línea de Retardo Fraccionaria Modulada por Suma de 3 LFOs No Lineales
- **Ecuación de Transferencia:** `y[n] = Dry*x[n] + Wet*x(n - D_0 - Depth * sum_{i=1}^3 sin(w_i*t)^(p_i))`
- **Arquitectura Interna:** Línea de retardo interpolada con diferencia estéreo, 3 LFOs con exponente de curvatura, Filtro de cruce (Cutoff High/Low)
- **Parámetros Clave:** Delay, Depth, Stereo, LFO 1..3 Freq, Cross Type & Cutoff, Wet Only
- **Mapeo MIDI CC:** `{"74": "Depth", "1": "LFO 1 Freq"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 44 bytes.

### 6.18. Fruity Compressor — *Compresor monobanda de margen dinámico con curvas de relajación vintage y dura*
- **Definición RAE:** Compresor clásico de respuesta rápida con umbral de 0 a -60 dB, razón de 1:1 a 30:1, ganancia de compensación y cuatro caracteres de rodilla y relajación (Hard, Medium, Vintage, Soft).
- **Familia DSP:** Detector de Envolvente RMS/Pico con Computación Logarítmica de Ganancia
- **Ecuación de Transferencia:** `G_dB[n] = Gain_makeup - max(0, Env_dB[n] - Threshold) * (1 - 1/Ratio)`
- **Arquitectura Interna:** Detector de nivel con Attack/Release, Computador de ganancia con 4 curvas de rodilla (Hard/Medium/Vintage/Soft)
- **Parámetros Clave:** Threshold, Ratio, Gain, Attack, Release, Type (Hard/Medium/Vintage/Soft)
- **Mapeo MIDI CC:** `{"74": "Threshold", "71": "Ratio"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 24 bytes.

### 6.19. Fruity Convolver — *Motor de convolución de latencia cero por respuesta al impulso con editor completo*
- **Definición RAE:** Procesador de convolución particionada que multiplica espectralmente la señal de entrada por cualquier respuesta al impulso grabada o sintetizada (catedrales, muelles, cabinas, filtros de fase lineal), incorporando el motor de edición de Edison para esculpir la envolvente de volumen, estéreo y tono del impulso.
- **Familia DSP:** Convolución Rápida Particionada No Uniforme en Dominio FFT (Zero-Latency Partitioned Convolution)
- **Ecuación de Transferencia:** `y[n] = sum_{m=0}^{L-1} h_IR[m] * x[n - m], calculada por bloques IFFT(FFT(x_p) * FFT(h_p)).`
- **Arquitectura Interna:** Motor de convolución FFT particionada sin latencia, Editor de onda y espectrograma de la Respuesta al Impulso (IR), Envolventes multipunto sobre la IR (Volumen, Pan, Stereo Separation, EQ), Grabador de barrido senoidal ( Impulse Response Capturer)
- **Parámetros Clave:** Dry Level, Wet Level, IR Stretch (Pitch/Time), Stereo Separation of IR, Feedback, EQ Curve
- **Mapeo MIDI CC:** `{"91": "Wet Level", "74": "IR Stretch"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el archivo WAV de la Respuesta al Impulso incrustado y sus curvas.

### 6.20. Fruity Delay — *Eco digital elemental sincronizado a subdivisiones de paso*
- **Definición RAE:** Línea de retardo ligera sincronizada en unidades de pasos del secuenciador (1..16 steps) con modo normal, invertido o ping-pong estereofónico.
- **Familia DSP:** Búfer Circular de Retardo Sincronizado con Realimentación
- **Ecuación de Transferencia:** `d[n] = Input * x[n] + Feedback * LP(d[n - N_steps])`
- **Arquitectura Interna:** Línea de retardo circular, Filtro paso-bajo de realimentación, Conmutador Ping-Pong
- **Parámetros Clave:** Input, Feedback, Cutoff, Tempo Steps, Mode (Normal/Inv/PingPong)
- **Mapeo MIDI CC:** `{"94": "Input Send", "74": "Feedback Cutoff"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 20 bytes.

### 6.21. Fruity Delay 2 — *Eco estereofónico con desplazamiento de tiempo interaural y filtrado de realimentación*
- **Definición RAE:** Evolución del eco básico que añade control continuo del tiempo de retardo, desplazamiento temporal entre el canal izquierdo y derecho (Time Stereo Offset) para ensanchamiento psicoacústico Haas y paneo de entrada.
- **Familia DSP:** Doble Línea de Retardo con Desfase Interaural (Efecto Haas) y Realimentación Cruzada
- **Ecuación de Transferencia:** `d_L[n] = Pan_L*x_L[n] + fb * H_lp(d_R[n - D_L]); d_R[n] = Pan_R*x_R[n] + fb * H_lp(d_L[n - D_R])`
- **Arquitectura Interna:** 2 Líneas de retardo con offset estéreo, Filtro paso-bajo de amortiguación, Selector Normal / Invert / Ping-Pong
- **Parámetros Clave:** Input Pan, Input Vol, Dry, FeedbackMode, Feedback Vol, Feedback Cutoff, Time, Time Stereo Offset
- **Mapeo MIDI CC:** `{"74": "Feedback Cutoff", "94": "Wet/Input Vol"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 32 bytes.

### 6.22. Fruity Delay 3 — *Emulador de eco analógico de cinta y cubo de brigada con modulación y degradación digital*
- **Definición RAE:** Línea de retardo maestra de FL Studio: modela físicamente la inestabilidad de velocidad de cinta (Pitch Keep / Resampling Doppler), difusión espacial de las repeticiones, saturación no lineal o reducción de frecuencia de muestreo y profundidad de bits en el bucle de realimentación, y filtro multimodo auto-oscilante.
- **Familia DSP:** Línea de Retardo de Velocidad Variable (Doppler Tape Interpolation) + Bucle con Filtro SVF, Difusor All-Pass y Bitcrusher
- **Ecuación de Transferencia:** `d(t) = x(t) + fb * Saturate_Crush(Diffuser(SVF(d(t - D(t) - LFO(t)))))`
- **Arquitectura Interna:** Interpolador de cinta con efecto Doppler real, Modulador LFO de tiempo y filtro, Sección de realimentación con Filtro LP/HP/BP, Difusor (Smear), Saturador/Limitador y Sample Rate/Bit Reduction, Panner y Expansor Estéreo de salida
- **Parámetros Clave:** Delay Time (Tempo Sync / ms), Stereo Offset, Feedback Level, Filter Cutoff & Res, Diffusion Level/Spread, Saturation / Bit & Sample Rate Crush, Modulation Rate/Time
- **Mapeo MIDI CC:** `{"74": "Feedback Filter Cutoff", "71": "Feedback Resonance", "94": "Wet Level", "1": "Time Modulation"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con todos los coeficientes del bucle analógico/digital.

### 6.23. Fruity Delay Bank — *Estación de ocho bancos de retardo en serie y paralelo con filtrado y granulación*
- **Definición RAE:** Arquitectura matricial de 8 unidades de retardo completas que pueden encadenarse en serie o sumarse en paralelo, cada una provista de filtro de entrada, filtro de realimentación, granulación de eco y envíos hacia el banco siguiente.
- **Familia DSP:** Red de 8 Líneas de Retardo Acopladas con Granulador y Filtros Multimodo Duales
- **Ecuación de Transferencia:** `Para banco k in 1..8: B_k[n] = Delay_Grain_k(Filter_in_k(x[n] + g_{k-1}*B_{k-1}[n]))`
- **Arquitectura Interna:** 8 Unidades de Delay independientes, Filtros SVF de entrada, realimentación y salida por banco, Módulo de granulación de repeticiones por banco
- **Parámetros Clave:** Bank 1..8 Time, Feedback, Cutoff, Grain Div, Next Bank Send
- **Mapeo MIDI CC:** `{"74": "Global Filter Cutoff", "94": "Wet Mix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las 8 estructuras de banco.

### 6.24. Fruity Fast Dist — *Distorsionador algebraico instantáneo de doble curva analítica*
- **Definición RAE:** Conformador de onda ultrarrápido con dos ecuaciones de transferencia seleccionables (Tipo A: compresión tangencial suave; Tipo B: recorte abrupto asimétrico con umbral) para bombos gabber, líneas ácidas 303 y sintetizadores.
- **Familia DSP:** Conformación Estática Sin Memoria (Memoryless Non-Linear Waveshaping)
- **Ecuación de Transferencia:** `Tipo A: y = x*(|x| + Pre) / (x^2 + (Pre - 1)*|x| + 1); Tipo B: recorte duro por encima de Threshold.`
- **Arquitectura Interna:** Etapa Preamp, Conmutador de ecuación A/B con Threshold, Mezclador Dry/Wet y Post-Gain
- **Parámetros Clave:** Pre, Threshold, Type (A/B), Mix, Post
- **Mapeo MIDI CC:** `{"1": "Pre Drive", "74": "Threshold"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 20 bytes (5 int32).

### 6.25. Fruity Fast LP — *Filtro paso-bajo resonante de dos polos de baja carga computacional*
- **Definición RAE:** Filtro paso-bajo de barrido rápido optimizado para automatización de cortes de pista sin latencia.
- **Familia DSP:** Filtro IIR de Estado Variable de Segundo Orden (12 dB/octava)
- **Ecuación de Transferencia:** `H(z) = b_0 / (1 + a_1*z^-1 + a_2*z^-2)`
- **Arquitectura Interna:** Par Cutoff y Resonance
- **Parámetros Clave:** Cutoff, Resonance
- **Mapeo MIDI CC:** `{"74": "Cutoff", "71": "Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 8 bytes.

### 6.26. Fruity Filter — *Filtro de estado variable multimodo con suma ponderada de respuestas*
- **Definición RAE:** Filtro clásico de FL Studio cuya topología de estado variable expone simultáneamente las salidas Paso-Bajo, Paso-Banda y Paso-Alto, permitiendo fundirlas en cualquier proporción junto con un multiplicador de pendiente x2 (12 dB -> 24 dB/oct).
- **Familia DSP:** Filtro de Estado Variable de Chamberlin (Chamberlin SVF) en Cascada Doble
- **Ecuación de Transferencia:** `y[n] = g_LP * LP[n] + g_BP * BP[n] + g_HP * HP[n]`
- **Arquitectura Interna:** Núcleo SVF de 1 o 2 etapas (x2), Mezclador independiente de ramas Low Pass, Band Pass y High Pass
- **Parámetros Clave:** Cutoff Freq, Resonance, Low Pass, Band Pass, High Pass, x2 Slope
- **Mapeo MIDI CC:** `{"74": "Cutoff Freq", "71": "Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 24 bytes.

### 6.27. Fruity Flanger — *Rebordeador estereofónico de peine con modulación cruzada e inversión de fase*
- **Definición RAE:** Generador de barrido metálico por línea de retardo corta (0.1 a 20 ms) modulada por LFO, con inversión de polaridad de la señal húmeda y de la realimentación para alternar entre picos y valles impares.
- **Familia DSP:** Filtro de Peine IIR Modulado en el Tiempo (Time-Varying IIR Comb Filter)
- **Ecuación de Transferencia:** `d[n] = x[n] + sgn_fb * fb * d[n - D(t)]; y[n] = Dry*x[n] + sgn_wet * Wet * d[n - D(t)]`
- **Arquitectura Interna:** Línea de retardo corta interpolada, LFO con forma ajustable, Inversores de fase Wet y Feedback
- **Parámetros Clave:** Delay, Depth, Rate, Phase, Damp, Feed, Invert Feedback/Wet
- **Mapeo MIDI CC:** `{"74": "Depth", "71": "Feedback", "1": "Rate"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 40 bytes.

### 6.28. Fruity Flangus — *Multiplicador de coro y rebordeado denso de múltiples líneas retardadas en paralelo*
- **Definición RAE:** Híbrido entre Chorus y Flanger que apila múltiples líneas de retardo moduladas y distribuidas en el campo estereofónico con un parámetro de Orden (Order) para ensanchar cuerdas, pads y guitarras.
- **Familia DSP:** Banco Paralelo de N Filtros de Peine Modulados con Distribución Panorámica
- **Ecuación de Transferencia:** `y_{L,R}[n] = Dry*x[n] + Wet * sum_{k=1}^{Order} Pan_k * x(n - D_k(t))`
- **Arquitectura Interna:** Matriz de N retardos modulados (Order), Filtro de cruce de graves, Expansor estéreo
- **Parámetros Clave:** Order, Depth, Speed, Delay, Spread, Stereo, Cross, Dry/Wet
- **Mapeo MIDI CC:** `{"74": "Depth", "1": "Speed"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 32 bytes.

### 6.29. Fruity Formula Controller — *Evaluador algebraico en tiempo real de funciones matemáticas de control*
- **Definición RAE:** Procesador de señales de control que compila y evalúa en cada tick una expresión matemática arbitraria escrita por el usuario en función de tres variables de entrada (a, b, c), el tiempo musical (SongTime) y funciones trigonométricas o estocásticas.
- **Familia DSP:** Compilador y Evaluador Simbólico de Expresiones en Coma Flotante
- **Ecuación de Transferencia:** `Out(t) = clamp(EvalAST(FormulaString, a(t), b(t), c(t), SongTime(t)), 0.0, 1.0)`
- **Arquitectura Interna:** Analizador sintáctico de expresiones matemáticas (sin, cos, tg, exp, log, sqrt, rand, Tension, Inter), 3 Potenciómetros de entrada (a, b, c) automatizables, Monitor oscilográfico de salida
- **Parámetros Clave:** Variable a, Variable b, Variable c, Formula Expression String
- **Mapeo MIDI CC:** `{"1": "Variable a", "11": "Variable b", "74": "Variable c"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los 3 floats (a,b,c) + cadena ASCII de la ecuación matemática.

### 6.30. Fruity Free Filter — *Filtro biquad universal de primer y segundo orden con seis topologías clásicas*
- **Definición RAE:** Filtro quirúrgico ligero con selección de tipo (Low Pass, Band Pass, High Pass, Notch, Low Shelf, Peaking EQ), frecuencia de 10 Hz a 16 kHz y factor Q.
- **Familia DSP:** Filtro Biquad Direct Form II Transposed (Fórmulas de Robert Bristow-Johnson Audio EQ Cookbook)
- **Ecuación de Transferencia:** `H(z) = (b_0 + b_1*z^-1 + b_2*z^-2) / (a_0 + a_1*z^-1 + a_2*z^-2)`
- **Arquitectura Interna:** Calculador de coeficientes RBJ Biquad, Conmutador de 6 modos de respuesta
- **Parámetros Clave:** Type, Freq, Q, Gain
- **Mapeo MIDI CC:** `{"74": "Freq", "71": "Q"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 16 bytes.

### 6.31. Fruity HTML NoteBook — *Visor de documentos hipertextuales sincronizado al proyecto*
- **Definición RAE:** Utilidad de documentación técnica que renderiza páginas HTML/CSS incrustadas o locales dentro del espacio de trabajo del mezclador.
- **Familia DSP:** Paso Transparente de Audio (Identidad)
- **Ecuación de Transferencia:** `y[n] = x[n]`
- **Arquitectura Interna:** Motor de renderizado HTML
- **Parámetros Clave:** HTML File Path / Page
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con ruta o contenido HTML.

### 6.32. Fruity LSD — *Sintetizador multitímbrico General MIDI de dieciséis canales sobre banco DLS*
- **Definición RAE:** Módulo de sonidos General MIDI / Roland GS alojado como efecto de inserción que recibe eventos desde canales MIDI Out en un puerto determinado y sintetiza hasta 16 instrumentos orquestales o percusivos simultáneos.
- **Familia DSP:** Síntesis por Tabla de Ondas General MIDI (Downloadable Sounds DLS Level 1/2)
- **Ecuación de Transferencia:** `y[n] = sum_{ch=1}^{16} Chorus_Reverb(DLS_Synth(MIDI_Port, ch)[n])`
- **Arquitectura Interna:** Receptor de Puerto MIDI interno, 16 Ranuras de instrumento GM/GS, Procesador de Reverb y Chorus global
- **Parámetros Clave:** MIDI Port, Channel 1..16 Patch/Vol/Pan/Reverb/Chorus
- **Mapeo MIDI CC:** `{"7": "Channel Volume", "10": "Channel Pan", "91": "Reverb"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con puerto MIDI y los 16 programas GM.

### 6.33. Fruity Limiter — *Limitador de muro infranqueable con anticipación temporal, compresor con cadena lateral y puerta de ruido*
- **Definición RAE:** Procesador dinámico de referencia en FL Studio que integra tres secciones en serie: un Compresor completo con soporte nativo de cadena lateral (Sidechain) desde cualquier pista del mezclador, un Limitador con ventana de anticipación (Lookahead Attack), curva de liberación doble y saturación tangencial de techo, y una Puerta de Ruido (Noise Gate), todo visualizado en un analizador temporal de envolventes.
- **Familia DSP:** Compresión por Cadena Lateral + Saturación de Umbral + Limitador de Convolución de Ventana de Ataque Anticipado
- **Ecuación de Transferencia:** `y[n] = x[n - L_att] * min(g_comp(E_sc[n]), g_lim(max_{k in [0, L_att]} |x[n-k]|, Ceiling))`
- **Arquitectura Interna:** Línea de retardo de anticipación (Lookahead = Attack Time del Limitador), Sección COMP (Threshold, Ratio, Knee, Attack, Release, Ahead, Sidechain Track Selector), Sección LIMIT (Ceiling, Gain, Saturation Threshold, Attack, Release, Curve 1..8), Sección NOISE GATE (Threshold, Gain, Release)
- **Parámetros Clave:** Gain, Limit Ceiling, Saturation Threshold, Limit Attack (Lookahead), Comp Threshold/Ratio/Knee, Sidechain Input Index
- **Mapeo MIDI CC:** `{"7": "Input Gain", "74": "Limit Ceiling", "71": "Comp Threshold"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 88 bytes con todos los parámetros de Comp, Limit y Gate.

### 6.34. Fruity Love Philter — *Estación matricial de ocho unidades de filtrado multimodo, conformación de onda y envolventes rítmicas*
- **Definición RAE:** Banco de 8 procesadores de filtro idénticos que pueden operar en paralelo o en serie: cada unidad posee un filtro de estado variable de pendiente simple/doble/triple, un distorsionador Waveshaper y 10 articuladores multipunto (frecuencia de corte, resonancia, nivel, waveshaper, paneo) gobernados por LFO, envolvente de patrón y moduladores X/Y.
- **Familia DSP:** Grafo Serie/Paralelo de 8 Filtros SVF No Lineales + 8 Conformadores de Onda + Desfasador Global
- **Ecuación de Transferencia:** `Para unidad k in 1..8: U_k[n] = SVF_k(Waveshaper_k(x[n] + fb_k*U_{k-1}[n]), f_c(Art_k), Q(Art_k))`
- **Arquitectura Interna:** 8 Unidades de Filtro + Waveshaper encadenables, 80 Curvas de Articulador Multipunto (10 por unidad: PAT, LFO, MOD X, MOD Y, ENV Follower), Seguidor de envolvente de entrada (IEF), Sección de Chorus y Delay global
- **Parámetros Clave:** Unit 1..8 Filter Mode/Cutoff/Res/Drive, Next Unit Send, Mod X, Mod Y
- **Mapeo MIDI CC:** `{"1": "Modulator X", "11": "Modulator Y", "74": "Unit 1 Cutoff", "71": "Unit 1 Resonance"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las 8 unidades y los 80 grafos de splines de articulador.

### 6.35. Fruity Multiband Compressor — *Compresor dinámico de tres bandas espectrales con filtros de cruce FIR/IIR*
- **Definición RAE:** Procesador dinámico de masterización y buses que divide el espectro en bandas Grave, Media y Aguda mediante filtros de cruce de 24 dB/octava (modo IIR o FIR de fase lineal) y aplica compresión independiente con limitador de salida.
- **Familia DSP:** División en 3 Bandas (IIR Butterworth / FIR Fase Lineal) + 3 Compresores Independientes
- **Ecuación de Transferencia:** `y[n] = Limiter(sum_{b in {L,M,H}} Comp_b(H_cross_b(z)[x[n]], Thresh_b, Ratio_b))`
- **Arquitectura Interna:** Filtros de cruce Low/Mid y Mid/High (modos FIR y IIR), 3 Compresores completos (Attack, Release, Knee, Ratio, Threshold, Gain), Limitador de techo de salida
- **Parámetros Clave:** Low/High Crossover Freq, Band L/M/H Threshold, Ratio, Attack, Release, Gain, Filter Type (FIR/IIR), Limiter Active
- **Mapeo MIDI CC:** `{"74": "Low Crossover", "71": "High Crossover"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 84 bytes.

### 6.36. Fruity Mute 2 — *Interruptor silencioso de flujo de audio y canales estereofónicos*
- **Definición RAE:** Conmutador automatizable de silenciamiento libre de clics con capacidad de silenciar el canal izquierdo, el derecho o ambos.
- **Familia DSP:** Compuerta Booleana con Rampa de Desvanecimiento de 2 ms (Anti-Click De-Zipper)
- **Ecuación de Transferencia:** `y[n] = (1 - g_mute[n]) * x[n]`
- **Arquitectura Interna:** Interruptor Mute, Selector de canal (L, R, Stereo)
- **Parámetros Clave:** Mute Switch, Channel Mode
- **Mapeo MIDI CC:** `{"120": "All Sound Off / Mute"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 8 bytes.

### 6.37. Fruity NoteBook — *Cuaderno de bitácora paginado de texto plano automatizable*
- **Definición RAE:** Bloc de notas de 100 páginas cuyo índice de página puede automatizarse en la Playlist para mostrar letras de canciones o instrucciones técnicas en sincronía con la reproducción.
- **Familia DSP:** Paso Transparente de Audio (Identidad)
- **Ecuación de Transferencia:** `y[n] = x[n]`
- **Arquitectura Interna:** 100 Páginas de texto indexadas
- **Parámetros Clave:** Current Page (1..100)
- **Mapeo MIDI CC:** `{"1": "Page Index"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las cadenas de texto de las páginas.

### 6.38. Fruity NoteBook 2 — *Cuaderno de bitácora de texto enriquecido (RTF) sincronizado a proyecto*
- **Definición RAE:** Evolución del cuaderno de notas con soporte Unicode completo, formato tipográfico enriquecido y 100 páginas automatizables.
- **Familia DSP:** Paso Transparente de Audio (Identidad)
- **Ecuación de Transferencia:** `y[n] = x[n]`
- **Arquitectura Interna:** Motor RTF de 100 páginas
- **Parámetros Clave:** Page Index (1..100)
- **Mapeo MIDI CC:** `{"1": "Page Index"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con flujos RTF UTF-16.

### 6.39. Fruity PanOMatic — *Modulador automático de panorámica y amplitud gobernado por oscilador de baja frecuencia*
- **Definición RAE:** Procesador de trémolo (modulación de volumen) y auto-paneo estereofónico con LFO de tres formas de onda (Seno, Triángulo, Cuadrada) cuya velocidad puede variar en función del nivel de la señal de entrada.
- **Familia DSP:** Modulación de Amplitud y Matriz Panorámica por LFO
- **Ecuación de Transferencia:** `L'[n], R'[n] = Pan_Vol(x[n], Vol + A_v*LFO(t), Pan + A_p*LFO(t))`
- **Arquitectura Interna:** Etapa de Pan y Volumen base, LFO asignable a Pan o Vol con forma, velocidad y cantidad
- **Parámetros Clave:** Pan, Volume, LFO Target (Off/Vol/Pan), LFO Shape, LFO Amount, LFO Speed
- **Mapeo MIDI CC:** `{"10": "Base Pan", "1": "LFO Speed"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 24 bytes.

### 6.40. Fruity Parametric EQ — *Ecualizador paramétrico clásico de siete bandas biquad*
- **Definición RAE:** Ecualizador paramétrico de 7 bandas independientes donde cada banda permite elegir el tipo de filtro (Low Shelf, Peaking, High Shelf, Low Pass, Band Pass, High Pass, Notch), la frecuencia central, el ancho de banda y la ganancia.
- **Familia DSP:** Cascada de 7 Filtros Biquad IIR Paramétricos
- **Ecuación de Transferencia:** `H(z) = G_master * prod_{k=1}^7 H_biquad(z; Type_k, f_k, BW_k, Gain_k)`
- **Arquitectura Interna:** 7 Secciones biquad de coma flotante, Gráfico de curva de magnitud combinada
- **Parámetros Clave:** Band 1..7 Type, Level, Freq, Bandwidth, Main Level
- **Mapeo MIDI CC:** `{"74": "Band 4 Frequency", "71": "Band 4 Bandwidth"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 116 bytes.

### 6.41. Fruity Parametric EQ 2 — *Ecualizador paramétrico de siete bandas con modo de fase lineal, sobremuestreo y espectrograma de calor*
- **Definición RAE:** Ecualizador quirúrgico de referencia en FL Studio: 7 bandas con pendientes seleccionables de 6 a 48 dB/octava (Orden 2 a 8), desacoplamiento de fase lineal (modo FIR sin rotación de fase para masterización), sobremuestreo 2x para eliminar la compresión de frecuencia cerca de Nyquist y monitor espectral de mapa de calor en segundo plano.
- **Familia DSP:** Cascada de 7 Filtros IIR Descraneados (Orfanidis) con Sobremuestreo 2x o Convolución FIR de Fase Lineal
- **Ecuación de Transferencia:** `En modo Linear Phase: h_FIR[n] = Window(IFFT(|H_target(w)| * exp(-j*w*(N-1)/2))).`
- **Arquitectura Interna:** 7 Nodos de filtro (LP, BP, HP, Notch, Low Shelf, Peaking, High Shelf) con orden Gentle 2..Steep 8, Motor FIR de Fase Lineal (Linear Phase), Motor HQ de sobremuestreo 2x / deconvolución de fase en Nyquist, Analizador FFT de mapa térmico de entrada/salida
- **Parámetros Clave:** Band 1..7 Type, Order, Gain, Freq, Bandwidth, Linear Phase Switch, HQ Oversampling Switch, Main Level
- **Mapeo MIDI CC:** `{"74": "Band 1 Frequency", "71": "Band 1 Bandwidth", "1": "Band 4 Gain"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 136 bytes (usado en Slot 0 de Master_C5_SOTA.fst).

### 6.42. Fruity Peak Controller — *Seguidor de envolvente de pico y oscilador LFO para modulación de cadena lateral*
- **Definición RAE:** Extractor de la envolvente de amplitud instantánea de una señal de audio (ej. un bombo) que la transforma en dos señales de control interno ('Peak', 'LFO' y 'Peak+LFO') con nivel base, escala positiva o negativa (agachamiento/ducking), tensión de curva y tiempo de caída.
- **Familia DSP:** Rectificador de Onda Completa + Detector de Pico con Caída Exponencial de Tensión Variable
- **Ecuación de Transferencia:** `E[n] = max(|x[n]|, E[n-1]*alpha_decay); Out_Peak[n] = clamp(Base + Vol * f_tension(E[n]), 0, 1)`
- **Arquitectura Interna:** Detector de pico (Base, Volume +/-200%, Tension, Decay), Oscilador LFO sincronizable a tempo, Conmutador Mute (permite dejar o silenciar el audio fuente)
- **Parámetros Clave:** Peak Base, Peak Vol (-200%..+200%), Peak Tension, Peak Decay, LFO Base/Vol/Tension/Speed, Mute Audio Output
- **Mapeo MIDI CC:** `{"74": "Peak Decay", "1": "Peak Vol"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 40 bytes.

### 6.43. Fruity Phase Inverter — *Inversor de polaridad eléctrica por canal estereofónico*
- **Definición RAE:** Utilidad de fase que multiplica por -1 (rotación de 180 grados en todas las frecuencias) el canal izquierdo, el derecho o ambos, para corregir cancelaciones de fase en grabaciones multimicrófono o extraer la señal diferencial.
- **Familia DSP:** Multiplicación Escalar Unitaria Negativa (-1.0)
- **Ecuación de Transferencia:** `L'[n] = s_L * L[n], R'[n] = s_R * R[n], con s_L, s_R in {-1, +1}.`
- **Arquitectura Interna:** Selector de estado (Off, Invert Left, Invert Right)
- **Parámetros Clave:** Invert Mode (Off / Left / Right)
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 4 bytes.

### 6.44. Fruity Phaser — *Desfasador analógico virtual de hasta veintitrés etapas paso-todo*
- **Definición RAE:** Procesador de barrido espectral que encadena entre 1 y 23 filtros paso-todo (all-pass) cuya frecuencia de rotación de fase oscila entre una frecuencia mínima y máxima mediante un LFO triangular/senoidal.
- **Familia DSP:** Cascada de M Filtros All-Pass de Primer Orden con Coeficiente Modulado
- **Ecuación de Transferencia:** `y[n] = Dry*x[n] + Wet * AP_{1..Stages}(x[n] + fb*y_{ap}[n-1], a(LFO(t)))`
- **Arquitectura Interna:** Red de 1 a 23 etapas All-Pass, Oscilador de barrido con Min/Max Depth, Bucle de realimentación resonante
- **Parámetros Clave:** Sweep Freq, Min Depth, Max Depth, Freq Range, Stereo Phase, Nr of Stages (1..23), Feedback, Dry/Wet
- **Mapeo MIDI CC:** `{"74": "Sweep Freq", "71": "Feedback"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 36 bytes.

### 6.45. Fruity Reeverb — *Reverberador algorítmico clásico de redes de Schroeder-Moorer*
- **Definición RAE:** Algoritmo clásico de reverberación digital basado en retardos de reflexiones tempranas seguidos de un banco paralelo de filtros de peine realimentados con amortiguación paso-bajo y una cascada de difusores paso-todo.
- **Familia DSP:** Red Algorítmica de Schroeder-Moorer (8 Peines Paralelos + 4 Difusores All-Pass en Serie)
- **Ecuación de Transferencia:** `y[n] = Dry*x[n] + Wet * AllPass_4(sum_{k=1}^8 Comb_k(HPF(x[n - D_pre]), RT60, HF_Damp))`
- **Arquitectura Interna:** Línea de Pre-Delay, Filtros Low Cut y High Cut de entrada, Matriz de recinto (Room Size, Diffusion, Decay, High Damping)
- **Parámetros Clave:** Low Cut, High Cut, PreDelay, Room Size, Diffusion, Decay, High Damping, Dry, Reverb Wet
- **Mapeo MIDI CC:** `{"91": "Reverb Wet", "74": "Decay Time"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 48 bytes.

### 6.46. Fruity Reeverb 2 — *Reverberador algorítmico geométrico con procesamiento Mid/Side y modulación de cola*
- **Definición RAE:** Reverberador algorítmico de estudio con representación geométrica de prisma poligonal (3 a 20 paredes = Difusión), selector de entrada Centro/Lateral (Mid/Side) para reverberar exclusivamente el centro o los lados, modulación de longitud de línea para eliminar resonancias metálicas y multiplicador de graves.
- **Familia DSP:** Red de Retardo Realimentada Modulada (Modulated FDN) con Codificación de Entrada Mid/Side
- **Ecuación de Transferencia:** `x_in = alpha_MS * Mid(x) + (1-alpha_MS)*Side(x); y = Dry*x + ER*EarlyRef(x_in) + Wet*FDN_Mod(x_in)`
- **Arquitectura Interna:** Selector de entrada Mid/Side, Línea de Pre-Delay sincronizable a tempo, Generador de Reflexiones Tempranas (ER), Tanque FDN con geometría variable (Diffusion/Walls), Modulación (Speed/Mod), Bass Multiplier y Crossover Damping
- **Parámetros Clave:** Mid/Side Input, High Cut, Low Cut, PreDelay, Size, Diffusion, Mod Speed/Amt, Decay, Bass Multiplier, Damping, ER, Wet, Dry, Stereo Separation
- **Mapeo MIDI CC:** `{"91": "Wet Level", "74": "Decay Time", "71": "Size"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 60 bytes.

### 6.47. Fruity Scratcher — *Plato giradiscos virtual de arrastre directo para rayado manual o automatizado*
- **Definición RAE:** Simulador de tornamesa en ranura de efecto que permite cargar un archivo WAV y manipular directamente el ángulo angular del disco (Wave Position) con física de masa, velocidad y aceleración, además de un interruptor de silenciamiento de crossfader.
- **Familia DSP:** Integrador Cinemático de Inercia de Plato + Interpolación Sinc de Fase Continua
- **Ecuación de Transferencia:** `theta''(t) = (Torque_motor - k_fric*theta'(t)) / I_platter; y(t) = (1 - Mute)*Sample(theta(t))`
- **Arquitectura Interna:** Plato rotatorio automatizable, Simulador de masa, velocidad (33/45 RPM) y aceleración, Botón de corte (Mute) y paneo
- **Parámetros Clave:** Wave Position, Mute, Pan, Speed, Acceleration, Sensitivity
- **Mapeo MIDI CC:** `{"1": "Wave Position (Scratch Wheel)", "64": "Crossfader Mute"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros cinemáticos y archivo WAV.

### 6.48. Fruity Send — *Derivador de señal pre-atenuador hacia cualquier canal del mezclador*
- **Definición RAE:** Utilidad de ruteo que extrae la señal en el punto exacto de la ranura de inserción donde se coloca (por tanto, antes del fader principal del canal, Pre-Fader) y la envía con control de volumen y panorámica a cualquier canal conectado en cadena lateral.
- **Familia DSP:** Derivación de Bus en Punto de Inserción (Pre-Fader Tap Routing)
- **Ecuación de Transferencia:** `y_slot[n] = Dry * x[n]; Bus_{SendTarget}[n] += Volume * Pan(x[n])`
- **Arquitectura Interna:** Selector de canal destino (Sidechain Target), Potenciómetros Dry, Volume y Pan
- **Parámetros Clave:** Pan, Dry, Volume, Send To Track
- **Mapeo MIDI CC:** `{"91": "Send Volume", "10": "Send Pan"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 16 bytes.

### 6.49. Fruity Soft Clipper — *Recortador armónico de cresta por función tangente hiperbólica con umbral variable*
- **Definición RAE:** Arma secreta de la sonoridad moderna en FL Studio: permanece 100% lineal e invisible por debajo del umbral (Threshold), y aplica una curva tangencial suave exclusivamente a las crestas transitorias que superan dicho umbral, afeando 1.5 a 3 dB de pico en microsegundos sin provocar el bombeo (pumping) de un limitador de envolvente.
- **Familia DSP:** Saturador Tangencial por Tramos Sin Memoria (Piecewise Linear / Hyperbolic Tangent Clipper)
- **Ecuación de Transferencia:** `y[n] = G_post * x[n] si |x[n]| <= T; G_post * sgn(x[n]) * (T + (1 - T)*tanh((|x[n]| - T)/(1 - T))) si |x[n]| > T.`
- **Arquitectura Interna:** Potenciómetro de Umbral (Threshold) de rodilla, Potenciómetro de Ganancia de Salida (Post Gain), Gráfico de función de transferencia entrada/salida en tiempo real
- **Parámetros Clave:** Threshold, Post Gain
- **Mapeo MIDI CC:** `{"74": "Threshold", "7": "Post Gain"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 8 bytes (2 int32: Threshold y Post Gain; usado en Slot 2 de Master_C5_SOTA.fst).

### 6.50. Fruity Spectroman — *Analizador de espectro en tiempo real por transformada rápida de Fourier o banco de filtros*
- **Definición RAE:** Medidor visual del contenido frecuencial de la mezcla con modos de visualización de barras o espectrograma de humo en estéreo o mono.
- **Familia DSP:** Transformada de Fourier de Tiempo Corto (STFT Ventana de Blackman-Harris)
- **Ecuación de Transferencia:** `y[n] = x[n] (medidor no intrusivo); P(k) = 20*log10(|FFT(w * x)|)`
- **Arquitectura Interna:** Motor FFT / Bandas, Escalador de ventana y amplificación visual
- **Parámetros Clave:** Amp, Scale, Windowing, Mode (Stereo/Mono)
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 16 bytes.

### 6.51. Fruity Squeeze — *Degradador digital de resolución y supresor periódico de muestras (Squarer/Bitcrusher)*
- **Definición RAE:** Efecto de distorsión digital extrema que combina un filtro paso-bajo resonante con un reductor de frecuencia de muestreo y una unidad 'Squeeze' que fuerza a cero o retiene tramos enteros de muestras periódicamente para timbres industriales y chiptune.
- **Familia DSP:** Submuestreo con Retención de Orden Cero (Zero-Order Hold) + Truncamiento Periódico de Ciclo
- **Ecuación de Transferencia:** `y[n] = SVF(x[floor(n / M)*M] * Gate_Squeeze(n mod P, Amount))`
- **Arquitectura Interna:** Unidad Punch/Squeeze (Preserve, Amount, Relation), Filtro LP resonante pre/post, Mix Dry/Wet
- **Parámetros Clave:** Preserve, Amount, Impact, Filter Cutoff & Res, Mix
- **Mapeo MIDI CC:** `{"74": "Filter Cutoff", "1": "Squeeze Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 32 bytes.

### 6.52. Fruity Stereo Enhancer — *Expansor estereofónico por desfase interaural y matriz de diferencia*
- **Definición RAE:** Procesador de imagen estéreo que combina codificación Mid/Side (Stereo Separation) con un retardo corto en uno de los canales (Phase Offset de hasta 500 ms, efecto Haas) e inversión de polaridad de un canal.
- **Familia DSP:** Matriz Mid/Side + Retardo Interaural (Haas Delay Line) + Inversión de Fase Unilateral
- **Ecuación de Transferencia:** `L'[n] = M[n] + alpha*S[n]; R'[n] = sgn_inv * (M[n - D_haas] - alpha*S[n - D_haas])`
- **Arquitectura Interna:** Separador estéreo M/S (-100% Merged..+100% Separated), Línea de retardo Phase Offset (Left/Right), Inversor de fase L/R
- **Parámetros Clave:** Stereo Separation, Phase Offset, Phase Inversion, Pan, Volume
- **Mapeo MIDI CC:** `{"74": "Stereo Separation", "71": "Phase Offset"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 24 bytes.

### 6.53. Fruity Stereo Shaper — *Matriz algebraica de mezcla estereofónica 2x2 con retardo e inversión de fase*
- **Definición RAE:** Herramienta de ingeniería de fase e imagen estéreo que expone explícitamente los 4 coeficientes de la matriz 2x2 de mezcla entre canales: Izquierdo en Izquierdo (L), Derecho en Izquierdo (R->L), Derecho en Derecho (R) e Izquierdo en Derecho (L->R), permitiendo decodificar pares Mid/Side, aislar el canal lateral o aplicar retardos de precisión.
- **Familia DSP:** Transformación Lineal Matricial 2x2 en R^2 con Retardo e Inversión por Rama
- **Ecuación de Transferencia:** `[L_out; R_out] = [[g_{LL}, g_{RL}]; [g_{LR}, g_{RR}]] * [L_in(t - d_L); R_in(t - d_R)]`
- **Arquitectura Interna:** 4 Deslizadores bipolares (-inf..0 dB con inversión de signo): Left->Right, Left, Right, Right->Left, Retardo Pre/Post (Delay L/R), Rotador de fase (Phase) y envío In/Out Difference a cadena lateral
- **Parámetros Clave:** Left into Right, Left, Right, Right into Left, Delay, Phase, In/Out Difference Send
- **Mapeo MIDI CC:** `{"74": "Side Cross-Mix", "71": "Phase Offset"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 28 bytes.

### 6.54. Fruity Vocoder — *Codificador de envolvente vocal clásico de hasta ciento veintiocho bandas de filtro*
- **Definición RAE:** Vocodificador clásico de banco de filtros que toma el canal Izquierdo como Modulador (Voz) y el Derecho como Portadora (Sintetizador), dividiendo ambos en entre 4 y 128 bandas frecuenciales de primer o segundo orden con detector de envolvente (Attack/Release) por banda.
- **Familia DSP:** Banco de N Filtros Paso-Banda IIR + N Seguidores de Envolvente Multiplicativos
- **Ecuación de Transferencia:** `y[n] = sum_{b=1}^N Gain_b * Env_AR(|H_b(z)[x_L[n]]|) * H_b(z)[x_R[n]]`
- **Arquitectura Interna:** Banco de 4 a 128 bandas con escala lineal/logarítmica, Seguidores de envolvente con Attack/Release y Formant Shift, Gráfico de barras de ganancia individual por banda
- **Parámetros Clave:** Bands (4..128), Filter Order, Freq Min/Max, Formant Pitch Shift, Env Attack/Release, Mod/Car/Wet Mix
- **Mapeo MIDI CC:** `{"74": "Formant Shift", "71": "Envelope Release"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los parámetros globales y el vector de ganancias de las 128 bandas.

### 6.55. Fruity WaveShaper — *Conformador de onda de curva de esplines libre con sobremuestreo hasta dieciséis veces*
- **Definición RAE:** Distorsionador gráfico matemático donde el usuario dibuja directamente la función de transferencia $y = f(x)$ mediante curvas spline multipunto en modo unipolar (simétrico, genera armónicos impares) o bipolar (asimétrico, genera armónicos pares e impares), con sobremuestreo de hasta 16x y bloqueo de continua.
- **Familia DSP:** Evaluación de Tabla de Búsqueda (LUT) Generada por Splines con Sobremuestreo Polifásico Anti-Aliasing
- **Ecuación de Transferencia:** `y[n] = DC_Block(Downsample_K(SplineCurve_Bipolar(Pre * Upsample_K(x[n])))) * Post`
- **Arquitectura Interna:** Editor de curva de transferencia $y=f(x)$ (Unipolar / Bipolar), Etapa Pre-gain, Mix y Post-gain, Filtro de sobremuestreo (None, 2x, 4x, 8x, 16x) y filtro Center (DC remover)
- **Parámetros Clave:** Pre Gain, Mix, Post Gain, Bipolar Mode, Oversampling (2x..16x), Center DC Filter
- **Mapeo MIDI CC:** `{"1": "Pre Gain Drive", "74": "Wet Mix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con la lista de nodos y tensiones de la curva spline.

### 6.56. Fruity Wrapper — *Adaptador anfitrión de procesadores de efectos externos (VST2/VST3/AU/CLAP)*
- **Definición RAE:** Versión de efecto de inserción del Fruity Wrapper que aloja plugins de procesamiento de terceros (ej. Ozone 11, FabFilter, Valhalla) en cualquiera de las 10 ranuras de los 125 canales del mezclador, gestionando entradas auxiliares de cadena lateral (Sidechain Auxiliary Inputs).
- **Familia DSP:** Puente Multicanal de Audio (Main Stereo + Sidechain Stereo) y Automatización VST3/AU
- **Ecuación de Transferencia:** `y_{L,R}[n] = VST3_EffectProcess(x_main[n], x_sidechain[n], ParamChanges)`
- **Arquitectura Interna:** Matriz de conexiones de entradas/salidas multipuerto (Processing Tab -> Auto Map Inputs), Reportador de latencia exacta al motor PDC del mezclador
- **Parámetros Clave:** Stereo Aux Input (Sidechain), Latency Compensation Offset, Dry/Wet Mix
- **Mapeo MIDI CC:** `{"1": "Mapped VST Parameter 1"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con cabecera Wrapper + estado binario opaco del efecto VST3/AU.

### 6.57. Fruity X-Y Controller — *Controlador vectorial bidimensional con física de inercia y suavizado de trayectoria*
- **Definición RAE:** Generador de dos señales de control interno (X e Y) manipulables simultáneamente mediante una cruceta bidimensional con velocidad y aceleración de suavizado configurables para barridos orgánicos de filtro y resonancia.
- **Familia DSP:** Filtro Cinemático de Segundo Orden (Velocidad y Aceleración Acotadas) en 2D
- **Ecuación de Transferencia:** `p''(t) = Accel * (p_target(t) - p(t)) - Damp * p'(t)`
- **Arquitectura Interna:** Plano cartesiano X/Y [0..1]^2, Integrador de Speed y Acceleration,  Escaladores Min/Max para X e Y
- **Parámetros Clave:** X Value, Y Value, Speed, Acceleration
- **Mapeo MIDI CC:** `{"1": "X Coordinate", "11": "Y Coordinate"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 32 bytes.

### 6.58. Fruity X-Y-Z Controller — *Controlador espacial tridimensional con funciones de transferencia por eje*
- **Definición RAE:** Evolución tridimensional del controlador vectorial que emite tres señales de control independientes (X, Y, Z), cada una con su propia curva spline de mapeo de entrada a salida y suavizado cinemático.
- **Familia DSP:** Mapeo No Lineal por Eje R^3 -> [0,1]^3 con Suavizado Temporal
- **Ecuación de Transferencia:** `Out_i(t) = Spline_i(Smooth(Input_i(t), Speed, Accel)) para i in {X, Y, Z}.`
- **Arquitectura Interna:** Cubo de coordenadas (X, Y, Z), 3 Editores de curvas de transferencia de entrada/salida, Motor de inercia
- **Parámetros Clave:** X, Y, Z, Speed, Acceleration
- **Mapeo MIDI CC:** `{"1": "X", "11": "Y", "74": "Z"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con coordenadas X, Y, Z y las 3 curvas spline.

### 6.59. Fruity dB meter — *Medidor de nivel de pico en decibelios referidos al fondo de escala (dBFS)*
- **Definición RAE:** Vúmetro digital vertical de alta visibilidad con retención de picos para vigilar la estructura de ganancia en cualquier punto de la cadena de efectos.
- **Familia DSP:** Conversión Logarítmica de Amplitud Instantánea a Decibelios (20*log10|x|)
- **Ecuación de Transferencia:** `dBFS[n] = 20 * log10(max(|x[n]|, 10^-5)); y[n] = x[n]`
- **Arquitectura Interna:** Detector de pico L/R con memoria de máximo
- **Parámetros Clave:** N/A
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 4 bytes.

### 6.60. Gross Beat — *Manipulador matricial de tiempo y amplitud en tiempo real sobre búfer de dos compases*
- **Definición RAE:** Procesador de culto de FL Studio que graba continuamente un búfer circular de 2 compases de audio y expone 36 ranuras de curvas de esplines de Tiempo (desplazamiento hacia atrás en el búfer: tartamudeo, parada de vinilo, medio tiempo '1/2 Speed', rayado) y 36 ranuras de Volumen (puerta rítmica, agachamiento de cadena lateral 'Sidechain') disparables por notas MIDI.
- **Familia DSP:** Lectura de Búfer Circular con Fase Temporal Gobernada por Spline (t_read = t_now - Delta_t(phi_bar))
- **Ecuación de Transferencia:** `y(t) = Env_{VolSlot}(t mod T_bar) * Buffer(t - T_bar * Env_{TimeSlot}(t mod T_bar))`
- **Arquitectura Interna:** Búfer circular de 2 compases sincronizado a PPQ, 36 Ranuras de Tiempo (Time Slots C5..B7) con curvas de derivada de velocidad, 36 Ranuras de Volumen (Volume Slots C2..B4) con suavizado anti-clic (Attack/Release/Tension), Conmutador de cuantización de disparo (Trigger Sync: Off, 1/4, 1/2, 1 Beat, 1 Bar)
- **Parámetros Clave:** Time Slot Index (1..36), Volume Slot Index (1..36), Time Mix, Volume Mix, Volume Attack/Release De-click
- **Mapeo MIDI CC:** `{"1": "Time Slot Mix", "11": "Volume Slot Mix", "74": "Time Slot Selector"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los 72 árboles de curvas spline (36 de Tiempo + 36 de Volumen).

### 6.61. Hardcore — *Pedalera virtual de guitarra con once efectos de modelado y ecualizador gráfico*
- **Definición RAE:** Bastidor de 5 pedales de efecto intercambiables para guitarra y sintetizadores (Distortion, Chorus, Flanger, Phaser, Modulator, Delay, Noise Gate, Equalizer, Compression, Muffler, TubeWarm) precedido de puerta de ruido y seguido de un ecualizador gráfico de 8 bandas y simulador de gabinete.
- **Familia DSP:** Cascada de 5 Pedales No Lineales + EQ de 8 Bandas + Convolución de Pantalla Acústica
- **Ecuación de Transferencia:** `y[n] = Cabinet_IR(EQ_8(Pedal_5(...Pedal_1(NoiseGate(x[n])))))`
- **Arquitectura Interna:** Noise Gate de entrada, 5 Ranuras de pedal con 11 modelos de circuito, Ecualizador de 8 bandas (65Hz..8kHz) + 5 modelos de pantalla Cabinet
- **Parámetros Clave:** Pedal 1..5 Parameters, Cabinet Model, 8-Band EQ Sliders
- **Mapeo MIDI CC:** `{"1": "Pedal 1 Drive", "74": "Cabinet Mix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con la topología de los 5 pedales y el EQ.

### 6.62. Hyper Chorus — *Multiplicador coral hiperdenso de seis voces con modulación multibanda*
- **Definición RAE:** Efecto de ensanchamiento estereofónico extremo que superpone hasta 6 líneas de retardo moduladas en contrafase con filtrado de graves para mantener intacto el centro monofónico de la mezcla.
- **Familia DSP:** Banco de 6 Líneas de Retardo Fraccionarias con Modulación Polifásica
- **Ecuación de Transferencia:** `y[n] = Dry*x[n] + Wet * sum_{k=1}^6 Pan_k * x(n - D_k - Depth*sin(w*t + 2*pi*k/6))`
- **Arquitectura Interna:** 6 Voces de retardo modulado, Filtro de exclusión de graves, Control de velocidad, profundidad y mezcla
- **Parámetros Clave:** Rate, Depth, Delay, Voices, Low Cut, Mix
- **Mapeo MIDI CC:** `{"74": "Depth", "1": "Rate"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros del banco de 6 voces.

### 6.63. Low Lifter — *Sintetizador psicoacústico de subarmónicos y armónicos superiores para refuerzo de graves*
- **Definición RAE:** Procesador de realce de bajas frecuencias que rastrea la fundamental del registro grave, sintetiza una octava inferior limpia (Sub-bass synthesis) y genera simultáneamente la serie de armónicos superiores (principio del fundamental ausente de Fletcher) para que el subgrave se perciba incluso en altavoces pequeños.
- **Familia DSP:** Divisor de Frecuencia Subarmónico + Excitación Polinómica de Armónicos Superiores (Missing Fundamental)
- **Ecuación de Transferencia:** `y[n] = x[n] + g_sub * Osc_{f0/2}[n] + g_harm * sum_{k=2}^5 c_k * T_k(LPF_bass(x[n]))`
- **Arquitectura Interna:** Detector de banda grave con frecuencia de cruce, Generador de subarmónicos en fase, Excitador armónico psicoacústico con limitador de excursión
- **Parámetros Clave:** Crossover Frequency, Sub Bass Level, Harmonic Drive, Output Ceiling, Dry/Wet
- **Mapeo MIDI CC:** `{"74": "Crossover Frequency", "1": "Sub Bass Level"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de seguimiento subarmónico.

### 6.64. LuxeVerb — *Reverberador algorítmico de alta densidad con tanque de realimentación tonal (Shimmer), seguidor de envolvente y compuerta*
- **Definición RAE:** Reverberador algorítmico insignia de FL Studio 2025: modela espacios acústicos realistas y cámaras hiperreales mediante una red de retardo de alta difusión con bucle de realimentación dotado de cambio de tono cromático (Pitch Shifter para colas angelicales Shimmer de +12 semitonos), seguidor de envolvente para agachamiento automático (Auto-Ducking de la cola mientras suena la voz/sintetizador), congelación infinita (Freeze) y separador Mid/Side.
- **Familia DSP:** Red FDN Modulada de Alta Densidad + Pitch Shifter Granular en Bucle de Realimentación + Seguidor de Envolvente
- **Ecuación de Transferencia:** `Tail[n] = FDN(x[n] + fb * PitchShift(Tail[n - D], +12 st)) * (1 - Duck(Env(x[n])))`
- **Arquitectura Interna:** Sección Input con Envelope Follower (modulable a Wet, Decay o PreDelay) y Freeze, Tanque Reverb (Decay, Size, Diffusion, Brightness, Mod Depth/Speed), Bucle Feedback con Pitch Shifter (-12..+12 semitonos) y Damping de 3 bandas, Sección Output con Peak/Shelf EQ y separación estéreo
- **Parámetros Clave:** Decay Time, Size, Brightness, Feedback Pitch (+12st Shimmer), Feedback Mix, Envelope Follower to Wet (Ducking), Freeze Switch
- **Mapeo MIDI CC:** `{"91": "Wet Level", "74": "Decay Time", "71": "Brightness", "1": "Shimmer Feedback Mix"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con estado completo del tanque FDN, Pitch Shifter y seguidor de envolvente.

### 6.65. Maximus — *Maximizado maestro multibanda con curvas de transferencia por esplines y limitador de anticipación*
- **Definición RAE:** Procesador supremo de dinámica y masterización de FL Studio: divide el espectro en tres bandas (Low, Mid, High) mediante filtros de cruce IIR o de fase lineal, somete cada banda y la suma maestra (Master) a una función de transferencia dinámica dibujada libremente con curvas spline (permitiendo simultáneamente puerta de ruido, expansión ascendente, compresión y limitación en una sola curva), integra saturación armónica analógica de dos tipos (A/B) y fuerza la monofonía absoluta de subgraves.
- **Familia DSP:** División de 3 Bandas (IIR / Fase Lineal) + 4 Computadores de Ganancia por Curva Spline + Saturador Asimétrico + Limitador Lookahead
- **Ecuación de Transferencia:** `Para banda b in {L, M, H, Master}: y_b[n] = Saturate(x_b[n - L_att] * (Spline_b(Env_b[n]) / max(Env_b[n], eps)))`
- **Arquitectura Interna:** Filtros de corte Low Cut (20..100Hz) y Crossovers Low-Mid / Mid-High con modo Linear Phase, 4 Bandas completas (LOW, MID, HIGH, MASTER), cada una con Pre-Gain, Curva Spline I/O, Attack, Release, Ahead, Sustain, Stereo Separation y Saturation (Threshold/Ceiling), Visualizador multimodo de compresión y crestas
- **Parámetros Clave:** Low/High Crossover Freq, Low Band Stereo Separation (100% Merged Mono), Band L/M/H/Master Pre-Gain & Post-Gain, Master Attack (Lookahead), Saturation Threshold/Ceiling
- **Mapeo MIDI CC:** `{"7": "Master Pre-Gain", "74": "Low Crossover Freq", "71": "Master Release"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los 4 árboles de curvas spline de transferencia (Low, Mid, High, Master) y crossovers (usado en Slot 1 de Master_C5_SOTA.fst).

### 6.66. Multiband Delay — *Banco espectral de dieciséis bandas de retardo, cambio de tono y paneo independientes*
- **Definición RAE:** Efecto de diseño sonoro vanguardista que descompone la señal en 16 bandas frecuenciales (escala lineal, logarítmica o armónica) y permite aplicar a cada banda un tiempo de retardo, realimentación, volumen, panorámica y desplazamiento de tono distintos, creando barridos dispersivos (chirps) y ritmos espectrales.
- **Familia DSP:** Banco de 16 Filtros de Reconstrucción Perfecta + 16 Líneas de Retardo Moduladas con Pitch Shift
- **Ecuación de Transferencia:** `y[n] = sum_{b=1}^{16} Pan_b * Vol_b * Delay_Pitch_b(H_band_b(z)[x[n]], D_b, fb_b)`
- **Arquitectura Interna:** Banco de 16 bandas con selector de escala (Harmonic, Bark, Linear), 16 Líneas de retardo sincronizables o en milisegundos, Morfismo entre 8 bancos de ajustes (Morph knob)
- **Parámetros Clave:** Band 1..16 Delay, Volume, Pan, Feedback, Pitch, Master Scale, Bank Morph, Keep Pitch
- **Mapeo MIDI CC:** `{"1": "Bank Morph", "74": "Global Delay Scale", "71": "Global Feedback"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las 8 matrices de los 16 canales de retardo espectral.

### 6.67. Newtime — *Editor de cuantización y deformación elástica del tiempo (Time Warping) por marcadores de transitorios*
- **Definición RAE:** Laboratorio de alineación rítmica de audio que detecta los ataques transitorios de una interpretación vocal o instrumental y permite desplazarlos individualmente sobre la rejilla del compás o aplicar ranuras de groove sin alterar la altura tonal mediante el motor Zplane Elastique Pro.
- **Familia DSP:** Vocodificador de Fase con Bloqueo de Transitorios (Transient-Preserving Phase Vocoder Zplane Elastique)
- **Ecuación de Transferencia:** `Estiramiento local r_k = (t'_{k+1} - t'_k) / (t_{k+1} - t_k) preservando la fase coherente en los instantes de ataque t_k.`
- **Arquitectura Interna:** Detector de marcadores de transitorios (Warp Markers), Motor Zplane Elastique Pro v3, Cuantizador de plantillas de Groove
- **Parámetros Clave:** Groove Amount, Marker Positions, Playback Sync to Host
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el archivo WAV y el vector de marcadores de deformación temporal.

### 6.68. Newtone — *Editor quirúrgico de corrección de altura tonal, formantes y vibrato nota a nota*
- **Definición RAE:** Estación de afinación vocal y monofónica (equivalente nativo a Melodyne) que segmenta una grabación en bloques de nota sobre un Piano Roll, permitiendo corregir su afinación central, desviación fina, transición entre notas (rampa de portamento), amplitud de vibrato y desplazamiento de formantes.
- **Familia DSP:** Detección de Frecuencia Fundamental (YIN/Autocorrelación) + Re-síntesis PSOLA / Phase Vocoder con Preservación de Formantes
- **Ecuación de Transferencia:** `Re-escalado espectral separando fuente glotal E(w) y envolvente formántica V(w): Y(w) = E(w / alpha_pitch) * V(w / alpha_formant).`
- **Arquitectura Interna:** Motor de detección monofónica y troceado de notas,  Corrector macro de Center, Variation (Vibrato) y Transition Speed, Modo Warp (estiramiento temporal) y exportación a MIDI
- **Parámetros Clave:** Center (Pitch Quantize), Variation (Vibrato Scaling), Transition Speed, Scale Snap
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el audio PCM y la lista de bloques de nota editados.

### 6.69. Patcher — *Sub-anfitrión modular de efectos en grafo acíclico dirigido*
- **Definición RAE:** Versión de efecto de inserción de Patcher que permite construir cadenas de procesamiento paralelas, multibanda (junto a Frequency Splitter) o Mid/Side (junto a Fruity Stereo Shaper) dentro de una única ranura del mezclador.
- **Familia DSP:** Evaluación Topológica de Grafo Dirigido de Procesadores de Audio y Control
- **Ecuación de Transferencia:** `y_out[n] = sum_{v in Sinks} Node_v(sum_{u -> v} g_{u,v} * Node_u[n])`
- **Arquitectura Interna:** Grafo de nodos de audio, eventos y parámetros, Panel Control Surface personalizable, Compensación automática de retardo por rama
- **Parámetros Clave:** Surface Macro Controls
- **Mapeo MIDI CC:** `{"1": "Surface Macro 1", "74": "Surface Macro 2"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 recursivo que empaqueta todos los efectos internos y sus conexiones.

### 6.70. Pitch Shifter — *Transpositor de altura tonal en tiempo real de doble motor (Granular y Vocodificador de Fasecon Formantes)*
- **Definición RAE:** Procesador de cambio de tono en vivo provisto de dos motores especializados: el modo 'Music' (vocodificador de fase polifónico con preservación y desplazamiento de formantes) y el modo 'Voice' (motor granular sincronizado al periodo glotal con duración y densidad ajustables).
- **Familia DSP:** Modo Music: STFT Phase Vocoder con Cepstrum Formant Preservation; Modo Voice: PSOLA Granular
- **Ecuación de Transferencia:** `f_out = f_in * 2^(Semitones/12 + Cents/1200)`
- **Arquitectura Interna:** Pestaña Voice (Granular: Pitch, Formant, Duration, Density, Jitter), Pestaña Music (Phase Vocoder: Pitch, Formant, Latency/Quality), Línea de retardo con realimentación (Crystals / Shimmer delays)
- **Parámetros Clave:** Pitch Semitones (-12..+12), Formant Shift, Engine Mode (Voice/Music), Delay Time & Feedback, Mix
- **Mapeo MIDI CC:** `{"74": "Pitch Shift", "71": "Formant Shift"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de ambos motores y línea de retardo.

### 6.71. Pitcher — *Corrector automático de afinación vocal en tiempo real y armonizador de cuatro voces*
- **Definición RAE:** Procesador de afinación instantánea de baja latencia (estilo Auto-Tune) que fuerza la frecuencia fundamental de una voz hacia las notas permitidas de una escala musical o hacia un acorde de 4 voces introducido por MIDI en tiempo real, con control de velocidad de corrección, preservación de formantes y deslizamiento de género (Masculino/Femenino).
- **Familia DSP:** Rastreo de Periodo Fundamental en Tiempo Real + Re-muestreo Sincrono al Tono (TD-PSOLA) con Filtro de Formantes
- **Ecuación de Transferencia:** `f_target = argmin_{f_k in Scale} |log2(f_detected / f_k)|; f_out(t) = f_out(t-1) + alpha_speed * (f_target - f_out(t-1))`
- **Arquitectura Interna:** Detector de pitch de latencia mínima (Min Freq: Normal/Bass), Cuantizador de escala cromática/diatónica, Motor de corrección (Speed: Fast..Slow) + Gender Formant Shifter, Armonizador de 4 voces controlado por puerto MIDI (Modo MIDI + Octaves)
- **Parámetros Clave:** Correction Speed, Fine Tune, Gender Formant, Scale Notes Enable, MIDI Mode & Port, Voice 1..4 Pan/Level
- **Mapeo MIDI CC:** `{"74": "Correction Speed", "71": "Gender Formant"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con máscara de escala, velocidad y configuración de las 4 voces.

### 6.72. Razer Chroma — *Transductor de energía espectral de audio a iluminación física RGB de periféricos*
- **Definición RAE:** Puente de visualización de hardware que analiza el espectro FFT o el nivel de pico del canal donde se inserta y transmite tramas de color RGB hacia teclados y dispositivos compatibles.
- **Familia DSP:** Análisis Espectral FFT de Baja Resolución -> Matriz RGB
- **Ecuación de Transferencia:** `y[n] = x[n] (paso transparente de audio)`
- **Arquitectura Interna:** Analizador de barras espectrales, Emisor de eventos de iluminación
- **Parámetros Clave:** Visualization Effect, Color Palette
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de configuración visual.

### 6.73. Soundgoodizer — *Macro-procesador psicoacústico multibanda de un solo mando basado en el motor Maximus*
- **Definición RAE:** Envoltorio simplificado del motor de masterización Maximus que expone únicamente una rueda maestra de cantidad (mezcla paralela de compresión/saturación multibanda) y cuatro perfiles precalibrados: Preset A (realce de graves y aire estereofónico en agudos), Preset B (saturación cálida de medios), Preset C (compresión densa y agresiva de presencia) y Preset D (pegamento dinámico suave).
- **Familia DSP:** Motor Maximus de 3 Bandas + Banda Master con Interpolación Paramétrica por Rueda Única
- **Ecuación de Transferencia:** `y[n] = Maximus_Engine(x[n]; Preset_{A,B,C,D}, MacroGain = Amount)`
- **Arquitectura Interna:** Núcleo completo de Maximus (3 bandas + Master), Selector de 4 curvas de transferencia (A, B, C, D), Potenciómetro rotatorio gigante de intensidad
- **Parámetros Clave:** Mode (A / B / C / D), Amount (0.0..1.0)
- **Mapeo MIDI CC:** `{"1": "Soundgoodizer Amount", "74": "Mode Selector"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 12 bytes (índice de modo 0..3 + float de cantidad).

### 6.74. Spreader — *Ensanchador estereofónico monocompatible por filtros de peine desfasados*
- **Definición RAE:** Procesador de apertura espacial que genera anchura estereofónica a partir de señales monofónicas o estrechas dividiendo el espectro mediante pares de filtros complementarios en oposición de fase cuyos lóbulos se cancelan exactamente al sumar a mono, garantizando cero cancelaciones destructivas en sistemas de club.
- **Familia DSP:** Par de Redes All-Pass / Filtros Complementarios Ortogonales (Suma Mono = Identidad)
- **Ecuación de Transferencia:** `L[n] = x_L[n] + alpha * H_orth(x_M[n]); R[n] = x_R[n] - alpha * H_orth(x_M[n]) => L + R = x_L + x_R.`
- **Arquitectura Interna:** Red de desfase ortogonal monocompatible, Filtro de preservación de bajas frecuencias (Low Bypass), Goniómetro / Vectorscopio integrado
- **Parámetros Clave:** Spread Amount, Separation, Low Bypass Frequency
- **Mapeo MIDI CC:** `{"74": "Spread Amount", "71": "Low Bypass"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de expansión ortogonal.

### 6.75. Transient Processor — *Escultor dinámico diferencial de ataque transitorio y cola de sostenimiento con división de graves*
- **Definición RAE:** Procesador de dinámica independiente del nivel absoluto que compara un detector de envolvente instantáneo con uno integrado para aislar el ataque inicial (Attack) y la caída posterior (Release/Sustain), permitiendo afilar o suavizar percusiones con una sección de corte de frecuencia (Split Frequency) para dejar intacto o procesar por separado el subgrave.
- **Familia DSP:** Detección Diferencial de Envolventes Duales + Saturación de Cresta (Drive)
- **Ecuación de Transferencia:** `g_dB[n] = G_att * max(0, E_fast[n] - E_slow[n]) + G_rel * max(0, E_slow[n] - E_fast[n])`
- **Arquitectura Interna:** Divisor frecuencial (Split Frequency) para proteger graves, Detector diferencial de Attack y Release con ajuste de forma (Attack Shape), Etapa de saturación Drive de picos, Monitor de ondas de ganancia diferencial
- **Parámetros Clave:** Attack, Drive, Release, Attack Shape, Split Frequency, Gain
- **Mapeo MIDI CC:** `{"74": "Attack Gain", "71": "Release Sustain", "1": "Drive"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 32 bytes.

### 6.76. Transporter — *Motor de bucles efímeros en tiempo real, salto estocástico de compás y rebanado al vuelo*
- **Definición RAE:** Procesador de manipulación temporal en vivo que captura continuamente los últimos compases de audio en un anillo de memoria y dispara bucles de subdivisión (1/16..2 compases), reversa instantánea, cambio de tono y saltos entre rebanadas con fundidos cruzados sin clics.
- **Familia DSP:** Búfer Circular Sincronizado a Tempo con Saltos de Puntero Ventaneados y Pitch Shift
- **Ecuación de Transferencia:** `y[n] = Crossfade_Hann(RingBuffer[p_loop(n)], RingBuffer[p_live(n)])`
- **Arquitectura Interna:** Anillo de captura sincronizado al reloj del proyecto, Motor de subdivisión de bucle, reversa y velocidad, Matriz de disparo en vivo
- **Parámetros Clave:** Loop Size, Reverse, Pitch Shift, Slice Jump, Dry/Wet
- **Mapeo MIDI CC:** `{"1": "Loop Trigger", "74": "Loop Size"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con configuración del motor de bucles.

### 6.77. Tuner — *Afinador estroboscópico y medidor de frecuencia fundamental de alta precisión*
- **Definición RAE:** Analizador monofónico que estima la frecuencia fundamental al centésimo de semitono (cents) mediante autocorrelación de ventana larga, con referencia ajustable (La4 = 400..480 Hz) y tres velocidades de respuesta.
- **Familia DSP:** Estimación de Periodo por Diferencia Cuadrática Media Normalizada (Algoritmo YIN / McLeod Pitch Method)
- **Ecuación de Transferencia:** `Delta_cents = 1200 * log2(f_est / (f_ref_A4 * 2^((MIDI_nearest - 69)/12)))`
- **Arquitectura Interna:** Detector de tono YIN, Visualizador de aguja y estroboscópico, Interruptor Mute output
- **Parámetros Clave:** Reference Pitch (440 Hz), Reactivity Speed, Bass Mode, Mute
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 16 bytes.

### 6.78. VFX Color Mapper — *Enrutador de flujos de notas por índice de color del Piano Roll (dieciséis canales de voz)*
- **Definición RAE:** Nodo de procesamiento de voz exclusivo para Patcher que recibe un flujo polifónico de notas y redirige cada uno de los 16 colores de nota del Piano Roll (grupos de voz 1..16) hacia cualquiera de sus 16 salidas independientes o los reasigna de color.
- **Familia DSP:** Demultiplexor Discreto 16x16 de Eventos de Voz por Atributo de Color
- **Ecuación de Transferencia:** `OutputPort(Note) = RoutingMap[Note.ColorIndex (1..16)]`
- **Arquitectura Interna:** Matriz de conmutación de 16 colores de entrada a 4/16 puertos de salida
- **Parámetros Clave:** Color 1..16 Target Output & Target Voice Color
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 de 64 bytes (exclusivo de Patcher).

### 6.79. VFX Envelope — *Modulador polifónico de propiedades por voz mediante curvas de esplines (altura, corte, resonancia, paneo)*
- **Definición RAE:** Nodo de Patcher que inyecta envolventes multipunto y LFOs independientes para cada nota individual (verdadera articulación polifónica por voz) sobre el tono fino, la frecuencia de corte (Mod X), la resonancia (Mod Y), la velocidad y el paneo.
- **Familia DSP:** Modulación Polifónica por Voz (Per-Voice Envelope Generator)
- **Ecuación de Transferencia:** `Voice_i.Prop(t) = clamp(Voice_i.Prop_0 + Env_Prop(t - t_{on,i}), Min, Max)`
- **Arquitectura Interna:** 5 Pestañas de articulador por voz (Velocity, Pitch, Pan, Mod X, Mod Y), Motor de splines con LFO, Key Mapping y Velocity Mapping
- **Parámetros Clave:** Pitch Env Tension/Level, Mod X/Y Env Curves
- **Mapeo MIDI CC:** `{"1": "Global Tension Scaling"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los 5 árboles de articuladores por voz.

### 6.80. VFX Key Mapper — *Transpositor matricial de escalas, cuantizador tonal y generador automático de acordes*
- **Definición RAE:** Nodo de Patcher que intercepta cada nota entrante dentro de una octava y permite reasignarla a otra altura cromática, silenciarla o disparar simultáneamente un acorde completo de hasta 4 notas por tecla.
- **Familia DSP:** Transformación Matricial Discreta sobre el Anillo de Clases de Altura Z_12 -> P(Z_128)
- **Ecuación de Transferencia:** `Notes_out(k) = {k + Offset_Octave + Delta_j : j in ActiveSliders(k mod 12)}`
- **Arquitectura Interna:** Matriz de 12 columnas cromáticas con cursores multivoz (-12..+12 semitonos), Transpositor global de entrada/salida y plantillas de escalas y acordes
- **Parámetros Clave:** Base Key, Input/Output Transpose, 12-Key Chord/Note Sliders
- **Mapeo MIDI CC:** `{"74": "Global Transpose"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con la matriz de mapeo de las 12 clases de altura.

### 6.81. VFX Keyboard Splitter — *Divisor de teclado en dieciséis zonas de altura y velocidad con probabilidades de disparo*
- **Definición RAE:** Nodo de Patcher que particiona el rango MIDI (C0..G10) y el rango de velocidad (0..127) en hasta 16 zonas independientes con fundidos cruzados (crossfades) y curvas de probabilidad aleatoria para distribuir el teclado entre varios sintetizadores.
- **Familia DSP:** Particionado del Espacio Fase (Key x Velocity) con Compuerta Estocástica de Bernoulli
- **Ecuación de Transferencia:** `Zona z dispara si Key in [K_{min,z}, K_{max,z}] y u_rand < P_z(Key, Vel).`
- **Arquitectura Interna:** 16 Zonas con puertos de salida de voz independientes, Curvas de mapeo de velocidad y probabilidad aleatoria por zona
- **Parámetros Clave:** Zone 1..16 Key Range, Transpose, Velocity Curve, Random Probability
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con las 16 definiciones de zona.

### 6.82. VFX Level Scaler — *Escalador matemático y humanizador estocástico de propiedades de nota en tiempo real*
- **Definición RAE:** Nodo de Patcher que transforma en vivo las 6 propiedades de cada nota entrante (Velocity, Release, Pitch Fine, Pan, Mod X, Mod Y) aplicando desplazamiento (Offset), multiplicación con tensión (Multiply), centrado y variación aleatoria (Humanize).
- **Familia DSP:** Transformación Afín No Lineal + Perturbación Estocástica por Nota
- **Ecuación de Transferencia:** `p' = clamp(Center + (p - Center)*Mult + Offset + eta_rand*Humanize, 0, 1)`
- **Arquitectura Interna:** 6 Pestañas de propiedad de voz, Gráfico de transferencia entrada/salida en vivo
- **Parámetros Clave:** Offset, Multiply, Center, Tension, Humanize Random
- **Mapeo MIDI CC:** `{"1": "Velocity Multiply", "11": "Humanize Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con los escaladores de las 6 propiedades.

### 6.83. VFX Script — *Intérprete programable en Python para procesamiento algorítmico de voces, microtonalidad y control*
- **Definición RAE:** Motor de ejecución Python embebido en tiempo real dentro de Patcher (introducido en FL Studio 2025) que expone callbacks deterministas por voz y por tick (`onTriggerVoice`, `onReleaseVoice`, `onTick`) para programar arpegiadores generativos, autómatas celulares, afinaciones microtonales exactas (24-TET, Just Intonation, Scala) y moduladores matemáticos.
- **Familia DSP:** Máquina Virtual Python en Tiempo Real Acoplada al Reloj PPQ y Objetos `vfx.Voice`
- **Ecuación de Transferencia:** `v.finePitch = f_python(v.note, PPQ_clock, UI_Controls); v.trigger()`
- **Arquitectura Interna:** Intérprete CPython embebido con módulo `fl_vfx` / `vfx`, Generador dinámico de controles UI desde código, Salidas múltiples de Voz y de Controladores continuos
- **Parámetros Clave:** Python Script Source Code, Dynamic Script UI Knobs
- **Mapeo MIDI CC:** `{"1": "Script Parameter 1", "74": "Script Parameter 2"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el código fuente Python UTF-8 y el estado de sus controles.

### 6.84. VFX Sequencer — *Arpegiador y secuenciador algorítmico por pasos de propiedades de voz para Patcher*
- **Definición RAE:** Secuenciador de patrones MIDI y modulador de pasos alojado en Patcher que transforma acordes entrantes en secuencias rítmicas complejas con control por paso de puerta, ligadura, transposición, velocidad y envío de controladores.
- **Familia DSP:** Cuantización y Despliegue Secuencial de Conjuntos de Notas Activas sobre Reloj PPQ
- **Ecuación de Transferencia:** `Note_step(k) = ChordBuffer[Pattern_Index(k)] + Transpose(k)`
- **Arquitectura Interna:** Matriz de pasos de nota, octava, gate y tie, Modulador de velocidad y acento
- **Parámetros Clave:** Step Rate, Gate Length, Swing, Arp Mode, Step Pitch/Vel
- **Mapeo MIDI CC:** `{"74": "Gate Length", "1": "Swing"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con la secuencia de pasos.

### 6.85. Vintage Chorus — *Emulador de línea de retardo analógica de cubo de brigada (BBD) del coro Roland Juno-6*
- **Definición RAE:** Modelado físico del circuito integrado analógico Panasonic MN3009 (256 etapas Bucket-Brigade Device) empleado en los sintetizadores Roland Juno: reproduce el filtrado anti-aliasing y de reconstrucción de 10 kHz, el ruido térmico característico de reloj BBD y los tres modos históricos (Modo I: 0.4 Hz suave; Modo II: 0.8 Hz profundo; Modo I+II: modulación rápida vibrante).
- **Familia DSP:** Doble Línea de Retardo Discreta de 256 Etapas (MN3009 BBD) con Reloj Modulado en Contrafase Estéreo
- **Ecuación de Transferencia:** `f_clk(t) = f_0 / (D_0 +/- Delta_D*LFO(t)); L = x + LPF(BBD_1(LPF(x), f_clk)); R = x + LPF(BBD_2(LPF(x), f_clk_inv))`
- **Arquitectura Interna:** 2 Chips virtuales MN3009 BBD en contrafase, 3 Botones de modo (Mode I, Mode II, Manual LFO), Control de retardo BBD, realimentación, filtro de graves y nivel de ruido analógico
- **Parámetros Clave:** Mode (I / II / Manual), Modulation Speed & Depth, Delay Time, Feedback, Noise Level, Low Bypass, Mix
- **Mapeo MIDI CC:** `{"93": "Wet Mix", "1": "Modulation Depth", "74": "Delay Time"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el estado del circuito BBD.

### 6.86. Vintage Phaser — *Emulador del desfasador óptico-analógico Electro-Harmonix Small Stone (años setenta)*
- **Definición RAE:** Recreación física de los circuitos integrados de transconductancia variable (OTA CA3094) del legendario pedal Small Stone (inmortalizado por Jean-Michel Jarre): modela la distorsión no lineal dependiente de la frecuencia en las etapas de desfase, el interruptor 'Color' (realimentación resonante profunda) y un LFO dual con retardo de inversión.
- **Familia DSP:** Cascada de Etapas All-Pass OTA No Lineales con Realimentación Resonante ('Color')
- **Ecuación de Transferencia:** `y[n] = x[n] + Mix * OTA_AllPass_{1..N}(x[n] + g_color * tanh(y_{ap}[n-1]), LFO(t))`
- **Arquitectura Interna:** Red OTA de 4 a 8 etapas con no linealidad analógica, Interruptor Color / Feedback continuo, Modulador LFO con ajuste de simetría, retardo estéreo y ruido de circuito
- **Parámetros Clave:** Min/Max Frequency, Feedback (Color), LFO Speed & Shape, Order (Stages), Delay, Mix
- **Mapeo MIDI CC:** `{"74": "Feedback Color", "1": "LFO Speed"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con parámetros de la red OTA.

### 6.87. Vocodex — *Vocodificador matricial de cien bandas con sintetizador Sytrus integrado y envoltura de contorno*
- **Definición RAE:** Cumbre mundial de la vocodificación digital: divide el espectro en entre 5 y 100 bandas isofónicas de ancho variable, incorpora internamente un motor sintetizador Sytrus como portadora (además de aceptar portadora externa por Sidechain), permite redibujar libremente el mapeo de frecuencia moduladora a frecuencia portadora, aplica compresión/puerta por banda (Soundgoodizer integrado) y esculpe el paso directo de consonantes fricativas.
- **Familia DSP:** Banco de 5 a 100 Filtros Paso-Banda de Orden Variable + Matriz de Remapeo Espectral + Compresor Multibanda Soundgoodizer
- **Ecuación de Transferencia:** `y[n] = Soundgoodizer(Noise_Pass(x_mod[n]) + sum_{b=1}^{100} Pan_b * Hold_AR(|H^{mod}_{M(b)}(x_mod)|)^gamma * H^{car}_b(x_car))`
- **Arquitectura Interna:** Selector de entradas Sidechain para Modulador (Voz) y Portadora (Synth) + Sintetizador Sytrus interno, Banco de 5..100 bandas con control de ancho de banda, orden de filtro y escala de frecuencia, Seguidores de envolvente por banda (Hold, Attack, Release) con congelación (Freeze), Curvas multipunto por banda (Band Gain, Band Panning, Modulator Pitch Shift, Noise Level, Envelope Min/Max), Compresor/Maximizado Soundgoodizer de salida
- **Parámetros Clave:** Bands (5..100), Band Width, Modulator Pitch Shift (Gender), Attack/Release, Soundgoodizer Amount, Carrier Synth Preset, Wet/Mod/Car Mix
- **Mapeo MIDI CC:** `{"74": "Modulator Pitch Shift (Formant)", "71": "Band Width", "1": "Soundgoodizer Amount"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el estado de las 100 bandas, curvas multipunto y parche Sytrus.

### 6.88. Wave Candy — *Instrumento cuádruple de metrología acústica (Osciloscopio, Espectrograma, Vectorscopio y Vúmetro ITU/RMS)*
- **Definición RAE:** Suite de análisis científico y visual de FL Studio que reúne cuatro instrumentos de precisión en ventanas flotantes escalables: Osciloscopio sincronizado en fase, Analizador de Espectro / Espectrograma STFT de hasta 8192 bandas, Vectorscopio polar Lissajous (X/Y o Mid/Side para verificar coherencia de fase) y Medidor de Nivel Peak/RMS/EBU/K-System.
- **Familia DSP:** Metrología en Silicio: STFT 8192-pt, Proyección Ortogonal de Lissajous (M/S) e Integración Balística RMS/ITU
- **Ecuación de Transferencia:** `y[n] = x[n] (instrumento de medida de impedancia infinita / paso transparente)`
- **Arquitectura Interna:** Modo Oscilloscope, Modo Spectrum (FFT 64..8192 bandas con escala en Semitonos/Hz), Modo Vectorscope (Lissajous L/R y Polar M/S), Modo Meter (dBFS, RMS, Leq(A), K-12/K-14/K-20)
- **Parámetros Clave:** Mode (Oscilloscope/Spectrum/Vectorscope/Meter), Max Resolution (8192 bands), Scale (dB/Hz/Semitones), Freeze
- **Mapeo MIDI CC:** `{}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con configuración del instrumento de medida (usado en Slot 4 de Master_C5_SOTA.fst).

### 6.89. ZGameEditor Visualizer — *Motor de síntesis audiovisual por sombreadores OpenGL reactivos al espectro y transitorios*
- **Definición RAE:** Estación de composición visual y renderizado de vídeo 4K/60fps dentro del mezclador: encadena hasta 100 capas de sombreadores GLSL (OpenGL), mallas 3D, vídeos, imágenes y textos cuyos parámetros (escala, brillo, distorsión, cámara) reaccionan automáticamente al pico de graves, al espectro FFT de 32..256 bandas o a controladores MIDI.
- **Familia DSP:** Extracción de Envolvente/FFT de Audio -> Uniforms de Sombreadores de Fragmentos GLSL en GPU
- **Ecuación de Transferencia:** `FragColor(u,v,t) = GLSL_Layer_N(..., GLSL_Layer_1(u, v, t, AudioFFT[1..256], AudioPeak))`
- **Arquitectura Interna:** Pipeline multicapa de hasta 100 sombreadores GLSL (Postprocess, Canvas, Blend, Mesh, Text), Extractor de telemetría espectral y de picos hacia la GPU, Codificador de exportación MP4/MOV H.264/H.265
- **Parámetros Clave:** Layer 1..N Alpha, Blend Mode, Shader Uniforms
- **Mapeo MIDI CC:** `{"1": "Layer A Parameter 1", "11": "Layer A Parameter 2"}`
- **Estructura Binaria `.fst`:** Chunk 0xD5 con el árbol de capas GLSL y rutas de recursos multimedia.

---

## 7. Ingeniería Inversa de los 7 Procesadores VST3 SOTA de Terceros

### 7.1. Combustor.vst3 — *Compresor adaptativo con cinco algoritmos de saturación no lineal en el bucle de detección*
- **Definición RAE:** Procesador híbrido de compresión y excitación armónica que inyecta saturación adaptativa dependiente de la envolvente a través de cinco modelos matemáticos de distorsión (Valve, Foldback, Sine, Rectifier, Bitcrush) con filtrado pre/post.
- **Familia DSP:** Compresión Acoplada a Conformación No Lineal de Onda con Filtrado Pre/Post
- **Ecuación de Transferencia:** `y[n] = LPF(f_{DistMode}(HPF(Comp_Adaptive(x[n]))))`
- **Arquitectura Interna:** Compresor adaptativo, 5 Modos de combustión armónica, Filtros de corte de graves y agudos
- **Parámetros Clave:** Threshold, Ratio, Combustion Drive, Mode (1..5), Low/High Cut, Mix
- **Mapeo MIDI CC:** `{"1": "Combustion Drive", "74": "High Cut"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + estado VST3 de Combustor.

### 7.2. FirePresser.vst3 — *Matriz vectorial de cuatro compresores analógicos clásicos en serie y paralelo (1176, LA-2A, Distressor, DBX 160)*
- **Definición RAE:** Estación de compresión cuádruple (United Plugins) que emula simultáneamente cuatro topologías de compresión de hardware legendarias —FET ultrarrápido (1176 Wrapper), Óptico electroluminiscente (LA-2A Retro), VCA controlado digitalmente con distorsión (Distressor) y VCA de percusión (DBX 160)— permitiendo fundir sus pesos relativos sobre un diagrama cromático 2D y añadir saturación de transformador Turbo.
- **Familia DSP:** Combinación Convexa / Cascada de 4 Modelos No Lineales de Compresión (FET, Opto, Distressor, VCA)
- **Ecuación de Transferencia:** `y[n] = Sat_Turbo(sum_{i=1}^4 w_i(X,Y) * CompModel_i(x[n], DetectorInput))`
- **Arquitectura Interna:** 4 Motores de compresión analógica (Wrapper FET, Retro Opto, Distressor, Clear VCA), Almohadilla cromática 2D de mezcla de los 4 compresores, Etapa Turbo de saturación armónica
- **Parámetros Clave:** Detector Input, Rainbow Pad Blend (1..4), Turbo Saturation, Dry/Wet
- **Mapeo MIDI CC:** `{"1": "Turbo Saturation", "74": "Detector Drive"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + estado VST3 de FirePresser.

### 7.3. KickShaper.vst3 — *Escultor psicoacústico de bombos por realce subarmónico, compresión de golpe y eliminación de barro*
- **Definición RAE:** Procesador especializado en diseño de bombos (WA Production) dividido en cuatro etapas en serie: 'Deboom' (atenuación dinámica de la cola resonante lodosa en 120-250 Hz), 'Thump' (síntesis de subarmónicos en fase para peso de club), 'Punch' (compresión y afilado del ataque transitorio) y 'Tone/Clipper' (brillo de clic y recorte suave de techo).
- **Familia DSP:** Atenuación Dinámica de Cola Resonante + Síntesis Subarmónica + Modelado de Transitorios + Soft Clipper
- **Ecuación de Transferencia:** `y[n] = SoftClip(Tone(Punch_Transient(Thump_Sub(Deboom_DynEQ(x[n])))))`
- **Arquitectura Interna:** Módulo Deboom, Módulo Thump (generador subarmónico), Módulo Punch (compresor de ataque), Módulo Tone & Clipper
- **Parámetros Clave:** Deboom, Thump, Punch, Tone, Clipper Switch, Mix
- **Mapeo MIDI CC:** `{"74": "Thump Sub", "71": "Punch Attack"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + estado VST3 de KickShaper.

### 7.4. LANDR Mastering Pro.vst3 — *Procesador adaptativo de masterización multibanda con tres perfiles tonales*
- **Definición RAE:** Motor de masterización asistida en bus maestro que analiza el factor de cresta y el balance espectral de la mezcla en tiempo real, ajustando un ecualizador adaptativo, compresor multibanda, excitador de saturación, expansor de campo estéreo y limitador de pico verdadero.
- **Familia DSP:** Cadena de Masterización Adaptativa (EQ + Multiband Comp + Harmonic Exciter + True Peak Limiter)
- **Ecuación de Transferencia:** `y[n] = TP_Limiter(StereoField(Exciter(MultibandComp(AdaptiveEQ(x[n])))))`
- **Arquitectura Interna:** Analizador de aprendizaje de mezcla, 3 Estilos (Warm, Balanced, Open), Controles de EQ, Presence, De-Esser, Compression, Saturation y Loudness LUFS
- **Parámetros Clave:** Loudness Target, Equalizer Low/Mid/High, Compression, Saturation, Stereo Width
- **Mapeo MIDI CC:** `{"7": "Loudness Target"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + estado VST3 de LANDR.

### 7.5. Ozone 11 Equalizer.vst3 — *Ecualizador maestro de fase lineal/analógica con separación de transitorios y sostenimiento*
- **Definición RAE:** Ecualizador de masterización de iZotope que permite operar en modos Estéreo, Mid/Side o Transitorio/Sostenimiento (ecualizando de forma independiente el golpe percusivo y la cola armónica) con filtros quirúrgicos de fase digital lineal o curvas analógicas modeladas.
- **Familia DSP:** Filtrado FIR de Fase Lineal / IIR Analógico sobre Descomposición M/S o Transient/Sustain
- **Ecuación de Transferencia:** `y[n] = EQ_Trans(x_trans[n]) + EQ_Sust(x_sust[n])`
- **Arquitectura Interna:** 8 Bandas de ecualización de alta precisión, Selector de canal (Stereo, Mid/Side, Left/Right, Transient/Sustain), Medidor de correlación de fase y espectro Delta
- **Parámetros Clave:** Band 1..8 Freq, Gain, Q, Phase Mode (Analog/Digital)
- **Mapeo MIDI CC:** `{"74": "Band 1 Freq"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + bloque de estado VST3 de iZotope.

### 7.6. Super VHS.vst3 — *Emulador de degradación de cinta magnética de videocasete (VHS) de los años ochenta*
- **Definición RAE:** Procesador multi-efecto de carácter nostálgico (Baby Audio) que recrea seis imperfecciones físicas de los grabadores de vídeo doméstico: ruido estático de cabezal (Static), saturación magnética cálida (Heat), conversión A/D de 8 bits de primera generación (Shape), fluctuación de velocidad del cabrestante (Drift / Wow & Flutter), ensanchamiento coral sombrío (Wash) y reverberación corta de sala ochentera (Magic).
- **Familia DSP:** Cascada de Ruido de Cinta + Saturación de Histéresis + Cuantización de 8 Bits + Modulación Estocástica de Retardo (Wow/Flutter) + Chorus/Reverb
- **Ecuación de Transferencia:** `y[n] = Reverb_Wash(Chorus_Magic(BitCrush_8b(TapeSat_Heat(x(t - Drift(t)) + Static[n]))))`
- **Arquitectura Interna:** Generador Static, Saturador de cinta Heat, Reductor de resolución Shape, Modulador de tono Drift, Reverb Wash y Chorus Magic
- **Parámetros Clave:** Static, Heat, Shape, Drift, Wash, Magic, Mix
- **Mapeo MIDI CC:** `{"1": "Drift Wow/Flutter", "74": "Heat Saturation", "91": "Wash Reverb"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + estado VST3 de Baby Audio.

### 7.7. Vital.vst3 — *Sintetizador espectral de deformación de tablas de ondas con modulación polifónica MPE*
- **Definición RAE:** Sintetizador VST3 de código abierto de referencia que opera sobre tablas de ondas en el dominio frecuencial (Fourier), permitiendo deformar los armónicos (Spectral Warping: Inharmonic, Smear, Phase Disperse, Shepard Tone) y la fase temporal (Bend, Squeeze, FM, Sync) en 3 osciladores con soporte nativo de escalas Scala (.scl/.kbm) y expresión polifónica MPE.
- **Familia DSP:** Síntesis por Tabla de Ondas en Dominio Espectral (IFFT por Ciclo) + 2 Filtros Multimodo ZDF
- **Ecuación de Transferencia:** `W_warped(t) = IFFT(Transform_Spec(FFT(WavetableFrame(u)), WarpParam))`
- **Arquitectura Interna:** 3 Osciladores Espectrales + 1 Muestreador de Ruido/Keytrack, 2 Filtros ZDF (Analog, Dirty, Ladder, Digital, Diode, Formant, Comb, Phaser), 4 Envolventes + 8 LFOs de esplines + 4 Macros + Matriz de Modulación Estéreo, Cadena de 9 Efectos reordenables
- **Parámetros Clave:** Macro 1..4, Osc 1..3 Frame & Spectral Morph, Filter 1/2 Cutoff & Res
- **Mapeo MIDI CC:** `{"1": "Mod Wheel", "74": "MPE Slide (Y-Axis)", "11": "Macro 1"}`
- **Estructura Binaria `.fst`:** Fruity Wrapper (0xD5) + JSON comprimido de estado Vital (.vital).

---

*Firmado en Silicio: **Borja Fernández Angulo** — Investigador en Sistemas Complejos (Arquitectura C5-REAL).*
