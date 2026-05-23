"""File watcher status route."""

from flask import Blueprint, jsonify

from web.watcher import get_watcher

watcher_bp = Blueprint('watcher', __name__)


@watcher_bp.route('/api/watcher/status')
def api_watcher_status():
    w = get_watcher()
    return jsonify({
        'running': w.running,
        'last_event': w.last_event,
        'files_added': w.files_added,
    })
