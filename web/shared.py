"""Shared helpers for the web app — config, Excel, filtering, path utilities, and task tracking.

All route blueprint modules import from here to avoid circular imports with app.py.
"""

import csv as csv_mod
import io
import json
import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from flask import Response, send_from_directory, send_file

from core.excel_manager import ExcelManager
from core.tag_utils import merge_tags
from core.utils import format_file_size, parse_size_to_bytes


CONFIG_PATH = str(Path(__file__).resolve().parent.parent / 'config.json')
DIST_DIR = str(Path(__file__).resolve().parent / 'static' / 'dist')


# ─── Tag cleaning ───────────────────────────────────────────────────────────

_JAPANESE_RE = re.compile(r'[぀-ゟ゠-ヿ]')

# Traditional-only Chinese chars that appear in our tag data (never used in simplified)
# Traditional-only Chinese chars common in tag data (never used in simplified)
_TRADITIONAL_CHARS = set('單體戲劇獨畫質碼賽藝數風關學條癡聖爲與從雲馬龍龜裏響聽貓臺灣係將帶連進過邊隊戰勝敗護詞彙選擇導團區傷麵開軌婦蕩輕艷戀亂顏淩戀憂鬱驗驚懼廣慶實當歸變獸廳選樣準讓認試識護導團區傷軌婦蕩輕艷戀亂顏戀憂鬱驗驚懼廣慶實當歸變獸廳選樣準讓認試亜')


def _has_traditional(text: str) -> bool:
    """Check if text contains any traditional-only Chinese character."""
    return any(c in _TRADITIONAL_CHARS for c in text)


def clean_movie_tags(tags_str: str, actress_names: set[str]) -> str:
    """Remove actress names, Japanese-only, and traditional Chinese tags."""
    if not tags_str:
        return ''
    clean = []
    for t in tags_str.split(','):
        t = t.strip()
        if not t:
            continue
        if t in actress_names:
            continue
        if _JAPANESE_RE.search(t):
            continue
        if _has_traditional(t):
            continue
        clean.append(t)
    return ','.join(clean)


def get_actress_names(excel) -> set[str]:
    """Extract all unique actress/actor names from Excel records."""
    names = set()
    for r in excel.get_all_movies():
        a = (r.get('actor', '') or '').strip()
        if a:
            names.add(a)
    return names


# ─── Config loading ─────────────────────────────────────────────────────

def _load_config():
    """Load config.json on demand (supports runtime updates)."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'path_config': {'excel_path': './电影管理.xlsx', 'backup_dir': './backups'},
            'tag_config': {},
        }


# ─── Excel cache (TTL) ──────────────────────────────────────────────────

_excel_cache = None
_cache_loaded_at = 0
EXCEL_CACHE_TTL = 30  # seconds


def get_excel():
    global _excel_cache, _cache_loaded_at
    now = time.time()
    if _excel_cache is not None and (now - _cache_loaded_at) < EXCEL_CACHE_TTL:
        return _excel_cache
    config = _load_config()
    excel_path = config.get('path_config', {}).get('excel_path', './电影管理.xlsx')
    _excel_cache = ExcelManager(excel_path)
    _cache_loaded_at = now
    return _excel_cache


def invalidate_excel_cache():
    global _excel_cache, _cache_loaded_at
    _excel_cache = None
    _cache_loaded_at = 0


def get_tag_config():
    return _load_config().get('tag_config', {})


def get_available_tags():
    return get_tag_config().get('available_tags', [])


# ─── Filtering / formatting ─────────────────────────────────────────────

def filter_records(records, actor='', tags_filter=None, rating_min=0, status='', search='',
                    size_min=None, size_max=None, date_from='', date_to=''):
    """Shared filtering logic used by /api/movies, export, and open-filtered.
    Works on raw Excel records (tags as comma-separated string, rating as string).
    size_min/size_max in GB (float), date_from/date_to as YYYY-MM-DD strings."""
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
        if size_min is not None or size_max is not None:
            size_bytes = parse_size_to_bytes(r.get('file_size', ''))
            if size_min is not None and size_bytes < int(size_min * 1024**3):
                continue
            if size_max is not None and size_bytes > int(size_max * 1024**3):
                continue
        if date_from or date_to:
            dl_date = (r.get('downloaded_at') or '').strip()
            if date_from and dl_date < date_from:
                continue
            if date_to and dl_date > date_to:
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


# ─── Path helpers ───────────────────────────────────────────────────────

def _wsl_to_win(wsl_path):
    """Convert /mnt/e/... → E:\\..."""
    if wsl_path.startswith('/mnt/'):
        drive = wsl_path[5:6].upper()
        return f'{drive}:' + wsl_path[6:].replace('/', '\\')
    return wsl_path.replace('/', '\\')


def _resolve_path(wsl_path: str) -> str:
    """Convert a WSL path to a path the current OS can open.

    On Windows Python, /mnt/e/... → E:\\...
    On WSL/Linux Python, /mnt/e/... stays as-is.
    """
    if not wsl_path:
        return wsl_path
    if os.name == 'nt':
        return _wsl_to_win(wsl_path)
    return wsl_path


def _resolve_movie(excel, movie_id):
    """Return (row, resolved_path) or (None, None) if not found."""
    row = excel.find_row_by_id(movie_id)
    if not row:
        return None, None
    fp = (row[excel._get_column_index('file_path')].value or '').strip()
    return row, _resolve_path(fp)


def _collect_files_by_ids(excel, ids):
    """Collect (resolved_path, display_name) for given movie IDs."""
    files = []
    fp_idx = excel._get_column_index('file_path')
    fn_idx = excel._get_column_index('file_name')
    for mid in ids:
        row = excel.find_row_by_id(mid)
        if row:
            fp = _resolve_path((row[fp_idx].value or '').strip())
            fn = (row[fn_idx].value or '').strip()
            if fp and os.path.exists(fp):
                files.append((fp, fn))
    return files


def _collect_files_by_filter(excel, data):
    """Collect files matching filter criteria in data dict."""
    actor = data.get('actor', '').strip()
    tags_filter = [t.strip() for t in data.get('tags', '').split(',') if t.strip()]
    rating_min = data.get('rating_min', 0)
    status = data.get('status', '').strip()
    search = (data.get('search', '') or '').strip().lower()

    records = excel.get_all_movies()
    filtered = filter_records(records, actor=actor, tags_filter=tags_filter,
                              rating_min=rating_min, status=status, search=search)
    files = []
    for r in filtered:
        fp = _resolve_path((r.get('file_path') or '').strip())
        fn = (r.get('file_name') or '').strip()
        if fp and os.path.exists(fp):
            files.append((fp, fn))
    return files


# ─── Task tracker (SSE progress) ────────────────────────────────────────

class TaskTracker:
    """In-memory task progress store for SSE endpoints."""

    def __init__(self):
        self._tasks: dict = {}
        self._lock = threading.Lock()

    def create(self, task_id: str):
        with self._lock:
            self._tasks[task_id] = {
                'running': True,
                'total': 0,
                'done': 0,
                'current': '',
                'messages': [],
            }

    def update(self, task_id: str, **kwargs):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(kwargs)

    def add_message(self, task_id: str, msg: str):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]['messages'].append(msg)
                if len(self._tasks[task_id]['messages']) > 100:
                    self._tasks[task_id]['messages'] = self._tasks[task_id]['messages'][-100:]

    def get(self, task_id: str) -> dict:
        with self._lock:
            return dict(self._tasks.get(task_id, {}))

    def finish(self, task_id: str):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]['running'] = False


_task_tracker = TaskTracker()


def get_task_tracker() -> TaskTracker:
    return _task_tracker


# ─── Shortcut helpers ────────────────────────────────────────────────────

def _create_shortcuts(files, link_dir):
    """Create .lnk shortcuts in link_dir via PowerShell COM. Returns count created."""
    if os.path.exists(link_dir):
        for f in os.listdir(link_dir):
            try:
                os.unlink(os.path.join(link_dir, f))
            except OSError:
                pass
    else:
        os.makedirs(link_dir, exist_ok=True)

    created = 0
    for src_wsl, fname in files:
        src_win = _wsl_to_win(src_wsl)
        link_name = os.path.splitext(fname)[0] + '.lnk'
        link_wsl = os.path.join(link_dir, link_name)
        link_win = _wsl_to_win(link_wsl)

        base = os.path.splitext(fname)[0]
        counter = 1
        while os.path.exists(link_wsl):
            link_name = f'{base}_{counter}.lnk'
            link_wsl = os.path.join(link_dir, link_name)
            link_win = _wsl_to_win(link_wsl)
            counter += 1

        safe_link_win = link_win.replace("'", "''")
        safe_src_win = src_win.replace("'", "''")
        ps_cmd = (
            f"$ws=New-Object -ComObject WScript.Shell;"
            f"$sc=$ws.CreateShortcut('{safe_link_win}');"
            f"$sc.TargetPath='{safe_src_win}';"
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
    return created
