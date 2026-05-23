#!/usr/bin/env python3
"""Batch pre-generate video thumbnails for all movies in Excel.

Uses ffmpeg to extract a single frame per video, cached to a directory.
Skips already-generated thumbnails that are newer than their source video.
Runs up to 4 ffmpeg jobs concurrently via ThreadPoolExecutor.

Usage:
    cd /mnt/e/tools/movieTool
    python3 scripts/pregen_thumbs.py                # dry-run: list what would happen
    python3 scripts/pregen_thumbs.py --generate      # actually generate thumbnails
    python3 scripts/pregen_thumbs.py --cache-dir /mnt/e/缩略图 --generate
"""

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.excel_manager import ExcelManager


def check_requirements():
    """Verify ffmpeg and ffprobe are available."""
    for cmd in ('ffmpeg', 'ffprobe'):
        try:
            subprocess.run([cmd, '-version'], capture_output=True, timeout=5, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f'❌ {cmd} 未找到或不可用，请先安装 ffmpeg。')
            sys.exit(1)


def get_duration(file_path: str) -> float:
    """Get video duration in seconds via ffprobe. Returns 0 on failure."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', file_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return 0.0
        import json
        data = json.loads(result.stdout)
        return float(data.get('format', {}).get('duration', 0))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, FileNotFoundError):
        return 0.0


def generate_thumb(file_path: str, cache_path: str) -> str:
    """Generate one thumbnail. Returns 'generated', 'skipped', or 'error'."""
    # Skip if thumbnail already exists and is newer than source
    if os.path.exists(cache_path):
        try:
            src_mtime = os.path.getmtime(file_path)
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime >= src_mtime:
                return 'skipped'
        except OSError:
            pass

    # Determine seek point: 5 minutes or half duration for short videos
    duration = get_duration(file_path)
    seek_sec = 300  # default 5 minutes
    if 0 < duration < 300:
        seek_sec = int(duration / 2)

    try:
        subprocess.run(
            ['ffmpeg', '-ss', str(seek_sec), '-i', file_path,
             '-vframes', '1', '-q:v', '8', cache_path, '-y'],
            capture_output=True, timeout=15,
        )
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            return 'generated'
        return 'error'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 'error'


def main():
    parser = argparse.ArgumentParser(description='Batch pre-generate video thumbnails')
    parser.add_argument('--generate', action='store_true',
                        help='Actually generate thumbnails (default: dry-run)')
    parser.add_argument('--cache-dir', default=None,
                        help='Thumbnail cache directory (default: from config or /mnt/e/缩略图/)')
    parser.add_argument('--excel', default=None,
                        help='Path to Excel file (default: from config)')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of concurrent ffmpeg workers (default: 4)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit to N movies (0 = all)')
    args = parser.parse_args()

    check_requirements()

    # Load config
    if args.excel:
        excel_path = args.excel
    else:
        config = ConfigManager()
        excel_path = config.get('path_config', {}).get('excel_path', './电影管理.xlsx')

    cache_dir = args.cache_dir
    if not cache_dir:
        config = ConfigManager()
        cache_dir = config.get('path_config', {}).get('thumb_cache', '/mnt/e/缩略图')

    os.makedirs(cache_dir, exist_ok=True)

    excel = ExcelManager(excel_path)
    records = excel.get_all_movies()
    if args.limit:
        records = records[:args.limit]

    total = len(records)
    print(f'📊 共 {total} 部影片')
    print(f'📁 缩略图目录: {cache_dir}')
    print(f'🔧 并发数: {args.workers}')
    print()

    if not args.generate:
        # Dry-run: count what would happen
        would_gen = 0
        would_skip = 0
        missing_files = 0
        for i, r in enumerate(records):
            if (i + 1) % 100 == 0:
                print(f'  ... 扫描中 {i + 1}/{total}')
            file_path = r.get('file_path', '')
            movie_id = r.get('movie_id', '')
            if not file_path or not os.path.exists(file_path):
                missing_files += 1
                continue
            cache_path = os.path.join(cache_dir, f'{movie_id}.jpg')
            if os.path.exists(cache_path):
                try:
                    if os.path.getmtime(cache_path) >= os.path.getmtime(file_path):
                        would_skip += 1
                        continue
                except OSError:
                    pass
            would_gen += 1

        print(f'📋 预览结果:')
        print(f'   需要生成: {would_gen}')
        print(f'   已缓存:   {would_skip}')
        if missing_files:
            print(f'   文件缺失: {missing_files}')
        print()
        if would_gen > 0:
            print(f'💡 使用 --generate 实际生成缩略图')
        return

    # Generate mode
    tasks = []
    for r in records:
        file_path = r.get('file_path', '')
        movie_id = r.get('movie_id', '')
        if not file_path or not os.path.exists(file_path):
            continue
        cache_path = os.path.join(cache_dir, f'{movie_id}.jpg')
        tasks.append((file_path, cache_path, movie_id))

    generated = 0
    skipped = 0
    errors = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(generate_thumb, fp, cp): (fp, cp, mid)
            for fp, cp, mid in tasks
        }
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result == 'generated':
                generated += 1
            elif result == 'skipped':
                skipped += 1
            else:
                errors += 1
                fp, cp, mid = futures[future]
                print(f'  ⚠️  错误: {mid}')

            if i % 50 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print(f'  ... {i}/{len(tasks)} ({rate:.1f}/s)  生成:{generated}  跳过:{skipped}  错误:{errors}')

    elapsed = time.time() - start_time
    print()
    print(f'✅ 完成! ({elapsed:.1f}s)')
    print(f'   生成: {generated}')
    print(f'   跳过: {skipped}')
    if errors:
        print(f'   错误: {errors}')
    print(f'   目录: {cache_dir}')


if __name__ == '__main__':
    main()
