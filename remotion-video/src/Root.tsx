import "./index.css";
import { Composition } from "remotion";
import { CyberEpistemology20Min } from "./Composition";
import { VideoCocodriloFilosofo } from "./VideoCocodriloFilosofo";
import { ParodiaDiscursoOdio } from "./ParodiaDiscursoOdio";

import narrativeData from "../public/narrative_20min.json";
import cocodriloData from "../public/cocodrilo_estructura.json";
import ucvhData from "../public/ucvh_odio.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
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

      {/* Composición 3: UCVH — Sátira Discurso de Odio y Moderación (20 Min) */}
      <Composition
        id="ParodiaDiscursoOdio"
        component={ParodiaDiscursoOdio}
        durationInFrames={ucvhData.metadata.totalDurationFrames}
        fps={ucvhData.metadata.fps}
        width={ucvhData.metadata.width}
        height={ucvhData.metadata.height}
      />
    </>
  );
};
