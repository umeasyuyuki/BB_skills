import { Composition } from "remotion";
import { ReelComposition } from "./ReelComposition";
import { ReelProps, REEL_WIDTH, REEL_HEIGHT, REEL_FPS } from "./types";

const defaultSlides: ReelProps = {
  title: "サンプルリール",
  workflow: "picks",
  transitionDurationFrames: 15,
  bgStyle: "gradient",
  slides: [
    {
      index: 0,
      telop: "クレアチンBEST5",
      narration: "今日はクレアチンのおすすめランキングを紹介します",
      durationInFrames: 120,
      slideType: "hook",
      accentColor: "#E94560",
    },
    {
      index: 1,
      telop: "評価基準は3つ",
      narration:
        "評価基準はコスパ、純度、そして溶けやすさの3つです",
      durationInFrames: 150,
      slideType: "content",
    },
    {
      index: 2,
      telop: "第5位：バルクスポーツ",
      narration:
        "第5位はバルクスポーツのクレアチンモノハイドレート。1グラムあたり3.2円とコスパ優秀",
      durationInFrames: 150,
      slideType: "content",
    },
    {
      index: 3,
      telop: "総まとめ",
      narration: "以上がクレアチンのおすすめランキングでした",
      durationInFrames: 180,
      slideType: "table",
      tableColumns: ["順位", "商品", "コスパ", "評価"],
      tableData: [
        { 順位: "1位", 商品: "マイプロテイン", コスパ: "◎", 評価: "★★★" },
        { 順位: "2位", 商品: "NOW Foods", コスパ: "○", 評価: "★★☆" },
        { 順位: "3位", 商品: "オプチマム", コスパ: "○", 評価: "★★☆" },
      ],
    },
    {
      index: 4,
      telop: "保存して見返してね！",
      narration:
        "参考になったら保存して見返してください。質問はコメント欄で！",
      durationInFrames: 120,
      slideType: "cta",
    },
  ],
};

export const RemotionRoot: React.FC = () => {
  const totalFrames = defaultSlides.slides.reduce(
    (sum, s) => sum + s.durationInFrames,
    0
  );

  return (
    <Composition
      id="Reel"
      component={ReelComposition}
      durationInFrames={totalFrames}
      fps={REEL_FPS}
      width={REEL_WIDTH}
      height={REEL_HEIGHT}
      defaultProps={defaultSlides}
    />
  );
};
