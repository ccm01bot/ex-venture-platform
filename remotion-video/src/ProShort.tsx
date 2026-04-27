import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  useVideoConfig,
  Sequence,
  interpolate,
  useCurrentFrame,
  spring,
  staticFile,
} from "remotion";

/**
 * ProShort — Three-zone sandwich layout matching viral AI news reels:
 * - Zone 1 (top ~350px): Hook/header text on dark background
 * - Zone 2 (middle ~1100px): Screen recording at READABLE size, padded, rounded corners
 * - Zone 3 (bottom ~350px): Caption text on dark background
 *
 * The screen recording is NEVER cropped to fill — it's shown at a readable size
 * with dark background around it.
 */

const ProShort: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const videoSrc = staticFile("source_clip.mp4");

  // Subtle slow zoom on the video (Ken Burns)
  const kenBurns = interpolate(frame, [0, 1200], [1.0, 1.04], {
    extrapolateRight: "clamp",
  });

  // AI NEWS badge subtle pulse
  const badgePulse = interpolate(
    frame % 90,
    [0, 20, 40],
    [1, 1.04, 1],
    { extrapolateRight: "clamp" }
  );

  // Header text definitions - changes over time
  const headers: { text: string; accent: string; startSec: number; endSec: number }[] = [
    { text: "ANTHROPIC JUST KILLED", accent: "DESIGN", startSec: 0, endSec: 5 },
    { text: "ONE PROMPT CREATES", accent: "FULL DASHBOARDS", startSec: 5, endSec: 13 },
    { text: "CHARTS. TABLES.", accent: "LIVE DATA.", startSec: 13, endSec: 21 },
    { text: "CLAUDE DESIGN CHANGES", accent: "EVERYTHING", startSec: 21, endSec: 30 },
    { text: "AVAILABLE NOW FOR", accent: "PRO USERS", startSec: 30, endSec: 37 },
    { text: "FOLLOW", accent: "@EXAI", startSec: 37, endSec: 40 },
  ];

  // Caption text (bottom zone)
  const captions: { text: string; startSec: number; endSec: number }[] = [
    { text: "Anthropic's new AI design tool just dropped", startSec: 0, endSec: 5 },
    { text: "Type what you want — it builds everything", startSec: 5, endSec: 13 },
    { text: "Full interactive data visualizations from text", startSec: 13, endSec: 21 },
    { text: "Pitch decks, dashboards, apps — all from chat", startSec: 21, endSec: 30 },
    { text: "Free for Claude Pro subscribers", startSec: 30, endSec: 37 },
    { text: "New AI tools every day", startSec: 37, endSec: 40 },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0f" }}>
      {/* === ZONE 1: TOP — Dark background with header text === */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 370,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: "0 40px",
          background: "linear-gradient(180deg, #0a0a1a 0%, #0d0d18 100%)",
        }}
      >
        {/* EXAI branding + AI NEWS badge row */}
        <div
          style={{
            position: "absolute",
            top: 50,
            left: 30,
            right: 30,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          {/* EXAI GLOBAL */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 4,
                height: 24,
                backgroundColor: "#00ccff",
                borderRadius: 2,
              }}
            />
            <span
              style={{
                color: "#00ccff",
                fontSize: 18,
                fontWeight: "bold",
                fontFamily: "Inter, Arial, Helvetica, sans-serif",
                letterSpacing: 3,
              }}
            >
              EXAI GLOBAL
            </span>
          </div>

          {/* AI NEWS badge */}
          <div style={{ transform: `scale(${badgePulse})` }}>
            <div
              style={{
                backgroundColor: "#e60000",
                borderRadius: 6,
                padding: "6px 14px",
                boxShadow: "0 2px 8px rgba(230,0,0,0.4)",
              }}
            >
              <span
                style={{
                  color: "white",
                  fontSize: 15,
                  fontWeight: "bold",
                  fontFamily: "Inter, Arial, Helvetica, sans-serif",
                  letterSpacing: 2,
                }}
              >
                AI NEWS
              </span>
            </div>
          </div>
        </div>

        {/* Header text — animated */}
        {headers.map((h, i) => {
          const startFrame = h.startSec * fps;
          const endFrame = h.endSec * fps;
          const dur = endFrame - startFrame;

          return (
            <Sequence key={`h-${i}`} from={startFrame} durationInFrames={dur}>
              <HeaderText
                text={h.text}
                accent={h.accent}
                fps={fps}
                localFrame={Math.max(0, frame - startFrame)}
                durationFrames={dur}
                isFirst={i === 0}
              />
            </Sequence>
          );
        })}
      </div>

      {/* === ZONE 2: MIDDLE — Screen recording, readable, padded === */}
      <div
        style={{
          position: "absolute",
          top: 370,
          left: 0,
          right: 0,
          height: 1100,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: "10px 30px",
        }}
      >
        {/* Subtle colored glow behind the video */}
        <div
          style={{
            position: "absolute",
            width: "90%",
            height: "80%",
            borderRadius: 24,
            background:
              "radial-gradient(ellipse at center, rgba(0, 100, 255, 0.08) 0%, transparent 70%)",
            filter: "blur(40px)",
          }}
        />

        {/* Video container with rounded corners and shadow */}
        <div
          style={{
            width: "100%",
            height: "100%",
            borderRadius: 16,
            overflow: "hidden",
            boxShadow: "0 8px 40px rgba(0,0,0,0.6), 0 0 60px rgba(0,100,255,0.1)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <OffthreadVideo
            src={videoSrc}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              transform: `scale(${kenBurns})`,
              backgroundColor: "#111118",
            }}
          />
        </div>
      </div>

      {/* === ZONE 3: BOTTOM — Caption text === */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 450,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: "0 50px",
          background: "linear-gradient(0deg, #0a0a1a 0%, #0d0d18 100%)",
        }}
      >
        {/* Caption text — animated */}
        {captions.map((c, i) => {
          const startFrame = c.startSec * fps;
          const endFrame = c.endSec * fps;
          const dur = endFrame - startFrame;

          return (
            <Sequence key={`c-${i}`} from={startFrame} durationInFrames={dur}>
              <CaptionText
                text={c.text}
                fps={fps}
                localFrame={Math.max(0, frame - startFrame)}
                durationFrames={dur}
              />
            </Sequence>
          );
        })}

        {/* Subscribe CTA — last 5 seconds */}
        {frame >= fps * 35 && (
          <SubscribeCTA
            fps={fps}
            localFrame={Math.max(0, frame - fps * 35)}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

// === COMPONENT: Header text with accent word ===
const HeaderText: React.FC<{
  text: string;
  accent: string;
  fps: number;
  localFrame: number;
  durationFrames: number;
  isFirst: boolean;
}> = ({ text, accent, fps, localFrame, durationFrames, isFirst }) => {
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  const translateY = interpolate(entrance, [0, 1], [40, 0]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  const fadeOut = interpolate(
    localFrame,
    [durationFrames - 10, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // First header gets a scale-up effect
  const scale = isFirst
    ? interpolate(
        spring({ frame: localFrame, fps, config: { damping: 10, stiffness: 80 } }),
        [0, 1],
        [0.5, 1]
      )
    : 1;

  return (
    <div
      style={{
        position: "absolute",
        top: 120,
        left: 30,
        right: 30,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: opacity * fadeOut,
        transform: `translateY(${translateY}px) scale(${scale})`,
      }}
    >
      <span
        style={{
          color: "white",
          fontSize: 48,
          fontWeight: 900,
          fontFamily: "Inter, Arial, Helvetica, sans-serif",
          textAlign: "center",
          letterSpacing: 1,
          lineHeight: 1.1,
        }}
      >
        {text}
      </span>
      <span
        style={{
          color: "#FFD700",
          fontSize: 56,
          fontWeight: 900,
          fontFamily: "Inter, Arial, Helvetica, sans-serif",
          textAlign: "center",
          letterSpacing: 1,
          lineHeight: 1.2,
          textShadow: "0 0 30px rgba(255, 215, 0, 0.3)",
          marginTop: 4,
        }}
      >
        {accent}
      </span>
    </div>
  );
};

// === COMPONENT: Caption text (bottom zone) ===
const CaptionText: React.FC<{
  text: string;
  fps: number;
  localFrame: number;
  durationFrames: number;
}> = ({ text, fps, localFrame, durationFrames }) => {
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 16, stiffness: 140 },
  });
  const translateY = interpolate(entrance, [0, 1], [25, 0]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  const fadeOut = interpolate(
    localFrame,
    [durationFrames - 8, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 40,
        left: 30,
        right: 30,
        display: "flex",
        justifyContent: "center",
        opacity: opacity * fadeOut,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <span
        style={{
          color: "rgba(255, 255, 255, 0.85)",
          fontSize: 32,
          fontWeight: 500,
          fontFamily: "Inter, Arial, Helvetica, sans-serif",
          textAlign: "center",
          lineHeight: 1.4,
        }}
      >
        {text}
      </span>
    </div>
  );
};

// === COMPONENT: Subscribe CTA ===
const SubscribeCTA: React.FC<{
  fps: number;
  localFrame: number;
}> = ({ fps, localFrame }) => {
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 12, stiffness: 100 },
  });
  const scale = interpolate(entrance, [0, 1], [0.5, 1]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  const pulse = interpolate(
    localFrame % 30,
    [0, 15, 30],
    [1, 1.08, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: 60,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          backgroundColor: "#ff0000",
          borderRadius: 12,
          padding: "14px 50px",
          transform: `scale(${pulse})`,
          boxShadow: "0 4px 20px rgba(255,0,0,0.4)",
        }}
      >
        <span
          style={{
            color: "white",
            fontSize: 26,
            fontWeight: "bold",
            fontFamily: "Inter, Arial, Helvetica, sans-serif",
            letterSpacing: 3,
          }}
        >
          SUBSCRIBE
        </span>
      </div>
    </div>
  );
};

export { ProShort };
