#!/usr/bin/env python3
"""Extract video metadata using ffprobe and auto-tag movies.

Requires ffmpeg installed: sudo apt install ffmpeg -y

Tags added:
  - Resolution: 4K, 1080p, 720p based on video width
  - HDR: if color_space is bt2020
  - 60fps: if frame rate is close to 60
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.excel_manager import ExcelManager
from core.config_manager import ConfigManager


def probe_video(file_path: str) -> dict | None:
    """Run ffprobe and return video stream info."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_streams', '-select_streams', 'v:0', file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        return streams[0] if streams else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def classify_resolution(width: int) -> str:
    """Map width to resolution tag."""
    if width >= 3840:
        return '4K'
    elif width >= 1920:
        return '1080p'
    elif width >= 1280:
        return '720p'
    return ''


def extract_frame_rate(stream: dict) -> float:
    """Extract frame rate from r_frame_rate string like '60000/1001'."""
    fps_str = stream.get('r_frame_rate', '0/1')
    try:
        num, den = fps_str.split('/')
        return float(num) / float(den)
    except (ValueError, ZeroDivisionError):
        return 0.0


def main():
    parser = argparse.ArgumentParser(description='Extract video metadata and auto-tag')
    parser.add_argument('--excel', help='Path to Excel file')
    parser.add_argument('--apply', action='store_true', help='Write tags to Excel')
    parser.add_argument('--limit', type=int, default=0, help='Limit to N movies')
    args = parser.parse_args()

    if args.excel:
        excel_path = args.excel
    else:
        config = ConfigManager()
        excel_path = config.get('path_config', {}).get('excel_path', './电影管理.xlsx')

    excel = ExcelManager(excel_path)
    records = excel.get_all_movies()

    if args.limit:
        records = records[:args.limit]

    print(f"📊 扫描 {len(records)} 部影片的元数据...")

    updates = {}
    tags_added: dict[str, int] = {}
    total = len(records)

    for i, r in enumerate(records):
        file_path = r.get('file_path', '')
        movie_id = r.get('movie_id', '')

        if not file_path or not os.path.exists(file_path):
            continue

        if (i + 1) % 50 == 0:
            print(f"  ... {i + 1}/{total}")

        stream = probe_video(file_path)
        if not stream:
            continue

        width = stream.get('width', 0)
        height = stream.get('height', 0)
        fps = extract_frame_rate(stream)
        codec = stream.get('codec_name', '')
        color_space = stream.get('color_space', '')

        new_tags = []
        res_tag = classify_resolution(width)
        if res_tag:
            new_tags.append(res_tag)

        if fps >= 55:
            new_tags.append('60fps')

        if codec in ('hevc', 'h265', 'av1'):
            new_tags.append(codec.upper())

        if 'bt2020' in str(color_space).lower():
            new_tags.append('HDR')

        if new_tags:
            existing_tags = [t.strip() for t in r.get('tags', '').split(',') if t.strip()]
            added = [t for t in new_tags if t not in existing_tags]
            if added:
                updates[movie_id] = ','.join(existing_tags + added)
                for t in added:
                    tags_added[t] = tags_added.get(t, 0) + 1

    print(f"\n📊 结果:")
    for tag, count in sorted(tags_added.items()):
        print(f"  {tag}: {count} 部")

    if not updates:
        print("  (无新标签需要添加)")
        return

    if args.apply:
        print(f"\n✏️  写入 {len(updates)} 条更新...")
        # Batch update: modify sheet directly, save once
        sheet = excel.sheet
        for row in sheet.iter_rows(min_row=2):
            movie_id = str(row[0].value or '')
            if movie_id in updates:
                tags_col = row[10]  # column K (0-indexed: 10)
                tags_col.value = updates[movie_id]

        excel.save()
        print("✅ 写入完成")
    else:
        print(f"\n💡 使用 --apply 参数写入 {len(updates)} 条更新 (dry-run)")


if __name__ == '__main__':
    main()
