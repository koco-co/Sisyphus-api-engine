"""International Help Messages for Sisyphus API Engine.

This module provides multilingual help messages for CLI.
Following Google Python Style Guide.
"""

# English help messages
EN_HELP_MESSAGES = {
    "description": "Sisyphus API Engine - Enterprise-grade API Testing Tool",
    "epilog": """
Examples:
  # Run a single test case
  sisyphus-api-engine --cases test_case.yaml

  # Run multiple test cases
  sisyphus-api-engine --cases test1.yaml test2.yaml test3.yaml

  # Run all test cases in a directory
  sisyphus-api-engine --cases tests/

  # Mix files and directories
  sisyphus-api-engine --cases test1.yaml tests/ integration/

  # Run with verbose output
  sisyphus-api-engine --cases test_case.yaml -v

  # Run and save results to JSON
  sisyphus-api-engine --cases test_case.yaml -o result.json

  # Generate HTML report (English)
  sisyphus-api-engine --cases test_case.yaml --format html --report-lang en -o report.html

  # Generate HTML report (Chinese)
  sisyphus-api-engine --cases test_case.yaml --format html --report-lang zh -o report.html

  # Validate YAML syntax
  sisyphus-api-engine --validate test_case.yaml

  # Validate multiple files
  sisyphus-api-engine --validate test1.yaml test2.yaml

  # Validate all files in directory
  sisyphus-api-engine --validate tests/

  # Or use the dedicated validate command
  sisyphus-api-validate test_case.yaml

Documentation:
  Full documentation: https://github.com/koco-co/Sisyphus-api-engine
  Report issues: https://github.com/koco-co/Sisyphus-api-engine/issues
    """,
    "args": {
        "--cases": "Path(s) to YAML test case file(s) or director(y/ies)",
        "-o/--output": "Output file path (supports JSON/CSV/HTML/JUnit XML, format determined by extension or --format)",
        "-v/--verbose": "Enable verbose output (show detailed step information)",
        "--validate": "Validate YAML syntax without execution",
        "--profile": "Active profile name (overrides config)",
        "--ws-server": "Enable WebSocket server for real-time updates",
        "--ws-host": "WebSocket server host",
        "--ws-port": "WebSocket server port",
        "--env-prefix": "Environment variable prefix to load (e.g., 'API_')",
        "--override": "Configuration overrides in format 'key=value' (can be used multiple times)",
        "--debug": "Enable debug mode with variable tracking",
        "--format": "Output format: text, json, csv, junit, or html",
        "--report-lang": "Report language: en (English) or zh (中文)",
        "--allure": "Generate Allure report (saves to allure-results directory)",
        "--allure-dir": "Allure results directory",
        "--allure-clean": "Clean Allure results directory before generating",
        "--allure-no-clean": "Keep previous Allure results (accumulate data)",
    }
}

# Chinese help messages
ZH_HELP_MESSAGES = {
    "description": "Sisyphus API Engine - 企业级 API 自动化测试工具",
    "epilog": """
使用示例:
  # 运行单个测试用例
  sisyphus-api-engine --cases test_case.yaml

  # 运行多个测试用例
  sisyphus-api-engine --cases test1.yaml test2.yaml test3.yaml

  # 运行目录中的所有测试用例
  sisyphus-api-engine --cases tests/

  # 混合文件和目录
  sisyphus-api-engine --cases test1.yaml tests/ integration/

  # 启用详细输出
  sisyphus-api-engine --cases test_case.yaml -v

  # 运行并保存结果到 JSON
  sisyphus-api-engine --cases test_case.yaml -o result.json

  # 生成 HTML 报告（英文）
  sisyphus-api-engine --cases test_case.yaml --format html --report-lang en -o report.html

  # 生成 HTML 报告（中文）
  sisyphus-api-engine --cases test_case.yaml --format html --report-lang zh -o report.html

  # 验证 YAML 语法
  sisyphus-api-engine --validate test_case.yaml

  # 验证多个文件
  sisyphus-api-engine --validate test1.yaml test2.yaml

  # 验证目录中的所有文件
  sisyphus-api-engine --validate tests/

  # 或使用专用验证命令
  sisyphus-api-validate test_case.yaml

文档支持:
  完整文档: https://github.com/koco-co/Sisyphus-api-engine
  问题反馈: https://github.com/koco-co/Sisyphus-api-engine/issues
    """,
    "args": {
        "--cases": "YAML 测试用例文件或目录路径（支持多个）",
        "-o/--output": "输出文件路径（支持 JSON/CSV/HTML/JUnit XML，格式由文件扩展名或 --format 决定）",
        "-v/--verbose": "启用详细输出模式（显示步骤详细信息）",
        "--validate": "仅验证 YAML 语法，不执行测试",
        "--profile": "激活的环境配置名称（覆盖配置文件）",
        "--ws-server": "启用 WebSocket 服务器进行实时推送",
        "--ws-host": "WebSocket 服务器主机地址",
        "--ws-port": "WebSocket 服务器端口",
        "--env-prefix": "要加载的环境变量前缀（例如: 'API_'）",
        "--override": "配置覆盖，格式为 'key=value'（可多次使用）",
        "--debug": "启用调试模式，包含变量追踪功能",
        "--format": "输出格式: text、json、csv、junit 或 html",
        "--report-lang": "报告语言: en（英文）或 zh（中文）",
        "--allure": "生成 Allure 报告（保存到 allure-results 目录）",
        "--allure-dir": "Allure 结果目录",
        "--allure-clean": "生成前清理 Allure 结果目录",
        "--allure-no-clean": "保留之前的 Allure 结果（累积数据）",
    }
}

# Validation command help
EN_VALIDATE_HELP = {
    "description": "Sisyphus API Engine - YAML Validator",
    "epilog": """
Examples:
  # Validate a single file
  sisyphus-api-validate test_case.yaml

  # Validate all files in a directory
  sisyphus-api-validate examples/

  # Validate multiple files
  sisyphus-api-validate test1.yaml test2.yaml test3.yaml
    """,
    "args": {
        "paths": "Path(s) to YAML file(s) or directory",
    }
}

ZH_VALIDATE_HELP = {
    "description": "Sisyphus API 引擎 - YAML 语法验证器",
    "epilog": """
使用示例:
  # 验证单个文件
  sisyphus-api-validate test_case.yaml

  # 验证目录中的所有文件
  sisyphus-api-validate examples/

  # 验证多个文件
  sisyphus-api-validate test1.yaml test2.yaml test3.yaml
    """,
    "args": {
        "paths": "YAML 文件或目录路径",
    }
}


def get_help_messages(lang: str = "en") -> dict:
    """Get help messages for specified language.

    Args:
        lang: Language code ('en' for English, 'zh' for Chinese)

    Returns:
        Dictionary containing help messages
    """
    if lang == "zh":
        return ZH_HELP_MESSAGES
    return EN_HELP_MESSAGES


def get_validate_help_messages(lang: str = "en") -> dict:
    """Get validation command help messages for specified language.

    Args:
        lang: Language code ('en' for English, 'zh' for Chinese)

    Returns:
        Dictionary containing help messages
    """
    if lang == "zh":
        return ZH_VALIDATE_HELP
    return EN_VALIDATE_HELP


# Mapping from argument names to message keys
ARGUMENT_MAPPING = {
    "cases": "--cases",
    "output": "-o/--output",
    "verbose": "-v/--verbose",
    "validate": "--validate",
    "profile": "--profile",
    "ws_server": "--ws-server",
    "ws_host": "--ws-host",
    "ws_port": "--ws-port",
    "env_prefix": "--env-prefix",
    "override": "--override",
    "debug": "--debug",
    "format": "--format",
    "report_lang": "--report-lang",
    "allure": "--allure",
    "allure_dir": "--allure-dir",
    "allure_clean": "--allure-clean",
    "allure_no_clean": "--allure-no-clean",
}
