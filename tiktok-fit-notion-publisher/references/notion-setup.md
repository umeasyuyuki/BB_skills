# Notionセットアップ（ドキュメント保存）

## 環境変数

```bash
export NOTION_API_KEY="secret_xxx"
export NOTION_DATA_SOURCE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# または
export NOTION_DATABASE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## 保存先固定（推奨）

```bash
# このプロジェクト専用の保存先を固定
python3 scripts/notion_target.py --data-source-id "<NEW_DATA_SOURCE_ID>"

# 現在の設定を確認
python3 scripts/notion_target.py --show
```

## 1) パッケージ作成

```bash
python3 scripts/create_document_package.py \
  --title "サイゼリヤの筋トレ飯5選" \
  --theme "サイゼリヤの最強筋トレ飯5選" \
  --workflow picks \
  --research-file /path/research.md \
  --compliance-file /path/check.md \
  --script-file /path/script.md \
  --summary-table-file /path/table.md \
  --references-file /path/references.md
```

## 2) dry-run

```bash
python3 scripts/notion_save_document.py --input data/notion-inbox/saizeriya.json --dry-run
```

## 3) 本保存

```bash
python3 scripts/notion_save_document.py --input data/notion-inbox/saizeriya.json
```

## 4) 一括保存

```bash
python3 scripts/notion_autosave.py --inbox-dir data/notion-inbox
```

## 5) 最短1コマンド保存

```bash
# 最新JSONを自動選択して保存前チェック
python3 scripts/notion_publish.py --dry-run

# 最新JSONを自動選択して保存
python3 scripts/notion_publish.py

# Markdownファイルを指定して保存（台本セクションは自動承認）
python3 scripts/notion_publish.py /path/to/post.md

# 一時的に保存先IDを上書きして保存
python3 scripts/notion_publish.py /path/to/post.md --notion-data-source-id "<OTHER_ID>"
```
