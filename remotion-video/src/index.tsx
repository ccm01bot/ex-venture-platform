import React from "react";
import { registerRoot } from "remotion";
import { Composition } from "remotion";
import { VideoClip } from "./VideoClip";
import { NewsShort } from "./NewsShort";

const Root: React.FC = () => {
  return (
    <>
      {/* Original video-based Short */}
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
      {/* Text-based News Short (no video source needed) */}
      <Composition
        id="NewsShort"
        component={NewsShort}
        durationInFrames={30 * 35}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          title: "Breaking News",
          lines: [
            "First news line goes here",
            "Second line with more detail",
            "Third line wraps up the story",
          ],
          accentColor: "#00aaff",
        }}
      />
    </>
  );
};

registerRoot(Root);
