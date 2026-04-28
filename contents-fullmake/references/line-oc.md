# LINE オープンチャット 取り扱いルール（contents-fullmake 用）

contents-fullmake は **TikTok カルーセル専用** スキル。LINE オープンチャットの URL や誘導文を**カルーセルには絶対に組み込まない**。

## TikTok カルーセルでの厳格ルール

- カルーセル本文（台本）: LINE OC URL 一切入れない
- カルーセルキャプション: LINE OC URL 一切入れない
- 1枚目〜最終枚: LINE OC URL 一切入れない

理由:

- TikTok 内で完結する設計が同プラットフォームでの伸びに効く
- 外部リンク誘導は TikTok のアルゴリズム上、表示優先度を下げる傾向
- LINE OC 誘導は **テキスト媒体（Threads / Note）に集中させる方針**

## Threads / Note への誘導

LINE OC 誘導が必要なテーマの場合は、別途 `bb-note-threads` スキルを起動する:

```
/bb-note-threads "タイトル"
```

`bb-note-threads` は Threads 投稿（要点）と Note 記事（深掘り）を生成し、両方の末尾に LINE OC 誘導を完成形 URL 付きで埋め込む。動線設計:

```
TikTok カルーセル（contents-fullmake）        ← LINE OC URL 入れない
   （プロフからフォロー / Threads アカへ流入）
        ↓
Threads 投稿（bb-note-threads）              ← LINE OC URL 埋め込み
   （Note URL を辿る）
        ↓
Note 記事（bb-note-threads）                  ← LINE OC URL 埋め込み（フル版）
        ↓
LINE オープンチャット
「サイエンスベースフィットネス@Brain Bulking」
```

## LINE OC 情報（参考のみ）

| 項目 | 値 |
|---|---|
| チャット名 | サイエンスベースフィットネス@Brain Bulking |
| URL | `https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw` |
| コンセプト | 京大院生と薬剤師が、日本最先端を本気で目指す、完全無料のフィットネス × ヘルスケアコミュニティ |

詳細は `bb-note-threads/references/line-oc-templates.md` を参照。

## 違反検知

contents-fullmake で生成された出力に LINE OC URL（`line.me/ti/g2/`）が混入していた場合、Phase 4 Notion 保存前に検出して中断する。混入箇所を削除してから保存する。
