import argparse
from core.config_manager import ConfigManager
from core.logger import Logger
from core.excel_manager import ExcelManager
from core.app_context import AppContext


def build_app(config_path='config.json'):
    config = ConfigManager(config_path)
    logger = Logger(config.get('log_config', {}))
    excel = ExcelManager(config.get('path_config', {}).get('excel_path'), logger)
    return AppContext(config, logger, excel)


def main():
    parser = argparse.ArgumentParser(description='电影自动化管理系统')
    parser.add_argument('--config', default='config.json', help='配置文件路径，默认 config.json')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('init', help='创建默认配置和 Excel 文件')
    subparsers.add_parser('scan', help='扫描下载目录并更新 Excel')
    subparsers.add_parser('classify', help='按演员或规则分类电影文件')
    subparsers.add_parser('copy', help='复制已管理的电影到目标目录')
    subparsers.add_parser('backup', help='备份当前 Excel 文件')
    fetch_parser = subparsers.add_parser('fetch', help='查询电影元数据并写入 Excel')
    fetch_parser.add_argument('--name', required=True, help='要查询的电影名称或代码')
    show_parser = subparsers.add_parser('show', help='显示 Excel 当前记录统计信息')
    show_parser.add_argument('--status', help='按状态过滤')

    args = parser.parse_args()
    ctx = build_app(args.config)

    if args.cli or args.command:
        from core.scanner import Scanner
        from core.classifier import Classifier
        from core.copier import Copier
        from core.metadata_fetcher import MetadataFetcher

        def run_command(command, fetch_name=None, status_filter=None):
            if command == 'init':
                ctx.excel.init_excel()
                ctx.logger.info('初始化完成：已创建 Excel 文件和默认配置（如有必要）。')
                return '初始化完成。'

            if command == 'scan':
                scanner = Scanner(ctx.config, ctx.excel, ctx.logger)
                total, added, updated = scanner.scan_new_movies()
                msg = f'扫描完成：共发现 {total} 个文件，新增 {added} 条，更新 {updated} 条。'
                ctx.logger.info(msg)
                ctx.maybe_backup()
                return msg

            if command == 'classify':
                classifier = Classifier(ctx.config, ctx.excel, ctx.logger)
                moved = classifier.classify_all()
                msg = f'分类完成：共移动 {moved} 个文件。'
                ctx.logger.info(msg)
                ctx.maybe_backup()
                return msg

            if command == 'copy':
                copier = Copier(ctx.config, ctx.excel, ctx.logger)
                copied = copier.copy_all()
                msg = f'复制完成：共复制 {copied} 个文件。'
                ctx.logger.info(msg)
                ctx.maybe_backup()
                return msg

            if command == 'backup':
                path = ctx.config.get('path_config', {}).get('backup_dir')
                ctx.excel.backup_excel(path)
                msg = 'Excel 文件备份完成。'
                ctx.logger.info(msg)
                return msg

            if command == 'fetch':
                fetcher = MetadataFetcher(ctx.config, ctx.logger)
                metadata = fetcher.fetch_metadata(fetch_name)
                if metadata:
                    return '\n'.join([f'{key}: {value}' for key, value in metadata.items()])
                return '未查询到元数据。'

            if command == 'show':
                records = ctx.excel.get_filtered_movies('status', status_filter) if status_filter else ctx.excel.get_all_movies()
                msg = f'当前记录数：{len(records)}'
                if records:
                    msg += f'\n第一条记录字段：{list(records[0].keys())}'
                return msg

            return '无效的操作。'

        if args.command:
            result = run_command(args.command, fetch_name=getattr(args, 'name', None), status_filter=getattr(args, 'status', None))
            print(result)
            return

    from ui.main_window import MainWindow
    window = MainWindow(ctx)
    window.run()


if __name__ == '__main__':
    main()
