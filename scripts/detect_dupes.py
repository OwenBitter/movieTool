#!/usr/bin/env python3
"""Detect duplicate movies by cleaned code name.

Finds movies with the same cleaned code (after stripping URL prefixes and
quality suffixes like -UC, -HD, -C) and reports them as duplicates.
"""

import argparse
import re
import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.excel_manager import ExcelManager
from core.config_manager import ConfigManager


def extract_code(filename: str) -> str:
    """Extract and clean JAV code from filename.

    Strips URL prefixes (xxx.com@) and quality suffixes (-UC, -HD, -C).
    Returns the normalized code for duplicate detection.
    """
    # Remove URL prefix
    code = re.sub(r'^[a-zA-Z0-9.-]+\.(com|net|org|cn|cc|to)@', '', filename)

    # Remove quality suffixes
    code = re.sub(r'-(UC|HD|C|FHD|4K|SD|RAW)$', '', code, flags=re.IGNORECASE)

    # Remove common suffixes
    code = re.sub(r'\.(mp4|mkv|avi|wmv|ts)$', '', code, flags=re.IGNORECASE)

    # Remove trailing dots and dashes
    code = code.strip().rstrip('.- ').strip()

    return code


def main():
    parser = argparse.ArgumentParser(description='Detect duplicate movies by code')
    parser.add_argument('--excel', help='Path to Excel file (uses config if not set)')
    parser.add_argument('--interactive', action='store_true',
                        help='Interactive mode: choose which duplicate to keep')
    args = parser.parse_args()

    if args.excel:
        excel_path = args.excel
    else:
        config = ConfigManager()
        excel_path = config.get('path_config', {}).get('excel_path', './电影管理.xlsx')

    excel = ExcelManager(excel_path)
    records = excel.get_all_movies()

    # Group by cleaned code
    code_map: dict[str, list[dict]] = {}
    for r in records:
        movie_name = r.get('movie_name', '') or r.get('file_name', '')
        code = extract_code(movie_name)
        if code:
            code_map.setdefault(code, []).append(r)

    # Find duplicates (code with >1 entry)
    dupes = {code: entries for code, entries in code_map.items() if len(entries) > 1}

    if not dupes:
        print("✅ 没有发现重复影片！")
        return

    print(f"🔍 发现 {len(dupes)} 组重复影片 (共 {sum(len(v) for v in dupes.values())} 部):\n")

    for code, entries in sorted(dupes.items()):
        print(f"  📼 {code} ({len(entries)} 部)")
        for e in entries:
            file_name = e.get('file_name', '?')
            file_size = e.get('file_size', '?')
            file_path = e.get('file_path', '?')
            dl_time = e.get('downloaded_at', '?')
            rating = e.get('rating', '0')
            print(f"     ├─ {file_name}")
            print(f"     │  📦 {file_size}  ⭐ {rating}  🕐 {dl_time}")
            print(f"     │  📁 {file_path}")
        print()

    if args.interactive and dupes:
        total_deleted = _interactive_dedup(dupes, excel)
        excel.save()
        print(f"\n✅ 已删除 {total_deleted} 个重复文件。")


def _interactive_dedup(dupes: dict, excel) -> int:
    """Interactive mode: user chooses which duplicate to keep per group."""
    deleted = 0
    for code, entries in sorted(dupes.items()):
        print(f"\n{'='*60}")
        print(f"📼 番号: {code} ({len(entries)} 个重复)")
        print(f"{'='*60}")
        for i, e in enumerate(entries, 1):
            file_name = e.get('file_name', '?')
            file_size = e.get('file_size', '?')
            file_path = e.get('file_path', '?')
            rating = e.get('rating', '0')
            status = e.get('status', '?')
            tags = e.get('tags', '')
            print(f"  [{i}] {file_name}")
            print(f"      大小: {file_size} | 评分: {rating} | 状态: {status}")
            if tags:
                print(f"      标签: {tags}")
            print(f"      路径: {file_path}")

        print(f"\n  保留哪个？输入编号 1-{len(entries)}，或 s=跳过: ", end='')
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消。")
            break

        if choice == 's' or not choice:
            print("  ⏭ 已跳过。")
            continue

        try:
            keep_idx = int(choice) - 1
            if keep_idx < 0 or keep_idx >= len(entries):
                print("  ❌ 无效编号，已跳过。")
                continue
        except ValueError:
            print("  ❌ 无效输入，已跳过。")
            continue

        # Delete all except the chosen one
        for i, e in enumerate(entries):
            if i == keep_idx:
                continue
            fp = e.get('file_path', '')
            mid = e.get('movie_id', '')
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                    print(f"  🗑 已删除文件: {os.path.basename(fp)}")
                except OSError as exc:
                    print(f"  ❌ 删除文件失败: {exc}")
            if mid:
                excel.delete_movie(mid)
                deleted += 1

    return deleted


if __name__ == '__main__':
    main()
