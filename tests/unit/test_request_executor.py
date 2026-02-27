"""HTTP 请求执行器与变量替换集成测试"""

from __future__ import annotations

from typing import Any

from apirun.core.models import RequestStepParams
from apirun.executor.request import execute_request_step


class _DummyResponse:
    def __init__(self, url: str) -> None:
        self.status_code = 200
        self.headers: dict[str, str] = {"X-Url": url}
        self._text = "ok"
        self._content = b"ok"
        self.cookies: dict[str, Any] = {}

    def json(self) -> Any:  # noqa: D401
        """模拟 JSON 响应解析失败以回退到 text。"""
        raise ValueError("not json")

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._content


def test_execute_request_step_renders_variables_in_url(monkeypatch):
    called = {}

    def fake_request(method: str, url: str, **kwargs: Any):
        called["method"] = method
        called["url"] = url
        called["kwargs"] = kwargs
        return _DummyResponse(url)

    monkeypatch.setattr("apirun.executor.request.requests.request", fake_request)

    params = RequestStepParams(method="GET", url="/users/{{user_id}}")
    result = execute_request_step(
        params, base_url="https://api.example.com", variables={"user_id": 123}
    )

    assert called["url"] == "https://api.example.com/users/123"
    assert result["status_code"] == 200
    assert result["body"] == "ok"


def test_execute_request_step_minio_files_download(monkeypatch, tmp_path):
    """当 files 中包含 MinIO 路径时，应自动下载到临时文件并作为文件上传。"""
    downloaded_paths: list[str] = []

    # 伪造 MinIO 下载函数，避免真实网络请求。
    def fake_download_to_temp(minio_path: str):
        downloaded_paths.append(minio_path)
        p = tmp_path / "minio_file.txt"
        p.write_text("file-from-minio", encoding="utf-8")
        return p

    monkeypatch.setattr(
        "apirun.executor.request.download_to_temp",
        fake_download_to_temp,
    )

    called: dict[str, Any] = {}

    def fake_request(method: str, url: str, **kwargs: Any):
        called["method"] = method
        called["url"] = url
        called["kwargs"] = kwargs
        return _DummyResponse(url)

    monkeypatch.setattr("apirun.executor.request.requests.request", fake_request)

    params = RequestStepParams(
        method="POST",
        url="/upload",
        files={"file1": "minio://bucket/path/to/file1.txt"},
    )

    result = execute_request_step(params, base_url="https://api.example.com", variables={})

    assert result["status_code"] == 200
    assert downloaded_paths == ["minio://bucket/path/to/file1.txt"]

    files_arg = called["kwargs"]["files"]
    assert isinstance(files_arg, dict)
    assert "file1" in files_arg
    file_tuple = files_arg["file1"]
    # (filename, fileobj)
    assert isinstance(file_tuple, tuple)
    assert file_tuple[0] == "minio_file.txt"


def test_execute_request_step_renders_variables_in_url(monkeypatch):
    called = {}

    def fake_request(method: str, url: str, **kwargs: Any):
        called["method"] = method
        called["url"] = url
        called["kwargs"] = kwargs
        return _DummyResponse(url)

    monkeypatch.setattr("apirun.executor.request.requests.request", fake_request)

    params = RequestStepParams(method="GET", url="/users/{{user_id}}")
    result = execute_request_step(
        params, base_url="https://api.example.com", variables={"user_id": 123}
    )

    assert called["url"] == "https://api.example.com/users/123"
    assert result["status_code"] == 200
    assert result["body"] == "ok"
