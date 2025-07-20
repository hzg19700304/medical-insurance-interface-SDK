"""
医保接口SDK - 通用医保接口调用SDK
支持多医院部署，兼容C/S和B/S架构
"""

__version__ = "1.0.0"
__author__ = "Medical Insurance SDK Team"

from .client import MedicalInsuranceClient
from .sdk import MedicalInsuranceSDK
from .utils.data_helper import DataHelper
from .async_processing import AsyncProcessor, TaskManager
from .exceptions import (
    MedicalInsuranceException,
    ValidationException,
    ConfigurationException,
    NetworkException,
)

__all__ = [
    "MedicalInsuranceClient",
    "MedicalInsuranceSDK",
    "DataHelper",
    "AsyncProcessor",
    "TaskManager",
    "MedicalInsuranceException",
    "ValidationException",
    "ConfigurationException",
    "NetworkException",
]
