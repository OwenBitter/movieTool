"""Application context — holds shared ConfigManager, Logger, ExcelManager instances."""


class AppContext:
    """Shared application context passed to CLI, UI, and Web components."""

    def __init__(self, config, logger, excel):
        self.config = config
        self.logger = logger
        self.excel = excel

    def maybe_backup(self):
        """Backup Excel if backup_frequency is 'every_operation'."""
        backup_config = self.config.get('backup_config', {})
        if backup_config.get('backup_frequency') == 'every_operation':
            backup_dir = self.config.get('path_config', {}).get('backup_dir')
            if backup_dir:
                backup_target = self.excel.backup_excel(backup_dir)
                self.logger.info(f'已备份 Excel 到 {backup_target}')
                return backup_target
        return None
