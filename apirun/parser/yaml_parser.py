"""YAML 用例解析器 — 读取 YAML 并校验为 CaseModel，统一抛出 EngineError（PAR-001～PAR-005）"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from apirun.core.models import CaseModel
from apirun.errors import (
    FILE_NOT_FOUND,
    YAML_PARSE_ERROR,
    YAML_VALIDATION_ERROR,
    EngineError,
)


def parse_yaml(yaml_path: str | Path) -> CaseModel:
    """
    读取 YAML 文件并解析为 CaseModel。
    - 文件不存在 → EngineError(FILE_NOT_FOUND)
    - YAML 语法错误 → EngineError(YAML_PARSE_ERROR)
    - Pydantic 校验失败 → EngineError(YAML_VALIDATION_ERROR)
    """
    path = Path(yaml_path)
    if not path.exists():
        raise EngineError(FILE_NOT_FOUND, f"YAML 文件不存在: {yaml_path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise EngineError(FILE_NOT_FOUND, f"无法读取文件: {yaml_path}") from e

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise EngineError(
            YAML_PARSE_ERROR,
            f"YAML 解析失败: {e}",
            detail=str(e),
        ) from e

    if data is None:
        data = {}

    try:
        return CaseModel.model_validate(data)
    except ValidationError as e:
        raise EngineError(
            YAML_VALIDATION_ERROR,
            f"YAML 结构校验失败: {e}",
            detail=e.model_dump_json(indent=2) if hasattr(e, "model_dump_json") else str(e),
        ) from e
