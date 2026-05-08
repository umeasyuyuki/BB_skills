# Skill 仕分け案

作成日: 2026-04-27

## 前提

ユーザー運用上、現在めちゃくちゃ使う skill はほぼ `contents-fullmake` のみ。

そのため、この仕分けでは「単独 skill として残すか」ではなく、次の観点で分類する。

1. `contents-fullmake` の実行に必要か
2. 現役で直接使うか
3. リール動画作成のように別用途で残す価値があるか
4. 現行 BB 戦略・マネタイズ・進捗管理に接続しているか

削除はまだ実行しない。まずは archive / merge / delete-candidate の判断材料にする。

2026-04-27 更新:
この方針に基づき、非現役 skill は `archive/skills/` へ退避済み。

## 結論

残すべき中核はかなり少ない。

### A. 現役として残す

| Directory | 判断 | 理由 |
|---|---|---|
| `contents-fullmake` | keep / core | 現在の唯一に近い入口。投稿制作・Notion保存・画像生成まで統合されている。 |
| `tiktok-fit-reel-renderer` | keep / separate | `contents-fullmake` とは別用途だが、リール動画作成の将来性があるため残す。ただし実行パス修正が必要。 |

### B. `contents-fullmake` の内部部品として残す

これらは単独 skill として育てる必要は薄いが、`contents-fullmake` から参照されているため即削除は危険。

| Directory | 判断 | 理由 |
|---|---|---|
| `tiktok-fit-research` | keep-as-component / later-merge | `contents-fullmake` Phase 1 で参照。単独利用は少ないなら、将来的には `contents-fullmake/references` へ吸収してもよい。 |
| `tiktok-fit-post-competitor-analysis` | keep-as-component / later-merge | `contents-fullmake` Phase 1 で参照。競合分析を使わない運用になったら削除候補。 |
| `tiktok-fit-carousel-script` | keep-as-component | `contents-fullmake` Phase 2 の実質本体。大きいが削除不可。 |
| `tiktok-fit-compliance-check` | keep-as-component | 公開前リスクチェックとして必要。単独 skill ではなく gate として残す。 |
| `tiktok-fit-notion-publisher` | keep-as-component | Notion 保存の実装。`contents-fullmake` の永続化レイヤー。 |
| `tiktok-fit-slide-renderer` | keep-as-component | `contents-fullmake` Phase 5 の Pillow 画像生成で参照。 |

### C. archive 済み

現行の「contents-fullmake 中心」運用から外れているため、`archive/skills/` に退避済み。

| Directory | 判断 | 理由 |
|---|---|---|
| `archive/skills/tiktok-fit-insta-single` | archived | 1枚画像生成は現行 pipeline の主役ではない。旧トーンも残っている。 |
| `archive/skills/tiktok-fit-skill-builder` | archived | 旧戦略の前提が多い。今後の skill 設計は repo docs / Codex で直接管理した方がよい。 |
| `archive/skills/tiktok-fit-slide-image-generator` | archived | `contents-fullmake` Phase 5 と重複。Antigravity 運用を使っていないなら不要。 |
| `archive/skills/tiktok-notion-analyzer` | archived | 投稿分析自体は有用だが、現在の主運用から外れている。進捗管理に統合するまで退避。 |

### D. Trend Research は縮小

リサーチ自体はたまに使うが、skill が2つある必要は薄い。

| Directory | 判断 | 理由 |
|---|---|---|
| `fitness-trend-researcher` | optional-keep / research-lab | Gemini CLI 自動調査を今後使うなら残す。たまに使う程度なら `docs/research/` に運用手順として残してもよい。 |
| `archive/skills/tiktok-fit-trend-research` | archived | `fitness-trend-researcher` と重複。古い方として archive 済み。 |

### E. skill ではないので登録対象から外す

| Directory | 判断 | 理由 |
|---|---|---|
| `Research_report` | keep-as-archive / non-skill | 投稿素材の保管場所としては有用。ただし Claude Code skill として登録しない。 |
| `scripts` | keep / non-skill | utility。skill ではない。 |
| `line-stamps` | move-out-or-delete-candidate | BB の現行 skill 管理とは別物。別 repo に出すか削除候補。 |

## かなり絞った理想構成

最終的には以下くらいまで減らせる。

```text
contents-fullmake/                 # 唯一の投稿制作入口
  references/
  scripts/

tiktok-fit-reel-renderer/           # リール動画作成だけ別系統で保持

tiktok-fit-slide-renderer/          # contents-fullmake の画像生成部品
tiktok-fit-notion-publisher/        # contents-fullmake のNotion保存部品

docs/
  strategy/
  progress/
  monetization/
  system/
  research/
```

さらに踏み込むなら、以下は `contents-fullmake/references/` に吸収可能。

- `tiktok-fit-research`
- `tiktok-fit-post-competitor-analysis`
- `tiktok-fit-carousel-script`
- `tiktok-fit-compliance-check`

ただし、いきなり吸収すると `contents-fullmake/SKILL.md` が肥大化しやすい。まずは「内部部品」として残し、単独 skill としての README 掲載や setup 登録を外すのが現実的。

## 削除順序案

### Step 1: setup 対象を絞る

`setup.sh` を修正し、`SKILL.md` があるディレクトリだけ登録する。

さらに、登録対象 allowlist を作るならまずは以下。

```text
contents-fullmake
tiktok-fit-reel-renderer
tiktok-fit-notion-publisher
tiktok-fit-slide-renderer
tiktok-fit-carousel-script
tiktok-fit-compliance-check
tiktok-fit-research
tiktok-fit-post-competitor-analysis
```

### Step 2: README から非現役 skill を外す

README の skill 一覧を「現役入口」「内部部品」「保留・archive」に分ける。

### Step 3: archive ディレクトリへ移動

削除ではなく、まずは以下を `archive/skills/` に移すのが安全。

```text
tiktok-fit-insta-single
tiktok-fit-skill-builder
tiktok-fit-slide-image-generator
tiktok-notion-analyzer
tiktok-fit-trend-research
```

`fitness-trend-researcher` は、今後も Gemini 調査を使うなら残す。使わないなら同じく archive。

### Step 4: repo から明らかな非 skill を分離

```text
line-stamps
```

これは BB skill repo からは外した方がよい。別 repo にするか、不要なら削除候補。

### Step 5: 内部部品の吸収を検討

`contents-fullmake` が安定してから、以下を本当に別 skill にしておく必要があるか判断する。

- research
- competitor-analysis
- carousel-script
- compliance-check

## 今回の判断で更新すべき認識

前回の `skill-registry.md` では active が多めだった。

今回の運用実態を踏まえると、正しくは:

- active entrypoint: `contents-fullmake`
- active separate: `tiktok-fit-reel-renderer`
- active components: Notion / slide-renderer / carousel / compliance / research / competitor
- archive candidates: それ以外のほとんど

## 次にやるなら

最初の実作業は、削除ではなくこの3点が安全。

1. `.gitignore` を強化する
2. `setup.sh` を `SKILL.md` あり + allowlist 登録に変える
3. README の skill 一覧を現役実態に合わせる

その後、archive 移動を1コミットで実施する。
