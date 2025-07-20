"""HTTP客户端工具类"""

from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HTTPClient:
    """HTTP客户端"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化HTTP客户端

        Args:
            config: HTTP配置
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
        self.pool_connections = self.config.get("pool_connections", 10)
        self.pool_maxsize = self.config.get("pool_maxsize", 10)

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.pool_connections,
            pool_maxsize=self.pool_maxsize,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """发送POST请求

        Args:
            url: 请求URL
            json: JSON数据
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 响应数据

        Raises:
            requests.RequestException: 请求失败时抛出异常
        """
        try:
            response = self.session.post(
                url=url,
                json=json,
                headers=headers,
                timeout=kwargs.get("timeout", self.timeout),
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            # TODO: 添加更详细的错误处理和日志记录
            raise e

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """发送GET请求

        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 响应数据
        """
        try:
            response = self.session.get(
                url=url,
                params=params,
                headers=headers,
                timeout=kwargs.get("timeout", self.timeout),
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            # TODO: 添加更详细的错误处理和日志记录
            raise e

    def close(self):
        """关闭HTTP会话"""
        if self.session:
            self.session.close()
