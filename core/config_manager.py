import json
import os


class ConfigManager:
    DEFAULT_CONFIG = {
        'path_config': {
            'download_dir': '',
            'classify_dir': '',
            'excel_path': './电影管理.xlsx',
            'copy_target_dir': '',
            'backup_dir': './backups'
        },
        'format_config': {
            'supported_formats': ['.mp4', '.mkv', '.avi', '.mov', '.rmvb', '.flv', '.wmv']
        },
        'backup_config': {
            'backup_frequency': 'every_operation',
            'backup_retention': 10
        },
        'log_config': {
            'log_path': './logs',
            'log_level': 'info',
            'log_retention_days': 30
        },
        'api_config': {
            'movie_metadata_api': 'https://api.example.com/movie/metadata',
            'api_timeout': 10,
            'api_retry_count': 3
        }
    }

    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = {}
        self.load_config()
        self.validate_config()
        self.ensure_paths()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as handle:
                    self.config = json.load(handle)
            except (ValueError, OSError):
                # Backup broken file before overwriting
                import shutil
                bak = self.config_path + '.bak'
                shutil.copy2(self.config_path, bak)
                self.config = self.DEFAULT_CONFIG.copy()
                self.save_config()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as handle:
            json.dump(self.config, handle, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_path_config(self):
        return self.config.get('path_config', {})

    def update_config(self, section, key, value):
        if section in self.config and isinstance(self.config[section], dict):
            self.config[section][key] = value
            self.save_config()
            return True
        return False

    def validate_config(self):
        if 'path_config' not in self.config:
            self.config['path_config'] = self.DEFAULT_CONFIG['path_config'].copy()
        if 'format_config' not in self.config:
            self.config['format_config'] = self.DEFAULT_CONFIG['format_config'].copy()
        if 'backup_config' not in self.config:
            self.config['backup_config'] = self.DEFAULT_CONFIG['backup_config'].copy()
        if 'log_config' not in self.config:
            self.config['log_config'] = self.DEFAULT_CONFIG['log_config'].copy()
        if 'api_config' not in self.config:
            self.config['api_config'] = self.DEFAULT_CONFIG['api_config'].copy()

        path_config = self.config['path_config']
        for key, value in self.DEFAULT_CONFIG['path_config'].items():
            if key not in path_config or not path_config[key]:
                path_config[key] = value

        format_config = self.config['format_config']
        if 'supported_formats' not in format_config or not isinstance(format_config['supported_formats'], list):
            format_config['supported_formats'] = self.DEFAULT_CONFIG['format_config']['supported_formats']

        backup_config = self.config['backup_config']
        if backup_config.get('backup_frequency') not in ('every_operation', 'daily', 'weekly'):
            backup_config['backup_frequency'] = self.DEFAULT_CONFIG['backup_config']['backup_frequency']
        if not isinstance(backup_config.get('backup_retention'), int):
            backup_config['backup_retention'] = self.DEFAULT_CONFIG['backup_config']['backup_retention']

        log_config = self.config['log_config']
        if log_config.get('log_level') not in ('debug', 'info', 'warning', 'error'):
            log_config['log_level'] = self.DEFAULT_CONFIG['log_config']['log_level']
        if not isinstance(log_config.get('log_retention_days'), int):
            log_config['log_retention_days'] = self.DEFAULT_CONFIG['log_config']['log_retention_days']

        api_config = self.config['api_config']
        if not api_config.get('movie_metadata_api'):
            api_config['movie_metadata_api'] = self.DEFAULT_CONFIG['api_config']['movie_metadata_api']
        if not isinstance(api_config.get('api_timeout'), int):
            api_config['api_timeout'] = self.DEFAULT_CONFIG['api_config']['api_timeout']
        if not isinstance(api_config.get('api_retry_count'), int):
            api_config['api_retry_count'] = self.DEFAULT_CONFIG['api_config']['api_retry_count']

    def ensure_paths(self):
        path_config = self.config['path_config']
        for key in ('download_dir', 'classify_dir', 'backup_dir'):
            value = self.expand_path(path_config.get(key))
            if value and not os.path.exists(value):
                os.makedirs(value, exist_ok=True)
                path_config[key] = value

        log_path = self.expand_path(self.config['log_config'].get('log_path'))
        if log_path and not os.path.exists(log_path):
            os.makedirs(log_path, exist_ok=True)
            self.config['log_config']['log_path'] = log_path

        excel_path = self.expand_path(path_config.get('excel_path'))
        if excel_path:
            parent = os.path.dirname(excel_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            path_config['excel_path'] = excel_path

    @staticmethod
    def expand_path(path_value):
        if not path_value:
            return path_value
        expanded = os.path.expandvars(path_value)
        expanded = os.path.expanduser(expanded)
        return os.path.abspath(expanded)
