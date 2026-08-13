import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import pLimit from 'p-limit';
import { GoogleGenAI } from '@google/genai';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuraciones
const CONCURRENCY_LIMIT = 3;
const limit = pLimit(CONCURRENCY_LIMIT);
const PUBLIC_DIR = path.resolve(__dirname, '../remotion-video/public');
const CLIPS_DIR = path.join(PUBLIC_DIR, 'clips');
const AUDIOS_DIR = path.join(PUBLIC_DIR, 'audios');

// Simulación de los clientes API (en producción se usan los SDK reales y las keys de .env)
const genai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || 'dummy_key' });

/**
 * Función helper para simular peticiones con sleep
 */
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Paso 1: Generar Voz (ElevenLabs Placeholder)
 */
async function generateVoice(scene) {
  const audioPath = path.join(AUDIOS_DIR, `voice_${scene.id}.mp3`);
  console.log(`[ElevenLabs] Generando audio para escena ${scene.id}...`);
  await sleep(1500); // Simula el retraso de red
  // En un entorno real se llama a ElevenLabs:
  // const response = await fetch("https://api.elevenlabs.io/v1/text-to-speech/...", { ... });
  // const buffer = await response.arrayBuffer();
  // await fs.writeFile(audioPath, Buffer.from(buffer));
  await fs.writeFile(audioPath, `Dummy audio for scene ${scene.id}`);
  console.log(`✅ [ElevenLabs] Audio guardado en ${audioPath}`);
  return `http://localhost:3000/audios/voice_${scene.id}.mp3`; // Dummy URL para el payload de Sync Labs
}

/**
 * Paso 2: Generar Video Estático (Gemini Omni Flash Placeholder)
 */
async function generateBaseVideo(scene) {
  console.log(`[Gemini] Generando video base para escena ${scene.id}...`);
  await sleep(2000); // Simulación Gemini API
  // let response = await genai.models.generateContent({
  //    model: 'gemini-omni-flash-preview',
  //    contents: scene.geminiPrompt,
  // });
  const dummyVideoUrl = `http://dummy.url/video_base_${scene.id}.mp4`;
  console.log(`✅ [Gemini] Video base generado para escena ${scene.id}`);
  return dummyVideoUrl;
}

/**
 * Paso 3: Sincronización Labial (Sync Labs API Tracker)
 */
async function performLipSync(scene, videoUrl, audioUrl) {
  console.log(`[Sync Labs] Iniciando sincronización labial para escena ${scene.id}...`);
  const apiKey = process.env.SYNC_LABS_API_KEY || 'dummy_sync_key';
  
  // 1. Iniciar el trabajo
  // const startRes = await fetch("https://api.synclabs.so/video", {
  //   method: "POST",
  //   headers: { "x-api-key": apiKey, "Content-Type": "application/json" },
  //   body: JSON.stringify({
  //     audioUrl,
  //     videoUrl,
  //     model: "sync-1.7"
  //   })
  // });
  // const { id: jobId } = await startRes.json();
  const jobId = `dummy_job_${scene.id}`;
  
  // 2. Polling loop
  let isCompleted = false;
  let finalVideoUrl = `http://dummy.url/synced_video_${scene.id}.mp4`;
  
  console.log(`[Sync Labs] Polling trabajo ${jobId} para escena ${scene.id}...`);
  for (let i = 0; i < 5; i++) {
    await sleep(2000); // Esperar 2 segundos antes del siguiente polling
    // const statusRes = await fetch(`https://api.synclabs.so/video/${jobId}`, { headers: { "x-api-key": apiKey }});
    // const statusData = await statusRes.json();
    // if (statusData.status === 'completed') { ... }
    console.log(`[Sync Labs] Job ${jobId} status: processing... (${i+1}/5)`);
  }
  
  console.log(`✅ [Sync Labs] Sincronización completada para escena ${scene.id}`);
  return finalVideoUrl;
}

/**
 * Paso 4: Descargar el archivo final
 */
async function downloadFinalClip(scene, url) {
  const destPath = path.join(CLIPS_DIR, `ucvh_ready_${scene.id}.mp4`);
  console.log(`[Local] Descargando resultado final para escena ${scene.id}...`);
  await sleep(1000);
  // Simulación de volcado de buffer
  await fs.writeFile(destPath, `Dummy final video content for ${scene.id}`);
  console.log(`✅ [Local] Clip final descargado: ${destPath}`);
}

/**
 * Orquestador principal de la escena
 */
async function processScene(scene) {
  console.log(`\n--- Iniciando procesamiento Escena ${scene.id} ---`);
  
  try {
    // Generar Audio y Video en paralelo (Paso 1 y 2)
    const [audioUrl, videoUrl] = await Promise.all([
      generateVoice(scene),
      generateBaseVideo(scene)
    ]);
    
    // Iniciar Sincronización (Paso 3)
    const finalVideoUrl = await performLipSync(scene, videoUrl, audioUrl);
    
    // Descargar a local (Paso 4)
    await downloadFinalClip(scene, finalVideoUrl);
    
    console.log(`🎉 --- Escena ${scene.id} completada exitosamente ---`);
  } catch (error) {
    console.error(`❌ Error procesando escena ${scene.id}:`, error);
  }
}

/**
 * Ejecución asíncrona controlada por concurrencia
 */
async function main() {
  await fs.mkdir(CLIPS_DIR, { recursive: true });
  await fs.mkdir(AUDIOS_DIR, { recursive: true });

  const podcastData = JSON.parse(await fs.readFile(path.join(__dirname, 'ucvh_podcast.json'), 'utf-8'));
  console.log(`Iniciando orquestación de ${podcastData.scenes.length} escenas. Concurrencia máxima: ${CONCURRENCY_LIMIT}`);
  
  const tasks = podcastData.scenes.map(scene => limit(() => processScene(scene)));
  
  await Promise.all(tasks);
  
  console.log('\n✅ Pipeline completo. Todos los clips generados y listos para Remotion.');
}

main().catch(console.error);
