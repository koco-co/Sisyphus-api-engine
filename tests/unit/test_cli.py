"""CLI 行为与 EngineError / JSON 输出测试。"""

from __future__ import annotations

from pathlib import Path

import json
from click.testing import CliRunner

from apirun.cli import main


def test_cli_json_engine_error_on_invalid_yaml(tmp_path: Path):
    """非法 YAML 时，json 输出应包含顶层 error 对象，exit code=1。"""
    yaml_path = tmp_path / "invalid.yaml"
    yaml_path.write_text("config:\n  name: [\n  invalid", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["--case", str(yaml_path), "-O", "json"])

    assert result.exit_code == 1
    # 输出必须是合法 JSON，且 status=error，包含 error.code
    data = json.loads(result.output)
    assert data["status"] == "error"
    assert data["error"]["code"] in {"YAML_PARSE_ERROR", "YAML_VALIDATION_ERROR"}

