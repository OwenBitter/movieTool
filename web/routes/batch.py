"""Batch operations routes — delete, move, copy, tag management."""

import os
import shutil

from flask import Blueprint, jsonify, request

from web.server_state import get_state
from web.shared import (
    get_excel,
    _resolve_movie,
)
from core.tag_utils import merge_tags

batch_bp = Blueprint('batch', __name__)


@batch_bp.route('/api/movies/batch/delete', methods=['POST'])
def batch_delete():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]
    if not ids:
        return jsonify({'success': False, 'error': '没有选中的影片'}), 400

    excel = get_excel()
    deleted_files = 0
    deleted_rows = 0
    errors = []

    for mid in ids:
        row, fp = _resolve_movie(excel, mid)
        if not row:
            errors.append({'movie_id': mid, 'error': '未找到'})
            continue
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
                deleted_files += 1
            except OSError as e:
                errors.append({'file': fp, 'error': str(e)})
        excel.delete_movie(mid)
        deleted_rows += 1

    excel.save()
    get_state().invalidate()
    return jsonify({
        'success': True,
        'deleted_files': deleted_files,
        'deleted_rows': deleted_rows,
        'errors': errors,
    })


@batch_bp.route('/api/movies/batch/move', methods=['POST'])
def batch_move():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]
    dest = (data.get('dest') or data.get('destination', '')).strip()

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
    get_state().invalidate()
    return jsonify({
        'success': True,
        'moved': moved,
        'errors': errors,
    })


@batch_bp.route('/api/movies/batch/copy', methods=['POST'])
def batch_copy():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]
    dest = (data.get('dest') or data.get('destination', '')).strip()

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


@batch_bp.route('/api/movies/batch/tags/add', methods=['POST'])
def batch_tags_add():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]
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
        new_tags = merge_tags(existing, tags_to_add)
        row[excel._get_column_index('tags')].value = new_tags
        updated += 1

    excel.save()
    get_state().invalidate()
    return jsonify({'success': True, 'updated': updated, 'added': tags_to_add})


@batch_bp.route('/api/movies/batch/tags/set', methods=['POST'])
def batch_tags_set():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]
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
    get_state().invalidate()
    return jsonify({'success': True, 'updated': updated, 'tags': new_tags_str})


@batch_bp.route('/api/movies/batch/tags/remove', methods=['POST'])
def batch_tags_remove():
    data = request.get_json() or {}
    ids = data.get('movie_ids') or data.get('ids', [])
    ids = ids[:100]
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
        new_tags = merge_tags(existing, [], tags_to_remove)
        row[excel._get_column_index('tags')].value = new_tags
        updated += 1

    excel.save()
    get_state().invalidate()
    return jsonify({'success': True, 'updated': updated, 'removed': tags_to_remove})
