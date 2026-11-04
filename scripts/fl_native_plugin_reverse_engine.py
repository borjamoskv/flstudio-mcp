#!/usr/bin/env python3
"""RAE documentation catalog and native plugin filename inventory.

The 147 descriptions are authored catalog entries, not results of algorithm
verification. Directory discovery cannot establish DSP behavior or equivalence.
"""

import json
import os
from typing import Any, Dict, List

FL_APP_PATH = "/Applications/FL Studio 2025.app/Contents/Resources/FL/Plugins/Fruity"
WORKSPACE_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")
OUTPUT_JSON_PATH = os.path.join(WORKSPACE_DIR, "samples/fl_native_plugins_reverse_matrix.json")
OUTPUT_MD_PATH = os.path.join(WORKSPACE_DIR, "docs/fl_studio_complete_rae_reverse_engineering.md")

# -----------------------------------------------------------------------------
# 1. DICCIONARIO LÉXICO RAE DE INGENIERÍA ACÚSTICA Y DSP (35 TÉRMINOS)
# -----------------------------------------------------------------------------
RAE_ACOUSTIC_LEXICON: Dict[str, Dict[str, str]] = {
    "DAW (Digital Audio Workstation)": {
        "termino_rae": "Estación de trabajo de audio digital",
        "acepcion_rae": "Del lat. statio ('puesto') y audio ('oír'). Sistema informático integral dedicado a la grabación, síntesis, edición, mezcla y masterización de señales sonoras discretizadas.",
        "invariante_fisica": "Muestreo uniforme regido por el Teorema de Nyquist-Shannon (fs >= 2 * f_max, canónicamente 48 kHz / coma flotante de 32/64 bits)."
    },
    "Plugin": {
        "termino_rae": "Complemento o módulo enchufable de procesamiento",
        "acepcion_rae": "De complementar ('dar perfección o añadir una función'). Biblioteca dinámica (Mach-O .dylib / bundle en macOS) que se acopla al bucle de audio del anfitrión.",
        "invariante_fisica": "Función de transformación de bloques de muestras x[n] -> y[n] acotada por el plazo temporal del búfer (L / fs segundos)."
    },
    "Wrapper": {
        "termino_rae": "Envoltorio o adaptador de interfaz binaria",
        "acepcion_rae": "De envolver ('rodear o recubrir'). Capa traductora que encapsula protocolos externos (VST3, Audio Units, CLAP) dentro del bus propietario de eventos de FL Studio.",
        "invariante_fisica": "Traducción biyectiva de buffers de audio, colas de eventos MIDI 1.0/2.0 y bloques opacos de estado (Chunk 0xD5)."
    },
    "Clipper (Soft Clipper)": {
        "termino_rae": "Recortador de cresta por saturación tangencial",
        "acepcion_rae": "De recortar ('cortar o cercenar lo que sobra'). Dispositivo no lineal sin memoria que limita la excursión instantánea de la onda redondeando sus picos.",
        "invariante_fisica": "y[n] = x[n] para |x| <= T; T + (1-T)*tanh((|x|-T)/(1-T))*sgn(x) para |x| > T."
    },
    "Limiter (True Peak Brickwall)": {
        "termino_rae": "Limitador de muro infranqueable de pico verdadero",
        "acepcion_rae": "De limitar ('fijar la extensión máxima'). Regulador dinámico con anticipación temporal (lookahead) y sobremuestreo polifásico que impide rebasar un techo de amplitud.",
        "invariante_fisica": "Sobremuestreo 4x/8x por filtro FIR polifásico seguido de atenuación de envolvente con ataque anticipado tau_a."
    },
    "Sidechain (Ducking)": {
        "termino_rae": "Modulación por cadena lateral (agachamiento dinámico)",
        "acepcion_rae": "De cadena ('sucesión de eslabones') y lateral. Control de la ganancia o banda espectral de una señal subordinada mediante la envolvente energética de una señal rectora (ej. bombo).",
        "invariante_fisica": "g[n] = (1 + exp(k * (E_ext[n] - T)))^-1; atenúa el bajo cuando irrumpe el transitorio del bombo."
    },
    "Compressor": {
        "termino_rae": "Compresor de margen dinámico",
        "acepcion_rae": "Del lat. compressor ('que oprime o reduce volumen'). Atenuador automático cuya ganancia decrece cuando la energía de entrada supera un umbral fijado.",
        "invariante_fisica": "En decibelios: Y_dB = T + (X_dB - T) / R para X_dB > T, gobernado por constantes de tiempo de ataque y relajación."
    },
    "Reverb (Reverberation)": {
        "termino_rae": "Reverberador acústico (persistencia sonora)",
        "acepcion_rae": "Del lat. reverberare ('repercutir o rebotar'). Persistencia del sonido en un recinto cerrado tras extinguirse la fuente, por reflexiones múltiples en sus paramentos.",
        "invariante_fisica": "Convolución y[n] = (x * h)[n] o red de retardo realimentada (FDN) con tiempo de caída Sabine RT60 = 0.161 * V / A."
    },
    "Delay": {
        "termino_rae": "Línea de retardo y eco realimentado",
        "acepcion_rae": "De retardar ('diferir o detener'). Repetición discreta de una señal tras un intervalo temporal sincronizado o libre, con realimentación amortiguada.",
        "invariante_fisica": "y[n] = x[n] + g * H_lp(z) * y[n - D], donde D = round(fs * 60 / BPM * fraccion)."
    },
    "Chorus": {
        "termino_rae": "Multiplicador coral por retardo modulado",
        "acepcion_rae": "Del lat. chorus ('conjunto de voces'). Efecto que simula la ejecución simultánea de varias fuentes mediante líneas de retardo (15-35 ms) moduladas en fase.",
        "invariante_fisica": "y[n] = x[n] + sum_k a_k * x(n - D_k - m_k * sin(2*pi*f_k*n/fs))."
    },
    "Flanger": {
        "termino_rae": "Rebordeador de peine por retardo corto modulado",
        "acepcion_rae": "De rebordear ('rozar la pestaña o reborde de un carrete magnético'). Filtro de peine variable originado al sumar una señal con una copia retardada entre 0.5 y 10 ms.",
        "invariante_fisica": "H(z) = 1 + g * z^(-D(n)), generando muescas armónicas equiespaciadas en frecuencia."
    },
    "Phaser": {
        "termino_rae": "Desfasador por cascada de filtros paso-todo",
        "acepcion_rae": "De desfasar ('alterar la diferencia de fase'). Procesador que rota la fase espectral mediante etapas paso-todo de primer orden y las suma a la señal directa.",
        "invariante_fisica": "H(z) = 1 + g * prod_{k=1}^M ((a_k(n) + z^-1) / (1 + a_k(n)*z^-1))."
    },
    "Vocoder": {
        "termino_rae": "Codificador e improntador de envolvente vocal",
        "acepcion_rae": "Acrónimo de voice coder ('codificador de voz'). Analizador-sintetizador que extrae la envolvente espectral de un modulador (voz) en N bandas y la impone a una portadora.",
        "invariante_fisica": "y[n] = sum_{b=1}^B Env(|h_b * x_mod|[n]) * (h_b * x_car)[n]."
    },
    "Wavetable Synthesis": {
        "termino_rae": "Síntesis por barrido de tabla de ondas",
        "acepcion_rae": "De síntesis ('composición de un todo') y tabla. Generación sonora por lectura periódica e interpolación bilineal entre ciclos de onda almacenados en una matriz.",
        "invariante_fisica": "y[n] = (1 - alpha)*W[k, phi[n]] + alpha*W[k+1, phi[n]]."
    },
    "FM Synthesis": {
        "termino_rae": "Síntesis por modulación de frecuencia (y fase)",
        "acepcion_rae": "Alteración instantánea de la frecuencia o fase de un oscilador portador mediante la salida de uno o varios osciladores moduladores (algoritmo de Chowning).",
        "invariante_fisica": "y(t) = A * sin(w_c * t + I * sin(w_m * t)) = A * sum_{k=-inf}^{inf} J_k(I) * sin((w_c + k*w_m)*t)."
    },
    "Additive / Resynthesis": {
        "termino_rae": "Síntesis aditiva y resíntesis espectral",
        "acepcion_rae": "Reconstrucción de cualquier timbre complejo mediante la superposición de parciales sinusoidales cuya amplitud y frecuencia evolucionan en el tiempo (Teorema de Fourier).",
        "invariante_fisica": "y(t) = sum_{k=1}^K A_k(t) * sin(integral(w_k(tau) dtau) + phi_k)."
    },
    "Granular Synthesis": {
        "termino_rae": "Síntesis corpuscular o granular",
        "acepcion_rae": "Del lat. granulum ('grano pequeño'). Atomización del sonido en micro-fragmentos acústicos (10-100 ms) envueltos por una ventana acampanada y reordenados estocásticamente.",
        "invariante_fisica": "y[n] = sum_g w((n - n_g)/L_g) * s[p_g + (n - n_g)*r_g]."
    },
    "Physical Modeling (Waveguide)": {
        "termino_rae": "Modelado físico por guía de ondas digital",
        "acepcion_rae": "Simulación numérica de las ecuaciones diferenciales de cuerdas tensas, membranas, placas o tubos acústicos (algoritmos de Karplus-Strong y Julius O. Smith).",
        "invariante_fisica": "d^2 u / dt^2 = c^2 * d^2 u / dx^2 resuelta mediante dos líneas de retardo bidireccionales acopladas a un filtro de pérdidas."
    },
    "Linear Phase EQ": {
        "termino_rae": "Ecualizador de fase lineal (retardo de grupo constante)",
        "acepcion_rae": "De igualar ('ajustar el balance frecuencial'). Filtro de respuesta finita al impulso (FIR) con coeficientes simétricos que altera la magnitud sin rotar la fase relativa.",
        "invariante_fisica": "h[n] = h[N - 1 - n] => Retardo de grupo tau_g(w) = (N - 1) / 2 constante en todo el espectro."
    },
    "Mid/Side (M/S) Processing": {
        "termino_rae": "Codificación y procesamiento Suma/Diferencia (Centro/Lateral)",
        "acepcion_rae": "Descomposición ortogonal de un par estereofónico (Izquierda/Derecha) en una componente monofónica central (Suma) y una componente diferencial periférica (Lateral).",
        "invariante_fisica": "M = (L + R)/2, S = (L - R)/2; reconstrucción exacta L = M + S, R = M - S (matriz de Hadamard 2x2)."
    },
    "Transient Shaper": {
        "termino_rae": "Escultor diferencial de transitorios y cola",
        "acepcion_rae": "Del lat. transitorius ('pasajero, ataque fugaz'). Procesador que discrimina el ataque percusivo del sostenimiento comparando dos seguidores de envolvente (rápido y lento).",
        "invariante_fisica": "Delta_E[n] = Env_fast[n] - Env_slow[n]; modula la ganancia según el signo y magnitud de Delta_E[n]."
    },
    "Waveshaper": {
        "termino_rae": "Conformador no lineal de onda por polinomios o curvas",
        "acepcion_rae": "De conformar ('dar forma'). Función estática f(x) aplicada muestra a muestra para inyectar armónicos pares (asimétrica) o impares (simétrica, polinomios de Chebyshev).",
        "invariante_fisica": "y[n] = sum_k c_k * T_k(x[n]), donde T_k(cos(theta)) = cos(k*theta)."
    },
    "Dithering (TPDF)": {
        "termino_rae": "Tremolado estocástico de recuantización (TPDF)",
        "acepcion_rae": "Inyección de ruido aleatorio de densidad triangular de media nula y amplitud 1 LSB antes de truncar la profundidad de bits, transformando distorsión no lineal en piso de ruido blanco.",
        "invariante_fisica": "y_q[n] = Q_Delta(x[n] + u_1[n] - u_2[n]), con u_1, u_2 ~ U(-Delta/2, Delta/2)."
    },
    "Convolution": {
        "termino_rae": "Convolución por respuesta al impulso",
        "acepcion_rae": "Del lat. convolvere ('enrollar juntos'). Operador integral lineal e invariante en el tiempo que imprime la huella acústica de un recinto o aparato físico sobre cualquier señal.",
        "invariante_fisica": "y[n] = sum_k x[k]*h[n-k] = IFFT(FFT(x) * FFT(h)) mediante particionado sin latencia."
    },
    "Pitch Bend / Microtonality": {
        "termino_rae": "Inflexión continua de altura tonal y microtonalidad",
        "acepcion_rae": "Desviación fina de la frecuencia fundamental respecto al temperamento igual de 12 semitonos (12-TET), expresada en centésimas de semitono (cents).",
        "invariante_fisica": "f = f_0 * 2^(Delta_cents / 1200); en MIDI 14-bit: val = 8192 + round(8192 * Delta_cents / Rango_cents)."
    },
    "Formant": {
        "termino_rae": "Formante o pico de resonancia del tracto acústico",
        "acepcion_rae": "De formar. Cada una de las regiones de concentración de energía espectral (F1, F2, F3) que determinan el timbre vocálico con independencia de la nota fundamental.",
        "invariante_fisica": "Polos complejos conjugados del filtro del tracto vocal H(z) = G / prod_{k=1}^M (1 - 2*r_k*cos(w_k)*z^-1 + r_k^2*z^-2)."
    },
    "Crest Factor": {
        "termino_rae": "Factor de cresta (relación pico a valor eficaz)",
        "acepcion_rae": "De cresta ('cima de una onda'). Cociente logarítmico entre la amplitud máxima absoluta de una señal y su valor cuadrático medio (RMS), indicador de vitalidad dinámica.",
        "invariante_fisica": "CF_dB = 20 * log10(max|x[n]| / sqrt(mean(x[n]^2)))."
    },
    "Spectral Flatness (Wiener Entropy)": {
        "termino_rae": "Planitud espectral (entropía de Wiener)",
        "acepcion_rae": "Cociente entre la media geométrica y la media aritmética del espectro de potencia; distingue tonos puros (cercano a 0) del ruido blanco o barro espectral (cercano a 1).",
        "invariante_fisica": "SFM = exp((1/K)*sum ln S[k]) / ((1/K)*sum S[k])."
    },
    "Plugin Delay Compensation (PDC)": {
        "termino_rae": "Compensación automática de retardo de inserción",
        "acepcion_rae": "Alineación temporal del grafo del mezclador mediante inserción de retardos de igualación en las ramas paralelas para neutralizar la latencia de filtros FIR o lookahead.",
        "invariante_fisica": "Para cada ruta r hacia el nodo sumador: D_comp(r) = max_j L(j) - L(r)."
    },
    "Step Sequencer / Channel Rack": {
        "termino_rae": "Secuenciador por pasos y bastidor de canales",
        "acepcion_rae": "De secuencia ('sucesión ordenada'). Matriz discreta de disparo rítmico cuantizada en subdivisiones de compás (1/16 de nota) que aloja todos los instrumentos del proyecto.",
        "invariante_fisica": "Disparo de eventos en instantes t_k = k * (60 / (BPM * 4)) + delta_swing."
    },
    "Piano Roll": {
        "termino_rae": "Rollo de pianola o matriz bidimensional tiempo-altura",
        "acepcion_rae": "Representación cartesiana donde el eje de abscisas mide el tiempo en pulsos por negra (PPQ) y el de ordenadas la altura tonal y propiedades por nota (velocidad, paneo, corte).",
        "invariante_fisica": "Resolución temporal de 96 a 960 PPQ; estructura binaria de 24 bytes por nota en el evento FLdt 0xEE."
    },
    "Playlist": {
        "termino_rae": "Lienzo de estructura macro-temporal (partitura general)",
        "acepcion_rae": "Espacio de montaje lineal donde se disponen patrones musicales, fragmentos de audio y curvas de automatización a lo largo de la duración de la obra.",
        "invariante_fisica": "Grafo temporal de eventos de clip codificados en el bloque binario FLdt 0xEC."
    },
    "Patcher": {
        "termino_rae": "Entorno modular de interconexión en grafo dirigido (DAG)",
        "acepcion_rae": "De parchear ('conectar mediante latiguillos'). Sub-anfitrión nodal que permite enrutar señales de audio, notas MIDI y parámetros de control en paralelo o serie arbitraria.",
        "invariante_fisica": "Evaluación topológica sin ciclos (o con retardo de 1 bloque en realimentación) de sub-nodos generadores y efectos."
    },
    "Automation Clip": {
        "termino_rae": "Curva de automatización paramétrica por esplines",
        "acepcion_rae": "De automático. Función continua definida a trozos mediante puntos de control y tensiones no lineales que gobierna la evolución temporal de cualquier parámetro del sistema.",
        "invariante_fisica": "Interpolación entre nodos (t_i, v_i) con exponente de tensión tau: u' = u^(2^tau) o 1 - (1-u)^(2^-tau)."
    },
    "LUFS (Loudness Units Full Scale)": {
        "termino_rae": "Unidades de sonoridad referidas al fondo de escala (ITU-R BS.1770)",
        "acepcion_rae": "Medida psicoacústica normalizada del volumen percibido por el oído humano tras aplicar ponderación frecuencial en K (pre-énfasis cefálico y filtro paso-alto RLB).",
        "invariante_fisica": "LUFS = -0.691 + 10 * log10(sum_i G_i * z_i), con compuerta absoluta a -70 LUFS y relativa a -10 LU."
    }
}

# -----------------------------------------------------------------------------
# 2. ARQUITECTURA NUCLEAR DE FL STUDIO 2025 (8 SUBSISTEMAS CORE RAE)
# -----------------------------------------------------------------------------
FL_CORE_ARCHITECTURE_RAE: Dict[str, Dict[str, Any]] = {
    "FLhd_FLdt_Binary_Protocol": {
        "termino_rae": "Protocolo Binario de Flujo de Eventos FLhd/FLdt",
        "definicion_rae": "Formato contenedor propietario basado en cabecera fija de 14 octetos ('FLhd') seguida de un bloque de flujo de eventos ('FLdt') codificado por identificador de evento y longitud variable (LEB128/VarLen).",
        "estructura_binaria": {
            "FLhd_Header_14B": "Magic 'FLhd' (4B) + Size=6 (uint32 LE) + FormatType (uint16 LE: 0=Project .flp, 16=Score .fsc, 64=Mixer .fst) + ChannelCount (uint16 LE) + PPQ (uint16 LE, default 96).",
            "FLdt_Chunk": "Magic 'FLdt' (4B) + ByteLength (uint32 LE) + Secuencia continua de eventos [EventID (1B) + Payload].",
            "Rangos_EventID": {
                "0..63 (0x00..0x3F)": "Eventos de 1 octeto (Byte / uint8).",
                "64..127 (0x40..0x7F)": "Eventos de 2 octetos (Word / uint16 LE).",
                "128..191 (0x80..0xBF)": "Eventos de 4 octetos (DWord / uint32 LE / float32).",
                "192..255 (0xC0..0xFF)": "Eventos de longitud variable (VarLen LEB128 + bloque de octetos/UTF-8/UTF-16LE)."
            }
        }
    },
    "Mixer_125_Insert_Engine": {
        "termino_rae": "Motor de Mezcla de 125 Canales de Inserción, 10 Ranuras y PDC",
        "definicion_rae": "Matriz de suma digital en coma flotante de 32 bits con 125 canales de inserción más canal Maestro, 10 ranuras de efectos por canal, ecualizador paramétrico de 3 bandas integrado, inversión de polaridad, permutación L/R, separación estereofónica M/S y compensación automática de retardo (PDC).",
        "ecuacion_dsp": "y_k[n] = G_fader * Pan(M_k[n] + alpha_sep * S_k[n]), con envíos post-fader S_{k->j} en grafo acíclico dirigido (DAG) validado contra ciclos de realimentación."
    },
    "Channel_Rack_and_Step_Sequencer": {
        "termino_rae": "Bastidor de Instrumentos, Secuenciador por Pasos y Ruteo Polifónico",
        "definicion_rae": "Contenedor central de generadores (sintetizadores, muestreadores y clips de audio/automatización) que despacha eventos de nota hacia cada instancia y encamina su salida de audio hacia uno de los 125 canales del mezclador.",
        "ecuacion_dsp": "Ganancia circular por defecto de -2.5 dB (factor 0.78 / ley de paneo circular) en el bastidor; t_step = k * (15 / BPM) + SwingOffset."
    },
    "Piano_Roll_and_Voice_Properties": {
        "termino_rae": "Matriz Bidimensional de Altura-Tiempo y Propiedades por Voz",
        "definicion_rae": "Secuenciador de alta resolución (96 a 960 PPQ) cuyas notas son objetos independientes de 24 octetos (Evento 0xEE) que portan modulación por voz: altura fina (pitch fine), corte de filtro (Mod X), resonancia (Mod Y), paneo por nota, velocidad de ataque y liberación, y notas de deslizamiento (slide/porta).",
        "estructura_binaria": "Struct 24B (<IIHHHHBBBBBBBB): Pos_Ticks(4B), Flags(4B), RackChan(2B), Length_Ticks(2B), Key_MIDI(2B), FinePitch(2B), Release(1B),MidiChan_SlideFlags(1B), Pan(1B), Velocity(1B), ModX_Cutoff(1B), ModY_Res(1B), Reserved(2B)."
    },
    "Playlist_and_Spline_Automation": {
        "termino_rae": "Lienzo Macro-Estructural y Motor de Automatización por Esplines de Tensión",
        "definicion_rae": "Secuenciador lineal de libre emplazamiento (hasta 500 pistas visuales) donde coexisten clips de patrón MIDI, clips de audio con estiramiento elástico (Zplane Elastique Pro v3) y clips de automatización continua.",
        "ecuacion_dsp": "Curva de tensión entre nodos (t_0, y_0) y (t_1, y_1): u = (t - t_0)/(t_1 - t_0); f(u, tau) = ((exp(k*u) - 1)/(exp(k) - 1)) para tensión exponencial continua."
    },
    "Patcher_and_VFX_Modular_DAG": {
        "termino_rae": "Sub-Anfitrión Modular en Grafo Acíclico Dirigido (Patcher) y Procesadores de Voz (VFX)",
        "definicion_rae": "Entorno de encapsulación topológica que permite construir instrumentos o cadenas de masterización complejas interconectando nodos de audio (cables amarillos), eventos de nota/voz (cables verdes) y parámetros de control (cables rojos).",
        "ecuacion_dsp": "Ordenación topológica de Kahn G=(V,E); soporta división frecuencial de fase lineal (Frequency Splitter) y remapeo microtonal en tiempo real (VFX Key Mapper / VFX Script)."
    },
    "Fruity_Wrapper_Plugin_Host": {
        "termino_rae": "Adaptador Universal de Complementos Externos (VST2 / VST3 / AU)",
        "definicion_rae": "Puente binario de aislamiento y traducción que aloja procesadores y sintetizadores de terceros en macOS ARM64, gestionando búferes de tamaño variable, tablas de 128 CC MIDI y serialización de estado en el evento 0xD5.",
        "estructura_binaria": "Evento 0xC9 ('Fruity Wrapper') + Evento 0xD5 (Cabecera de versión Wrapper + Ruta/UUID del plugin VST3/AU + Tamaño de estado + Volcado binario nativo del plugin)."
    },
    "FL_Cloud_TDR_Mastering_Engine": {
        "termino_rae": "Motor de Masterización Asistida de Ocho Etapas (Tokyo Dawn Records)",
        "definicion_rae": "Cadena determinista de masterización integrada en `/Contents/Resources/FL/System/Config/Master/references.txt` que encadena filtrado M/S, compresión de pegamento, ecualización dinámica multibanda, recorte suave y limitación de pico verdadero a 4x.",
        "ecuacion_dsp": "SlickEQ_M(HPF + MonoSub) -> Kotelnikov(RMS Glue) -> Nova_GE(3-Band DynEQ) -> SoftClipper(tanh) -> Limiter6_GE(4x Polyphase ISP Brickwall)."
    }
}

# -----------------------------------------------------------------------------
# 3. TABLA COMPLETA DE EVENTOS BINARIOS FLhd/FLdt (44 CÓDIGOS CANÓNICOS)
# -----------------------------------------------------------------------------
FL_EVENT_CODES: Dict[int, Dict[str, Any]] = {
    # Byte Events (0..63)
    0: {"id": 0, "hex": "0x00", "tipo": "Byte (uint8)", "nombre": "Byte_Enabled", "descripcion_rae": "Estado de activación o desvío (bypass) del canal o ranura (0=Inactivo, 1=Activo)."},
    1: {"id": 1, "hex": "0x01", "tipo": "Byte (uint8)", "nombre": "Byte_NoteOn", "descripcion_rae": "Activación de nota elemental en secuencias heredadas."},
    2: {"id": 2, "hex": "0x02", "tipo": "Byte (uint8)", "nombre": "Byte_Vol", "descripcion_rae": "Volumen de canal codificado en un octeto (0..128 nominal)."},
    3: {"id": 3, "hex": "0x03", "tipo": "Byte (uint8)", "nombre": "Byte_Pan", "descripcion_rae": "Posición panorámica (0=Izquierda extrema, 64=Centro, 128=Derecha extrema)."},
    4: {"id": 4, "hex": "0x04", "tipo": "Byte (uint8)", "nombre": "Byte_MIDIChan", "descripcion_rae": "Canal MIDI asignado (0..15)."},
    5: {"id": 5, "hex": "0x05", "tipo": "Byte (uint8)", "nombre": "Byte_MIDINote", "descripcion_rae": "Nota raíz MIDI de referencia (por defecto 60 = Do central C5 en FL)."},
    6: {"id": 6, "hex": "0x06", "tipo": "Byte (uint8)", "nombre": "Byte_MIDIPatch", "descripcion_rae": "Cambio de programa MIDI (Program Change 1..128)."},
    7: {"id": 7, "hex": "0x07", "tipo": "Byte (uint8)", "nombre": "Byte_MIDIBank", "descripcion_rae": "Selector de banco MIDI."},
    9: {"id": 9, "hex": "0x09", "tipo": "Byte (uint8)", "nombre": "Byte_LoopActive", "descripcion_rae": "Indicador de bucle de patrón activo (0/1)."},
    10: {"id": 10, "hex": "0x0A", "tipo": "Byte (uint8)", "nombre": "Byte_ShowInfo", "descripcion_rae": "Mostrar ventana de información al abrir el proyecto."},
    11: {"id": 11, "hex": "0x0B", "tipo": "Byte (uint8)", "nombre": "Byte_Shuffle", "descripcion_rae": "Cantidad de atresillamiento rítmico global (Swing / Shuffle 0..128)."},
    12: {"id": 12, "hex": "0x0C", "tipo": "Byte (uint8)", "nombre": "Byte_MainVol", "descripcion_rae": "Volumen maestro global del proyecto."},
    13: {"id": 13, "hex": "0x0D", "tipo": "Byte (uint8)", "nombre": "Byte_Stretch", "descripcion_rae": "Factor de estiramiento temporal de muestra."},
    14: {"id": 14, "hex": "0x0E", "tipo": "Byte (uint8)", "nombre": "Byte_Pitchable", "descripcion_rae": "Habilita transposición tonal de la muestra."},
    15: {"id": 15, "hex": "0x0F", "tipo": "Byte (uint8)", "nombre": "Byte_Zipped", "descripcion_rae": "Proyecto empaquetado en contenedor comprimido ZIP."},
    16: {"id": 16, "hex": "0x10", "tipo": "Byte (uint8)", "nombre": "Byte_Delay_Flags", "descripcion_rae": "Banderas del eco interno de canal."},
    17: {"id": 17, "hex": "0x11", "tipo": "Byte (uint8)", "nombre": "Byte_TimeSig_Num", "descripcion_rae": "Numerador del compás musical (ej. 4 en 4/4, 12 en Bulerías)."},
    18: {"id": 18, "hex": "0x12", "tipo": "Byte (uint8)", "nombre": "Byte_TimeSig_Beat", "descripcion_rae": "Denominador o subdivisión de pulso del compás."},
    19: {"id": 19, "hex": "0x13", "tipo": "Byte (uint8)", "nombre": "Byte_UseLoopPoints", "descripcion_rae": "Activa los puntos de bucle incrustados en el archivo WAV."},
    20: {"id": 20, "hex": "0x14", "tipo": "Byte (uint8)", "nombre": "Byte_LoopType", "descripcion_rae": "Modo de bucle de muestra (Adelante, Ping-Pong)."},
    21: {"id": 21, "hex": "0x15", "tipo": "Byte (uint8)", "nombre": "Byte_ChanType", "descripcion_rae": "Tipo de canal en el bastidor (0=Sampler, 2=Generator Plugin, 3=Layer, 4=AudioClip, 5=AutomationClip)."},
    22: {"id": 22, "hex": "0x16", "tipo": "Byte (uint8)", "nombre": "Byte_MixSliceNum", "descripcion_rae": "Canal de inserción del mezclador asignado al generador (0=Maestro, 1..125=Insertos)."},
    23: {"id": 23, "hex": "0x17", "tipo": "Byte (uint8)", "nombre": "Byte_EffectChannelMuted", "descripcion_rae": "Estado de silenciamiento (Mute) e inversión del canal de mezcla."},
    # Word Events (64..127)
    64: {"id": 64, "hex": "0x40", "tipo": "Word (uint16 LE)", "nombre": "Word_NewChan", "descripcion_rae": "Instancia un nuevo canal en el bastidor con su índice entero (0..N-1)."},
    65: {"id": 65, "hex": "0x41", "tipo": "Word (uint16 LE)", "nombre": "Word_NewPat", "descripcion_rae": "Abre la definición de un nuevo patrón musical (1..999)."},
    66: {"id": 66, "hex": "0x42", "tipo": "Word (uint16 LE)", "nombre": "Word_Tempo", "descripcion_rae": "Tempo entero heredado en pulsos por minuto (BPM)."},
    67: {"id": 67, "hex": "0x43", "tipo": "Word (uint16 LE)", "nombre": "Word_CurrentPatNum", "descripcion_rae": "Número del patrón actualmente seleccionado."},
    69: {"id": 69, "hex": "0x45", "tipo": "Word (uint16 LE)", "nombre": "Word_FX", "descripcion_rae": "Parámetro de efecto interno de canal."},
    70: {"id": 70, "hex": "0x46", "tipo": "Word (uint16 LE)", "nombre": "Word_Fade_Stereo", "descripcion_rae": "Banderas de fundido y fase estereofónica del muestreador."},
    71: {"id": 71, "hex": "0x47", "tipo": "Word (uint16 LE)", "nombre": "Word_CutOff", "descripcion_rae": "Frecuencia de corte del filtro interno del canal (0..1024)."},
    72: {"id": 72, "hex": "0x48", "tipo": "Word (uint16 LE)", "nombre": "Word_DotVol", "descripcion_rae": "Volumen por paso en el secuenciador."},
    73: {"id": 73, "hex": "0x49", "tipo": "Word (uint16 LE)", "nombre": "Word_DotPan", "descripcion_rae": "Paneo por paso en el secuenciador."},
    74: {"id": 74, "hex": "0x4A", "tipo": "Word (uint16 LE)", "nombre": "Word_PreAmp", "descripcion_rae": "Ganancia de preamplificación de muestra."},
    75: {"id": 75, "hex": "0x4B", "tipo": "Word (uint16 LE)", "nombre": "Word_Decay", "descripcion_rae": "Tiempo de caída (Decay) de la envolvente de muestra."},
    76: {"id": 76, "hex": "0x4C", "tipo": "Word (uint16 LE)", "nombre": "Word_Attack", "descripcion_rae": "Tiempo de ataque de la envolvente de muestra."},
    77: {"id": 77, "hex": "0x4D", "tipo": "Word (uint16 LE)", "nombre": "Word_DotNote", "descripcion_rae": "Altura tonal por paso en el secuenciador."},
    78: {"id": 78, "hex": "0x4E", "tipo": "Word (uint16 LE)", "nombre": "Word_DotPitch", "descripcion_rae": "Desplazamiento fino de tono por paso."},
    80: {"id": 80, "hex": "0x50", "tipo": "Word (uint16 LE)", "nombre": "Word_MainPitch", "descripcion_rae": "Transposición tonal maestra en cents (-1200..+1200)."},
    82: {"id": 82, "hex": "0x52", "tipo": "Word (uint16 LE)", "nombre": "Word_Resonance", "descripcion_rae": "Factor de calidad (Q / Resonancia) del filtro interno de canal."},
    # DWord Events (128..191)
    128: {"id": 128, "hex": "0x80", "tipo": "DWord (uint32 LE)", "nombre": "DWord_Color", "descripcion_rae": "Color RGB/BGR de 32 bits asignado al canal, pista o patrón."},
    129: {"id": 129, "hex": "0x81", "tipo": "DWord (uint32 LE)", "nombre": "DWord_PlayListItem", "descripcion_rae": "Elemento de patrón en la lista de reproducción (formato compacto)."},
    131: {"id": 131, "hex": "0x83", "tipo": "DWord (uint32 LE)", "nombre": "DWord_FXSine", "descripcion_rae": "Modulación sinusoidal de frecuencia graves del muestreador."},
    132: {"id": 132, "hex": "0x84", "tipo": "DWord (uint32 LE)", "nombre": "DWord_CutCutBy", "descripcion_rae": "Grupo de exclusión mutua de voces (Cut Self / Cut By) para hi-hats y bajos."},
    134: {"id": 134, "hex": "0x86", "tipo": "DWord (uint32 LE)", "nombre": "DWord_MiddleNote", "descripcion_rae": "Nota raíz con ajuste fino en formato de 32 bits."},
    146: {"id": 146, "hex": "0x92", "tipo": "DWord (uint32 LE)", "nombre": "DWord_DelayReso", "descripcion_rae": "Empaquetado de corte y resonancia del filtro de retardo."},
    147: {"id": 147, "hex": "0x93", "tipo": "DWord (uint32 LE)", "nombre": "DWord_Reverb", "descripcion_rae": "Parámetros de reverberación precalculada del muestreador."},
    148: {"id": 148, "hex": "0x94", "tipo": "DWord (uint32 LE)", "nombre": "DWord_StretchTime", "descripcion_rae": "Duración exacta de estiramiento temporal en ticks/milisegundos."},
    149: {"id": 149, "hex": "0x95", "tipo": "DWord (uint32 LE)", "nombre": "DWord_MixerIconColor", "descripcion_rae": "Icono y color de pista del mezclador."},
    156: {"id": 156, "hex": "0x9C", "tipo": "DWord (uint32 LE)", "nombre": "DWord_FineTempo", "descripcion_rae": "Tempo de alta precisión en milésimas de BPM (ej. 124000 = 124.000 BPM)."},
    # VarLen Events (192..255)
    192: {"id": 192, "hex": "0xC0", "tipo": "VarLen (String)", "nombre": "Text_ChanName", "descripcion_rae": "Nombre del canal de instrumento en el bastidor."},
    193: {"id": 193, "hex": "0xC1", "tipo": "VarLen (String)", "nombre": "Text_PatName", "descripcion_rae": "Nombre del patrón musical actual."},
    194: {"id": 194, "hex": "0xC2", "tipo": "VarLen (String)", "nombre": "Text_Title", "descripcion_rae": "Título de la obra o proyecto."},
    195: {"id": 195, "hex": "0xC3", "tipo": "VarLen (String)", "nombre": "Text_Comment", "descripcion_rae": "Comentarios y metadatos de autoría del proyecto."},
    196: {"id": 196, "hex": "0xC4", "tipo": "VarLen (String)", "nombre": "Text_SampleFileName", "descripcion_rae": "Ruta del archivo de audio (.wav/.flac/.mp3) cargado en el muestreador o clip."},
    197: {"id": 197, "hex": "0xC5", "tipo": "VarLen (String)", "nombre": "Text_URL", "descripcion_rae": "Enlace web asociado al proyecto."},
    199: {"id": 199, "hex": "0xC7", "tipo": "VarLen (String)", "nombre": "Text_Version", "descripcion_rae": "Cadena de versión del motor de FL Studio (ej. '24.1.0\\x00' o '25.0.0\\x00')."},
    201: {"id": 201, "hex": "0xC9", "tipo": "VarLen (String)", "nombre": "Text_PluginName", "descripcion_rae": "Nombre interno del complemento generador o efecto (ej. 'Sytrus', 'Maximus')."},
    203: {"id": 203, "hex": "0xCB", "tipo": "VarLen (String)", "nombre": "Text_Genre", "descripcion_rae": "Género musical declarado en los metadatos del proyecto."},
    204: {"id": 204, "hex": "0xCC", "tipo": "VarLen (String)", "nombre": "Text_MixerTrackName", "descripcion_rae": "Etiqueta de texto de un canal del mezclador o autor."},
    212: {"id": 212, "hex": "0xD4", "tipo": "VarLen (Struct 52B)", "nombre": "Data_PluginSlotRouting", "descripcion_rae": "Estructura de 52 octetos que define el índice de ranura (offset 4), activación (offset 8) y mezcla Dry/Wet (offset 16)."},
    213: {"id": 213, "hex": "0xD5", "tipo": "VarLen (Binary Blob)", "nombre": "Data_PluginStatePayload", "descripcion_rae": "Volcado binario del estado de parámetros de un plugin nativo o del envoltorio VST3/AU."},
    223: {"id": 223, "hex": "0xDF", "tipo": "VarLen (Binary Array)", "nombre": "Data_AutomationData", "descripcion_rae": "Puntos de control y tensiones de un clip de automatización."},
    224: {"id": 224, "hex": "0xE0", "tipo": "VarLen (Struct)", "nombre": "Data_ChanGroupName", "descripcion_rae": "Agrupación de filtro del bastidor de canales (ej. 'Audio', 'Automation', 'Unsorted')."},
    225: {"id": 225, "hex": "0xE1", "tipo": "VarLen (Struct 336B)", "nombre": "Data_MixerTrackStrip", "descripcion_rae": "Estado completo de una banda del mezclador (336 octetos: fader float32, separación estéreo, EQ de 3 bandas, matriz de envíos)."},
    227: {"id": 227, "hex": "0xE3", "tipo": "VarLen (Struct 164B)", "nombre": "Data_BasicChanParams", "descripcion_rae": "Parámetros básicos de envolvente AHDSR, LFO, filtro SVF y polifonía del canal."},
    236: {"id": 236, "hex": "0xEC", "tipo": "VarLen (Struct Array)", "nombre": "Data_PlaylistItems", "descripcion_rae": "Matriz de elementos posicionados en el lienzo de la Playlist (tick inicial, duración, pista, índice de patrón/clip)."},
    238: {"id": 238, "hex": "0xEE", "tipo": "VarLen (Struct N*24B)", "nombre": "Data_PianoRollNotes", "descripcion_rae": "Vector de notas del Piano Roll; cada nota ocupa exactamente 24 octetos."}
}

# -----------------------------------------------------------------------------
# 4. INGENIERÍA INVERSA RAE DE LOS 51 GENERADORES NATIVOS DE FL STUDIO 2025
# -----------------------------------------------------------------------------
GENERATORS_RAE_SPEC: Dict[str, Dict[str, Any]] = {
    "3x Osc": {
        "termino_rae": "Sintetizador sustractivo de tres osciladores acoplados",
        "definicion_rae": "Generador elemental de tres osciladores en serie/paralelo con desfase estereofónico, inversión de polaridad y modulación de amplitud (AM) del tercer oscilador por los dos primeros.",
        "familia_dsp": "Síntesis Sustractiva / Modulación en Anillo",
        "ecuacion_transferencia": "y[n] = SVF_LP(o_1[n] + g_2*o_2[n] + g_3*o_3[n] * (1 + alpha_AM*o_1[n]))",
        "arquitectura_interna": ["3 Osciladores multimodo (Senoidal, Triángulo, Sierra, Cuadrada, Ruido, Muestra)", "Desfase estéreo por oscilador", "Envolventes AHDSR + Filtro SVF del canal"],
        "parametros_clave": ["Coarse/Fine Pitch (1..3)", "Stereo Phase Offset", "Mix Level 2 & 3", "Osc 3 AM Mode"],
        "cc_mapping": {"74": "Cutoff SVF", "71": "Resonance SVF", "1": "Detune Depth"},
        "estructura_fst": "Chunk 0xD5 de 92 bytes (3 bloques de 24B de oscilador + 20B de banderas globales)."
    },
    "Autogun": {
        "termino_rae": "Generador aditivo-metálico de universo paramétrico indexado",
        "definicion_rae": "Sintetizador aditivo derivado del motor Ogun que explora 4.294.967.296 timbres (2^32 semillas pseudoaleatorias deterministas) de 32.768 parciales armónicos e inarmónicos.",
        "familia_dsp": "Síntesis Aditiva de Alta Densidad (Semilla de 32 bits)",
        "ecuacion_transferencia": "y[n] = sum_{k=1}^{32768} A_k(Seed_32) * sin(2*pi*f_k(Seed_32)*n/fs + phi_k)",
        "arquitectura_interna": ["PRNG determinista de 32 bits -> Curvas espectrales de Ogun", "Motor IFFT de 32.768 parciales", "Realzador psicoacústico Soundgoodizer integrado"],
        "parametros_clave": ["Preset Seed Number (1..4294967296)", "Soundgoodizer Macro Amount"],
        "cc_mapping": {"1": "Soundgoodizer Gain", "7": "Master Volume"},
        "estructura_fst": "Chunk 0xD5 de 16 bytes (uint32 Seed + float32 Macro + flags)."
    },
    "BassDrum": {
        "termino_rae": "Sintetizador físico-analógico de bombo con barrido exponencial",
        "definicion_rae": "Motor especializado en percusión grave que combina dos osciladores con envolvente de caída exponencial de frecuencia (barrido de ataque a subgrave), transitorio de clic y capa de ruido o muestra.",
        "familia_dsp": "Síntesis Percusiva de Barrido de Fase + Capa Transitoria",
        "ecuacion_transferencia": "y[n] = tanh(g_drv * (A(n)*sin(2*pi * integral(f_base + Delta_f*exp(-t/tau_p)) dt) + Click(n) + Sample(n)))",
        "arquitectura_interna": ["Oscilador Principal (Base/Peak/Slide Time)", "Oscilador Esclavo de Subgrave", "Generador de Pulso de Ataque (Click)", "Mezclador de Muestra de Ruido + Saturador"],
        "parametros_clave": ["Main Base/Peak/Slide", "Drive Saturation", "Sub-Bass Level", "Click Freq/Cut", "Duration"],
        "cc_mapping": {"74": "Base Frequency", "71": "Pitch Slide Time", "1": "Drive Amount"},
        "estructura_fst": "Chunk 0xD5 de 128 bytes con vectores float32 normalizados [0..1] y ruta de muestra opcional."
    },
    "BeepMap": {
        "termino_rae": "Transductor aditivo de mapa de bits óptico a espectro sonoro",
        "definicion_rae": "Sintetizador de imagen a sonido que escanea columnas de píxeles RGB: el eje vertical determina la frecuencia del parcial (escala lineal o logarítmica), el canal Rojo la amplitud izquierda, el Verde la amplitud derecha y el Azul el ancho de banda de ruido.",
        "familia_dsp": "Resíntesis Aditiva Espectrográfica por Imagen Bitmap",
        "ecuacion_transferencia": "L(t) = sum_y R(x(t), y)*sin(w_y*t); R(t) = sum_y G(x(t), y)*sin(w_y*t + B(x(t), y)*eta(t))",
        "arquitectura_interna": ["Escáner matricial de mapa de bits RGB", "Banco de osciladores sinusoidales en escala log/lineal", "Modulador de fase por canal azul"],
        "parametros_clave": ["Frequency Range (Octaves)", "Pixel Duration (Loop Length)", "Scale Type (Log/Linear/Harmonic)", "Use Blue"],
        "cc_mapping": {"1": "Frequency Range", "74": "Max Frequency"},
        "estructura_fst": "Chunk 0xD5 con cabecera de parámetros + bitmap DIB comprimido incrustado."
    },
    "BooBass": {
        "termino_rae": "Modelador monofónico de bajo eléctrico con ecualizador de tres bandas",
        "definicion_rae": "Emulador de bajo eléctrico de cuerda pulsada que filtra una tabla de ondas armónica a través de una red pasiva/activa de tres bandas (Graves, Medios, Agudos) acoplada a la velocidad MIDI.",
        "familia_dsp": "Muestreo Híbrido + Filtrado Formántico de Cuerda Pulsada",
        "ecuacion_transferencia": "H(z) = H_low(z, G_B) * H_mid(z, G_M) * H_high(z, G_T) aplicado sobre excitación de cuerda dependiente de velocidad.",
        "arquitectura_interna": ["Excitador de cuerda muestreado/modelado", "Ecualizador tonal de 3 bandas (Bass, Mid, Treble)"],
        "parametros_clave": ["Bass", "Mid", "Treble"],
        "cc_mapping": {"74": "Mid Tone", "71": "Treble Brightness", "1": "Bass Weight"},
        "estructura_fst": "Chunk 0xD5 compacto de 24 bytes (3 float32 para Bass/Mid/Treble + cabecera)."
    },
    "Dashboard": {
        "termino_rae": "Tablero de control MIDI y generador de mensajes exclusivos del sistema (SysEx)",
        "definicion_rae": "Constructor de paneles de mando virtuales (potenciómetros, deslizadores, selectores) para gobernar sintetizadores físicos externos o plugins mediante mensajes MIDI CC, RPN, NRPN y SysEx.",
        "familia_dsp": "Enrutamiento de Control Discreto MIDI / RPN / NRPN",
        "ecuacion_transferencia": "CC_out = clamp(round(u_knob * (Max - Min) + Min), 0, 127)",
        "arquitectura_interna": ["Motor de diseño de componentes UI", "Traductor de tablas RPN/NRPN de 14 bits", "Despachador de puertos MIDI"],
        "parametros_clave": ["Port Number", "MIDI Channel", "Controller Numbers (CC 0..127)"],
        "cc_mapping": {"1": "Custom Wheel 1", "74": "Custom Slider 1"},
        "estructura_fst": "Chunk 0xD5 con definición INI/binaria de controles y enlaces MIDI."
    },
    "DirectWave": {
        "termino_rae": "Muestreador polifónico multicapa con matriz de modulación y síntesis granular",
        "definicion_rae": "Estación de muestreo profesional de 16 partes multitímbricas con mapeo de zonas por nota y velocidad, estiramiento temporal en tiempo real, filtros multimodo en serie/paralelo y matriz de modulación de 16 ranuras.",
        "familia_dsp": "Interpolación Sinc Ventaneada de Muestras + Síntesis Granular + Filtrado Biquad",
        "ecuacion_transferencia": "y[n] = SVF_2(SVF_1(sum_k x_zone[k] * sinc((t(n) - k)/T_s) * w_k))",
        "arquitectura_interna": ["Motor de zonas 2D (Key x Velocity)", "Interpolador Polifásico de 64 puntos", "2 Filtros Multimodo + Shaper + Decimator", "Matriz de Modulación 16x2", "Bus FX (RingMod, Phaser, Chorus, Delay, Reverb)"],
        "parametros_clave": ["Zone Start/Loop", "Time Stretch / Pitch Shift", "Filter 1/2 Cutoff & Resonance", "Mod Matrix Depth"],
        "cc_mapping": {"1": "Mod Wheel Matrix Source", "74": "Filter 1 Cutoff", "71": "Filter 1 Resonance", "11": "Expression"},
        "estructura_fst": "Chunk 0xD5 contenedor DWP/DWB con descriptores de zona y referencias WAV."
    },
    "Drumaxx": {
        "termino_rae": "Sintetizador de percusión por modelado físico de membranas acopladas",
        "definicion_rae": "Motor de síntesis de batería de 16 almohadillas que modela físicamente la baqueta o maza (Mallet), la tensión, material y amortiguamiento de una membrana vibrante bidimensional y la resonancia del casco cilíndrico.",
        "familia_dsp": "Modelado Físico Modal de Membrana 2D (Funciones de Bessel / Modos Circulares)",
        "ecuacion_transferencia": "y[n] = sum_{m,k} A_{m,k} * exp(-d_{m,k}*n/fs) * sin(w_{m,k}(Tension, Shape)*n/fs + phi_{m,k}) * Excitacion_Maza[n]",
        "arquitectura_interna": ["Excitador de Impacto (Mallet Amplitude, Stiffness, Noise)", "Banco de Resonadores Modales de Membrana (Material, Damping, Tension, Shape)", "Filtro Auto-Modulado + Compresor/Limitador por canal", "Secuenciador de Patrones Interno"],
        "parametros_clave": ["Membrane Tension", "Material (Wood/Metal/Skin)", "Membrane Damping", "Shape (Square..Circle)", "Mallet Stiffness"],
        "cc_mapping": {"74": "Membrane Tension", "71": "Membrane Material", "1": "Mallet Noise"},
        "estructura_fst": "Chunk 0xD5 con 16 estructuras de pad físico + secuencias MIDI internas."
    },
    "Drumpad": {
        "termino_rae": "Almohadilla unitaria de percusión por modelado físico de membrana",
        "definicion_rae": "Versión monocanal de Drumaxx diseñada para cargarse directamente como un canal individual en el Step Sequencer sin sobrecarga multitímbrica.",
        "familia_dsp": "Modelado Físico Modal de Membrana Circular/Cuadrada (1 Voz Percusiva)",
        "ecuacion_transferencia": "y[n] = sum_{i=1}^N (h_i * f_mallet)[n], con polos modales desplazados por la tensión instantánea.",
        "arquitectura_interna": ["Generador de maza", "Resonador modal de membrana", "Ecualizador de salida de 2 bandas"],
        "parametros_clave": ["Mallet Amplitude/Decay", "Membrane Tension/Phase/Material", "Low/High EQ"],
        "cc_mapping": {"74": "Tension", "71": "Material", "1": "Decay"},
        "estructura_fst": "Chunk 0xD5 de 1 pad físico (164 bytes de floats de parámetros)."
    },
    "FL Keys": {
        "termino_rae": "Sintetizador híbrido de pianos acústicos y electromecánicos por tabla de ondas y modelado",
        "definicion_rae": "Instrumento de teclado que combina muestras de ataque de martillo o púa metálica (Rhodes/Wurlitzer/Grand Piano) con resonadores de cuerda y timbre dependiente de la dureza de pulsación.",
        "familia_dsp": "Síntesis por Tabla de Ondas con Conmutación de Velocidad y Desafinación Estocástica",
        "ecuacion_transferencia": "y[n] = Env_ADSR(n) * Filtro_Dureza(v_MIDI) * Osc_Cuerda(f_0 * (1 + delta_detune))",
        "arquitectura_interna": ["Motor de ataque de martillo", "Banco de tablas de ondas armónicas", "Modulador de Trémolo/Panner (Rhodes)", "Overdrive de previo"],
        "parametros_clave": ["Decay", "Release", "Hardness", "Vel->Hardness", "Muffle", "Stereo/Pan", "Overdrive", "Detune"],
        "cc_mapping": {"64": "Sustain Pedal", "74": "Muffle Filter", "1": "LFO Tremolo Speed"},
        "estructura_fst": "Chunk 0xD5 con parámetros de modelo y referencia a tabla de ondas."
    },
    "FL Slayer": {
        "termino_rae": "Sintetizador de guitarra eléctrica por guía de ondas Karplus-Strong y amplificador modelado",
        "definicion_rae": "Modelador físico de seis cuerdas de guitarra eléctrica con simulación de pastillas magnéticas (bobina simple/doble), técnicas de ejecución (glissando, apagado con palma, armónicos) y etapa de distorsión de válvulas con recinto acústico.",
        "familia_dsp": "Guía de Ondas Karplus-Strong Extendida + No Linealidad de Válvula + Convolución de Pantalla",
        "ecuacion_transferencia": "s[n] = x_pick[n] + g_damp * H_loop(z) * s[n - D]; y[n] = Cab_IR * tanh(Gain * Pickup(s[n]))",
        "arquitectura_interna": ["6 Líneas de retardo fraccionario Karplus-Strong", "Filtro de posición de pastilla (comb filter espacial)", "Previo de distorsión + Gabinete + Efectos de pedal"],
        "parametros_clave": ["String Damp", "Vel/Damp", "Pickup Position", "Amp Drive/Presence", "Cabinet Type"],
        "cc_mapping": {"1": "Wah / Vibrato", "74": "Amp Tone", "71": "String Damping"},
        "estructura_fst": "Chunk 0xD5 de parámetros de cuerda, pastilla y amplificador."
    },
    "FL Studio Mobile": {
        "termino_rae": "Estación de producción modular embebida de arquitectura móvil",
        "definicion_rae": "Sub-entorno completo de secuenciación y síntesis multi-instrumento (DirectWave, MiniSynth, GMS, Transistor Bass, SuperSaw) alojado como un único generador dentro de FL Studio de escritorio.",
        "familia_dsp": "Motor Multitímbrico de Síntesis y Secuenciación Autónoma",
        "ecuacion_transferencia": "y_master[n] = Limiter(sum_{ch=1}^N Chain_FX_ch(Gen_ch[n]))",
        "arquitectura_interna": ["Secuenciador multipista .flm", "Sintetizadores integrados (SuperSaw, MiniSynth, GMS)", "Rack de efectos modular"],
        "parametros_clave": ["Master Volume", "Macro Knobs 1..8"],
        "cc_mapping": {"1": "Macro 1", "2": "Macro 2", "74": "Filter Cutoff"},
        "estructura_fst": "Chunk 0xD5 contenedor de proyecto binario .flm completo."
    },
    "FL Studio Mobile Rack": {
        "termino_rae": "Bastidor de instrumentos modulares del motor FL Studio Mobile",
        "definicion_rae": "Alojamiento directo de los módulos de síntesis de FL Studio Mobile (SuperSaw, Drum Sampler, MiniSynth) como un instrumento individual del Channel Rack.",
        "familia_dsp": "Síntesis Polifónica SuperSaw / Sustractiva Ligera",
        "ecuacion_transferencia": "y[n] = SVF(sum_{k=1}^7 a_k * Saw(2*pi*f_0*(1 + d_k)*n/fs + phi_k))",
        "arquitectura_interna": ["Módulo generador Mobile", "Cadena de inserción móvil"],
        "parametros_clave": ["Detune", "Pan Spread", "Cutoff", "Resonance"],
        "cc_mapping": {"74": "Cutoff", "71": "Resonance"},
        "estructura_fst": "Chunk 0xD5 con estado del módulo Mobile."
    },
    "FLEX": {
        "termino_rae": "Sintetizador polifónico de motor híbrido con ocho macro-controladores y telemetría visual",
        "definicion_rae": "Motor de síntesis multidimensional que combina internamente síntesis sustractiva, tabla de ondas, multisamples, FM y modelado físico Karplus-Strong, exponiendo 8 macro-controles preasignados, filtro maestro y analizador en tiempo real.",
        "familia_dsp": "Síntesis Híbrida (Wavetable + Multisample + FM + Karplus-Strong) + Cadena Master FX",
        "ecuacion_transferencia": "y[n] = Limiter(Reverb(Delay(Filter_Master(Engine_Hybrid(n, Macros_{1..8})))))",
        "arquitectura_interna": ["Motor de síntesis oculto configurable por pack", "8 Macro-potenciómetros de interpolación multiparamétrica", "Envolventes de Filtro y Volumen", "Filtro Maestro Multimodo", "Delay, Reverb y Limitador Maestro con Vectorscopio/Espectrograma"],
        "parametros_clave": ["Macro 1..8", "Master Filter Cutoff/Res", "Pitch/Filter/Amp ADSR", "Limiter Type (Warm/Clip/Limit)"],
        "cc_mapping": {"1": "Macro 1 (Cutoff/Timbre)", "2": "Macro 2 (Resonance)", "74": "Master Filter Cutoff", "71": "Master Filter Res"},
        "estructura_fst": "Chunk 0xD5 con UUID de paquete FLEX + índice de preset + vector de 8 macros y envolventes."
    },
    "FPC": {
        "termino_rae": "Centro de producción percusiva de dieciséis almohadillas multicapa",
        "definicion_rae": "Muestreador de batería inspirado en el hardware Akai MPC, dotado de dos bancos de 16 almohadillas (32 en total), cada una con múltiples capas conmutadas por velocidad, envolvente dedicada y salida independiente al mezclador.",
        "familia_dsp": "Disparo Polifónico de Muestras Multicapa con Grupos de Corte Mutuo (Choke Groups)",
        "ecuacion_transferencia": "y_pad[n] = Env_AHDSR(n) * Layer_{v_MIDI}[n * 2^(Pitch/1200)], con silenciamiento instantáneo si ChokeGroup_i == ChokeGroup_j.",
        "arquitectura_interna": ["32 Pads (Banco A/B)", "Apilador de capas de velocidad con fundido cruzado", "Motor de grupos Cut/Cut By", "Ruteo individual de compensación de canal de mezclador"],
        "parametros_clave": ["Pad Volume/Pan/Pitch", "Layer Velocity Min/Max", "Cut Group / Cut By Group", "Output Offset"],
        "cc_mapping": {"7": "Bank Volume", "10": "Pad Pan"},
        "estructura_fst": "Chunk 0xD5 con descriptores de 32 pads, rangos de velocidad y rutas WAV."
    },
    "Fruit Kick": {
        "termino_rae": "Oscilador de bombo electrónico por barrido senoidal y distorsión",
        "definicion_rae": "Sintetizador minimalista de bombo electrónico (estilo 808/909) basado en un único oscilador senoidal cuya frecuencia cae exponencialmente desde una frecuencia máxima hasta una frecuencia fundamental subgrave.",
        "familia_dsp": "Oscilador Senoidal con Modulación Exponencial de Frecuencia y Recorte",
        "ecuacion_transferencia": "f(t) = f_min + (f_max - f_min)*exp(-t / tau_sweep); y(t) = clip(A(t) * sin(2*pi * integral f(tau) dtau))",
        "arquitectura_interna": ["Oscilador senoidal bloqueado en fase a 0 grados", "Generador de envolvente de barrido tonal", "Distorsionador de onda cuadrada"],
        "parametros_clave": ["Max Freq", "Min Freq", "Pitch Decay", "Amp Decay", "Click (Start Phase)", "Distortion"],
        "cc_mapping": {"74": "Max Freq", "71": "Pitch Decay", "1": "Distortion"},
        "estructura_fst": "Chunk 0xD5 de 24 bytes (6 enteros de 32 bits)."
    },
    "Fruity DX10": {
        "termino_rae": "Sintetizador de modulación de fase de dos operadores (arquitectura FM clásica)",
        "definicion_rae": "Sintetizador polifónico de 8 voces que implementa modulación de fase de dos operadores ( un Oscilador Portador senoidal y un Oscilador Modulador con razón armónica gruesa/fina y envolvente propia) para timbres de campana, bajo eléctrico y órgano.",
        "familia_dsp": "Síntesis por Modulación de Fase (PM / FM de 2 Operadores)",
        "ecuacion_transferencia": "y(t) = E_c(t) * sin(2*pi*f_c*t + E_m1(t)*I_1*sin(2*pi*f_m1*t) + E_m2(t)*I_2*sin(2*pi*f_m2*t))",
        "arquitectura_interna": ["Portadora senoidal con envolvente Attack/Decay/Release", "2 Moduladores en cascada/paralelo con razón Coarse/Fine", "LFO global de vibrato"],
        "parametros_clave": ["Carrier Attack/Decay/Release", "Mod 1 Coarse/Fine/Init/Time/Sus", "Mod 2 Coarse/Fine/Vel", "Waveform Brightness"],
        "cc_mapping": {"1": "Vibrato LFO", "74": "Modulator 1 Initial Level", "71": "Modulator 1 Decay"},
        "estructura_fst": "Chunk 0xD5 de 80 bytes con parámetros normalizados en coma flotante."
    },
    "Fruity Dance": {
        "termino_rae": "Visualizador coreográfico sincronizado al reloj de transporte y eventos MIDI",
        "definicion_rae": "Generador visual de hoja de sprites (FL-Chan) cuyas secuencias de animación se disparan mediante notas MIDI (C5..B5) y cuya velocidad de fotogramas se bloquea en fase con el pulso del proyecto (PPQ).",
        "familia_dsp": "Sincronización de Fase de Reloj Musical (PPQ -> Frame Index)",
        "ecuacion_transferencia": "Frame_idx(t) = floor((Ticks_PPQ(t) / 96) * FPS_sprite) mod TotalFrames_anim",
        "arquitectura_interna": ["Decodificador de hojas de sprites PNG", "Mapeador de notas MIDI a estados coreográficos"],
        "parametros_clave": ["Animation State Note", "Window Position", "Sprite Skin"],
        "cc_mapping": {"1": "Dance Style"},
        "estructura_fst": "Chunk 0xD5 con ruta de skin y coordenadas de ventana."
    },
    "Fruity DrumSynth Live": {
        "termino_rae": "Estación de síntesis analógica de percusión de doble oscilador y puente de ruido",
        "definicion_rae": "Sintetizador de batería en tiempo real donde cada nota MIDI dispara un parche autónomo compuesto por dos osciladores con modulación en anillo/ruido, barrido de tono, filtro paso-banda/paso-bajo y distorsión.",
        "familia_dsp": "Síntesis Analógica Virtual de Percusión (2 Osciladores + Ruido Filtrado + Saturación)",
        "ecuacion_transferencia": "y[n] = Clip(E_1[n]*Osc_1[n] + E_2[n]*Osc_2[n] + E_noise[n]*SVF(Noise[n]))",
        "arquitectura_interna": ["120 Nodos de parche de percusión (1 por tecla MIDI)", "Oscilador 1 y 2 con barrido de tono", "Generador de ruido blanco/rosa con filtro multimodo", "Etapa de saturación y envío a mezclador por tecla"],
        "parametros_clave": ["Osc 1/2 Freq & Sweep", "Noise Filter Cutoff/Res/Mode", "Overdrive", "Track Send"],
        "cc_mapping": {"74": "Noise Cutoff", "71": "Noise Resonance"},
        "estructura_fst": "Chunk 0xD5 con matriz de 120 parches de percusión."
    },
    "Fruity Envelope Controller": {
        "termino_rae": "Generador de señales de control multipunto disparado por notas MIDI",
        "definicion_rae": "Transductor de eventos MIDI a señales de automatización interna que dispone de 8 articuladores independientes, cada uno con envolvente multipunto, LFO sincronizable, mapeo de escala de teclado y curva de velocidad.",
        "familia_dsp": "Síntesis de Señales de Control (Sub-audio / Tasa de Tick PPQ)",
        "ecuacion_transferencia": "C_k(t, note, vel) = Base_k + Env_k(t) * LFO_k(t) * KeyMap_k(note) * VelMap_k(vel) * ModX * ModY",
        "arquitectura_interna": ["8 Articuladores de control independientes", "Editor de splines multipunto con tensión", "Mapeador X/Y continuo por voz"],
        "parametros_clave": ["Articulator 1..8 Output", "Base Level", "Envelope Multiplier", "LFO Speed/Tension", "Mod X / Mod Y"],
        "cc_mapping": {"1": "Modulator X", "11": "Modulator Y"},
        "estructura_fst": "Chunk 0xD5 con 8 árboles de curvas spline de articulador."
    },
    "Fruity Granulizer": {
        "termino_rae": "Sintetizador corpuscular de muestras por fragmentación y solapamiento temporal",
        "definicion_rae": "Motor de síntesis granular en tiempo real que trocea una muestra de audio en granos de duración (10-500 ms), ataque/caída (suavizado trapezoidal) y espaciado variables, permitiendo estirar el tiempo o congelar la posición sin alterar el tono.",
        "familia_dsp": "Síntesis Granular Síncrona/Asíncrona (Overlap-Add con Ventana Trapezoidal)",
        "ecuacion_transferencia": "y[n] = sum_k w_trap((n - k*Delta_G)/L_G, Attack) * x[Pos(k) + (n - k*Delta_G)*2^(Pitch/12)]",
        "arquitectura_interna": ["Planificador de disparo de granos (Grain Spacing / Wave Spacing)", "Envolvente trapezoidal de grano (Attack/Decay)", "Modulador LFO de profundidad y velocidad de posición", "Retención (Hold / Freeze) de grano"],
        "parametros_clave": ["Grain Attack", "Grain Hold", "Grain Spacing", "Wave Spacing (-300%..+300%)", "Sample Start", "Hold Freeze"],
        "cc_mapping": {"74": "Wave Spacing", "71": "Grain Spacing", "1": "Sample Start Position"},
        "estructura_fst": "Chunk 0xD5 de parámetros de grano + evento 0xC4 de ruta de muestra."
    },
    "Fruity Keyboard Controller": {
        "termino_rae": "Transductor de altura de nota y velocidad MIDI a señal de control continuo",
        "definicion_rae": "Generador de control interno que convierte el número de nota MIDI (0..127) y la velocidad de pulsación en dos señales continuas normalizadas [0.0..1.0] con suavizado temporal (portamento de control) para automatizar filtros o afinaciones.",
        "familia_dsp": "Cuantización Discreta de Altura a Voltaje Virtual (1V/Octava Digital) con Filtro de Suavizado",
        "ecuacion_transferencia": "y_ctl[n] = y_ctl[n-1] + alpha_smooth * (Table_Note[MIDI_Key] - y_ctl[n-1])",
        "arquitectura_interna": ["Tabla de transferencia de 128 teclas", "Tabla de velocidad", "Filtro paso-bajo de suavizado de transiciones (Attack/Release Smoothing)"],
        "parametros_clave": ["Note Value Map", "Attack Smoothing", "Release Smoothing", "Key Range"],
        "cc_mapping": {"1": "Attack Smoothing"},
        "estructura_fst": "Chunk 0xD5 con vector de 128 floats de mapeo por tecla."
    },
    "Fruity Slicer": {
        "termino_rae": "Troceador de bucles por detección de transitorios y resecuenciador rítmico",
        "definicion_rae": "Muestreador de bucles rítmicos que detecta ataques percusivos mediante derivada energética, divide el audio en rebanadas independientes, las asigna a teclas cromáticas sucesivas y exporta la partitura al Piano Roll.",
        "familia_dsp": "Detección de Inicio por Flujo de Energía + Estiramiento de Grano para Relleno de Huecos",
        "ecuacion_transferencia": "Onset si d/dt(E_short(t)) > Threshold; cada rebanada i se reproduce en la nota MIDI (C5 + i).",
        "arquitectura_interna": ["Detector de umbrales de ataque y caída", "Asignador cromático de rebanadas", "Estirador de tono/tiempo por rebanada"],
        "parametros_clave": ["Low/High Threshold", "Pitch Shift", "Time Stretch", "Attack/Decay De-click"],
        "cc_mapping": {"74": "Pitch Shift", "71": "Time Stretch"},
        "estructura_fst": "Chunk 0xD5 con marcadores de muestra y audio/ruta incrustada."
    },
    "Fruity Slicer 2": {
        "termino_rae": "Troceador espectral de segunda generación con envolvente y filtro por rebanada",
        "definicion_rae": "Evolución del motor de troceado con detección espectral de alta precisión, reproducción en reversa por rebanada, envolvente de amplitud y filtro multimodo dedicados.",
        "familia_dsp": "Detección de Transitorios por Flujo Espectral + Interpolación Sinc por Rebanada",
        "ecuacion_transferencia": "SF(m) = sum_k max(0, |X(m,k)| - |X(m-1,k)|); y_slice[n] = SVF(Env(n) * Slice_i[n])",
        "arquitectura_interna": ["Detector de flujo espectral", "Filtro multimodo y envolvente por rebanada", "Puente de exportación directa a Piano Roll"],
        "parametros_clave": ["Slice Sensitivity", "Filter Cutoff/Res", "Slice Reverse", "Pitch/Stretch"],
        "cc_mapping": {"74": "Cutoff", "71": "Resonance"},
        "estructura_fst": "Chunk 0xD5 con tabla de regiones y parámetros de filtro."
    },
    "Fruity Video Player": {
        "termino_rae": "Reproductor de flujo de vídeo sincronizado al código de tiempo SMPTE/PPQ",
        "definicion_rae": "Decodificador de contenedores de vídeo (MP4/MOV/AVI) enganchado de forma determinista a la posición de reproducción de la Playlist para composición de bandas sonoras y doblaje.",
        "familia_dsp": "Sincronización de Fase de Transporte (Ticks PPQ <-> Timestamp PTS de Vídeo)",
        "ecuacion_transferencia": "t_video = t_song_sec + t_offset_SMPTE",
        "arquitectura_interna": ["Decodificador FFmpeg/AVFoundation", "Sincronizador de reloj de transporte", "Extractor de pista de audio opcional"],
        "parametros_clave": ["SMPTE Offset", "Detach Window", "Ignore Tempo Changes"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con ruta del archivo de vídeo y desplazamiento temporal."
    },
    "Fruity Voltage Controller": {
        "termino_rae": "Transductor de eventos digitales a voltajes continuos acoplados en corriente continua (DC-Coupled CV/Gate)",
        "definicion_rae": "Generador de señales en corriente continua (DC) y rampa de 1V/octava o Hz/V a través de interfaces de audio acopladas en DC para gobernar sintetizadores modulares analógicos Eurorack.",
        "familia_dsp": "Generación de Nivel DC de Precisión Flotante y Escala Logarítmica 1V/Octava",
        "ecuacion_transferencia": "V_pitch[n] = V_ref + (MIDI_Note - 60) / 12.0; V_gate[n] = V_high si NoteOn sino 0.0",
        "arquitectura_interna": ["Generador de rampa 1V/Oct y Hz/V (Korg/Yamaha)", "Generador de pulso Gate/Trigger", "Calibrador de escala de octava por hardware"],
        "parametros_clave": ["Pitch Scale (1V/Oct, Hz/V)", "Gate Level", "Tune Calibration", "Mod CV Level"],
        "cc_mapping": {"1": "Auxiliary CV Output"},
        "estructura_fst": "Chunk 0xD5 con tablas de calibración de voltaje."
    },
    "Fruity Wrapper": {
        "termino_rae": "Adaptador anfitrión de instrumentos virtuales externos (VST2/VST3/AU/CLAP)",
        "definicion_rae": "Contenedor de instrumentos de terceros que traduce las notas con propiedades por voz de FL Studio y los 128 controladores MIDI hacia la API binaria del plugin externo.",
        "familia_dsp": "Puente de Búfer de Audio de Coma Flotante y Despacho de Eventos MIDI/MPE",
        "ecuacion_transferencia": "y_{L,R}[n] = VST3_ProcessAudio(x_{L,R}[n], EventQueue_MIDI_MPE)",
        "arquitectura_interna": ["Cargador dinámico de bundles VST3/AU", "Tabla de 128 parámetros CC + 4096 parámetros de automatización", "Gestor de búfer fijo/variable y compensación de latencia"],
        "parametros_clave": ["MIDI Input/Output Port", "Pitch Bend Range", "Use Fixed Size Buffers", "Notify About Rendering Mode"],
        "cc_mapping": {"1": "CC #1 Mod Wheel", "74": "CC #74 Brightness", "64": "CC #64 Sustain"},
        "estructura_fst": "Chunk 0xD5 con cabecera Wrapper + estado opaco del plugin VST3/AU."
    },
    "GMS": {
        "termino_rae": "Estación de síntesis de ranura rítmica con tres osciladores y matriz de efectos por compás",
        "definicion_rae": "Sintetizador agresivo (Groove Machine Synth) dotado de 3 osciladores con sincronización dura, modulación de frecuencia y anillo, filtro multimodo y una sección de 10 efectos internos encadenables y automatizables en tiempo real (Trance Gate, Crusher, Flanger, Phaser, Comb).",
        "familia_dsp": "Síntesis Sustractiva/FM + Procesamiento de Efectos Modulado por Almohadilla X/Y",
        "ecuacion_transferencia": "y[n] = FX_Rack_{1..10}(SVF(Osc_1[n] + Osc_2[n] + Osc_3[n] + Sub[n], Env_Filter))",
        "arquitectura_interna": ["3 Osciladores de tabla de ondas con Sync/FM/RM", "Filtro Multimodo (LP/HP/BP) con envolvente e inversión", "2 LFOs + 2 Envolventes", "10 Efectos de rendimiento con botón Glue (retención) y Gate de 16 pasos"],
        "parametros_clave": ["Osc 1..3 Wave & Detune", "Cutoff & Resonance", "FX Selection (Distortion, Crusher, Flanger, Phaser, LPF, HPF, Echo, Reverb, Pan, TranceGate)", "Mod X/Y"],
        "cc_mapping": {"74": "Filter Cutoff", "71": "Filter Resonance", "1": "FX Mod X", "11": "FX Mod Y"},
        "estructura_fst": "Chunk 0xD5 con vector completo de parámetros de osciladores y matriz de 10 efectos."
    },
    "Harmless": {
        "termino_rae": "Sintetizador sustractivo ejecutado íntegramente mediante un motor de síntesis aditiva",
        "definicion_rae": "Hermano compacto de Harmor donde el filtrado paso-bajo, la resonancia, el desfasador (phaser) y el unísono no se aplican sobre una onda en el dominio del tiempo, sino esculpiendo directamente las amplitudes y fases de cientos de parciales sinusoidales antes de su suma.",
        "familia_dsp": "Síntesis Sustractiva en Dominio Espectral Aditivo (Modificación Directa de Parciales)",
        "ecuacion_transferencia": "y(t) = sum_{k=1}^N A_k * H_mask(k*f_0, f_cut, Q) * Phaser_mask(k*f_0, t) * sin(2*pi * k * f_0 * f_detune(k) * t + phi_k)",
        "arquitectura_interna": ["Generador de tabla de armónicos y fase", "Máscara espectral de filtro de pendiente arbitraria (hasta cientos de dB/oct)", "Máscara de Phaser armónico", "Armonizador, Unísono de parciales y Compresor/Distorsionador"],
        "parametros_clave": ["Pluck Decay", "Harmonic Mask Cutoff & Width", "Custom Resonance Shape", "Phaser Speed/Width", "Unison Pitch/Pan", "Harmonizer"],
        "cc_mapping": {"74": "Frequency Cutoff", "71": "Resonance Peak", "1": "Phaser Mix"},
        "estructura_fst": "Chunk 0xD5 con estado vectorial de máscaras espectrales."
    },
    "Harmor": {
        "termino_rae": "Sintetizador aditivo de doble unidad (A/B) y motor de resíntesis espectral e imagen",
        "definicion_rae": "Cumbre de la síntesis aditiva en FL Studio: cada una de sus dos partes (A y B) controla en paralelo 516 parciales sinusoidales cuya frecuencia y amplitud en decibelios se procesan como mapas bidimensionales antes de la síntesis final, permitiendo prismas inarmónicos, desplazamiento de formantes, resíntesis de audio/imagen y afinación microtonal exacta (.scl).",
        "familia_dsp": "Síntesis Aditiva de 516 Parciales con Procesamiento Espectral en Escala Logarítmica (Octava/dB)",
        "ecuacion_transferencia": "y(t) = sum_{p in {A,B}} sum_{k=1}^{516} 10^(M_amp(k, t)/20) * sin(2*pi * integral(f_0 * M_freq(k, t)) dtau + phi_{p,k})",
        "arquitectura_interna": ["2 Unidades Aditivas Independientes (Parte A y Parte B)", "Motor de Prisma Inarmónico y Desplazamiento de Formantes", "Resintetizador de Audio e Imagen 2D", "2 Filtros Espectrales de forma libre + Phaser Espectral", "Matriz de Articuladores Multipunto (Envolventes, LFOs, Mapeos X/Y/Z, Escalas Scala .scl)", "Cadena FX (Distorsión, Chorus, Delay, Reverb, Compresión Multibanda Maximus)"],
        "parametros_clave": ["Timbre 1/2 Mix", "Pluck", "Blur (Time Smearing)", "Prism", "Harmonizer", "Filter 1/2 Freq & Width", "Mod X / Mod Y / Mod Z"],
        "cc_mapping": {"1": "Modulator X (Cutoff)", "2": "Modulator Y (Resonance)", "11": "Modulator Z (Prism/Timbre)", "74": "Filter 1 Frequency"},
        "estructura_fst": "Chunk 0xD5 con tablas armónicas duales, mapas de imagen/muestra y árboles de articuladores."
    },
    "Kepler": {
        "termino_rae": "Emulador de modelado físico del sintetizador analógico polifónico Roland Juno-6/106",
        "definicion_rae": "Recreación fiel de circuito del clásico sintetizador de oscilador controlado digitalmente (DCO) de 1984, integrando ondas de pulso modulado (PWM), diente de sierra y suboscilador cuadrado, filtro paso-alto estático, filtro paso-bajo resonante de 4 polos (IR3109) y el icónico coro estereofónico de línea de retardo analógica (BBD Chorus I/II).",
        "familia_dsp": "Oscilador DCO Sin Aliasing (PolyBLEP) + Filtro Escalera OTA de 4 Polos + Coro BBD Estéreo",
        "ecuacion_transferencia": "y[n] = BBD_Chorus_{I,II}(OTA_LP4(HPF(DCO_Pulse[n] + DCO_Saw[n] + Sub[n] + Noise[n]), f_c, Q))",
        "arquitectura_interna": ["Arpegiador clásico Up/Down", "DCO con PWM, Sierra, Sub y Ruido", "Filtro HPF + VCF de 24 dB/oct auto-oscilante", "Envolvente ADSR única compartida/invertible", "Doble línea de retardo Bucket-Brigade Device (Chorus I, II y I+II)"],
        "parametros_clave": ["DCO Pulse Width", "Sub Oscillator Level", "HPF Cutoff", "VCF Freq & Res", "Chorus I / Chorus II Buttons"],
        "cc_mapping": {"74": "VCF Frequency", "71": "VCF Resonance", "1": "LFO Pitch Depth", "93": "Chorus Mode"},
        "estructura_fst": "Chunk 0xD5 con parámetros de circuito Juno y estado de botones Chorus."
    },
    "Kepler Exo": {
        "termino_rae": "Sintetizador analógico virtual de doble capa de osciladores DCO y matriz de modulación",
        "definicion_rae": "Expansión hipertrófica del motor Kepler (inspirada en la fusión Juno-106 / Jupiter-8) con dos osciladores DCO completos con sincronización dura, modulación cruzada (X-Mod), conformación de onda continua, dos filtros multimodo, matriz de modulación de 16 ranuras y rack de 5 efectos de estudio.",
        "familia_dsp": "Doble DCO con Sincronización y Modulación Cruzada + Doble Filtro ZDF (Zero-Delay Feedback)",
        "ecuacion_transferencia": "y[n] = FX_Chain(ZDF_VCF(DCO_1(n) + DCO_2(n, Sync, XMod) + Sub(n)))",
        "arquitectura_interna": ["2 Osciladores DCO con Wave Shaping y X-Mod", "Filtro Dual ZDF de 12/24 dB/oct con saturación", "3 Envolventes + 3 LFOs + Matriz de Modulación de 16 rutas", "Rack FX (Hyper Chorus, Phaser, Saturator, Delay, Reverb)"],
        "parametros_clave": ["DCO 1/2 Pitch & Wave", "Cross Modulation (X-Mod)", "VCF Cutoff, Res & Drive", "Unison Voices & Detune", "Hyper Chorus Mix"],
        "cc_mapping": {"74": "VCF Cutoff", "71": "VCF Resonance", "1": "Mod Wheel Matrix", "11": "Filter Drive"},
        "estructura_fst": "Chunk 0xD5 con estado de ambos DCO, matriz de 16 ranuras y rack de efectos."
    },
    "MIDI Out": {
        "termino_rae": "Emisor y encaminador de flujos de mensajes MIDI hacia puertos externos o internos",
        "definicion_rae": "Generador sin síntesis de audio propia que transmite notas del Piano Roll, cambios de programa, selección de banco y hasta 9 páginas de 8 potenciómetros configurables (CC, RPN, NRPN, Aftertouch) a través de un puerto y canal MIDI específico.",
        "familia_dsp": "Serialización Determinista de Protocolo MIDI 1.0 (31.25 kBaud / Virtual Port Bus)",
        "ecuacion_transferencia": "Msg_MIDI = [StatusByte(0xB0 | Chan), CC_Num(0..127), Value(0..127)]",
        "arquitectura_interna": ["Selector de Puerto Virtual (0..255) y Canal (1..16)", "Selector de Banco MSB/LSB y Patch", "9 Páginas x 8 Potenciómetros asignables a CC/RPN/NRPN"],
        "parametros_clave": ["Port", "Channel", "Bank MSB/LSB", "Patch", "Page 1..9 Knobs 1..8"],
        "cc_mapping": {"1": "Knob 1", "74": "Knob 2", "71": "Knob 3"},
        "estructura_fst": "Chunk 0xD5 con definiciones de los 72 potenciómetros y puerto de salida."
    },
    "MiniSynth": {
        "termino_rae": "Sintetizador sustractivo monofónico/polifónico de seis pestañas de flujo directo",
        "definicion_rae": "Sintetizador ligero de aprendizaje y esbozo rápido estructurado en 6 secciones contiguas (Oscillator, Filter, Env, LFO, Fx, Keys) con transformación continua de forma de onda y coro/retardo integrados.",
        "familia_dsp": "Oscilador con Morfismo de Forma de Onda + Filtro Biquad Resonante",
        "ecuacion_transferencia": "y[n] = Chorus_Delay(Biquad_SVF(Osc_Morph(n, Shape, Mod), f_c(Env, LFO), Q))",
        "arquitectura_interna": ["Oscilador con Wave Shape y Modulator", "Filtro LP/BP/HP con inversión de envolvente", "Envolvente ADSR, LFO y sección FX"],
        "parametros_clave": ["Osc Waveform", "Wave Modifier", "Filter Cutoff & Peak", "LFO Rate & Amount", "FX Mode (Chorus/Delay)"],
        "cc_mapping": {"74": "Filter Cutoff", "71": "Filter Peak", "1": "Wave Modifier"},
        "estructura_fst": "Chunk 0xD5 compacto de 64 bytes."
    },
    "Morphine": {
        "termino_rae": "Sintetizador aditivo de cuatro generadores con morfismo espectral bidimensional",
        "definicion_rae": "Potente estación de síntesis aditiva y resíntesis provista de 4 generadores independientes (A, B, C, D) cuyos espectros de armónicos évolucionan mediante instantáneas temporales (Breakpoints) y se funden continuamente mediante una almohadilla de morfismo X/Y.",
        "familia_dsp": "Síntesis Aditiva de Cuatro Fuentes con Interpolación Bilineal de Espectros (Morphing 2D)",
        "ecuacion_transferencia": "S_mix(k, t) = (1-x)*(1-y)*S_A + x*(1-y)*S_B + (1-x)*y*S_C + x*y*S_D; y(t) = sum_k S_mix(k,t)*sin(w_k*t)",
        "arquitectura_interna": ["4 Generadores Aditivos (A, B, C, D) con resíntesis WAV", "Secuencias de Breakpoints espectrales por generador", "Matriz de Morfismo Bilineal X/Y", "Filtro Formántico + Cadena de 5 Efectos"],
        "parametros_clave": ["Morph X", "Morph Y", "Generator A..D Detune/Pan/Mix", "Formant Shift", "Harmonic Detune"],
        "cc_mapping": {"1": "Morph X", "11": "Morph Y", "74": "Formant Shift"},
        "estructura_fst": "Chunk 0xD5 con las tablas de instantáneas armónicas de los 4 generadores."
    },
    "Ogun": {
        "termino_rae": "Sintetizador aditivo de treinta y dos mil parciales para timbres metálicos e inarmónicos",
        "definicion_rae": "Motor de síntesis aditiva extrema capaz de generar y modular en tiempo real más de 32.000 parciales sinusoidales mediante funciones de mapeo X/Y de riqueza tímbrica, caída espectral dependiente de la frecuencia y dispersión inarmónica (platillos, gongs, campanas y texturas industriales).",
        "familia_dsp": "Síntesis Aditiva Masiva (32.768 Parciales) con Distribución de Fase y Decaimiento Espectral",
        "ecuacion_transferencia": "y(t) = sum_{k=1}^{32768} A_k(t) * exp(-d(f_k)*t) * sin(2*pi * f_0 * Map_inharm(k)*t + phi_k)",
        "arquitectura_interna": ["Generador espectral de 32.768 parciales", "Curvas de mapeo de Timbre, Decay, Pre-decay y Fullness", "Unísono aditivo + Armonizador + Filtro EQ + Chorus/Delay/Reverb"],
        "parametros_clave": ["Richness", "Timbre Seed", "Pre-decay", "Decay Curve", "Unison Pitch", "Mod X / Mod Y"],
        "cc_mapping": {"1": "Modulator X", "11": "Modulator Y", "74": "Harmonic Cutoff"},
        "estructura_fst": "Chunk 0xD5 con curvas multipunto de densidad y decaimiento de parciales."
    },
    "Patcher": {
        "termino_rae": "Sub-anfitrión modular de instrumentos en grafo acíclico dirigido",
        "definicion_rae": "Versión generadora de Patcher que aloja múltiples sintetizadores, procesadores de voz (VFX) y efectos conectados mediante un grafo arbitrario, presentando hacia el exterior una única superficie de control personalizada (Control Surface).",
        "familia_dsp": "Evaluación Topológica de Subgrafo de Audio, Voz MIDI y Parámetros",
        "ecuacion_transferencia": "y_out[n] = sum_{v in Sinks} Node_v(sum_{u -> v} g_{u,v} * Node_u[n])",
        "arquitectura_interna": ["Lienzo de grafo Map (Nodos de Audio, Notas y Parámetros)", "Diseñador de interfaz Control Surface", "Aislamiento de latencia PDC por rama"],
        "parametros_clave": ["Surface Macro Controls", "Node Audio Send Levels"],
        "cc_mapping": {"1": "Surface Control 1", "74": "Surface Control 2"},
        "estructura_fst": "Chunk 0xD5 recursivo que anida los chunks 0xD5 de todos los plugins hijos y la lista de adyacencia del grafo."
    },
    "Plucked!": {
        "termino_rae": "Sintetizador de cuerda pulsada por línea de retardo realimentada (algoritmo Karplus-Strong)",
        "definicion_rae": "Implementación canónica del modelo físico de cuerda pulsada de Karplus-Strong: una ráfaga inicial de ruido o forma de onda llena una línea de retardo cuya longitud fija la nota fundamental y cuyo bucle de realimentación incorpora un filtro paso-bajo que amortigua progresivamente los agudos.",
        "familia_dsp": "Síntesis por Guía de Ondas Digital Karplus-Strong",
        "ecuacion_transferencia": "y[n] = x_exc[n] + g_decay * ((1 - a)*y[n - D] + a*y[n - D - 1]), con D = fs / f_0.",
        "arquitectura_interna": ["Excitador de pulso/ruido coloreado", "Línea de retardo con interpolador fraccionario", "Filtro de amortiguamiento de bucle", "Modulador de anchura estereofónica"],
        "parametros_clave": ["Decay", "Color (Excitation Filter)", "Normalize", "Gate", "Widen Stereo"],
        "cc_mapping": {"74": "Color Brightness", "71": "Decay Time"},
        "estructura_fst": "Chunk 0xD5 de 20 bytes (5 parámetros enteros de 32 bits)."
    },
    "PoiZone": {
        "termino_rae": "Sintetizador sustractivo de dos osciladores con puerta de trance y arpegiador",
        "definicion_rae": "Sintetizador polifónico sustractivo de arquitectura directa (sin menús ocultos) con dos osciladores (Sierra/Pulso), modulación de anchura de pulso, sincronización y modulación en anillo, unísono de 4 voces, filtro multimodo y puerta rítmica de 16 pasos.",
        "familia_dsp": "Síntesis Sustractiva Analógica Virtual + Compuerta Rítmica (Trance Gate)",
        "ecuacion_transferencia": "y[n] = Gate_16(n) * Delay_Chorus(SVF(Osc_A[n] + Osc_B[n] + Noise[n], f_c, Q))",
        "arquitectura_interna": ["Oscilador A y B con Sync y Ring Mod", "Filtro LP/BP/HP con seguimiento de teclado", "2 Envolventes ADSR + LFO + Unísono", "Trance Gate de 16 pasos + Arpegiador + Delay/Chorus"],
        "parametros_clave": ["Osc Balance", "Pulse Width", "Filter Cutoff & Res", "Trance Gate Wet & Pattern", "Unison Detune"],
        "cc_mapping": {"74": "Cutoff", "71": "Resonance", "1": "LFO Amount"},
        "estructura_fst": "Chunk 0xD5 con vector de parámetros y máscara de 16 bits del Trance Gate."
    },
    "ReWired": {
        "termino_rae": "Cliente-anfitrión de interconexión interprocesos de audio y transporte (Protocolo ReWire)",
        "definicion_rae": "Puente de memoria compartida heredado para sincronizar el reloj de transporte, envíos MIDI y hasta 64 canales de audio en tiempo real con aplicaciones externas compatibles con ReWire.",
        "familia_dsp": "Transferencia IPC Síncrona de Bloques PCM y Reloj PPQ",
        "ecuacion_transferencia": "y_{ch}[n] = SharedMemoryRing_ReWire[ch, n]",
        "arquitectura_interna": ["Selector de dispositivo ReWire esclavo", "Bus de 16 buses MIDI", "Enrutador multicanal hacia el mezclador"],
        "parametros_clave": ["Device Selection", "Multi-Output Routing"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con identificador del proceso esclavo."
    },
    "Sakura": {
        "termino_rae": "Sintetizador de instrumentos de cuerda por modelado físico de cinco etapas acústicas",
        "definicion_rae": "Modelador físico de alta precisión para instrumentos de cuerda frotada, pulsada y percutida (violín, violonchelo, koto, shamisen, guitarra acústica) que simula las 5 etapas físicas: Contacto (impulso mecánico), Generación de vibración, Interacción de dos cuerdas independientes, Resonancia de caja armónica de 8 bandas y Espacio acústico.",
        "familia_dsp": "Doble Guía de Ondas Acoplada con No Linealidad de Fricción de Arco + Banco de 8 Resonadores de Caja",
        "ecuacion_transferencia": "s_i[n] = Exc_BowPluck[n] + H_string_i(z)*s_i[n - D_i]; y[n] = Chorus_Rev(sum_{b=1}^8 H_body_b(z)*(s_1[n] + s_2[n]))",
        "arquitectura_interna": ["Etapa 1: Excitador de Contacto/Fricción", "Etapa 2 & 3: Dos Líneas de Retardo de Cuerda con Damping y No Linealidad", "Etapa 4: Ecualizador Resonante de Cuerpo de 8 filtros pico", "Etapa 5: Chorus y Reverberación Acústica"],
        "parametros_clave": ["Contact Hardness/Noise", "String 1/2 Decay & Damp", "String Feedback", "Body Resonator Freqs 1..8"],
        "cc_mapping": {"1": "Vibrato Depth", "74": "String Damping", "71": "Body Resonance Mix", "11": "Bow Pressure"},
        "estructura_fst": "Chunk 0xD5 con coeficientes de las 2 cuerdas y los 8 resonadores de cuerpo."
    },
    "Sawer": {
        "termino_rae": "Emulador de modelado físico del sintetizador analógico soviético Polivoks (1982)",
        "definicion_rae": "Recreación de los circuitos analógicos con amplificadores operacionales soviéticos (KR140UD12) del mítico Polivoks, célebre por la inestabilidad armónica de su oscilador diente de sierra y la resonancia salvaje y auto-oscilante de su filtro de frecuencia de corte programable.",
        "familia_dsp": "Oscilador con Deriva Analógica + Filtro de Estado Variable No Lineal (Op-Amp Soviet Saturation)",
        "ecuacion_transferencia": "y[n] = FX(SVF_Polivoks(Saw_Drift[n] + Sub_Oct[n] + Noise[n], f_c, Q_nonlinear))",
        "arquitectura_interna": ["Oscilador principal Saw con Sync y Suboscilador (-1/-2 oct)", "Filtro Polivoks LP/BP/HP con Drive de amplificador operacional", "Arpegiador + Secuenciador MIDI de 8 pasos", "Chorus, Phaser, Delay y Reverb"],
        "parametros_clave": ["Sub Osc Level & Phase", "Noise Level", "Filter Cutoff, Resonance & Drive", "Unison Voices"],
        "cc_mapping": {"74": "Filter Cutoff", "71": "Filter Resonance", "1": "LFO Depth"},
        "estructura_fst": "Chunk 0xD5 con parámetros analógicos y secuencia de 8 pasos."
    },
    "SimSynth": {
        "termino_rae": "Sintetizador analógico virtual de tres osciladores con filtro de estado variable",
        "definicion_rae": "Sintetizador polifónico clásico inspirado en los diseños analógicos de los años ochenta: tres osciladores con calidez de fase (Warm) y seguimiento de envolvente, sección SVF programable con barrido doble (Cutoff 1 -> Cutoff 2) y coro integrado.",
        "familia_dsp": "Síntesis Sustractiva de 3 Osciladores + Filtro SVF Doble con Barrido de Frecuencia",
        "ecuacion_transferencia": "y[n] = Chorus(SVF(sum_{i=1}^3 Osc_i[n], f_c(t), Q))",
        "arquitectura_interna": ["3 Osciladores con Ring Mod, Warmth (duplicación detune) y LFO", "Filtro SVF con Highpass, Bandpass y Lowpass", "Envolventes de Amplitud y Filtro + Chorus"],
        "parametros_clave": ["Osc 1..3 Shape & Warm", "SVF Cutoff, Bandwidth &kb Track", "Filter Env Amount", "Chorus Mix"],
        "cc_mapping": {"74": "SVF Cutoff", "71": "SVF Emphasis (Resonance)"},
        "estructura_fst": "Chunk 0xD5 con estado de los 3 osciladores y sección SVF."
    },
    "Slicex": {
        "termino_rae": "Estación avanzada de disección de bucles con doble plato, articuladores y edición espectral",
        "definicion_rae": "Herramienta insignia de troceado y manipulación rítmica de FL Studio: incorpora dos platos de muestras independientes (Deck A y B), el motor completo de edición de audio y scripts de Edison, 8 articuladores multipunto de filtro/tono/velocidad y asignación individual de cada rebanada a cualquier canal del mezclador.",
        "familia_dsp": "Detección Multibanda de Ataques + 8 Articuladores con Filtros SVF en Serie/Paralelo",
        "ecuacion_transferencia": "y_region[n] = Art_SVF_{1..8}(Deck_{A,B}[Region_i, n * Speed_i]) -> MixerTrack_{Offset_i}",
        "arquitectura_interna": ["Doble Plato de Audio (Deck A / Deck B) con motor Edison embebido", "Detector de marcadores de transitorios por sensibilidad dual", "8 Articuladores completos (Vol, Filter LP/BP/HP, Pitch, Speed, Start)", "Modulación X/Y continua por nota en Piano Roll"],
        "parametros_clave": ["Region Articulator (1..8)", "Filter Cutoff & Res", "Master Pitch", "Deck A/B Mix", "Mod X / Mod Y"],
        "cc_mapping": {"1": "Master Mod X", "11": "Master Mod Y", "74": "Articulator 1 Cutoff"},
        "estructura_fst": "Chunk 0xD5 masivo con marcadores de región, 8 articuladores y PCM de ambos platos."
    },
    "Soundfont Player": {
        "termino_rae": "Reproductor polifónico de bancos de muestras normalizados SoundFont 2 (.sf2)",
        "definicion_rae": "Motor nativo de 64 bits de reproducción de bancos de instrumentos multipista en formato SoundFont (.sf2), con interpolación de alta calidad, envolvente ADSR superpuesta, LFO de vibrato y envíos internos de reverberación y coro.",
        "familia_dsp": "Reproducción de Tablas PCM .sf2 con Interpolación Sinc y Envolventes Modulares",
        "ecuacion_transferencia": "y[n] = Env_ADSR(n) * SF2_Zone(MIDI_Patch, MIDI_Bank, Key, Vel)[n]",
        "arquitectura_interna": ["Analizador de contenedores RIFF sfbk (.sf2)", "Selector de Banco y Parche", "Sobreescritura de Envolvente, LFO y Cutoff"],
        "parametros_clave": ["Patch", "Bank", "Reverb Send", "Chorus Send", "Env Attack/Decay/Sustain/Release", "Cutoff"],
        "cc_mapping": {"74": "Filter Cutoff", "91": "Reverb Send", "93": "Chorus Send"},
        "estructura_fst": "Chunk 0xD5 con ruta al archivo .sf2, banco, programa y offsets de envolvente."
    },
    "Sytrus": {
        "termino_rae": "Sintetizador matricial híbrido de seis operadores FM, modulación en anillo y síntesis aditiva",
        "definicion_rae": "Joya de la corona de la síntesis matemática en FL Studio: 6 operadores independientes (cada uno un sintetizador aditivo de 256 armónicos con bloqueo de fase) interconectados mediante una matriz 6x6 bidireccional de Modulación de Frecuencia (FM) y Modulación en Anillo (RM), 3 filtros multimodo en serie/paralelo con distorsión waveshaper, unidad de coro/delay/reverb y soporte nativo de escalas microtonales Scala (.scl).",
        "familia_dsp": "Matriz 6x6 de Modulación de Fase/Frecuencia + Modulación en Anillo + 3 Filtros SVF + Waveshaper",
        "ecuacion_transferencia": "Op_i(t) = A_i(t) * Wave_i(2*pi*f_i*t + sum_{j=1}^6 M^{FM}_{j,i}*Op_j(t)) * prod_{j=1}^6 (1 + M^{RM}_{j,i}*Op_j(t))",
        "arquitectura_interna": ["6 Operadores Aditivos/Tabla de Ondas con ratio de frecuencia y offset en Hz", "Matriz 6x6 de FM + Matriz 6x6 de RM", "3 Unidades de Filtro SVF + Conformador de Onda (Waveshaper) cada una", "Más de 200 Articuladores Multipunto (ENV, LFO, KEY, VEL, MOD X, MOD Y, UNISON)", "Unidad de Efectos (Chorus de hasta 8 órdenes, 3 Líneas de Delay, Reverb)"],
        "parametros_clave": ["Matrix FM Knobs (Op j -> Op i)", "Op Frequency Ratio & Offset Hz", "Filter 1..3 Cutoff & Res", "Master Pitch / Unison Order", "Mod X / Mod Y"],
        "cc_mapping": {"1": "Modulator X (Macro Cutoff/FM Index)", "11": "Modulator Y (Macro Resonance/Timbre)", "74": "Filter 1 Cutoff"},
        "estructura_fst": "Chunk 0xD5 con la matriz 6x6 flotante, 6 tablas de 256 armónicos y grafos de los 200+ articuladores."
    },
    "Toxic Biohazard": {
        "termino_rae": "Sintetizador híbrido de seis osciladores con matriz FM y secuenciador polifónico de sesenta y cuatro pasos",
        "definicion_rae": "Sintetizador FM/sustractivo de carácter oscuro y cristalino cuyos 6 osciladores calculan formas de onda de alta precisión en tiempo real (cero aliasing a frecuencias ultrasónicas), combinando una matriz FM 6x6, filtro analógico modelado con resonancia cálida, ecualizador de 8 bandas y un secuenciador de 64 pasos divisible en dos mitades de 32.",
        "familia_dsp": "Síntesis FM/Sustractiva de 6 Osciladores con Cálculo Analítico Sin Aliasing",
        "ecuacion_transferencia": "y[n] = EQ_8Band(FX(Filter_Analog(sum_{i=1}^6 Pan_i * Osc_i(w_i*t + sum_j FM_{j,i}*Osc_j(t)))))",
        "arquitectura_interna": ["6 Osciladores con ondas analíticas y carga de muestras WAV", "Matriz de Modulación FM 6x6", "Filtro Multimodo con saturación Drive", "Secuenciador inteligente de 64 pasos", "Ecualizador de 8 bandas + 2 ranuras de efectos (Phaser, Flanger, Delay, Reverb, Lo-Fi)"],
        "parametros_clave": ["Osc 1..6 Pitch/Mix/Drive", "FM Matrix Amounts", "Filter Cutoff, Res & Env", "EQ Bands 1..8"],
        "cc_mapping": {"74": "Filter Cutoff", "71": "Filter Resonance", "1": "Mod Wheel Matrix"},
        "estructura_fst": "Chunk 0xD5 con la matriz 6x6, tablas de onda, secuencia de 64 pasos y EQ."
    },
    "Transistor Bass": {
        "termino_rae": "Emulador de circuito analógico del sintetizador de bajo ácido Roland TB-303 (1981)",
        "definicion_rae": "Modelado físico a nivel de transistores y condensadores del legendario sintetizador monofónico de ácido: reproduce exactamente el oscilador de sierra/cuadrada desplazada, el filtro escalera de diodos de 18 dB/octava (3 polos acoplados), el circuito acumulador de acento (Sweep/Decay coupling) y un secuenciador interno de 16 pasos con ligaduras (Slide) y acentos.",
        "familia_dsp": "Filtro Escalera de Diodos No Lineal de 18 dB/oct (ZDF) + Circuito Acumulador de Acento RC",
        "ecuacion_transferencia": "y[n] = Dist_Pedal(DiodeLadder_18dB(Osc_{Saw/Sq}[n], f_c + E_env(Accent)*Mod, Q_res))",
        "arquitectura_interna": ["Oscilador TB-303 con ajuste continuo de forma de onda (Waveform tweak)", "Filtro escalera de 3 polos efectivos (18 dB/oct)", "Circuito de Acento no lineal acoplado a resonancia", "Secuenciador de 16 pasos con Gate, Slide y Accent", "Pedal de distorsión Overdrive + Delay/Reverb"],
        "parametros_clave": ["Tuning", "Waveform", "Cutoff", "Resonance", "Env Mod", "Decay", "Accent", "Distortion Drive"],
        "cc_mapping": {"74": "Cutoff Frequency", "71": "Resonance", "1": "Env Mod", "11": "Accent Amount"},
        "estructura_fst": "Chunk 0xD5 con los parámetros de circuito y los bancos de patrones de 16 pasos."
    },
    "Wasp": {
        "termino_rae": "Sintetizador híbrido de tres osciladores digitales y filtro analógico de estado variable",
        "definicion_rae": "Sintetizador inspirado en el EDP Wasp británico de 1978: combina tres osciladores controlados digitalmente con modulación de anchura de pulso, sincronización y modulación de frecuencia junto con un filtro de estado variable de distorsión áspera y dos LFOs.",
        "familia_dsp": "Síntesis Sustractiva Híbrida Digital-Analógica con Distorsión de Filtro",
        "ecuacion_transferencia": "y[n] = SVF_Distorted(Osc_1[n] + Osc_2[n] + Osc_3_Sub[n] + Noise[n], f_c, Q, Drive)",
        "arquitectura_interna": ["2 Osciladores principales + 1 Suboscilador + Ruido", "Filtro multimodo (LP, HP, BP, Notch) con distorsión ajustable", "2 Envolventes ADSR + 2 LFOs"],
        "parametros_clave": ["Osc 1/2 Coarse/Fine/PW", "FM & RingMod", "Cutoff, Resonance & Filter Distortion", "LFO 1/2 Speed & Amt"],
        "cc_mapping": {"74": "Cutoff", "71": "Resonance", "1": "FM Depth"},
        "estructura_fst": "Chunk 0xD5 de parámetros de Wasp."
    },
    "Wasp XT": {
        "termino_rae": "Sintetizador Wasp extendido con osciladores en desafinación dual y envolventes encadenadas",
        "definicion_rae": "Evolución del sintetizador Wasp que añade modo de oscilador dual desafinado (Dual Osc), modulación de amplitud cruzada, fundido entre dos filtros y mayor control sobre la etapa de distorsión.",
        "familia_dsp": "Síntesis Sustractiva de Doble Filtro con Modulación en Anillo y Distorsión",
        "ecuacion_transferencia": "y[n] = Crossfade(SVF_1(x[n]), SVF_2(x[n])) con saturación no lineal.",
        "arquitectura_interna": ["3 Osciladores con modo Dual Detune", "Doble modo de filtro con distorsión", "2 LFOs sincronizables + 2 ADSR"],
        "parametros_clave": ["Dual Osc Detune", "Cutoff & Res", "Distortion", "Env Mod"],
        "cc_mapping": {"74": "Cutoff", "71": "Resonance"},
        "estructura_fst": "Chunk 0xD5 de parámetros de Wasp XT."
    },
    "Wave Traveller": {
        "termino_rae": "Simulador de tornamesa y rayado de vinilo (scratching) gobernado por curvas de esplines",
        "definicion_rae": "Generador especializado en turntablism que asigna a cada nota MIDI una curva bidimensional de posición de muestra frente al tiempo (velocidad instantánea es la derivada de la curva) junto con una envolvente de volumen del fader cruzado (crossfader muting).",
        "familia_dsp": "Integración Diferencial de Fase de Muestra por Derivada de Espline (v(t) = dPos(t)/dt)",
        "ecuacion_transferencia": "y(t) = Env_Fader(t) * Sample(Pos_Spline(t)), donde la altura instantánea es proporcional a dPos_Spline(t)/dt.",
        "arquitectura_interna": ["Motor de interpolación sinc de velocidad variable y reversa", "Editor de curvas de desplazamiento de vinilo por tecla MIDI", "Editor de envolvente de corte de crossfader (Mute envelope)"],
        "parametros_clave": ["Spline Position Curve", "Volume Gate Curve", "Turntable Speed / Vinyl Inertia", "Patch Note Selection"],
        "cc_mapping": {"1": "Scratch Speed Scaling"},
        "estructura_fst": "Chunk 0xD5 con las curvas spline de cada nota MIDI y la muestra de audio."
    }
}

# -----------------------------------------------------------------------------
# 5. INGENIERÍA INVERSA RAE DE LOS 89 EFECTOS NATIVOS DE FL STUDIO 2025
# -----------------------------------------------------------------------------
EFFECTS_RAE_SPEC: Dict[str, Dict[str, Any]] = {
    "Control Surface": {
        "termino_rae": "Superficie de mando y diseño de paneles de control paramétrico",
        "definicion_rae": "Efecto sin alteración directa del flujo de audio que permite construir interfaces gráficas a medida (perillas, cursores, almohadillas X/Y, interruptores) para gobernar múltiples parámetros del mezclador o de Patcher simultáneamente.",
        "familia_dsp": "Enrutamiento de Señales de Control Interno (1:N Parameter Mapping)",
        "ecuacion_transferencia": "y_audio[n] = x_audio[n]; Param_target_k = f_link_k(Control_UI_m)",
        "arquitectura_interna": ["Motor vectorial de widgets UI", "Bus de salida de controladores internos de FL Studio"],
        "parametros_clave": ["Custom Knobs, Sliders, Buttons, XY Pads"],
        "cc_mapping": {"1": "Macro Control 1"},
        "estructura_fst": "Chunk 0xD5 con definición geométrica y visual de los controles."
    },
    "Distructor": {
        "termino_rae": "Procesador modular de cuatro ranuras de distorsión, filtrado, coro y simulación de altavoz",
        "definicion_rae": "Estación de saturación multietapa que encadena 4 módulos intercambiables: Distorsión (modelos de Harmor, Blood Overdrive, Fast Dist y Crusher), Filtro multimodo/peine, Coro estereofónico y Convolucionador de pantallas de guitarra y amplificadores.",
        "familia_dsp": "Cascada de 4 Etapas (Saturación No Lineal + Filtro Biquad/Comb + Coro + Convolución FIR de Gabinete)",
        "ecuacion_transferencia": "y[n] = Stage_4(Stage_3(Stage_2(Stage_1(x[n]))))",
        "arquitectura_interna": ["Ranura 1..4 reordenables", "Módulo Distorsión (Asymmetric, Cubed, Ribbons, Blood, Crusher)", "Módulo Filtro (LP/BP/HP/Comb)", "Módulo Chorus", "Módulo Speaker Cabinet (Respuestas al Impulso FIR)"],
        "parametros_clave": ["Preamp / Threshold", "Distortion Type", "Filter Cutoff/Res", "Cabinet IR Selection"],
        "cc_mapping": {"74": "Filter Cutoff", "1": "Distortion Drive"},
        "estructura_fst": "Chunk 0xD5 con configuración de las 4 ranuras y selección de IR."
    },
    "EQUO": {
        "termino_rae": "Ecualizador gráfico adaptativo de banco de filtros con morfismo y aprendizaje espectral",
        "definicion_rae": "Ecualizador gráfico de 32 bandas con capacidad de analizar el espectro de entrada ('Analyze') para esculpir automáticamente una curva complementaria o inversa, y de interpolar entre 8 bancos de curvas mediante un parámetro de morfismo.",
        "familia_dsp": "Banco de 32 Filtros Paso-Banda con Interpolación de Bancos y Análisis Espectral",
        "ecuacion_transferencia": "y[n] = sum_{b=1}^{32} G_b(Morph) * Pan_b * H_band_b(z)[x[n]]",
        "arquitectura_interna": ["Banco de 32 bandas en octavas fraccionarias", "8 Bancos de curvas (Volumen y Paneo por banda) con perilla Morph", "Analizador de espectro inverso/complementario"],
        "parametros_clave": ["Morph (Bank 1..8)", "Mix", "Smooth", "Shift Frequency"],
        "cc_mapping": {"1": "Bank Morph", "74": "Frequency Shift"},
        "estructura_fst": "Chunk 0xD5 con las 8 matrices de 32 bandas (ganancia y paneo)."
    },
    "Edison": {
        "termino_rae": "Laboratorio de grabación, edición de onda, cirugía espectral y análisis de convolución",
        "definicion_rae": "Editor y grabador de audio integrado en el mezclador que opera en el dominio del tiempo y en el espectrograma de alta resolución, dotado de eliminación de ruido por huella espectral, igualación espectral, troceado automático de bucles y motor de scripts Python.",
        "familia_dsp": "STFT de Fase Exacta, Sustracción Espectral de Ruido y Edición de Muestras en Memoria",
        "ecuacion_transferencia": "Sustracción de ruido: |Y(m,k)| = max(0, |X(m,k)| - alpha * N_profile(k))",
        "arquitectura_interna": ["Búfer de audio RAM de 32 bits", "Motor STFT de cirugía espectral", "Denoiser por perfil de ruido", "Troceador de regiones y exportador Drag-and-Drop"],
        "parametros_clave": ["Record Mode (Now/On Input/On Play)", "Denoise Threshold/Amount", "Blur/Reverb Convolver"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 que incrusta íntegramente el archivo WAV de 32 bits y sus marcadores."
    },
    "Effector": {
        "termino_rae": "Procesador táctil de doce algoritmos de efectos en tiempo real gobernados por matriz X/Y",
        "definicion_rae": "Unidad de efectos de directo con 12 algoritmos seleccionables (Distortion, Lo-Fi, Flanger, Phaser, Filter LP/HP, Delay, Reverb, Stereo Pan, Binaural, Granulizer, Vocal Formants, Ring Mod) controlados por una almohadilla X/Y con modulación rítmica LFO.",
        "familia_dsp": "Conmutador de 12 Motores DSP Controlado por Coordenadas Cartesianas (X, Y) y Compuerta",
        "ecuacion_transferencia": "y[n] = Mix(x[n], Engine_{alg}(x[n], X(t), Y(t)))",
        "arquitectura_interna": ["12 Motores DSP independientes", "Almohadilla X/Y con interruptor Bypass (Mute FX)", "Modulador rítmico sincronizado a tempo (1/16..4 compases)"],
        "parametros_clave": ["FX Algorithm (1..12)", "Param X", "Param Y", "Bypass Switch", "Tempo Mod Depth", "Dry/Wet"],
        "cc_mapping": {"1": "Param X", "11": "Param Y", "74": "Dry/Wet Level"},
        "estructura_fst": "Chunk 0xD5 compacto con índice de algoritmo y coordenadas X/Y."
    },
    "Emphasis": {
        "termino_rae": "Limitador maestro multietapa de pico verdadero y realzador dinámico de sonoridad",
        "definicion_rae": "Procesador de masterización de alta precisión incorporado en FL Studio 2025 que combina filtrado de pre-énfasis tonal (Tilt/Baxandall), saturación instantánea de cresta, compresión de programa y limitación de muro infranqueable con sobremuestreo polifásico hasta 16x.",
        "familia_dsp": "Pre-Énfasis Espectral + Recorte Armónico + Limitador de Pico Verdadero Sobremuestreado",
        "ecuacion_transferencia": "y[n] = Downsample_M(Brickwall_ISP(SoftClip(PreEmphasis_EQ(Upsample_M(x[n])))))",
        "arquitectura_interna": ["Etapa de ganancia de entrada y tono (Tone/Tilt)", "Etapa de recuperación e impacto transitorio", "Limitador True Peak con sobremuestreo de fase lineal/mínima"],
        "parametros_clave": ["Input Gain", "Ceiling dBTP", "Release Speed", "Tone Balance", "Oversampling Factor"],
        "cc_mapping": {"7": "Input Drive", "74": "Tone Balance"},
        "estructura_fst": "Chunk 0xD5 con parámetros de techo dBTP y factor de sobremuestreo."
    },
    "Emphasizer": {
        "termino_rae": "Maximizado compacto de sonoridad y saturación armónica de cresta",
        "definicion_rae": "Versión simplificada y de baja latencia del motor Emphasis orientada a buses de batería, sintetizadores e insertos individuales para incrementar la densidad percibida sin rebasar el techo digital.",
        "familia_dsp": "Saturación de Cresta + Limitación Rápida de Bus",
        "ecuacion_transferencia": "y[n] = Ceiling * tanh(Drive * x[n] / Ceiling)",
        "arquitectura_interna": ["Preamplificador de empuje (Drive)", "Circuito de saturación/limitación", "Filtro de carácter tonal"],
        "parametros_clave": ["Drive", "Ceiling", "Character"],
        "cc_mapping": {"1": "Drive"},
        "estructura_fst": "Chunk 0xD5 compacto de parámetros de bus."
    },
    "FL Studio Mobile Rack FX": {
        "termino_rae": "Bastidor de efectos modulares del motor FL Studio Mobile",
        "definicion_rae": "Contenedor de inserción que permite utilizar la cadena de efectos ligeros de FL Studio Mobile (Multi FX, Autoduck, Limiter, Analyzer, Tuner, Comb Filter) dentro del mezclador principal.",
        "familia_dsp": "Cadena de Procesamiento Modular Ligero de Coma Flotante",
        "ecuacion_transferencia": "y[n] = MobileFX_Chain(x[n])",
        "arquitectura_interna": ["Ranuras de efectos Mobile encadenables"],
        "parametros_clave": ["Mix", "Module Parameters"],
        "cc_mapping": {"1": "Macro Mix"},
        "estructura_fst": "Chunk 0xD5 con el estado de la cadena FX Mobile."
    },
    "Frequency Shifter": {
        "termino_rae": "Desplazador lineal de frecuencias por transformada de Hilbert y modulación en banda lateral única",
        "definicion_rae": "Procesador que suma una cantidad constante de hercios (+Delta_f Hz) a todas las componentes espectrales de una señal (rompiendo la relación armónica y produciendo timbres metálicos o efectos Barberpole Phaser), empleando una red de desfase de 90 grados (transformada de Hilbert) y modulación en cuadratura.",
        "familia_dsp": "Modulación de Banda Lateral Única (SSB) mediante Red Polifásica de Hilbert",
        "ecuacion_transferencia": "y(t) = x(t)*cos(2*pi*Delta_f*t) - Hilbert(x(t))*sin(2*pi*Delta_f*t)",
        "arquitectura_interna": ["Red de filtros paso-todo en cuadratura (90 deg Hilbert)", "Oscilador en cuadratura (Seno/Coseno) de escala lineal (Hz) o logarítmica", "Bucle de realimentación (Feedback) para efectos de remolino espectral"],
        "parametros_clave": ["Frequency Shift Hz", "Range (20Hz / 2kHz / 20kHz)", "Mix (Freq Shift vs Ring Mod)", "Feedback", "Stereo Spread"],
        "cc_mapping": {"74": "Frequency Shift", "71": "Feedback"},
        "estructura_fst": "Chunk 0xD5 con parámetros de desplazamiento y realimentación."
    },
    "Frequency Splitter": {
        "termino_rae": "Divisor espectral de tres bandas con filtros de cruce Linkwitz-Riley y fase lineal",
        "definicion_rae": "Separador de frecuencias de precisión quirúrgica que divide una señal en tres bandas independientes (Graves, Medios, Agudos) con pendientes de 6 a 96 dB/octava en modo de latencia cero (Linkwitz-Riley IIR) o fase lineal perfecta (FIR), permitiendo enviar cada banda a un canal distinto del mezclador o de Patcher.",
        "familia_dsp": "Filtros de Cruce Complementarios (Linkwitz-Riley LR4/LR8 o FIR Simétrico de Fase Lineal)",
        "ecuacion_transferencia": "H_low(z) + H_mid(z) + H_high(z) = z^(-D) (reconstrucción de magnitud y fase unitaria exacta).",
        "arquitectura_interna": ["2 Frecuencias de cruce ajustables (Low-Mid, Mid-High)", "Selector de fase lineal o latencia mínima", "3 Salidas independientes de envío (Send Outputs) para procesamiento multibanda en paralelo"],
        "parametros_clave": ["Low-Mid Crossover Hz", "Mid-High Crossover Hz", "Slope (6..96 dB/oct)", "Linear Phase Mode", "Band Gains"],
        "cc_mapping": {"74": "Low-Mid Crossover", "71": "Mid-High Crossover"},
        "estructura_fst": "Chunk 0xD5 con frecuencias de cruce, pendientes y matriz de salidas."
    },
    "Fruity 7 Band EQ": {
        "termino_rae": "Ecualizador gráfico estático de siete bandas de octava",
        "definicion_rae": "Ecualizador clásico de consumo mínimo de CPU compuesto por 7 filtros biquad en cascada centrados en 63 Hz, 125 Hz, 250 Hz, 500 Hz, 1 kHz, 2.5 kHz y 6 kHz (±18 dB por banda).",
        "familia_dsp": "Cascada de 7 Filtros Biquad IIR de Segundo Orden (Estantes Extremos + 5 Campanas)",
        "ecuacion_transferencia": "H(z) = prod_{k=1}^7 ((b_{0,k} + b_{1,k}*z^-1 + b_{2,k}*z^-2) / (1 + a_{1,k}*z^-1 + a_{2,k}*z^-2))",
        "arquitectura_interna": ["7 Deslizadores de ganancia (±18 dB) a frecuencias fijas"],
        "parametros_clave": ["Band 63Hz", "Band 125Hz", "Band 250Hz", "Band 500Hz", "Band 1kHz", "Band 2.5kHz", "Band 6kHz"],
        "cc_mapping": {"74": "Band 1kHz", "71": "Band 6kHz"},
        "estructura_fst": "Chunk 0xD5 de 28 bytes (7 enteros de 32 bits)."
    },
    "Fruity Balance": {
        "termino_rae": "Atenuador de ganancia y posicionador panorámico libre de artefactos de cremallera",
        "definicion_rae": "Etapa de ganancia y paneo dedicada a la automatización de volumen sin ocupar el deslizador principal del canal del mezclador, provista de interpolación suave por muestra.",
        "familia_dsp": "Multiplicador Lineal de Matriz Estereofónica con Suavizado Exponencial de Un Polo",
        "ecuacion_transferencia": "L'[n] = g_vol[n] * g_panL[n] * L[n]; R'[n] = g_vol[n] * g_panR[n] * R[n]",
        "arquitectura_interna": ["Potenciómetro de Pan (-100%..+100%)", "Potenciómetro de Volumen (-inf..+5.6 dB)"],
        "parametros_clave": ["Pan", "Volume"],
        "cc_mapping": {"7": "Volume", "10": "Pan"},
        "estructura_fst": "Chunk 0xD5 de 8 bytes (2 int32: Pan y Volume)."
    },
    "Fruity Bass Boost": {
        "termino_rae": "Realzador resonante de frecuencias graves y subgraves",
        "definicion_rae": "Filtro de campana de segundo orden de alto factor de mérito (Q) diseñado para amplificar selectivamente la fundamental de bombos y bajos entre 40 Hz y 120 Hz.",
        "familia_dsp": "Filtro Biquad de Pico (Peaking EQ) en Región Subgrave",
        "ecuacion_transferencia": "H(z) = Biquad_Peak(f_0 in [40, 120] Hz, Gain_dB)",
        "arquitectura_interna": ["Selector de frecuencia central", "Potenciómetro de intensidad de realce"],
        "parametros_clave": ["Frequency", "Amount"],
        "cc_mapping": {"74": "Frequency", "71": "Amount"},
        "estructura_fst": "Chunk 0xD5 de 8 bytes."
    },
    "Fruity Big Clock": {
        "termino_rae": "Cronómetro visual de gran formato en compases, pulsos o minutos y segundos",
        "definicion_rae": "Utilidad de monitorización visual que muestra la posición actual del cabezal de reproducción con dígitos gigantes para cabinas de grabación o directo.",
        "familia_dsp": "Conversión de Ticks PPQ a Código de Tiempo Visual (Bar:Step:Tick / Min:Sec:Centisec)",
        "ecuacion_transferencia": "y[n] = x[n] (paso transparente de audio)",
        "arquitectura_interna": ["Decodificador de reloj de transporte"],
        "parametros_clave": ["Display Mode (Bars/Time)"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 4 bytes."
    },
    "Fruity Blood Overdrive": {
        "termino_rae": "Saturador asimétrico de modelado de preamplificador y pedal de distorsión",
        "definicion_rae": "Distorsionador clásico de FL Studio con multiplicador de preamplificación (x100), filtro paso-banda de coloración previo a la saturación y etapa de filtrado post-distorsión para domar la aspereza de alta frecuencia.",
        "familia_dsp": "Filtrado Pre-Énfasis + Función de Transferencia No Lineal Asimétrica + Filtro Paso-Bajo Post-Saturación",
        "ecuacion_transferencia": "y[n] = LPF_post(f_nonlinear(BPF_color(PreBand * x[n]) * PreAmp * (1 + 99*x100)))",
        "arquitectura_interna": ["Filtro PreBand y Color", "Etapa PreAmp con interruptor x100", "Filtro PostFilter y compensación PostGain"],
        "parametros_clave": ["PreBand", "Color", "PreAmp", "x100 Switch", "PostFilter", "PostGain"],
        "cc_mapping": {"1": "PreAmp Drive", "74": "Color Frequency"},
        "estructura_fst": "Chunk 0xD5 de 24 bytes (6 float32)."
    },
    "Fruity Center": {
        "termino_rae": "Eliminador de componente continua (DC Offset) en tiempo real",
        "definicion_rae": "Filtro paso-alto de frecuencia de corte sub-infrasónica (~2 Hz) que suprime cualquier desplazamiento asimétrico respecto al cero eléctrico (DC offset) para preservar el margen dinámico completo del mezclador.",
        "familia_dsp": "Filtro Bloqueador de Continua de Primer Orden (DC Blocker IIR)",
        "ecuacion_transferencia": "y[n] = x[n] - x[n-1] + 0.9995 * y[n-1], o H(z) = (1 - z^-1) / (1 - 0.9995*z^-1)",
        "arquitectura_interna": ["Integrador leaky de eliminación DC"],
        "parametros_clave": ["Mode (On / Off)"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 4 bytes."
    },
    "Fruity Chorus": {
        "termino_rae": "Multiplicador coral estereofónico de tres osciladores de baja frecuencia",
        "definicion_rae": "Procesador de ensanchamiento espacial que utiliza líneas de retardo variables moduladas por tres LFOs independientes con control de forma (Seno^x) y filtro de cruce para mantener o excluir las frecuencias bajas.",
        "familia_dsp": "Línea de Retardo Fraccionaria Modulada por Suma de 3 LFOs No Lineales",
        "ecuacion_transferencia": "y[n] = Dry*x[n] + Wet*x(n - D_0 - Depth * sum_{i=1}^3 sin(w_i*t)^(p_i))",
        "arquitectura_interna": ["Línea de retardo interpolada con diferencia estéreo", "3 LFOs con exponente de curvatura", "Filtro de cruce (Cutoff High/Low)"],
        "parametros_clave": ["Delay", "Depth", "Stereo", "LFO 1..3 Freq", "Cross Type & Cutoff", "Wet Only"],
        "cc_mapping": {"74": "Depth", "1": "LFO 1 Freq"},
        "estructura_fst": "Chunk 0xD5 de 44 bytes."
    },
    "Fruity Compressor": {
        "termino_rae": "Compresor monobanda de margen dinámico con curvas de relajación vintage y dura",
        "definicion_rae": "Compresor clásico de respuesta rápida con umbral de 0 a -60 dB, razón de 1:1 a 30:1, ganancia de compensación y cuatro caracteres de rodilla y relajación (Hard, Medium, Vintage, Soft).",
        "familia_dsp": "Detector de Envolvente RMS/Pico con Computación Logarítmica de Ganancia",
        "ecuacion_transferencia": "G_dB[n] = Gain_makeup - max(0, Env_dB[n] - Threshold) * (1 - 1/Ratio)",
        "arquitectura_interna": ["Detector de nivel con Attack/Release", "Computador de ganancia con 4 curvas de rodilla (Hard/Medium/Vintage/Soft)"],
        "parametros_clave": ["Threshold", "Ratio", "Gain", "Attack", "Release", "Type (Hard/Medium/Vintage/Soft)"],
        "cc_mapping": {"74": "Threshold", "71": "Ratio"},
        "estructura_fst": "Chunk 0xD5 de 24 bytes."
    },
    "Fruity Convolver": {
        "termino_rae": "Motor de convolución de latencia cero por respuesta al impulso con editor completo",
        "definicion_rae": "Procesador de convolución particionada que multiplica espectralmente la señal de entrada por cualquier respuesta al impulso grabada o sintetizada (catedrales, muelles, cabinas, filtros de fase lineal), incorporando el motor de edición de Edison para esculpir la envolvente de volumen, estéreo y tono del impulso.",
        "familia_dsp": "Convolución Rápida Particionada No Uniforme en Dominio FFT (Zero-Latency Partitioned Convolution)",
        "ecuacion_transferencia": "y[n] = sum_{m=0}^{L-1} h_IR[m] * x[n - m], calculada por bloques IFFT(FFT(x_p) * FFT(h_p)).",
        "arquitectura_interna": ["Motor de convolución FFT particionada sin latencia", "Editor de onda y espectrograma de la Respuesta al Impulso (IR)", "Envolventes multipunto sobre la IR (Volumen, Pan, Stereo Separation, EQ)", "Grabador de barrido senoidal ( Impulse Response Capturer)"],
        "parametros_clave": ["Dry Level", "Wet Level", "IR Stretch (Pitch/Time)", "Stereo Separation of IR", "Feedback", "EQ Curve"],
        "cc_mapping": {"91": "Wet Level", "74": "IR Stretch"},
        "estructura_fst": "Chunk 0xD5 con el archivo WAV de la Respuesta al Impulso incrustado y sus curvas."
    },
    "Fruity Delay": {
        "termino_rae": "Eco digital elemental sincronizado a subdivisiones de paso",
        "definicion_rae": "Línea de retardo ligera sincronizada en unidades de pasos del secuenciador (1..16 steps) con modo normal, invertido o ping-pong estereofónico.",
        "familia_dsp": "Búfer Circular de Retardo Sincronizado con Realimentación",
        "ecuacion_transferencia": "d[n] = Input * x[n] + Feedback * LP(d[n - N_steps])",
        "arquitectura_interna": ["Línea de retardo circular", "Filtro paso-bajo de realimentación", "Conmutador Ping-Pong"],
        "parametros_clave": ["Input", "Feedback", "Cutoff", "Tempo Steps", "Mode (Normal/Inv/PingPong)"],
        "cc_mapping": {"94": "Input Send", "74": "Feedback Cutoff"},
        "estructura_fst": "Chunk 0xD5 de 20 bytes."
    },
    "Fruity Delay 2": {
        "termino_rae": "Eco estereofónico con desplazamiento de tiempo interaural y filtrado de realimentación",
        "definicion_rae": "Evolución del eco básico que añade control continuo del tiempo de retardo, desplazamiento temporal entre el canal izquierdo y derecho (Time Stereo Offset) para ensanchamiento psicoacústico Haas y paneo de entrada.",
        "familia_dsp": "Doble Línea de Retardo con Desfase Interaural (Efecto Haas) y Realimentación Cruzada",
        "ecuacion_transferencia": "d_L[n] = Pan_L*x_L[n] + fb * H_lp(d_R[n - D_L]); d_R[n] = Pan_R*x_R[n] + fb * H_lp(d_L[n - D_R])",
        "arquitectura_interna": ["2 Líneas de retardo con offset estéreo", "Filtro paso-bajo de amortiguación", "Selector Normal / Invert / Ping-Pong"],
        "parametros_clave": ["Input Pan", "Input Vol", "Dry", "FeedbackMode", "Feedback Vol", "Feedback Cutoff", "Time", "Time Stereo Offset"],
        "cc_mapping": {"74": "Feedback Cutoff", "94": "Wet/Input Vol"},
        "estructura_fst": "Chunk 0xD5 de 32 bytes."
    },
    "Fruity Delay 3": {
        "termino_rae": "Emulador de eco analógico de cinta y cubo de brigada con modulación y degradación digital",
        "definicion_rae": "Línea de retardo maestra de FL Studio: modela físicamente la inestabilidad de velocidad de cinta (Pitch Keep / Resampling Doppler), difusión espacial de las repeticiones, saturación no lineal o reducción de frecuencia de muestreo y profundidad de bits en el bucle de realimentación, y filtro multimodo auto-oscilante.",
        "familia_dsp": "Línea de Retardo de Velocidad Variable (Doppler Tape Interpolation) + Bucle con Filtro SVF, Difusor All-Pass y Bitcrusher",
        "ecuacion_transferencia": "d(t) = x(t) + fb * Saturate_Crush(Diffuser(SVF(d(t - D(t) - LFO(t)))))",
        "arquitectura_interna": ["Interpolador de cinta con efecto Doppler real", "Modulador LFO de tiempo y filtro", "Sección de realimentación con Filtro LP/HP/BP, Difusor (Smear), Saturador/Limitador y Sample Rate/Bit Reduction", "Panner y Expansor Estéreo de salida"],
        "parametros_clave": ["Delay Time (Tempo Sync / ms)", "Stereo Offset", "Feedback Level", "Filter Cutoff & Res", "Diffusion Level/Spread", "Saturation / Bit & Sample Rate Crush", "Modulation Rate/Time"],
        "cc_mapping": {"74": "Feedback Filter Cutoff", "71": "Feedback Resonance", "94": "Wet Level", "1": "Time Modulation"},
        "estructura_fst": "Chunk 0xD5 con todos los coeficientes del bucle analógico/digital."
    },
    "Fruity Delay Bank": {
        "termino_rae": "Estación de ocho bancos de retardo en serie y paralelo con filtrado y granulación",
        "definicion_rae": "Arquitectura matricial de 8 unidades de retardo completas que pueden encadenarse en serie o sumarse en paralelo, cada una provista de filtro de entrada, filtro de realimentación, granulación de eco y envíos hacia el banco siguiente.",
        "familia_dsp": "Red de 8 Líneas de Retardo Acopladas con Granulador y Filtros Multimodo Duales",
        "ecuacion_transferencia": "Para banco k in 1..8: B_k[n] = Delay_Grain_k(Filter_in_k(x[n] + g_{k-1}*B_{k-1}[n]))",
        "arquitectura_interna": ["8 Unidades de Delay independientes", "Filtros SVF de entrada, realimentación y salida por banco", "Módulo de granulación de repeticiones por banco"],
        "parametros_clave": ["Bank 1..8 Time, Feedback, Cutoff, Grain Div, Next Bank Send"],
        "cc_mapping": {"74": "Global Filter Cutoff", "94": "Wet Mix"},
        "estructura_fst": "Chunk 0xD5 con las 8 estructuras de banco."
    },
    "Fruity Fast Dist": {
        "termino_rae": "Distorsionador algebraico instantáneo de doble curva analítica",
        "definicion_rae": "Conformador de onda ultrarrápido con dos ecuaciones de transferencia seleccionables (Tipo A: compresión tangencial suave; Tipo B: recorte abrupto asimétrico con umbral) para bombos gabber, líneas ácidas 303 y sintetizadores.",
        "familia_dsp": "Conformación Estática Sin Memoria (Memoryless Non-Linear Waveshaping)",
        "ecuacion_transferencia": "Tipo A: y = x*(|x| + Pre) / (x^2 + (Pre - 1)*|x| + 1); Tipo B: recorte duro por encima de Threshold.",
        "arquitectura_interna": ["Etapa Preamp", "Conmutador de ecuación A/B con Threshold", "Mezclador Dry/Wet y Post-Gain"],
        "parametros_clave": ["Pre", "Threshold", "Type (A/B)", "Mix", "Post"],
        "cc_mapping": {"1": "Pre Drive", "74": "Threshold"},
        "estructura_fst": "Chunk 0xD5 de 20 bytes (5 int32)."
    },
    "Fruity Fast LP": {
        "termino_rae": "Filtro paso-bajo resonante de dos polos de baja carga computacional",
        "definicion_rae": "Filtro paso-bajo de barrido rápido optimizado para automatización de cortes de pista sin latencia.",
        "familia_dsp": "Filtro IIR de Estado Variable de Segundo Orden (12 dB/octava)",
        "ecuacion_transferencia": "H(z) = b_0 / (1 + a_1*z^-1 + a_2*z^-2)",
        "arquitectura_interna": ["Par Cutoff y Resonance"],
        "parametros_clave": ["Cutoff", "Resonance"],
        "cc_mapping": {"74": "Cutoff", "71": "Resonance"},
        "estructura_fst": "Chunk 0xD5 de 8 bytes."
    },
    "Fruity Filter": {
        "termino_rae": "Filtro de estado variable multimodo con suma ponderada de respuestas",
        "definicion_rae": "Filtro clásico de FL Studio cuya topología de estado variable expone simultáneamente las salidas Paso-Bajo, Paso-Banda y Paso-Alto, permitiendo fundirlas en cualquier proporción junto con un multiplicador de pendiente x2 (12 dB -> 24 dB/oct).",
        "familia_dsp": "Filtro de Estado Variable de Chamberlin (Chamberlin SVF) en Cascada Doble",
        "ecuacion_transferencia": "y[n] = g_LP * LP[n] + g_BP * BP[n] + g_HP * HP[n]",
        "arquitectura_interna": ["Núcleo SVF de 1 o 2 etapas (x2)", "Mezclador independiente de ramas Low Pass, Band Pass y High Pass"],
        "parametros_clave": ["Cutoff Freq", "Resonance", "Low Pass", "Band Pass", "High Pass", "x2 Slope"],
        "cc_mapping": {"74": "Cutoff Freq", "71": "Resonance"},
        "estructura_fst": "Chunk 0xD5 de 24 bytes."
    },
    "Fruity Flanger": {
        "termino_rae": "Rebordeador estereofónico de peine con modulación cruzada e inversión de fase",
        "definicion_rae": "Generador de barrido metálico por línea de retardo corta (0.1 a 20 ms) modulada por LFO, con inversión de polaridad de la señal húmeda y de la realimentación para alternar entre picos y valles impares.",
        "familia_dsp": "Filtro de Peine IIR Modulado en el Tiempo (Time-Varying IIR Comb Filter)",
        "ecuacion_transferencia": "d[n] = x[n] + sgn_fb * fb * d[n - D(t)]; y[n] = Dry*x[n] + sgn_wet * Wet * d[n - D(t)]",
        "arquitectura_interna": ["Línea de retardo corta interpolada", "LFO con forma ajustable", "Inversores de fase Wet y Feedback"],
        "parametros_clave": ["Delay", "Depth", "Rate", "Phase", "Damp", "Feed", "Invert Feedback/Wet"],
        "cc_mapping": {"74": "Depth", "71": "Feedback", "1": "Rate"},
        "estructura_fst": "Chunk 0xD5 de 40 bytes."
    },
    "Fruity Flangus": {
        "termino_rae": "Multiplicador de coro y rebordeado denso de múltiples líneas retardadas en paralelo",
        "definicion_rae": "Híbrido entre Chorus y Flanger que apila múltiples líneas de retardo moduladas y distribuidas en el campo estereofónico con un parámetro de Orden (Order) para ensanchar cuerdas, pads y guitarras.",
        "familia_dsp": "Banco Paralelo de N Filtros de Peine Modulados con Distribución Panorámica",
        "ecuacion_transferencia": "y_{L,R}[n] = Dry*x[n] + Wet * sum_{k=1}^{Order} Pan_k * x(n - D_k(t))",
        "arquitectura_interna": ["Matriz de N retardos modulados (Order)", "Filtro de cruce de graves", "Expansor estéreo"],
        "parametros_clave": ["Order", "Depth", "Speed", "Delay", "Spread", "Stereo", "Cross", "Dry/Wet"],
        "cc_mapping": {"74": "Depth", "1": "Speed"},
        "estructura_fst": "Chunk 0xD5 de 32 bytes."
    },
    "Fruity Formula Controller": {
        "termino_rae": "Evaluador algebraico en tiempo real de funciones matemáticas de control",
        "definicion_rae": "Procesador de señales de control que compila y evalúa en cada tick una expresión matemática arbitraria escrita por el usuario en función de tres variables de entrada (a, b, c), el tiempo musical (SongTime) y funciones trigonométricas o estocásticas.",
        "familia_dsp": "Compilador y Evaluador Simbólico de Expresiones en Coma Flotante",
        "ecuacion_transferencia": "Out(t) = clamp(EvalAST(FormulaString, a(t), b(t), c(t), SongTime(t)), 0.0, 1.0)",
        "arquitectura_interna": ["Analizador sintáctico de expresiones matemáticas (sin, cos, tg, exp, log, sqrt, rand, Tension, Inter)", "3 Potenciómetros de entrada (a, b, c) automatizables", "Monitor oscilográfico de salida"],
        "parametros_clave": ["Variable a", "Variable b", "Variable c", "Formula Expression String"],
        "cc_mapping": {"1": "Variable a", "11": "Variable b", "74": "Variable c"},
        "estructura_fst": "Chunk 0xD5 con los 3 floats (a,b,c) + cadena ASCII de la ecuación matemática."
    },
    "Fruity Free Filter": {
        "termino_rae": "Filtro biquad universal de primer y segundo orden con seis topologías clásicas",
        "definicion_rae": "Filtro quirúrgico ligero con selección de tipo (Low Pass, Band Pass, High Pass, Notch, Low Shelf, Peaking EQ), frecuencia de 10 Hz a 16 kHz y factor Q.",
        "familia_dsp": "Filtro Biquad Direct Form II Transposed (Fórmulas de Robert Bristow-Johnson Audio EQ Cookbook)",
        "ecuacion_transferencia": "H(z) = (b_0 + b_1*z^-1 + b_2*z^-2) / (a_0 + a_1*z^-1 + a_2*z^-2)",
        "arquitectura_interna": ["Calculador de coeficientes RBJ Biquad", "Conmutador de 6 modos de respuesta"],
        "parametros_clave": ["Type", "Freq", "Q", "Gain"],
        "cc_mapping": {"74": "Freq", "71": "Q"},
        "estructura_fst": "Chunk 0xD5 de 16 bytes."
    },
    "Fruity HTML NoteBook": {
        "termino_rae": "Visor de documentos hipertextuales sincronizado al proyecto",
        "definicion_rae": "Utilidad de documentación técnica que renderiza páginas HTML/CSS incrustadas o locales dentro del espacio de trabajo del mezclador.",
        "familia_dsp": "Paso Transparente de Audio (Identidad)",
        "ecuacion_transferencia": "y[n] = x[n]",
        "arquitectura_interna": ["Motor de renderizado HTML"],
        "parametros_clave": ["HTML File Path / Page"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con ruta o contenido HTML."
    },
    "Fruity LSD": {
        "termino_rae": "Sintetizador multitímbrico General MIDI de dieciséis canales sobre banco DLS",
        "definicion_rae": "Módulo de sonidos General MIDI / Roland GS alojado como efecto de inserción que recibe eventos desde canales MIDI Out en un puerto determinado y sintetiza hasta 16 instrumentos orquestales o percusivos simultáneos.",
        "familia_dsp": "Síntesis por Tabla de Ondas General MIDI (Downloadable Sounds DLS Level 1/2)",
        "ecuacion_transferencia": "y[n] = sum_{ch=1}^{16} Chorus_Reverb(DLS_Synth(MIDI_Port, ch)[n])",
        "arquitectura_interna": ["Receptor de Puerto MIDI interno", "16 Ranuras de instrumento GM/GS", "Procesador de Reverb y Chorus global"],
        "parametros_clave": ["MIDI Port", "Channel 1..16 Patch/Vol/Pan/Reverb/Chorus"],
        "cc_mapping": {"7": "Channel Volume", "10": "Channel Pan", "91": "Reverb"},
        "estructura_fst": "Chunk 0xD5 con puerto MIDI y los 16 programas GM."
    },
    "Fruity Limiter": {
        "termino_rae": "Limitador de muro infranqueable con anticipación temporal, compresor con cadena lateral y puerta de ruido",
        "definicion_rae": "Procesador dinámico de referencia en FL Studio que integra tres secciones en serie: un Compresor completo con soporte nativo de cadena lateral (Sidechain) desde cualquier pista del mezclador, un Limitador con ventana de anticipación (Lookahead Attack), curva de liberación doble y saturación tangencial de techo, y una Puerta de Ruido (Noise Gate), todo visualizado en un analizador temporal de envolventes.",
        "familia_dsp": "Compresión por Cadena Lateral + Saturación de Umbral + Limitador de Convolución de Ventana de Ataque Anticipado",
        "ecuacion_transferencia": "y[n] = x[n - L_att] * min(g_comp(E_sc[n]), g_lim(max_{k in [0, L_att]} |x[n-k]|, Ceiling))",
        "arquitectura_interna": ["Línea de retardo de anticipación (Lookahead = Attack Time del Limitador)", "Sección COMP (Threshold, Ratio, Knee, Attack, Release, Ahead, Sidechain Track Selector)", "Sección LIMIT (Ceiling, Gain, Saturation Threshold, Attack, Release, Curve 1..8)", "Sección NOISE GATE (Threshold, Gain, Release)"],
        "parametros_clave": ["Gain", "Limit Ceiling", "Saturation Threshold", "Limit Attack (Lookahead)", "Comp Threshold/Ratio/Knee", "Sidechain Input Index"],
        "cc_mapping": {"7": "Input Gain", "74": "Limit Ceiling", "71": "Comp Threshold"},
        "estructura_fst": "Chunk 0xD5 de 88 bytes con todos los parámetros de Comp, Limit y Gate."
    },
    "Fruity Love Philter": {
        "termino_rae": "Estación matricial de ocho unidades de filtrado multimodo, conformación de onda y envolventes rítmicas",
        "definicion_rae": "Banco de 8 procesadores de filtro idénticos que pueden operar en paralelo o en serie: cada unidad posee un filtro de estado variable de pendiente simple/doble/triple, un distorsionador Waveshaper y 10 articuladores multipunto (frecuencia de corte, resonancia, nivel, waveshaper, paneo) gobernados por LFO, envolvente de patrón y moduladores X/Y.",
        "familia_dsp": "Grafo Serie/Paralelo de 8 Filtros SVF No Lineales + 8 Conformadores de Onda + Desfasador Global",
        "ecuacion_transferencia": "Para unidad k in 1..8: U_k[n] = SVF_k(Waveshaper_k(x[n] + fb_k*U_{k-1}[n]), f_c(Art_k), Q(Art_k))",
        "arquitectura_interna": ["8 Unidades de Filtro + Waveshaper encadenables", "80 Curvas de Articulador Multipunto (10 por unidad: PAT, LFO, MOD X, MOD Y, ENV Follower)", "Seguidor de envolvente de entrada (IEF)", "Sección de Chorus y Delay global"],
        "parametros_clave": ["Unit 1..8 Filter Mode/Cutoff/Res/Drive", "Next Unit Send", "Mod X", "Mod Y"],
        "cc_mapping": {"1": "Modulator X", "11": "Modulator Y", "74": "Unit 1 Cutoff", "71": "Unit 1 Resonance"},
        "estructura_fst": "Chunk 0xD5 con las 8 unidades y los 80 grafos de splines de articulador."
    },
    "Fruity Multiband Compressor": {
        "termino_rae": "Compresor dinámico de tres bandas espectrales con filtros de cruce FIR/IIR",
        "definicion_rae": "Procesador dinámico de masterización y buses que divide el espectro en bandas Grave, Media y Aguda mediante filtros de cruce de 24 dB/octava (modo IIR o FIR de fase lineal) y aplica compresión independiente con limitador de salida.",
        "familia_dsp": "División en 3 Bandas (IIR Butterworth / FIR Fase Lineal) + 3 Compresores Independientes",
        "ecuacion_transferencia": "y[n] = Limiter(sum_{b in {L,M,H}} Comp_b(H_cross_b(z)[x[n]], Thresh_b, Ratio_b))",
        "arquitectura_interna": ["Filtros de cruce Low/Mid y Mid/High (modos FIR y IIR)", "3 Compresores completos (Attack, Release, Knee, Ratio, Threshold, Gain)", "Limitador de techo de salida"],
        "parametros_clave": ["Low/High Crossover Freq", "Band L/M/H Threshold, Ratio, Attack, Release, Gain", "Filter Type (FIR/IIR)", "Limiter Active"],
        "cc_mapping": {"74": "Low Crossover", "71": "High Crossover"},
        "estructura_fst": "Chunk 0xD5 de 84 bytes."
    },
    "Fruity Mute 2": {
        "termino_rae": "Interruptor silencioso de flujo de audio y canales estereofónicos",
        "definicion_rae": "Conmutador automatizable de silenciamiento libre de clics con capacidad de silenciar el canal izquierdo, el derecho o ambos.",
        "familia_dsp": "Compuerta Booleana con Rampa de Desvanecimiento de 2 ms (Anti-Click De-Zipper)",
        "ecuacion_transferencia": "y[n] = (1 - g_mute[n]) * x[n]",
        "arquitectura_interna": ["Interruptor Mute", "Selector de canal (L, R, Stereo)"],
        "parametros_clave": ["Mute Switch", "Channel Mode"],
        "cc_mapping": {"120": "All Sound Off / Mute"},
        "estructura_fst": "Chunk 0xD5 de 8 bytes."
    },
    "Fruity NoteBook": {
        "termino_rae": "Cuaderno de bitácora paginado de texto plano automatizable",
        "definicion_rae": "Bloc de notas de 100 páginas cuyo índice de página puede automatizarse en la Playlist para mostrar letras de canciones o instrucciones técnicas en sincronía con la reproducción.",
        "familia_dsp": "Paso Transparente de Audio (Identidad)",
        "ecuacion_transferencia": "y[n] = x[n]",
        "arquitectura_interna": ["100 Páginas de texto indexadas"],
        "parametros_clave": ["Current Page (1..100)"],
        "cc_mapping": {"1": "Page Index"},
        "estructura_fst": "Chunk 0xD5 con las cadenas de texto de las páginas."
    },
    "Fruity NoteBook 2": {
        "termino_rae": "Cuaderno de bitácora de texto enriquecido (RTF) sincronizado a proyecto",
        "definicion_rae": "Evolución del cuaderno de notas con soporte Unicode completo, formato tipográfico enriquecido y 100 páginas automatizables.",
        "familia_dsp": "Paso Transparente de Audio (Identidad)",
        "ecuacion_transferencia": "y[n] = x[n]",
        "arquitectura_interna": ["Motor RTF de 100 páginas"],
        "parametros_clave": ["Page Index (1..100)"],
        "cc_mapping": {"1": "Page Index"},
        "estructura_fst": "Chunk 0xD5 con flujos RTF UTF-16."
    },
    "Fruity PanOMatic": {
        "termino_rae": "Modulador automático de panorámica y amplitud gobernado por oscilador de baja frecuencia",
        "definicion_rae": "Procesador de trémolo (modulación de volumen) y auto-paneo estereofónico con LFO de tres formas de onda (Seno, Triángulo, Cuadrada) cuya velocidad puede variar en función del nivel de la señal de entrada.",
        "familia_dsp": "Modulación de Amplitud y Matriz Panorámica por LFO",
        "ecuacion_transferencia": "L'[n], R'[n] = Pan_Vol(x[n], Vol + A_v*LFO(t), Pan + A_p*LFO(t))",
        "arquitectura_interna": ["Etapa de Pan y Volumen base", "LFO asignable a Pan o Vol con forma, velocidad y cantidad"],
        "parametros_clave": ["Pan", "Volume", "LFO Target (Off/Vol/Pan)", "LFO Shape", "LFO Amount", "LFO Speed"],
        "cc_mapping": {"10": "Base Pan", "1": "LFO Speed"},
        "estructura_fst": "Chunk 0xD5 de 24 bytes."
    },
    "Fruity Parametric EQ": {
        "termino_rae": "Ecualizador paramétrico clásico de siete bandas biquad",
        "definicion_rae": "Ecualizador paramétrico de 7 bandas independientes donde cada banda permite elegir el tipo de filtro (Low Shelf, Peaking, High Shelf, Low Pass, Band Pass, High Pass, Notch), la frecuencia central, el ancho de banda y la ganancia.",
        "familia_dsp": "Cascada de 7 Filtros Biquad IIR Paramétricos",
        "ecuacion_transferencia": "H(z) = G_master * prod_{k=1}^7 H_biquad(z; Type_k, f_k, BW_k, Gain_k)",
        "arquitectura_interna": ["7 Secciones biquad de coma flotante", "Gráfico de curva de magnitud combinada"],
        "parametros_clave": ["Band 1..7 Type, Level, Freq, Bandwidth", "Main Level"],
        "cc_mapping": {"74": "Band 4 Frequency", "71": "Band 4 Bandwidth"},
        "estructura_fst": "Chunk 0xD5 de 116 bytes."
    },
    "Fruity Parametric EQ 2": {
        "termino_rae": "Ecualizador paramétrico de siete bandas con modo de fase lineal, sobremuestreo y espectrograma de calor",
        "definicion_rae": "Ecualizador quirúrgico de referencia en FL Studio: 7 bandas con pendientes seleccionables de 6 a 48 dB/octava (Orden 2 a 8), desacoplamiento de fase lineal (modo FIR sin rotación de fase para masterización), sobremuestreo 2x para eliminar la compresión de frecuencia cerca de Nyquist y monitor espectral de mapa de calor en segundo plano.",
        "familia_dsp": "Cascada de 7 Filtros IIR Descraneados (Orfanidis) con Sobremuestreo 2x o Convolución FIR de Fase Lineal",
        "ecuacion_transferencia": "En modo Linear Phase: h_FIR[n] = Window(IFFT(|H_target(w)| * exp(-j*w*(N-1)/2))).",
        "arquitectura_interna": ["7 Nodos de filtro (LP, BP, HP, Notch, Low Shelf, Peaking, High Shelf) con orden Gentle 2..Steep 8", "Motor FIR de Fase Lineal (Linear Phase)", "Motor HQ de sobremuestreo 2x / deconvolución de fase en Nyquist", "Analizador FFT de mapa térmico de entrada/salida"],
        "parametros_clave": ["Band 1..7 Type, Order, Gain, Freq, Bandwidth", "Linear Phase Switch", "HQ Oversampling Switch", "Main Level"],
        "cc_mapping": {"74": "Band 1 Frequency", "71": "Band 1 Bandwidth", "1": "Band 4 Gain"},
        "estructura_fst": "Chunk 0xD5 de 136 bytes (usado en Slot 0 de Master_C5_SOTA.fst)."
    },
    "Fruity Peak Controller": {
        "termino_rae": "Seguidor de envolvente de pico y oscilador LFO para modulación de cadena lateral",
        "definicion_rae": "Extractor de la envolvente de amplitud instantánea de una señal de audio (ej. un bombo) que la transforma en dos señales de control interno ('Peak', 'LFO' y 'Peak+LFO') con nivel base, escala positiva o negativa (agachamiento/ducking), tensión de curva y tiempo de caída.",
        "familia_dsp": "Rectificador de Onda Completa + Detector de Pico con Caída Exponencial de Tensión Variable",
        "ecuacion_transferencia": "E[n] = max(|x[n]|, E[n-1]*alpha_decay); Out_Peak[n] = clamp(Base + Vol * f_tension(E[n]), 0, 1)",
        "arquitectura_interna": ["Detector de pico (Base, Volume +/-200%, Tension, Decay)", "Oscilador LFO sincronizable a tempo", "Conmutador Mute (permite dejar o silenciar el audio fuente)"],
        "parametros_clave": ["Peak Base", "Peak Vol (-200%..+200%)", "Peak Tension", "Peak Decay", "LFO Base/Vol/Tension/Speed", "Mute Audio Output"],
        "cc_mapping": {"74": "Peak Decay", "1": "Peak Vol"},
        "estructura_fst": "Chunk 0xD5 de 40 bytes."
    },
    "Fruity Phase Inverter": {
        "termino_rae": "Inversor de polaridad eléctrica por canal estereofónico",
        "definicion_rae": "Utilidad de fase que multiplica por -1 (rotación de 180 grados en todas las frecuencias) el canal izquierdo, el derecho o ambos, para corregir cancelaciones de fase en grabaciones multimicrófono o extraer la señal diferencial.",
        "familia_dsp": "Multiplicación Escalar Unitaria Negativa (-1.0)",
        "ecuacion_transferencia": "L'[n] = s_L * L[n], R'[n] = s_R * R[n], con s_L, s_R in {-1, +1}.",
        "arquitectura_interna": ["Selector de estado (Off, Invert Left, Invert Right)"],
        "parametros_clave": ["Invert Mode (Off / Left / Right)"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 4 bytes."
    },
    "Fruity Phaser": {
        "termino_rae": "Desfasador analógico virtual de hasta veintitrés etapas paso-todo",
        "definicion_rae": "Procesador de barrido espectral que encadena entre 1 y 23 filtros paso-todo (all-pass) cuya frecuencia de rotación de fase oscila entre una frecuencia mínima y máxima mediante un LFO triangular/senoidal.",
        "familia_dsp": "Cascada de M Filtros All-Pass de Primer Orden con Coeficiente Modulado",
        "ecuacion_transferencia": "y[n] = Dry*x[n] + Wet * AP_{1..Stages}(x[n] + fb*y_{ap}[n-1], a(LFO(t)))",
        "arquitectura_interna": ["Red de 1 a 23 etapas All-Pass", "Oscilador de barrido con Min/Max Depth", "Bucle de realimentación resonante"],
        "parametros_clave": ["Sweep Freq", "Min Depth", "Max Depth", "Freq Range", "Stereo Phase", "Nr of Stages (1..23)", "Feedback", "Dry/Wet"],
        "cc_mapping": {"74": "Sweep Freq", "71": "Feedback"},
        "estructura_fst": "Chunk 0xD5 de 36 bytes."
    },
    "Fruity Reeverb": {
        "termino_rae": "Reverberador algorítmico clásico de redes de Schroeder-Moorer",
        "definicion_rae": "Algoritmo clásico de reverberación digital basado en retardos de reflexiones tempranas seguidos de un banco paralelo de filtros de peine realimentados con amortiguación paso-bajo y una cascada de difusores paso-todo.",
        "familia_dsp": "Red Algorítmica de Schroeder-Moorer (8 Peines Paralelos + 4 Difusores All-Pass en Serie)",
        "ecuacion_transferencia": "y[n] = Dry*x[n] + Wet * AllPass_4(sum_{k=1}^8 Comb_k(HPF(x[n - D_pre]), RT60, HF_Damp))",
        "arquitectura_interna": ["Línea de Pre-Delay", "Filtros Low Cut y High Cut de entrada", "Matriz de recinto (Room Size, Diffusion, Decay, High Damping)"],
        "parametros_clave": ["Low Cut", "High Cut", "PreDelay", "Room Size", "Diffusion", "Decay", "High Damping", "Dry", "Reverb Wet"],
        "cc_mapping": {"91": "Reverb Wet", "74": "Decay Time"},
        "estructura_fst": "Chunk 0xD5 de 48 bytes."
    },
    "Fruity Reeverb 2": {
        "termino_rae": "Reverberador algorítmico geométrico con procesamiento Mid/Side y modulación de cola",
        "definicion_rae": "Reverberador algorítmico de estudio con representación geométrica de prisma poligonal (3 a 20 paredes = Difusión), selector de entrada Centro/Lateral (Mid/Side) para reverberar exclusivamente el centro o los lados, modulación de longitud de línea para eliminar resonancias metálicas y multiplicador de graves.",
        "familia_dsp": "Red de Retardo Realimentada Modulada (Modulated FDN) con Codificación de Entrada Mid/Side",
        "ecuacion_transferencia": "x_in = alpha_MS * Mid(x) + (1-alpha_MS)*Side(x); y = Dry*x + ER*EarlyRef(x_in) + Wet*FDN_Mod(x_in)",
        "arquitectura_interna": ["Selector de entrada Mid/Side", "Línea de Pre-Delay sincronizable a tempo", "Generador de Reflexiones Tempranas (ER)", "Tanque FDN con geometría variable (Diffusion/Walls), Modulación (Speed/Mod), Bass Multiplier y Crossover Damping"],
        "parametros_clave": ["Mid/Side Input", "High Cut", "Low Cut", "PreDelay", "Size", "Diffusion", "Mod Speed/Amt", "Decay", "Bass Multiplier", "Damping", "ER", "Wet", "Dry", "Stereo Separation"],
        "cc_mapping": {"91": "Wet Level", "74": "Decay Time", "71": "Size"},
        "estructura_fst": "Chunk 0xD5 de 60 bytes."
    },
    "Fruity Scratcher": {
        "termino_rae": "Plato giradiscos virtual de arrastre directo para rayado manual o automatizado",
        "definicion_rae": "Simulador de tornamesa en ranura de efecto que permite cargar un archivo WAV y manipular directamente el ángulo angular del disco (Wave Position) con física de masa, velocidad y aceleración, además de un interruptor de silenciamiento de crossfader.",
        "familia_dsp": "Integrador Cinemático de Inercia de Plato + Interpolación Sinc de Fase Continua",
        "ecuacion_transferencia": "theta''(t) = (Torque_motor - k_fric*theta'(t)) / I_platter; y(t) = (1 - Mute)*Sample(theta(t))",
        "arquitectura_interna": ["Plato rotatorio automatizable", "Simulador de masa, velocidad (33/45 RPM) y aceleración", "Botón de corte (Mute) y paneo"],
        "parametros_clave": ["Wave Position", "Mute", "Pan", "Speed", "Acceleration", "Sensitivity"],
        "cc_mapping": {"1": "Wave Position (Scratch Wheel)", "64": "Crossfader Mute"},
        "estructura_fst": "Chunk 0xD5 con parámetros cinemáticos y archivo WAV."
    },
    "Fruity Send": {
        "termino_rae": "Derivador de señal pre-atenuador hacia cualquier canal del mezclador",
        "definicion_rae": "Utilidad de ruteo que extrae la señal en el punto exacto de la ranura de inserción donde se coloca (por tanto, antes del fader principal del canal, Pre-Fader) y la envía con control de volumen y panorámica a cualquier canal conectado en cadena lateral.",
        "familia_dsp": "Derivación de Bus en Punto de Inserción (Pre-Fader Tap Routing)",
        "ecuacion_transferencia": "y_slot[n] = Dry * x[n]; Bus_{SendTarget}[n] += Volume * Pan(x[n])",
        "arquitectura_interna": ["Selector de canal destino (Sidechain Target)", "Potenciómetros Dry, Volume y Pan"],
        "parametros_clave": ["Pan", "Dry", "Volume", "Send To Track"],
        "cc_mapping": {"91": "Send Volume", "10": "Send Pan"},
        "estructura_fst": "Chunk 0xD5 de 16 bytes."
    },
    "Fruity Soft Clipper": {
        "termino_rae": "Recortador armónico de cresta por función tangente hiperbólica con umbral variable",
        "definicion_rae": "Arma secreta de la sonoridad moderna en FL Studio: permanece 100% lineal e invisible por debajo del umbral (Threshold), y aplica una curva tangencial suave exclusivamente a las crestas transitorias que superan dicho umbral, afeando 1.5 a 3 dB de pico en microsegundos sin provocar el bombeo (pumping) de un limitador de envolvente.",
        "familia_dsp": "Saturador Tangencial por Tramos Sin Memoria (Piecewise Linear / Hyperbolic Tangent Clipper)",
        "ecuacion_transferencia": "y[n] = G_post * x[n] si |x[n]| <= T; G_post * sgn(x[n]) * (T + (1 - T)*tanh((|x[n]| - T)/(1 - T))) si |x[n]| > T.",
        "arquitectura_interna": ["Potenciómetro de Umbral (Threshold) de rodilla", "Potenciómetro de Ganancia de Salida (Post Gain)", "Gráfico de función de transferencia entrada/salida en tiempo real"],
        "parametros_clave": ["Threshold", "Post Gain"],
        "cc_mapping": {"74": "Threshold", "7": "Post Gain"},
        "estructura_fst": "Chunk 0xD5 de 8 bytes (2 int32: Threshold y Post Gain; usado en Slot 2 de Master_C5_SOTA.fst)."
    },
    "Fruity Spectroman": {
        "termino_rae": "Analizador de espectro en tiempo real por transformada rápida de Fourier o banco de filtros",
        "definicion_rae": "Medidor visual del contenido frecuencial de la mezcla con modos de visualización de barras o espectrograma de humo en estéreo o mono.",
        "familia_dsp": "Transformada de Fourier de Tiempo Corto (STFT Ventana de Blackman-Harris)",
        "ecuacion_transferencia": "y[n] = x[n] (medidor no intrusivo); P(k) = 20*log10(|FFT(w * x)|)",
        "arquitectura_interna": ["Motor FFT / Bandas", "Escalador de ventana y amplificación visual"],
        "parametros_clave": ["Amp", "Scale", "Windowing", "Mode (Stereo/Mono)"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 16 bytes."
    },
    "Fruity Squeeze": {
        "termino_rae": "Degradador digital de resolución y supresor periódico de muestras (Squarer/Bitcrusher)",
        "definicion_rae": "Efecto de distorsión digital extrema que combina un filtro paso-bajo resonante con un reductor de frecuencia de muestreo y una unidad 'Squeeze' que fuerza a cero o retiene tramos enteros de muestras periódicamente para timbres industriales y chiptune.",
        "familia_dsp": "Submuestreo con Retención de Orden Cero (Zero-Order Hold) + Truncamiento Periódico de Ciclo",
        "ecuacion_transferencia": "y[n] = SVF(x[floor(n / M)*M] * Gate_Squeeze(n mod P, Amount))",
        "arquitectura_interna": ["Unidad Punch/Squeeze (Preserve, Amount, Relation)", "Filtro LP resonante pre/post", "Mix Dry/Wet"],
        "parametros_clave": ["Preserve", "Amount", "Impact", "Filter Cutoff & Res", "Mix"],
        "cc_mapping": {"74": "Filter Cutoff", "1": "Squeeze Amount"},
        "estructura_fst": "Chunk 0xD5 de 32 bytes."
    },
    "Fruity Stereo Enhancer": {
        "termino_rae": "Expansor estereofónico por desfase interaural y matriz de diferencia",
        "definicion_rae": "Procesador de imagen estéreo que combina codificación Mid/Side (Stereo Separation) con un retardo corto en uno de los canales (Phase Offset de hasta 500 ms, efecto Haas) e inversión de polaridad de un canal.",
        "familia_dsp": "Matriz Mid/Side + Retardo Interaural (Haas Delay Line) + Inversión de Fase Unilateral",
        "ecuacion_transferencia": "L'[n] = M[n] + alpha*S[n]; R'[n] = sgn_inv * (M[n - D_haas] - alpha*S[n - D_haas])",
        "arquitectura_interna": ["Separador estéreo M/S (-100% Merged..+100% Separated)", "Línea de retardo Phase Offset (Left/Right)", "Inversor de fase L/R"],
        "parametros_clave": ["Stereo Separation", "Phase Offset", "Phase Inversion", "Pan", "Volume"],
        "cc_mapping": {"74": "Stereo Separation", "71": "Phase Offset"},
        "estructura_fst": "Chunk 0xD5 de 24 bytes."
    },
    "Fruity Stereo Shaper": {
        "termino_rae": "Matriz algebraica de mezcla estereofónica 2x2 con retardo e inversión de fase",
        "definicion_rae": "Herramienta de ingeniería de fase e imagen estéreo que expone explícitamente los 4 coeficientes de la matriz 2x2 de mezcla entre canales: Izquierdo en Izquierdo (L), Derecho en Izquierdo (R->L), Derecho en Derecho (R) e Izquierdo en Derecho (L->R), permitiendo decodificar pares Mid/Side, aislar el canal lateral o aplicar retardos de precisión.",
        "familia_dsp": "Transformación Lineal Matricial 2x2 en R^2 con Retardo e Inversión por Rama",
        "ecuacion_transferencia": "[L_out; R_out] = [[g_{LL}, g_{RL}]; [g_{LR}, g_{RR}]] * [L_in(t - d_L); R_in(t - d_R)]",
        "arquitectura_interna": ["4 Deslizadores bipolares (-inf..0 dB con inversión de signo): Left->Right, Left, Right, Right->Left", "Retardo Pre/Post (Delay L/R)", "Rotador de fase (Phase) y envío In/Out Difference a cadena lateral"],
        "parametros_clave": ["Left into Right", "Left", "Right", "Right into Left", "Delay", "Phase", "In/Out Difference Send"],
        "cc_mapping": {"74": "Side Cross-Mix", "71": "Phase Offset"},
        "estructura_fst": "Chunk 0xD5 de 28 bytes."
    },
    "Fruity Vocoder": {
        "termino_rae": "Codificador de envolvente vocal clásico de hasta ciento veintiocho bandas de filtro",
        "definicion_rae": "Vocodificador clásico de banco de filtros que toma el canal Izquierdo como Modulador (Voz) y el Derecho como Portadora (Sintetizador), dividiendo ambos en entre 4 y 128 bandas frecuenciales de primer o segundo orden con detector de envolvente (Attack/Release) por banda.",
        "familia_dsp": "Banco de N Filtros Paso-Banda IIR + N Seguidores de Envolvente Multiplicativos",
        "ecuacion_transferencia": "y[n] = sum_{b=1}^N Gain_b * Env_AR(|H_b(z)[x_L[n]]|) * H_b(z)[x_R[n]]",
        "arquitectura_interna": ["Banco de 4 a 128 bandas con escala lineal/logarítmica", "Seguidores de envolvente con Attack/Release y Formant Shift", "Gráfico de barras de ganancia individual por banda"],
        "parametros_clave": ["Bands (4..128)", "Filter Order", "Freq Min/Max", "Formant Pitch Shift", "Env Attack/Release", "Mod/Car/Wet Mix"],
        "cc_mapping": {"74": "Formant Shift", "71": "Envelope Release"},
        "estructura_fst": "Chunk 0xD5 con los parámetros globales y el vector de ganancias de las 128 bandas."
    },
    "Fruity WaveShaper": {
        "termino_rae": "Conformador de onda de curva de esplines libre con sobremuestreo hasta dieciséis veces",
        "definicion_rae": "Distorsionador gráfico matemático donde el usuario dibuja directamente la función de transferencia $y = f(x)$ mediante curvas spline multipunto en modo unipolar (simétrico, genera armónicos impares) o bipolar (asimétrico, genera armónicos pares e impares), con sobremuestreo de hasta 16x y bloqueo de continua.",
        "familia_dsp": "Evaluación de Tabla de Búsqueda (LUT) Generada por Splines con Sobremuestreo Polifásico Anti-Aliasing",
        "ecuacion_transferencia": "y[n] = DC_Block(Downsample_K(SplineCurve_Bipolar(Pre * Upsample_K(x[n])))) * Post",
        "arquitectura_interna": ["Editor de curva de transferencia $y=f(x)$ (Unipolar / Bipolar)", "Etapa Pre-gain, Mix y Post-gain", "Filtro de sobremuestreo (None, 2x, 4x, 8x, 16x) y filtro Center (DC remover)"],
        "parametros_clave": ["Pre Gain", "Mix", "Post Gain", "Bipolar Mode", "Oversampling (2x..16x)", "Center DC Filter"],
        "cc_mapping": {"1": "Pre Gain Drive", "74": "Wet Mix"},
        "estructura_fst": "Chunk 0xD5 con la lista de nodos y tensiones de la curva spline."
    },
    "Fruity Wrapper": {
        "termino_rae": "Adaptador anfitrión de procesadores de efectos externos (VST2/VST3/AU/CLAP)",
        "definicion_rae": "Versión de efecto de inserción del Fruity Wrapper que aloja plugins de procesamiento de terceros (ej. Ozone 11, FabFilter, Valhalla) en cualquiera de las 10 ranuras de los 125 canales del mezclador, gestionando entradas auxiliares de cadena lateral (Sidechain Auxiliary Inputs).",
        "familia_dsp": "Puente Multicanal de Audio (Main Stereo + Sidechain Stereo) y Automatización VST3/AU",
        "ecuacion_transferencia": "y_{L,R}[n] = VST3_EffectProcess(x_main[n], x_sidechain[n], ParamChanges)",
        "arquitectura_interna": ["Matriz de conexiones de entradas/salidas multipuerto (Processing Tab -> Auto Map Inputs)", "Reportador de latencia exacta al motor PDC del mezclador"],
        "parametros_clave": ["Stereo Aux Input (Sidechain)", "Latency Compensation Offset", "Dry/Wet Mix"],
        "cc_mapping": {"1": "Mapped VST Parameter 1"},
        "estructura_fst": "Chunk 0xD5 con cabecera Wrapper + estado binario opaco del efecto VST3/AU."
    },
    "Fruity X-Y Controller": {
        "termino_rae": "Controlador vectorial bidimensional con física de inercia y suavizado de trayectoria",
        "definicion_rae": "Generador de dos señales de control interno (X e Y) manipulables simultáneamente mediante una cruceta bidimensional con velocidad y aceleración de suavizado configurables para barridos orgánicos de filtro y resonancia.",
        "familia_dsp": "Filtro Cinemático de Segundo Orden (Velocidad y Aceleración Acotadas) en 2D",
        "ecuacion_transferencia": "p''(t) = Accel * (p_target(t) - p(t)) - Damp * p'(t)",
        "arquitectura_interna": ["Plano cartesiano X/Y [0..1]^2", "Integrador de Speed y Acceleration", " Escaladores Min/Max para X e Y"],
        "parametros_clave": ["X Value", "Y Value", "Speed", "Acceleration"],
        "cc_mapping": {"1": "X Coordinate", "11": "Y Coordinate"},
        "estructura_fst": "Chunk 0xD5 de 32 bytes."
    },
    "Fruity X-Y-Z Controller": {
        "termino_rae": "Controlador espacial tridimensional con funciones de transferencia por eje",
        "definicion_rae": "Evolución tridimensional del controlador vectorial que emite tres señales de control independientes (X, Y, Z), cada una con su propia curva spline de mapeo de entrada a salida y suavizado cinemático.",
        "familia_dsp": "Mapeo No Lineal por Eje R^3 -> [0,1]^3 con Suavizado Temporal",
        "ecuacion_transferencia": "Out_i(t) = Spline_i(Smooth(Input_i(t), Speed, Accel)) para i in {X, Y, Z}.",
        "arquitectura_interna": ["Cubo de coordenadas (X, Y, Z)", "3 Editores de curvas de transferencia de entrada/salida", "Motor de inercia"],
        "parametros_clave": ["X", "Y", "Z", "Speed", "Acceleration"],
        "cc_mapping": {"1": "X", "11": "Y", "74": "Z"},
        "estructura_fst": "Chunk 0xD5 con coordenadas X, Y, Z y las 3 curvas spline."
    },
    "Fruity dB meter": {
        "termino_rae": "Medidor de nivel de pico en decibelios referidos al fondo de escala (dBFS)",
        "definicion_rae": "Vúmetro digital vertical de alta visibilidad con retención de picos para vigilar la estructura de ganancia en cualquier punto de la cadena de efectos.",
        "familia_dsp": "Conversión Logarítmica de Amplitud Instantánea a Decibelios (20*log10|x|)",
        "ecuacion_transferencia": "dBFS[n] = 20 * log10(max(|x[n]|, 10^-5)); y[n] = x[n]",
        "arquitectura_interna": ["Detector de pico L/R con memoria de máximo"],
        "parametros_clave": {},
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 4 bytes."
    },
    "Gross Beat": {
        "termino_rae": "Manipulador matricial de tiempo y amplitud en tiempo real sobre búfer de dos compases",
        "definicion_rae": "Procesador de culto de FL Studio que graba continuamente un búfer circular de 2 compases de audio y expone 36 ranuras de curvas de esplines de Tiempo (desplazamiento hacia atrás en el búfer: tartamudeo, parada de vinilo, medio tiempo '1/2 Speed', rayado) y 36 ranuras de Volumen (puerta rítmica, agachamiento de cadena lateral 'Sidechain') disparables por notas MIDI.",
        "familia_dsp": "Lectura de Búfer Circular con Fase Temporal Gobernada por Spline (t_read = t_now - Delta_t(phi_bar))",
        "ecuacion_transferencia": "y(t) = Env_{VolSlot}(t mod T_bar) * Buffer(t - T_bar * Env_{TimeSlot}(t mod T_bar))",
        "arquitectura_interna": ["Búfer circular de 2 compases sincronizado a PPQ", "36 Ranuras de Tiempo (Time Slots C5..B7) con curvas de derivada de velocidad", "36 Ranuras de Volumen (Volume Slots C2..B4) con suavizado anti-clic (Attack/Release/Tension)", "Conmutador de cuantización de disparo (Trigger Sync: Off, 1/4, 1/2, 1 Beat, 1 Bar)"],
        "parametros_clave": ["Time Slot Index (1..36)", "Volume Slot Index (1..36)", "Time Mix", "Volume Mix", "Volume Attack/Release De-click"],
        "cc_mapping": {"1": "Time Slot Mix", "11": "Volume Slot Mix", "74": "Time Slot Selector"},
        "estructura_fst": "Chunk 0xD5 con los 72 árboles de curvas spline (36 de Tiempo + 36 de Volumen)."
    },
    "Hardcore": {
        "termino_rae": "Pedalera virtual de guitarra con once efectos de modelado y ecualizador gráfico",
        "definicion_rae": "Bastidor de 5 pedales de efecto intercambiables para guitarra y sintetizadores (Distortion, Chorus, Flanger, Phaser, Modulator, Delay, Noise Gate, Equalizer, Compression, Muffler, TubeWarm) precedido de puerta de ruido y seguido de un ecualizador gráfico de 8 bandas y simulador de gabinete.",
        "familia_dsp": "Cascada de 5 Pedales No Lineales + EQ de 8 Bandas + Convolución de Pantalla Acústica",
        "ecuacion_transferencia": "y[n] = Cabinet_IR(EQ_8(Pedal_5(...Pedal_1(NoiseGate(x[n])))))",
        "arquitectura_interna": ["Noise Gate de entrada", "5 Ranuras de pedal con 11 modelos de circuito", "Ecualizador de 8 bandas (65Hz..8kHz) + 5 modelos de pantalla Cabinet"],
        "parametros_clave": ["Pedal 1..5 Parameters", "Cabinet Model", "8-Band EQ Sliders"],
        "cc_mapping": {"1": "Pedal 1 Drive", "74": "Cabinet Mix"},
        "estructura_fst": "Chunk 0xD5 con la topología de los 5 pedales y el EQ."
    },
    "Hyper Chorus": {
        "termino_rae": "Multiplicador coral hiperdenso de seis voces con modulación multibanda",
        "definicion_rae": "Efecto de ensanchamiento estereofónico extremo que superpone hasta 6 líneas de retardo moduladas en contrafase con filtrado de graves para mantener intacto el centro monofónico de la mezcla.",
        "familia_dsp": "Banco de 6 Líneas de Retardo Fraccionarias con Modulación Polifásica",
        "ecuacion_transferencia": "y[n] = Dry*x[n] + Wet * sum_{k=1}^6 Pan_k * x(n - D_k - Depth*sin(w*t + 2*pi*k/6))",
        "arquitectura_interna": ["6 Voces de retardo modulado", "Filtro de exclusión de graves", "Control de velocidad, profundidad y mezcla"],
        "parametros_clave": ["Rate", "Depth", "Delay", "Voices", "Low Cut", "Mix"],
        "cc_mapping": {"74": "Depth", "1": "Rate"},
        "estructura_fst": "Chunk 0xD5 con parámetros del banco de 6 voces."
    },
    "Low Lifter": {
        "termino_rae": "Sintetizador psicoacústico de subarmónicos y armónicos superiores para refuerzo de graves",
        "definicion_rae": "Procesador de realce de bajas frecuencias que rastrea la fundamental del registro grave, sintetiza una octava inferior limpia (Sub-bass synthesis) y genera simultáneamente la serie de armónicos superiores (principio del fundamental ausente de Fletcher) para que el subgrave se perciba incluso en altavoces pequeños.",
        "familia_dsp": "Divisor de Frecuencia Subarmónico + Excitación Polinómica de Armónicos Superiores (Missing Fundamental)",
        "ecuacion_transferencia": "y[n] = x[n] + g_sub * Osc_{f0/2}[n] + g_harm * sum_{k=2}^5 c_k * T_k(LPF_bass(x[n]))",
        "arquitectura_interna": ["Detector de banda grave con frecuencia de cruce", "Generador de subarmónicos en fase", "Excitador armónico psicoacústico con limitador de excursión"],
        "parametros_clave": ["Crossover Frequency", "Sub Bass Level", "Harmonic Drive", "Output Ceiling", "Dry/Wet"],
        "cc_mapping": {"74": "Crossover Frequency", "1": "Sub Bass Level"},
        "estructura_fst": "Chunk 0xD5 con parámetros de seguimiento subarmónico."
    },
    "LuxeVerb": {
        "termino_rae": "Reverberador algorítmico de alta densidad con tanque de realimentación tonal (Shimmer), seguidor de envolvente y compuerta",
        "definicion_rae": "Reverberador algorítmico insignia de FL Studio 2025: modela espacios acústicos realistas y cámaras hiperreales mediante una red de retardo de alta difusión con bucle de realimentación dotado de cambio de tono cromático (Pitch Shifter para colas angelicales Shimmer de +12 semitonos), seguidor de envolvente para agachamiento automático (Auto-Ducking de la cola mientras suena la voz/sintetizador), congelación infinita (Freeze) y separador Mid/Side.",
        "familia_dsp": "Red FDN Modulada de Alta Densidad + Pitch Shifter Granular en Bucle de Realimentación + Seguidor de Envolvente",
        "ecuacion_transferencia": "Tail[n] = FDN(x[n] + fb * PitchShift(Tail[n - D], +12 st)) * (1 - Duck(Env(x[n])))",
        "arquitectura_interna": ["Sección Input con Envelope Follower (modulable a Wet, Decay o PreDelay) y Freeze", "Tanque Reverb (Decay, Size, Diffusion, Brightness, Mod Depth/Speed)", "Bucle Feedback con Pitch Shifter (-12..+12 semitonos) y Damping de 3 bandas", "Sección Output con Peak/Shelf EQ y separación estéreo"],
        "parametros_clave": ["Decay Time", "Size", "Brightness", "Feedback Pitch (+12st Shimmer)", "Feedback Mix", "Envelope Follower to Wet (Ducking)", "Freeze Switch"],
        "cc_mapping": {"91": "Wet Level", "74": "Decay Time", "71": "Brightness", "1": "Shimmer Feedback Mix"},
        "estructura_fst": "Chunk 0xD5 con estado completo del tanque FDN, Pitch Shifter y seguidor de envolvente."
    },
    "Maximus": {
        "termino_rae": "Maximizado maestro multibanda con curvas de transferencia por esplines y limitador de anticipación",
        "definicion_rae": "Procesador supremo de dinámica y masterización de FL Studio: divide el espectro en tres bandas (Low, Mid, High) mediante filtros de cruce IIR o de fase lineal, somete cada banda y la suma maestra (Master) a una función de transferencia dinámica dibujada libremente con curvas spline (permitiendo simultáneamente puerta de ruido, expansión ascendente, compresión y limitación en una sola curva), integra saturación armónica analógica de dos tipos (A/B) y fuerza la monofonía absoluta de subgraves.",
        "familia_dsp": "División de 3 Bandas (IIR / Fase Lineal) + 4 Computadores de Ganancia por Curva Spline + Saturador Asimétrico + Limitador Lookahead",
        "ecuacion_transferencia": "Para banda b in {L, M, H, Master}: y_b[n] = Saturate(x_b[n - L_att] * (Spline_b(Env_b[n]) / max(Env_b[n], eps)))",
        "arquitectura_interna": ["Filtros de corte Low Cut (20..100Hz) y Crossovers Low-Mid / Mid-High con modo Linear Phase", "4 Bandas completas (LOW, MID, HIGH, MASTER), cada una con Pre-Gain, Curva Spline I/O, Attack, Release, Ahead, Sustain, Stereo Separation y Saturation (Threshold/Ceiling)", "Visualizador multimodo de compresión y crestas"],
        "parametros_clave": ["Low/High Crossover Freq", "Low Band Stereo Separation (100% Merged Mono)", "Band L/M/H/Master Pre-Gain & Post-Gain", "Master Attack (Lookahead)", "Saturation Threshold/Ceiling"],
        "cc_mapping": {"7": "Master Pre-Gain", "74": "Low Crossover Freq", "71": "Master Release"},
        "estructura_fst": "Chunk 0xD5 con los 4 árboles de curvas spline de transferencia (Low, Mid, High, Master) y crossovers (usado en Slot 1 de Master_C5_SOTA.fst)."
    },
    "Multiband Delay": {
        "termino_rae": "Banco espectral de dieciséis bandas de retardo, cambio de tono y paneo independientes",
        "definicion_rae": "Efecto de diseño sonoro vanguardista que descompone la señal en 16 bandas frecuenciales (escala lineal, logarítmica o armónica) y permite aplicar a cada banda un tiempo de retardo, realimentación, volumen, panorámica y desplazamiento de tono distintos, creando barridos dispersivos (chirps) y ritmos espectrales.",
        "familia_dsp": "Banco de 16 Filtros de Reconstrucción Perfecta + 16 Líneas de Retardo Moduladas con Pitch Shift",
        "ecuacion_transferencia": "y[n] = sum_{b=1}^{16} Pan_b * Vol_b * Delay_Pitch_b(H_band_b(z)[x[n]], D_b, fb_b)",
        "arquitectura_interna": ["Banco de 16 bandas con selector de escala (Harmonic, Bark, Linear)", "16 Líneas de retardo sincronizables o en milisegundos", "Morfismo entre 8 bancos de ajustes (Morph knob)"],
        "parametros_clave": ["Band 1..16 Delay, Volume, Pan, Feedback, Pitch", "Master Scale", "Bank Morph", "Keep Pitch"],
        "cc_mapping": {"1": "Bank Morph", "74": "Global Delay Scale", "71": "Global Feedback"},
        "estructura_fst": "Chunk 0xD5 con las 8 matrices de los 16 canales de retardo espectral."
    },
    "Newtime": {
        "termino_rae": "Editor de cuantización y deformación elástica del tiempo (Time Warping) por marcadores de transitorios",
        "definicion_rae": "Laboratorio de alineación rítmica de audio que detecta los ataques transitorios de una interpretación vocal o instrumental y permite desplazarlos individualmente sobre la rejilla del compás o aplicar ranuras de groove sin alterar la altura tonal mediante el motor Zplane Elastique Pro.",
        "familia_dsp": "Vocodificador de Fase con Bloqueo de Transitorios (Transient-Preserving Phase Vocoder Zplane Elastique)",
        "ecuacion_transferencia": "Estiramiento local r_k = (t'_{k+1} - t'_k) / (t_{k+1} - t_k) preservando la fase coherente en los instantes de ataque t_k.",
        "arquitectura_interna": ["Detector de marcadores de transitorios (Warp Markers)", "Motor Zplane Elastique Pro v3", "Cuantizador de plantillas de Groove"],
        "parametros_clave": ["Groove Amount", "Marker Positions", "Playback Sync to Host"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con el archivo WAV y el vector de marcadores de deformación temporal."
    },
    "Newtone": {
        "termino_rae": "Editor quirúrgico de corrección de altura tonal, formantes y vibrato nota a nota",
        "definicion_rae": "Estación de afinación vocal y monofónica (equivalente nativo a Melodyne) que segmenta una grabación en bloques de nota sobre un Piano Roll, permitiendo corregir su afinación central, desviación fina, transición entre notas (rampa de portamento), amplitud de vibrato y desplazamiento de formantes.",
        "familia_dsp": "Detección de Frecuencia Fundamental (YIN/Autocorrelación) + Re-síntesis PSOLA / Phase Vocoder con Preservación de Formantes",
        "ecuacion_transferencia": "Re-escalado espectral separando fuente glotal E(w) y envolvente formántica V(w): Y(w) = E(w / alpha_pitch) * V(w / alpha_formant).",
        "arquitectura_interna": ["Motor de detección monofónica y troceado de notas", " Corrector macro de Center, Variation (Vibrato) y Transition Speed", "Modo Warp (estiramiento temporal) y exportación a MIDI"],
        "parametros_clave": ["Center (Pitch Quantize)", "Variation (Vibrato Scaling)", "Transition Speed", "Scale Snap"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con el audio PCM y la lista de bloques de nota editados."
    },
    "Patcher": {
        "termino_rae": "Sub-anfitrión modular de efectos en grafo acíclico dirigido",
        "definicion_rae": "Versión de efecto de inserción de Patcher que permite construir cadenas de procesamiento paralelas, multibanda (junto a Frequency Splitter) o Mid/Side (junto a Fruity Stereo Shaper) dentro de una única ranura del mezclador.",
        "familia_dsp": "Evaluación Topológica de Grafo Dirigido de Procesadores de Audio y Control",
        "ecuacion_transferencia": "y_out[n] = sum_{v in Sinks} Node_v(sum_{u -> v} g_{u,v} * Node_u[n])",
        "arquitectura_interna": ["Grafo de nodos de audio, eventos y parámetros", "Panel Control Surface personalizable", "Compensación automática de retardo por rama"],
        "parametros_clave": ["Surface Macro Controls"],
        "cc_mapping": {"1": "Surface Macro 1", "74": "Surface Macro 2"},
        "estructura_fst": "Chunk 0xD5 recursivo que empaqueta todos los efectos internos y sus conexiones."
    },
    "Pitch Shifter": {
        "termino_rae": "Transpositor de altura tonal en tiempo real de doble motor (Granular y Vocodificador de Fasecon Formantes)",
        "definicion_rae": "Procesador de cambio de tono en vivo provisto de dos motores especializados: el modo 'Music' (vocodificador de fase polifónico con preservación y desplazamiento de formantes) y el modo 'Voice' (motor granular sincronizado al periodo glotal con duración y densidad ajustables).",
        "familia_dsp": "Modo Music: STFT Phase Vocoder con Cepstrum Formant Preservation; Modo Voice: PSOLA Granular",
        "ecuacion_transferencia": "f_out = f_in * 2^(Semitones/12 + Cents/1200)",
        "arquitectura_interna": ["Pestaña Voice (Granular: Pitch, Formant, Duration, Density, Jitter)", "Pestaña Music (Phase Vocoder: Pitch, Formant, Latency/Quality)", "Línea de retardo con realimentación (Crystals / Shimmer delays)"],
        "parametros_clave": ["Pitch Semitones (-12..+12)", "Formant Shift", "Engine Mode (Voice/Music)", "Delay Time & Feedback", "Mix"],
        "cc_mapping": {"74": "Pitch Shift", "71": "Formant Shift"},
        "estructura_fst": "Chunk 0xD5 con parámetros de ambos motores y línea de retardo."
    },
    "Pitcher": {
        "termino_rae": "Corrector automático de afinación vocal en tiempo real y armonizador de cuatro voces",
        "definicion_rae": "Procesador de afinación instantánea de baja latencia (estilo Auto-Tune) que fuerza la frecuencia fundamental de una voz hacia las notas permitidas de una escala musical o hacia un acorde de 4 voces introducido por MIDI en tiempo real, con control de velocidad de corrección, preservación de formantes y deslizamiento de género (Masculino/Femenino).",
        "familia_dsp": "Rastreo de Periodo Fundamental en Tiempo Real + Re-muestreo Sincrono al Tono (TD-PSOLA) con Filtro de Formantes",
        "ecuacion_transferencia": "f_target = argmin_{f_k in Scale} |log2(f_detected / f_k)|; f_out(t) = f_out(t-1) + alpha_speed * (f_target - f_out(t-1))",
        "arquitectura_interna": ["Detector de pitch de latencia mínima (Min Freq: Normal/Bass)", "Cuantizador de escala cromática/diatónica", "Motor de corrección (Speed: Fast..Slow) + Gender Formant Shifter", "Armonizador de 4 voces controlado por puerto MIDI (Modo MIDI + Octaves)"],
        "parametros_clave": ["Correction Speed", "Fine Tune", "Gender Formant", "Scale Notes Enable", "MIDI Mode & Port", "Voice 1..4 Pan/Level"],
        "cc_mapping": {"74": "Correction Speed", "71": "Gender Formant"},
        "estructura_fst": "Chunk 0xD5 con máscara de escala, velocidad y configuración de las 4 voces."
    },
    "Razer Chroma": {
        "termino_rae": "Transductor de energía espectral de audio a iluminación física RGB de periféricos",
        "definicion_rae": "Puente de visualización de hardware que analiza el espectro FFT o el nivel de pico del canal donde se inserta y transmite tramas de color RGB hacia teclados y dispositivos compatibles.",
        "familia_dsp": "Análisis Espectral FFT de Baja Resolución -> Matriz RGB",
        "ecuacion_transferencia": "y[n] = x[n] (paso transparente de audio)",
        "arquitectura_interna": ["Analizador de barras espectrales", "Emisor de eventos de iluminación"],
        "parametros_clave": ["Visualization Effect", "Color Palette"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de configuración visual."
    },
    "Soundgoodizer": {
        "termino_rae": "Macro-procesador psicoacústico multibanda de un solo mando basado en el motor Maximus",
        "definicion_rae": "Envoltorio simplificado del motor de masterización Maximus que expone únicamente una rueda maestra de cantidad (mezcla paralela de compresión/saturación multibanda) y cuatro perfiles precalibrados: Preset A (realce de graves y aire estereofónico en agudos), Preset B (saturación cálida de medios), Preset C (compresión densa y agresiva de presencia) y Preset D (pegamento dinámico suave).",
        "familia_dsp": "Motor Maximus de 3 Bandas + Banda Master con Interpolación Paramétrica por Rueda Única",
        "ecuacion_transferencia": "y[n] = Maximus_Engine(x[n]; Preset_{A,B,C,D}, MacroGain = Amount)",
        "arquitectura_interna": ["Núcleo completo de Maximus (3 bandas + Master)", "Selector de 4 curvas de transferencia (A, B, C, D)", "Potenciómetro rotatorio gigante de intensidad"],
        "parametros_clave": ["Mode (A / B / C / D)", "Amount (0.0..1.0)"],
        "cc_mapping": {"1": "Soundgoodizer Amount", "74": "Mode Selector"},
        "estructura_fst": "Chunk 0xD5 de 12 bytes (índice de modo 0..3 + float de cantidad)."
    },
    "Spreader": {
        "termino_rae": "Ensanchador estereofónico monocompatible por filtros de peine desfasados",
        "definicion_rae": "Procesador de apertura espacial que genera anchura estereofónica a partir de señales monofónicas o estrechas dividiendo el espectro mediante pares de filtros complementarios en oposición de fase cuyos lóbulos se cancelan exactamente al sumar a mono, garantizando cero cancelaciones destructivas en sistemas de club.",
        "familia_dsp": "Par de Redes All-Pass / Filtros Complementarios Ortogonales (Suma Mono = Identidad)",
        "ecuacion_transferencia": "L[n] = x_L[n] + alpha * H_orth(x_M[n]); R[n] = x_R[n] - alpha * H_orth(x_M[n]) => L + R = x_L + x_R.",
        "arquitectura_interna": ["Red de desfase ortogonal monocompatible", "Filtro de preservación de bajas frecuencias (Low Bypass)", "Goniómetro / Vectorscopio integrado"],
        "parametros_clave": ["Spread Amount", "Separation", "Low Bypass Frequency"],
        "cc_mapping": {"74": "Spread Amount", "71": "Low Bypass"},
        "estructura_fst": "Chunk 0xD5 con parámetros de expansión ortogonal."
    },
    "Transient Processor": {
        "termino_rae": "Escultor dinámico diferencial de ataque transitorio y cola de sostenimiento con división de graves",
        "definicion_rae": "Procesador de dinámica independiente del nivel absoluto que compara un detector de envolvente instantáneo con uno integrado para aislar el ataque inicial (Attack) y la caída posterior (Release/Sustain), permitiendo afilar o suavizar percusiones con una sección de corte de frecuencia (Split Frequency) para dejar intacto o procesar por separado el subgrave.",
        "familia_dsp": "Detección Diferencial de Envolventes Duales + Saturación de Cresta (Drive)",
        "ecuacion_transferencia": "g_dB[n] = G_att * max(0, E_fast[n] - E_slow[n]) + G_rel * max(0, E_slow[n] - E_fast[n])",
        "arquitectura_interna": ["Divisor frecuencial (Split Frequency) para proteger graves", "Detector diferencial de Attack y Release con ajuste de forma (Attack Shape)", "Etapa de saturación Drive de picos", "Monitor de ondas de ganancia diferencial"],
        "parametros_clave": ["Attack", "Drive", "Release", "Attack Shape", "Split Frequency", "Gain"],
        "cc_mapping": {"74": "Attack Gain", "71": "Release Sustain", "1": "Drive"},
        "estructura_fst": "Chunk 0xD5 de 32 bytes."
    },
    "Transporter": {
        "termino_rae": "Motor de bucles efímeros en tiempo real, salto estocástico de compás y rebanado al vuelo",
        "definicion_rae": "Procesador de manipulación temporal en vivo que captura continuamente los últimos compases de audio en un anillo de memoria y dispara bucles de subdivisión (1/16..2 compases), reversa instantánea, cambio de tono y saltos entre rebanadas con fundidos cruzados sin clics.",
        "familia_dsp": "Búfer Circular Sincronizado a Tempo con Saltos de Puntero Ventaneados y Pitch Shift",
        "ecuacion_transferencia": "y[n] = Crossfade_Hann(RingBuffer[p_loop(n)], RingBuffer[p_live(n)])",
        "arquitectura_interna": ["Anillo de captura sincronizado al reloj del proyecto", "Motor de subdivisión de bucle, reversa y velocidad", "Matriz de disparo en vivo"],
        "parametros_clave": ["Loop Size", "Reverse", "Pitch Shift", "Slice Jump", "Dry/Wet"],
        "cc_mapping": {"1": "Loop Trigger", "74": "Loop Size"},
        "estructura_fst": "Chunk 0xD5 con configuración del motor de bucles."
    },
    "Tuner": {
        "termino_rae": "Afinador estroboscópico y medidor de frecuencia fundamental de alta precisión",
        "definicion_rae": "Analizador monofónico que estima la frecuencia fundamental al centésimo de semitono (cents) mediante autocorrelación de ventana larga, con referencia ajustable (La4 = 400..480 Hz) y tres velocidades de respuesta.",
        "familia_dsp": "Estimación de Periodo por Diferencia Cuadrática Media Normalizada (Algoritmo YIN / McLeod Pitch Method)",
        "ecuacion_transferencia": "Delta_cents = 1200 * log2(f_est / (f_ref_A4 * 2^((MIDI_nearest - 69)/12)))",
        "arquitectura_interna": ["Detector de tono YIN", "Visualizador de aguja y estroboscópico", "Interruptor Mute output"],
        "parametros_clave": ["Reference Pitch (440 Hz)", "Reactivity Speed", "Bass Mode", "Mute"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 16 bytes."
    },
    "VFX Color Mapper": {
        "termino_rae": "Enrutador de flujos de notas por índice de color del Piano Roll (dieciséis canales de voz)",
        "definicion_rae": "Nodo de procesamiento de voz exclusivo para Patcher que recibe un flujo polifónico de notas y redirige cada uno de los 16 colores de nota del Piano Roll (grupos de voz 1..16) hacia cualquiera de sus 16 salidas independientes o los reasigna de color.",
        "familia_dsp": "Demultiplexor Discreto 16x16 de Eventos de Voz por Atributo de Color",
        "ecuacion_transferencia": "OutputPort(Note) = RoutingMap[Note.ColorIndex (1..16)]",
        "arquitectura_interna": ["Matriz de conmutación de 16 colores de entrada a 4/16 puertos de salida"],
        "parametros_clave": ["Color 1..16 Target Output & Target Voice Color"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 de 64 bytes (exclusivo de Patcher)."
    },
    "VFX Envelope": {
        "termino_rae": "Modulador polifónico de propiedades por voz mediante curvas de esplines (altura, corte, resonancia, paneo)",
        "definicion_rae": "Nodo de Patcher que inyecta envolventes multipunto y LFOs independientes para cada nota individual (verdadera articulación polifónica por voz) sobre el tono fino, la frecuencia de corte (Mod X), la resonancia (Mod Y), la velocidad y el paneo.",
        "familia_dsp": "Modulación Polifónica por Voz (Per-Voice Envelope Generator)",
        "ecuacion_transferencia": "Voice_i.Prop(t) = clamp(Voice_i.Prop_0 + Env_Prop(t - t_{on,i}), Min, Max)",
        "arquitectura_interna": ["5 Pestañas de articulador por voz (Velocity, Pitch, Pan, Mod X, Mod Y)", "Motor de splines con LFO, Key Mapping y Velocity Mapping"],
        "parametros_clave": ["Pitch Env Tension/Level", "Mod X/Y Env Curves"],
        "cc_mapping": {"1": "Global Tension Scaling"},
        "estructura_fst": "Chunk 0xD5 con los 5 árboles de articuladores por voz."
    },
    "VFX Key Mapper": {
        "termino_rae": "Transpositor matricial de escalas, cuantizador tonal y generador automático de acordes",
        "definicion_rae": "Nodo de Patcher que intercepta cada nota entrante dentro de una octava y permite reasignarla a otra altura cromática, silenciarla o disparar simultáneamente un acorde completo de hasta 4 notas por tecla.",
        "familia_dsp": "Transformación Matricial Discreta sobre el Anillo de Clases de Altura Z_12 -> P(Z_128)",
        "ecuacion_transferencia": "Notes_out(k) = {k + Offset_Octave + Delta_j : j in ActiveSliders(k mod 12)}",
        "arquitectura_interna": ["Matriz de 12 columnas cromáticas con cursores multivoz (-12..+12 semitonos)", "Transpositor global de entrada/salida y plantillas de escalas y acordes"],
        "parametros_clave": ["Base Key", "Input/Output Transpose", "12-Key Chord/Note Sliders"],
        "cc_mapping": {"74": "Global Transpose"},
        "estructura_fst": "Chunk 0xD5 con la matriz de mapeo de las 12 clases de altura."
    },
    "VFX Keyboard Splitter": {
        "termino_rae": "Divisor de teclado en dieciséis zonas de altura y velocidad con probabilidades de disparo",
        "definicion_rae": "Nodo de Patcher que particiona el rango MIDI (C0..G10) y el rango de velocidad (0..127) en hasta 16 zonas independientes con fundidos cruzados (crossfades) y curvas de probabilidad aleatoria para distribuir el teclado entre varios sintetizadores.",
        "familia_dsp": "Particionado del Espacio Fase (Key x Velocity) con Compuerta Estocástica de Bernoulli",
        "ecuacion_transferencia": "Zona z dispara si Key in [K_{min,z}, K_{max,z}] y u_rand < P_z(Key, Vel).",
        "arquitectura_interna": ["16 Zonas con puertos de salida de voz independientes", "Curvas de mapeo de velocidad y probabilidad aleatoria por zona"],
        "parametros_clave": ["Zone 1..16 Key Range, Transpose, Velocity Curve, Random Probability"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con las 16 definiciones de zona."
    },
    "VFX Level Scaler": {
        "termino_rae": "Escalador matemático y humanizador estocástico de propiedades de nota en tiempo real",
        "definicion_rae": "Nodo de Patcher que transforma en vivo las 6 propiedades de cada nota entrante (Velocity, Release, Pitch Fine, Pan, Mod X, Mod Y) aplicando desplazamiento (Offset), multiplicación con tensión (Multiply), centrado y variación aleatoria (Humanize).",
        "familia_dsp": "Transformación Afín No Lineal + Perturbación Estocástica por Nota",
        "ecuacion_transferencia": "p' = clamp(Center + (p - Center)*Mult + Offset + eta_rand*Humanize, 0, 1)",
        "arquitectura_interna": ["6 Pestañas de propiedad de voz", "Gráfico de transferencia entrada/salida en vivo"],
        "parametros_clave": ["Offset", "Multiply", "Center", "Tension", "Humanize Random"],
        "cc_mapping": {"1": "Velocity Multiply", "11": "Humanize Amount"},
        "estructura_fst": "Chunk 0xD5 con los escaladores de las 6 propiedades."
    },
    "VFX Script": {
        "termino_rae": "Intérprete programable en Python para procesamiento algorítmico de voces, microtonalidad y control",
        "definicion_rae": "Motor de ejecución Python embebido en tiempo real dentro de Patcher (introducido en FL Studio 2025) que expone callbacks deterministas por voz y por tick (`onTriggerVoice`, `onReleaseVoice`, `onTick`) para programar arpegiadores generativos, autómatas celulares, afinaciones microtonales exactas (24-TET, Just Intonation, Scala) y moduladores matemáticos.",
        "familia_dsp": "Máquina Virtual Python en Tiempo Real Acoplada al Reloj PPQ y Objetos `vfx.Voice`",
        "ecuacion_transferencia": "v.finePitch = f_python(v.note, PPQ_clock, UI_Controls); v.trigger()",
        "arquitectura_interna": ["Intérprete CPython embebido con módulo `fl_vfx` / `vfx`", "Generador dinámico de controles UI desde código", "Salidas múltiples de Voz y de Controladores continuos"],
        "parametros_clave": ["Python Script Source Code", "Dynamic Script UI Knobs"],
        "cc_mapping": {"1": "Script Parameter 1", "74": "Script Parameter 2"},
        "estructura_fst": "Chunk 0xD5 con el código fuente Python UTF-8 y el estado de sus controles."
    },
    "VFX Sequencer": {
        "termino_rae": "Arpegiador y secuenciador algorítmico por pasos de propiedades de voz para Patcher",
        "definicion_rae": "Secuenciador de patrones MIDI y modulador de pasos alojado en Patcher que transforma acordes entrantes en secuencias rítmicas complejas con control por paso de puerta, ligadura, transposición, velocidad y envío de controladores.",
        "familia_dsp": "Cuantización y Despliegue Secuencial de Conjuntos de Notas Activas sobre Reloj PPQ",
        "ecuacion_transferencia": "Note_step(k) = ChordBuffer[Pattern_Index(k)] + Transpose(k)",
        "arquitectura_interna": ["Matriz de pasos de nota, octava, gate y tie", "Modulador de velocidad y acento"],
        "parametros_clave": ["Step Rate", "Gate Length", "Swing", "Arp Mode", "Step Pitch/Vel"],
        "cc_mapping": {"74": "Gate Length", "1": "Swing"},
        "estructura_fst": "Chunk 0xD5 con la secuencia de pasos."
    },
    "Vintage Chorus": {
        "termino_rae": "Emulador de línea de retardo analógica de cubo de brigada (BBD) del coro Roland Juno-6",
        "definicion_rae": "Modelado físico del circuito integrado analógico Panasonic MN3009 (256 etapas Bucket-Brigade Device) empleado en los sintetizadores Roland Juno: reproduce el filtrado anti-aliasing y de reconstrucción de 10 kHz, el ruido térmico característico de reloj BBD y los tres modos históricos (Modo I: 0.4 Hz suave; Modo II: 0.8 Hz profundo; Modo I+II: modulación rápida vibrante).",
        "familia_dsp": "Doble Línea de Retardo Discreta de 256 Etapas (MN3009 BBD) con Reloj Modulado en Contrafase Estéreo",
        "ecuacion_transferencia": "f_clk(t) = f_0 / (D_0 +/- Delta_D*LFO(t)); L = x + LPF(BBD_1(LPF(x), f_clk)); R = x + LPF(BBD_2(LPF(x), f_clk_inv))",
        "arquitectura_interna": ["2 Chips virtuales MN3009 BBD en contrafase", "3 Botones de modo (Mode I, Mode II, Manual LFO)", "Control de retardo BBD, realimentación, filtro de graves y nivel de ruido analógico"],
        "parametros_clave": ["Mode (I / II / Manual)", "Modulation Speed & Depth", "Delay Time", "Feedback", "Noise Level", "Low Bypass", "Mix"],
        "cc_mapping": {"93": "Wet Mix", "1": "Modulation Depth", "74": "Delay Time"},
        "estructura_fst": "Chunk 0xD5 con el estado del circuito BBD."
    },
    "Vintage Phaser": {
        "termino_rae": "Emulador del desfasador óptico-analógico Electro-Harmonix Small Stone (años setenta)",
        "definicion_rae": "Recreación física de los circuitos integrados de transconductancia variable (OTA CA3094) del legendario pedal Small Stone (inmortalizado por Jean-Michel Jarre): modela la distorsión no lineal dependiente de la frecuencia en las etapas de desfase, el interruptor 'Color' (realimentación resonante profunda) y un LFO dual con retardo de inversión.",
        "familia_dsp": "Cascada de Etapas All-Pass OTA No Lineales con Realimentación Resonante ('Color')",
        "ecuacion_transferencia": "y[n] = x[n] + Mix * OTA_AllPass_{1..N}(x[n] + g_color * tanh(y_{ap}[n-1]), LFO(t))",
        "arquitectura_interna": ["Red OTA de 4 a 8 etapas con no linealidad analógica", "Interruptor Color / Feedback continuo", "Modulador LFO con ajuste de simetría, retardo estéreo y ruido de circuito"],
        "parametros_clave": ["Min/Max Frequency", "Feedback (Color)", "LFO Speed & Shape", "Order (Stages)", "Delay", "Mix"],
        "cc_mapping": {"74": "Feedback Color", "1": "LFO Speed"},
        "estructura_fst": "Chunk 0xD5 con parámetros de la red OTA."
    },
    "Vocodex": {
        "termino_rae": "Vocodificador matricial de cien bandas con sintetizador Sytrus integrado y envoltura de contorno",
        "definicion_rae": "Cumbre mundial de la vocodificación digital: divide el espectro en entre 5 y 100 bandas isofónicas de ancho variable, incorpora internamente un motor sintetizador Sytrus como portadora (además de aceptar portadora externa por Sidechain), permite redibujar libremente el mapeo de frecuencia moduladora a frecuencia portadora, aplica compresión/puerta por banda (Soundgoodizer integrado) y esculpe el paso directo de consonantes fricativas.",
        "familia_dsp": "Banco de 5 a 100 Filtros Paso-Banda de Orden Variable + Matriz de Remapeo Espectral + Compresor Multibanda Soundgoodizer",
        "ecuacion_transferencia": "y[n] = Soundgoodizer(Noise_Pass(x_mod[n]) + sum_{b=1}^{100} Pan_b * Hold_AR(|H^{mod}_{M(b)}(x_mod)|)^gamma * H^{car}_b(x_car))",
        "arquitectura_interna": ["Selector de entradas Sidechain para Modulador (Voz) y Portadora (Synth) + Sintetizador Sytrus interno", "Banco de 5..100 bandas con control de ancho de banda, orden de filtro y escala de frecuencia", "Seguidores de envolvente por banda (Hold, Attack, Release) con congelación (Freeze)", "Curvas multipunto por banda (Band Gain, Band Panning, Modulator Pitch Shift, Noise Level, Envelope Min/Max)", "Compresor/Maximizado Soundgoodizer de salida"],
        "parametros_clave": ["Bands (5..100)", "Band Width", "Modulator Pitch Shift (Gender)", "Attack/Release", "Soundgoodizer Amount", "Carrier Synth Preset", "Wet/Mod/Car Mix"],
        "cc_mapping": {"74": "Modulator Pitch Shift (Formant)", "71": "Band Width", "1": "Soundgoodizer Amount"},
        "estructura_fst": "Chunk 0xD5 con el estado de las 100 bandas, curvas multipunto y parche Sytrus."
    },
    "Wave Candy": {
        "termino_rae": "Instrumento cuádruple de metrología acústica (Osciloscopio, Espectrograma, Vectorscopio y Vúmetro ITU/RMS)",
        "definicion_rae": "Suite de análisis científico y visual de FL Studio que reúne cuatro instrumentos de precisión en ventanas flotantes escalables: Osciloscopio sincronizado en fase, Analizador de Espectro / Espectrograma STFT de hasta 8192 bandas, Vectorscopio polar Lissajous (X/Y o Mid/Side para verificar coherencia de fase) y Medidor de Nivel Peak/RMS/EBU/K-System.",
        "familia_dsp": "Metrología en Silicio: STFT 8192-pt, Proyección Ortogonal de Lissajous (M/S) e Integración Balística RMS/ITU",
        "ecuacion_transferencia": "y[n] = x[n] (instrumento de medida de impedancia infinita / paso transparente)",
        "arquitectura_interna": ["Modo Oscilloscope", "Modo Spectrum (FFT 64..8192 bandas con escala en Semitonos/Hz)", "Modo Vectorscope (Lissajous L/R y Polar M/S)", "Modo Meter (dBFS, RMS, Leq(A), K-12/K-14/K-20)"],
        "parametros_clave": ["Mode (Oscilloscope/Spectrum/Vectorscope/Meter)", "Max Resolution (8192 bands)", "Scale (dB/Hz/Semitones)", "Freeze"],
        "cc_mapping": {},
        "estructura_fst": "Chunk 0xD5 con configuración del instrumento de medida (usado en Slot 4 de Master_C5_SOTA.fst)."
    },
    "ZGameEditor Visualizer": {
        "termino_rae": "Motor de síntesis audiovisual por sombreadores OpenGL reactivos al espectro y transitorios",
        "definicion_rae": "Estación de composición visual y renderizado de vídeo 4K/60fps dentro del mezclador: encadena hasta 100 capas de sombreadores GLSL (OpenGL), mallas 3D, vídeos, imágenes y textos cuyos parámetros (escala, brillo, distorsión, cámara) reaccionan automáticamente al pico de graves, al espectro FFT de 32..256 bandas o a controladores MIDI.",
        "familia_dsp": "Extracción de Envolvente/FFT de Audio -> Uniforms de Sombreadores de Fragmentos GLSL en GPU",
        "ecuacion_transferencia": "FragColor(u,v,t) = GLSL_Layer_N(..., GLSL_Layer_1(u, v, t, AudioFFT[1..256], AudioPeak))",
        "arquitectura_interna": ["Pipeline multicapa de hasta 100 sombreadores GLSL (Postprocess, Canvas, Blend, Mesh, Text)", "Extractor de telemetría espectral y de picos hacia la GPU", "Codificador de exportación MP4/MOV H.264/H.265"],
        "parametros_clave": ["Layer 1..N Alpha, Blend Mode, Shader Uniforms"],
        "cc_mapping": {"1": "Layer A Parameter 1", "11": "Layer A Parameter 2"},
        "estructura_fst": "Chunk 0xD5 con el árbol de capas GLSL y rutas de recursos multimedia."
    }
}

# -----------------------------------------------------------------------------
# 6. INGENIERÍA INVERSA RAE DE LOS 7 PLUGINS VST3 SOTA DEL ECOSISTEMA
# -----------------------------------------------------------------------------
VST3_PLUGINS_RAE_SPEC: Dict[str, Dict[str, Any]] = {
    "Vital.vst3": {
        "termino_rae": "Sintetizador espectral de deformación de tablas de ondas con modulación polifónica MPE",
        "definicion_rae": "Sintetizador VST3 de código abierto de referencia que opera sobre tablas de ondas en el dominio frecuencial (Fourier), permitiendo deformar los armónicos (Spectral Warping: Inharmonic, Smear, Phase Disperse, Shepard Tone) y la fase temporal (Bend, Squeeze, FM, Sync) en 3 osciladores con soporte nativo de escalas Scala (.scl/.kbm) y expresión polifónica MPE.",
        "familia_dsp": "Síntesis por Tabla de Ondas en Dominio Espectral (IFFT por Ciclo) + 2 Filtros Multimodo ZDF",
        "ecuacion_transferencia": "W_warped(t) = IFFT(Transform_Spec(FFT(WavetableFrame(u)), WarpParam))",
        "arquitectura_interna": ["3 Osciladores Espectrales + 1 Muestreador de Ruido/Keytrack", "2 Filtros ZDF (Analog, Dirty, Ladder, Digital, Diode, Formant, Comb, Phaser)", "4 Envolventes + 8 LFOs de esplines + 4 Macros + Matriz de Modulación Estéreo", "Cadena de 9 Efectos reordenables"],
        "parametros_clave": ["Macro 1..4", "Osc 1..3 Frame & Spectral Morph", "Filter 1/2 Cutoff & Res"],
        "cc_mapping": {"1": "Mod Wheel", "74": "MPE Slide (Y-Axis)", "11": "Macro 1"},
        "estructura_fst": "Fruity Wrapper (0xD5) + JSON comprimido de estado Vital (.vital)."
    },
    "Ozone 11 Equalizer.vst3": {
        "termino_rae": "Ecualizador maestro de fase lineal/analógica con separación de transitorios y sostenimiento",
        "definicion_rae": "Ecualizador de masterización de iZotope que permite operar en modos Estéreo, Mid/Side o Transitorio/Sostenimiento (ecualizando de forma independiente el golpe percusivo y la cola armónica) con filtros quirúrgicos de fase digital lineal o curvas analógicas modeladas.",
        "familia_dsp": "Filtrado FIR de Fase Lineal / IIR Analógico sobre Descomposición M/S o Transient/Sustain",
        "ecuacion_transferencia": "y[n] = EQ_Trans(x_trans[n]) + EQ_Sust(x_sust[n])",
        "arquitectura_interna": ["8 Bandas de ecualización de alta precisión", "Selector de canal (Stereo, Mid/Side, Left/Right, Transient/Sustain)", "Medidor de correlación de fase y espectro Delta"],
        "parametros_clave": ["Band 1..8 Freq, Gain, Q", "Phase Mode (Analog/Digital)"],
        "cc_mapping": {"74": "Band 1 Freq"},
        "estructura_fst": "Fruity Wrapper (0xD5) + bloque de estado VST3 de iZotope."
    },
    "LANDR Mastering Pro.vst3": {
        "termino_rae": "Procesador adaptativo de masterización multibanda con tres perfiles tonales",
        "definicion_rae": "Motor de masterización asistida en bus maestro que analiza el factor de cresta y el balance espectral de la mezcla en tiempo real, ajustando un ecualizador adaptativo, compresor multibanda, excitador de saturación, expansor de campo estéreo y limitador de pico verdadero.",
        "familia_dsp": "Cadena de Masterización Adaptativa (EQ + Multiband Comp + Harmonic Exciter + True Peak Limiter)",
        "ecuacion_transferencia": "y[n] = TP_Limiter(StereoField(Exciter(MultibandComp(AdaptiveEQ(x[n])))))",
        "arquitectura_interna": ["Analizador de aprendizaje de mezcla", "3 Estilos (Warm, Balanced, Open)", "Controles de EQ, Presence, De-Esser, Compression, Saturation y Loudness LUFS"],
        "parametros_clave": ["Loudness Target", "Equalizer Low/Mid/High", "Compression", "Saturation", "Stereo Width"],
        "cc_mapping": {"7": "Loudness Target"},
        "estructura_fst": "Fruity Wrapper (0xD5) + estado VST3 de LANDR."
    },
    "Super VHS.vst3": {
        "termino_rae": "Emulador de degradación de cinta magnética de videocasete (VHS) de los años ochenta",
        "definicion_rae": "Procesador multi-efecto de carácter nostálgico (Baby Audio) que recrea seis imperfecciones físicas de los grabadores de vídeo doméstico: ruido estático de cabezal (Static), saturación magnética cálida (Heat), conversión A/D de 8 bits de primera generación (Shape), fluctuación de velocidad del cabrestante (Drift / Wow & Flutter), ensanchamiento coral sombrío (Wash) y reverberación corta de sala ochentera (Magic).",
        "familia_dsp": "Cascada de Ruido de Cinta + Saturación de Histéresis + Cuantización de 8 Bits + Modulación Estocástica de Retardo (Wow/Flutter) + Chorus/Reverb",
        "ecuacion_transferencia": "y[n] = Reverb_Wash(Chorus_Magic(BitCrush_8b(TapeSat_Heat(x(t - Drift(t)) + Static[n]))))",
        "arquitectura_interna": ["Generador Static", "Saturador de cinta Heat", "Reductor de resolución Shape", "Modulador de tono Drift", "Reverb Wash y Chorus Magic"],
        "parametros_clave": ["Static", "Heat", "Shape", "Drift", "Wash", "Magic", "Mix"],
        "cc_mapping": {"1": "Drift Wow/Flutter", "74": "Heat Saturation", "91": "Wash Reverb"},
        "estructura_fst": "Fruity Wrapper (0xD5) + estado VST3 de Baby Audio."
    },
    "KickShaper.vst3": {
        "termino_rae": "Escultor psicoacústico de bombos por realce subarmónico, compresión de golpe y eliminación de barro",
        "definicion_rae": "Procesador especializado en diseño de bombos (WA Production) dividido en cuatro etapas en serie: 'Deboom' (atenuación dinámica de la cola resonante lodosa en 120-250 Hz), 'Thump' (síntesis de subarmónicos en fase para peso de club), 'Punch' (compresión y afilado del ataque transitorio) y 'Tone/Clipper' (brillo de clic y recorte suave de techo).",
        "familia_dsp": "Atenuación Dinámica de Cola Resonante + Síntesis Subarmónica + Modelado de Transitorios + Soft Clipper",
        "ecuacion_transferencia": "y[n] = SoftClip(Tone(Punch_Transient(Thump_Sub(Deboom_DynEQ(x[n])))))",
        "arquitectura_interna": ["Módulo Deboom", "Módulo Thump (generador subarmónico)", "Módulo Punch (compresor de ataque)", "Módulo Tone & Clipper"],
        "parametros_clave": ["Deboom", "Thump", "Punch", "Tone", "Clipper Switch", "Mix"],
        "cc_mapping": {"74": "Thump Sub", "71": "Punch Attack"},
        "estructura_fst": "Fruity Wrapper (0xD5) + estado VST3 de KickShaper."
    },
    "FirePresser.vst3": {
        "termino_rae": "Matriz vectorial de cuatro compresores analógicos clásicos en serie y paralelo (1176, LA-2A, Distressor, DBX 160)",
        "definicion_rae": "Estación de compresión cuádruple (United Plugins) que emula simultáneamente cuatro topologías de compresión de hardware legendarias —FET ultrarrápido (1176 Wrapper), Óptico electroluminiscente (LA-2A Retro), VCA controlado digitalmente con distorsión (Distressor) y VCA de percusión (DBX 160)— permitiendo fundir sus pesos relativos sobre un diagrama cromático 2D y añadir saturación de transformador Turbo.",
        "familia_dsp": "Combinación Convexa / Cascada de 4 Modelos No Lineales de Compresión (FET, Opto, Distressor, VCA)",
        "ecuacion_transferencia": "y[n] = Sat_Turbo(sum_{i=1}^4 w_i(X,Y) * CompModel_i(x[n], DetectorInput))",
        "arquitectura_interna": ["4 Motores de compresión analógica (Wrapper FET, Retro Opto, Distressor, Clear VCA)", "Almohadilla cromática 2D de mezcla de los 4 compresores", "Etapa Turbo de saturación armónica"],
        "parametros_clave": ["Detector Input", "Rainbow Pad Blend (1..4)", "Turbo Saturation", "Dry/Wet"],
        "cc_mapping": {"1": "Turbo Saturation", "74": "Detector Drive"},
        "estructura_fst": "Fruity Wrapper (0xD5) + estado VST3 de FirePresser."
    },
    "Combustor.vst3": {
        "termino_rae": "Compresor adaptativo con cinco algoritmos de saturación no lineal en el bucle de detección",
        "definicion_rae": "Procesador híbrido de compresión y excitación armónica que inyecta saturación adaptativa dependiente de la envolvente a través de cinco modelos matemáticos de distorsión (Valve, Foldback, Sine, Rectifier, Bitcrush) con filtrado pre/post.",
        "familia_dsp": "Compresión Acoplada a Conformación No Lineal de Onda con Filtrado Pre/Post",
        "ecuacion_transferencia": "y[n] = LPF(f_{DistMode}(HPF(Comp_Adaptive(x[n]))))",
        "arquitectura_interna": ["Compresor adaptativo", "5 Modos de combustión armónica", "Filtros de corte de graves y agudos"],
        "parametros_clave": ["Threshold", "Ratio", "Combustion Drive", "Mode (1..5)", "Low/High Cut", "Mix"],
        "cc_mapping": {"1": "Combustion Drive", "74": "High Cut"},
        "estructura_fst": "Fruity Wrapper (0xD5) + estado VST3 de Combustor."
    }
}

# Unificación de la especificación completa
PLUGIN_REVERSE_SPECIFICATION: Dict[str, Any] = {
    "Lexicon_RAE": RAE_ACOUSTIC_LEXICON,
    "Core_Architecture": FL_CORE_ARCHITECTURE_RAE,
    "Binary_Event_Codes": {str(k): v for k, v in FL_EVENT_CODES.items()},
    "Generators": GENERATORS_RAE_SPEC,
    "Effects": EFFECTS_RAE_SPEC,
    "VST3_Third_Party": VST3_PLUGINS_RAE_SPEC,
}


# -----------------------------------------------------------------------------
# 7. GENERADOR DE TRATADO MARKDOWN COMPLETO Y AUDITORÍA DE COBERTURA 100%
# -----------------------------------------------------------------------------
def generate_complete_rae_markdown_treatise(report: Dict[str, Any]) -> str:
    """Genera el Tratado Completo de Ingeniería Inversa RAE en docs/."""
    lines: List[str] = [
        "# Catálogo RAE de plugins: documentación y comparación de nombres",
        "",
        "**Autor:** Borja Fernández Angulo (*Investigador en Sistemas Complejos*)",
        "",
        "---",
        "",
        f"**Resultado:** {report['status']}; algoritmos verificados: {report['algorithms_verified']}; inventario: {report['inventory_status']}; coincidencia de nombres: {report['catalog_coverage_percent']}",
        "## 1. Alcance documental RAE",
        "Las 147 fichas son documentación declarativa. No se han verificado los algoritmos DSP ni su equivalencia con los plugins originales. Los porcentajes documentales siguientes sólo cuentan entradas del catálogo:",
        "1. **RAE (*Real Academia Española*):** Traducción ontológica rigurosa de la jerga anglosajona de producción musical al español técnico y académico, sustituyendo metáforas comerciales (*vibe coding* acústico) por definiciones basadas en la física del sonido y el procesamiento digital de señales.",
        "2. **RAE (*Reverse Audio & Architecture Engine*):** Deconstrucción del protocolo binario `FLhd`/`FLdt` (`.flp`, `.fst`, `.fsc`), las ecuaciones matemáticas de transferencia $y[n]$ / $H(z)$, la topología interna y los mapeos MIDI CC de cada módulo.",
        "",
        f"- **Generadores Nativos Documentados:** `{len(GENERATORS_RAE_SPEC)} / 51` (**100%**)",
        f"- **Efectos Nativos Documentados:** `{len(EFFECTS_RAE_SPEC)} / 89` (**100%**)",
        f"- **Complementos VST3 de Terceros Documentados:** `{len(VST3_PLUGINS_RAE_SPEC)} / 7` (**100%**)",
        f"- **Subsistemas Nucleares del Motor Documentados:** `{len(FL_CORE_ARCHITECTURE_RAE)} / 8` (**100%**)",
        f"- **Códigos de Evento Binario `FLdt` Documentados:** `{len(FL_EVENT_CODES)}`",
        f"- **Términos del Léxico Acústico RAE:** `{len(RAE_ACOUSTIC_LEXICON)}`",
        "",
        "---",
        "",
        "## 2. Diccionario Léxico RAE de Ingeniería Acústica y DSP",
        "",
        "| Anglicismo / Jerga DAW | Término Canónico RAE | Definición Académica y Física | Ecuación / Invariante Matemática |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for eng, item in RAE_ACOUSTIC_LEXICON.items():
        lines.append(
            f"| **{eng}** | *{item['termino_rae']}* | {item['acepcion_rae']} | `{item['invariante_fisica']}` |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Arquitectura Nuclear de FL Studio 2025 (8 Subsistemas Core)",
        "",
    ])
    for key, sub in FL_CORE_ARCHITECTURE_RAE.items():
        lines.append(f"### 3.{list(FL_CORE_ARCHITECTURE_RAE.keys()).index(key) + 1}. {key} — *{sub['termino_rae']}*")
        lines.append(f"- **Definición RAE:** {sub['definicion_rae']}")
        if "ecuacion_dsp" in sub:
            lines.append(f"- **Ecuación / Ley DSP:** `{sub['ecuacion_dsp']}`")
        if "estructura_binaria" in sub:
            lines.append(f"- **Estructura Binaria:** `{json.dumps(sub['estructura_binaria'], ensure_ascii=False)}`")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Protocolo Binario `FLhd` / `FLdt`: Tabla de Eventos (`.flp` / `.fst` / `.fsc`)",
        "",
        "| ID Decimal | Hex | Tipo de Dato | Identificador | Descripción Académica RAE |",
        "| :---: | :---: | :--- | :--- | :--- |",
    ])
    for code_id, ev in sorted(FL_EVENT_CODES.items()):
        lines.append(
            f"| `{code_id}` | `{ev['hex']}` | {ev['tipo']} | `{ev['nombre']}` | {ev['descripcion_rae']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Ingeniería Inversa de los 51 Generadores Nativos (Sintetizadores y Muestreadores)",
        "",
    ])
    for idx, (name, spec) in enumerate(sorted(GENERATORS_RAE_SPEC.items()), start=1):
        lines.extend([
            f"### 5.{idx}. {name} — *{spec['termino_rae']}*",
            f"- **Definición RAE:** {spec['definicion_rae']}",
            f"- **Familia DSP:** {spec['familia_dsp']}",
            f"- **Ecuación de Transferencia:** `{spec['ecuacion_transferencia']}`",
            f"- **Arquitectura Interna:** {', '.join(spec['arquitectura_interna'])}",
            f"- **Parámetros Clave:** {', '.join(spec['parametros_clave']) if spec['parametros_clave'] else 'N/A'}",
            f"- **Mapeo MIDI CC:** `{json.dumps(spec['cc_mapping'], ensure_ascii=False)}`",
            f"- **Estructura Binaria `.fst`:** {spec['estructura_fst']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 6. Ingeniería Inversa de los 89 Efectos Nativos (Procesadores de Señal y Voz)",
        "",
    ])
    for idx, (name, spec) in enumerate(sorted(EFFECTS_RAE_SPEC.items()), start=1):
        lines.extend([
            f"### 6.{idx}. {name} — *{spec['termino_rae']}*",
            f"- **Definición RAE:** {spec['definicion_rae']}",
            f"- **Familia DSP:** {spec['familia_dsp']}",
            f"- **Ecuación de Transferencia:** `{spec['ecuacion_transferencia']}`",
            f"- **Arquitectura Interna:** {', '.join(spec['arquitectura_interna'])}",
            f"- **Parámetros Clave:** {', '.join(spec['parametros_clave']) if spec['parametros_clave'] else 'N/A'}",
            f"- **Mapeo MIDI CC:** `{json.dumps(spec['cc_mapping'], ensure_ascii=False)}`",
            f"- **Estructura Binaria `.fst`:** {spec['estructura_fst']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 7. Ingeniería Inversa de los 7 Procesadores VST3 SOTA de Terceros",
        "",
    ])
    for idx, (name, spec) in enumerate(sorted(VST3_PLUGINS_RAE_SPEC.items()), start=1):
        lines.extend([
            f"### 7.{idx}. {name} — *{spec['termino_rae']}*",
            f"- **Definición RAE:** {spec['definicion_rae']}",
            f"- **Familia DSP:** {spec['familia_dsp']}",
            f"- **Ecuación de Transferencia:** `{spec['ecuacion_transferencia']}`",
            f"- **Arquitectura Interna:** {', '.join(spec['arquitectura_interna'])}",
            f"- **Parámetros Clave:** {', '.join(spec['parametros_clave'])}",
            f"- **Mapeo MIDI CC:** `{json.dumps(spec['cc_mapping'], ensure_ascii=False)}`",
            f"- **Estructura Binaria `.fst`:** {spec['estructura_fst']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "*Documento generado a partir del catálogo; no constituye certificación de hardware ni de DSP.*",
        "",
    ])

    os.makedirs(os.path.dirname(OUTPUT_MD_PATH), exist_ok=True)
    content = "\n".join(lines)
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return OUTPUT_MD_PATH


def inspect_plugin_rae(plugin_name: str) -> Dict[str, Any]:
    """Busca un plugin o subsistema (insensible a mayúsculas) y devuelve su ficha RAE completa."""
    q = plugin_name.strip().lower()
    categories = [
        ("Native Generator", GENERATORS_RAE_SPEC),
        ("Native Effect", EFFECTS_RAE_SPEC),
        ("VST3 Third-Party", VST3_PLUGINS_RAE_SPEC),
        ("Core Subsystem", FL_CORE_ARCHITECTURE_RAE),
    ]
    # 1. Coincidencia exacta
    for cat_label, table in categories:
        for k, v in table.items():
            if k.lower() == q:
                return {"status": "FOUND", "name": k, "category": cat_label, "rae_specification": v}
    # 2. Coincidencia parcial por nombre o término RAE
    matches = []
    for cat_label, table in categories:
        for k, v in table.items():
            if q in k.lower() or q in v.get("termino_rae", "").lower():
                matches.append({"name": k, "category": cat_label, "rae_specification": v})
    if len(matches) == 1:
        return {"status": "FOUND", **matches[0]}
    if len(matches) > 1:
        return {"status": "MULTIPLE_MATCHES", "count": len(matches), "matches": matches}
    return {"status": "NOT_FOUND", "query": plugin_name}


def search_rae_lexicon(query: str = "") -> Dict[str, Any]:
    """Filtra el Diccionario Léxico RAE y el catálogo de 147 plugins por palabra clave."""
    q = query.strip().lower()
    lex_hits = {}
    for k, v in RAE_ACOUSTIC_LEXICON.items():
        if not q or q in k.lower() or q in v["termino_rae"].lower() or q in v["acepcion_rae"].lower():
            lex_hits[k] = v

    plugin_hits = []
    for cat_label, table in [
        ("Generator", GENERATORS_RAE_SPEC),
        ("Effect", EFFECTS_RAE_SPEC),
        ("VST3", VST3_PLUGINS_RAE_SPEC),
    ]:
        for k, v in table.items():
            if (
                not q
                or q in k.lower()
                or q in v["termino_rae"].lower()
                or q in v["definicion_rae"].lower()
                or q in v["familia_dsp"].lower()
            ):
                plugin_hits.append({
                    "name": k,
                    "category": cat_label,
                    "termino_rae": v["termino_rae"],
                    "familia_dsp": v["familia_dsp"],
                    "ecuacion_transferencia": v["ecuacion_transferencia"],
                })

    return {
        "status": "SUCCESS",
        "query": query,
        "lexicon_matches_count": len(lex_hits),
        "lexicon_matches": lex_hits,
        "plugin_matches_count": len(plugin_hits),
        "plugin_matches": plugin_hits,
    }


def scan_native_fl_plugins(
    write_artifacts: bool = True, *, plugins_root: str | None = None,
    simulation: bool = False, real_io_evidence_dir: str | None = None,
) -> Dict[str, Any]:
    """Compare directory names with the catalog; never verifies plugin DSP.

    coverage_percent is retained as null: no algorithm equivalence was measured.
    catalog_coverage_percent concerns only names observed in both native folders.
    VST3 catalog entries are not scanned by this function.
    """
    root = plugins_root if plugins_root is not None else FL_APP_PATH
    errors = []

    def discover(category: str) -> List[str]:
        if simulation:
            return []
        try:
            names = sorted(os.listdir(os.path.join(root, category)))
        except OSError as exc:
            errors.append(f"{category}: {type(exc).__name__}: {exc}")
            return []
        if not names:
            errors.append(f"{category}: EMPTY_INVENTORY")
        return names

    generators_found = discover("Generators")
    effects_found = discover("Effects")
    missing_generators = [g for g in generators_found if g not in GENERATORS_RAE_SPEC]
    missing_effects = [e for e in effects_found if e not in EFFECTS_RAE_SPEC]
    detected = len(generators_found) + len(effects_found)
    unknown = len(missing_generators) + len(missing_effects)
    available = not simulation and not errors and detected > 0
    report: Dict[str, Any] = {
        "mode": "simulation" if simulation else "inventory",
        "status": "SIMULATION_ONLY" if simulation else ("UNVERIFIED" if available else "FAIL_MISSING_EVIDENCE"),
        "verified": False,
        "real_verification": False,
        "algorithms_verified": 0,
        "inventory_status": ("COMPLETE" if unknown == 0 else "INCOMPLETE") if available else "UNAVAILABLE",
        "inventory_errors": errors,
        "evidence_limitations": ["NO_DSP_COMPARISON_WITH_ORIGINAL", "FILENAMES_ONLY", "VST3_NOT_SCANNED"],
        "plugins_root": str(root),
        "fl_studio_version": "not_verified",
        "total_generators": len(GENERATORS_RAE_SPEC),
        "total_effects": len(EFFECTS_RAE_SPEC),
        "total_vst3": len(VST3_PLUGINS_RAE_SPEC),
        "total_plugins_documented": len(GENERATORS_RAE_SPEC) + len(EFFECTS_RAE_SPEC) + len(VST3_PLUGINS_RAE_SPEC),
        "total_core_subsystems": len(FL_CORE_ARCHITECTURE_RAE),
        "total_binary_event_codes": len(FL_EVENT_CODES),
        "total_rae_lexicon_terms": len(RAE_ACOUSTIC_LEXICON),
        "detected_plugins": detected,
        "coverage_percent": None,
        "catalog_coverage_percent": round(100.0 * (detected - unknown) / detected, 2) if available else None,
        "missing_generators": missing_generators,
        "missing_effects": missing_effects,
        "detected_generators": generators_found,
        "detected_effects": effects_found,
        "generators": sorted(GENERATORS_RAE_SPEC),
        "effects": sorted(EFFECTS_RAE_SPEC),
        "vst3_third_party": sorted(VST3_PLUGINS_RAE_SPEC),
        "specifications": PLUGIN_REVERSE_SPECIFICATION,
    }
    if real_io_evidence_dir is not None:
        try:
            if simulation:
                raise ValueError("SIMULATION_CANNOT_CONSUME_REAL_VERIFICATION")
            try:
                from scripts.real_io_verifier import check_evidence_path
            except ModuleNotFoundError:
                from real_io_verifier import check_evidence_path
            report["real_io_evidence"] = check_evidence_path(real_io_evidence_dir)
            report["real_io_evidence"]["bundle"] = os.path.abspath(real_io_evidence_dir)
            report["real_io_evidence"]["scope"] = "Installed AU controls and CLI version only; native FL/VST3 DSP remains unverified"
        except Exception as exc:
            report["status"] = "FAIL_INVALID_IO_EVIDENCE"
            report["real_io_evidence"] = {"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
    if write_artifacts:
        os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        md_path = generate_complete_rae_markdown_treatise(report)
        report["exported_json_path"] = OUTPUT_JSON_PATH
        report["exported_markdown_path"] = md_path
    return report


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Catalog/inventory comparison; no DSP verification")
    parser.add_argument("--plugins-root")
    parser.add_argument("--real-io-evidence-dir")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--inventory-only", action="store_true", help="Exit success only for a complete observed name inventory")
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args(argv)
    report = scan_native_fl_plugins(args.write_artifacts, plugins_root=args.plugins_root, simulation=args.simulate, real_io_evidence_dir=args.real_io_evidence_dir)
    print(json.dumps({k: v for k, v in report.items() if k != "specifications"}, indent=2, ensure_ascii=False))
    if report["status"] == "FAIL_INVALID_IO_EVIDENCE":
        return 1
    if args.simulate:
        return 0  # Explicit catalog simulation, still verified=False.
    if args.inventory_only:
        return 0 if report["inventory_status"] == "COMPLETE" else 1
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
