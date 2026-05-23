"""SSE progress endpoint for long-running operations."""

import json
import time

from flask import Blueprint, Response

from web.shared import get_task_tracker

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/api/progress/<task_id>')
def api_progress(task_id):
    """Server-Sent Events stream for task progress."""
    tracker = get_task_tracker()

    def generate():
        last_data = None
        while True:
            task = tracker.get(task_id)
            if not task:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                return

            current_data = json.dumps({
                'running': task.get('running', False),
                'total': task.get('total', 0),
                'done': task.get('done', 0),
                'current': task.get('current', ''),
            }, ensure_ascii=False)

            if current_data != last_data:
                yield f"data: {current_data}\n\n"
                last_data = current_data

            if not task.get('running'):
                return

            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
