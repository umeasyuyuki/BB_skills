# bb-note-threads

BB（Brain Bulking）専用のテキスト媒体オーケストレーター。タイトル投入 1 つで Threads 投稿と Note 記事を並列生成し、LINE オープンチャット誘導付きで Notion 保存まで完結する。

## このスキルが解決する課題

TikTok カルーセル生成（contents-fullmake）とは独立した「Threads → Note → LINE OC」の文字媒体動線を、ボタン 1 つで構築できる。3 メディア統合運用と切り離して、テキスト媒体だけで完結するワークフローを回したいときに使う。

## 動線設計

```
Threads（要点・抽象、500-700字）
   ↓ Note URL リンク
Note（深掘り、2500-3500字）
   ↓ LINE OC URL + 「なぜ最新トレンドが必要か」
LINE オープンチャット（コミュニティ化）
```

## 使い方

```bash
# 対話モード（タイトルを聞かれる）
/bb-note-threads

# タイトル直接指定
/bb-note-threads "プロテイン値上げで起きる栄養格差"
```

## 実行フロー

| Phase | 内容 | 並列性 | 所要時間 |
|---|---|---|---|
| 0 | タイトル受領、カテゴリ自動判定 | — | 〜5 秒 |
| 1 | リサーチ（researcher 単独、差別化軸抽出含む） | — | 3〜5 分 |
| 2 | Threads + Note 並列生成 | ✅ | 3〜4 分 |
| 3 | 薬機法チェック（両媒体並列） | ✅ | 30 秒 |
| 4 | Notion 2 ページ保存 + 相互リンク | 直列 | 30 秒 |

合計: 7〜10 分

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
- **Threads / Note にだけ LINE OC URL を完成形で直書き**

## トーン

- **関西弁レベル 2（バランス型）** — 自然な関西出身者の文体。「〜やで」「〜ねん」「ほな」を自然に
- BB の「情熱が見える怒り」を**ツッコミ系の関西弁**で表現
- Threads = 全文関西弁 / Note = 地の文標準語 + 主張・体験談で関西弁ハイブリッド
- LINE OC 誘導の L1 = 関西弁、L2-L4 固定文 = 標準語維持（コミュニティの公式キャッチ感）
- TikTok カルーセル（contents-fullmake）は標準語のまま（媒体カルチャー違いを尊重）

## 主要ファイル

- `SKILL.md` — オーケストレーター本体（Phase 0-4 のコア手順）
- `references/workflow-spec.md` — Phase 詳細・エージェント通信仕様
- `references/kansai-tone.md` — **関西弁トーンガイド（共通、必読）**
- `references/threads-style.md` — Threads 文体ガイド（ツリー構成・4 型）
- `references/note-style.md` — Note 文体ガイド（ハイブリッド関西弁）
- `references/line-oc-templates.md` — LINE OC 誘導文（L1 参考プール + L2-L4 固定文）
- `references/output-spec.md` — 出力フォーマット定義
- `references/notion-publishing.md` — Notion 保存仕様
- `references/quality-gates.md` — セルフチェック・薬機法ゲート

## 依存スキル

| スキル | 役割 | 流用度 |
|---|---|---|
| `tiktok-fit-research` | Phase 1 リサーチ + 差別化軸抽出 | 媒体非依存、そのまま流用 |
| `tiktok-fit-compliance-check` | Phase 3 薬機法 | そのまま流用 |
| `tiktok-fit-notion-publisher` | Phase 4 Notion 保存 | content_type に `threads` 追加 + 新プロパティ |
| `note-writer`（汎用） | 参考実装、現在は使用しない | — |

## LINE OC 運用注意点

- LINE OC URL `https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw` はチャット名「サイエンスベースフィットネス@Brain Bulking」と紐付く
- URL 変更時は本スキル `references/line-oc-templates.md` と `contents-fullmake/references/line-oc.md` の両方を同期する必要あり
- 完全無料運用、ステータスシンボル化を本気で目指す方針

## Note 有料化への備え

Note 有料化（Threads 500 フォロワー後）に備え、Notion DB に `pricing_mode` プロパティ（`free` / `paid`）を持たせている。現状は `free` のみ。`paid` モード生成ロジックは別タスクで実装予定。

## 環境変数

| 変数 | 既定値 | 用途 |
|---|---|---|
| `BB_NOTE_THREADS_OUTPUT_DIR` | `output/` | エラー時のローカルバックアップ先 |

## 設計判断（ADR 抜粋）

- **タイトル評価フロー無し**: ユーザーが既にタイトルを決めている前提。投入されたタイトルをそのまま採用、各媒体微調整のみ実施
- **Notion DB は既存 DB に追加**: 専用 DB を切らず、`content_type` で TikTok と分離。Notion 側のビュー設計のみで運用
- **L1 は AI 生成 + L2-L4 固定**: 記事ごとのテーマ連動性と、LINE OC 訴求の一貫性を両立
- **paired_post_url で相互リンク**: Threads ⇔ Note の動線を Notion 上でも追跡可能に
