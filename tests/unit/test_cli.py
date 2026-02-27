"""CLI 行为与 EngineError / JSON 输出测试。"""

from __future__ import annotations

from pathlib import Path

import json
from click.testing import CliRunner  # type: ignore[reportMissingImports]

import apirun.cli as cli
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


def test_cli_injects_active_profile_environment_when_yaml_missing_env(monkeypatch):
    """YAML 未配置 environment 时，CLI 应注入 .sisyphus active_profile。"""

    class _DummyResult:
        def model_dump(self):
            return {"status": "passed", "steps": [], "summary": {}}

    captured: dict[str, object] = {}

    def _fake_run_case(case_model, verbose=False):  # noqa: ANN001, FBT002
        assert case_model.config.environment is not None
        captured["name"] = case_model.config.environment.name
        captured["base_url"] = case_model.config.environment.base_url
        captured["variables"] = case_model.config.environment.variables
        return _DummyResult()

    monkeypatch.setattr(cli, "run_case", _fake_run_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".sisyphus").mkdir(parents=True, exist_ok=True)
        Path(".sisyphus/config.yaml").write_text(
            (
                "profiles:\n"
                "  dev:\n"
                "    base_url: \"https://api.injected.local\"\n"
                "    variables:\n"
                "      token: \"abc\"\n"
                "active_profile: \"dev\"\n"
                "variables:\n"
                "  common_timeout: 30\n"
            ),
            encoding="utf-8",
        )
        Path("case.yaml").write_text(
            (
                "config:\n"
                "  name: \"case\"\n"
                "  project_id: \"p1\"\n"
                "  scenario_id: \"s1\"\n"
                "teststeps:\n"
                "  - name: \"req\"\n"
                "    keyword_type: \"request\"\n"
                "    keyword_name: \"http_request\"\n"
                "    request:\n"
                "      method: \"GET\"\n"
                "      url: \"/api/ping\"\n"
            ),
            encoding="utf-8",
        )
        result = runner.invoke(main, ["--case", "case.yaml", "-O", "json"])

    assert result.exit_code == 0
    assert captured["name"] == "dev"
    assert captured["base_url"] == "https://api.injected.local"
    assert captured["variables"] == {"common_timeout": 30, "token": "abc"}


def test_cli_keeps_yaml_environment_priority_over_sisyphus(monkeypatch):
    """YAML 显式 environment 优先级高于 .sisyphus active_profile。"""

    class _DummyResult:
        def model_dump(self):
            return {"status": "passed", "steps": [], "summary": {}}

    captured: dict[str, str] = {}

    def _fake_run_case(case_model, verbose=False):  # noqa: ANN001, FBT002
        assert case_model.config.environment is not None
        captured["name"] = case_model.config.environment.name
        captured["base_url"] = case_model.config.environment.base_url
        captured["config_base_url"] = case_model.config.base_url or ""
        return _DummyResult()

    monkeypatch.setattr(cli, "run_case", _fake_run_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".sisyphus").mkdir(parents=True, exist_ok=True)
        Path(".sisyphus/config.yaml").write_text(
            (
                "profiles:\n"
                "  dev:\n"
                "    base_url: \"https://api.injected.local\"\n"
                "active_profile: \"dev\"\n"
            ),
            encoding="utf-8",
        )
        Path("case.yaml").write_text(
            (
                "config:\n"
                "  name: \"case\"\n"
                "  project_id: \"p1\"\n"
                "  scenario_id: \"s1\"\n"
                "  environment:\n"
                "    name: \"yaml\"\n"
                "    base_url: \"https://api.from.yaml\"\n"
                "    variables: {}\n"
                "teststeps:\n"
                "  - name: \"req\"\n"
                "    keyword_type: \"request\"\n"
                "    keyword_name: \"http_request\"\n"
                "    request:\n"
                "      method: \"GET\"\n"
                "      url: \"/api/ping\"\n"
            ),
            encoding="utf-8",
        )
        result = runner.invoke(main, ["--case", "case.yaml", "-O", "json"])

    assert result.exit_code == 0
    assert captured["name"] == "yaml"
    assert captured["base_url"] == "https://api.from.yaml"
    assert captured["config_base_url"] == ""


def test_cli_keeps_yaml_base_url_priority_over_sisyphus(monkeypatch):
    """YAML config.base_url 优先级高于 .sisyphus active_profile.base_url。"""

    class _DummyResult:
        def model_dump(self):
            return {"status": "passed", "steps": [], "summary": {}}

    captured: dict[str, str] = {}

    def _fake_run_case(case_model, verbose=False):  # noqa: ANN001, FBT002
        captured["base_url"] = case_model.config.base_url or ""
        return _DummyResult()

    monkeypatch.setattr(cli, "run_case", _fake_run_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".sisyphus").mkdir(parents=True, exist_ok=True)
        Path(".sisyphus/config.yaml").write_text(
            (
                "profiles:\n"
                "  dev:\n"
                "    base_url: \"https://api.injected.local\"\n"
                "active_profile: \"dev\"\n"
            ),
            encoding="utf-8",
        )
        Path("case.yaml").write_text(
            (
                "config:\n"
                "  name: \"case\"\n"
                "  project_id: \"p1\"\n"
                "  scenario_id: \"s1\"\n"
                "  base_url: \"https://api.from.case\"\n"
                "teststeps:\n"
                "  - name: \"req\"\n"
                "    keyword_type: \"request\"\n"
                "    keyword_name: \"http_request\"\n"
                "    request:\n"
                "      method: \"GET\"\n"
                "      url: \"/api/ping\"\n"
            ),
            encoding="utf-8",
        )
        result = runner.invoke(main, ["--case", "case.yaml", "-O", "json"])

    assert result.exit_code == 0
    assert captured["base_url"] == "https://api.from.case"


def test_cli_uses_yaml_base_url_when_without_environment(monkeypatch):
    """仅在用例 YAML 配置 base_url 时应可直接生效。"""

    class _DummyResult:
        def model_dump(self):
            return {"status": "passed", "steps": [], "summary": {}}

    captured: dict[str, str] = {}

    def _fake_run_case(case_model, verbose=False):  # noqa: ANN001, FBT002
        captured["base_url"] = case_model.config.base_url or ""
        captured["env_name"] = case_model.config.environment.name if case_model.config.environment else ""
        return _DummyResult()

    monkeypatch.setattr(cli, "run_case", _fake_run_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("case.yaml").write_text(
            (
                "config:\n"
                "  name: \"case\"\n"
                "  project_id: \"p1\"\n"
                "  scenario_id: \"s1\"\n"
                "  base_url: \"https://api.from.case\"\n"
                "teststeps:\n"
                "  - name: \"req\"\n"
                "    keyword_type: \"request\"\n"
                "    keyword_name: \"http_request\"\n"
                "    request:\n"
                "      method: \"GET\"\n"
                "      url: \"/api/ping\"\n"
            ),
            encoding="utf-8",
        )
        result = runner.invoke(main, ["--case", "case.yaml", "-O", "json"])

    assert result.exit_code == 0
    assert captured["base_url"] == "https://api.from.case"
    assert captured["env_name"] == ""


def test_cli_merges_global_and_yaml_environment_variables(monkeypatch):
    """全局 variables 与 YAML environment.variables 合并，且 YAML 覆盖同名键。"""

    class _DummyResult:
        def model_dump(self):
            return {"status": "passed", "steps": [], "summary": {}}

    captured: dict[str, object] = {}

    def _fake_run_case(case_model, verbose=False):  # noqa: ANN001, FBT002
        assert case_model.config.environment is not None
        captured["variables"] = case_model.config.environment.variables
        return _DummyResult()

    monkeypatch.setattr(cli, "run_case", _fake_run_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".sisyphus").mkdir(parents=True, exist_ok=True)
        Path(".sisyphus/config.yaml").write_text(
            (
                "profiles:\n"
                "  dev:\n"
                "    base_url: \"https://api.injected.local\"\n"
                "    variables:\n"
                "      token: \"from-profile\"\n"
                "active_profile: \"dev\"\n"
                "variables:\n"
                "  common_header:\n"
                "    User-Agent: \"ua-global\"\n"
            ),
            encoding="utf-8",
        )
        Path("case.yaml").write_text(
            (
                "config:\n"
                "  name: \"case\"\n"
                "  project_id: \"p1\"\n"
                "  scenario_id: \"s1\"\n"
                "  environment:\n"
                "    name: \"yaml\"\n"
                "    base_url: \"https://api.from.yaml\"\n"
                "    variables:\n"
                "      token: \"from-yaml\"\n"
                "      locale: \"zh-CN\"\n"
                "teststeps:\n"
                "  - name: \"req\"\n"
                "    keyword_type: \"request\"\n"
                "    keyword_name: \"http_request\"\n"
                "    request:\n"
                "      method: \"GET\"\n"
                "      url: \"/api/ping\"\n"
            ),
            encoding="utf-8",
        )
        result = runner.invoke(main, ["--case", "case.yaml", "-O", "json"])

    assert result.exit_code == 0
    assert captured["variables"] == {
        "common_header": {"User-Agent": "ua-global"},
        "token": "from-yaml",
        "locale": "zh-CN",
    }


def test_cli_ignores_invalid_sisyphus_config_without_crash(monkeypatch):
    """`.sisyphus/config.yaml` 非法时，CLI 降级执行且不崩溃。"""

    class _DummyResult:
        def model_dump(self):
            return {"status": "passed", "steps": [], "summary": {}}

    captured: dict[str, object] = {}

    def _fake_run_case(case_model, verbose=False):  # noqa: ANN001, FBT002
        captured["environment"] = case_model.config.environment
        return _DummyResult()

    monkeypatch.setattr(cli, "run_case", _fake_run_case)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".sisyphus").mkdir(parents=True, exist_ok=True)
        Path(".sisyphus/config.yaml").write_text("not: [valid", encoding="utf-8")
        Path("case.yaml").write_text(
            (
                "config:\n"
                "  name: \"case\"\n"
                "  project_id: \"p1\"\n"
                "  scenario_id: \"s1\"\n"
                "teststeps:\n"
                "  - name: \"req\"\n"
                "    keyword_type: \"request\"\n"
                "    keyword_name: \"http_request\"\n"
                "    request:\n"
                "      method: \"GET\"\n"
                "      url: \"/api/ping\"\n"
            ),
            encoding="utf-8",
        )
        result = runner.invoke(main, ["--case", "case.yaml", "-O", "json"])

    assert result.exit_code == 0
    assert captured["environment"] is None

