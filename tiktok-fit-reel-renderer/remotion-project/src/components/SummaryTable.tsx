import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, TableRow } from "../types";

type Props = {
  columns: string[];
  data: TableRow[];
  title?: string;
};

export const SummaryTable: React.FC<Props> = ({ columns, data, title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "120px 50px",
      }}
    >
      {title && (
        <div
          style={{
            fontSize: 48,
            fontWeight: 900,
            fontFamily:
              '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
            color: COLORS.primary,
            marginBottom: 40,
            textAlign: "center",
            opacity: interpolate(frame, [0, 0.3 * fps], [0, 1], {
              extrapolateRight: "clamp",
            }),
          }}
        >
          {title}
        </div>
      )}

      {/* Table */}
      <div
        style={{
          width: "100%",
          borderRadius: 16,
          overflow: "hidden",
          boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            backgroundColor: COLORS.tableHeader,
            padding: "20px 0",
            opacity: interpolate(frame, [0.2 * fps, 0.5 * fps], [0, 1], {
              extrapolateRight: "clamp",
            }),
          }}
        >
          {columns.map((col, ci) => (
            <div
              key={ci}
              style={{
                flex: 1,
                color: "#FFFFFF",
                fontSize: 32,
                fontWeight: 700,
                fontFamily:
                  '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
                textAlign: "center",
                padding: "0 8px",
              }}
            >
              {col}
            </div>
          ))}
        </div>

        {/* Rows - staggered animation */}
        {data.map((row, ri) => {
          const rowDelay = 0.4 + ri * 0.15;
          const rowOpacity = interpolate(
            frame,
            [rowDelay * fps, (rowDelay + 0.3) * fps],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          const rowSlide = interpolate(
            frame,
            [rowDelay * fps, (rowDelay + 0.3) * fps],
            [30, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          return (
            <div
              key={ri}
              style={{
                display: "flex",
                backgroundColor:
                  ri % 2 === 0 ? COLORS.tableRow1 : COLORS.tableRow2,
                padding: "18px 0",
                opacity: rowOpacity,
                transform: `translateX(${rowSlide}px)`,
              }}
            >
              {columns.map((col, ci) => (
                <div
                  key={ci}
                  style={{
                    flex: 1,
                    color: COLORS.primary,
                    fontSize: 30,
                    fontWeight: ci === 0 ? 700 : 500,
                    fontFamily:
                      '"Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif',
                    textAlign: "center",
                    padding: "0 8px",
                  }}
                >
                  {row[col] || ""}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
