import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, SlideType } from "../types";

type Props = {
  style: "gradient" | "particles" | "geometric";
  slideType: SlideType;
  accentColor?: string;
};

export const DynamicBackground: React.FC<Props> = ({
  style,
  slideType,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const accent = accentColor || COLORS.accent;

  if (style === "gradient") {
    return <GradientBg frame={frame} fps={fps} accent={accent} slideType={slideType} />;
  }
  if (style === "geometric") {
    return <GeometricBg frame={frame} fps={fps} accent={accent} />;
  }
  return <GradientBg frame={frame} fps={fps} accent={accent} slideType={slideType} />;
};

const GradientBg: React.FC<{
  frame: number;
  fps: number;
  accent: string;
  slideType: SlideType;
}> = ({ frame, fps, accent, slideType }) => {
  // Slow rotation of gradient angle
  const angle = interpolate(frame, [0, 10 * fps], [135, 180], {
    extrapolateRight: "clamp",
  });

  // Subtle pulse for CTA slides
  const scale =
    slideType === "cta"
      ? interpolate(frame, [0, fps, 2 * fps], [1, 1.02, 1], {
          extrapolateRight: "clamp",
        })
      : 1;

  const bgColor =
    slideType === "hook"
      ? `linear-gradient(${angle}deg, ${accent}08, ${accent}15, #FFFFFF)`
      : slideType === "cta"
        ? `linear-gradient(${angle}deg, ${accent}12, #FFFFFF, ${accent}08)`
        : `linear-gradient(${angle}deg, #F8F9FA, #FFFFFF, #F8F9FA)`;

  return (
    <AbsoluteFill
      style={{
        background: bgColor,
        transform: `scale(${scale})`,
      }}
    />
  );
};

const GeometricBg: React.FC<{
  frame: number;
  fps: number;
  accent: string;
}> = ({ frame, fps, accent }) => {
  const y1 = interpolate(frame, [0, 8 * fps], [0, -40], {
    extrapolateRight: "clamp",
  });
  const y2 = interpolate(frame, [0, 8 * fps], [0, 30], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, fps], [0, 0.06], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      {/* Floating circles */}
      <div
        style={{
          position: "absolute",
          top: 200 + y1,
          right: -80,
          width: 300,
          height: 300,
          borderRadius: "50%",
          backgroundColor: accent,
          opacity,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 300 + y2,
          left: -60,
          width: 200,
          height: 200,
          borderRadius: "50%",
          backgroundColor: accent,
          opacity: opacity * 0.7,
        }}
      />
    </AbsoluteFill>
  );
};
