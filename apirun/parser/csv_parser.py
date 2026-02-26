"""CSV 数据源解析器 — 第一行为表头，解析为 list[dict]（PAR-006～PAR-008）"""

import csv
from pathlib import Path

from apirun.errors import CSV_FILE_NOT_FOUND, CSV_PARSE_ERROR, EngineError


def parse_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """
    读取 CSV 文件并解析为 list[dict]。
    - 第一行为表头，后续行为数据，每行一个 dict（PAR-006）
    - 文件不存在 → EngineError(CSV_FILE_NOT_FOUND)（PAR-007）
    - 格式错误 → EngineError(CSV_PARSE_ERROR)（PAR-008）
    """
    path = Path(csv_path)
    if not path.exists():
        raise EngineError(CSV_FILE_NOT_FOUND, f"CSV 文件不存在: {csv_path}")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise EngineError(CSV_FILE_NOT_FOUND, f"无法读取文件: {csv_path}") from e

    try:
        reader = csv.DictReader(
            text.splitlines(),
            delimiter=",",
            quotechar='"',
            skipinitialspace=True,
        )
        rows = list(reader)
        if reader.fieldnames:
            # 统一为 str 值（CSV 无类型）
            return [dict((k, str(v)) for k, v in r.items()) for r in rows]
        return []
    except (csv.Error, ValueError, KeyError) as e:
        raise EngineError(
            CSV_PARSE_ERROR,
            f"CSV 解析失败: {e}",
            detail=str(e),
        ) from e
