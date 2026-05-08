#!/bin/bash

# BB_skills セットアップスクリプト
# Claude Code に Brain Bulking の現役スキルだけを登録します

SKILLS_DIR="$HOME/.claude/skills"
BB_SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)"

ACTIVE_SKILLS=(
  "tiktok-speed"
  "bb-note-threads"
  "substack-fit-writer"
)

contains_skill() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    if [ "$item" = "$needle" ]; then
      return 0
    fi
  done
  return 1
}

echo "BB_skills のセットアップを開始します..."
echo ""

# ~/.claude/skills/ ディレクトリが存在しない場合は作成
if [ ! -d "$SKILLS_DIR" ]; then
  mkdir -p "$SKILLS_DIR"
  echo "スキルフォルダを作成しました: $SKILLS_DIR"
fi

# このリポジトリ由来の古い symlink を整理する
PRUNE=0
for link_path in "$SKILLS_DIR"/*; do
  [ -L "$link_path" ] || continue

  skill_name=$(basename "$link_path")
  target=$(readlink "$link_path")

  case "$target" in
    "$BB_SKILLS_DIR"/*)
      if ! contains_skill "$skill_name" "${ACTIVE_SKILLS[@]}"; then
        rm "$link_path"
        echo "整理済み（旧/非現役スキル登録を解除）: $skill_name"
        PRUNE=$((PRUNE + 1))
      fi
      ;;
  esac
done

# 現役スキルフォルダをシンボリックリンクで登録
SUCCESS=0
SKIP=0
MISSING=0

for skill_name in "${ACTIVE_SKILLS[@]}"; do
  skill_path="$BB_SKILLS_DIR/$skill_name"
  link_path="$SKILLS_DIR/$skill_name"

  if [ ! -f "$skill_path/SKILL.md" ]; then
    echo "未登録（SKILL.md が見つかりません）: $skill_name"
    MISSING=$((MISSING + 1))
    continue
  fi

  # すでに同じ場所へ登録済みの場合はスキップ。
  # 別の場所を指す古い symlink は張り替える。
  if [ -e "$link_path" ]; then
    if [ -L "$link_path" ]; then
      current_target=$(readlink "$link_path")
      expected_target="$skill_path/"
      if [ "$current_target" = "$expected_target" ] || [ "$current_target" = "$skill_path" ]; then
        echo "スキップ（登録済み）: $skill_name"
        SKIP=$((SKIP + 1))
        continue
      fi

      rm "$link_path"
      echo "張り替え（旧パス -> 新パス）: $skill_name"
    else
      echo "未登録（同名の通常ファイル/ディレクトリが存在）: $skill_name"
      MISSING=$((MISSING + 1))
      continue
    fi
  fi

  ln -s "$skill_path/" "$link_path"
  echo "登録完了: $skill_name"
  SUCCESS=$((SUCCESS + 1))
done

echo ""
echo "========================================="
echo "セットアップ完了！"
echo "  新規登録: ${SUCCESS}個"
echo "  スキップ: ${SKIP}個（登録済み）"
echo "  旧登録解除: ${PRUNE}個"
echo "  未登録: ${MISSING}個"
echo "========================================="
echo ""
echo "Claude Code を再起動して、スキルが使えるか確認してください。"
echo "使い方は README.md を参照してください。"
