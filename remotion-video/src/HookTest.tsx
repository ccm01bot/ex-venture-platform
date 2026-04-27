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

// Subtitle card with pill background, blue accent border, spring entrance
const SubtitleCard: React.FC<{
  text: string;
  frame: number;
  fps: number;
  localFrame: number;
  durationFrames: number;
}> = ({ text, fps, localFrame, durationFrames }) => {
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });
  const translateY = interpolate(entrance, [0, 1], [80, 0]);
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
        top: "65%",
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
          backgroundColor: "rgba(0, 0, 0, 0.72)",
          borderRadius: 16,
          padding: "18px 36px",
          backdropFilter: "blur(8px)",
          borderLeft: "4px solid #3388ff",
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

export const HookTest: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const totalFrames = 1200;

  const videoSrc = staticFile("source_clip.mp4");

  // ===== PATTERN INTERRUPT: RED FLASH (frames 0-2) =====
  const redFlashOpacity = interpolate(frame, [0, 2, 4], [1, 1, 0], {
    extrapolateRight: "clamp",
  });

  // ===== BREAKING TEXT (frames 2-15): scale 2.0 -> 1.0 crash =====
  const breakingScale = interpolate(frame, [2, 12], [2.0, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const breakingOpacity = interpolate(frame, [2, 4, 13, 15], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ===== ZOOM PULSES at text transitions (4s, 12s, 20s, 30s) =====
  const pulseFrames = [4 * fps, 12 * fps, 20 * fps, 30 * fps];
  let zoomPulse = 1.0;
  for (const pf of pulseFrames) {
    if (frame >= pf && frame <= pf + 9) {
      // 0.3s = 9 frames at 30fps
      const localF = frame - pf;
      zoomPulse = interpolate(localF, [0, 4, 9], [1.0, 1.05, 1.0], {
        extrapolateRight: "clamp",
      });
    }
  }

  // ===== KEN BURNS: slow continuous zoom =====
  const kenBurns = interpolate(frame, [0, totalFrames], [1.0, 1.1], {
    extrapolateRight: "clamp",
  });

  // ===== HOOK ZOOM (frames 0-50): dramatic opening zoom =====
  const hookZoom = interpolate(frame, [0, 50], [1.0, 1.15], {
    extrapolateRight: "clamp",
  });
  const videoScale =
    frame <= 50
      ? hookZoom * zoomPulse
      : interpolate(frame, [50, 80], [1.15, kenBurns], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }) * zoomPulse;

  // ===== SEAMLESS LOOP: fade to red in last 1s (frames 1170-1200) =====
  const loopFadeToRed = interpolate(frame, [1170, 1200], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Video playback: freeze on first frame for 15 frames, then play
  const videoStartFrom = frame <= 15 ? 0 : frame - 15;

  // AI NEWS badge pulse
  const newsBadgePulse = interpolate(frame % 90, [0, 20, 40], [1, 1.05, 1], {
    extrapolateRight: "clamp",
  });

  // CTA subscribe animation
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

  // Subtitle definitions
  const subtitles: { text: string; startSec: number; endSec: number }[] = [
    { text: "ANTHROPIC\nJUST KILLED\nDESIGN", startSec: 0.5, endSec: 4 },
    { text: "ONE PROMPT\nCREATES FULL\nDASHBOARDS", startSec: 4, endSec: 12 },
    { text: "CHARTS. TABLES.\nLIVE DATA.\nALL AI.", startSec: 12, endSec: 20 },
    { text: "CLAUDE DESIGN\nCHANGES\nEVERYTHING", startSec: 20, endSec: 30 },
    { text: "WOULD YOU\nUSE THIS?", startSec: 30, endSec: 37 },
    { text: "FOLLOW\n@EXAI", startSec: 37, endSec: 40 },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Background video */}
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
            transform: `scale(${videoScale})`,
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

      {/* ===== PATTERN INTERRUPT: RED FLASH ===== */}
      {frame < 5 && (
        <AbsoluteFill
          style={{
            backgroundColor: "#ff0000",
            opacity: redFlashOpacity,
            zIndex: 10,
          }}
        />
      )}

      {/* ===== BREAKING TEXT (frames 2-15) ===== */}
      {frame >= 2 && frame <= 15 && (
        <AbsoluteFill
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 11,
            opacity: breakingOpacity,
            transform: `scale(${breakingScale})`,
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: 120,
              fontWeight: 900,
              fontFamily: "Arial, Helvetica, sans-serif",
              letterSpacing: 8,
              textShadow:
                "0 0 60px rgba(255,0,0,0.9), 0 0 120px rgba(255,0,0,0.6), 0 4px 20px rgba(0,0,0,0.9)",
            }}
          >
            BREAKING
          </span>
        </AbsoluteFill>
      )}

      {/* ===== SUBTITLE OVERLAYS ===== */}
      {subtitles.map((sub, i) => {
        const startFrame = Math.round(sub.startSec * fps);
        const endFrame = Math.round(sub.endSec * fps);
        const dur = endFrame - startFrame;

        // First subtitle: hook text with spring entrance from below
        if (i === 0) {
          return (
            <Sequence key={i} from={startFrame} durationInFrames={dur}>
              {(() => {
                const localFrame = Math.max(0, frame - startFrame);
                const entrance = spring({
                  frame: localFrame,
                  fps,
                  config: { damping: 12, stiffness: 80 },
                });
                const translateY = interpolate(entrance, [0, 1], [120, 0]);
                const opacity = interpolate(entrance, [0, 1], [0, 1]);
                const fadeOut = interpolate(
                  localFrame,
                  [dur - 8, dur],
                  [1, 0],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                );
                return (
                  <div
                    style={{
                      position: "absolute",
                      top: "65%",
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
                        backgroundColor: "rgba(0, 0, 0, 0.72)",
                        borderRadius: 16,
                        padding: "18px 36px",
                        backdropFilter: "blur(8px)",
                        borderLeft: "4px solid #3388ff",
                      }}
                    >
                      <span
                        style={{
                          color: "white",
                          fontSize: 64,
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
                );
              })()}
            </Sequence>
          );
        }

        // Engagement hook at 30s: "WOULD YOU USE THIS?" + "YES / NO"
        if (i === 4) {
          return (
            <Sequence key={i} from={startFrame} durationInFrames={dur}>
              {(() => {
                const localFrame = Math.max(0, frame - startFrame);
                const entrance = spring({
                  frame: localFrame,
                  fps,
                  config: { damping: 14, stiffness: 100 },
                });
                const translateY = interpolate(entrance, [0, 1], [80, 0]);
                const opacity = interpolate(entrance, [0, 1], [0, 1]);
                const fadeOut = interpolate(
                  localFrame,
                  [dur - 8, dur],
                  [1, 0],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                );

                // Pulsing for the YES/NO text
                const commentPulse = interpolate(
                  localFrame % 30,
                  [0, 15, 30],
                  [1, 1.08, 1],
                  { extrapolateRight: "clamp" }
                );

                return (
                  <div
                    style={{
                      position: "absolute",
                      top: "55%",
                      left: 40,
                      right: 40,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      opacity: opacity * fadeOut,
                      transform: `translateY(${translateY}px)`,
                      gap: 24,
                    }}
                  >
                    {/* Main question */}
                    <div
                      style={{
                        backgroundColor: "rgba(0, 0, 0, 0.72)",
                        borderRadius: 16,
                        padding: "18px 36px",
                        borderLeft: "4px solid #3388ff",
                      }}
                    >
                      <span
                        style={{
                          color: "white",
                          fontSize: 60,
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
                    {/* Comment driver */}
                    <div
                      style={{
                        transform: `scale(${commentPulse})`,
                      }}
                    >
                      <span
                        style={{
                          color: "#ffcc00",
                          fontSize: 42,
                          fontWeight: 800,
                          fontFamily: "Arial, Helvetica, sans-serif",
                          letterSpacing: 3,
                          textShadow:
                            "0 2px 10px rgba(0,0,0,0.9), 0 0 30px rgba(255,204,0,0.3)",
                        }}
                      >
                        {"YES \uD83D\uDC47 or NO \uD83D\uDC47"}
                      </span>
                    </div>
                  </div>
                );
              })()}
            </Sequence>
          );
        }

        // Last subtitle: CTA with subscribe
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

      {/* ===== SEAMLESS LOOP: fade to red in last 1s ===== */}
      {frame >= 1170 && (
        <AbsoluteFill
          style={{
            backgroundColor: "#ff0000",
            opacity: loopFadeToRed,
            zIndex: 20,
          }}
        />
      )}
    </AbsoluteFill>
  );
};
