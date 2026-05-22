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
        excel_path = config.get('path_config', {}).get('excel_path', '/mnt/e/电影管理.xlsx')

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

    if args.interactive:
        print("交互模式暂未实现，请手动处理。")
        print("建议：保留文件较大的版本，删除较小者。")


if __name__ == '__main__':
    main()
