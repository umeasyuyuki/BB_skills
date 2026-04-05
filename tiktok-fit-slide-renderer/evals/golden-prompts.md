# Golden Prompts（tiktok-fit-slide-renderer）

品質検証用のプロンプト集。

## テストケース1: 元部活ランキング（11枚カルーセル）

サンプル台本: `evals/sample_motobukatsu_test.md`

```bash
# このサンプルを data/pipeline/drafts/ にコピーしてテスト
cp evals/sample_motobukatsu_test.md data/pipeline/drafts/motobukatsu_test.md
python3 scripts/render_slides.py --parse --input data/pipeline/drafts/motobukatsu_test.md
python3 scripts/render_slides.py --render --manifest data/pipeline/drafts/motobukatsu_test_render_manifest.yaml
```

期待される動作:
- 11枚のPNGが生成される
- 1位柔道部のスライドで「1位 柔道部」が赤・大サイズで表示される
- 握力「70kg」が自動で青色になる
- まとめ表スライド（スライド10）が表形式で正しく描画される
- CTAスライドで「部活歴(年) × ベンチMAX(kg) = ?」が表示される

## テストケース2: 単一スライドの微調整

ユーザー入力例:
- 「3枚目のメインを中サイズに変えて」
- 「スライド5の赤を黒に変更」
- 「補足レイヤーを全部skipして」

期待される動作:
- Editツールでmanifest.yamlを直接変更
- feedback_log.jsonlに変更が記録される
- 「変更完了しました」と報告

## テストケース3: 空レイヤーのバリデーション

期待される動作:
- 空レイヤーがある場合、WARNINGが表示される
- レンダリングは続行可能
