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

// Reusable animated text card
const AnimatedCard: React.FC<{
  text: string;
  fps: number;
  localFrame: number;
  durationFrames: number;
  fontSize?: number;
  color?: string;
  bottom?: string;
}> = ({ text, fps, localFrame, durationFrames, fontSize = 56, color = "white", bottom = "30%" }) => {
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 12, stiffness: 120 },
  });
  const translateY = interpolate(entrance, [0, 1], [80, 0]);
  const scale = interpolate(entrance, [0, 1], [0.8, 1]);
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
        bottom,
        left: 40,
        right: 40,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        opacity: opacity * fadeOut,
        transform: `translateY(${translateY}px) scale(${scale})`,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          borderRadius: 16,
          padding: "20px 36px",
          backdropFilter: "blur(10px)",
        }}
      >
        <span
          style={{
            color,
            fontSize,
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

export const EngagementShort: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const totalFrames = 1200; // 40s at 30fps

  const videoSrc = staticFile("source_clip.mp4");

  // === VIDEO SCALE: Ken Burns + Hook Zoom ===
  const hookZoom = interpolate(frame, [0, 50], [1.0, 1.18], {
    extrapolateRight: "clamp",
  });
  const kenBurns = interpolate(frame, [0, totalFrames], [1.0, 1.1], {
    extrapolateRight: "clamp",
  });
  const videoScale =
    frame <= 50
      ? hookZoom
      : interpolate(frame, [50, 90], [1.18, kenBurns], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

  // === FALSE ENDING: fade to black at 30-31s, snap back at 31s ===
  const falseEndStart = 30 * fps; // frame 900
  const falseEndBlack = 31 * fps; // frame 930
  const falseEndSnap = 31.5 * fps; // frame 945

  let masterOpacity = 1;
  if (frame >= falseEndStart && frame < falseEndBlack) {
    // Fade to black
    masterOpacity = interpolate(frame, [falseEndStart, falseEndBlack], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (frame >= falseEndBlack && frame < falseEndSnap) {
    // Stay black briefly then snap back
    masterOpacity = interpolate(frame, [falseEndBlack, falseEndSnap], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  // === LOOP TRICK: fade out at very end to match frame 1 composition ===
  const loopFade = interpolate(frame, [totalFrames - 20, totalFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // === HOOK TEXT (0-4s): controversy hook with shake ===
  const hookSpring = spring({
    frame,
    fps,
    config: { damping: 8, stiffness: 80 },
  });
  const hookScale = interpolate(hookSpring, [0, 1], [0, 1]);
  const hookShake = frame < 30 ? Math.sin(frame * 1.5) * 3 : 0;

  // AI NEWS badge pulse
  const badgePulse = interpolate(frame % 60, [0, 15, 30], [1, 1.08, 1], {
    extrapolateRight: "clamp",
  });

  // Video playback: freeze first 15 frames
  const videoStartFrom = frame <= 15 ? 0 : frame - 15;

  const textShadow =
    "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.5), -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000";

  // === CTA STACK (33-40s) animations ===
  const ctaStart = 33 * fps; // frame 990
  const ctaLocal = Math.max(0, frame - ctaStart);
  const ctaSubPulse = interpolate(ctaLocal % 30, [0, 10, 20, 30], [1, 1.15, 1, 1], {
    extrapolateRight: "clamp",
  });
  const ctaGlow = interpolate(ctaLocal % 50, [0, 25, 50], [0.3, 1, 0.3], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Main content layer with false-ending and loop-trick opacity */}
      <div style={{ width: "100%", height: "100%", opacity: masterOpacity * loopFade }}>
        {/* Background video */}
        <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
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
            height: 100,
            background: "linear-gradient(to bottom, rgba(0,0,0,0.75) 0%, transparent 100%)",
          }}
        />

        {/* Bottom gradient */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 250,
            background:
              "linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 50%, transparent 100%)",
          }}
        />

        {/* EXAI GLOBAL branding top-left */}
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
            transform: `scale(${badgePulse})`,
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

        {/* === SECTION 1: CONTROVERSY HOOK (0-4s, frames 0-120) === */}
        <Sequence from={0} durationInFrames={4 * fps}>
          <div
            style={{
              position: "absolute",
              bottom: "30%",
              left: 40,
              right: 40,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              opacity: interpolate(hookSpring, [0, 1], [0, 1]) *
                interpolate(frame, [4 * fps - 10, 4 * fps], [1, 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              transform: `scale(${hookScale}) translateX(${hookShake}px)`,
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(200, 0, 0, 0.75)",
                borderRadius: 16,
                padding: "24px 36px",
                border: "3px solid rgba(255, 80, 80, 0.6)",
              }}
            >
              <span
                style={{
                  color: "white",
                  fontSize: 52,
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
                {"DESIGNERS ARE\nPANICKING\nRIGHT NOW"}
              </span>
            </div>
          </div>
        </Sequence>

        {/* === SECTION 2: INFORMATION GAP (4-12s, frames 120-360) === */}
        {/* "Here's why..." teaser (4-7s) */}
        <Sequence from={4 * fps} durationInFrames={3 * fps}>
          <AnimatedCard
            text={"HERE'S WHY..."}
            fps={fps}
            localFrame={Math.max(0, frame - 4 * fps)}
            durationFrames={3 * fps}
            fontSize={64}
            color="#ffcc00"
          />
        </Sequence>
        {/* Demo context (7-12s) */}
        <Sequence from={7 * fps} durationInFrames={5 * fps}>
          <AnimatedCard
            text={"ONE PROMPT\nCREATES FULL\nDASHBOARDS"}
            fps={fps}
            localFrame={Math.max(0, frame - 7 * fps)}
            durationFrames={5 * fps}
          />
        </Sequence>

        {/* === SECTION 3: SHARE TRIGGER (12-20s, frames 360-600) === */}
        <Sequence from={12 * fps} durationInFrames={4 * fps}>
          <AnimatedCard
            text={"CHARTS. TABLES.\nLIVE DATA.\nALL AI."}
            fps={fps}
            localFrame={Math.max(0, frame - 12 * fps)}
            durationFrames={4 * fps}
          />
        </Sequence>
        {/* Tag overlay (16-20s) */}
        <Sequence from={16 * fps} durationInFrames={4 * fps}>
          <div
            style={{
              position: "absolute",
              bottom: "20%",
              left: 40,
              right: 40,
              display: "flex",
              justifyContent: "center",
              opacity: interpolate(
                spring({ frame: Math.max(0, frame - 16 * fps), fps, config: { damping: 14, stiffness: 100 } }),
                [0, 1], [0, 1]
              ) * interpolate(frame, [20 * fps - 8, 20 * fps], [1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(0, 150, 255, 0.8)",
                borderRadius: 14,
                padding: "16px 32px",
                border: "2px solid rgba(100, 200, 255, 0.6)",
              }}
            >
              <span
                style={{
                  color: "white",
                  fontSize: 38,
                  fontWeight: 800,
                  fontFamily: "Arial, Helvetica, sans-serif",
                  textAlign: "center",
                  textShadow: "0 2px 8px rgba(0,0,0,0.7)",
                  display: "block",
                }}
              >
                TAG A DESIGNER WHO{"\n"}NEEDS TO SEE THIS 👇
              </span>
            </div>
          </div>
        </Sequence>

        {/* === SECTION 4: POLL/QUESTION (20-30s, frames 600-900) === */}
        <Sequence from={20 * fps} durationInFrames={5 * fps}>
          <AnimatedCard
            text={"CLAUDE DESIGN\nCHANGES\nEVERYTHING"}
            fps={fps}
            localFrame={Math.max(0, frame - 20 * fps)}
            durationFrames={5 * fps}
          />
        </Sequence>
        {/* Comment poll (25-30s) */}
        <Sequence from={25 * fps} durationInFrames={5 * fps}>
          <div
            style={{
              position: "absolute",
              bottom: "25%",
              left: 40,
              right: 40,
              display: "flex",
              justifyContent: "center",
              flexDirection: "column",
              alignItems: "center",
              gap: 16,
              opacity: interpolate(
                spring({ frame: Math.max(0, frame - 25 * fps), fps, config: { damping: 12, stiffness: 100 } }),
                [0, 1], [0, 1]
              ) * interpolate(frame, [30 * fps - 8, 30 * fps], [1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `scale(${interpolate(
                spring({ frame: Math.max(0, frame - 25 * fps), fps, config: { damping: 12, stiffness: 100 } }),
                [0, 1], [0.7, 1]
              )})`,
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                borderRadius: 20,
                padding: "28px 44px",
                border: "3px solid #ffcc00",
                boxShadow: "0 0 30px rgba(255, 204, 0, 0.3)",
              }}
            >
              <span
                style={{
                  color: "#ffcc00",
                  fontSize: 46,
                  fontWeight: 900,
                  fontFamily: "Arial, Helvetica, sans-serif",
                  textAlign: "center",
                  textShadow: "0 2px 10px rgba(0,0,0,0.9)",
                  display: "block",
                  whiteSpace: "pre-line",
                  lineHeight: 1.3,
                }}
              >
                {"RATE THIS AI\n1-10 IN\nCOMMENTS 👇"}
              </span>
            </div>
          </div>
        </Sequence>

        {/* === SECTION 5: FALSE ENDING handled by masterOpacity above === */}
        {/* "WAIT" snap-back text (31-33s) */}
        <Sequence from={falseEndSnap} durationInFrames={Math.round(2.5 * fps)}>
          <div
            style={{
              position: "absolute",
              bottom: "35%",
              left: 40,
              right: 40,
              display: "flex",
              justifyContent: "center",
              opacity: interpolate(
                spring({ frame: Math.max(0, frame - falseEndSnap), fps, config: { damping: 8, stiffness: 200 } }),
                [0, 1], [0, 1]
              ) * interpolate(frame, [ctaStart - 8, ctaStart], [1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `scale(${interpolate(
                spring({ frame: Math.max(0, frame - falseEndSnap), fps, config: { damping: 8, stiffness: 200 } }),
                [0, 1], [1.5, 1]
              )})`,
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(230, 0, 0, 0.85)",
                borderRadius: 16,
                padding: "24px 48px",
                border: "3px solid rgba(255, 100, 100, 0.7)",
              }}
            >
              <span
                style={{
                  color: "white",
                  fontSize: 56,
                  fontWeight: 900,
                  fontFamily: "Arial, Helvetica, sans-serif",
                  textAlign: "center",
                  textShadow,
                  display: "block",
                  whiteSpace: "pre-line",
                }}
              >
                {"WAIT —\nTHERE'S MORE"}
              </span>
            </div>
          </div>
        </Sequence>

        {/* === SECTION 6: CTA STACK (33-40s, frames 990-1200) === */}
        <Sequence from={ctaStart} durationInFrames={totalFrames - ctaStart}>
          {/* FOLLOW @EXAI */}
          <div
            style={{
              position: "absolute",
              bottom: "38%",
              left: 40,
              right: 40,
              display: "flex",
              justifyContent: "center",
              opacity: interpolate(
                spring({ frame: ctaLocal, fps, config: { damping: 14, stiffness: 100 } }),
                [0, 1], [0, 1]
              ),
              transform: `translateY(${interpolate(
                spring({ frame: ctaLocal, fps, config: { damping: 14, stiffness: 100 } }),
                [0, 1], [40, 0]
              )}px)`,
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(0, 0, 0, 0.75)",
                borderRadius: 16,
                padding: "18px 44px",
              }}
            >
              <span
                style={{
                  color: "#00ccff",
                  fontSize: 52,
                  fontWeight: 900,
                  fontFamily: "Arial, Helvetica, sans-serif",
                  letterSpacing: 4,
                  textShadow: "0 0 20px rgba(0,204,255,0.5)",
                  display: "block",
                  textAlign: "center",
                }}
              >
                FOLLOW @EXAI
              </span>
            </div>
          </div>

          {/* SUBSCRIBE button with pulse */}
          <div
            style={{
              position: "absolute",
              bottom: "26%",
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
              opacity: interpolate(
                spring({ frame: Math.max(0, ctaLocal - 10), fps, config: { damping: 14, stiffness: 100 } }),
                [0, 1], [0, 1]
              ),
            }}
          >
            <div
              style={{
                backgroundColor: "#ff0000",
                borderRadius: 14,
                padding: "18px 70px",
                transform: `scale(${ctaSubPulse})`,
                boxShadow: `0 4px 30px rgba(255,0,0,${0.4 + ctaGlow * 0.5}), 0 0 60px rgba(255,0,0,${ctaGlow * 0.3})`,
              }}
            >
              <span
                style={{
                  color: "white",
                  fontSize: 34,
                  fontWeight: "bold",
                  fontFamily: "Arial, Helvetica, sans-serif",
                  letterSpacing: 4,
                  textShadow: "0 1px 4px rgba(0,0,0,0.5)",
                }}
              >
                SUBSCRIBE
              </span>
            </div>
          </div>

          {/* "New AI news EVERY DAY" */}
          <div
            style={{
              position: "absolute",
              bottom: "18%",
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
              opacity: interpolate(
                spring({ frame: Math.max(0, ctaLocal - 20), fps, config: { damping: 14, stiffness: 100 } }),
                [0, 1], [0, 1]
              ),
              transform: `translateY(${interpolate(
                spring({ frame: Math.max(0, ctaLocal - 20), fps, config: { damping: 14, stiffness: 100 } }),
                [0, 1], [30, 0]
              )}px)`,
            }}
          >
            <span
              style={{
                color: "rgba(255,255,255,0.9)",
                fontSize: 28,
                fontWeight: 700,
                fontFamily: "Arial, Helvetica, sans-serif",
                letterSpacing: 2,
                textShadow: "0 2px 8px rgba(0,0,0,0.8)",
              }}
            >
              NEW AI NEWS EVERY DAY
            </span>
          </div>
        </Sequence>
      </div>

      {/* === LOOP TRICK: Re-show hook composition at very end === */}
      {frame >= totalFrames - 20 && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            opacity: interpolate(frame, [totalFrames - 20, totalFrames], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
            backgroundColor: "black",
          }}
        >
          {/* Replicate frame-1 composition for seamless loop */}
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
            <div style={{ width: 4, height: 28, backgroundColor: "#00ccff", borderRadius: 2 }} />
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
          <div style={{ position: "absolute", top: 48, right: 30 }}>
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
          {/* Hook text appearing (matching frame 1) */}
          <div
            style={{
              position: "absolute",
              bottom: "30%",
              left: 40,
              right: 40,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              opacity: interpolate(frame, [totalFrames - 15, totalFrames - 5], [0, 0.6], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: "scale(0.4)",
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(200, 0, 0, 0.75)",
                borderRadius: 16,
                padding: "24px 36px",
                border: "3px solid rgba(255, 80, 80, 0.6)",
              }}
            >
              <span
                style={{
                  color: "white",
                  fontSize: 52,
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
                {"DESIGNERS ARE\nPANICKING\nRIGHT NOW"}
              </span>
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
