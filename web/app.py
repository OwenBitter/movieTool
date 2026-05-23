#!/usr/bin/env python3
"""电影分类浏览器 - Flask Web 后端 (纯数据服务)"""

import os
from pathlib import Path

# IMPORTANT: This file is designed to run from the project root:
#   cd /mnt/e/tools/movieTool && python3 web/app.py
# Or set PYTHONPATH:
#   PYTHONPATH=/mnt/e/tools/movieTool python3 web/app.py

from flask import Flask

from web.routes.spa import spa_bp
from web.routes.movies import movies_bp
from web.routes.actors import actors_bp
from web.routes.tags import tags_bp
from web.routes.stats import stats_bp
from web.routes.batch import batch_bp
from web.routes.files import files_bp
from web.routes.backups import backups_bp
from web.routes.progress import progress_bp
from web.routes.metadata import metadata_bp
from web.routes.watcher_routes import watcher_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(spa_bp)
app.register_blueprint(movies_bp)
app.register_blueprint(actors_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(batch_bp)
app.register_blueprint(files_bp)
app.register_blueprint(backups_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(metadata_bp)
app.register_blueprint(watcher_bp)

# Start file watcher in background
from web.watcher import get_watcher
get_watcher().start()


if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    use_production = os.environ.get('FLASK_PRODUCTION', '').lower() == 'true'

    if use_production:
        from waitress import serve
        print(f'🎬 电影分类浏览器 (生产模式): http://{host}:{port}')
        serve(app, host=host, port=port)
    else:
        print(f'🎬 电影分类浏览器启动: http://{host}:{port}')
        app.run(host=host, port=port, debug=debug)
