import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { DynamicBackground } from "./DynamicBackground";
import { Telop } from "./Telop";
import { SummaryTable } from "./SummaryTable";
import { COLORS, SlideData, Workflow } from "../types";

type Props = {
  slide: SlideData;
  workflow: Workflow;
  bgStyle: "gradient" | "particles" | "geometric";
  totalSlides: number;
};

export const Slide: React.FC<Props> = ({ slide, workflow, bgStyle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* Layer 1: Dynamic Background */}
      <DynamicBackground
        style={bgStyle}
        slideType={slide.slideType}
        accentColor={slide.accentColor}
      />

      {/* Layer 2: Optional Image (for Nano Banana integration) */}
      {slide.imageFile && <ImageLayer src={slide.imageFile} frame={frame} fps={fps} />}

      {/* Layer 3: Content */}
      {slide.slideType === "table" && slide.tableData && slide.tableColumns ? (
        <SummaryTable
          columns={slide.tableColumns}
          data={slide.tableData}
          title="総まとめ"
        />
      ) : (
        <ContentLayer slide={slide} frame={frame} fps={fps} />
      )}

      {/* Layer 4: Telop */}
      <Telop
        text={slide.telop}
        position={slide.slideType === "hook" ? "center" : "bottom"}
      />

      {/* Slide counter */}
      <SlideCounter index={slide.index} frame={frame} fps={fps} />
    </AbsoluteFill>
  );
};

const ContentLayer: React.FC<{
  slide: SlideData;
  frame: number;
  fps: number;
}> = ({ slide, frame, fps }) => {
  const opacity = interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = interpolate(frame, [0.3 * fps, 0.8 * fps], [0.95, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (slide.slideType === "hook") {
    return (
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "0 60px",
          opacity,
          transform: `scale(${scale})`,
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 900,
            fontFamily:
              '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
            color: COLORS.primary,
            textAlign: "center",
            lineHeight: 1.4,
            letterSpacing: 2,
          }}
        >
          {slide.telop}
        </div>
      </AbsoluteFill>
    );
  }

  if (slide.slideType === "cta") {
    const pulse = interpolate(
      frame % (fps * 2),
      [0, fps, 2 * fps],
      [1, 1.05, 1],
      { extrapolateRight: "clamp" }
    );

    return (
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "0 80px",
          opacity,
        }}
      >
        <div
          style={{
            transform: `scale(${pulse})`,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 56,
              fontWeight: 900,
              fontFamily:
                '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
              color: COLORS.accent,
              marginBottom: 30,
            }}
          >
            {slide.telop}
          </div>
          <div
            style={{
              fontSize: 36,
              fontWeight: 500,
              fontFamily:
                '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
              color: COLORS.muted,
            }}
          >
            コメントで教えてね
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // Default content slide
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "200px 70px 280px",
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          fontSize: 52,
          fontWeight: 800,
          fontFamily:
            '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
          color: COLORS.primary,
          textAlign: "center",
          lineHeight: 1.6,
          letterSpacing: 1,
        }}
      >
        {slide.narration}
      </div>
    </AbsoluteFill>
  );
};

const ImageLayer: React.FC<{
  src: string;
  frame: number;
  fps: number;
}> = ({ src, frame, fps }) => {
  // Slow Ken Burns zoom
  const scale = interpolate(frame, [0, 6 * fps], [1, 1.08], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 0.5 * fps], [0, 0.3], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
    </AbsoluteFill>
  );
};

const SlideCounter: React.FC<{
  index: number;
  frame: number;
  fps: number;
}> = ({ index, frame, fps }) => {
  const opacity = interpolate(frame, [0.5 * fps, fps], [0, 0.4], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 60,
        right: 50,
        opacity,
        fontSize: 28,
        fontWeight: 600,
        fontFamily: '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
        color: COLORS.muted,
      }}
    >
      {index + 1}
    </div>
  );
};
