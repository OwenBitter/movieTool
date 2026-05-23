"""Stats routes."""

from flask import Blueprint, jsonify

from web.server_state import get_state
from web.shared import get_excel

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/api/stats')
def api_stats():
    excel = get_excel()
    state = get_state()
    state.ensure_fresh(excel)
    return jsonify(state.stats_cache)


@stats_bp.route('/api/stats/detail')
def api_stats_detail():
    excel = get_excel()
    state = get_state()
    state.ensure_fresh(excel)
    return jsonify(state.stats_detail_cache)
