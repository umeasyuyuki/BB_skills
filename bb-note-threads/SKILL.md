---
name: bb-note-threads
description: BB（Brain Bulking）専用のテキスト媒体オーケストレーター。タイトル投入1つで、Threads投稿とNote記事を生成し、Threads最終リプはNote案内+LINEオープンチャット匂わせ、Note末尾は公式LINEオープンチャット実リンク付きの関連リンク案内で締める。専門用語は読者の語彙に翻訳する。
---

<!--
このファイルはコア手順のみ。詳細仕様は references/ 配下に分離。
肥大化チェック: scripts/check_skill_size.sh bb-note-threads を改修後に必ず実行。
-->

# BB Note × Threads オーケストレーター

## 役割

タイトル文字列1つを入口に、Threads投稿とNote記事を並列生成し、Notion保存と note.com 下書き保存までつなぐ。

主要導線:

```text
Threads 本体
  -> 最終リプで Note URL 案内
  -> 最終リプのサブで「プロフィールの相談室」を控えめに案内
Note
  -> 末尾の関連リンクで公式LINEオープンチャット実リンクを案内
```

## 正本ファイル

| 領域 | 正本 |
|---|---|
| ブランド前提 | `references/brand-profile.md` |
| 実行手順・agent指示 | `references/workflow-spec.md` |
| 共通トーン | `references/tone-guide.md` |
| 専門用語翻訳 | `references/domain-vocabulary.md` |
| Threads共通ルール | `references/threads-style.md` |
| Threads 8型テンプレ | `references/threads-patterns.md` |
| Note固有ルール | `references/note-style.md` |
| CTA / LINE OC / 関連リンク | `references/cta-policy.md` |
| 出力形式 | `references/output-spec.md` |
| Notion保存 | `references/notion-publishing.md` |
| note.com下書き保存 | `references/note-com-publishing.md` |
| 品質ゲート | `references/quality-gates.md` |

旧参照互換: `references/line-oc-templates.md` と `references/kansai-tone.md` は非推奨。新規参照では使わない。

## 起動フロー

| 呼び出し方 | 動作 |
|---|---|
| `/bb-note-threads` | 対話モード: タイトル質問 → フルフロー |
| `/bb-note-threads "タイトル"` | タイトル即採用 → フルフロー |
| `/bb-note-threads "タイトル" --no-competitor` | 競合分析を省略する軽量モード |

カテゴリは `compare` / `ingredient` / `entertainment` / `debunk` / `discovery` の5種。Threads型選択、最終リプ、Note本文の切り口調整に使う。

## フェーズ

| Phase | 内容 | 正本 |
|---:|---|---|
| 0 | タイトル受領・カテゴリ判定 | `workflow-spec.md` |
| 1 | research + competitor-analysis 並列調査 | `workflow-spec.md` |
| 2 | threads-writer + note-writer 並列生成 | `workflow-spec.md` |
| 3 | 薬機法チェック | `quality-gates.md` |
| 4 | Notion保存・相互リンク | `notion-publishing.md` |
| 5 | note.com下書き保存 | `note-com-publishing.md` |

## Phase 2 必須仕様

- Threads は親 + 本体リプ + 最終リプのツリー構成。型選択は `threads-patterns.md`。
- Threads 本文は低温の標準語 BB トーン。関西弁・高温口語・`俺ら` 連発は禁止。
- Threads 最終リプは `cta-policy.md` の D-2 二段構成: Note案内 + 区切り + LINE OC匂わせ。
- Noteは導入直後に `[TOC]` を単独行で置き、H2/H3から note.com 目次を自動生成する。
- 専門用語は `domain-vocabulary.md` に従い、読者の語彙へ翻訳する。

## セルフチェック

writer は `quality-gates.md` のチェックリストを全項目実行する。特に以下は必須。

- D-2 二段構成
- 専門用語翻訳
- 関西弁混入なし
- Threads LINE 直 URL なし / Note は指定OCリンクのみ
- 強い誘導語なし
- 医療相談・個別診断ではない旨の免責

## TikTok との分離原則

- TikTok カルーセル / Threads は LINE 直 URL 禁止。Note 末尾のみ指定の公式OCリンクを入れる。
- 本スキルの LINE OC 露出は Threads 最終リプ（サブ）と Note 末尾の関連リンクのみ。
- TikTok 用台本生成は `contents-fullmake` または TikTok 専用スキルを使う。

## エラー時の挙動

- Phase 1で調査系が両方失敗: 中断し、エラー報告。
- Phase 2で片方のwriterが失敗: 成功側を保持し、失敗側のみリトライ。
- Phase 3でRed判定が2回続く: 手動修正を依頼。
- Phase 4でNotion保存失敗: `output/<timestamp>/` にローカルバックアップ。
- Phase 5でnote.com下書き保存失敗: Chrome Cookie取り込みまたはnote-mcp登録状態を確認し、Notion URLとローカルバックアップを返す。
