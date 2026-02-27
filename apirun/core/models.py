"""YAML 配置模型定义 - 符合 YAML 输入规范。

本模块只负责描述 YAML → Python 的数据结构, 不包含执行逻辑。
"""

import warnings

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

# 抑制 Pydantic v2 关于 'validate' 字段名的 UserWarning
# 'validate' 是 YAML 规范中的标准字段名，覆盖 Pydantic v1 遗留的 validate() 方法
# 功能完全正常，仅抑制警告以避免干扰
warnings.filterwarnings("ignore", message=".*shadows an attribute.*", category=UserWarning)


class EnvironmentConfig(BaseModel):
    """config.environment"""

    name: str
    base_url: str
    variables: dict[str, Any] = Field(default_factory=dict)


class PrePostSql(BaseModel):
    """config.pre_sql / post_sql"""

    datasource: str
    statements: list[str]


class Config(BaseModel):
    """config - 场景配置"""

    name: str
    description: str | None = None
    project_id: str = ""
    scenario_id: str = ""
    priority: str = "P2"
    tags: list[str] = Field(default_factory=list)
    base_url: str | None = None
    environment: EnvironmentConfig | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    pre_sql: PrePostSql | None = None
    post_sql: PrePostSql | None = None
    csv_datasource: str | None = None


def _body_field_set(v: Any) -> bool:
    """是否有有效 body 字段：非 None 且（非 dict/list 或非空）。"""
    if v is None:
        return False
    if isinstance(v, (dict, list)) and len(v) == 0:
        return False
    return True


class RequestStepParams(BaseModel):
    """teststeps[].request — json / data / files 三者互斥（MDL-015）。"""

    model_config = {"populate_by_name": True}

    method: str = "GET"
    url: str
    headers: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    json_body: dict[str, Any] | list[Any] | None = Field(default=None, alias="json")
    data: dict[str, Any] | None = None
    files: dict[str, Any] | None = None
    cookies: dict[str, Any] = Field(default_factory=dict)
    timeout: int = 30
    allow_redirects: bool = True
    verify: bool = True

    @model_validator(mode="after")
    def check_body_mutually_exclusive(self) -> "RequestStepParams":
        """json / data / files 三者最多只能填一个。"""
        set_count = sum(_body_field_set(getattr(self, f)) for f in ("json_body", "data", "files"))
        if set_count > 1:
            raise ValueError("request 中 json、data、files 三者互斥，最多只能填写一个")
        return self


class ExtractRule(BaseModel):
    """变量提取规则 - 可用于 request 内联 extract 或独立 extract 步骤。"""

    name: str
    type: str  # json / header / cookie
    expression: str
    scope: str = "global"  # global / environment
    default: Any | None = None
    source_variable: str | None = None


class ValidateRule(BaseModel):
    """内联断言规则 - 用于 request.validate。"""

    target: str  # json / header / cookie / status_code / response_time / env_variable
    comparator: str
    expected: Any
    expression: str | None = None
    message: str | None = None


class AssertionParams(BaseModel):
    """独立断言步骤参数 - teststeps[].assertion。"""

    target: str
    comparator: str
    expected: Any
    source_variable: str | None = None
    expression: str | None = None
    message: str | None = None


class DbExtractRule(BaseModel):
    """数据库结果提取规则 - db.extract。"""

    name: str
    expression: str
    scope: str = "global"
    default: Any | None = None


class DbValidateRule(BaseModel):
    """数据库结果断言规则 - db.validate。"""

    expression: str
    comparator: str
    expected: Any
    message: str | None = None


class DbParams(BaseModel):
    """数据库操作参数 - teststeps[].db。"""

    model_config = ConfigDict(protected_namespaces=())

    datasource: str
    sql: str
    extract: list[DbExtractRule] | None = None
    validate: list[DbValidateRule] | None = None


class CustomParams(BaseModel):
    """自定义关键字参数 - teststeps[].parameters / extract。"""

    parameters: dict[str, Any] = Field(default_factory=dict)
    extract: list[ExtractRule] | None = None


class StepDefinition(BaseModel):
    """单条测试步骤定义。"""

    model_config = ConfigDict(protected_namespaces=())

    name: str
    keyword_type: str  # request / assertion / extract / db / custom
    keyword_name: str
    enabled: bool = True

    # request 步骤相关
    request: RequestStepParams | None = None
    extract: list[ExtractRule] | None = None
    validate: list[ValidateRule] | None = None

    # assertion 步骤
    assertion: AssertionParams | None = None

    # db 步骤
    db: DbParams | None = None

    # custom 步骤
    custom: CustomParams | None = None


class Ddts(BaseModel):
    """ddts - 数据驱动"""

    name: str
    parameters: list[dict[str, Any]]


class CaseModel(BaseModel):
    """YAML 顶层结构 — config.csv_datasource 与 ddts 互斥（MDL-016）。"""

    config: Config
    teststeps: list[StepDefinition]
    ddts: Ddts | None = None

    @model_validator(mode="after")
    def check_csv_datasource_and_ddts_exclusive(self) -> "CaseModel":
        """csv_datasource 与 ddts 不能同时配置。"""
        if self.config.csv_datasource and (self.ddts and self.ddts.parameters):
            raise ValueError("config.csv_datasource 与 ddts 互斥，不能同时配置")
        return self
