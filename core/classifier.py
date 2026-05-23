import os
import re
import shutil

from core.utils import resolve_conflict


class Classifier:
    def __init__(self, config, excel_manager, logger=None):
        self.config = config
        self.excel_manager = excel_manager
        self.logger = logger
        self.classify_dir = self.config.get('path_config', {}).get('classify_dir')

    def classify_all(self):
        moved = 0
        if not self.classify_dir:
            raise ValueError('未配置分类目录。')
        os.makedirs(self.classify_dir, exist_ok=True)
        records = self.excel_manager.get_all_movies()

        for record in records:
            file_path = record.get('file_path')
            if not file_path or not os.path.exists(file_path):
                continue
            status = (record.get('status') or '').strip().lower()
            if status == 'classified':
                continue
            actor = (record.get('actor') or '').strip() or self._sanitize_folder_name(record.get('movie_name') or 'Unknown')
            target_dir = os.path.join(self.classify_dir, self._sanitize_folder_name(actor))
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, os.path.basename(file_path))
            target_path = resolve_conflict(target_path)
            shutil.move(file_path, target_path)
            self.excel_manager.update_movie(record.get('movie_id'), {
                'file_path': target_path,
                'status': 'classified'
            })
            moved += 1
            if self.logger:
                self.logger.info(f'已移动: {file_path} -> {target_path}')

        return moved

    @staticmethod
    def _sanitize_folder_name(name):
        name = name.strip()
        return re.sub(r'[\\/:*?"<>|]+', '_', name)[:120]
