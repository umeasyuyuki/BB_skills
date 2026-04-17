#!/bin/bash
# check_skill_size.sh
# SKILL.md と references/*.md の行数・バイト数が上限を超えていないかチェック。
# 全 skill 横断で実行（引数なし）or 特定 skill のみ実行（引数 skill 名）。
#
# 使い方:
#   ./scripts/check_skill_size.sh                  # 全 skill チェック
#   ./scripts/check_skill_size.sh contents-fullmake # 単一 skill チェック
#
# 上限:
#   SKILL.md           : 250 行 / 12 KB
#   references/*.md    : 500 行 / 30 KB（プレイブック系を考慮）

set -e

SKILL_MAX_LINES=250
SKILL_MAX_BYTES=12288    # 12 KB

REF_MAX_LINES=500
REF_MAX_BYTES=30720      # 30 KB

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"

errors=0
warnings=0

check_file() {
    local file="$1"
    local max_lines="$2"
    local max_bytes="$3"
    local rel_path="${file#$REPO_ROOT/}"

    if [ ! -f "$file" ]; then
        return
    fi

    local lines bytes
    lines=$(wc -l < "$file" | tr -d ' ')
    bytes=$(wc -c < "$file" | tr -d ' ')

    local line_pct=$((lines * 100 / max_lines))
    local byte_pct=$((bytes * 100 / max_bytes))

    if [ "$lines" -gt "$max_lines" ] || [ "$bytes" -gt "$max_bytes" ]; then
        echo "❌ $rel_path"
        echo "   ${lines}行 / ${bytes}バイト（上限: ${max_lines}行 / ${max_bytes}バイト）"
        echo "   → references/ への切り出しを検討してください"
        errors=$((errors + 1))
    elif [ "$line_pct" -ge 90 ] || [ "$byte_pct" -ge 90 ]; then
        echo "⚠️  $rel_path"
        echo "   ${lines}行 / ${bytes}バイト（上限の ${line_pct}% / ${byte_pct}%）"
        echo "   → 上限が近い。次の改修で切り出し検討を推奨"
        warnings=$((warnings + 1))
    else
        echo "✅ $rel_path（${lines}行 / ${bytes}バイト）"
    fi
}

check_skill() {
    local skill_dir="$1"
    local skill_name
    skill_name=$(basename "$skill_dir")

    echo ""
    echo "=== $skill_name ==="

    # SKILL.md チェック
    check_file "$skill_dir/SKILL.md" "$SKILL_MAX_LINES" "$SKILL_MAX_BYTES"

    # references/*.md チェック
    if [ -d "$skill_dir/references" ]; then
        for ref in "$skill_dir/references"/*.md; do
            [ -f "$ref" ] && check_file "$ref" "$REF_MAX_LINES" "$REF_MAX_BYTES"
        done
    fi
}

cd "$REPO_ROOT"

if [ -n "$TARGET" ]; then
    if [ ! -d "$TARGET" ]; then
        echo "Error: skill directory not found: $TARGET"
        exit 1
    fi
    check_skill "$TARGET"
else
    # 全 skill 横断
    for d in */; do
        skill_dir="${d%/}"
        # SKILL.md があるディレクトリのみ対象
        if [ -f "$skill_dir/SKILL.md" ]; then
            check_skill "$skill_dir"
        fi
    done
fi

echo ""
echo "=== 集計 ==="
echo "❌ エラー: ${errors} 件（上限超過）"
echo "⚠️  警告: ${warnings} 件（上限の 90% 以上）"

if [ "$errors" -gt 0 ]; then
    exit 1
fi
exit 0
