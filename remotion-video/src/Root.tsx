import "./index.css";
import { Composition } from "remotion";
import { CyberEpistemology20Min } from "./Composition";
import { VideoCocodriloFilosofo } from "./VideoCocodriloFilosofo";
import { ParodiaDiscursoOdio } from "./ParodiaDiscursoOdio";
import { Test1MinVideo } from "./Test1MinVideo";

import narrativeData from "../public/narrative_20min.json";
import cocodriloData from "../public/cocodrilo_estructura.json";
import ucvhData from "../public/ucvh_odio.json";

import { VideoclipBacalaDeTroya } from "./VideoclipBacalaDeTroya";
import { PodcastAlainElektrocaniche } from "./PodcastAlainElektrocaniche";
import { PodcastSouthParkAlain } from "./PodcastSouthParkAlain";
import { PodcastChiquitoBorjaAlain } from "./PodcastChiquitoBorjaAlain";
import { VideoclipMitxu100BPM } from "./VideoclipMitxu100BPM";
import { VideoclipCeutong } from "./VideoclipCeutong";
import { VideoclipVillaMelilla } from "./VideoclipVillaMelilla";
import { PodcastSouthParkDelirio20Min } from "./PodcastSouthParkDelirio20Min";
import podcastData from "../public/podcast_data.json";
import spData from "../public/southpark_data.json";
import chiquitoData from "../public/chiquito_podcast_data.json";
import mitxuVideoData from "../public/mitxu_videoclip_data.json";
import ceutongData from "../public/ceutong_telemetry.json";
import { UniversalSouthParkVideo } from "./UniversalSouthParkVideo";
import universalTelemetry from "../public/universal_video_telemetry.json";
import { StreetFighterBerghain } from "./StreetFighterBerghain";
import { StreetFighterOteguiVsEscohotado } from "./StreetFighterOteguiVsEscohotado";
import villaMelillaData from "../public/villamelilla_telemetry.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* STREET FIGHTER: GORKA OTEGUI («OTE») vs. ANTONIO ESCOHOTADO */}
      <Composition
        id="StreetFighterOteguiVsEscohotado"
        component={StreetFighterOteguiVsEscohotado}
        durationInFrames={1500}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* UNIVERSAL MASTER GENERATOR COMPOSITION: SOUTH PARK & CINEMATIC SOTA */}
      <Composition
        id="UniversalSouthParkVideo"
        component={UniversalSouthParkVideo}
        durationInFrames={universalTelemetry.metadata.totalFrames || 6300}
        fps={universalTelemetry.metadata.fps || 30}
        width={universalTelemetry.metadata.width || 1920}
        height={universalTelemetry.metadata.height || 1080}
      />

      {/* STREET FIGHTER: CONDE CERO (BILBAO) vs. FETO INFINITO & NIÑA KRAVITZ */}
      <Composition
        id="StreetFighterBerghain"
        component={StreetFighterBerghain}
        durationInFrames={5400}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* PODCAST DELIRIO 20 MIN: 120 Escenas, 21 Invitados, South Park SOTA */}
      <Composition
        id="PodcastSouthParkDelirio20Min"
        component={PodcastSouthParkDelirio20Min}
        durationInFrames={36000}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Videoclip VILLA MELILLA: Ciudad Vacacional 0% Tax (Borja, Alain, Mitxu, Chiquito, Echenique, MacGyver) */}
      <Composition
        id="VideoclipVillaMelilla"
        component={VideoclipVillaMelilla}
        durationInFrames={villaMelillaData.metadata.totalFrames}
        fps={villaMelillaData.metadata.fps}
        width={1920}
        height={1080}
      />
      {/* Videoclip CEUTONG: El Hong Kong del Estrecho (Chiquito, Echenique, MacGyver) */}
      <Composition
        id="VideoclipCeutong"
        component={VideoclipCeutong}
        durationInFrames={ceutongData.metadata.totalFrames}
        fps={ceutongData.metadata.fps}
        width={1920}
        height={1080}
      />
      {/* Videoclip Mitxu & Borja: Katana Silence 100 BPM (-40 BPM) */}
      <Composition
        id="VideoclipMitxu100BPM"
        component={VideoclipMitxu100BPM}
        durationInFrames={mitxuVideoData.metadata.totalFrames}
        fps={mitxuVideoData.metadata.fps}
        width={1920}
        height={1080}
      />

      {/* Podcast South Park / Chiquito: Borja Moskv vs. Alain Elektrocaniche (Explicaciones C5-REAL) */}
      <Composition
        id="PodcastChiquitoBorjaAlain"
        component={PodcastChiquitoBorjaAlain}
        durationInFrames={chiquitoData.metadata.totalFrames}
        fps={chiquitoData.metadata.fps}
        width={1920}
        height={1080}
      />

      {/* Podcast South Park: Alain Elektrocaniche Flap-Mouth (Voice Only, No Music) */}
      <Composition
        id="PodcastSouthParkAlain"
        component={PodcastSouthParkAlain}
        durationInFrames={spData.metadata.totalFrames}
        fps={spData.metadata.fps}
        width={1920}
        height={1080}
      />

      {/* Podcast SOTA: Alain Elektrocaniche (Cortezas y Concertas) */}
      <Composition
        id="PodcastAlainElektrocaniche"
        component={PodcastAlainElektrocaniche}
        durationInFrames={podcastData.metadata.totalFrames}
        fps={podcastData.metadata.fps}
        width={1920}
        height={1080}
      />
      {/* Composición Principal: Videoclip Bacala de Troya (Mitxu) Chicago Soul Electro */}
      <Composition
        id="VideoclipBacalaDeTroya"
        component={VideoclipBacalaDeTroya}
        durationInFrames={1828}
        fps={30}
        width={1080}
        height={1920}
      />

      {/* Composición 1: Cyber-Epistemology Industrial Noir (20 Min) */}
      <Composition
        id="CyberEpistemology20Min"
        component={CyberEpistemology20Min}
        durationInFrames={narrativeData.metadata.totalFrames}
        fps={narrativeData.metadata.fps}
        width={narrativeData.metadata.width}
        height={narrativeData.metadata.height}
      />

      {/* Composición 2: ¿Qué opinaría un cocodrilo? (20 Min) */}
      <Composition
        id="VideoCocodriloFilosofo"
        component={VideoCocodriloFilosofo}
        durationInFrames={cocodriloData.metadata.totalDurationFrames}
        fps={cocodriloData.metadata.fps}
        width={cocodriloData.metadata.width}
        height={cocodriloData.metadata.height}
      />

      {/* Composición 4: Vídeo de Prueba 1 Minuto (60s / 1800 frames) */}
      <Composition
        id="Test1MinVideo"
        component={Test1MinVideo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
