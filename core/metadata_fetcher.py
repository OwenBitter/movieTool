import requests


class MetadataFetcher:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        self.api_url = self.config.get('api_config', {}).get('movie_metadata_api')
        self.timeout = self.config.get('api_config', {}).get('api_timeout', 10)
        self.retry_count = self.config.get('api_config', {}).get('api_retry_count', 3)

    def fetch_metadata(self, movie_name):
        if not self.api_url:
            if self.logger:
                self.logger.warning('未配置元数据 API 地址。')
            return None

        params = {'title': movie_name}
        for attempt in range(1, self.retry_count + 1):
            try:
                response = requests.get(self.api_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                if self.validate_api_response(data):
                    return self.normalize_response(data)
                if self.logger:
                    self.logger.warning(f'API 返回数据格式不符合预期: {data}')
                break
            except requests.RequestException as exc:
                if self.logger:
                    self.logger.warning(f'第 {attempt} 次查询失败: {exc}')
        return None

    @staticmethod
    def validate_api_response(data):
        if not isinstance(data, dict):
            return False
        return any(key in data for key in ('title', 'actor', 'director', 'release_year', 'genre', 'rating'))

    @staticmethod
    def normalize_response(data):
        return {
            'title': data.get('title'),
            'actor': data.get('actor'),
            'director': data.get('director'),
            'release_year': data.get('release_year'),
            'genre': data.get('genre'),
            'rating': data.get('rating')
        }
