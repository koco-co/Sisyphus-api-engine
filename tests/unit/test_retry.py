"""HTTP 请求重试机制测试"""

import time
from unittest import mock

import pytest
import requests

from apirun.config import Config
from apirun.utils.retry import (
    calculate_backoff,
    execute_with_retry,
    should_retry_on_exception,
    should_retry_on_status_code,
)


def test_should_retry_on_5xx_status_codes():
    """测试 5xx 状态码应该重试"""
    # 500-599 都应该重试
    for code in range(500, 600):
        assert should_retry_on_status_code(code) is True


def test_should_retry_on_429():
    """测试 429 Too Many Requests 应该重试"""
    assert should_retry_on_status_code(429) is True


def test_should_not_retry_on_4xx_status_codes():
    """测试 4xx 客户端错误不应该重试"""
    # 400-499 除了 429 都不应该重试
    for code in range(400, 600):
        if code == 429:
            continue
        if 500 <= code < 600:
            continue
        assert should_retry_on_status_code(code) is False


def test_should_retry_on_network_errors():
    """测试网络错误应该重试"""
    # ConnectionError 应该重试
    assert should_retry_on_exception(requests.exceptions.ConnectionError()) is True

    # Timeout 应该重试
    assert should_retry_on_exception(requests.exceptions.Timeout()) is True

    # RequestException 应该重试
    assert should_retry_on_exception(requests.exceptions.RequestException()) is True


def test_should_not_retry_on_other_exceptions():
    """测试其他异常不应该重试"""
    # ValueError 不应该重试
    assert should_retry_on_exception(ValueError()) is False

    # TypeError 不应该重试
    assert should_retry_on_exception(TypeError()) is False


def test_calculate_backoff():
    """测试指数退避计算"""
    # 基础退避 0.5 秒
    assert calculate_backoff(0, 0.5) == 0.5
    assert calculate_backoff(1, 0.5) == 1.0
    assert calculate_backoff(2, 0.5) == 2.0
    assert calculate_backoff(3, 0.5) == 4.0

    # 自定义基础退避
    assert calculate_backoff(0, 1.0) == 1.0
    assert calculate_backoff(1, 1.0) == 2.0
    assert calculate_backoff(2, 1.0) == 4.0


def test_execute_with_retry_success_on_first_try(monkeypatch):
    """测试第一次就成功的情况"""
    call_count = {"value": 0}

    def mock_request(**kwargs):
        call_count["value"] += 1
        # 创建一个模拟的 Response 对象
        resp = mock.Mock()
        resp.status_code = 200
        resp.headers = {"Content-Type": "application/json"}
        resp.content = b'{"result": "ok"}'
        resp.text = '{"result": "ok"}'
        resp.json.return_value = {"result": "ok"}
        resp.cookies = {}
        return resp

    result = execute_with_retry(mock_request, max_retries=3, url="http://example.com")

    assert result.status_code == 200
    assert call_count["value"] == 1


def test_execute_with_retry_retry_on_5xx(monkeypatch):
    """测试 5xx 错误时重试"""
    call_count = {"value": 0}

    def mock_request(**kwargs):
        call_count["value"] += 1
        resp = mock.Mock()

        # 前两次返回 500，第三次成功
        if call_count["value"] < 3:
            resp.status_code = 500
        else:
            resp.status_code = 200

        resp.headers = {}
        resp.content = b'{}'
        resp.text = '{}'
        resp.json.return_value = {}
        resp.cookies = {}
        return resp

    result = execute_with_retry(mock_request, max_retries=3, base_backoff=0.01)

    assert result.status_code == 200
    assert call_count["value"] == 3


def test_execute_with_retry_retry_on_connection_error(monkeypatch):
    """测试网络错误时重试"""
    call_count = {"value": 0}

    def mock_request(**kwargs):
        call_count["value"] += 1

        # 前两次抛出 ConnectionError，第三次成功
        if call_count["value"] < 3:
            raise requests.exceptions.ConnectionError("Connection refused")

        resp = mock.Mock()
        resp.status_code = 200
        resp.headers = {}
        resp.content = b'{}'
        resp.text = '{}'
        resp.json.return_value = {}
        resp.cookies = {}
        return resp

    result = execute_with_retry(mock_request, max_retries=3, base_backoff=0.01)

    assert result.status_code == 200
    assert call_count["value"] == 3


def test_execute_with_retry_exhausted_retries(monkeypatch):
    """测试重试次数用尽后抛出异常"""
    call_count = {"value": 0}

    def mock_request(**kwargs):
        call_count["value"] += 1
        raise requests.exceptions.ConnectionError("Connection refused")

    with pytest.raises(requests.exceptions.ConnectionError):
        execute_with_retry(mock_request, max_retries=2, base_backoff=0.01)

    # 应该尝试了 max_retries + 1 次
    assert call_count["value"] == 3


def test_execute_with_retry_no_retry_on_4xx(monkeypatch):
    """测试 4xx 错误时不重试"""
    call_count = {"value": 0}

    def mock_request(**kwargs):
        call_count["value"] += 1
        resp = mock.Mock()
        resp.status_code = 404
        resp.headers = {}
        resp.content = b'Not Found'
        resp.text = 'Not Found'
        resp.cookies = {}
        return resp

    result = execute_with_retry(mock_request, max_retries=3, retry_on_5xx=True)

    # 4xx 错误不重试，只调用一次
    assert result.status_code == 404
    assert call_count["value"] == 1


def test_execute_with_retry_uses_config(monkeypatch):
    """测试使用配置的默认重试次数"""
    def mock_request(**kwargs):
        resp = mock.Mock()
        resp.status_code = 200
        resp.headers = {}
        resp.content = b'{}'
        resp.text = '{}'
        resp.json.return_value = {}
        resp.cookies = {}
        return resp

    # 设置配置
    Config.reset()
    config = Config()
    config.HTTP_MAX_RETRIES = 5

    result = execute_with_retry(mock_request)

    assert result.status_code == 200


def test_execute_with_retry_backoff_timing(monkeypatch):
    """测试指数退避时间"""
    call_times = []
    start = time.time()

    def mock_request(**kwargs):
        call_times.append(time.time() - start)

        resp = mock.Mock()
        # 前三次失败，第四次成功
        if len(call_times) < 4:
            resp.status_code = 500
        else:
            resp.status_code = 200
        resp.headers = {}
        resp.content = b'{}'
        resp.text = '{}'
        resp.json.return_value = {}
        resp.cookies = {}
        return resp

    execute_with_retry(mock_request, max_retries=3, base_backoff=0.1)

    # 验证时间间隔（允许一定误差）
    assert len(call_times) == 4
    # 第一次重试约 0.1 秒后
    assert call_times[1] - call_times[0] >= 0.08
    # 第二次重试约 0.2 秒后
    assert call_times[2] - call_times[1] >= 0.15
    # 第三次重试约 0.4 秒后
    assert call_times[3] - call_times[2] >= 0.3
