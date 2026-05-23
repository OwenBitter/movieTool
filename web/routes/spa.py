"""SPA serving routes — React build + Jinja2 fallback."""

import os

from flask import Blueprint, render_template, send_from_directory

from web.shared import DIST_DIR

spa_bp = Blueprint('spa', __name__)


@spa_bp.route('/')
def index():
    dist_index = os.path.join(DIST_DIR, 'index.html')
    if os.path.exists(dist_index):
        return send_from_directory(DIST_DIR, 'index.html')
    return render_template('index.html')


@spa_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(DIST_DIR, 'assets')
    return send_from_directory(assets_dir, filename)


@spa_bp.route('/<path:path>')
def spa_fallback(path):
    target = os.path.join(DIST_DIR, path)
    if os.path.isfile(target):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, 'index.html')
