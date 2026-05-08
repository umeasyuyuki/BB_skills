# bb-note-threads

BB（Brain Bulking）専用のテキスト媒体オーケストレーター。タイトル投入 1 つで Threads 投稿と Note 記事を並列生成し、Threads から Note へ自然に案内し、Note 末尾で公式 LINE オープンチャットへ温かくつなぐ。

## このスキルが解決する課題

TikTok カルーセル生成（contents-fullmake）とは独立した「Threads → Note → LINE オープンチャット」の文字媒体動線を、ボタン 1 つで構築できる。3 メディア統合運用と切り離して、テキスト媒体だけで完結するワークフローを回したいときに使う。

## 動線設計

```
Threads（要点・抽象、500-700字）
   ↓ Note URL リンク
Note（深掘り、2500-3500字）
   ↓ Note末尾の公式リンク
LINEオープンチャット「サイエンスベースフィットネス@Brain Bulking」
```

## 使い方

```bash
# 対話モード（タイトルを聞かれる）
/bb-note-threads

# タイトル直接指定
/bb-note-threads "プロテイン値上げで起きる栄養格差"

# 競合分析を省略（軽量モード）
/bb-note-threads "プロテイン値上げで起きる栄養格差" --no-competitor
```

## 実行フロー

| Phase | 内容 | 並列性 | 所要時間 |
|---|---|---|---|
| 0 | タイトル受領、カテゴリ自動判定 | — | 〜5 秒 |
| 1 | リサーチ + 競合分析（並列） | ✅ TeamCreate | 3〜5 分 |
| 2 | Threads + Note 並列生成 | ✅ | 3〜4 分 |
| 3 | 薬機法チェック（両媒体並列） | ✅ | 30 秒 |
| 4 | Notion 2 ページ保存 + 相互リンク | 直列 | 30 秒 |
| 5 | note.com 下書き保存 | 直列 | 30 秒 |

合計: 8〜12 分

## 出力

Notion DB に 2 ページ作成（既存の tiktok-fit-notion-publisher の DB に追加）:

| ページ | content_type | funnel_stage | pricing_mode |
|---|---|---|---|
| Threads 投稿 | `threads` | `awareness` | `free` |
| Note 記事 | `note` | `engagement` | `free` |

両ページに `paired_post_url` プロパティで相互リンクが張られる。

## TikTok との関係

- **TikTok カルーセル生成** → `contents-fullmake` を使う（こちらは TikTok カルーセル専用に縮退済み）
- **Threads + Note 生成** → 本スキル `bb-note-threads` を使う
- **TikTok カルーセルには LINE OC URL を絶対に入れない**（contents-fullmake/references/line-oc.md と整合）
- **Threads にも LINE OC URL を入れない**。Threads は Note URL のみ
- **Note 末尾は公式 LINE OC 実リンクへ案内**する

## トーン

- **低温の標準語ベース** — 断定・体言止めを基調に、関西弁っぽい親しさや勢いを落とし、数字と事実で強く言う BB トーン（旧仕様の関西弁レベル 2 は廃止）
- BB の「情熱が見える怒り」は事実と数字で表現する
- Threads 本文 = 低温の標準語 BB トーン（`俺ら` は原則使わない）
- Note 本文 = 標準語 BB トーン
- Threads 最終リプ = 温かく、ゆるい Note 案内
- Note 末尾 = 関連リンク案内。押し付けず、医療相談・個別診断ではない旨を明記
- TikTok カルーセル（contents-fullmake）は従来通り標準語

## 主要ファイル

- `SKILL.md` — オーケストレーター本体（Phase 0-4 のコア手順）
- `references/workflow-spec.md` — Phase 詳細・エージェント通信仕様
- `references/brand-profile.md` — BB の思想・対象読者・媒体別役割
- `references/tone-guide.md` — 共通文体・低温の標準語ルール
- `references/domain-vocabulary.md` — 専門用語の翻訳辞書
- `references/threads-style.md` — Threads 共通ルール
- `references/threads-patterns.md` — Threads 8 型テンプレ・カテゴリ × 型マッピング
- `references/note-style.md` — Note 固有ルール
- `references/cta-policy.md` — Threads 最終リプ / Note 末尾 / LINE OC 導線
- `references/output-spec.md` — 出力フォーマット定義
- `references/notion-publishing.md` — Notion 保存仕様
- `references/note-com-publishing.md` — note.com 下書き保存仕様
- `references/quality-gates.md` — セルフチェック・薬機法ゲート

## 依存スキル

| スキル | 役割 | 流用度 |
|---|---|---|
| `tiktok-fit-research` | Phase 1 リサーチ | 媒体非依存、そのまま流用 |
| `tiktok-fit-post-competitor-analysis` | Phase 1 競合分析 | platform に `threads`/`note` 追加で流用 |
| `tiktok-fit-compliance-check` | Phase 3 薬機法 | そのまま流用 |
| `tiktok-fit-notion-publisher` | Phase 4 Notion 保存 | content_type に `threads` 追加 + 新プロパティ |
| `note-writer`（汎用） | 参考実装、現在は使用しない | — |

## 外部導線の運用注意点

- Threads 投稿には LINE 直リンクを置かない
- Threads の最終リプは「詳しい根拠は Note に置いておきます」の温度感にする
- Note 末尾は `## 関連リンク` とし、公式 LINE オープンチャットへの実リンクを入れる
- Threads では LINE 直リンクを置かず、プロフィールの相談室として匂わせる
- 健康・栄養・ヘルスケア領域では、個別の医療相談や診断ではない旨を明記する

## Note 有料化への備え

Note 有料化（Threads 500 フォロワー後）に備え、Notion DB に `pricing_mode` プロパティ（`free` / `paid`）を持たせている。現状は `free` のみ。`paid` モード生成ロジックは別タスクで実装予定。

## 環境変数

| 変数 | 既定値 | 用途 |
|---|---|---|
| `BB_NOTE_THREADS_OUTPUT_DIR` | `output/` | エラー時のローカルバックアップ先 |

## 設計判断（ADR 抜粋）

- **タイトル評価フロー無し**: ユーザーが既にタイトルを決めている前提。投入されたタイトルをそのまま採用、各媒体微調整のみ実施
- **Notion DB は既存 DB に追加**: 専用 DB を切らず、`content_type` で TikTok と分離。Notion 側のビュー設計のみで運用
- **案内文は固定テンプレ + 軽い調整**: Threads は Note 案内、Note は公式 LINE OC 実リンク付きの関連リンク案内に寄せる
- **paired_post_url で相互リンク**: Threads ⇔ Note の動線を Notion 上でも追跡可能に
