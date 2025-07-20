"""HTTP客户端模块

提供HTTP请求功能，包括连接池管理、超时设置、重试机制和错误处理。
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ..exceptions import NetworkException, MedicalInsuranceException


logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP客户端类
    
    提供HTTP请求功能，支持连接池、超时设置、重试机制和错误处理。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化HTTP客户端
        
        Args:
            config: HTTP客户端配置
                - timeout: 请求超时时间（秒），默认30
                - max_retries: 最大重试次数，默认3
                - backoff_factor: 重试间隔因子，默认0.3
                - pool_connections: 连接池大小，默认10
                - pool_maxsize: 连接池最大连接数，默认10
                - status_forcelist: 需要重试的HTTP状态码列表
        """
        self.config = config or {}
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """创建HTTP会话，配置连接池和重试策略"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.config.get('max_retries', 3),
            backoff_factor=self.config.get('backoff_factor', 0.3),
            status_forcelist=self.config.get('status_forcelist', [429, 500, 502, 503, 504]),
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(
            pool_connections=self.config.get('pool_connections', 10),
            pool_maxsize=self.config.get('pool_maxsize', 10),
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def post(self, url: str, data: Optional[Union[Dict, str]] = None, 
             json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
             timeout: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """发送POST请求
        
        Args:
            url: 请求URL
            data: 请求数据（字符串或字典）
            json_data: JSON格式请求数据
            headers: 请求头
            timeout: 超时时间（秒）
            **kwargs: 其他requests参数
            
        Returns:
            响应数据字典
            
        Raises:
            NetworkException: 网络请求异常
        """
        return self._request('POST', url, data=data, json=json_data, 
                           headers=headers, timeout=timeout, **kwargs)
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None,
            **kwargs) -> Dict[str, Any]:
        """发送GET请求
        
        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            timeout: 超时时间（秒）
            **kwargs: 其他requests参数
            
        Returns:
            响应数据字典
            
        Raises:
            NetworkException: 网络请求异常
        """
        return self._request('GET', url, params=params, headers=headers, 
                           timeout=timeout, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求的内部方法
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 请求参数
            
        Returns:
            响应数据字典
            
        Raises:
            NetworkException: 网络请求异常
        """
        # 设置默认超时时间
        timeout = kwargs.pop('timeout', None) or self.config.get('timeout', 30)
        
        # 设置默认请求头
        headers = kwargs.get('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'MedicalInsuranceSDK/1.0'
        kwargs['headers'] = headers
        
        start_time = time.time()
        
        try:
            logger.info(f"发送{method}请求: {url}")
            logger.debug(f"请求参数: {kwargs}")
            
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            
            # 记录响应时间
            response_time = time.time() - start_time
            logger.info(f"请求完成，耗时: {response_time:.3f}秒，状态码: {response.status_code}")
            
            # 检查HTTP状态码
            if not response.ok:
                error_msg = f"HTTP请求失败: {response.status_code} {response.reason}"
                logger.error(f"{error_msg}, 响应内容: {response.text[:500]}")
                raise NetworkException(
                    error_msg,
                    status_code=response.status_code,
                    response_body=response.text
                )
            
            # 解析响应数据
            return self._parse_response(response)
            
        except requests.exceptions.Timeout as e:
            error_msg = f"请求超时: {url} (超时时间: {timeout}秒)"
            logger.error(error_msg)
            raise NetworkException(error_msg) from e
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接错误: {url}"
            logger.error(f"{error_msg}, 详细信息: {str(e)}")
            raise NetworkException(error_msg) from e
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {url}"
            logger.error(f"{error_msg}, 详细信息: {str(e)}")
            raise NetworkException(error_msg) from e
            
        except Exception as e:
            error_msg = f"未知错误: {url}"
            logger.error(f"{error_msg}, 详细信息: {str(e)}")
            raise MedicalInsuranceException(error_msg) from e
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """解析HTTP响应
        
        Args:
            response: HTTP响应对象
            
        Returns:
            解析后的响应数据
            
        Raises:
            NetworkException: 响应解析异常
        """
        try:
            # 尝试解析JSON响应
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            
            # 尝试解析文本响应为JSON
            response_text = response.text.strip()
            if response_text.startswith('{') or response_text.startswith('['):
                return json.loads(response_text)
            
            # 返回文本响应
            return {'text': response_text, 'status_code': response.status_code}
            
        except json.JSONDecodeError as e:
            logger.warning(f"响应不是有效的JSON格式: {response.text[:200]}")
            return {
                'text': response.text,
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
        except Exception as e:
            error_msg = f"响应解析失败: {str(e)}"
            logger.error(error_msg)
            raise NetworkException(error_msg) from e
    
    def close(self):
        """关闭HTTP会话"""
        if self.session:
            self.session.close()
            logger.info("HTTP会话已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class MedicalInsuranceHTTPClient(HTTPClient):
    """医保专用HTTP客户端
    
    针对医保接口的特殊需求进行优化。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化医保HTTP客户端
        
        Args:
            config: HTTP客户端配置
        """
        # 医保接口的默认配置
        default_config = {
            'timeout': 30,
            'max_retries': 3,
            'backoff_factor': 0.5,
            'pool_connections': 20,
            'pool_maxsize': 20,
            'status_forcelist': [429, 500, 502, 503, 504]
        }
        
        if config:
            default_config.update(config)
            
        super().__init__(default_config)
    
    def call_medical_api(self, url: str, request_data: Dict[str, Any], 
                        headers: Dict[str, str], timeout: Optional[int] = None) -> Dict[str, Any]:
        """调用医保接口的专用方法
        
        Args:
            url: 医保接口URL
            request_data: 请求数据
            headers: 请求头（包含网关认证信息）
            timeout: 超时时间
            
        Returns:
            医保接口响应数据
            
        Raises:
            NetworkException: 网络请求异常
        """
        logger.info(f"调用医保接口: {url}")
        logger.debug(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        # 医保接口通常使用text/plain格式发送JSON数据
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'text/plain; charset=utf-8'
        
        # 将请求数据转换为JSON字符串
        json_str = json.dumps(request_data, ensure_ascii=False, separators=(',', ':'))
        
        try:
            response_data = self.post(
                url=url,
                data=json_str,
                headers=headers,
                timeout=timeout
            )
            
            logger.debug(f"医保接口响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return response_data
            
        except NetworkException as e:
            logger.error(f"医保接口调用失败: {str(e)}")
            raise
        except Exception as e:
            error_msg = f"医保接口调用异常: {str(e)}"
            logger.error(error_msg)
            raise NetworkException(error_msg) from e