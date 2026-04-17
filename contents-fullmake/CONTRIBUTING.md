# contents-fullmake 改修ガイド

このスキルを改修するときの規約。**SKILL.md 肥大化と Drift を防ぐ**ためのルールを集約する。

---

## 1. SKILL.md の上限

| 指標 | 上限 | 現在値（参考） |
|---|---:|---:|
| 行数 | 250 行 | 172 行 |
| バイト数 | 12 KB | 10.5 KB |
| 1改修あたりの増分 | +30 行まで | — |

> 日本語 UTF-8 は 1 文字 3 バイトのため、英語スキルより上限を緩めてある。

### 上限を超えそうな時

そのまま SKILL.md に追記せず、**まず references/ に切り出せないか検討する**。判断フローは下記。

```
新規ルールを追加したい
    ↓
SKILL.md フロー全体（Phase 構造・起動・参照リンク）に関わるか？
    ├─ YES → SKILL.md に追記（増分は最小限に）
    └─ NO  → references/ 配下に新規 .md を作成 or 既存 .md に追記
              SKILL.md には1行の参照リンクのみ追加
```

### SKILL.md に直書きしてよいもの

- Phase 構造の骨格（Phase 名・順序・依存関係）
- エージェント名と起動時の最低限の役割
- 必須ゲートの**名称**（詳細条件は quality-gates.md）
- 参照ファイルへのリンク

### SKILL.md に書いてはいけないもの

- プロンプトテンプレ全文（references に切り出す）
- 採点基準・スコア定義の詳細（references に切り出す）
- 出力フォーマットのサンプル（references に切り出す）
- 過去経緯の説明・歴史的コメント
- bash コマンド詳細（依存スキル側に委譲する）

---

## 2. 改修ごとの必須チェックリスト

毎回スキルを改修したら、コミット前に以下を全部実行する。

- [ ] `../scripts/check_skill_size.sh contents-fullmake` を実行し、SKILL.md が上限内であることを確認
- [ ] SKILL.md と references/ で **同じ事実が二重定義されていない**か grep で確認
  - 例：「キャプション 3500 字」が SKILL.md と quality-gates.md の両方に書かれていてもよいが、片方が「3000 字」になっていたら Drift
- [ ] 旧仕様の記述を残していないか確認（半年前のカテゴリ名、廃止コマンド名など）
- [ ] `references/` の新規ファイルを SKILL.md 末尾の「参照ファイル」表に追加したか
- [ ] `evals/golden-prompts.md` に新機能の Success / Failure ケースを追加したか
- [ ] 自動メモリ（`~/.claude/projects/.../memory/`）に蓄積すべき改修ナレッジがないか確認

---

## 3. references/ ファイルの書き方

### 1ファイル1責務

- `workflow-spec.md` → カテゴリ・チーム通信・出力制約
- `title-playbook.md` → タイトルのバズ理論
- `title-workflow.md` → Phase 1.5 の手順
- `x-post-style.md` → X 投稿生成ルール
- `notion-publishing.md` → Notion 保存スキーマ
- `output-spec.md` → 出力順仕様・タイトル微調整方針
- `quality-gates.md` → 各 Phase の品質ゲート
- `writing-style.md` → 文章スタイル・禁止ワード

新規追加する場合は **既存ファイルに収まらない時だけ**にする。1責務 = 1ファイルを守る。

### 各ファイルの上限

| ファイル種別 | 推奨上限 |
|---|---:|
| references/*.md（標準） | 400 行 |
| references/*.md（プレイブック系） | 500 行 |
| references/*.md（ワークフロー手順） | 400 行 |

これを超える場合は、ファイル分割 or サブセクション削減を検討する。

### 内部リンク

references 内のファイル間で参照する場合は **相対パス** で書く：

```markdown
詳細は [title-workflow.md](title-workflow.md) の「Step C」を参照
```

---

## 4. Drift 防止ルール

### 旧仕様の更新は「リネーム＋全置換」

例：カテゴリ名を `picks` → `compare` に変える場合：

1. `grep -r "picks" .` で全箇所を洗い出す
2. SKILL.md と references/ 内の全箇所を一括置換
3. **依存スキル側にも同じ変更が必要か** Issue として記録
4. evals/golden-prompts.md のテストケースも更新

### 「コードと仕様書の Drift を許容しない」（CLAUDE.md 原則）

このスキルでは「コード」= プロンプトテンプレ／エージェント定義／品質ゲート。
これらと SKILL.md / references の記述に乖離が出たら、**乖離を見つけた時点で必ず直す**。後回し禁止。

---

## 5. 依存スキルへの変更

このスキルは以下の外部スキルに依存する：

- `tiktok-fit-research`
- `tiktok-fit-post-competitor-analysis`
- `tiktok-fit-carousel-script`
- `tiktok-fit-compliance-check`
- `tiktok-fit-notion-publisher`
- `tiktok-fit-slide-renderer`
- グローバル `note-writer`

依存スキルの **入力スキーマやコマンド体系を変える時**は、必ず本スキル側の起動プロンプトも併せて更新する。依存スキル側だけ直すと Drift が発生する。

---

## 6. 自動チェックの運用

### check_skill_size.sh の実行タイミング

- スキル改修後・コミット前（手動 or pre-commit hook）
- CI（将来導入時）

### CLAUDE.md MUST ルール（ユーザー個人設定）

ユーザー側の `~/.claude/CLAUDE.md` に以下を追記する運用：

```markdown
## Skill 改修時のチェック

IMPORTANT: contents-fullmake または他 skill の SKILL.md を編集した場合、
編集後に必ず `./scripts/check_skill_size.sh` を実行し、
上限超過がないことを確認すること。MUST。
```

これにより Claude が自律的にチェックを実行する二重防壁になる。

---

## 7. レビュー観点（次回大規模改修時）

このスキルは「個人運用 BB アカウント専用」だが、改修時は以下の観点で第三者目線をシミュレートする：

- 半年後の自分が SKILL.md だけ読んで全体像を掴めるか
- 新規参加者が references/ をどの順番で読めば理解できるか（README 的な索引が必要なら SKILL.md 末尾の参照ファイル表で代用）
- 依存スキルとの境界が明確か（このスキルが「やる」ことと「他スキルに任せる」ことの区別）
- 一気通貫フローが分断されすぎていないか（ユーザー介入ゲートは Phase 1.5 と Phase 5 の 2 箇所のみが原則）
