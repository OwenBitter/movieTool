#!/usr/bin/env python3
"""Auto-tag movies by code prefix — infer manufacturer/genre from JAV code.

Usage:
    cd /mnt/e/tools/movieTool
    python3 scripts/tag_by_code.py          # scan all, preview only
    python3 scripts/tag_by_code.py --apply  # scan + write tags to Excel
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.excel_manager import ExcelManager

# ── Code prefix → type tags ──────────────────────────────────────────────
# Prefixes are matched case-insensitively. Tags are appended (not replaced).
CODE_PREFIX_MAP = {
    # S1
    'SONE':  ['S1', '偶像'],
    'SSIS':  ['S1', '剧情'],
    'SSNI':  ['S1', '剧情'],
    'SOE':   ['S1', '经典'],
    'SNIS':  ['S1', '剧情'],
    'OAE':   ['S1', '写真'],
    # IdeaPocket
    'IPZZ':  ['IdeaPocket', '美少女'],
    'IPX':   ['IdeaPocket', '美少女'],
    'IPZ':   ['IdeaPocket', '美少女'],
    # MOODYZ
    'MIDV':  ['MOODYZ', '巨乳'],
    'MIDE':  ['MOODYZ', '巨乳'],
    'MIAA':  ['MOODYZ', '美少女'],
    'MIDA':  ['MOODYZ', '巨乳'],
    'MIMK':  ['MOODYZ', '漫改'],
    'MIKR':  ['MOODYZ', '企划'],
    # Madonna
    'JUQ':   ['Madonna', '熟女'],
    'JUL':   ['Madonna', '人妻'],
    'JUR':   ['Madonna', '人妻'],
    'URE':   ['Madonna', '漫改'],
    'ACHJ':  ['Madonna', '熟女'],
    # 溜池
    'MEYD':  ['溜池', '人妻'],
    'MDYD':  ['溜池', '人妻'],
    # OPPAI
    'PPPE':  ['OPPAI', '巨乳'],
    'PPPD':  ['OPPAI', '巨乳'],
    # 痴女系
    'DASS':  ['痴女', '硬核'],
    'CJOD':  ['痴女', '巨乳'],
    # SOD
    'STARS': ['SOD', '剧情'],
    'START': ['SOD', '剧情'],
    'SDDE':  ['SOD', '企划'],
    'SDMU':  ['SOD', '企划'],
    'SDJS':  ['SOD', '素人'],
    # kawaii*
    'CAWD':  ['kawaii', '美少女'],
    'KAWD':  ['kawaii', '美少女'],
    # FALENO
    'FSDSS': ['FALENO', '美少女'],
    # 本中
    'HMN':   ['本中', '企划'],
    'HND':   ['本中', '企划'],
    # 其他厂商
    'ABF':   ['写真', '美体'],
    'ABP':   ['PRESTIGE', '美少女'],
    'ABW':   ['PRESTIGE', '美少女'],
    'EBWH':  ['E-BODY', '巨乳'],
    'ROE':   ['Madonna', '熟女'],
    'ROYD':  ['ROYAL', '美少女'],
    'DLDSS': ['DAHLIA', '美少女'],
    'JUFE':  ['Fitch', '巨乳'],
    'WAAA':  ['WANZ', '硬核'],
    'WANZ':  ['WANZ', '硬核'],
    'PRED':  ['PRESTIGE', '美少女'],
    'ADN':   ['ATTACKERS', '剧情'],
    'RBK':   ['ATTACKERS', '剧情'],
    'MEYD':  ['溜池', '人妻'],
    # 无码
    'FC2':   ['无码', '素人'],
    'CARIB': ['无码', '加勒比'],
    '1PONDO':['无码', '一本道'],
    'HEYZO': ['无码'],
    # 其他
    '259LUXU': ['素人', '高画质'],
    # Additional mappings from unmatched analysis
    'BLK':    ['kira☆kira', '辣妹'],
    'EBOD':   ['E-BODY', '巨乳'],
    'SAME':   ['ATTACKERS', '剧情'],
    'RBD':    ['ATTACKERS', '剧情'],
    'FCDSS':  ['FALENO', '美少女'],
    'SSPD':   ['ATTACKERS', '剧情'],
    'ATID':   ['ATTACKERS', '剧情'],
    'DASD':   ['痴女', '剧情'],
    'REBD':   ['写真', '美体'],
    'TEK':    ['写真', '偶像'],
    'TEK00097': ['写真', '偶像'],
    'MUDR':   ['MOODYZ', '漫改'],
    'OFJE':   ['S1', '合集'],
    'MTALL':  ['巨乳', '合集'],
    'CEAD':   ['剧情', '合集'],
    'FNS':    ['素人', '企划'],
    'MMTA':   ['素人', '企划'],
    'HYPN':   ['催眠', '企划'],
    'ION':    ['素人', '美少女'],
    'RKI':    ['剧情', '硬核'],
    'MIRD':   ['MOODYZ', '巨乳'],
    'WO':     ['素人', '企划'],
    'CWPBD':  ['无码', '合集'],
    'SMBD':   ['无码', '合集'],
    'STAR':   ['SOD', '企划'],
    'PGD':    ['PRESTIGE', '美少女'],
    'BF':     ['剧情', '美少女'],
    'SABA':   ['素人', '企划'],
    'PFES':   ['素人', '企划'],
    'HSODA':  ['SOD', '剧情'],
    'HODV':   ['h.m.p', '美少女'],
    'NHDTB':  ['企划', '剧情'],
    'SV':     ['写真', '美体'],
    'LUXU':   ['素人', '高画质'],
    'MIAB':   ['MOODYZ', '美少女'],
    'BDA':    ['企划', '剧情'],
    'NNPJ':   ['企划', '素人'],
    'MBF':    ['美少女', '写真'],
    'GENM':   ['企划', '素人'],
    'SHKD':   ['ATTACKERS', '剧情'],
    'DOM':    ['企划', '素人'],
    'DSVR':   ['企划', '合集'],
    'MIUM':   ['企划', '素人'],
    'USBA':   ['写真', '美体'],
    'MKMP':   ['企划', '美少女'],
    'DVAJ':   ['企划', '剧情'],
    'TSDS':   ['合集', '素人'],
    'AVOP':   ['合集', '企划'],
}


def extract_code_prefix(movie_name: str) -> str | None:
    """Extract the JAV code prefix from a movie name.

    Examples:
        SONE-912       → SONE
        ssis-280       → SSIS
        EBWH-063CX     → EBWH
        DASD623        → DASD
        carib-120614-753（QQ4K.CC） → CARIB
        FC2-PPV-123456 → FC2
        259LUXU-123    → 259LUXU
        051920-001-carib-1080p → CARIB
    """
    if not movie_name:
        return None

    name = movie_name.strip()

    # Remove suffixes in parentheses, brackets, and common URL/tag suffixes
    name = re.sub(r'[（(][^)）]*[)）]', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'(-UC|-HD|-C)(\b|$)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'(QQ4K\.CC|\.(?:com|cc|net|xyz))', '', name, flags=re.IGNORECASE)
    name = name.strip()

    # Detect carib/1pondo/HEYZO patterns embedded deeper in the name
    # e.g. "051920-001-carib-1080p" → prefix is carib
    for keyword in ('CARIB', '1PONDO', 'HEYZO'):
        m = re.search(rf'(?:^|-)({keyword})(?:-|$)', name, re.IGNORECASE)
        if m:
            return m.group(1).upper()

    # Special case: FC2-PPV-xxx → FC2, also handle FC-2PPV variant
    m = re.match(r'^(FC2|FC)', name, re.IGNORECASE)
    if m:
        if m.group(1).upper() == 'FC':
            # Must be FC-2PPV or similar FC-series
            if re.match(r'^FC[-.]?\d', name, re.IGNORECASE):
                return 'FC2'
        else:
            return 'FC2'

    # Try extracting alphabetic prefix from alphanumeric-then-hyphen
    # e.g. "DASD623" → "DASD", "259LUXU-123" → "259LUXU", "MIAB-009" → "MIAB"
    m = re.match(r'^([A-Za-z]+)\d*-', name)
    if m:
        return m.group(1).upper()

    # Try: pure alphanumeric prefix (e.g. 259LUXU)
    m = re.match(r'^([A-Za-z\d]+)-', name)
    if m:
        return m.group(1).upper()

    # Try: no hyphen, e.g. "DASD623" (code without hyphen)
    m = re.match(r'^([A-Za-z]+)(\d+)', name)
    if m:
        return m.group(1).upper()

    # Fallback: just the first alphanumeric token
    m = re.match(r'^([A-Za-z\d]+)', name)
    if m:
        token = m.group(1).upper()
        if len(token) >= 2 and not token.isdigit():
            return token

    return None


def merge_tags(existing_str: str, add_tags: list[str]) -> str:
    """Merge tags: add new ones, keep existing, deduplicate."""
    current = set(t.strip() for t in existing_str.split(',') if t.strip())
    current.update(t.strip() for t in add_tags if t.strip())
    return ','.join(sorted(current))


def main():
    parser = argparse.ArgumentParser(description='Auto-tag movies by JAV code prefix')
    parser.add_argument('--apply', action='store_true', help='Actually write tags to Excel (default: dry-run)')
    parser.add_argument('--config', default='config.json', help='Path to config.json')
    args = parser.parse_args()

    cm = ConfigManager(args.config)
    em = ExcelManager(cm.get('path_config', {}).get('excel_path'))
    records = em.get_all_movies()

    matched = 0
    no_prefix = 0
    no_map = 0
    tag_counts = {}  # tag → count of movies that get it

    tags_idx = em._get_column_index('tags')

    for r in records:
        movie_id = r.get('movie_id', '')
        movie_name = r.get('movie_name', '')

        prefix = extract_code_prefix(movie_name)
        if not prefix:
            no_prefix += 1
            continue

        new_tags = CODE_PREFIX_MAP.get(prefix)
        if not new_tags:
            no_map += 1
            continue

        matched += 1
        for t in new_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

        if args.apply:
            # Direct row update (single save at end — no per-row save)
            existing_tags = r.get('tags', '')
            merged = merge_tags(existing_tags, new_tags)
            row = em.find_row_by_id(movie_id)
            if row:
                row[tags_idx].value = merged

    if args.apply:
        em.save()

    # Summary
    print(f'=== 番号标签分析 ===')
    print(f'总影片数:   {len(records)}')
    print(f'匹配成功:   {matched} ({matched*100//max(len(records),1)}%)')
    print(f'无番号前缀: {no_prefix}')
    print(f'未匹配映射: {no_map}')
    print(f'')

    if tag_counts:
        print(f'标签分布 (tag → movie_count):')
        for tag, cnt in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f'  {tag:20s} {cnt}')

    if args.apply:
        # Also update config.json type_tags with new tags
        config = cm.config
        tc = config.setdefault('tag_config', {})
        existing_type_tags = set(tc.get('type_tags', []))
        new_type_tags = set(tag_counts.keys()) - existing_type_tags
        if new_type_tags:
            tc['type_tags'] = sorted(existing_type_tags | new_type_tags)
            cm.save_config()
            print(f'\n已添加 {len(new_type_tags)} 个新类型标签到 config.json:')
            for t in sorted(new_type_tags):
                print(f'  + {t}')
        print(f'\n✅ 已写入 Excel。')
    else:
        print(f'\n💡 预览模式。使用 --apply 实际写入。')


if __name__ == '__main__':
    main()
