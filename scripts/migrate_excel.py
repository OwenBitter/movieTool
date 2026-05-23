#!/usr/bin/env python3
"""Migrate 电影管理.xlsx from old format (English headers, 13 cols) to new format (Chinese headers, 11 cols).

Changes:
- Remove director and genre columns (both empty)
- Rename updated_at → downloaded_at, populate with file mtime
- Convert all headers to Chinese
- Add rating (default 0) and tags (default empty)
"""

import os
import sys
import shutil
from datetime import datetime
from openpyxl import Workbook, load_workbook

# OLD headers (what exists now)
OLD_HEADERS = [
    'movie_id', 'file_name', 'movie_name', 'actor', 'director',
    'release_year', 'genre', 'rating', 'file_size', 'file_path',
    'status', 'tags', 'updated_at'
]

# NEW headers (internal keys)
NEW_HEADERS = [
    'movie_id', 'file_name', 'movie_name', 'actor',
    'release_year', 'rating', 'file_size', 'file_path',
    'status', 'tags', 'downloaded_at',
]

# Chinese display labels
HEADER_LABELS = {
    'movie_id': '编号',
    'file_name': '文件名',
    'movie_name': '影片名称',
    'actor': '演员',
    'release_year': '发行年份',
    'rating': '评分',
    'file_size': '文件大小',
    'file_path': '文件路径',
    'status': '状态',
    'tags': '标签',
    'downloaded_at': '下载时间',
}

# Column mapping: old index → new key (None = skip)
OLD_TO_NEW = [
    'movie_id',      # 0
    'file_name',     # 1
    'movie_name',    # 2
    'actor',         # 3
    None,            # 4: director → SKIP
    'release_year',  # 5
    None,            # 6: genre → SKIP
    'rating',        # 7
    'file_size',     # 8
    'file_path',     # 9
    'status',        # 10
    'tags',          # 11
    'downloaded_at', # 12: updated_at → downloaded_at
]


def get_file_mtime(file_path):
    """Get file modification time as download time proxy."""
    try:
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    except OSError:
        pass
    return ''


def migrate(src_path, dst_path=None):
    """Migrate Excel from old to new format."""
    if dst_path is None:
        dst_path = src_path

    print(f"Reading: {src_path}")
    wb = load_workbook(src_path)
    sheet = wb.active
    print(f"  Rows: {sheet.max_row}, Cols: {sheet.max_column}")

    # Validate old format
    old_headers = [str(cell.value).strip() if cell.value else '' for cell in sheet[1]]
    print(f"  Old headers: {old_headers}")

    # Read all data
    rows = []
    stats = {'total': 0, 'dir_empty': 0, 'genre_empty': 0, 'time_updated': 0}

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        stats['total'] += 1

        new_row = {}
        for old_idx, new_key in enumerate(OLD_TO_NEW):
            if new_key is None:
                continue
            val = row[old_idx] if old_idx < len(row) else None
            val = str(val).strip() if val is not None else ''

            # Special: updated_at → downloaded_at: use file mtime
            if new_key == 'downloaded_at':
                file_path = str(row[9]).strip() if len(row) > 9 and row[9] else ''
                mtime = get_file_mtime(file_path)
                if mtime:
                    new_row[new_key] = mtime
                    stats['time_updated'] += 1
                else:
                    new_row[new_key] = val  # keep old value as fallback
            else:
                new_row[new_key] = val

        # Ensure rating is valid (default 0 = unrated)
        if not new_row.get('rating') or new_row['rating'] == '':
            new_row['rating'] = '0'

        rows.append(new_row)

    # Create new workbook
    new_wb = Workbook()
    new_sheet = new_wb.active
    new_sheet.title = 'Movies'

    # Write Chinese header row
    chinese_headers = [HEADER_LABELS[h] for h in NEW_HEADERS]
    new_sheet.append(chinese_headers)
    print(f"  New headers: {chinese_headers}")

    # Write data rows
    for new_row in rows:
        sheet_row = [new_row.get(key, '') for key in NEW_HEADERS]
        new_sheet.append(sheet_row)

    # Save
    new_wb.save(dst_path)
    print(f"\nSaved: {dst_path}")
    print(f"  Records: {stats['total']}")
    print(f"  Download times set from file mtime: {stats['time_updated']}")
    print(f"  Skipped columns: director, genre")
    return True


if __name__ == '__main__':
    src = './电影管理.xlsx'
    
    # Backup first
    backup_dir = '/mnt/e/电影备份'
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'{timestamp}_电影管理_迁移前备份.xlsx')
    
    # Work on a copy in /tmp to avoid WSL permission issues
    tmp_path = '/tmp/电影管理_migrate.xlsx'
    shutil.copy2(src, tmp_path)
    shutil.copy2(src, backup_path)
    print(f"Backup saved: {backup_path}")
    
    # Migrate
    tmp_out = '/tmp/电影管理_new.xlsx'
    success = migrate(tmp_path, tmp_out)
    
    if success:
        # Copy back
        shutil.copy2(tmp_out, src)
        print(f"\n迁移完成! 文件已更新: {src}")
        print(f"备份文件: {backup_path}")
