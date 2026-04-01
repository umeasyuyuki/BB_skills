export type Workflow = "picks" | "myth" | "harms" | "intake";

export type SlideType = "hook" | "content" | "table" | "cta";

export type TableRow = Record<string, string>;

export type SlideData = {
  index: number;
  telop: string;
  narration: string;
  audioFile?: string;
  audioDurationSec?: number;
  durationInFrames: number;
  slideType: SlideType;
  tableData?: TableRow[];
  tableColumns?: string[];
  imageFile?: string;
  accentColor?: string;
};

export type ReelProps = {
  slides: SlideData[];
  workflow: Workflow;
  title: string;
  transitionDurationFrames: number;
  bgStyle: "gradient" | "particles" | "geometric";
};

export const REEL_WIDTH = 1080;
export const REEL_HEIGHT = 1920;
export const REEL_FPS = 30;

export const COLORS = {
  bg: "#FFFFFF",
  primary: "#1A1A2E",
  accent: "#E94560",
  secondary: "#0F3460",
  muted: "#6B7280",
  success: "#10B981",
  warning: "#F59E0B",
  tableHeader: "#1A1A2E",
  tableRow1: "#F8F9FA",
  tableRow2: "#FFFFFF",
};
