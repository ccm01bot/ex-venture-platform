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

export const DemoShort: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const videoSrc = staticFile("source_clip.mp4");

  // Slow zoom for engagement
  const scale = interpolate(frame, [0, fps * 40], [1, 1.08], {
    extrapolateRight: "clamp",
  });

  // --- Hook text (0-5s): "ANTHROPIC JUST KILLED DESIGN" ---
  const hookIn = spring({ frame, fps, config: { damping: 12, stiffness: 80 } });
  const hookScale = interpolate(hookIn, [0, 1], [0.3, 1]);
  const hookOpacity = interpolate(hookIn, [0, 1], [0, 1]);
  const hookOut = interpolate(frame, [fps * 4, fps * 5], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Feature 1 (5-15s): slide from left ---
  const feat1Frame = Math.max(0, frame - fps * 5);
  const feat1In = interpolate(feat1Frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const feat1X = interpolate(feat1In, [0, 1], [-600, 0]);
  const feat1Out = interpolate(frame, [fps * 13, fps * 15], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Feature 2 (15-25s): slide from right ---
  const feat2Frame = Math.max(0, frame - fps * 15);
  const feat2In = interpolate(feat2Frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const feat2X = interpolate(feat2In, [0, 1], [600, 0]);
  const feat2Out = interpolate(frame, [fps * 23, fps * 25], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Feature 3 (25-35s): fade in centered ---
  const feat3Frame = Math.max(0, frame - fps * 25);
  const feat3Opacity = interpolate(feat3Frame, [0, 25], [0, 1], { extrapolateRight: "clamp" });
  const feat3Out = interpolate(frame, [fps * 33, fps * 35], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- CTA (35-40s): subscribe button ---
  const ctaFrame = Math.max(0, frame - fps * 35);
  const ctaSpring = spring({ frame: ctaFrame, fps, config: { damping: 10, stiffness: 100 } });
  const ctaScale = interpolate(ctaSpring, [0, 1], [0.5, 1]);
  const ctaOpacity = interpolate(ctaSpring, [0, 1], [0, 1]);

  // Badge pulse for CTA
  const badgePulse = interpolate(
    ctaFrame % 45,
    [0, 15, 30, 45],
    [1, 1.08, 1, 1],
    { extrapolateRight: "clamp" }
  );

  // AI NEWS badge pulse
  const newsBadgePulse = interpolate(
    frame % 90,
    [0, 20, 40],
    [1, 1.05, 1],
    { extrapolateRight: "clamp" }
  );

  const textShadow = "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.5)";

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Background video scaled to fill 1080x1920 */}
      <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
        <OffthreadVideo
          src={videoSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
          }}
        />
      </div>

      {/* Bottom gradient (always visible) */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 500,
          background:
            "linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 50%, transparent 100%)",
        }}
      />

      {/* Top gradient */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 200,
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 100%)",
        }}
      />

      {/* EXAI GLOBAL watermark top-left (always visible) */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 30,
        }}
      >
        <span
          style={{
            color: "#00aaff",
            fontSize: 22,
            fontWeight: "bold",
            fontFamily: "Arial, Helvetica, sans-serif",
            textShadow: "0 1px 6px rgba(0,0,0,0.9)",
            letterSpacing: 3,
          }}
        >
          EXAI GLOBAL
        </span>
      </div>

      {/* AI NEWS badge top-right (always visible) */}
      <div
        style={{
          position: "absolute",
          top: 50,
          right: 30,
          transform: `scale(${newsBadgePulse})`,
        }}
      >
        <div
          style={{
            backgroundColor: "#e60000",
            borderRadius: 6,
            padding: "8px 18px",
            boxShadow: "0 2px 10px rgba(230,0,0,0.5)",
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: 20,
              fontWeight: "bold",
              fontFamily: "Arial, Helvetica, sans-serif",
              letterSpacing: 2,
            }}
          >
            AI NEWS
          </span>
        </div>
      </div>

      {/* Hook text (0-5s): ANTHROPIC JUST KILLED DESIGN */}
      <Sequence from={0} durationInFrames={fps * 5}>
        <div
          style={{
            position: "absolute",
            bottom: 350,
            left: 40,
            right: 40,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            opacity: hookOpacity * hookOut,
            transform: `scale(${hookScale})`,
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                width: interpolate(hookIn, [0, 1], [0, 120]),
                height: 5,
                backgroundColor: "#e60000",
                margin: "0 auto 16px auto",
                borderRadius: 3,
              }}
            />
            <span
              style={{
                color: "white",
                fontSize: 56,
                fontWeight: 900,
                fontFamily: "Arial, Helvetica, sans-serif",
                lineHeight: 1.15,
                textShadow,
                letterSpacing: 1,
              }}
            >
              ANTHROPIC{"\n"}JUST KILLED{"\n"}DESIGN
            </span>
          </div>
        </div>
      </Sequence>

      {/* Feature 1 (5-15s): One prompt -> Full dashboard */}
      <Sequence from={fps * 5} durationInFrames={fps * 10}>
        <div
          style={{
            position: "absolute",
            bottom: 300,
            left: 40,
            right: 40,
            opacity: feat1Out,
            transform: `translateX(${feat1X}px)`,
          }}
        >
          <div
            style={{
              width: 80,
              height: 4,
              backgroundColor: "#00aaff",
              marginBottom: 14,
              borderRadius: 2,
            }}
          />
          <span
            style={{
              color: "white",
              fontSize: 48,
              fontWeight: 800,
              fontFamily: "Arial, Helvetica, sans-serif",
              lineHeight: 1.2,
              textShadow,
            }}
          >
            One prompt{"\n"}&rarr; Full dashboard
          </span>
        </div>
      </Sequence>

      {/* Feature 2 (15-25s): Charts. Tables. Live data. */}
      <Sequence from={fps * 15} durationInFrames={fps * 10}>
        <div
          style={{
            position: "absolute",
            bottom: 300,
            left: 40,
            right: 40,
            opacity: feat2Out,
            transform: `translateX(${feat2X}px)`,
            textAlign: "right",
          }}
        >
          <div
            style={{
              width: 80,
              height: 4,
              backgroundColor: "#ff6600",
              marginBottom: 14,
              marginLeft: "auto",
              borderRadius: 2,
            }}
          />
          <span
            style={{
              color: "white",
              fontSize: 48,
              fontWeight: 800,
              fontFamily: "Arial, Helvetica, sans-serif",
              lineHeight: 1.2,
              textShadow,
            }}
          >
            Charts. Tables.{"\n"}Live data.
          </span>
        </div>
      </Sequence>

      {/* Feature 3 (25-35s): Claude Design is here. */}
      <Sequence from={fps * 25} durationInFrames={fps * 10}>
        <div
          style={{
            position: "absolute",
            bottom: 300,
            left: 40,
            right: 40,
            opacity: feat3Opacity * feat3Out,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              width: interpolate(feat3Frame, [0, 30], [0, 100], {
                extrapolateRight: "clamp",
              }),
              height: 4,
              backgroundColor: "#aa44ff",
              marginBottom: 14,
              borderRadius: 2,
            }}
          />
          <span
            style={{
              color: "white",
              fontSize: 52,
              fontWeight: 900,
              fontFamily: "Arial, Helvetica, sans-serif",
              lineHeight: 1.2,
              textShadow,
              textAlign: "center",
            }}
          >
            Claude Design{"\n"}is here.
          </span>
        </div>
      </Sequence>

      {/* CTA (35-40s): Follow @EXAI */}
      <Sequence from={fps * 35} durationInFrames={fps * 5}>
        <div
          style={{
            position: "absolute",
            bottom: 280,
            left: 40,
            right: 40,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 20,
            opacity: ctaOpacity,
            transform: `scale(${ctaScale})`,
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: 46,
              fontWeight: 900,
              fontFamily: "Arial, Helvetica, sans-serif",
              textShadow,
              textAlign: "center",
            }}
          >
            Follow @EXAI
          </span>
          <div
            style={{
              backgroundColor: "#ff0000",
              borderRadius: 12,
              padding: "14px 50px",
              transform: `scale(${badgePulse})`,
              boxShadow: "0 4px 20px rgba(255,0,0,0.4)",
            }}
          >
            <span
              style={{
                color: "white",
                fontSize: 28,
                fontWeight: "bold",
                fontFamily: "Arial, Helvetica, sans-serif",
                letterSpacing: 2,
              }}
            >
              SUBSCRIBE
            </span>
          </div>
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
