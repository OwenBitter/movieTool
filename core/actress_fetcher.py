import os
import re
import requests
from bs4 import BeautifulSoup


class ActressFetcher:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        self.supported_formats = [fmt.lower() for fmt in self.config.get('format_config', {}).get('supported_formats', [])]
        self.download_dir = self.config.get('path_config', {}).get('download_dir')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_actress_name(self, code):
        url = f'https://www.njavtv.art/cn/{code.lower()}'
        try:
            r = self.session.get(url, timeout=30, verify=False)
            if r.status_code != 200:
                return None, f'页面不存在: {r.status_code}'
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text()
            match = re.search(r'女优[:：]\s*([^\n\r]+)', text)
            if not match:
                return None, '未找到演员信息'
            actress = match.group(1).strip()
            actress = actress.split(',')[0].strip()
            actress = actress.split(' (')[0].strip()
            return actress, 'ok'
        except Exception as exc:
            message = str(exc)
            return None, f'错误: {message}'

    @staticmethod
    def extract_code_from_filename(filename):
        name = os.path.splitext(filename)[0]
        match = re.search(r'([A-Z]{2,5}-\d{3,4})', name.upper())
        if match:
            return match.group(1)
        return None

    def process_folder(self, folder=None):
        folder = folder or self.download_dir
        if not folder or not os.path.exists(folder):
            raise FileNotFoundError(f'下载目录不存在: {folder}')

        results = []
        for root, _, files in os.walk(folder):
            for name in files:
                _, ext = os.path.splitext(name)
                if ext.lower() not in self.supported_formats:
                    continue
                file_path = os.path.abspath(os.path.join(root, name))
                code = self.extract_code_from_filename(name)
                if not code:
                    results.append((file_path, None, '无法提取代码'))
                    continue
                actress, status = self.get_actress_name(code)
                results.append((file_path, actress, status))
        return results

    def update_excel_with_actress(self, excel_manager, folder=None):
        results = self.process_folder(folder)
        success = 0
        failed = 0
        for file_path, actress, status in results:
            movie_info = {
                'file_name': os.path.basename(file_path),
                'movie_name': os.path.splitext(os.path.basename(file_path))[0],
                'file_path': file_path,
                'actor': actress or '',
                'status': 'new',
            }
            excel_manager.add_or_update_movie(movie_info)
            if status == 'ok' and actress:
                success += 1
            else:
                failed += 1
        return results, success, failed
