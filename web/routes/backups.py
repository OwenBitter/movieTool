"""Backup management routes."""

import json
import os
import shutil
import time

from flask import Blueprint, jsonify, request

from web.server_state import get_state
from web.shared import (
    _load_config,
    format_file_size,
    get_excel,
    invalidate_excel_cache,
)

backups_bp = Blueprint('backups', __name__)


@backups_bp.route('/api/backups')
def api_backups():
    config = _load_config()
    backup_dir = config.get('path_config', {}).get('backup_dir', '')
    if not backup_dir or not os.path.exists(backup_dir):
        return jsonify({'backups': [], 'dir': backup_dir})

    files = []
    for f in sorted(os.listdir(backup_dir), reverse=True):
        path = os.path.join(backup_dir, f)
        if os.path.isfile(path) and f.endswith('.xlsx'):
            stat = os.stat(path)
            files.append({
                'name': f,
                'size': format_file_size(stat.st_size),
                'mtime': int(stat.st_mtime),
                'mtime_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
            })
    return jsonify({'backups': files, 'dir': backup_dir})


@backups_bp.route('/api/backup/create', methods=['POST'])
def api_backup_create():
    excel = get_excel()
    config = _load_config()
    backup_dir = config.get('path_config', {}).get('backup_dir', '')
    if not backup_dir:
        return jsonify({'success': False, 'error': '未配置备份目录'}), 400
    try:
        target = excel.backup_excel(backup_dir)
        invalidate_excel_cache()
        return jsonify({'success': True, 'path': target})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@backups_bp.route('/api/backup/restore/<filename>', methods=['POST'])
def api_backup_restore(filename):
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'success': False, 'error': '非法文件名'}), 400
    config = _load_config()
    backup_dir = config.get('path_config', {}).get('backup_dir', '')
    src = os.path.join(backup_dir, filename)
    if not os.path.exists(src) or not os.path.realpath(src).startswith(os.path.realpath(backup_dir)):
        return jsonify({'success': False, 'error': '备份文件不存在'}), 404

    excel = get_excel()
    dst = excel.excel_path
    try:
        shutil.copy2(src, dst)
        invalidate_excel_cache()
        get_state().invalidate()
        return jsonify({'success': True, 'restored': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@backups_bp.route('/api/backup/<filename>', methods=['DELETE'])
def api_backup_delete(filename):
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'success': False, 'error': '非法文件名'}), 400
    config = _load_config()
    backup_dir = config.get('path_config', {}).get('backup_dir', '')
    path = os.path.join(backup_dir, filename)
    if not os.path.exists(path) or not os.path.realpath(path).startswith(os.path.realpath(backup_dir)):
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    try:
        os.unlink(path)
        return jsonify({'success': True, 'deleted': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
