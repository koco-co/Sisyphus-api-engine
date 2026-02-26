"""统一异常与错误码 — 引擎级与步骤级错误，供各模块复用。"""

# ---------------------------------------------------------------------------
# 引擎级错误码（ERR-002）
# ---------------------------------------------------------------------------
FILE_NOT_FOUND = "FILE_NOT_FOUND"
YAML_PARSE_ERROR = "YAML_PARSE_ERROR"
YAML_VALIDATION_ERROR = "YAML_VALIDATION_ERROR"
CSV_FILE_NOT_FOUND = "CSV_FILE_NOT_FOUND"
CSV_PARSE_ERROR = "CSV_PARSE_ERROR"
ENGINE_INTERNAL_ERROR = "ENGINE_INTERNAL_ERROR"
TIMEOUT_ERROR = "TIMEOUT_ERROR"

# ---------------------------------------------------------------------------
# 步骤级错误码（ERR-003）
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = "REQUEST_TIMEOUT"
REQUEST_CONNECTION_ERROR = "REQUEST_CONNECTION_ERROR"
REQUEST_SSL_ERROR = "REQUEST_SSL_ERROR"
ASSERTION_FAILED = "ASSERTION_FAILED"
EXTRACT_FAILED = "EXTRACT_FAILED"
DB_CONNECTION_ERROR = "DB_CONNECTION_ERROR"
DB_QUERY_ERROR = "DB_QUERY_ERROR"
DB_DATASOURCE_NOT_FOUND = "DB_DATASOURCE_NOT_FOUND"
KEYWORD_NOT_FOUND = "KEYWORD_NOT_FOUND"
KEYWORD_EXECUTION_ERROR = "KEYWORD_EXECUTION_ERROR"
VARIABLE_NOT_FOUND = "VARIABLE_NOT_FOUND"
VARIABLE_RENDER_ERROR = "VARIABLE_RENDER_ERROR"


class EngineError(Exception):
    """
    统一异常基类（ERR-001）。
    属性: code（错误码）、message（描述）、detail（可选详情/堆栈）。
    """

    def __init__(
        self,
        code: str,
        message: str,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict[str, str | None]:
        """转为 JSON 输出规范中的 error 对象。"""
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }
