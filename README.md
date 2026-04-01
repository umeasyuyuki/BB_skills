# BB_skills

Brain Bulking の TikTok フィード投稿を自動生成する Claude Code スキル集です。
テーマを入力するだけで、台本・キャプション・まとめ表・根拠リンクまで一気に出力します。

---

## 必要なもの

- Mac（Windows 未対応）
- [Claude Code](https://claude.ai/code) がインストール済みであること

---

## セットアップ（初回のみ）

### 1. このリポジトリをダウンロードする

ターミナルを開いて、以下のコマンドを貼り付けて実行してください。

```bash
cd ~/Projects && git clone https://github.com/umeasyuyuki/BB_skills.git
```

> ターミナルの開き方: `Cmd + Space` → `ターミナル` と入力 → Enter

### 2. セットアップスクリプトを実行する

```bash
cd ~/Projects/BB_skills && chmod +x setup.sh && ./setup.sh
```

「セットアップ完了！」と表示されたら成功です。

### 3. Claude Code を再起動する

アプリを一度終了して、再度起動してください。

---

## 使い方

Claude Code を開いて、以下のコマンドを入力するだけです。

### フルフロー（リサーチ → 台本 → 薬機法チェック → Notion保存）

```
/tiktok-fit-feed-orchestrator
```

実行すると、カテゴリとテーマを順番に聞いてきます。

**カテゴリ一覧:**

| カテゴリ | 内容 | 例 |
|---|---|---|
| 比較系 | 〇〇 vs 〇〇 | ホエイ vs カゼイン |
| 成分解説系 | 食品・サプリの成分 | アシュワガンダ、牛乳 |
| エンタメ系 | 固有名詞×フィットネス科学 | ラランド西田の食生活を科学した |
| 誤認訂正系 | 世間の間違いを正す | プロテインは腎臓を悪くする |

---

### 台本だけ作る（素材がすでにある場合）

```
/script-compare テーマ      # 比較系
/script-ingredient テーマ   # 成分解説系
/script-entertainment テーマ # エンタメ系
/script-debunk テーマ       # 誤認訂正系
```

---

## スキル一覧

| スキル名 | 役割 |
|---|---|
| tiktok-fit-feed-orchestrator | 入口。全フローを統合実行 |
| tiktok-fit-research | 科学的根拠・論文の調査 |
| tiktok-fit-post-competitor-analysis | 競合投稿の分析 |
| tiktok-fit-carousel-script | 台本生成（本体） |
| tiktok-fit-compliance-check | 薬機法・表現チェック |
| tiktok-fit-notion-publisher | Notion への保存 |
| tiktok-fit-trend-research | トレンド調査 |
| tiktok-fit-insta-single | 1枚まとめ画像の生成 |
| tiktok-fit-slide-image-generator | スライド画像の一括生成 |
| tiktok-fit-reel-renderer | リール動画のレンダリング |
| tiktok-fit-skill-builder | 新スキルの設計 |
| tiktok-notion-analyzer | TikTok 投稿の分析 |

---

## Notion 連携について

Notion への自動保存を使うには、Claude Code の MCP 設定に Notion Integration トークンを追加する必要があります。
設定方法は別途共有します。

---

## 更新する方法

スキルが更新されたら、以下のコマンドで最新版に同期できます。

```bash
cd ~/Projects/BB_skills && git pull
```
