"""HTTP 请求执行器 - 发送请求并返回响应与耗时。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from apirun.core.models import RequestStepParams
from apirun.utils.minio_client import download_to_temp
from apirun.utils.variables import render_template


def _prepare_files(files: Any) -> tuple[Any, list[Path], list[Any]]:
    """预处理 files 参数，支持 MinIO 路径自动下载为临时文件。"""
    if files is None:
        return None, [], []

    temp_paths: list[Path] = []
    file_handles: list[Any] = []

    if isinstance(files, dict):
        prepared: dict[str, Any] = {}
        for field, value in files.items():
            if isinstance(value, str):
                temp_path = download_to_temp(value)
                temp_paths.append(temp_path)
                fh = temp_path.open("rb")
                file_handles.append(fh)
                prepared[field] = (temp_path.name, fh)
            else:
                prepared[field] = value
        return prepared, temp_paths, file_handles

    return files, temp_paths, file_handles


def execute_request_step(
    params: RequestStepParams,
    base_url: str = "",
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    执行单步 HTTP 请求
    :param params: 请求参数
    :param base_url: 环境 base_url，与 params.url 拼接
    :param variables: 变量表，用于替换 {{var}} / {{func()}}
    :return: 含 status_code, headers, body, response_time, error 的字典
    """
    variables = variables or {}
    # 先渲染 URL, 再进行 base_url 拼接
    rendered_url = render_template(params.url, variables)
    if not isinstance(rendered_url, str):
        rendered_url = str(rendered_url)
    url = rendered_url
    if base_url and not url.startswith(("http://", "https://")):
        url = (base_url.rstrip("/") + "/" + url.lstrip("/")) if url else base_url

    # 渲染其余请求参数
    headers = render_template(params.headers, variables)
    query_params = render_template(params.params, variables)
    json_body = (
        render_template(params.json_body, variables) if params.json_body is not None else None
    )
    data = render_template(params.data, variables) if params.data is not None else None
    files_raw = render_template(params.files, variables) if params.files is not None else None
    cookies = render_template(params.cookies, variables)

    method = (params.method or "GET").upper()
    start = time.perf_counter()
    temp_paths: list[Path] = []
    file_handles: list[Any] = []
    try:
        files, temp_paths, file_handles = _prepare_files(files_raw)

        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=query_params,
            json=json_body,
            data=data,
            files=files,
            cookies=cookies,
            timeout=params.timeout,
            allow_redirects=params.allow_redirects,
            verify=params.verify,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": body,
            "body_size": len(resp.content),
            "response_time": elapsed_ms,
            "cookies": dict(resp.cookies),
            "error": None,
        }
    except requests.exceptions.Timeout as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status_code": 0,
            "headers": {},
            "body": None,
            "body_size": 0,
            "response_time": elapsed_ms,
            "cookies": {},
            "error": {"code": "REQUEST_TIMEOUT", "message": str(e), "detail": None},
        }
    except requests.exceptions.SSLError as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status_code": 0,
            "headers": {},
            "body": None,
            "body_size": 0,
            "response_time": elapsed_ms,
            "cookies": {},
            "error": {"code": "REQUEST_SSL_ERROR", "message": str(e), "detail": None},
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status_code": 0,
            "headers": {},
            "body": None,
            "body_size": 0,
            "response_time": elapsed_ms,
            "cookies": {},
            "error": {"code": "REQUEST_CONNECTION_ERROR", "message": str(e), "detail": None},
        }
    finally:
        for fh in file_handles:
            try:
                fh.close()
            except Exception:
                pass
        for path in temp_paths:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

