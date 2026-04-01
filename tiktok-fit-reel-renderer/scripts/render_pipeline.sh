#!/bin/bash
#
# リール動画レンダリング パイプライン
#
# Usage:
#   ./render_pipeline.sh <script.md> [--speaker 13] [--output output.mp4]
#
# Flow:
#   1. 台本パース → slides.json
#   2. VOICEVOX音声生成 → public/audio/
#   3. Remotionレンダリング → MP4
#

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="${SKILL_DIR}/scripts"
PROJECT_DIR="${SKILL_DIR}/remotion-project"

# Defaults
SPEAKER=13
OUTPUT=""
SCRIPT_FILE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --speaker) SPEAKER="$2"; shift 2 ;;
    --output|-o) OUTPUT="$2"; shift 2 ;;
    *) SCRIPT_FILE="$1"; shift ;;
  esac
done

if [[ -z "$SCRIPT_FILE" ]]; then
  echo "Usage: $0 <script.md> [--speaker 13] [--output output.mp4]"
  exit 1
fi

if [[ ! -f "$SCRIPT_FILE" ]]; then
  echo "Error: Script file not found: $SCRIPT_FILE"
  exit 1
fi

SLIDES_JSON="${PROJECT_DIR}/slides.json"
AUDIO_DIR="${PROJECT_DIR}/public/audio"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [[ -z "$OUTPUT" ]]; then
  BASENAME=$(basename "$SCRIPT_FILE" .md)
  OUTPUT="${SKILL_DIR}/output/${BASENAME}_${TIMESTAMP}.mp4"
fi

mkdir -p "$(dirname "$OUTPUT")"
mkdir -p "$AUDIO_DIR"

echo "=== Reel Render Pipeline ==="
echo "Script: $SCRIPT_FILE"
echo "Speaker: $SPEAKER"
echo "Output: $OUTPUT"
echo ""

# Step 1: Parse script
echo "--- Step 1: Parsing script ---"
python3 "${SCRIPTS_DIR}/parse_script.py" "$SCRIPT_FILE" \
  --output "$SLIDES_JSON"
echo ""

# Step 2: Generate VOICEVOX audio
echo "--- Step 2: Generating VOICEVOX audio ---"
python3 "${SCRIPTS_DIR}/voicevox_tts.py" "$SLIDES_JSON" \
  --speaker "$SPEAKER" \
  --output-dir "$AUDIO_DIR"
echo ""

# Step 3: Install deps if needed
if [[ ! -d "${PROJECT_DIR}/node_modules" ]]; then
  echo "--- Installing Remotion dependencies ---"
  cd "$PROJECT_DIR" && npm install
  echo ""
fi

# Step 4: Render with Remotion
echo "--- Step 3: Rendering video ---"
cd "$PROJECT_DIR"

# Pass slides data as input props
npx remotion render src/index.ts Reel \
  --output "$OUTPUT" \
  --codec h264 \
  --props "$SLIDES_JSON"

echo ""
echo "=== Done ==="
echo "Output: $OUTPUT"

# Calculate total duration
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT" 2>/dev/null || echo "unknown")
echo "Duration: ${DURATION}s"
