import { AbsoluteFill, Sequence, staticFile } from "remotion";
import { Audio } from "@remotion/media";
import { Slide } from "./components/Slide";
import { Transition } from "./components/Transition";
import { ReelProps } from "./types";

export const ReelComposition: React.FC<ReelProps> = ({
  slides,
  workflow,
  transitionDurationFrames,
  bgStyle,
}) => {
  let currentFrame = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      {slides.map((slide, i) => {
        const from = currentFrame;
        currentFrame += slide.durationInFrames;

        return (
          <Sequence
            key={i}
            from={from}
            durationInFrames={slide.durationInFrames}
          >
            {/* Transition wrapper */}
            <Transition
              type={i === 0 ? "fade" : "slide-up"}
              durationInFrames={transitionDurationFrames}
              totalDurationInFrames={slide.durationInFrames}
            >
              <Slide
                slide={slide}
                workflow={workflow}
                bgStyle={bgStyle}
                totalSlides={slides.length}
              />
            </Transition>

            {/* Audio track for this slide */}
            {slide.audioFile && (
              <Audio src={staticFile(slide.audioFile)} volume={1} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
