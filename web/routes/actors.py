"""Actress / actor routes."""

from flask import Blueprint, jsonify, request

from web.server_state import get_state
from web.shared import (
    _resolve_path,
    clean_movie_tags,
    format_file_size,
    format_movie,
    get_actress_names,
    get_excel,
    parse_size_to_bytes,
)

actors_bp = Blueprint('actors', __name__)


@actors_bp.route('/api/actress/<name>/detail')
def api_actress_detail(name):
    excel = get_excel()
    records = [r for r in excel.get_all_movies()
               if (r.get('actor', '') or '').strip() == name]

    movies = [format_movie(r) for r in records]
    tag_counts: dict[str, int] = {}
    rating_dist: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    rated = 0
    total_size = 0

    for r in records:
        tags_str = r.get('tags', '')
        if tags_str:
            for t in tags_str.split(','):
                t = t.strip()
                if t:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
        rating = r.get('rating', '0')
        if rating and rating != '0':
            r_int = int(rating)
            if 1 <= r_int <= 5:
                rating_dist[r_int] += 1
                rated += 1
        total_size += parse_size_to_bytes(r.get('file_size', '0'))

    top_tags = dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:15])
    avg_rating = round(
        sum(k * v for k, v in rating_dist.items()) / max(rated, 1), 1
    )

    actress_names = {name}
    for m in movies:
        m['tags'] = clean_movie_tags(m['tags'], actress_names)

    return jsonify({
        'name': name,
        'total': len(records),
        'rated': rated,
        'avg_rating': avg_rating,
        'total_size': format_file_size(total_size),
        'rating_distribution': rating_dist,
        'top_tags': top_tags,
        'movies': sorted(movies, key=lambda x: x['downloaded_at'], reverse=True),
    })


@actors_bp.route('/api/actors')
def api_actors():
    excel = get_excel()
    state = get_state()
    state.ensure_fresh(excel)
    return jsonify(state.actors_cache)
