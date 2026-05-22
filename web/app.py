#!/usr/bin/env python3
"""电影分类浏览器 - Flask Web 后端 (纯数据服务)"""

import io
import csv as csv_mod
import json
import os
import shutil
import subprocess
from pathlib import Path

# IMPORTANT: This file is designed to run from the project root:
#   cd /mnt/e/tools/movieTool && python3 web/app.py
# Or set PYTHONPATH:
#   PYTHONPATH=/mnt/e/tools/movieTool python3 web/app.py

from flask import Flask, jsonify, request, render_template, Response, send_from_directory, send_file
from core.excel_manager import ExcelManager

app = Flask(__name__)

CONFIG_PATH = str(Path(__file__).resolve().parent.parent / 'config.json')
DIST_DIR = str(Path(__file__).resolve().parent / 'static' / 'dist')


def _load_config():
    """Load config.json on demand (supports runtime updates)."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_excel():
    config = _load_config()
    excel_path = config.get('path_config', {}).get('excel_path', '/mnt/e/电影管理.xlsx')
    return ExcelManager(excel_path)


def get_tag_config():
    return _load_config().get('tag_config', {})


def get_available_tags():
    return get_tag_config().get('available_tags', [])


def filter_records(records, actor='', tags_filter=None, rating_min=0, status='', search=''):
    """Shared filtering logic used by /api/movies, export, and open-filtered.
    Works on raw Excel records (tags as comma-separated string, rating as string)."""
    if tags_filter is None:
        tags_filter = []
    filtered = []
    for r in records:
        if actor and r.get('actor', '').strip() != actor:
            continue
        if tags_filter:
            movie_tags = [t.strip() for t in r.get('tags', '').split(',') if t.strip()]
            if not all(t in movie_tags for t in tags_filter):
                continue
        if rating_min > 0:
            try:
                if int(r.get('rating', '0') or '0') < rating_min:
                    continue
            except ValueError:
                continue
        if status and r.get('status', '').strip() != status:
            continue
        if search:
            fn = (r.get('file_name', '') + r.get('actor', '') + r.get('movie_name', '')).lower()
            if search not in fn:
                continue
        filtered.append(r)
    return filtered


def format_movie(record):
    return {
        'movie_id': record.get('movie_id', ''),
        'file_name': record.get('file_name', ''),
        'movie_name': record.get('movie_name', ''),
        'actor': record.get('actor', ''),
        'release_year': record.get('release_year', ''),
        'rating': int(record.get('rating', '0') or '0'),
        'file_size': record.get('file_size', ''),
        'status': record.get('status', ''),
        'tags': record.get('tags', ''),
        'downloaded_at': record.get('downloaded_at', ''),
    }


@app.route('/')
def index():
    # Try serving React build first, fallback to Jinja2 template
    dist_index = os.path.join(DIST_DIR, 'index.html')
    if os.path.exists(dist_index):
        return send_from_directory(DIST_DIR, 'index.html')
    return render_template('index.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve built React assets from dist/."""
    assets_dir = os.path.join(DIST_DIR, 'assets')
    return send_from_directory(assets_dir, filename)


@app.route('/<path:path>')
def spa_fallback(path):
    """SPA fallback: serve index.html for any non-API, non-asset path."""
    target = os.path.join(DIST_DIR, path)
    if os.path.isfile(target):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, 'index.html')


# ─── Query APIs ────────────────────────────────────────────────────────

@app.route('/api/actors')
def api_actors():
    excel = get_excel()
    records = excel.get_all_movies()
    actors = {}
    for r in records:
        actor = r.get('actor', '').strip() or '未分类'
        if actor not in actors:
            actors[actor] = {'name': actor, 'count': 0}
        actors[actor]['count'] += 1
    result = sorted(actors.values(), key=lambda x: (-x['count'], x['name']))
    return jsonify(result)


@app.route('/api/movies')
def api_movies():
    excel = get_excel()
    records = excel.get_all_movies()

    actor = request.args.get('actor', '').strip()
    tags_filter = [t.strip() for t in request.args.get('tags', '').split(',') if t.strip()]
    rating_min = request.args.get('rating_min', type=int, default=0)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip().lower()
    sort = request.args.get('sort', 'time')

    raw = filter_records(records, actor=actor, tags_filter=tags_filter,
                         rating_min=rating_min, status=status, search=search)
    filtered = [format_movie(r) for r in raw]

    if sort == 'rating':
        filtered.sort(key=lambda x: -x['rating'])
    elif sort == 'name':
        filtered.sort(key=lambda x: x['movie_name'])
    else:
        filtered.sort(key=lambda x: x['downloaded_at'], reverse=True)

    return jsonify(filtered)


@app.route('/api/tag-templates')
def api_tag_templates():
    """Return available tag templates from config."""
    return jsonify(get_tag_config().get('tag_templates', {}))


@app.route('/api/tags')
def api_tags():
    excel = get_excel()
    records = excel.get_all_movies()
    usage = {}
    for r in records:
        tags_str = r.get('tags', '')
        if tags_str:
            for t in tags_str.split(','):
                t = t.strip()
                if t:
                    usage[t] = usage.get(t, 0) + 1

    # Merge available_tags + type_tags + usage-based tags
    available = get_available_tags()
    type_tags = get_tag_config().get('type_tags', [])
    all_defined = set(available + type_tags)
    custom_tags = [t for t in usage if t not in all_defined]
    delimiter = get_tag_config().get('delimiter', ',')

    return jsonify({
        'available_tags': available,        # attribute tags (美乳, 巨乳...)
        'type_tags': type_tags,            # film type tags (S1, MOODYZ...)
        'custom_tags': custom_tags,        # user-created tags
        'usage': usage,                    # tag → count
        'allow_custom': get_tag_config().get('allow_custom', True),
        'delimiter': delimiter,
    })


@app.route('/api/tags/add', methods=['POST'])
def add_tag():
    """Add a new tag to config.json. group: 'attribute' (default) or 'type'."""
    data = request.get_json() or {}
    new_tag = data.get('tag', '').strip()
    group = data.get('group', 'attribute')
    if not new_tag:
        return jsonify({'success': False, 'error': '标签名不能为空'}), 400

    key = 'type_tags' if group == 'type' else 'available_tags'
    group_cn = '类型' if group == 'type' else '属性'
    config = _load_config()
    tag_list = config.setdefault('tag_config', {}).get(key, [])
    if new_tag in tag_list:
        return jsonify({'success': False, 'error': f'标签「{new_tag}」已在{group_cn}组中'}), 409

    # Also check if it exists in the other group
    other_key = 'available_tags' if group == 'type' else 'type_tags'
    other_list = config['tag_config'].get(other_key, [])
    if new_tag in other_list:
        other_cn = '属性' if group == 'type' else '类型'
        return jsonify({'success': False, 'error': f'标签「{new_tag}」已在{other_cn}组中，请先在另一组删除再添加'}), 409

    tag_list.append(new_tag)
    config['tag_config'][key] = tag_list
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'tag': new_tag, 'group': group})


@app.route('/api/tags/<tagname>', methods=['DELETE'])
def delete_tag(tagname):
    """Remove a tag from config.json library (checks both groups)."""
    data = request.get_json() or {}
    clean_movies = data.get('clean_movies', False)

    config = _load_config()
    tc = config.setdefault('tag_config', {})
    # Find which group the tag belongs to
    for key in ('available_tags', 'type_tags'):
        lst = tc.get(key, [])
        if tagname in lst:
            lst.remove(tagname)
            tc[key] = lst
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            cleaned = 0
            if clean_movies:
                excel = get_excel()
                for r in excel.get_all_movies():
                    tags_str = r.get('tags', '')
                    current = [t.strip() for t in tags_str.split(',') if t.strip()]
                    if tagname in current:
                        current.remove(tagname)
                        excel.update_movie(r['movie_id'], {'tags': ','.join(current)})
                        cleaned += 1

            return jsonify({'success': True, 'removed': tagname, 'cleaned_movies': cleaned})

    return jsonify({'success': False, 'error': '标签不存在'}), 404


@app.route('/api/tags/<tagname>', methods=['PUT'])
def rename_tag(tagname):
    """Rename a tag: update config.json library (both groups) + replace in all movies."""
    data = request.get_json() or {}
    new_name = (data.get('new_name', '') or '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': '新标签名不能为空'}), 400

    config = _load_config()
    tc = config.setdefault('tag_config', {})

    # Find and update in either group
    for key in ('available_tags', 'type_tags'):
        lst = tc.get(key, [])
        if tagname in lst:
            if new_name in lst:
                return jsonify({'success': False, 'error': '新标签名已存在'}), 409
            idx = lst.index(tagname)
            lst[idx] = new_name
            tc[key] = lst
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # Replace in all movies
            excel = get_excel()
            updated = 0
            for r in excel.get_all_movies():
                tags_str = r.get('tags', '')
                current = [t.strip() for t in tags_str.split(',') if t.strip()]
                if tagname in current:
                    current[current.index(tagname)] = new_name
                    excel.update_movie(r['movie_id'], {'tags': ','.join(current)})
                    updated += 1

            return jsonify({'success': True, 'old': tagname, 'new': new_name, 'updated_movies': updated})

    return jsonify({'success': False, 'error': '原标签不存在'}), 404


@app.route('/api/stats')
def api_stats():
    excel = get_excel()
    records = excel.get_all_movies()
    total = len(records)
    actors = set()
    classified = rated = tagged = 0
    for r in records:
        if r.get('actor', '').strip():
            actors.add(r.get('actor', '').strip())
        if r.get('status') == 'classified':
            classified += 1
        rating = r.get('rating', '0')
        if rating and rating != '0':
            rated += 1
        if r.get('tags', '').strip():
            tagged += 1
    return jsonify({
        'total': total,
        'actors_count': len(actors),
        'classified': classified,
        'new': total - classified,
        'rated': rated,
        'tagged': tagged,
    })


@app.route('/api/stats/detail')
def api_stats_detail():
    """Detailed stats for the dashboard: tag distribution, rating distribution, top actors, etc."""
    excel = get_excel()
    records = excel.get_all_movies()

    total = len(records)
    actors_count: dict[str, int] = {}
    rating_dist: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    tag_counts: dict[str, int] = {}
    total_size_bytes = 0
    classified = rated = tagged = 0
    recent_7d = 0
    import datetime

    now = datetime.datetime.now()
    week_ago = now - datetime.timedelta(days=7)

    for r in records:
        actor = r.get('actor', '').strip()
        if actor:
            actors_count[actor] = actors_count.get(actor, 0) + 1

        rating = r.get('rating', '0')
        if rating and rating != '0':
            rated += 1
            r_int = int(rating)
            if 1 <= r_int <= 5:
                rating_dist[r_int] += 1

        tags_str = r.get('tags', '')
        if tags_str:
            tagged += 1
            for t in tags_str.split(','):
                t = t.strip()
                if t:
                    tag_counts[t] = tag_counts.get(t, 0) + 1

        if r.get('status') == 'classified':
            classified += 1

        # Size: parse "6.27 GB" format
        size_str = r.get('file_size', '0')
        try:
            parts = size_str.split()
            if len(parts) == 2:
                val = float(parts[0])
                unit = parts[1].upper()
                if unit == 'TB':
                    total_size_bytes += int(val * 1024 * 1024 * 1024 * 1024)
                elif unit == 'GB':
                    total_size_bytes += int(val * 1024 * 1024 * 1024)
                elif unit == 'MB':
                    total_size_bytes += int(val * 1024 * 1024)
                elif unit == 'KB':
                    total_size_bytes += int(val * 1024)
                else:
                    total_size_bytes += int(val)
        except (ValueError, IndexError):
            pass

        # Recent downloads
        dl = r.get('downloaded_at', '')
        if dl:
            try:
                dl_date = datetime.datetime.strptime(dl[:10], '%Y-%m-%d')
                if dl_date >= week_ago:
                    recent_7d += 1
            except ValueError:
                pass

    # Top 10 actors
    top_actors = sorted(actors_count.items(), key=lambda x: -x[1])[:10]
    top_actors_list = [{'name': name, 'count': count} for name, count in top_actors]

    # Format total size
    if total_size_bytes >= 1024 * 1024 * 1024 * 1024:
        total_size = f"{total_size_bytes / (1024*1024*1024*1024):.2f} TB"
    elif total_size_bytes >= 1024 * 1024 * 1024:
        total_size = f"{total_size_bytes / (1024*1024*1024):.1f} GB"
    elif total_size_bytes >= 1024 * 1024:
        total_size = f"{total_size_bytes / (1024*1024):.1f} MB"
    else:
        total_size = f"{total_size_bytes} B"

    # Average rating
    rated_records = [int(r.get('rating', '0')) for r in records
                     if r.get('rating', '0') and r.get('rating', '0') != '0']
    avg_rating = round(sum(rated_records) / len(rated_records), 1) if rated_records else 0

    # Sort tag_counts by count descending
    sorted_tags = dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:20])

    return jsonify({
        'total': total,
        'classified': classified,
        'unclassified': total - classified,
        'rated': rated,
        'tagged': tagged,
        'top_actors': top_actors_list,
        'rating_distribution': rating_dist,
        'tag_counts': sorted_tags,
        'total_size': total_size,
        'avg_rating': avg_rating,
        'recent_downloads': recent_7d,
    })


# ─── Mutation API (rating + tags only) ──────────────────────────────────

@app.route('/api/movies/<movie_id>', methods=['PATCH'])
def patch_movie(movie_id):
    data = request.get_json() or {}
    excel = get_excel()
    row = excel.find_row_by_id(movie_id)
    if not row:
        return jsonify({'success': False, 'error': '影片不存在'}), 404

    updates = {}
    if 'rating' in data:
        try:
            rating = int(data['rating'])
            if 0 <= rating <= 5:
                updates['rating'] = str(rating)
        except (ValueError, TypeError):
            pass

    if 'tags' in data:
        raw = str(data.get('tags', '')).strip()
        updates['tags'] = ','.join([t.strip() for t in raw.split(',') if t.strip()]) if raw else ''

    if not updates:
        return jsonify({'success': False, 'error': '没有需要更新的字段'}), 400

    for key, value in updates.items():
        row[excel._get_column_index(key)].value = value
    excel.save()
    return jsonify({'success': True, 'updates': updates})


# ─── Export ─────────────────────────────────────────────────────────────

@app.route('/api/movies/export')
def export_csv():
    excel = get_excel()
    records = excel.get_all_movies()

    actor = request.args.get('actor', '').strip()
    tags_filter = [t.strip() for t in request.args.get('tags', '').split(',') if t.strip()]
    rating_min = request.args.get('rating_min', type=int, default=0)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip().lower()

    filtered = filter_records(records, actor=actor, tags_filter=tags_filter,
                              rating_min=rating_min, status=status, search=search)

    output = io.StringIO()
    writer = csv_mod.writer(output)
    writer.writerow([excel.HEADER_LABELS.get(h, h) for h in excel.HEADERS])
    for r in filtered:
        writer.writerow([r.get(h, '') for h in excel.HEADERS])
    csv_content = output.getvalue()
    output.close()

    return Response(csv_content, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=movies_export.csv'})


# ─── Open in Explorer ───────────────────────────────────────────────────

def _wsl_to_win(wsl_path):
    """Convert /mnt/e/... → E:\\..."""
    if wsl_path.startswith('/mnt/'):
        drive = wsl_path[5:6].upper()
        return f'{drive}:' + wsl_path[6:].replace('/', '\\')
    return wsl_path.replace('/', '\\')


@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    """Open the file's containing folder in Windows Explorer."""
    data = request.get_json() or {}
    movie_id = data.get('movie_id', '')

    excel = get_excel()
    row = excel.find_row_by_id(movie_id)
    if not row:
        return jsonify({'success': False, 'error': '影片不存在'}), 404

    fp_idx = excel._get_column_index('file_path')
    wsl_path = (row[fp_idx].value or '').strip()
    if not wsl_path or not os.path.exists(wsl_path):
        return jsonify({'success': False, 'error': '文件不存在'}), 404

    win_path = _wsl_to_win(wsl_path)
    try:
        subprocess.Popen(['explorer.exe', '/select,', win_path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/open-filtered', methods=['POST'])
def open_filtered():
    """Collect filtered/selected files via symlinks into one folder, open in Explorer."""
    data = request.get_json() or {}
    ids = data.get('ids', [])

    excel = get_excel()
    files = []  # list of (wsl_path, display_name)

    if ids:
        for mid in ids:
            row = excel.find_row_by_id(mid)
            if row:
                fp = (row[excel._get_column_index('file_path')].value or '').strip()
                fn = (row[excel._get_column_index('file_name')].value or '').strip()
                if fp and os.path.exists(fp):
                    files.append((fp, fn))
    else:
        actor = data.get('actor', '').strip()
        tags_filter = [t.strip() for t in data.get('tags', '').split(',') if t.strip()]
        rating_min = data.get('rating_min', 0)
        status = data.get('status', '').strip()
        search = (data.get('search', '') or '').strip().lower()

        records = excel.get_all_movies()
        filtered = filter_records(records, actor=actor, tags_filter=tags_filter,
                                  rating_min=rating_min, status=status, search=search)
        for r in filtered:
            fp = (r.get('file_path') or '').strip()
            fn = (r.get('file_name') or '').strip()
            if fp and os.path.exists(fp):
                files.append((fp, fn))

    if not files:
        return jsonify({'success': False, 'error': '没有匹配的文件'}), 404

    # Create/clear the temp folder
    link_dir = '/mnt/e/筛选结果'
    if os.path.exists(link_dir):
        for f in os.listdir(link_dir):
            try:
                os.unlink(os.path.join(link_dir, f))
            except OSError:
                pass
    else:
        os.makedirs(link_dir, exist_ok=True)

    # Create .lnk shortcuts via PowerShell (no admin required)
    created = 0
    for src_wsl, fname in files:
        src_win = _wsl_to_win(src_wsl)
        link_name = os.path.splitext(fname)[0] + '.lnk'
        link_wsl = os.path.join(link_dir, link_name)
        link_win = _wsl_to_win(link_wsl)

        # Handle duplicate names
        base = os.path.splitext(fname)[0]
        counter = 1
        while os.path.exists(link_wsl):
            link_name = f'{base}_{counter}.lnk'
            link_wsl = os.path.join(link_dir, link_name)
            link_win = _wsl_to_win(link_wsl)
            counter += 1

        # PowerShell COM: create shortcut to original file
        ps_cmd = (
            f"$ws=New-Object -ComObject WScript.Shell;"
            f"$sc=$ws.CreateShortcut('{link_win}');"
            f"$sc.TargetPath='{src_win}';"
            f"$sc.Save()"
        )
        try:
            subprocess.run(
                ['powershell.exe', '-Command', ps_cmd],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=5,
            )
            if os.path.exists(link_wsl):
                created += 1
        except Exception:
            pass

    # Open the single folder
    win_link_dir = _wsl_to_win(link_dir)
    try:
        subprocess.Popen(['explorer.exe', win_link_dir],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    return jsonify({'success': True, 'files': created, 'folder': 'E:\\筛选结果'})


# ─── Batch Operations ───────────────────────────────────────────────────

def _resolve_movie(excel, movie_id):
    """Return (row, file_path_wsl) or (None, None) if not found."""
    row = excel.find_row_by_id(movie_id)
    if not row:
        return None, None
    fp = (row[excel._get_column_index('file_path')].value or '').strip()
    return row, fp


@app.route('/api/movies/batch/delete', methods=['POST'])
def batch_delete():
    """Delete movies: remove files from disk + remove rows from Excel."""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400

    excel = get_excel()
    deleted_files = 0
    deleted_rows = 0
    errors = []

    # Collect rows to delete (process in reverse to preserve row indices)
    rows_to_delete = []
    for mid in ids:
        row, fp = _resolve_movie(excel, mid)
        if not row:
            errors.append({'movie_id': mid, 'error': '未找到'})
            continue
        rows_to_delete.append((row, fp))

    # Delete files first, then remove rows
    for row, fp in rows_to_delete:
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
                deleted_files += 1
            except OSError as e:
                errors.append({'file': fp, 'error': str(e)})
        # Remove row from sheet
        row_num = row[0].row  # 1-indexed row number
        excel.sheet.delete_rows(row_num)
        deleted_rows += 1

    excel.save()
    return jsonify({
        'success': True,
        'deleted_files': deleted_files,
        'deleted_rows': deleted_rows,
        'errors': errors,
    })


@app.route('/api/movies/batch/move', methods=['POST'])
def batch_move():
    """Move selected movie files to a destination directory."""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    dest = (data.get('dest', '') or '').strip()

    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400
    if not dest:
        return jsonify({'success': False, 'error': '请提供目标路径'}), 400

    dest = os.path.abspath(dest)
    os.makedirs(dest, exist_ok=True)

    excel = get_excel()
    moved = 0
    errors = []

    for mid in ids:
        row, fp = _resolve_movie(excel, mid)
        if not row or not fp:
            errors.append({'movie_id': mid, 'error': '未找到'})
            continue
        if not os.path.exists(fp):
            errors.append({'movie_id': mid, 'error': '文件不存在'})
            continue

        fname = (row[excel._get_column_index('file_name')].value or '').strip()
        dest_path = os.path.join(dest, fname)

        # Handle duplicate filenames
        base, ext = os.path.splitext(fname)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest, f'{base}_{counter}{ext}')
            counter += 1

        try:
            shutil.move(fp, dest_path)
            row[excel._get_column_index('file_path')].value = dest_path
            row[excel._get_column_index('status')].value = 'classified'
            moved += 1
        except OSError as e:
            errors.append({'movie_id': mid, 'file': fp, 'error': str(e)})

    excel.save()
    return jsonify({
        'success': True,
        'moved': moved,
        'errors': errors,
    })


@app.route('/api/movies/batch/copy', methods=['POST'])
def batch_copy():
    """Copy selected movie files to a destination directory (files stay in place)."""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    dest = (data.get('dest', '') or '').strip()

    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400
    if not dest:
        return jsonify({'success': False, 'error': '请提供目标路径'}), 400

    dest = os.path.abspath(dest)
    os.makedirs(dest, exist_ok=True)

    excel = get_excel()
    copied = 0
    errors = []

    for mid in ids:
        row, fp = _resolve_movie(excel, mid)
        if not row or not fp:
            errors.append({'movie_id': mid, 'error': '未找到'})
            continue
        if not os.path.exists(fp):
            errors.append({'movie_id': mid, 'error': '文件不存在'})
            continue

        fname = (row[excel._get_column_index('file_name')].value or '').strip()
        dest_path = os.path.join(dest, fname)
        base, ext = os.path.splitext(fname)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest, f'{base}_{counter}{ext}')
            counter += 1

        try:
            shutil.copy2(fp, dest_path)
            copied += 1
        except OSError as e:
            errors.append({'movie_id': mid, 'file': fp, 'error': str(e)})

    return jsonify({
        'success': True,
        'copied': copied,
        'errors': errors,
    })


# ─── Batch Tag Operations ──────────────────────────────────────────────

def _merge_tags(existing_str, add_tags, remove_tags=None):
    """Merge tags: existing comma-separated string + add list - remove list."""
    current = set(t.strip() for t in existing_str.split(',') if t.strip())
    if add_tags:
        current.update(t.strip() for t in add_tags if t.strip())
    if remove_tags:
        current.difference_update(t.strip() for t in remove_tags if t.strip())
    return ','.join(sorted(current))


@app.route('/api/movies/batch/tags/add', methods=['POST'])
def batch_tags_add():
    """Add tags to selected movies (append, don't remove existing)."""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    tags_to_add = data.get('tags', [])
    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400
    if not tags_to_add:
        return jsonify({'success': False, 'error': '请提供要添加的标签'}), 400

    excel = get_excel()
    updated = 0
    for mid in ids:
        row, _ = _resolve_movie(excel, mid)
        if not row:
            continue
        existing = (row[excel._get_column_index('tags')].value or '').strip()
        new_tags = _merge_tags(existing, tags_to_add)
        row[excel._get_column_index('tags')].value = new_tags
        updated += 1

    excel.save()
    return jsonify({'success': True, 'updated': updated, 'added': tags_to_add})


@app.route('/api/movies/batch/tags/set', methods=['POST'])
def batch_tags_set():
    """Replace tags on selected movies entirely."""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    tags = data.get('tags', [])
    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400

    new_tags_str = ','.join(t.strip() for t in tags if t.strip()) if tags else ''

    excel = get_excel()
    updated = 0
    for mid in ids:
        row, _ = _resolve_movie(excel, mid)
        if not row:
            continue
        row[excel._get_column_index('tags')].value = new_tags_str
        updated += 1

    excel.save()
    return jsonify({'success': True, 'updated': updated, 'tags': new_tags_str})


@app.route('/api/movies/batch/tags/remove', methods=['POST'])
def batch_tags_remove():
    """Remove specified tags from selected movies."""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    tags_to_remove = data.get('tags', [])
    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400
    if not tags_to_remove:
        return jsonify({'success': False, 'error': '请提供要移除的标签'}), 400

    excel = get_excel()
    updated = 0
    for mid in ids:
        row, _ = _resolve_movie(excel, mid)
        if not row:
            continue
        existing = (row[excel._get_column_index('tags')].value or '').strip()
        new_tags = _merge_tags(existing, [], tags_to_remove)
        row[excel._get_column_index('tags')].value = new_tags
        updated += 1

    excel.save()
    return jsonify({'success': True, 'updated': updated, 'removed': tags_to_remove})


# ─── Play Video ─────────────────────────────────────────────────────────

@app.route('/api/play/<movie_id>', methods=['POST'])
def play_movie(movie_id):
    """Open the video file with the default system player."""
    excel = get_excel()
    row, fp = _resolve_movie(excel, movie_id)
    if not row or not fp:
        return jsonify({'success': False, 'error': '影片不存在'}), 404
    if not os.path.exists(fp):
        return jsonify({'success': False, 'error': '文件不存在'}), 404

    win_path = _wsl_to_win(fp)
    try:
        subprocess.Popen(['cmd.exe', '/c', 'start', '', win_path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/thumb/<movie_id>')
def api_thumb(movie_id):
    """Generate and serve video thumbnail (cached)."""
    from pathlib import Path as PathLib
    excel = get_excel()
    row, fp = _resolve_movie(excel, movie_id)
    if not row or not fp:
        return jsonify({'error': '影片不存在'}), 404
    if not os.path.exists(fp):
        return jsonify({'error': '文件不存在'}), 404

    # Cache dir
    config = _load_config()
    cache_dir = config.get('path_config', {}).get('thumb_cache', '/mnt/e/缩略图')
    os.makedirs(cache_dir, exist_ok=True)

    cache_path = os.path.join(cache_dir, f'{movie_id}.jpg')

    if not os.path.exists(cache_path):
        try:
            subprocess.run(
                ['ffmpeg', '-ss', '300', '-i', fp, '-vframes', '1',
                 '-q:v', '5', cache_path, '-y'],
                capture_output=True, timeout=15
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return jsonify({'error': 'ffmpeg 未安装或超时'}), 500

    if not os.path.exists(cache_path):
        return jsonify({'error': '缩略图生成失败'}), 500

    return send_file(cache_path, mimetype='image/jpeg')


if __name__ == '__main__':
    print('🎬 电影分类浏览器启动: http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)
