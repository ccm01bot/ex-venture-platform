import React from "react";
import { registerRoot } from "remotion";
import { Composition } from "remotion";
import { VideoClip } from "./VideoClip";
import { NewsShort } from "./NewsShort";
import { DemoShort } from "./DemoShort";
import { UltimateShort } from "./UltimateShort";
import { HookTest } from "./HookTest";
import { EngagementShort } from "./EngagementShort";
import { ProShort } from "./ProShort";

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
      {/* Claude Design Demo Short */}
      <Composition
        id="DemoShort"
        component={DemoShort}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* Ultimate Algorithm-Optimized Short */}
      <Composition
        id="UltimateShort"
        component={UltimateShort}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* Hook Test - Pattern Interrupt Short */}
      <Composition
        id="HookTest"
        component={HookTest}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* Engagement-Optimized Short */}
      <Composition
        id="EngagementShort"
        component={EngagementShort}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* Pro Short - Three-zone sandwich layout (readable screen recording) */}
      <Composition
        id="ProShort"
        component={ProShort}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};

registerRoot(Root);
