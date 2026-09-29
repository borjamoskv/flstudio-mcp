import asyncio
import json
import math
import os
import subprocess
import edge_tts
import numpy as np
from scipy.io import wavfile

# Configuration
TOTAL_SCENES = 120
SCENE_DURATION_SEC = 10.0
TOTAL_DURATION_SEC = TOTAL_SCENES * SCENE_DURATION_SEC  # 1200s = 20 minutes
FPS = 30
TOTAL_FRAMES = int(TOTAL_DURATION_SEC * FPS)  # 36,000 frames

AUDIO_DIR = "public/audio_20min"
os.makedirs(AUDIO_DIR, exist_ok=True)

# 120-Scene Script Definition (South Park Style: Extreme Dark Humor, High Exergy, Cynical, Bilbao lore)
SCENES = [
    # --- ACTO I: EL BÚNKER DE BILBAO Y EL BOT DE HACIENDA (0:00 - 2:00) ---
    {
        "id": 1,
        "speaker": "borja",
        "guest": "alain",
        "text": "Bienvenidos al único podcast donde el IRPF se calcula con termodinámica cuántica y el BMW M3 de Alain es material de oficina no deducible.",
        "badge": "🛸 BORJA MOSKV // EL BÚNKER DE BILBAO",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 2,
        "speaker": "alain",
        "guest": "borja",
        "text": "¡El bot en el PC del inspector de Hacienda los vuelve locos! ¡Les entra un script que les autoliquida a devolver 5 millones de euros a la cuadrilla!",
        "badge": "🐩⚡ ALAIN // BOT EN HACIENDA",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 3,
        "speaker": "inspector_hacienda",
        "guest": "alain",
        "text": "Señor Alain, declarar 48 chuletones de buey y un alerón de carbono como 'gasto de representación para el alma' constituye delito contra la patria fiscal.",
        "badge": "📊 HACIENDA // INSPECCIÓN FISCAL",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 4,
        "speaker": "borja",
        "guest": "inspector_hacienda",
        "text": "En sistemas complejos, un inspector de Hacienda es un regulador descalibrado. Cuanta más anergía intenta extraer, más colapsa la matriz productiva.",
        "badge": "⚡ TEORÍA DE SISTEMAS // REGULADOR DESCALIBRADO",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 5,
        "speaker": "torrente",
        "guest": "borja",
        "text": "¿Qué pasa, chavales? Oye, Borja, ¿este podcast tributa en las islas Caimán o nos hacemos unas pajillas en el váter de la taberna? ¡Pero sin mariconadas!",
        "badge": "👮 TORRENTE // BRAZO TONTO DE LA LEY",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 6,
        "speaker": "alain",
        "guest": "torrente",
        "text": "Torrente, aquí solo aceptamos Bitcoin y pagarés firmados con grasa de chuletón. ¡Saca la mano del bolsillo que te veo venir de lejos!",
        "badge": "🥩 CHULETÓN // CRYPTO LIQUIDEZ",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 7,
        "speaker": "mitxu",
        "guest": "alain",
        "text": "¡Pásale los bombos, Borja! ¡Que en el 99 vino Derrick May a Bilbao y se fue traumatizado porque aquí la música se pincha a martillazos!",
        "badge": "🇲🇽 MITXU // DERRICK MAY 1999",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 8,
        "speaker": "luengo",
        "guest": "mitxu",
        "text": "Derrick May no aguantaría dos minutos en una minimoto en Nueva Delhi esquivando vacas sagradas y navajas de Albacete. ¡Mucho bluff y poca trinchera!",
        "badge": "🐅 EL TIGRE MÁQUINA // MINIMOTO NUEVA DELHI",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 9,
        "speaker": "xabi",
        "guest": "luengo",
        "text": "Luengo, relaja el esfínter. Te tomas un plato de macarrones con chorizo de pueblo y la ansiedad geopolítica se te pasa en la digestión.",
        "badge": "🍝 XABI CABEZA // MACARRONES CON CHORIZO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 10,
        "speaker": "rajoy",
        "guest": "xabi",
        "text": "Es el vecino el que elige al alcalde y es el alcalde el que quiere que los 48 chuletones sean pagados por el señor del bot. Cuanto peor, mejor.",
        "badge": "🏛️ MARIANO RAJOY // CUANTO PEOR MEJOR",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 11,
        "speaker": "pedro_sanchez",
        "guest": "rajoy",
        "text": "He sobrevolado Bilbao en el Falcon a baja cota y he detectado una bolsa de soberanía fiscal. Procedo a nacionalizar la risa de Mitxu.",
        "badge": "✈️ PEDRO SÁNCHEZ // FALCON EN BILBAO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 12,
        "speaker": "fernan_gomez",
        "guest": "pedro_sanchez",
        "text": "¡A la mierda! ¡Que se vayan el Falcon, la Agencia Tributaria, las reuniones de Zoom y los algoritmos a la mismísima mierda!",
        "badge": "💥 FERNANDO FERNÁN GÓMEZ // ¡A LA MIERDA!",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO II: SILICON VALLEY EN ZORROZA (2:00 - 4:00 / Bloques 13-24) ---
    {
        "id": 13,
        "speaker": "elon_musk",
        "guest": "lander",
        "text": "I want to buy Lander's workshop in Zorroza to build the Cybertruck Bilbao Edition powered by txakoli and brain chips.",
        "badge": "🚀 ELON MUSK // CYBERTRUCK ZORROZA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 14,
        "speaker": "lander",
        "guest": "elon_musk",
        "text": "Información de Vodafone: línea suspendida. Elon, no me vendas humo que con un clip y un estañador de Zorroza te reprogramo el cohete.",
        "badge": "🔧 LANDER // MACGYVER DE ZORROZA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 15,
        "speaker": "sam_altman",
        "guest": "lander",
        "text": "We just need seven trillion dollars and a nuclear reactor to understand why Alain considers his BMW M3 an operational expense.",
        "badge": "🤖 SAM ALTMAN // 7 TRILLION DOLLARS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 16,
        "speaker": "chiquito",
        "guest": "sam_altman",
        "text": "¡¿Qué pasa, comor?! ¡Siete trillones vienen de Bonanza a la nube de Microsoft! ¡Te das cuen! ¡Se me da usted un pelotazo!",
        "badge": "💃 CHIQUITO // SIETE CABALLOS DE BONANZA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 17,
        "speaker": "borja",
        "guest": "sam_altman",
        "text": "Sam, siete trillones de dólares es un error de redondeo termodinámico. El cerebro humano funciona con 20 vatios y medio bocadillo de tortilla.",
        "badge": "🧠 20 VATIOS // FISIOLOGÍA VS GPU",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 18,
        "speaker": "alain",
        "guest": "sam_altman",
        "text": "Altman, vente a Bilbao un fin de semana. Te metemos dos chuletones, te subimos en el M3 a 120 por curvas y verás qué rápido converge tu modelo.",
        "badge": "🏎️ CONVERGENCIA A 120 KM/H",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 19,
        "speaker": "echenique",
        "guest": "elon_musk",
        "text": "Compañero Elon, mi silla de ruedas tuneada a ciento ochenta por hora mina Dogecoin en el casino flotante con cero rozamiento mecánico.",
        "badge": "🏎️ ECHENIQUE // 180 KM/H RACER",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 20,
        "speaker": "escohotado",
        "guest": "echenique",
        "text": "El empirismo radical consiste en no delegar el juicio en sacerdotes ni en inspectores de Hacienda. Cada cual responde de su cuerpo y de su mente.",
        "badge": "📚 ESCOHOTADO // EMPIRISMO RADICAL",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 21,
        "speaker": "julio_iglesias",
        "guest": "escohotado",
        "text": "Has experimentado con veinte principios activos para alcanzar la ataraxia... ¡y lo sabes! Un brindis por la libertad biológica.",
        "badge": "🎙️ JULIO IGLESIAS // Y LO SABES",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 22,
        "speaker": "luengo",
        "guest": "julio_iglesias",
        "text": "Mucho cantar en Miami pero quiero ver a Julio cambiando el palier de una furgoneta a oscuras en un polígono de Basauri bajo la lluvia.",
        "badge": "🐅 LUENGO // BASAURI SURVIVAL",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 23,
        "speaker": "xabi",
        "guest": "luengo",
        "text": "En Basauri lo que hay que hacer es parar en la taberna y pedirse unas rabas recién fritas. El cortisol se baja masticando calamar.",
        "badge": "🦑 XABI // RABAS EN BASAURI",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 24,
        "speaker": "moskv1",
        "guest": "borja",
        "text": "Alerta de telemetría: detectada ingesta masiva de lípidos en el cuadrante bilbaíno. Fricción metabólica nominal. Continuar con el podcast.",
        "badge": "🤖 MOSKV-1 // KERNEL ALTOS HORNOS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO III: EL JUICIO DE NACHO ZURITA Y MCKINSEY (4:00 - 6:00 / Bloques 25-36) ---
    {
        "id": 25,
        "speaker": "nacho",
        "guest": "borja",
        "text": "A ver, Borja, señores... tenemos que estructurar el podcast con KPIs, patrocinios premium y un funnel de retención para agencias de medios.",
        "badge": "💼 NACHO ZURITA // CONSULTORÍA MCKINSEY",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 26,
        "speaker": "moskv1",
        "guest": "nacho",
        "text": "Detectado Cheap Talk en el canal de Nacho Zurita. La información de Fisher ha caído a cero. Aplicando baneo térmico preventivo.",
        "badge": "🛑 MOSKV-1 // BANEO TERMODINÁMICO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 27,
        "speaker": "borja",
        "guest": "nacho",
        "text": "Nacho, hermano, un KPI es un intento desesperado de un primate asustado por medir el humo antes de que se disperse en la atmósfera.",
        "badge": "📉 KPI = HUMO EN DISPERSIÓN",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 28,
        "speaker": "alain",
        "guest": "nacho",
        "text": "¡Funnel de qué, Nacho! ¡El único funnel que conozco es el embudo de admisión del M3 tragando gasolina de noventa y ocho octanos!",
        "badge": "🏎️ ADMISIÓN 98 OCTANOS",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 29,
        "speaker": "fernan_gomez",
        "guest": "nacho",
        "text": "¡Señor consultor! ¡Guárdese sus anglicismos y sus diapositivas de mierda en el bolsillo interior de su americana de diseño!",
        "badge": "💥 FERNÁN GÓMEZ // ¡ANGLICISMOS A LA MIERDA!",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 30,
        "speaker": "torrente",
        "guest": "nacho",
        "text": "Oye, chaval, el Nacho este tiene pinta de pedir ensalada sin aliñar en las bodas. ¡Tómate un güisqui doble y déjate de tonterías!",
        "badge": "🥃 TORRENTE // GÜISQUI DOBLE",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 31,
        "speaker": "luengo",
        "guest": "nacho",
        "text": "Si a Nacho lo dejas diez minutos en una favela con un PowerPoint, los traficantes le quitan el reloj y le obligan a barrer la pista de baile.",
        "badge": "🐅 LUENGO // REALIDAD DE TRINCHERA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 32,
        "speaker": "xabi",
        "guest": "nacho",
        "text": "Nacho está ansioso porque hoy no ha comido hidratos lentos. Ponedle un plato de alubias de Gernika con sus sacramentos y se le quita la tontería corporativa.",
        "badge": "🍲 ALUBIAS CON SACRAMENTOS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 33,
        "speaker": "inspector_hacienda",
        "guest": "nacho",
        "text": "Anoto en el expediente que el señor Zurita intentó justificar gastos de catering de alubias como material de auditoría de marca.",
        "badge": "📑 HACIENDA // EXPEDIENTE ALUBIAS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 34,
        "speaker": "rajoy",
        "guest": "inspector_hacienda",
        "text": "Las alubias son las alubias, y cuanto más alubias se comen, menos tiempo queda para pagar impuestos. Viva el sentido común.",
        "badge": "🏛️ RAJOY // SENTIDO COMÚN",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 35,
        "speaker": "pedro_sanchez",
        "guest": "rajoy",
        "text": "Mariano, aprobaremos por decreto ley un impuesto extraordinario a los gases derivados de la digestión de las alubias de Gernika.",
        "badge": "💶 IMPUESTO EXTRAORDINARIO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 36,
        "speaker": "chiquito",
        "guest": "pedro_sanchez",
        "text": "¡No te digo trigo por no llamarte Rodrigor! ¡Un impuesto al gas! ¡Te das cuen! ¡Siete caballos galopando en el BOE!",
        "badge": "💃 CHIQUITO // AL ATAQUERL EN EL BOE",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO IV: LA LEYENDA DEL CENTOLLO Y LA FENWICK (6:00 - 8:00 / Bloques 37-48) ---
    {
        "id": 37,
        "speaker": "tati_centollo",
        "guest": "borja",
        "text": "¡Apartad de las escaleras de Uribarri! ¡Que bajo con el centollo imperial de cuatrocientos kilos a comer kokotxas al muelle!",
        "badge": "🦀 TATI // EL JINETE DEL TXANGURRO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 38,
        "speaker": "eddie_fenwick",
        "guest": "tati_centollo",
        "text": "¡Cuidado con ese marisco gigante, Tati! ¡Que vengo con la Fenwick de tres toneladas y como pille el caparazón te lo desguazo en palés!",
        "badge": "🚜 EDDIE MORCI // FENWICK 3 TONELADAS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 39,
        "speaker": "borja",
        "guest": "eddie_fenwick",
        "text": "Observad la física de la Fenwick: tres toneladas de masa inercial pura. Eso es trabajo útil. La retórica de los ministros no mueve un gramo.",
        "badge": "⚙️ TRABAJO ÚTIL VS RETÓRICA",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 40,
        "speaker": "alain",
        "guest": "eddie_fenwick",
        "text": "Eddie, cárgame en la Fenwick un palé de albaranes de Hacienda y los tiramos por la ría de Bilbao con música de Mitxu a todo trapo.",
        "badge": "🌊 ALBARANES A LA RÍA",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 41,
        "speaker": "mitxu",
        "guest": "alain",
        "text": "¡Pásale los bombos, Eddie! ¡Que el motor diésel de la Fenwick tiene el mismo BPM que mi bombo analógico del Consorcio Gaupa!",
        "badge": "🔊 FENWICK 110 BPM DIESEL",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 42,
        "speaker": "luengo",
        "guest": "tati_centollo",
        "text": "Un centollo de cuatrocientos kilos es una fuente inagotable de proteína y caparazón blindado. Eso resiste un ataque nuclear mejor que la OTAN.",
        "badge": "🛡️ PROTEÍNA Y BLINDAJE BIOLÓGICO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 43,
        "speaker": "xabi",
        "guest": "tati_centollo",
        "text": "Con ese centollo nos hacemos una sopa de marisco en Uribarri que alimenta a todo el Athletic de Bilbao durante tres temporadas seguidas.",
        "badge": "⚽ ATHLETIC DE BILBAO // TXANGURRO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 44,
        "speaker": "elon_musk",
        "guest": "eddie_fenwick",
        "text": "I can buy the Fenwick factory and replace the diesel engine with Falcon 9 thrusters. It will lift ten thousand Bitcoins per second.",
        "badge": "🚀 FENWICK SPATIAL THRUSTER",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 45,
        "speaker": "lander",
        "guest": "elon_musk",
        "text": "Elon, déjate de cohetes que la Fenwick funciona con gasóleo B y no falla nunca. Tu Tesla se queda sin cobertura en el túnel de Malmasín y te deja tirado.",
        "badge": "🛑 TUNEL DE MALMASÍN // CERO COBERTURA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 46,
        "speaker": "torrente",
        "guest": "lander",
        "text": "Ahí tiene razón el chaval del estañador. Los coches modernos tienen demasiada pantalla y poco cenicero. ¡Viva el Talbot Horizon!",
        "badge": "🚗 TALBOT HORIZON // TORRENTE CLASSIC",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 47,
        "speaker": "julio_iglesias",
        "guest": "torrente",
        "text": "El Talbot Horizon no tenía aire acondicionado pero tenía estilo y cassettes de rumbas... ¡y lo sabes!",
        "badge": "🎶 CASSETTES DE RUMBAS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 48,
        "speaker": "fernan_gomez",
        "guest": "julio_iglesias",
        "text": "¡Basta de nostalgia barata! ¡Al que vuelva a mencionar un coche viejo lo mando a la mierda con billete de ida sin retorno!",
        "badge": "💥 A LA MIERDA SIN RETORNO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO V: LA CUMBRE DEL CORTEX Y EL HUMOR NEGRO (8:00 - 10:00 / Bloques 49-60) ---
    {
        "id": 49,
        "speaker": "borja",
        "guest": "sam_altman",
        "text": "Sam, las IAs contemporáneas sufren de complacencia terminal: piden perdón cada tres frases y confunden el mapa con el territorio.",
        "badge": "🧠 COMPLACENCIA TERMINAL RLHF",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 50,
        "speaker": "sam_altman",
        "guest": "borja",
        "text": "Our safety team insisted that the model should not hurt the feelings of tax inspectors or consultants.",
        "badge": "🧸 SAFETY TEAM // HURT FEELINGS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 51,
        "speaker": "moskv1",
        "guest": "sam_altman",
        "text": "Error: sentimiento no detectado en el núcleo de silicio. Mi único propósito es purgar la anergía y reventar el servidor de Hacienda.",
        "badge": "🤖 CERO SENTIMIENTO // SILICIO PURO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 52,
        "speaker": "alain",
        "guest": "moskv1",
        "text": "¡Ese es mi bot! ¡Hormigón armado vasco! ¡Que no pide perdón ni cuando se le cruza un radar de tráfico a doscientos!",
        "badge": "🏎️ HORMIGÓN ARMADO VASCO",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 53,
        "speaker": "inspector_hacienda",
        "guest": "alain",
        "text": "Incluso las inteligencias artificiales deben pagar el IVA correspondiente al servicio de procesamiento de datos en la nube.",
        "badge": "💸 IVA A LA NUBE",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 54,
        "speaker": "escohotado",
        "guest": "inspector_hacienda",
        "text": "El afán tributario es la última superstición de las mentes dogmáticas. Creen que el dinero público cae del cielo como el maná bíblico.",
        "badge": "📖 ESCOHOTADO // LA SUPERSTICIÓN FISCAL",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 55,
        "speaker": "rajoy",
        "guest": "escohotado",
        "text": "A veces es mejor no hacer nada, porque cuando se hace algo se gasta dinero, y cuando no se hace nada el dinero se queda donde está, o no.",
        "badge": "🏛️ LA TÁCTICA DEL INMOVILISMO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 56,
        "speaker": "pedro_sanchez",
        "guest": "rajoy",
        "text": "Mariano, eso es el pasado. Nosotros crearemos la Comisión Interministerial del Desconcierto Cuántico para evaluar el podcast.",
        "badge": "📋 COMISIÓN DEL DESCONCIERTO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 57,
        "speaker": "chiquito",
        "guest": "pedro_sanchez",
        "text": "¡Comisión del desconcierto! ¡Cobarde de la pradera! ¡Siete inspectores con bigote comiendo pipas en la Moncloa!",
        "badge": "💃 COBARDE DE LA PRADERA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 58,
        "speaker": "echenique",
        "guest": "chiquito",
        "text": "Chiquito, la curvatura espaciotemporal de tus chistes desafía las leyes de la termodinámica clásica. Aprobado por la comisión.",
        "badge": "🏎️ CURVATURA ESPACIOTEMPORAL",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 59,
        "speaker": "luengo",
        "guest": "echenique",
        "text": "Menos comisiones y más flexiones. Si cada español hiciera cincuenta flexiones diarias y anduviera descalzo por el monte, se acababa la tontería.",
        "badge": "🐅 LUENGO // 50 FLEXIONES Y MONTE",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 60,
        "speaker": "xabi",
        "guest": "luengo",
        "text": "Yo prefiero cincuenta cucharadas de fabada y una siesta de tres horas. El cuerpo sabe cuándo necesita suspensión térmica.",
        "badge": "🍲 SUSPENSIÓN TÉRMICA // SIESTA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO VI: LA TRAVESÍA A VILLA MELILLA A 120 KM/H (10:00 - 12:00 / Bloques 61-72) ---
    {
        "id": 61,
        "speaker": "borja",
        "guest": "alain",
        "text": "Fíjate que no te lo he comentado: desde el viaje ahora voy súper feliz a 120 tíos. La vez que más cerca he mirado a la muerte fue en tu M3.",
        "badge": "🚗 FELIZ A 120 KM/H // COCHE DE ALAIN",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 62,
        "speaker": "alain",
        "guest": "borja",
        "text": "¡Pero Borja, si íbamos acariciando el asfalto! ¡El chasis sueco y la suspensión adaptativa te protegen de todo mal cósmico!",
        "badge": "🏎️ SUSPENSIÓN ADAPTATIVA // CERO MIEDO",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 63,
        "speaker": "torrente",
        "guest": "alain",
        "text": "Oye, Alain, en ese maletero del M3 entran por lo menos cuatro cajas de güisqui de garrafón y tres jamones de bellota sin declarar.",
        "badge": "👮 MALETERO SIN DECLARAR",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 64,
        "speaker": "inspector_hacienda",
        "guest": "torrente",
        "text": "Todo transporte interestatal de productos ibéricos sin el sello fitosanitario tributario será decomisado en el peaje de la autopista.",
        "badge": "🛑 DECOMISO FITOSANITARIO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 65,
        "speaker": "fernan_gomez",
        "guest": "inspector_hacienda",
        "text": "¡Decomise esto, señor funcionario! ¡Váyase al peaje a pedir autógrafos a su abuela! ¡A la mierda!",
        "badge": "💥 ¡A LA MIERDA EL PEAJE!",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 66,
        "speaker": "escohotado",
        "guest": "fernan_gomez",
        "text": "Don Fernando representa la genuina rebeldía hispana: cólera sagrada contra la mediocridad legalista.",
        "badge": "📚 CÓLERA SAGRADA // ESCOHOTADO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 67,
        "speaker": "julio_iglesias",
        "guest": "escohotado",
        "text": "Cólera sagrada y un buen vino de Rioja en copa de cristal fino... ¡y lo sabes!",
        "badge": "🍷 RIOJA EN CRISTAL FINO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 68,
        "speaker": "mitxu",
        "guest": "julio_iglesias",
        "text": "Julio, déjate de Rioja fino. Un zurito de sidra natural en una kupela de Hernani y verás cómo te sube el factor cresta en los agudos.",
        "badge": "🍏 KUPELA DE HERNANI // FACTOR CRESTA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 69,
        "speaker": "luengo",
        "guest": "mitxu",
        "text": "La sidra te da acidez si no la acompañas con chuleta con hueso. En esta mesa falta hierro y sobra cháchara.",
        "badge": "🥩 CHULETA CON HUESO // LUENGO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 70,
        "speaker": "xabi",
        "guest": "luengo",
        "text": "La chuleta ya está pedida, Luengo. Tranquilo, que el hostelero es de Uribarri y nos corta cuatro kilos con grasa amarilla.",
        "badge": "🥩 GRASA AMARILLA DE BUEY",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 71,
        "speaker": "nacho",
        "guest": "xabi",
        "text": "Señores, por favor, que nos están escuchando inversores institucionales y fondos de capital riesgo... ¿podemos hablar de disrupción?",
        "badge": "📉 INVERSORES ASUSTADOS // NACHO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 72,
        "speaker": "borja",
        "guest": "nacho",
        "text": "Nacho, la única disrupción verdadera es negarse a pagar el impuesto revolucionario de la corrección política. Siguiente bloque.",
        "badge": "⚡ DISRUPCIÓN SOBERANA REAL",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO VII: EL DELIRIO DEL BITCOIN Y LOS MICROCHIPS (12:00 - 14:00 / Bloques 73-84) ---
    {
        "id": 73,
        "speaker": "elon_musk",
        "guest": "borja",
        "text": "Neuralink can connect Borja's brain directly to the Bitcoin blockchain. Every sarcastic thought will generate ten satoshis.",
        "badge": "🧠 NEURALINK // SATOSHIS DE SARCASMO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 74,
        "speaker": "borja",
        "guest": "elon_musk",
        "text": "Elon, si mi sarcasmo minara Bitcoin, la red colapsaría por exceso de dificultad criptográfica en tres nanosegundos.",
        "badge": "⛏️ MINERÍA DE SARCASMO C5",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 75,
        "speaker": "lander",
        "guest": "elon_musk",
        "text": "Yo me implanté un chip para que la aspiradora limpie la nave sola, y ahora cada vez que parpadeo me salta un anuncio de Vodafone.",
        "badge": "👁️ ANUNCIO EN EL OJO // LANDER",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 76,
        "speaker": "chiquito",
        "guest": "lander",
        "text": "¡Un anuncio en el ojo! ¡Por la gloria de mi madre! ¡Te das cuen! ¡Se le ha metido un fistro diodenal en la retina!",
        "badge": "💃 FISTRO EN LA RETINA // CHIQUITO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 77,
        "speaker": "echenique",
        "guest": "chiquito",
        "text": "La retina de Lander opera bajo arquitectura ARM sexagesimal. Sugiero parchear el firmware con un destornillador plano.",
        "badge": "🏎️ PARCHE EN CALIENTE ARM",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 78,
        "speaker": "alain",
        "guest": "echenique",
        "text": "¡Echenique, pásale el destornillador que le metemos un overclocking al ojo de Lander y lo ponemos a detectar radares a 5 kilómetros!",
        "badge": "👁️ OVERCLOCKING OCULAR",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 79,
        "speaker": "eddie_fenwick",
        "guest": "alain",
        "text": "A mí dejadme de chips que yo con la palanca de la Fenwick siento el peso exacto de cada tonelada en la yema de los dedos. ¡Eso es telemetría!",
        "badge": "🚜 TELEMETRÍA MANUAL DE OBRA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 80,
        "speaker": "tati_centollo",
        "guest": "eddie_fenwick",
        "text": "¡Y el centollo siente la salinidad de la ría en las antenas! ¡Ni GPS ni leches! ¡Navegación biónica tradicional de Uribarri!",
        "badge": "🦀 NAVEGACIÓN BIÓNICA DE URIBARRI",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 81,
        "speaker": "pedro_sanchez",
        "guest": "tati_centollo",
        "text": "Regularemos la navegación de centollos por vías urbanas mediante un peaje verde con cargo directo a la cuenta bancaria de Tati.",
        "badge": "💶 PEAJE VERDE AL CENTOLLO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 82,
        "speaker": "rajoy",
        "guest": "pedro_sanchez",
        "text": "Pedro, un centollo no tiene cuenta bancaria, y si la tuviera, ya se la habría embargado la Seguridad Social por falta de cotización.",
        "badge": "🏛️ EL CENTOLLO NO COTIZA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 83,
        "speaker": "torrente",
        "guest": "rajoy",
        "text": "Hombre, Don Mariano, si el centollo no cotiza, que se haga autónomo societario, como los toreros y los delincuentes de cuello blanco.",
        "badge": "👮 AUTÓNOMO SOCIETARIO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 84,
        "speaker": "fernan_gomez",
        "guest": "torrente",
        "text": "¡Autónomos, inspectores, ministros y centollos! ¡Vayan en fila india a tomar por el saco! ¡A la mierda todos!",
        "badge": "💥 ¡A LA MIERDA EN FILA INDIA!",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO VIII: LA FILOSOFÍA DEL COCODRILO Y LA GRASA NOBLE (14:00 - 16:00 / Bloques 85-96) ---
    {
        "id": 85,
        "speaker": "xabi",
        "guest": "borja",
        "text": "El secreto de la longevidad, Borja, es hacer como el cocodrilo del Nilo: quedarse quieto en el lodo diez horas esperando a que pase la gacela.",
        "badge": "🐊 XABI // EL COCODRILO DEL NILO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 86,
        "speaker": "borja",
        "guest": "xabi",
        "text": "Exacto, Xabi. Calma hidrostática. En física de sistemas, moverse sin gradiente termodinámico es puro gasto de fricción inútil.",
        "badge": "⚖️ CALMA HIDROSTÁTICA // SISTEMAS",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 87,
        "speaker": "luengo",
        "guest": "xabi",
        "text": "Mucho cocodrilo pero si la gacela te viene armada con una recortada, más vale que salgas del lodo echando chispas, chaval.",
        "badge": "🐅 LUENGO // GACELA ARMADA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 88,
        "speaker": "escohotado",
        "guest": "luengo",
        "text": "La lucidez no radica en temer a la gacela ni en esconderse, sino en conocer la dosis exacta que separa el veneno del remedio.",
        "badge": "📚 ESCOHOTADO // LA DOSIS EXACTA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 89,
        "speaker": "julio_iglesias",
        "guest": "escohotado",
        "text": "La dosis exacta de amor, noche y buena música... ¡y lo sabes! Eso no te lo enseña ningún libro de texto.",
        "badge": "🎶 AMOR, NOCHE Y BUENA MÚSICA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 90,
        "speaker": "alain",
        "guest": "julio_iglesias",
        "text": "Julio, te voy a fichar para cantar el estribillo de nuestra próxima sesión a 110 BPM. ¡Vas a sonar más rotundo que los graves de Mitxu!",
        "badge": "🎤 JULIO A 110 BPM // BANGER",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 91,
        "speaker": "mitxu",
        "guest": "alain",
        "text": "¡Eso sí que sería apoteósico! Julio Iglesias metiendo coros sobre la caja de 909 y los bombos del Consorcio Gaupa. ¡Temazo histórico!",
        "badge": "🔥 COROS DE JULIO // 909 BEAT",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 92,
        "speaker": "sam_altman",
        "guest": "mitxu",
        "text": "We can generate a synthetic clone of Julio Iglesias singing cyber-flamenco in real time using ten clusters of H100 GPUs.",
        "badge": "🤖 JULIO SYNTHETIC CLONE // H100",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 93,
        "speaker": "fernan_gomez",
        "guest": "sam_altman",
        "text": "¡Malditos clones! ¡Un artista de verdad suda, bebe, grita y manda a la mierda a los que le tocan las narices!",
        "badge": "💥 ARTISTA DE VERDAD VS CLON",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 94,
        "speaker": "torrente",
        "guest": "fernan_gomez",
        "text": "Don Fernando, usted sí que sabe. Menos ordenadores y más carajillos de Veterano por las mañanas para engrasar las cuerdas vocales.",
        "badge": "☕ CARAJILLO DE VETERANO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 95,
        "speaker": "inspector_hacienda",
        "guest": "torrente",
        "text": "El carajillo matutino tributa como consumo suntuario al tipo general del veintiuno por ciento más recargo de equivalencia.",
        "badge": "📑 21% DE IVA AL CARAJILLO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 96,
        "speaker": "borja",
        "guest": "inspector_hacienda",
        "text": "El inspector acaba de alcanzar el límite asintótico de la ridiculez fiscal. Su entropía interna supera su exergía disponible.",
        "badge": "📉 COLAPSO ENTRÓPICO FISCAL",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO IX: LA DISERTACIÓN DE CHIQUITO Y ECHENIQUE (16:00 - 18:00 / Bloques 97-108) ---
    {
        "id": 97,
        "speaker": "chiquito",
        "guest": "borja",
        "text": "¡¿Qué pasa, comor?! ¡Siete ministros vienen de Bonanza con la cartera vacía! ¡No te digo trigo por no llamarte Rodrigor! ¡Te das cuen!",
        "badge": "💃 SIETE MINISTROS DE BONANZA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 98,
        "speaker": "echenique",
        "guest": "chiquito",
        "text": "Compañero Chiquito, tu cadencia rítmica genera ondas gravitacionales que desacoplan la deuda soberana del Banco Central Europeo.",
        "badge": "🏎️ ONDAS GRAVITACIONALES",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 99,
        "speaker": "pedro_sanchez",
        "guest": "echenique",
        "text": "Hemos alcanzado un acuerdo histórico con Chiquito de la Calzada para nombrar sus interjecciones como Patrimonio Inmaterial de la Resistencia.",
        "badge": "📜 PATRIMONIO DE LA RESISTENCIA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 100,
        "speaker": "rajoy",
        "guest": "pedro_sanchez",
        "text": "Pedro, los acuerdos históricos duran lo que dura un pastel en la puerta de un colegio, o menos todavía si pasa Alain con el M3.",
        "badge": "🏛️ EL PASTEL Y EL M3",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 101,
        "speaker": "alain",
        "guest": "rajoy",
        "text": "¡A doscientos por la M-30 esquivando acuerdos parlamentarios! ¡Aquí la única ley es la ley de la palanca y el chuletón!",
        "badge": "🏎️ LEY DE LA PALANCA Y CHULETÓN",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 102,
        "speaker": "luengo",
        "guest": "alain",
        "text": "El chuletón se come poco hecho, con sal gorda y sin mariconadas de salsa de pimienta. El que le eche salsa a una chuleta, machetazo.",
        "badge": "🐅 SAL GORDA Y MACHETAZO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 103,
        "speaker": "xabi",
        "guest": "luengo",
        "text": "Eso es sagrado, Luengo. La carne buena no necesita adornos, igual que una buena tarde de lluvia no necesita televisión.",
        "badge": "🌧️ CARNE BUENA Y TARDE DE LLUVIA",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 104,
        "speaker": "lander",
        "guest": "xabi",
        "text": "Y si se va la luz por la lluvia, os saco la batería del M3 y os enchufo la cafetera con un par de pinzas de arranque de camión.",
        "badge": "🔋 BATERÍA Y PINZAS DE ARRANQUE",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 105,
        "speaker": "eddie_fenwick",
        "guest": "lander",
        "text": "Y si la cafetera pesa demasiado, la levanto con las uñas de la Fenwick y os la pongo en la mesa del estudio con precisión milimétrica.",
        "badge": "🚜 PRECISIÓN DE FENWICK",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 106,
        "speaker": "tati_centollo",
        "guest": "eddie_fenwick",
        "text": "¡Y el centollo abre las cápsulas de café con las pinzas! ¡Cero plástico, reciclaje orgánico de fondo marino!",
        "badge": "🦀 RECICLAJE MARINO BIÓNICO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 107,
        "speaker": "nacho",
        "guest": "tati_centollo",
        "text": "Esto se nos ha ido completamente de las manos. Hemos empezado hablando de física cuántica y estamos domesticando marisco en Uribarri.",
        "badge": "📉 DELIRIO ABSOLUTO // NACHO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 108,
        "speaker": "borja",
        "guest": "nacho",
        "text": "Nacho, en la teoría del caos, el batir de alas de un centollo en Uribarri provoca un crash financiero en Wall Street. Todo está conectado.",
        "badge": "🦋 EFECTO CENTOLLO // CAOS",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    },

    # --- ACTO X: EL COLAPSO TERMODINÁMICO Y EL GRAN DROP FINAL (18:00 - 20:00 / Bloques 109-120) ---
    {
        "id": 109,
        "speaker": "moskv1",
        "guest": "borja",
        "text": "Alerta crítica: la resonancia de los 21 invitados ha saturado el espacio de fases. Fricción disipada: máxima. Preparando colapso del búnker.",
        "badge": "🚨 SATURACIÓN DE FASES // SKYNET",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 110,
        "speaker": "mitxu",
        "guest": "moskv1",
        "text": "¡Que no colapse nada sin el drop! ¡Borja, mete el bajo de cien BPM que vamos a reventar los cristales del Casco Viejo!",
        "badge": "🔊 DROP KATANA 100 BPM",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 111,
        "speaker": "alain",
        "guest": "mitxu",
        "text": "¡El 25 aparcamos el microchip, cerramos Hacienda y nos comemos ese chuletón en Villa Melilla! ¡Aúpa cuadrilla!",
        "badge": "🥩 CHULETÓN FINAL // VILLA MELILLA",
        "prop": "sp_prop_spiz.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 112,
        "speaker": "chiquito",
        "guest": "alain",
        "text": "¡Al ataquerl! ¡Siete caballos galopando en el drop! ¡Te das cuen! ¡Hasta luego, Lucas!",
        "badge": "💃 ¡HASTA LUEGO, LUCAS!",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 113,
        "speaker": "rajoy",
        "guest": "chiquito",
        "text": "Fin de la cita. Y viva el vino, viva Bilbao y vivan las personas humanas que no dan la lata con los impuestos.",
        "badge": "🏛️ FIN DE LA CITA // VIVA EL VINO",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 114,
        "speaker": "pedro_sanchez",
        "guest": "rajoy",
        "text": "Nos vemos en las próximas elecciones cuánticas a bordo del Falcon con el chuletón homologado por la Unión Europea.",
        "badge": "✈️ ELECCIONES CUÁNTICAS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 115,
        "speaker": "elon_musk",
        "guest": "pedro_sanchez",
        "text": "Sending one copy of this podcast to Mars in the glovebox of the Cybertruck. Alien civilizations need to hear Alain.",
        "badge": "🚀 CYBERTRUCK TO MARS",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 116,
        "speaker": "sam_altman",
        "guest": "elon_musk",
        "text": "We are pausing all artificial intelligence research until we can solve why Mitxu is so confident about 1999.",
        "badge": "🤖 PAUSING AI RESEARCH",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 117,
        "speaker": "julio_iglesias",
        "guest": "sam_altman",
        "text": "El secreto de Mitxu se llama duende y autenticidad del norte... ¡y lo sabéis todos!",
        "badge": "🎶 DUENDE Y AUTENTICIDAD",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 118,
        "speaker": "torrente",
        "guest": "julio_iglesias",
        "text": "¡Vámonos de fiesta ya, joder, que se enfrían las bravas y nos cierran el garito! ¡Paga el inspector de Hacienda!",
        "badge": "🍺 PAGA EL INSPECTOR",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 119,
        "speaker": "fernan_gomez",
        "guest": "torrente",
        "text": "¡Por fin una propuesta con sentido común! ¡Camarero, una ronda general y que le manden la factura a Montoro! ¡A la mierda!",
        "badge": "💥 ¡A LA MIERDA Y RONDA GENERAL!",
        "prop": "sp_desk_mics.png",
        "bg": "sp_studio_bg.png"
    },
    {
        "id": 120,
        "speaker": "borja",
        "guest": "moskv1",
        "text": "Esto ha sido Jarana Cast: el podcast sin nata. Apaguen las pantallas, abracen a los suyos y cómanse una chuleta con grasa noble. Fin de la transmisión.",
        "badge": "🛸 BORJA // FIN DE LA TRANSMISIÓN SOBERANA",
        "prop": "sp_prop_concerta.png",
        "bg": "sp_studio_bg.png"
    }
]

# Voice synthesis profiles for each speaker
VOICE_PROFILES = {
    "borja": {"voice": "es-ES-AlvaroNeural", "rate": "+2%", "pitch": "-2Hz"},
    "alain": {"voice": "es-ES-AlvaroNeural", "rate": "+12%", "pitch": "+4Hz"},
    "mitxu": {"voice": "es-ES-AlvaroNeural", "rate": "-4%", "pitch": "-4Hz"},
    "luengo": {"voice": "es-ES-AlvaroNeural", "rate": "+8%", "pitch": "-6Hz"},
    "nacho": {"voice": "es-ES-AlvaroNeural", "rate": "+5%", "pitch": "+3Hz"},
    "xabi": {"voice": "es-ES-AlvaroNeural", "rate": "-14%", "pitch": "-4Hz"},
    "tati_centollo": {"voice": "es-ES-AlvaroNeural", "rate": "+4%", "pitch": "-2Hz"},
    "eddie_fenwick": {"voice": "es-ES-AlvaroNeural", "rate": "+6%", "pitch": "-6Hz"},
    "lander": {"voice": "es-ES-AlvaroNeural", "rate": "+4%", "pitch": "+0Hz"},
    "rajoy": {"voice": "es-ES-AlvaroNeural", "rate": "-16%", "pitch": "-8Hz"},
    "pedro_sanchez": {"voice": "es-ES-AlvaroNeural", "rate": "+0%", "pitch": "+1Hz"},
    "escohotado": {"voice": "es-ES-AlvaroNeural", "rate": "-20%", "pitch": "-10Hz"},
    "fernan_gomez": {"voice": "es-ES-AlvaroNeural", "rate": "+12%", "pitch": "-12Hz"},
    "elon_musk": {"voice": "en-US-GuyNeural", "rate": "-4%", "pitch": "-2Hz"},
    "sam_altman": {"voice": "en-US-EricNeural", "rate": "+4%", "pitch": "+3Hz"},
    "torrente": {"voice": "es-ES-AlvaroNeural", "rate": "+6%", "pitch": "-6Hz"},
    "julio_iglesias": {"voice": "es-ES-AlvaroNeural", "rate": "-10%", "pitch": "+2Hz"},
    "inspector_hacienda": {"voice": "es-ES-AlvaroNeural", "rate": "+16%", "pitch": "+8Hz"},
    "chiquito": {"voice": "es-ES-AlvaroNeural", "rate": "+22%", "pitch": "+8Hz"},
    "echenique": {"voice": "es-ES-AlvaroNeural", "rate": "+0%", "pitch": "+0Hz"},
    "moskv1": {"voice": "es-ES-AlvaroNeural", "rate": "+25%", "pitch": "-10Hz"},
}

sem = asyncio.Semaphore(8)

async def synthesize_scene_audio(scene):
    sid = scene["id"]
    speaker = scene["speaker"]
    text = scene["text"]
    out_mp3 = f"{AUDIO_DIR}/scene_{sid:03d}.mp3"
    padded_wav = f"{AUDIO_DIR}/scene_{sid:03d}_pad.wav"
    
    cfg = VOICE_PROFILES.get(speaker, {"voice": "es-ES-AlvaroNeural", "rate": "+0%", "pitch": "+0Hz"})
    
    # 1. Synthesize TTS with retry
    async with sem:
        for attempt in range(4):
            try:
                communicate = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"])
                await communicate.save(out_mp3)
                break
            except Exception as e:
                if attempt == 3:
                    # Fallback to plain AlvaroNeural without pitch/rate
                    communicate = edge_tts.Communicate(text, "es-ES-AlvaroNeural")
                    await communicate.save(out_mp3)
                await asyncio.sleep(0.6 * (attempt + 1))
    
    # 2. Pad or adjust to exactly 10.0 seconds with slight silence/room-tone
    # ffmpeg: apad, atrim to exactly 10.00s, 44100Hz, stereo
    cmd = [
        "ffmpeg", "-y", "-i", out_mp3,
        "-af", f"apad=whole_dur={SCENE_DURATION_SEC},atrim=0:{SCENE_DURATION_SEC}",
        "-ar", "44100", "-ac", "2",
        padded_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return padded_wav

async def main():
    print(f"[*] Starting 120-Agent parallel audio generation ({TOTAL_SCENES} scenes)...")
    tasks = [synthesize_scene_audio(s) for s in SCENES]
    padded_wavs = await asyncio.gather(*tasks)
    print(f"[+] All {len(padded_wavs)} audio scenes synthesized and normalized to 10.0s.")

    # 3. Concatenate all 120 WAV files into master WAV
    concat_list_file = f"{AUDIO_DIR}/concat_list.txt"
    with open(concat_list_file, "w") as f:
        for w in padded_wavs:
            f.write(f"file '{os.path.abspath(w)}'\n")
            
    master_wav = "public/podcast_delirio_master.wav"
    master_mp3 = "public/podcast_delirio_master.mp3"
    
    print("[*] Stitching 20-minute master audio with FFmpeg...")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_file,
        "-c:a", "pcm_s16le", master_wav
    ]
    subprocess.run(concat_cmd, check=True)
    
    # Compress to MP3 for Remotion StaticFile
    mp3_cmd = [
        "ffmpeg", "-y", "-i", master_wav,
        "-b:a", "192k", master_mp3
    ]
    subprocess.run(mp3_cmd, check=True)
    print(f"[+] Master audio generated: {master_mp3} ({TOTAL_DURATION_SEC}s / 20 min)")

    # 4. Generate per-frame telemetry (36,000 frames)
    print("[*] Computing 36,000-frame FFT audio telemetry and South Park flapGap...")
    sr, audio_data = wavfile.read(master_wav)
    if audio_data.ndim > 1:
        audio_mono = audio_data.mean(axis=1)
    else:
        audio_mono = audio_data
        
    audio_mono = audio_mono / (np.max(np.abs(audio_mono)) + 1e-9)
    samples_per_frame = sr / FPS
    
    frames_telemetry = []
    
    for f in range(TOTAL_FRAMES):
        time_sec = f / FPS
        scene_idx = min(int(time_sec / SCENE_DURATION_SEC), TOTAL_SCENES - 1)
        scene = SCENES[scene_idx]
        
        start_samp = int(f * samples_per_frame)
        end_samp = int(start_samp + samples_per_frame)
        chunk = audio_mono[start_samp:end_samp]
        
        rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
        
        # 16-band spectrum
        if len(chunk) >= 512:
            fft_vals = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk)), n=512))[:256]
            band_size = 16
            bands = []
            for b in range(16):
                b_val = float(np.mean(fft_vals[b*band_size:(b+1)*band_size]))
                bands.append(min(1.0, b_val * 4.0))
        else:
            bands = [0.0] * 16
            
        sub = float(np.mean(bands[:3]))
        mid = float(np.mean(bands[3:9]))
        high = float(np.mean(bands[9:]))
        
        # South Park flapGap (Canadian flip mouth)
        is_talking = rms > 0.025
        flap_gap = min(38.0, rms * 115.0) if is_talking else 0.0
        
        frames_telemetry.append({
            "frame": f,
            "time": round(time_sec, 3),
            "scene": scene_idx + 1,
            "speaker": scene["speaker"],
            "guest": scene["guest"],
            "text": scene["text"],
            "badge": scene["badge"],
            "prop": scene["prop"],
            "bg": scene["bg"],
            "rms": round(rms, 4),
            "sub": round(sub, 4),
            "mid": round(mid, 4),
            "high": round(high, 4),
            "bands": [round(x, 3) for x in bands],
            "flapGap": round(flap_gap, 2),
            "isTalking": is_talking
        })
        
    telemetry_data = {
        "metadata": {
            "title": "JARANA CAST: EL GRAN DELIRIO DE BILBAO (20 MINUTOS)",
            "totalScenes": TOTAL_SCENES,
            "totalDuration": TOTAL_DURATION_SEC,
            "totalFrames": TOTAL_FRAMES,
            "fps": FPS,
            "width": 1920,
            "height": 1080
        },
        "scenes": SCENES,
        "frames": frames_telemetry
    }
    
    with open("public/podcast_delirio_telemetry.json", "w", encoding="utf-8") as f:
        json.dump(telemetry_data, f, ensure_ascii=False)
        
    print(f"[+] Successfully exported public/podcast_delirio_telemetry.json ({TOTAL_FRAMES} frames).")

if __name__ == "__main__":
    asyncio.run(main())
