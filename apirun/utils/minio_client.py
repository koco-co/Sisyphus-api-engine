"""MinIO 文件下载工具 - 将 MinIO 路径下载为本地临时文件。

设计约定（配合 YAML 输入规范 4.1.1 中的 files 字段）：

- YAML 中 `files` 字段的 Value 为「MinIO 文件路径」字符串。
- 为了避免在核心引擎中强绑定特定 MinIO SDK，这里统一走 HTTP 下载方式：
  - 当值形如 `minio://bucket/path/to/file` 时：
    - 使用环境变量 `MINIO_ENDPOINT` 或 `SISYPHUS_MINIO_ENDPOINT` 作为 HTTP 前缀，
      拼接为 `{endpoint}/{bucket}/{object}` 进行下载。
  - 当值为普通字符串但不是 HTTP URL 时：
    - 仍使用上述 endpoint，将值视为 `{bucket}/{object}` 或直接为相对路径，由调用方约定。
  - 当值本身就是 `http://` 或 `https://` 开头的 URL 时：
    - 直接按该 URL 下载，不再拼接 endpoint。

下载失败或配置缺失时统一抛出 EngineError(ENGINE_INTERNAL_ERROR, ...)，
由上层执行器转换为请求级错误。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Final

import requests

from apirun.errors import ENGINE_INTERNAL_ERROR, EngineError


_ENV_ENDPOINT_KEYS: Final[list[str]] = ["MINIO_ENDPOINT", "SISYPHUS_MINIO_ENDPOINT"]


def _get_minio_endpoint() -> str:
    """从环境变量中获取 MinIO HTTP 访问地址。"""
    for key in _ENV_ENDPOINT_KEYS:
        value = os.getenv(key)
        if value:
            return value
    raise EngineError(
        ENGINE_INTERNAL_ERROR,
        "MinIO endpoint 未配置，请设置环境变量 MINIO_ENDPOINT 或 SISYPHUS_MINIO_ENDPOINT",
    )


def _build_download_url(minio_path: str) -> str:
    """根据约定将 MinIO 路径转换为可直接访问的 HTTP URL。"""
    minio_path = minio_path.strip()
    if not minio_path:
        raise EngineError(ENGINE_INTERNAL_ERROR, "MinIO 路径不能为空")

    # 已经是 HTTP(S) URL 时直接返回，适配预签名 URL 等场景。
    if minio_path.startswith(("http://", "https://")):
        return minio_path

    endpoint = _get_minio_endpoint().rstrip("/")

    # 显式 minio://bucket/object 语法
    if minio_path.startswith("minio://"):
        without_scheme = minio_path[len("minio://") :]
        parts = without_scheme.split("/", 1)
        if not parts[0]:
            raise EngineError(ENGINE_INTERNAL_ERROR, f"无效的 MinIO 路径: {minio_path}")
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        key = key.lstrip("/")
        return f"{endpoint}/{bucket}/{key}" if key else f"{endpoint}/{bucket}"

    # 兼容简单形式：直接使用 endpoint + 相对路径
    return f"{endpoint}/{minio_path.lstrip('/')}"


def download_to_temp(minio_path: str) -> Path:
    """将 MinIO 路径下载为本地临时文件并返回路径。

    调用者负责在使用完文件后删除临时文件。
    """
    url = _build_download_url(minio_path)
    try:
        resp = requests.get(url, stream=True, timeout=30)
    except requests.RequestException as e:  # noqa: TRY003
        raise EngineError(
            ENGINE_INTERNAL_ERROR,
            f"MinIO 文件下载失败（网络错误）: {url}",
            detail=str(e),
        ) from e

    if not resp.ok:
        raise EngineError(
            ENGINE_INTERNAL_ERROR,
            f"MinIO 文件下载失败: {url} (status={resp.status_code})",
        )

    # 尝试从路径中推断文件后缀，便于调试
    suffix = ""
    last_segment = url.rsplit("/", 1)[-1]
    if "." in last_segment:
        suffix = "." + last_segment.split(".")[-1]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                tmp.write(chunk)
        tmp.flush()
    finally:
        tmp.close()

    return Path(tmp.name)

