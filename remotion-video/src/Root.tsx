import "./index.css";
import { Composition } from "remotion";
import { CyberEpistemology20Min } from "./Composition";
import narrativeData from "../public/narrative_20min.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CyberEpistemology20Min"
        component={CyberEpistemology20Min}
        durationInFrames={narrativeData.metadata.totalFrames}
        fps={narrativeData.metadata.fps}
        width={narrativeData.metadata.width}
        height={narrativeData.metadata.height}
      />
    </>
  );
};
