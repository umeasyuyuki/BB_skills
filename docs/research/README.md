# Research Operations

作成日: 2026-04-27

## 現状

リサーチ skill は以前より使用頻度が下がっている。

今後は毎回 skill として重く回すより、必要な時だけ以下を使う。

- `contents-fullmake` 内の research component
- optional な `fitness-trend-researcher`
- `Research_report/` の過去レポート

## 方針

1. 投稿テーマが明確な時は `contents-fullmake` の内部調査で足りる。
2. 市場・トレンドの棚卸しが必要な時だけ `fitness-trend-researcher` を使う。
3. 旧 `tiktok-fit-trend-research` は archive 済み。復活は原則しない。
4. 調査結果は `Research_report/` に残す。

## Optional Skill

`fitness-trend-researcher` を Claude Code に登録したい場合:

```bash
INCLUDE_OPTIONAL_SKILLS=1 ./setup.sh
```

通常セットアップでは登録しない。
