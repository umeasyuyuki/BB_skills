import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS } from "../types";

type Props = {
  text: string;
  position?: "bottom" | "center";
};

export const Telop: React.FC<Props> = ({ text, position = "bottom" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in after 0.2s
  const opacity = interpolate(frame, [0.2 * fps, 0.6 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Slide up slightly
  const translateY = interpolate(frame, [0.2 * fps, 0.6 * fps], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Auto line break for long text (max 15 chars per line)
  const lines = splitTextToLines(text, 15);

  const positionStyle: React.CSSProperties =
    position === "center"
      ? { justifyContent: "center" }
      : { justifyContent: "flex-end", paddingBottom: 180 };

  return (
    <AbsoluteFill
      style={{
        ...positionStyle,
        alignItems: "center",
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          borderRadius: 12,
          padding: "16px 32px",
          marginLeft: 40,
          marginRight: 40,
          maxWidth: 1000,
        }}
      >
        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              color: "#FFFFFF",
              fontSize: 42,
              fontWeight: 700,
              fontFamily:
                '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
              textAlign: "center",
              lineHeight: 1.5,
              letterSpacing: 1,
            }}
          >
            {line}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

function splitTextToLines(text: string, maxChars: number): string[] {
  const lines: string[] = [];
  let remaining = text;

  while (remaining.length > maxChars) {
    // Try to break at punctuation or space
    let breakPoint = maxChars;
    for (let i = maxChars; i >= maxChars - 5 && i > 0; i--) {
      if ("、。！？ ".includes(remaining[i])) {
        breakPoint = i + 1;
        break;
      }
    }
    lines.push(remaining.slice(0, breakPoint));
    remaining = remaining.slice(breakPoint);
  }
  if (remaining.length > 0) {
    lines.push(remaining);
  }

  return lines;
}
