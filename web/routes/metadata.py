"""Metadata scan routes — ffprobe video files and auto-tag in Excel."""

import json
import os
import subprocess
import threading
import uuid

from flask import Blueprint, jsonify, request

from web.shared import _load_config, get_excel, get_task_tracker, invalidate_excel_cache
from web.server_state import get_state

metadata_bp = Blueprint('metadata', __name__)

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.ts', '.m2ts', '.iso', '.rmvb'}


def _probe_video(file_path: str) -> dict | None:
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_streams', '-select_streams', 'v:0', file_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        return streams[0] if streams else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def _classify_resolution(width: int) -> str:
    if width >= 3840:
        return '4K'
    elif width >= 1920:
        return '1080p'
    elif width >= 1280:
        return '720p'
    return ''


def _extract_frame_rate(stream: dict) -> float:
    fps_str = stream.get('r_frame_rate', '0/1')
    try:
        num, den = fps_str.split('/')
        return float(num) / float(den)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _run_metadata_scan(task_id: str):
    tracker = get_task_tracker()
    try:
        config = _load_config()
        excel_path = config.get('path_config', {}).get('excel_path', './电影管理.xlsx')
        excel = get_excel()
        records = excel.get_all_movies()

        # Filter to only existing video files
        videos = []
        for r in records:
            fp = r.get('file_path', '')
            ext = os.path.splitext(fp)[1].lower()
            if fp and os.path.exists(fp) and ext in VIDEO_EXTENSIONS:
                videos.append(r)

        total = len(videos)
        tracker.update(task_id, total=total, done=0, current='Starting scan...')

        tags_added: dict[str, int] = {}
        done = 0

        for r in videos:
            file_path = r.get('file_path', '')
            movie_id = r.get('movie_id', '')
            fname = os.path.basename(file_path)
            tracker.update(task_id, done=done + 1, current=fname)

            stream = _probe_video(file_path)
            if not stream:
                done += 1
                continue

            width = stream.get('width', 0)
            fps = _extract_frame_rate(stream)
            codec = stream.get('codec_name', '')
            color_space = stream.get('color_space', '')

            new_tags = []
            res_tag = _classify_resolution(width)
            if res_tag:
                new_tags.append(res_tag)
            if fps >= 55:
                new_tags.append('60fps')
            if codec in ('hevc', 'h265', 'av1'):
                new_tags.append(codec.upper())
            if 'bt2020' in str(color_space).lower():
                new_tags.append('HDR')

            if new_tags:
                existing_tags = [t.strip() for t in r.get('tags', '').split(',') if t.strip()]
                added = [t for t in new_tags if t not in existing_tags]
                if added:
                    r['tags'] = ','.join(existing_tags + added)
                    for t in added:
                        tags_added[t] = tags_added.get(t, 0) + 1

            done += 1

        # Persist tag changes to Excel
        excel_data = get_excel()
        sheet = excel_data.sheet
        tag_col = excel_data._get_column_index('tags')
        for row in sheet.iter_rows(min_row=2):
            mid = str(row[0].value or '')
            for r in videos:
                if r.get('movie_id') == mid and 'tags' in r:
                    row[tag_col].value = r['tags']
                    break

        excel_data.save()
        invalidate_excel_cache()
        get_state().invalidate()

        msg = ', '.join(f'{t}:{c}' for t, c in sorted(tags_added.items())) or 'No new tags'
        tracker.update(task_id, done=done, current=f'Done: {msg}')
        tracker.add_message(task_id, f'Scan complete: {msg}')
    except Exception as e:
        tracker.update(task_id, current=f'Error: {e}')
        tracker.add_message(task_id, f'Error: {e}')
    finally:
        tracker.finish(task_id)


@metadata_bp.route('/api/metadata/scan', methods=['POST'])
def api_metadata_scan():
    task_id = uuid.uuid4().hex[:12]
    tracker = get_task_tracker()
    tracker.create(task_id)

    thread = threading.Thread(target=_run_metadata_scan, args=(task_id,), daemon=True)
    thread.start()

    return jsonify({'task_id': task_id})


@metadata_bp.route('/api/metadata/status')
def api_metadata_status():
    task_id = request.args.get('task_id', '')
    tracker = get_task_tracker()
    if not task_id:
        return jsonify({'running': False, 'total': 0, 'done': 0, 'current': ''})
    task = tracker.get(task_id)
    return jsonify({
        'running': task.get('running', False),
        'total': task.get('total', 0),
        'done': task.get('done', 0),
        'current': task.get('current', ''),
    })
