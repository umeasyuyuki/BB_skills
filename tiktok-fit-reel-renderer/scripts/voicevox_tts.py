#!/usr/bin/env python3
"""
VOICEVOX音声合成スクリプト。
slides.json からナレーション文を読み取り、スライドごとに .wav を生成する。
音声の長さに基づいて durationInFrames を自動計算する。

Usage:
    python3 voicevox_tts.py <slides.json> [--speaker 13] [--output-dir public/audio]

Prerequisites:
    - VOICEVOX engine running on localhost:50021
    - Start with: open /Applications/VOICEVOX.app
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


VOICEVOX_URL = "http://127.0.0.1:50021"
DEFAULT_SPEAKER = 13  # 青山龍星 (male, good for fitness)
FPS = 30
BUFFER_FRAMES = 15  # 0.5s buffer after audio ends
MIN_DURATION_SEC = 3.0
MAX_DURATION_SEC = 8.0
SPEED_SCALE_MIN = 0.8
SPEED_SCALE_MAX = 1.4


def check_voicevox():
    """VOICEVOXエンジンの起動確認"""
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/version")
        with urllib.request.urlopen(req, timeout=3) as resp:
            version = resp.read().decode()
            print(f"VOICEVOX engine: {version}")
            return True
    except (urllib.error.URLError, TimeoutError):
        return False


def wait_for_voicevox(max_wait: int = 30):
    """VOICEVOXの起動を待つ"""
    print("Waiting for VOICEVOX engine...")
    for i in range(max_wait):
        if check_voicevox():
            return True
        time.sleep(1)
    return False


def get_audio_query(text: str, speaker: int, speed_scale: float = 1.0) -> dict:
    """音声合成用クエリを取得"""
    encoded_text = urllib.parse.quote(text)
    url = f"{VOICEVOX_URL}/audio_query?text={encoded_text}&speaker={speaker}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as resp:
        query = json.loads(resp.read())
    query["speedScale"] = speed_scale
    return query


def synthesize(query: dict, speaker: int) -> bytes:
    """音声合成を実行"""
    url = f"{VOICEVOX_URL}/synthesis?speaker={speaker}"
    data = json.dumps(query).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def get_wav_duration(wav_path: str) -> float:
    """ffprobeでWAVファイルの長さを取得"""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            wav_path,
        ],
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def generate_slide_audio(
    narration: str,
    output_path: Path,
    speaker: int,
) -> float:
    """
    スライドの音声を生成。
    目標: MIN_DURATION_SEC 〜 MAX_DURATION_SEC に収まるよう速度を自動調整。
    Returns: audio duration in seconds
    """
    # 1st pass: normal speed
    query = get_audio_query(narration, speaker, speed_scale=1.0)
    wav_data = synthesize(query, speaker)
    output_path.write_bytes(wav_data)
    duration = get_wav_duration(str(output_path))

    # Speed adjustment if needed
    if duration < MIN_DURATION_SEC or duration > MAX_DURATION_SEC:
        # Calculate target speed
        target = (MIN_DURATION_SEC + MAX_DURATION_SEC) / 2
        new_speed = duration / target
        new_speed = max(SPEED_SCALE_MIN, min(SPEED_SCALE_MAX, new_speed))

        query = get_audio_query(narration, speaker, speed_scale=new_speed)
        wav_data = synthesize(query, speaker)
        output_path.write_bytes(wav_data)
        duration = get_wav_duration(str(output_path))
        print(f"  Speed adjusted: {new_speed:.2f}x → {duration:.1f}s")

    return duration


def main():
    parser = argparse.ArgumentParser(description="Generate VOICEVOX audio for slides")
    parser.add_argument("input", help="Path to slides.json")
    parser.add_argument("--speaker", type=int, default=DEFAULT_SPEAKER, help="VOICEVOX speaker ID")
    parser.add_argument("--output-dir", default="remotion-project/public/audio", help="Output audio directory")
    parser.add_argument("--skip-voicevox-check", action="store_true")
    args = parser.parse_args()

    # Load slides
    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    slides = data["slides"]

    # Check VOICEVOX
    if not args.skip_voicevox_check:
        if not check_voicevox():
            print("VOICEVOX not running. Starting...")
            subprocess.Popen(["open", "/Applications/VOICEVOX.app"])
            if not wait_for_voicevox():
                print("Error: VOICEVOX failed to start", file=sys.stderr)
                sys.exit(1)

    # Create output dir
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate audio for each slide
    total_duration = 0
    for slide in slides:
        narration = slide.get("narration", "")
        if not narration:
            print(f"  Slide {slide['index']}: No narration, skipping audio")
            continue

        audio_filename = f"slide_{slide['index']:02d}.wav"
        audio_path = output_dir / audio_filename
        print(f"  Slide {slide['index']}: Generating audio...")

        duration = generate_slide_audio(narration, audio_path, args.speaker)
        total_duration += duration

        # Update slide with audio info
        slide["audioFile"] = f"audio/{audio_filename}"
        slide["audioDurationSec"] = round(duration, 2)
        slide["durationInFrames"] = int(duration * FPS) + BUFFER_FRAMES

        print(f"  Slide {slide['index']}: {duration:.1f}s → {slide['durationInFrames']} frames")

    # Save updated slides
    input_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTotal duration: {total_duration:.1f}s ({len(slides)} slides)")
    print(f"Updated: {input_path}")


if __name__ == "__main__":
    main()
