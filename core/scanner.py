import os
from datetime import datetime

from core.utils import format_file_size


class Scanner:
    def __init__(self, config, excel_manager, logger=None):
        self.config = config
        self.excel_manager = excel_manager
        self.logger = logger
        self.download_dir = self.config.get('path_config', {}).get('download_dir')
        self.supported_formats = [fmt.lower() for fmt in self.config.get('format_config', {}).get('supported_formats', [])]

    def scan_new_movies(self):
        total = 0
        added = 0
        updated = 0
        if not self.download_dir or not os.path.exists(self.download_dir):
            raise FileNotFoundError(f'下载目录不存在: {self.download_dir}')

        for root, _, files in os.walk(self.download_dir):
            for name in files:
                _, ext = os.path.splitext(name)
                if ext.lower() not in self.supported_formats:
                    continue
                total += 1
                file_path = os.path.abspath(os.path.join(root, name))
                movie_info = self._build_movie_info(file_path)
                result = self.excel_manager.add_or_update_movie(movie_info, save=False)
                if result == 'added':
                    added += 1
                elif result == 'updated':
                    updated += 1
                if self.logger:
                    self.logger.debug(f'扫描到文件: {file_path} => {result}')

        # Single save after all files processed
        self.excel_manager.save()
        self.excel_manager._invalidate_row_index()
        return total, added, updated

    def _build_movie_info(self, file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        # Use file modification time as the best proxy for download time
        mtime = os.path.getmtime(file_path)
        downloaded_at = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        return {
            'file_name': file_name,
            'movie_name': os.path.splitext(file_name)[0],
            'file_path': file_path,
            'file_size': format_file_size(file_size),
            'status': 'new',
            'downloaded_at': downloaded_at
        }
