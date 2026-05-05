# 投稿単位競合分析テンプレート

## スナップショット

- platform (tiktok / youtube / instagram / threads / note)
- post_url
- theme_match
- hook_pattern
- structure_pattern
- claim_pattern
- evidence_pattern
- practical_score
- clarity_score
- save_proxy_score
- engagement_proxy（platform 固有指標、下記参照）

### platform 別エンゲージメント指標

| platform | 重視する指標 |
|---|---|
| `tiktok` | 保存数、シェア数、コメント率 |
| `youtube` | 視聴維持率、いいね率、コメント率 |
| `instagram` | 保存数、シェア数、フォロー転換率 |
| `threads` | リポスト数、コメント数、引用数 |
| `note` | スキ（いいね）数、コメント数、購入率（有料記事のみ） |

## 共通パターン

- 多用されるフック
- 多用される結論
- 多用される CTA
- 欠けている情報

### platform 別の構造パターン観点

- `tiktok` / `instagram`: スライド枚数、1 枚目フック、最終枚 CTA
- `youtube`: イントロ尺、本論セクション数、エンドカード設計
- `threads`: 文字数、改行設計、外部リンクの扱い
- `note`: 見出し数、本文字数、有料化境界の設計

## 独自化アイデア

- angle
- competitor_gap
- evidence_anchor
- plain_explanation
- practical_rule

## 台本指示

- opening_recommendation
- content_order（媒体に応じて: slide_order / paragraph_order / heading_order）
- cta_recommendation

### bb-note-threads 連携時の追加指示

threads / note を platform 指定して呼ばれた場合、以下を必ず出力する:

- **threads_specific**: Threads 特有の差別化ポイント（500-700 字内での要点凝縮、Note 案内の自然さ、LINE 直誘導を避けた構成）
- **note_specific**: Note 特有の差別化ポイント（SEO 見出し設計、脚注密度、有料化への耐性）
- **cross_funnel**: Threads → Note の動線で、競合がやっていない補強ポイント
