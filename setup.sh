#!/bin/bash

# BB_skills セットアップスクリプト
# Claude Code にスキルを登録します

SKILLS_DIR="$HOME/.claude/skills"
BB_SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "BB_skills のセットアップを開始します..."
echo ""

# ~/.claude/skills/ ディレクトリが存在しない場合は作成
if [ ! -d "$SKILLS_DIR" ]; then
  mkdir -p "$SKILLS_DIR"
  echo "スキルフォルダを作成しました: $SKILLS_DIR"
fi

# 各スキルフォルダをシンボリックリンクで登録
SUCCESS=0
SKIP=0

for skill_path in "$BB_SKILLS_DIR"/*/; do
  skill_name=$(basename "$skill_path")
  link_path="$SKILLS_DIR/$skill_name"

  # すでに登録済みの場合はスキップ
  if [ -e "$link_path" ]; then
    echo "スキップ（登録済み）: $skill_name"
    SKIP=$((SKIP + 1))
    continue
  fi

  ln -s "$skill_path" "$link_path"
  echo "登録完了: $skill_name"
  SUCCESS=$((SUCCESS + 1))
done

echo ""
echo "========================================="
echo "セットアップ完了！"
echo "  新規登録: ${SUCCESS}個"
echo "  スキップ: ${SKIP}個（登録済み）"
echo "========================================="
echo ""
echo "Claude Code を再起動して、スキルが使えるか確認してください。"
echo "使い方は README.md を参照してください。"
