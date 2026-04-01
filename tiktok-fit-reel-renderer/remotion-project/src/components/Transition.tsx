import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type TransitionType = "fade" | "slide-up" | "slide-left" | "zoom";

type Props = {
  type: TransitionType;
  durationInFrames: number;
  totalDurationInFrames: number;
  children: React.ReactNode;
};

export const Transition: React.FC<Props> = ({
  type,
  durationInFrames,
  totalDurationInFrames,
  children,
}) => {
  const frame = useCurrentFrame();

  // Enter animation
  const enterProgress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Exit animation (last N frames)
  const exitStart = totalDurationInFrames - durationInFrames;
  const exitProgress = interpolate(
    frame,
    [exitStart, totalDurationInFrames],
    [1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const style = getTransitionStyle(type, enterProgress, exitProgress);

  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

function getTransitionStyle(
  type: TransitionType,
  enter: number,
  exit: number
): React.CSSProperties {
  switch (type) {
    case "fade":
      return {
        opacity: Math.min(enter, exit),
      };

    case "slide-up":
      const yEnter = interpolate(enter, [0, 1], [100, 0]);
      return {
        opacity: Math.min(enter, exit),
        transform: `translateY(${enter < 1 ? yEnter : 0}px)`,
      };

    case "slide-left":
      const xEnter = interpolate(enter, [0, 1], [200, 0]);
      return {
        opacity: Math.min(enter, exit),
        transform: `translateX(${enter < 1 ? xEnter : 0}px)`,
      };

    case "zoom":
      const scale = interpolate(enter, [0, 1], [0.8, 1]);
      return {
        opacity: Math.min(enter, exit),
        transform: `scale(${enter < 1 ? scale : 1})`,
      };
  }
}
