import React from "react";
import {
  AbsoluteFill,
  useVideoConfig,
  Sequence,
  interpolate,
  useCurrentFrame,
  spring,
} from "remotion";

// --- Sub-components ---

const GridBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slow drift for the grid
  const offsetY = interpolate(frame, [0, fps * 60], [0, -200], {
    extrapolateRight: "extend",
  });
  const offsetX = interpolate(frame, [0, fps * 60], [0, -50], {
    extrapolateRight: "extend",
  });

  // Subtle pulse
  const pulse = interpolate(frame % (fps * 4), [0, fps * 2, fps * 4], [0.03, 0.07, 0.03]);

  const gridSize = 60;
  const lines: React.ReactNode[] = [];

  // Horizontal lines
  for (let y = -200; y < 2200; y += gridSize) {
    lines.push(
      <line
        key={`h${y}`}
        x1={0}
        y1={y + (offsetY % gridSize)}
        x2={1080}
        y2={y + (offsetY % gridSize)}
        stroke={`rgba(0, 170, 255, ${pulse})`}
        strokeWidth={1}
      />
    );
  }
  // Vertical lines
  for (let x = -200; x < 1300; x += gridSize) {
    lines.push(
      <line
        key={`v${x}`}
        x1={x + (offsetX % gridSize)}
        y1={0}
        x2={x + (offsetX % gridSize)}
        y2={1920}
        stroke={`rgba(0, 170, 255, ${pulse})`}
        strokeWidth={1}
      />
    );
  }

  return (
    <svg
      width={1080}
      height={1920}
      style={{ position: "absolute", top: 0, left: 0 }}
    >
      {lines}
    </svg>
  );
};

const Particles: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Deterministic particles
  const particles = React.useMemo(() => {
    const arr: { x: number; y: number; speed: number; size: number; delay: number }[] = [];
    for (let i = 0; i < 30; i++) {
      const seed = (i * 7919 + 1) % 1000;
      arr.push({
        x: (seed * 1.08) % 1080,
        y: ((seed * 3.7) % 1920),
        speed: 0.3 + (seed % 5) * 0.15,
        size: 2 + (seed % 4),
        delay: (seed % 90),
      });
    }
    return arr;
  }, []);

  return (
    <svg
      width={1080}
      height={1920}
      style={{ position: "absolute", top: 0, left: 0 }}
    >
      {particles.map((p, i) => {
        const activeFrame = frame - p.delay;
        if (activeFrame < 0) return null;
        const yPos = (p.y - activeFrame * p.speed * 2) % 1920;
        const adjustedY = yPos < 0 ? yPos + 1920 : yPos;
        const opacity = interpolate(
          activeFrame % (fps * 8),
          [0, fps * 2, fps * 6, fps * 8],
          [0, 0.6, 0.6, 0],
          { extrapolateRight: "clamp" }
        );
        return (
          <circle
            key={i}
            cx={p.x}
            cy={adjustedY}
            r={p.size}
            fill={`rgba(0, 170, 255, ${opacity})`}
          />
        );
      })}
    </svg>
  );
};

const AnimatedLine: React.FC<{
  text: string;
  startFrame: number;
  durationFrames: number;
  fontSize?: number;
}> = ({ text, startFrame, durationFrames, fontSize = 64 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relFrame = frame - startFrame;

  if (relFrame < 0 || relFrame > durationFrames) return null;

  // Fade + slide in
  const enter = spring({
    frame: relFrame,
    fps,
    config: { damping: 18, stiffness: 80, mass: 0.8 },
  });

  // Fade out at end
  const fadeOut = interpolate(
    relFrame,
    [durationFrames - 15, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const translateY = interpolate(enter, [0, 1], [60, 0]);
  const opacity = enter * fadeOut;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 70px",
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          color: "white",
          fontSize,
          fontWeight: 700,
          fontFamily: "'Arial Black', 'Helvetica Neue', Arial, sans-serif",
          lineHeight: 1.25,
          textAlign: "center",
          textShadow: "0 4px 20px rgba(0,0,0,0.7), 0 1px 4px rgba(0,0,0,0.9)",
          wordBreak: "break-word",
        }}
      >
        {text}
      </div>
    </div>
  );
};

// --- Main Component ---

export const NewsShort: React.FC<{
  title: string;
  lines: string[];
  accentColor?: string;
}> = ({ title, lines, accentColor = "#00aaff" }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Timing: title card + lines evenly spaced, with subscribe at end
  const titleDuration = Math.round(fps * 3); // 3 seconds for title
  const subscribeDuration = Math.round(fps * 3);
  const contentFrames = durationInFrames - titleDuration - subscribeDuration;
  const perLine = Math.floor(contentFrames / Math.max(lines.length, 1));

  // Title animations
  const titleEnter = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 60, mass: 1 },
  });
  const titleFadeOut = interpolate(
    frame,
    [titleDuration - 20, titleDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const titleOpacity = titleEnter * titleFadeOut;
  const titleScale = interpolate(titleEnter, [0, 1], [0.7, 1]);

  // Subscribe button
  const subscribeStart = durationInFrames - subscribeDuration;
  const subscribeFrame = frame - subscribeStart;
  const subscribeEnter = subscribeFrame >= 0
    ? spring({ frame: subscribeFrame, fps, config: { damping: 12, stiffness: 100, mass: 0.6 } })
    : 0;
  const subscribePulse = subscribeFrame > 0
    ? interpolate(subscribeFrame % 50, [0, 15, 30, 50], [1, 1.08, 1, 1])
    : 1;

  // Background gradient shift
  const hueShift = interpolate(frame, [0, durationInFrames], [0, 30]);

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg,
          hsl(${220 + hueShift}, 60%, 8%) 0%,
          hsl(${230 + hueShift}, 50%, 14%) 40%,
          hsl(${210 + hueShift}, 55%, 10%) 100%)`,
      }}
    >
      {/* Animated grid */}
      <GridBackground />

      {/* Floating particles */}
      <Particles />

      {/* Accent glow */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "50%",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${accentColor}15 0%, transparent 70%)`,
          transform: "translate(-50%, -50%)",
          filter: "blur(40px)",
        }}
      />

      {/* Top bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 4,
          background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
          opacity: 0.8,
        }}
      />

      {/* EXAI GLOBAL branding - top left */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 50,
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div
          style={{
            width: 8,
            height: 32,
            backgroundColor: accentColor,
            borderRadius: 4,
          }}
        />
        <span
          style={{
            color: accentColor,
            fontSize: 28,
            fontWeight: 900,
            fontFamily: "'Arial Black', Arial, sans-serif",
            letterSpacing: 4,
            textShadow: `0 0 20px ${accentColor}40`,
          }}
        >
          EXAI GLOBAL
        </span>
      </div>

      {/* AI NEWS badge - top right */}
      <div
        style={{
          position: "absolute",
          top: 60,
          right: 50,
          zIndex: 10,
        }}
      >
        <div
          style={{
            background: "#ff0000",
            borderRadius: 8,
            padding: "6px 20px",
            opacity: interpolate(frame, [5, 20], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
            boxShadow: "0 2px 12px rgba(255,0,0,0.5)",
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: 22,
              fontWeight: 900,
              fontFamily: "'Arial Black', Arial, sans-serif",
              letterSpacing: 3,
            }}
          >
            AI NEWS
          </span>
        </div>
      </div>

      {/* Title card */}
      <Sequence from={0} durationInFrames={titleDuration}>
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "200px 70px 200px 70px",
            opacity: titleOpacity,
            transform: `scale(${titleScale})`,
          }}
        >
          <div style={{ textAlign: "center" }}>
            {/* Decorative line above */}
            <div
              style={{
                width: interpolate(titleEnter, [0, 1], [0, 120]),
                height: 4,
                backgroundColor: accentColor,
                margin: "0 auto 30px auto",
                borderRadius: 2,
              }}
            />
            <div
              style={{
                color: "white",
                fontSize: 72,
                fontWeight: 900,
                fontFamily: "'Arial Black', 'Helvetica Neue', Arial, sans-serif",
                lineHeight: 1.15,
                textShadow: `0 4px 30px rgba(0,0,0,0.8), 0 0 60px ${accentColor}30`,
              }}
            >
              {title}
            </div>
            {/* Decorative line below */}
            <div
              style={{
                width: interpolate(titleEnter, [0, 1], [0, 120]),
                height: 4,
                backgroundColor: accentColor,
                margin: "30px auto 0 auto",
                borderRadius: 2,
              }}
            />
          </div>
        </div>
      </Sequence>

      {/* Content lines - each appears one at a time, centered */}
      {lines.map((line, i) => {
        const lineStart = titleDuration + i * perLine;
        // Auto-size: shorter text gets bigger font
        const charCount = line.length;
        let fontSize = 64;
        if (charCount > 120) fontSize = 48;
        else if (charCount > 80) fontSize = 54;
        else if (charCount > 50) fontSize = 60;
        else if (charCount < 30) fontSize = 76;

        return (
          <AnimatedLine
            key={i}
            text={line}
            startFrame={lineStart}
            durationFrames={perLine}
            fontSize={fontSize}
          />
        );
      })}

      {/* Subscribe button */}
      <Sequence from={subscribeStart}>
        <div
          style={{
            position: "absolute",
            bottom: 180,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: subscribeEnter,
            transform: `scale(${subscribeEnter * subscribePulse})`,
          }}
        >
          <div
            style={{
              backgroundColor: "#ff0000",
              borderRadius: 12,
              padding: "16px 50px",
              boxShadow: "0 4px 20px rgba(255,0,0,0.4)",
            }}
          >
            <span
              style={{
                color: "white",
                fontSize: 30,
                fontWeight: 900,
                fontFamily: "'Arial Black', Arial, sans-serif",
                letterSpacing: 2,
              }}
            >
              SUBSCRIBE
            </span>
          </div>
        </div>
        {/* Follow text */}
        <div
          style={{
            position: "absolute",
            bottom: 120,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: interpolate(
              subscribeFrame,
              [10, 25],
              [0, 0.7],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            ),
          }}
        >
          <span
            style={{
              color: "#aaa",
              fontSize: 20,
              fontFamily: "Arial, sans-serif",
              letterSpacing: 1,
            }}
          >
            @ExaiGlobal
          </span>
        </div>
      </Sequence>

      {/* Bottom bar accent */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 4,
          background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
          opacity: 0.6,
        }}
      />
    </AbsoluteFill>
  );
};
