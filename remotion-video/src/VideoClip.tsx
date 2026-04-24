import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  useVideoConfig,
  Sequence,
  interpolate,
  useCurrentFrame,
  staticFile,
} from "remotion";

export const VideoClip: React.FC<{
  src: string;
  startFrom: number;
  duration: number;
  title?: string;
}> = ({ src, startFrom, title }) => {
  const { fps, width, height } = useVideoConfig();
  const frame = useCurrentFrame();

  // Use staticFile if src starts with "public/"
  const videoSrc = src.startsWith("http") ? src : staticFile(src.replace("public/", ""));

  // Slow zoom for engagement
  const scale = interpolate(frame, [0, fps * 15], [1, 1.06], {
    extrapolateRight: "clamp",
  });

  // Title fade in then stay
  const titleOpacity = interpolate(frame, [0, 20, fps * 4, fps * 4 + 20], [0, 1, 1, 0], {
    extrapolateRight: "clamp",
  });

  // Subscribe badge pulse
  const badgeScale = interpolate(
    frame % 60,
    [0, 15, 30],
    [1, 1.1, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Video fills full 9:16 */}
      <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
        <OffthreadVideo
          src={videoSrc}
          startFrom={startFrom * fps}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
          }}
        />
      </div>

      {/* Top gradient for readability */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 150,
          background: "linear-gradient(to bottom, rgba(0,0,0,0.6), transparent)",
        }}
      />

      {/* Bottom gradient */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 300,
          background: "linear-gradient(to top, rgba(0,0,0,0.7), transparent)",
        }}
      />

      {/* Title overlay with animated bar */}
      {title && (
        <div
          style={{
            position: "absolute",
            bottom: 200,
            left: 30,
            right: 30,
            opacity: titleOpacity,
          }}
        >
          {/* Blue accent line */}
          <div
            style={{
              width: interpolate(frame, [0, 20], [0, 60], { extrapolateRight: "clamp" }),
              height: 4,
              backgroundColor: "#00aaff",
              marginBottom: 12,
              borderRadius: 2,
            }}
          />
          <span
            style={{
              color: "white",
              fontSize: 42,
              fontWeight: "bold",
              fontFamily: "Arial, Helvetica, sans-serif",
              lineHeight: 1.2,
              textShadow: "0 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            {title}
          </span>
        </div>
      )}

      {/* EXAI GLOBAL badge */}
      <div
        style={{
          position: "absolute",
          top: 50,
          left: 30,
        }}
      >
        <span
          style={{
            color: "#00aaff",
            fontSize: 24,
            fontWeight: "bold",
            fontFamily: "Arial, Helvetica, sans-serif",
            textShadow: "0 1px 4px rgba(0,0,0,0.8)",
            letterSpacing: 2,
          }}
        >
          EXAI GLOBAL
        </span>
      </div>

      {/* Subscribe button */}
      <Sequence from={fps * 3}>
        <div
          style={{
            position: "absolute",
            bottom: 100,
            left: 30,
            right: 30,
            display: "flex",
            justifyContent: "center",
            opacity: interpolate(
              frame - fps * 3,
              [0, 15],
              [0, 1],
              { extrapolateRight: "clamp" }
            ),
          }}
        >
          <div
            style={{
              backgroundColor: "#ff0000",
              borderRadius: 8,
              padding: "10px 30px",
              transform: `scale(${badgeScale})`,
            }}
          >
            <span
              style={{
                color: "white",
                fontSize: 22,
                fontWeight: "bold",
                fontFamily: "Arial, Helvetica, sans-serif",
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
