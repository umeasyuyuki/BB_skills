# BB Weekly Status

更新日: 2026-04-27

## 今週のフォーカス

1. skill 群を `contents-fullmake` 中心に整理する。
2. BB_skills を BB 全体管理 repo に拡張する。
3. 進捗・戦略・マネタイズ・システム設計の置き場を作る。

## 現在の状態

| 領域 | 状態 | メモ |
|---|---|---|
| 投稿制作 | 稼働中 | 入口は `contents-fullmake` に集約 |
| 事業戦略 | 整備中 | 入口として `bb-business-strategist` を追加 |
| リール動画 | 保留 / 維持 | `tiktok-fit-reel-renderer` は残すが実行パス要修正 |
| リサーチ | 低頻度 | `fitness-trend-researcher` は optional |
| skill 管理 | 整理中 | archive 移動を開始 |
| 収益化 | 設計フェーズ | BB Checker / affiliate / community を docs 化する |
| システム開発 | 未着手 | BB Checker が最有力候補 |

## 決定事項

| 日付 | 決定 | 理由 |
|---|---|---|
| 2026-04-27 | 現役 skill 入口を `contents-fullmake` に絞る | 実運用上ほぼこれしか使っていないため |
| 2026-04-27 | 事業戦略・マネタイズ壁打ち用に `bb-business-strategist` を追加 | BB全体管理repoへ拡張するため |
| 2026-04-27 | リール動画作成は別系統で残す | 将来的に動画展開が必要になるため |
| 2026-04-27 | 非現役 skill は削除ではなく archive へ退避 | 復活可能性と履歴を残すため |

## ブロッカー / 要確認

- `tiktok-fit-reel-renderer/SKILL.md` の実行パスが repo 内実装とズレている。
- `node_modules` が git 管理下に大量に入っている。
- `contents-fullmake` 周辺に既存の未コミット変更が多い。
- `fitness-trend-researcher` を今後も使うか決める必要がある。

## 次アクション

1. `.gitignore` と `setup.sh` を整理後の構成に合わせる。
2. README を現役 skill 中心に更新する。
3. `archive/skills/` に非現役 skill を退避する。
4. BB Checker のロードマップを `docs/monetization/` に具体化する。
5. reel renderer の実行パスを修正する。
6. `bb-business-strategist` を使って、有料コミュニティとBB Checkerの初期オファーを壁打ちする。
