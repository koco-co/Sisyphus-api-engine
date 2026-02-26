"""CSV 解析器单元测试（PAR-006～PAR-008 / TST-032）"""

import tempfile
from pathlib import Path

import pytest

from apirun.errors import CSV_FILE_NOT_FOUND, CSV_PARSE_ERROR, EngineError
from apirun.parser.csv_parser import parse_csv


def test_parse_csv_returns_list_of_dict():
    """parse_csv 返回 list[dict]，第一行为表头（PAR-006）"""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write("a,b,c\n1,2,3\n4,5,6\n")
        path = Path(f.name)
    try:
        rows = parse_csv(path)
        assert len(rows) == 2
        assert rows[0] == {"a": "1", "b": "2", "c": "3"}
        assert rows[1] == {"a": "4", "b": "5", "c": "6"}
    finally:
        path.unlink(missing_ok=True)


def test_parse_csv_file_not_found():
    """文件不存在时抛出 CSV_FILE_NOT_FOUND（PAR-007）"""
    with pytest.raises(EngineError) as exc_info:
        parse_csv("/nonexistent/data.csv")
    assert exc_info.value.code == CSV_FILE_NOT_FOUND


def test_parse_csv_empty_file():
    """空文件返回空列表"""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write("")
        path = Path(f.name)
    try:
        rows = parse_csv(path)
        assert rows == []
    finally:
        path.unlink(missing_ok=True)


def test_parse_csv_header_only():
    """仅表头时返回空列表"""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write("x,y\n")
        path = Path(f.name)
    try:
        rows = parse_csv(path)
        assert rows == []
    finally:
        path.unlink(missing_ok=True)
