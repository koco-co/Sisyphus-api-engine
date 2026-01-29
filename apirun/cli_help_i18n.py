"""International Help Messages for Sisyphus API Engine.

This module provides multilingual help messages for CLI.
Following Google Python Style Guide.
"""

# English help messages
EN_HELP_MESSAGES = {
    "description": "Sisyphus API Engine - Enterprise-grade API Testing Tool",
    "epilog": """
Examples:
  # Run a test case
  sisyphus-api-engine --cases test_case.yaml

  # Run with verbose output
  sisyphus-api-engine --cases test_case.yaml -v

  # Run and save results to JSON
  sisyphus-api-engine --cases test_case.yaml -o result.json

  # Validate YAML syntax
  sisyphus-api-engine --validate test_case.yaml

  # Or use the dedicated validate command
  sisyphus-api-validate test_case.yaml

Documentation:
  Full documentation: https://github.com/koco-co/Sisyphus-api-engine
  Report issues: https://github.com/koco-co/Sisyphus-api-engine/issues
    """,
    "args": {
        "--cases": "Path to YAML test case file or directory",
        "-o/--output": "Output file path for JSON results",
        "-v/--verbose": "Enable verbose output (show detailed step information)",
        "--validate": "Validate YAML syntax without execution",
        "--profile": "Active profile name (overrides config)",
        "--ws-server": "Enable WebSocket server for real-time updates",
        "--ws-host": "WebSocket server host (default: localhost)",
        "--ws-port": "WebSocket server port (default: 8765)",
        "--env-prefix": "Environment variable prefix to load (e.g., 'API_')",
        "--override": "Configuration overrides in format 'key=value' (can be used multiple times)",
        "--debug": "Enable debug mode with variable tracking",
        "--format": "Output format: text (default), json, csv, junit, or html",
        "--allure": "Generate Allure report (saves to allure-results directory)",
        "--allure-dir": "Allure results directory (default: allure-results)",
        "-H/--中文帮助": "Show help message in Chinese (显示中文帮助信息)",
    }
}

# Chinese help messages
ZH_HELP_MESSAGES = {
    "description": "Sisyphus API 引擎 - 企业级 API 自动化测试工具",
    "epilog": """
使用示例:
  # 运行测试用例
  sisyphus-api-engine --cases test_case.yaml

  # 启用详细输出
  sisyphus-api-engine --cases test_case.yaml -v

  # 运行并保存结果到 JSON
  sisyphus-api-engine --cases test_case.yaml -o result.json

  # 验证 YAML 语法
  sisyphus-api-engine --validate test_case.yaml

  # 或使用专用验证命令
  sisyphus-api-validate test_case.yaml

文档支持:
  完整文档: https://github.com/koco-co/Sisyphus-api-engine
  问题反馈: https://github.com/koco-co/Sisyphus-api-engine/issues
    """,
    "args": {
        "--cases": "YAML 测试用例文件或目录路径",
        "-o/--output": "JSON 结果输出文件路径",
        "-v/--verbose": "启用详细输出模式（显示步骤详细信息）",
        "--validate": "仅验证 YAML 语法，不执行测试",
        "--profile": "激活的环境配置名称（覆盖配置文件）",
        "--ws-server": "启用 WebSocket 服务器进行实时推送",
        "--ws-host": "WebSocket 服务器主机地址（默认: localhost）",
        "--ws-port": "WebSocket 服务器端口（默认: 8765）",
        "--env-prefix": "要加载的环境变量前缀（例如: 'API_'）",
        "--override": "配置覆盖，格式为 'key=value'（可多次使用）",
        "--debug": "启用调试模式，包含变量追踪功能",
        "--format": "输出格式: text（默认）, json, csv, junit, 或 html",
        "--allure": "生成 Allure 报告（保存到 allure-results 目录）",
        "--allure-dir": "Allure 结果目录（默认: allure-results）",
        "-H/--中文帮助": "显示中文帮助信息 (Show help in Chinese)",
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
