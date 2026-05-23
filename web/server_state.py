"""In-memory cache for Flask API — eliminates redundant Excel reads per request.

All aggregation logic mirrors what web/app.py currently does inline.
Mutations call invalidate(); reads call ensure_fresh() for lazy rebuild.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from core.utils import format_file_size, parse_size_to_bytes


@dataclass
class ServerState:
    """Cached aggregations rebuilt from Excel only when dirty."""

    actors_cache: list = field(default_factory=list)
    tags_usage: dict = field(default_factory=dict)
    stats_cache: dict = field(default_factory=dict)
    stats_detail_cache: dict = field(default_factory=dict)

    _dirty: bool = True
    _dirty_at: float = 0.0

    def invalidate(self):
        self._dirty = True
        self._dirty_at = time.time()

    def ensure_fresh(self, excel):
        """Rebuild all caches from Excel if dirty."""
        if not self._dirty:
            return

        records = excel.get_all_movies()

        # ── Actors (mirrors api_actors) ────────────────────────────
        actors: dict[str, int] = {}
        for r in records:
            a = r.get('actor', '').strip() or '未分类'
            actors[a] = actors.get(a, 0) + 1
        self.actors_cache = sorted(
            [{'name': n, 'count': c} for n, c in actors.items()],
            key=lambda x: (-x['count'], x['name']),
        )

        # ── Tags usage (mirrors api_tags) ─────────────────────────
        self.tags_usage = {}
        for r in records:
            tags_str = r.get('tags', '')
            if tags_str:
                for t in tags_str.split(','):
                    t = t.strip()
                    if t:
                        self.tags_usage[t] = self.tags_usage.get(t, 0) + 1

        # ── Basic stats (mirrors api_stats) ───────────────────────
        total = len(records)
        actor_set: set[str] = set()
        classified = rated = tagged = 0
        for r in records:
            a = r.get('actor', '').strip()
            if a:
                actor_set.add(a)
            if r.get('status') == 'classified':
                classified += 1
            rating = r.get('rating', '0')
            if rating and rating != '0':
                rated += 1
            if r.get('tags', '').strip():
                tagged += 1

        self.stats_cache = {
            'total': total,
            'actors_count': len(actor_set),
            'classified': classified,
            'new': total - classified,
            'rated': rated,
            'tagged': tagged,
        }

        # ── Detailed stats (mirrors _aggregate_stats) ─────────────
        rating_dist: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        tag_counts: dict[str, int] = {}
        actor_counts: dict[str, int] = {}
        total_bytes = 0
        recent_7d = 0
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        for r in records:
            a = r.get('actor', '').strip()
            if a:
                actor_counts[a] = actor_counts.get(a, 0) + 1

            rating = r.get('rating', '0')
            if rating and rating != '0':
                r_int = int(rating)
                if 1 <= r_int <= 5:
                    rating_dist[r_int] += 1

            tags_str = r.get('tags', '')
            if tags_str:
                for t in tags_str.split(','):
                    t = t.strip()
                    if t:
                        tag_counts[t] = tag_counts.get(t, 0) + 1

            total_bytes += parse_size_to_bytes(r.get('file_size', '0'))

            dl = r.get('downloaded_at', '')
            if dl:
                try:
                    dl_date = datetime.strptime(dl[:10], '%Y-%m-%d')
                    if dl_date >= week_ago:
                        recent_7d += 1
                except ValueError:
                    pass

        rated_records = [
            int(r.get('rating', '0'))
            for r in records
            if r.get('rating', '0') and r.get('rating', '0') != '0'
        ]
        avg_rating = (
            round(sum(rated_records) / len(rated_records), 1)
            if rated_records
            else 0
        )

        self.stats_detail_cache = {
            'total': total,
            'classified': classified,
            'unclassified': total - classified,
            'rated': rated,
            'tagged': tagged,
            'top_actors': sorted(
                [{'name': n, 'count': c} for n, c in actor_counts.items()],
                key=lambda x: -x['count'],
            )[:10],
            'rating_distribution': rating_dist,
            'tag_counts': dict(
                sorted(tag_counts.items(), key=lambda x: -x[1])[:20]
            ),
            'total_size': format_file_size(total_bytes),
            'avg_rating': avg_rating,
            'recent_downloads': recent_7d,
        }

        self._dirty = False


# Module-level singleton
_state = ServerState()


def get_state() -> ServerState:
    return _state
