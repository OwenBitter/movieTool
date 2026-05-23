"""Movie query + mutation routes."""

import csv as csv_mod
import io
import random

from flask import Blueprint, Response, jsonify, request

from web.server_state import get_state
from web.shared import (
    filter_records,
    format_movie,
    get_excel,
)

movies_bp = Blueprint('movies', __name__)


@movies_bp.route('/api/movies')
def api_movies():
    excel = get_excel()
    records = excel.get_all_movies()

    actor = request.args.get('actor', '').strip()
    tags_filter = [t.strip() for t in request.args.get('tags', '').split(',') if t.strip()]
    rating_min = request.args.get('rating_min', type=int, default=0)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip().lower()
    sort = request.args.get('sort', 'time')
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=0)
    size_min = request.args.get('size_min', type=float, default=None)
    size_max = request.args.get('size_max', type=float, default=None)
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    raw = filter_records(records, actor=actor, tags_filter=tags_filter,
                         rating_min=rating_min, status=status, search=search,
                         size_min=size_min, size_max=size_max,
                         date_from=date_from, date_to=date_to)
    filtered = [format_movie(r) for r in raw]

    if sort == 'rating':
        filtered.sort(key=lambda x: -x['rating'])
    elif sort == 'name':
        filtered.sort(key=lambda x: x['movie_name'])
    else:
        filtered.sort(key=lambda x: x['downloaded_at'], reverse=True)

    total = len(filtered)
    if per_page > 0:
        start = (page - 1) * per_page
        filtered = filtered[start:start + per_page]

    return jsonify({
        'movies': filtered,
        'total': total,
        'page': page,
        'per_page': per_page if per_page > 0 else total,
    })


@movies_bp.route('/api/movies/export')
def export_csv():
    excel = get_excel()
    records = excel.get_all_movies()

    actor = request.args.get('actor', '').strip()
    tags_filter = [t.strip() for t in request.args.get('tags', '').split(',') if t.strip()]
    rating_min = request.args.get('rating_min', type=int, default=0)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip().lower()
    size_min = request.args.get('size_min', type=float, default=None)
    size_max = request.args.get('size_max', type=float, default=None)
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    filtered = filter_records(records, actor=actor, tags_filter=tags_filter,
                              rating_min=rating_min, status=status, search=search,
                              size_min=size_min, size_max=size_max,
                              date_from=date_from, date_to=date_to)

    output = io.StringIO()
    writer = csv_mod.writer(output)
    writer.writerow([excel.HEADER_LABELS.get(h, h) for h in excel.HEADERS])
    for r in filtered:
        writer.writerow([r.get(h, '') for h in excel.HEADERS])
    csv_content = output.getvalue()
    output.close()

    return Response(csv_content, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=movies_export.csv'})


@movies_bp.route('/api/movies/quick-rate')
def api_quick_rate():
    excel = get_excel()
    records = excel.get_all_movies()
    unrated = [r for r in records if not (r.get('rating', '0') or '0').strip() or r.get('rating', '0') == '0']
    total = len(records)
    rated_count = total - len(unrated)

    if not unrated:
        return jsonify({'movie': None, 'rated': rated_count, 'total': total, 'done': True})

    pick = random.choice(unrated)
    return jsonify({
        'movie': format_movie(pick),
        'rated': rated_count,
        'total': total,
        'done': False,
    })


@movies_bp.route('/api/movies/<movie_id>', methods=['PATCH'])
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
    get_state().invalidate()
    return jsonify({'success': True, 'updates': updates})
