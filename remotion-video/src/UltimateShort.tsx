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

// Subtitle card component with pill background and spring animation
const SubtitleCard: React.FC<{
  text: string;
  frame: number;
  fps: number;
  localFrame: number;
  durationFrames: number;
}> = ({ text, fps, localFrame, durationFrames }) => {
  // Slide-up spring entrance
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });
  const translateY = interpolate(entrance, [0, 1], [60, 0]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  // Fade out in last 8 frames
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
        bottom: "30%",
        left: 40,
        right: 40,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        opacity: opacity * fadeOut,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.65)",
          borderRadius: 16,
          padding: "18px 36px",
          backdropFilter: "blur(8px)",
        }}
      >
        <span
          style={{
            color: "white",
            fontSize: 56,
            fontWeight: 900,
            fontFamily: "Arial, Helvetica, sans-serif",
            lineHeight: 1.2,
            letterSpacing: 2,
            textTransform: "uppercase",
            textAlign: "center",
            textShadow:
              "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.5), -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000",
            display: "block",
            whiteSpace: "pre-line",
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};

export const UltimateShort: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const totalFrames = 1200;

  const videoSrc = staticFile("source_clip.mp4");

  // --- HOOK: Freeze + Zoom (frames 0-50) ---
  // Video starts frozen for 0.5s (15 frames), then plays
  // Dramatic zoom: 1.0 -> 1.15 over first 50 frames
  const hookZoom = interpolate(frame, [0, 50], [1.0, 1.15], {
    extrapolateRight: "clamp",
  });

  // --- Ken Burns: slow continuous zoom 1.0 -> 1.08 over 40s ---
  const kenBurns = interpolate(frame, [0, totalFrames], [1.0, 1.08], {
    extrapolateRight: "clamp",
  });

  // Combine: use hook zoom for first 50 frames, then transition to ken burns
  const videoScale =
    frame <= 50
      ? hookZoom
      : interpolate(frame, [50, 80], [1.15, kenBurns], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

  // --- LOOP END: zoom out + fade (frames 1170-1200) ---
  const endZoom = interpolate(frame, [1170, 1200], [1, 0.92], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const endFade = interpolate(frame, [1170, 1200], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Final scale combines video scale with end zoom
  const finalScale = frame >= 1170 ? videoScale * endZoom : videoScale;

  // --- Hook text animation (scale from 0) ---
  const hookTextSpring = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 60 },
  });
  const hookTextScale = interpolate(hookTextSpring, [0, 1], [0, 1]);
  const hookTextOpacity = interpolate(hookTextSpring, [0, 1], [0, 1]);

  // AI NEWS badge pulse
  const newsBadgePulse = interpolate(
    frame % 90,
    [0, 20, 40],
    [1, 1.05, 1],
    { extrapolateRight: "clamp" }
  );

  // --- CTA subscribe animation ---
  const ctaLocalFrame = Math.max(0, frame - fps * 37);
  const ctaBadgePulse = interpolate(
    ctaLocalFrame % 30,
    [0, 10, 20, 30],
    [1, 1.12, 1, 1],
    { extrapolateRight: "clamp" }
  );
  const ctaGlow = interpolate(
    ctaLocalFrame % 60,
    [0, 30, 60],
    [0.3, 0.8, 0.3],
    { extrapolateRight: "clamp" }
  );

  const textShadow =
    "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.5), -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000";

  // Video playback: freeze on first frame for 15 frames (0.5s), then play
  const videoStartFrom = frame <= 15 ? 0 : frame - 15;

  // Subtitle definitions
  const subtitles: {
    text: string;
    startSec: number;
    endSec: number;
  }[] = [
    { text: "ANTHROPIC\nJUST KILLED\nDESIGN", startSec: 0, endSec: 4 },
    { text: "ONE PROMPT\nCREATES FULL\nDASHBOARDS", startSec: 4, endSec: 12 },
    { text: "CHARTS. TABLES.\nLIVE DATA.\nALL AI.", startSec: 12, endSec: 20 },
    { text: "CLAUDE DESIGN\nCHANGES\nEVERYTHING", startSec: 20, endSec: 30 },
    { text: "AVAILABLE NOW\nFOR PRO USERS", startSec: 30, endSec: 37 },
    { text: "FOLLOW\n@EXAI", startSec: 37, endSec: 40 },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "black", opacity: endFade }}>
      {/* Background video with freeze-frame hook */}
      <div
        style={{
          width: "100%",
          height: "100%",
          overflow: "hidden",
        }}
      >
        <OffthreadVideo
          src={videoSrc}
          startFrom={videoStartFrom}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${finalScale})`,
          }}
        />
      </div>

      {/* Top gradient */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 80,
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 100%)",
        }}
      />

      {/* Bottom gradient */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 200,
          background:
            "linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.3) 50%, transparent 100%)",
        }}
      />

      {/* EXAI GLOBAL top-left with accent bar */}
      <div
        style={{
          position: "absolute",
          top: 55,
          left: 30,
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <div
          style={{
            width: 4,
            height: 28,
            backgroundColor: "#00ccff",
            borderRadius: 2,
          }}
        />
        <span
          style={{
            color: "#00ccff",
            fontSize: 20,
            fontWeight: "bold",
            fontFamily: "Arial, Helvetica, sans-serif",
            textShadow: "0 1px 6px rgba(0,0,0,0.9)",
            letterSpacing: 3,
          }}
        >
          EXAI GLOBAL
        </span>
      </div>

      {/* AI NEWS badge top-right */}
      <div
        style={{
          position: "absolute",
          top: 48,
          right: 30,
          transform: `scale(${newsBadgePulse})`,
        }}
      >
        <div
          style={{
            backgroundColor: "#e60000",
            borderRadius: 8,
            padding: "8px 18px",
            boxShadow: "0 2px 10px rgba(230,0,0,0.5)",
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: 18,
              fontWeight: "bold",
              fontFamily: "Arial, Helvetica, sans-serif",
              letterSpacing: 2,
            }}
          >
            AI NEWS
          </span>
        </div>
      </div>

      {/* Subtitle-style text overlays */}
      {subtitles.map((sub, i) => {
        const startFrame = sub.startSec * fps;
        const endFrame = sub.endSec * fps;
        const dur = endFrame - startFrame;

        // Special handling for first subtitle (hook) - use scale-from-0 spring
        if (i === 0) {
          return (
            <Sequence
              key={i}
              from={startFrame}
              durationInFrames={dur}
            >
              <div
                style={{
                  position: "absolute",
                  bottom: "30%",
                  left: 40,
                  right: 40,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  opacity: hookTextOpacity * interpolate(
                    frame,
                    [startFrame + dur - 10, startFrame + dur],
                    [1, 0],
                    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                  ),
                  transform: `scale(${hookTextScale})`,
                }}
              >
                <div
                  style={{
                    backgroundColor: "rgba(0, 0, 0, 0.65)",
                    borderRadius: 16,
                    padding: "18px 36px",
                  }}
                >
                  <span
                    style={{
                      color: "white",
                      fontSize: 56,
                      fontWeight: 900,
                      fontFamily: "Arial, Helvetica, sans-serif",
                      lineHeight: 1.2,
                      letterSpacing: 2,
                      textTransform: "uppercase",
                      textAlign: "center",
                      textShadow,
                      display: "block",
                      whiteSpace: "pre-line",
                    }}
                  >
                    {sub.text}
                  </span>
                </div>
              </div>
            </Sequence>
          );
        }

        // Special handling for last subtitle (CTA with subscribe)
        if (i === subtitles.length - 1) {
          return (
            <Sequence key={i} from={startFrame} durationInFrames={dur}>
              <SubtitleCard
                text={sub.text}
                frame={frame}
                fps={fps}
                localFrame={Math.max(0, frame - startFrame)}
                durationFrames={dur}
              />
              {/* Subscribe button */}
              <div
                style={{
                  position: "absolute",
                  bottom: "18%",
                  left: 0,
                  right: 0,
                  display: "flex",
                  justifyContent: "center",
                  opacity: interpolate(
                    Math.max(0, frame - startFrame),
                    [0, 15],
                    [0, 1],
                    { extrapolateRight: "clamp" }
                  ),
                }}
              >
                <div
                  style={{
                    backgroundColor: "#ff0000",
                    borderRadius: 14,
                    padding: "16px 60px",
                    transform: `scale(${ctaBadgePulse})`,
                    boxShadow: `0 4px 20px rgba(255,0,0,${0.4 + ctaGlow * 0.4})`,
                  }}
                >
                  <span
                    style={{
                      color: "white",
                      fontSize: 30,
                      fontWeight: "bold",
                      fontFamily: "Arial, Helvetica, sans-serif",
                      letterSpacing: 3,
                      textShadow: "0 1px 4px rgba(0,0,0,0.5)",
                    }}
                  >
                    SUBSCRIBE
                  </span>
                </div>
              </div>
            </Sequence>
          );
        }

        // Regular subtitle cards
        return (
          <Sequence key={i} from={startFrame} durationInFrames={dur}>
            <SubtitleCard
              text={sub.text}
              frame={frame}
              fps={fps}
              localFrame={Math.max(0, frame - startFrame)}
              durationFrames={dur}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
