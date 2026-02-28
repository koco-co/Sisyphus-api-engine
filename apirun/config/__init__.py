"""配置管理系统 - 集中管理所有硬编码配置"""

from __future__ import annotations

import os
from typing import Any


class Config:
    """配置管理器 - 从环境变量和默认值加载配置"""

    # 安全配置
    MAX_RESPONSE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    MAX_SQL_LENGTH: int = 10000
    ENABLE_SQL_VALIDATION: bool = True

    # 性能配置
    REQUEST_TIMEOUT: int = 30  # 秒
    STEP_TIMEOUT: int = 300  # 5 分钟
    DB_POOL_SIZE: int = 5
    MAX_WORKERS: int = 4
    HTTP_MAX_RETRIES: int = 3  # HTTP 请求最大重试次数

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str | None = None
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CSV 配置
    MAX_CSV_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_CSV_ROWS: int = 1000000

    # 内存配置
    MAX_VARIABLE_SIZE: int = 10 * 1024 * 1024  # 10MB

    _instance: Config | None = None

    def __new__(cls) -> Config:
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_from_env()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例（主要用于测试）"""
        cls._instance = None

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 安全配置
        self.MAX_RESPONSE_SIZE = self._get_int(
            "SISYPHUS_MAX_RESPONSE_SIZE", self.MAX_RESPONSE_SIZE
        )
        self.MAX_FILE_SIZE = self._get_int("SISYPHUS_MAX_FILE_SIZE", self.MAX_FILE_SIZE)
        self.MAX_SQL_LENGTH = self._get_int("SISYPHUS_MAX_SQL_LENGTH", self.MAX_SQL_LENGTH)
        self.ENABLE_SQL_VALIDATION = self._get_bool(
            "SISYPHUS_ENABLE_SQL_VALIDATION", self.ENABLE_SQL_VALIDATION
        )

        # 性能配置
        self.REQUEST_TIMEOUT = self._get_int("SISYPHUS_REQUEST_TIMEOUT", self.REQUEST_TIMEOUT)
        self.STEP_TIMEOUT = self._get_int("SISYPHUS_STEP_TIMEOUT", self.STEP_TIMEOUT)
        self.DB_POOL_SIZE = self._get_int("SISYPHUS_DB_POOL_SIZE", self.DB_POOL_SIZE)
        self.MAX_WORKERS = self._get_int("SISYPHUS_MAX_WORKERS", self.MAX_WORKERS)
        self.HTTP_MAX_RETRIES = self._get_int("SISYPHUS_HTTP_MAX_RETRIES", self.HTTP_MAX_RETRIES)

        # 日志配置
        self.LOG_LEVEL = os.getenv("SISYPHUS_LOG_LEVEL", self.LOG_LEVEL)
        self.LOG_FILE = os.getenv("SISYPHUS_LOG_FILE", self.LOG_FILE)

        # CSV 配置
        self.MAX_CSV_SIZE = self._get_int("SISYPHUS_MAX_CSV_SIZE", self.MAX_CSV_SIZE)
        self.MAX_CSV_ROWS = self._get_int("SISYPHUS_MAX_CSV_ROWS", self.MAX_CSV_ROWS)

        # 内存配置
        self.MAX_VARIABLE_SIZE = self._get_int(
            "SISYPHUS_MAX_VARIABLE_SIZE", self.MAX_VARIABLE_SIZE
        )

    def _get_int(self, key: str, default: int) -> int:
        """从环境变量获取整数"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _get_bool(self, key: str, default: bool) -> bool:
        """从环境变量获取布尔值"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def as_dict(self) -> dict[str, Any]:
        """返回所有配置的字典（用于调试）"""
        return {
            "security": {
                "max_response_size": self.MAX_RESPONSE_SIZE,
                "max_file_size": self.MAX_FILE_SIZE,
                "max_sql_length": self.MAX_SQL_LENGTH,
                "enable_sql_validation": self.ENABLE_SQL_VALIDATION,
            },
            "performance": {
                "request_timeout": self.REQUEST_TIMEOUT,
                "step_timeout": self.STEP_TIMEOUT,
                "db_pool_size": self.DB_POOL_SIZE,
                "max_workers": self.MAX_WORKERS,
            },
            "logging": {
                "log_level": self.LOG_LEVEL,
                "log_file": self.LOG_FILE,
            },
            "csv": {
                "max_csv_size": self.MAX_CSV_SIZE,
                "max_csv_rows": self.MAX_CSV_ROWS,
            },
            "memory": {
                "max_variable_size": self.MAX_VARIABLE_SIZE,
            },
        }


# 全局配置实例
config = Config()
