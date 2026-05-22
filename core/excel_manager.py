import hashlib
import os
import shutil
from datetime import datetime

from openpyxl import Workbook, load_workbook


class ExcelManager:
    # Internal programmatic keys (used in all code)
    HEADERS = [
        'movie_id',       # 编号
        'file_name',      # 文件名
        'movie_name',     # 影片名称
        'actor',          # 演员
        'release_year',   # 发行年份
        'rating',         # 评分 (1-5, 0=未评分)
        'file_size',      # 文件大小
        'file_path',      # 文件路径
        'status',         # 状态
        'tags',           # 标签 (逗号分隔)
        'downloaded_at',  # 下载时间
    ]

    # Chinese display labels written to Excel header row
    HEADER_LABELS = {
        'movie_id': '编号',
        'file_name': '文件名',
        'movie_name': '影片名称',
        'actor': '演员',
        'release_year': '发行年份',
        'rating': '评分',
        'file_size': '文件大小',
        'file_path': '文件路径',
        'status': '状态',
        'tags': '标签',
        'downloaded_at': '下载时间',
    }

    # Reverse mapping: Chinese label → English key (built at load time)
    _label_to_key = {}

    def __init__(self, excel_path, logger=None):
        self.excel_path = os.path.abspath(excel_path)
        self.logger = logger
        if not os.path.exists(self.excel_path):
            self.init_excel()
        self.load_workbook()

    def load_workbook(self):
        self.wb = load_workbook(self.excel_path)
        self.sheet = self.wb.active
        self._build_label_mapping()

    def _build_label_mapping(self):
        """Map Excel header row (Chinese labels) back to internal English keys."""
        self._label_to_key = {}
        header_row = [cell.value for cell in self.sheet[1]]
        for idx, label in enumerate(header_row):
            if label is None:
                continue
            # Try reverse lookup from HEADER_LABELS
            for key, cn_label in self.HEADER_LABELS.items():
                if cn_label == str(label).strip():
                    self._label_to_key[idx] = key
                    break
            else:
                # Legacy: try English header directly
                if str(label).strip() in self.HEADERS:
                    self._label_to_key[idx] = str(label).strip()

    def save(self):
        self.wb.save(self.excel_path)

    def init_excel(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Movies'
        # Write Chinese header row
        chinese_headers = [self.HEADER_LABELS[h] for h in self.HEADERS]
        sheet.append(chinese_headers)
        parent = os.path.dirname(self.excel_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        workbook.save(self.excel_path)
        if self.logger:
            self.logger.info(f'创建 Excel 文件：{self.excel_path}')

    def backup_excel(self, backup_dir):
        if not backup_dir:
            raise ValueError('需要提供备份目录。')
        backup_dir = os.path.abspath(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(self.excel_path)
        target = os.path.join(backup_dir, f'{timestamp}_{filename}')
        shutil.copy2(self.excel_path, target)
        if self.logger:
            self.logger.info(f'备份 Excel 到：{target}')
        return target

    def generate_movie_id(self, file_path):
        digest = hashlib.sha1(file_path.encode('utf-8')).hexdigest()
        return digest[:12].upper()

    @staticmethod
    def _normalize(value):
        if value is None:
            return ''
        return str(value).strip()

    def _get_column_index(self, key):
        """Get 0-based column index for an internal English key."""
        return self.HEADERS.index(key)

    def _row_to_record(self, values):
        """Convert a row of cell values to a {key: value} dict with English keys."""
        record = {}
        for col_idx, value in enumerate(values):
            key = self._label_to_key.get(col_idx)
            if key:
                record[key] = self._normalize(value)
        for key in self.HEADERS:
            if key not in record:
                record[key] = ''
        return record

    def find_row_by_path(self, file_path):
        file_path = os.path.abspath(file_path)
        fp_idx = self._get_column_index('file_path')
        for row in self.sheet.iter_rows(min_row=2):
            cell_path = self._normalize(row[fp_idx].value)
            if os.path.abspath(cell_path) == file_path:
                return row
        return None

    def find_row_by_id(self, movie_id):
        mid_idx = self._get_column_index('movie_id')
        for row in self.sheet.iter_rows(min_row=2):
            if self._normalize(row[mid_idx].value) == movie_id:
                return row
        return None

    def get_all_movies(self):
        """Return list of dicts with English keys, mapped from Excel columns."""
        records = []
        for row in self.sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            records.append(self._row_to_record(row))
        return records

    def get_filtered_movies(self, field_name, field_value):
        if field_name not in self.HEADERS:
            return []
        col_idx = self._get_column_index(field_name)
        results = []
        for row in self.sheet.iter_rows(min_row=2, values_only=True):
            value = row[col_idx]
            if value is not None and str(value).strip() == str(field_value).strip():
                results.append(self._row_to_record(row))
        return results

    def _get_file_download_time(self, file_path):
        """Get file modification time as the best proxy for download time."""
        try:
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except OSError:
            pass
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def add_or_update_movie(self, movie_info):
        file_path = os.path.abspath(movie_info.get('file_path', ''))
        if not file_path:
            raise ValueError('movie_info 必须包含 file_path。')

        row = self.find_row_by_path(file_path)
        data = {key: self._normalize(movie_info.get(key, '')) for key in self.HEADERS}
        data['file_path'] = file_path
        if not data['movie_id']:
            data['movie_id'] = self.generate_movie_id(file_path)
        if not data['movie_name']:
            data['movie_name'] = self._normalize(os.path.splitext(data['file_name'])[0])
        if not data['downloaded_at']:
            data['downloaded_at'] = self._get_file_download_time(file_path)

        if row:
            # Update existing row
            for key in self.HEADERS:
                if data[key]:
                    col_idx = self._get_column_index(key)
                    row[col_idx].value = data[key]
            # Preserve downloaded_at for existing rows unless explicitly updated
            if not movie_info.get('downloaded_at'):
                dl_idx = self._get_column_index('downloaded_at')
                # Don't overwrite — keep existing value
                pass
            self.save()
            return 'updated'

        # New row
        sheet_row = [data.get(key, '') for key in self.HEADERS]
        self.sheet.append(sheet_row)
        self.save()
        return 'added'

    def update_movie(self, movie_id, update_data):
        row = self.find_row_by_id(movie_id)
        if not row:
            return False
        for key, value in update_data.items():
            if key in self.HEADERS:
                col_idx = self._get_column_index(key)
                row[col_idx].value = self._normalize(value)
        # Do NOT auto-overwrite downloaded_at — only update if explicitly provided
        self.save()
        return True
