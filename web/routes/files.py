"""File operation routes — open folder, open filtered, play, thumbnails."""

import os
import subprocess
import tempfile

from flask import Blueprint, jsonify, request, send_file

from web.server_state import get_state
from web.shared import (
    DIST_DIR,
    _collect_files_by_filter,
    _collect_files_by_ids,
    _create_shortcuts,
    _load_config,
    _resolve_movie,
    _resolve_path,
    _wsl_to_win,
    get_excel,
)

files_bp = Blueprint('files', __name__)


@files_bp.route('/api/open-folder', methods=['POST'])
def open_folder():
    data = request.get_json() or {}
    movie_id = data.get('movie_id', '')

    excel = get_excel()
    row, fp = _resolve_movie(excel, movie_id)
    if not row or not fp:
        return jsonify({'success': False, 'error': '影片不存在'}), 404
    if not os.path.exists(fp):
        return jsonify({'success': False, 'error': '文件不存在'}), 404

    try:
        subprocess.Popen(['explorer.exe', '/select,', fp],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/api/open-filtered', methods=['POST'])
def open_filtered():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]

    excel = get_excel()
    files = _collect_files_by_ids(excel, ids) if ids else _collect_files_by_filter(excel, data)

    if not files:
        return jsonify({'success': False, 'error': '没有匹配的文件'}), 404

    link_dir = os.path.join(tempfile.gettempdir(), 'movieTool_筛选结果')
    created = _create_shortcuts(files, link_dir)

    win_link_dir = _wsl_to_win(link_dir)
    try:
        subprocess.Popen(['explorer.exe', win_link_dir],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    return jsonify({'success': True, 'files': created, 'folder': 'E:\\筛选结果'})


@files_bp.route('/api/play/<movie_id>', methods=['POST'])
def play_movie(movie_id):
    excel = get_excel()
    row, fp = _resolve_movie(excel, movie_id)
    if not row or not fp:
        return jsonify({'success': False, 'error': '影片不存在'}), 404
    if not os.path.exists(fp):
        return jsonify({'success': False, 'error': '文件不存在'}), 404

    win_path = _wsl_to_win(fp)
    try:
        subprocess.Popen(['explorer.exe', win_path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/api/thumb/<movie_id>')
def api_thumb(movie_id):
    excel = get_excel()
    row, fp = _resolve_movie(excel, movie_id)
    if not row or not fp:
        return jsonify({'error': '影片不存在'}), 404
    if not os.path.exists(fp):
        return jsonify({'error': '文件不存在'}), 404

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


# ── Cover image ──────────────────────────────────────────────────────

import re as _re


def _extract_code_from_name(movie_name: str) -> str | None:
    """Extract JAV code from a movie name. Returns None if not found."""
    if not movie_name:
        return None
    m = _re.search(r'([A-Z]+-\d+)', movie_name, _re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = _re.search(r'([A-Z]{2,6}\d{2,5})', movie_name, _re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


@files_bp.route('/api/cover/<movie_id>')
def api_cover(movie_id):
    """Serve javbus cover image if available."""
    excel = get_excel()
    row = excel.find_row_by_id(movie_id)
    if not row:
        return jsonify({'error': '影片不存在'}), 404
    
    movie_name = (row[excel._get_column_index('movie_name')].value or '').strip()
    code = _extract_code_from_name(movie_name)
    if not code:
        return jsonify({'error': '无法提取番号'}), 404
    
    config = _load_config()
    cover_dir = config.get('path_config', {}).get('cover_dir', '/mnt/e/tools/movieTool/covers')
    cover_dir = _resolve_path(cover_dir)
    cover_path = os.path.join(cover_dir, f'{code}.jpg')
    
    if not os.path.exists(cover_path):
        return jsonify({'error': '封面不存在'}), 404
    
    return send_file(cover_path, mimetype='image/jpeg')


# ── Path validation ──────────────────────────────────────────────────


@files_bp.route('/api/validate-paths', methods=['POST'])
def validate_paths():
    """Check all movie file paths and report which ones are missing."""
    excel = get_excel()
    records = excel.get_all_movies()
    results = []
    valid_count = 0
    invalid_count = 0

    for r in records:
        fp = (r.get('file_path') or '').strip()
        resolved = _resolve_path(fp)
        exists = bool(resolved) and os.path.exists(resolved)
        if exists:
            valid_count += 1
        else:
            invalid_count += 1
        results.append({
            'movie_id': r.get('movie_id', ''),
            'movie_name': r.get('movie_name', '') or r.get('file_name', ''),
            'actor': r.get('actor', ''),
            'file_size': r.get('file_size', ''),
            'file_path': fp,
            'exists': exists,
        })

    return jsonify({
        'success': True,
        'total': len(results),
        'valid': valid_count,
        'invalid': invalid_count,
        'results': results,
    })


@files_bp.route('/api/repair-path', methods=['POST'])
def repair_path():
    """Search for a missing movie file in download_dir and classify_dir, then update Excel."""
    data = request.get_json() or {}
    movie_id = data.get('movie_id', '')
    if not movie_id:
        return jsonify({'success': False, 'error': '缺少 movie_id'}), 400

    excel = get_excel()
    row = excel.find_row_by_id(movie_id)
    if not row:
        return jsonify({'success': False, 'error': '影片不存在'}), 404

    fp_idx = excel._get_column_index('file_path')
    mn_idx = excel._get_column_index('movie_name')
    fn_idx = excel._get_column_index('file_name')

    old_path = (row[fp_idx].value or '').strip()
    movie_name = (row[mn_idx].value or '').strip()
    file_name = (row[fn_idx].value or '').strip()

    # Extract JAV code for search
    code = _extract_code_from_name(movie_name) or _extract_code_from_name(file_name)
    if not code:
        return jsonify({'success': False, 'error': '无法提取番号用于搜索'}), 400

    config = _load_config()
    search_dirs = []
    dd = config.get('path_config', {}).get('download_dir', '')
    cd = config.get('path_config', {}).get('classify_dir', '')
    if dd:
        search_dirs.append(_resolve_path(dd))
    if cd:
        search_dirs.append(_resolve_path(cd))

    found_path = None
    for base_dir in search_dirs:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        for dirpath, _, filenames in os.walk(base_dir):
            for fname in filenames:
                if code in fname.upper() or code.replace('-', '') in fname.upper():
                    candidate = os.path.join(dirpath, fname)
                    if os.path.exists(candidate):
                        found_path = candidate
                        break
            if found_path:
                break
        if found_path:
            break

    if not found_path:
        return jsonify({
            'success': True,
            'found': False,
            'movie_id': movie_id,
            'message': f'在下载目录和分类目录中未找到 {code} 相关文件',
        })

    row[fp_idx].value = found_path
    excel.save()
    get_state().invalidate()

    return jsonify({
        'success': True,
        'found': True,
        'movie_id': movie_id,
        'movie_name': movie_name,
        'old_path': old_path,
        'new_path': found_path,
    })
