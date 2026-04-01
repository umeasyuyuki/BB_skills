---
name: tiktok-fit-reel-renderer
description: tiktok-fit-carousel-script または orchestrator が生成した台本Markdownから、VOICEVOX音声・背景動画・BGM付きの縦型リール動画（9:16）を自動レンダリングするスキル。2フェーズ運用（台本→JSON→画像作成→動画生成）に対応。
---

# TikTok Fit Reel Renderer

## Purpose

既存の台本スキルチェーン（orchestrator → research → script）の出力を受け取り、
ナレーション音声・背景動画ループ・トランジションSE・BGM付きのリール動画を生成する。

## Trigger

- orchestrator 完了後に「動画も作って」と言われたとき
- 台本Markdownを指定して「リール動画にして」と言われたとき
- `/render-reel <script.md>` コマンド

## 2フェーズ運用

### Phase 1: 台本 → slides.json + 音声生成

```bash
cd /Users/asyuyukiume/Projects/Reel-movie
./build.sh --script 台本.md
```

1. `parse_script.py` が台本Markdownを解析 → `slides.json` 生成
2. VOICEVOX で全スライドの音声を生成（固定速度1.3x）
3. 画像チェックリストを表示して終了

### (手動) 画像作成

チェックリストに沿って画像を作成し `public/images/` に配置。
ファイル名: `slide_00.jpg`, `slide_01.jpg`, ...（自動で割り当て済み）

### Phase 2: 動画生成

```bash
./build.sh --skip-audio
```

1. Remotion で動画レンダー（背景動画ループ + 1:1画像中央配置 + トランジションSE）
2. BGM フォルダからランダム選曲してミックス（音量12%、最後2秒フェードアウト）
3. 完成動画を自動再生

## build.sh オプション

```bash
./build.sh --script 台本.md           # Phase 1
./build.sh --skip-audio               # Phase 2
./build.sh                            # フルビルド（Phase 1+2、画像が既にある場合）
./build.sh --speed 1.5                # 読み上げ速度変更
./build.sh --speaker 3                # 声の変更（ずんだもん）
./build.sh --bgm-volume 0.20         # BGM音量調整
./build.sh --skip-audio --skip-render # BGMだけ再ミックス
./build.sh --no-bgm                   # BGMなし
./build.sh --output my_video.mp4      # 出力名指定
```

## 動画仕様

| 項目 | 値 |
|------|-----|
| 解像度 | 1080 × 1920（9:16） |
| FPS | 30 |
| コーデック | H.264 + AAC 192kbps |
| 画像配置 | 1:1画像を中央配置、ズームアウト（8秒で6%縮小） |
| 背景 | `public/material/bg_loop.mp4` をループ再生 |
| テロップ | なし（ナレーション + 画像のみ） |
| トランジション | punch → slide-up → zoom → fade ローテーション |
| トランジションSE | スライド切替時に効果音（音量60%） |
| BGM | `BGM/` フォルダからランダム選曲、音量12%、最後2秒フェードアウト |
| 読み上げ速度 | 1.3x 固定（全スライド統一） |

## VOICEVOX Speaker ID

| ID | 名前 | 特徴 |
|----|------|------|
| 13 | 青山龍星（デフォルト） | 低音男性、フィットネス向け |
| 2  | 四国めたん | 落ち着いた女性 |
| 3  | ずんだもん | 元気でかわいい |
| 8  | 春日部つむぎ | 明るい女性 |
| 14 | 冥鳴ひまり | 柔らかい女性 |

## プロジェクト構成

```
/Users/asyuyukiume/Projects/Reel-movie/
├── slides.json              # スライド定義（narration, imageFile, slideType）
├── build.sh                 # ビルドスクリプト（Mac）
├── build.bat                # ビルドスクリプト（Windows）
├── MANUAL.md                # 取扱説明書（非エンジニア向け）
├── scripts/
│   ├── parse_script.py      # 台本Markdown → slides.json
│   └── voicevox_tts.py      # VOICEVOX音声生成（--speed, --speaker対応）
├── src/
│   ├── Root.tsx              # Remotion設定 + calculateMetadata
│   ├── ReelComposition.tsx   # メインコンポジション（背景動画 + SE）
│   └── components/
│       ├── Slide.tsx         # 1:1画像中央配置 + Ken Burns
│       └── Transition.tsx    # 4種トランジション
├── public/
│   ├── images/               # スライド画像
│   ├── audio/                # 生成音声 + transition_se.wav
│   └── material/bg_loop.mp4  # 背景ループ動画
├── BGM/                      # BGM素材（ランダム選曲）
└── output/                   # 完成動画
```

## Orchestrator 連携フロー

```
/tiktok-fit-feed-orchestrator テーマ名
  → 台本Markdown生成 + Notion保存
  → ./build.sh --script 台本.md     (Phase 1)
  → 画像を手動作成
  → ./build.sh --skip-audio          (Phase 2)
  → MP4 完成
```

## Constraints

- VOICEVOX engine が localhost:50021 で起動している必要がある
- ffmpeg / ffprobe が必要
- Node.js 18+ が必要
- Remotion v4.0.434（`npx remotion` はシンボリックリンク破損のため `node node_modules/@remotion/cli/remotion-cli.js` で直接呼出し）
- 画像は手動作成が必要（正方形1:1推奨）
