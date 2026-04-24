import { Composition } from "remotion";
import { VideoClip } from "./VideoClip";

export const ShortClip: React.FC = () => {
  return (
    <>
      <Composition
        id="Short"
        component={VideoClip}
        durationInFrames={30 * 58}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          src: "",
          startFrom: 0,
          duration: 58,
          title: "",
        }}
      />
    </>
  );
};
