import os
import shutil


class Copier:
    def __init__(self, config, excel_manager, logger=None):
        self.config = config
        self.excel_manager = excel_manager
        self.logger = logger
        self.copy_target_dir = self.config.get('path_config', {}).get('copy_target_dir')

    def copy_all(self):
        if not self.copy_target_dir:
            raise ValueError('未配置复制目标目录。')
        os.makedirs(self.copy_target_dir, exist_ok=True)
        records = self.excel_manager.get_all_movies()
        copied = 0

        for record in records:
            source_path = record.get('file_path')
            if not source_path or not os.path.exists(source_path):
                continue
            target_path = os.path.join(self.copy_target_dir, os.path.basename(source_path))
            if self.is_duplicate(source_path, target_path):
                if self.logger:
                    self.logger.debug(f'目标文件已存在且相同，跳过: {target_path}')
                continue
            target_path = self._resolve_conflict(target_path)
            shutil.copy2(source_path, target_path)
            copied += 1
            if self.logger:
                self.logger.info(f'已复制: {source_path} -> {target_path}')

        return copied

    @staticmethod
    def is_duplicate(source_path, target_path):
        if not os.path.exists(target_path):
            return False
        try:
            return os.path.getsize(source_path) == os.path.getsize(target_path)
        except OSError:
            return False

    @staticmethod
    def _resolve_conflict(path):
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        index = 1
        while os.path.exists(path):
            path = f'{base}_{index}{ext}'
            index += 1
        return path
