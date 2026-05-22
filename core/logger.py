import logging
import os
from datetime import datetime, timedelta


class Logger:
    LEVEL_MAP = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
    }

    def __init__(self, config):
        self.log_dir = os.path.abspath(config.get('log_path', 'logs'))
        self.log_level = config.get('log_level', 'info').lower()
        self.retention_days = config.get('log_retention_days', 30)
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger = logging.getLogger('movie_automation_manager')
        self.logger.setLevel(self.LEVEL_MAP.get(self.log_level, logging.INFO))
        self.logger.propagate = False
        self._configure_handlers()
        self.clean_old_logs()

    def _configure_handlers(self):
        if self.logger.handlers:
            return
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(self.log_dir, f'movie_tool_{timestamp}.log')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

        file_handler = logging.FileHandler(filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.LEVEL_MAP.get(self.log_level, logging.INFO))
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.LEVEL_MAP.get(self.log_level, logging.INFO))
        self.logger.addHandler(console_handler)

    def clean_old_logs(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for item in os.listdir(self.log_dir):
            path = os.path.join(self.log_dir, item)
            if os.path.isfile(path):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(path))
                    if mtime < cutoff:
                        os.remove(path)
                except OSError:
                    pass

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)
