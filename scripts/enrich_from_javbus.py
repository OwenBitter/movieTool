#!/usr/bin/env python3
"""Batch enrich movie data from javbus.com — release dates, genre tags, cover images.

Usage:
    cd /mnt/e/tools/movieTool
    python3 scripts/enrich_from_javbus.py          # dry-run: preview only
    python3 scripts/enrich_from_javbus.py --apply   # write to Excel + download covers
"""

import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config_manager import ConfigManager
from core.excel_manager import ExcelManager
from core.javbus_fetcher import search, get_detail, download_cover


# ── Japanese → Chinese tag translation ─────────────────────────────────

TAG_TRANSLATIONS = {
    # Physical attributes
    "巨乳": "巨乳", "美乳": "美乳", "貧乳": "贫乳", "爆乳": "爆乳",
    "美脚": "美腿", "美少女": "美少女", "美女": "美女",
    "人妻": "人妻", "熟女": "熟女", "お姉さん": "姐姐",
    # Scenes / setups
    "単体作品": "单体作品", "單體作品": "单体作品",
    "ドラマ": "剧情", "戲劇": "剧情",
    "ハイビジョン": "高清", "ハイクオリティ": "高画质",
    "独占配信": "独家", "DMM獨家": "DMM独家", "配信専用": "网络配信",
    "デジタル": "数字版",
    # Actions
    "中出し": "中出", "中出": "中出",
    "顔射": "颜射", "ぶっかけ": "颜射",
    "潮吹き": "潮吹", "潮吹": "潮吹",
    "アクメ・オーガズム": "高潮", "絶頂": "绝顶",
    "フェラ": "口交", "パイズリ": "乳交",
    "手コキ": "手淫", "打手槍": "打手枪",
    "キス・接吻": "接吻", "接吻": "接吻",
    "アナル": "肛交",
    # Costume / role
    "制服": "制服", "水着": "泳装", "ナース": "护士",
    "女教師": "女教师", "家庭教師": "家教", "家教": "家教",
    "女子大生": "女大学生", "女大學生": "女大学生",
    "女子校生": "女高中生", "高中女生": "女高中生",
    "OL": "OL", "スチュワーデス": "空姐",
    # Attributes
    "スレンダー": "苗条", "苗條": "苗条",
    "パイパン": "白虎", "剛毛": "多毛",
    "日焼け": "日烧", "ギャル": "辣妹",
    "着エロ": "着衣诱惑", "コスプレ": "角色扮演",
    # Film type
    "ドキュメンタリー": "纪录片", "纪录片": "纪录片",
    "ハーレム": "后宫",
    "企画": "企划", "企劃": "企划",
    "多P": "多P", "乱交": "乱交",
    "レズ": "女同", "女同性恋": "女同",
    "寝取り": "NTR", "寝取": "NTR",
    # Other
    "拘束": "拘束", "SM": "SM", "緊縛": "捆绑",
    "痴女": "痴女", "ドS": "抖S", "ドM": "抖M",
    "アスリート": "运动员",
    "アイドル・芸能人": "偶像艺人", "偶像藝人": "偶像艺人",
    "ハメ撮り": "自拍",
    "花癡": "花痴",
    "乳液": "润滑液", "汗だく": "汗流浃背",
    "イラマチオ": "深喉",
    "淫語": "淫语",
    "おもちゃ": "玩具",
    "ごっくん": "吞精",
    "放尿": "放尿",
    # Skip these (too generic or same as existing)
    "薄马赛克": "薄码",
    "薄馬賽克": "薄码",
    "高画質": "高画质",
    "高畫質": "高画质",
    "4K": "4K",
    "独占": "独家",
}


def translate_tag(tag: str) -> str:
    """Translate a javbus tag to Chinese. Keeps original if no translation."""
    return TAG_TRANSLATIONS.get(tag, tag)


def is_actress_tag(tag: str, actresses: list[str]) -> bool:
    """Check if a tag is actually an actress name."""
    tag_clean = tag.strip()
    for actress in actresses:
        if tag_clean == actress or tag_clean in actress or actress in tag_clean:
            return True
    return False


def extract_code(movie_name: str) -> str | None:
    """Extract JAV code from movie name."""
    if not movie_name:
        return None
    m = re.search(r'([A-Z]+-\d+)', movie_name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'([A-Z]{2,6}\d{2,5})', movie_name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch enrich movies from javbus.com")
    parser.add_argument("--apply", action="store_true", help="Write to Excel and download covers")
    parser.add_argument("--delay", type=float, default=0.8, help="Delay between requests (seconds)")
    parser.add_argument("--limit", type=int, default=0, help="Limit to N movies (0=all)")
    args = parser.parse_args()

    cm = ConfigManager()
    em = ExcelManager(cm.get_path_config()['excel_path'])
    cover_dir = cm.get_path_config().get('cover_dir', '/mnt/e/tools/movieTool/covers')
    os.makedirs(cover_dir, exist_ok=True)

    records = em.get_all_movies()
    if args.limit:
        records = records[:args.limit]

    # Build code → record map
    todos = []
    for r in records:
        name = r.get('movie_name', '') or r.get('file_name', '')
        code = extract_code(name)
        if code:
            todos.append((code, r))

    total = len(todos)
    print(f"📊 {total} 部影片可查询 javbus")
    print(f"📁 封面目录: {cover_dir}")
    print()

    # Stats
    dates_added = 0
    tags_added = 0
    covers_downloaded = 0
    not_found = 0
    errors = 0
    total_new_tags: dict[str, int] = {}

    date_col = em._get_column_index('release_year')
    tags_col = em._get_column_index('tags')

    for i, (code, record) in enumerate(todos):
        row = em.find_row_by_id(record['movie_id'])
        if not row:
            continue

        if (i + 1) % 20 == 0:
            print(f"  ... {i + 1}/{total}  (日期+{dates_added}  标签+{tags_added}  封面+{covers_downloaded})")

        try:
            results = search(code)
            if not results:
                not_found += 1
                continue

            movie = get_detail(results[0].detail_url, code)

            if not args.apply:
                if movie.release_date and not record.get('release_year', '').strip():
                    dates_added += 1
                    print(f"  {code}: 日期 {movie.release_date}")
                if movie.genres:
                    existing = set(t.strip() for t in record.get('tags', '').split(',') if t.strip())
                    actress_names = set(movie.actresses)
                    new = []
                    for g in movie.genres:
                        translated = translate_tag(g)
                        if translated == g:
                            continue  # skip untranslatable
                        if translated in existing:
                            continue  # skip duplicates
                        if is_actress_tag(translated, list(actress_names)):
                            continue  # skip actress names
                        new.append(translated)
                    if new:
                        tags_added += len(new)
                        for g in new:
                            total_new_tags[g] = total_new_tags.get(g, 0) + 1
                        print(f"  {code}: +标签 {', '.join(new[:8])}")
                continue

            # === Apply mode ===
            changed = False

            # 1. Release date
            if movie.release_date:
                year = movie.release_date[:4]
                existing_year = (row[date_col].value or '').strip()
                if not existing_year or existing_year == '0':
                    row[date_col].value = year
                    dates_added += 1
                    changed = True

            # 2. Genre tags (translated, no actresses, no duplicates)
            existing_tags = set(t.strip() for t in (row[tags_col].value or '').split(',') if t.strip())
            actress_names = set(movie.actresses)
            new_tags = []
            for g in movie.genres:
                translated = translate_tag(g)
                if translated == g:
                    continue
                if translated in existing_tags:
                    continue
                if is_actress_tag(translated, list(actress_names)):
                    continue
                new_tags.append(translated)
                total_new_tags[translated] = total_new_tags.get(translated, 0) + 1

            if new_tags:
                merged = ','.join(sorted(existing_tags | set(new_tags)))
                row[tags_col].value = merged
                tags_added += len(new_tags)
                changed = True

            # 3. Cover image
            cover_path = os.path.join(cover_dir, f"{code}.jpg")
            if not os.path.exists(cover_path):
                try:
                    download_cover(movie.cover_url, cover_dir, f"{code}.jpg",
                                   referer=movie.detail_url)
                    covers_downloaded += 1
                except Exception:
                    pass

            if changed or (i + 1) % 20 == 0:
                em.save()

            time.sleep(args.delay)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  ⚠️ {code}: {e}")

    em.save()

    print(f"\n{'='*50}")
    print(f"✅ {'已应用' if args.apply else '预览'}完成!")
    print(f"  查询: {total}")
    print(f"  未找到: {not_found}")
    print(f"  新增日期: {dates_added}")
    print(f"  新增标签: {tags_added}  ({len(total_new_tags)} 种)")
    print(f"  下载封面: {covers_downloaded}")
    if errors:
        print(f"  错误: {errors}")

    if total_new_tags:
        print(f"\n新标签分布:")
        for tag, cnt in sorted(total_new_tags.items(), key=lambda x: -x[1])[:30]:
            print(f"  {tag:20s} {cnt}")

    if not args.apply:
        print(f"\n💡 使用 --apply 实际写入 Excel 和下载封面")


if __name__ == '__main__':
    main()
