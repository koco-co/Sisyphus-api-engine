"""Sisyphus API Engine 数据模型。

本模块定义测试执行过程中使用的核心数据结构。
遵循 Google Python Style Guide。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HttpMethod(Enum):
    """HTTP 方法枚举。"""

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'


class ErrorCategory(Enum):
    """错误分类枚举。"""

    ASSERTION = 'assertion'
    NETWORK = 'network'
    TIMEOUT = 'timeout'
    PARSING = 'parsing'
    BUSINESS = 'business'
    SYSTEM = 'system'


@dataclass
class ProfileConfig:
    """环境配置文件。

    Attributes:
        base_url: 环境的基础 URL
        variables: 环境特定变量
        timeout: 请求默认超时时间
        verify_ssl: 是否验证 SSL 证书
        overrides: 来自环境变量或 CLI 的配置覆盖
        priority: 变量优先级（值越高优先级越高）
    """

    base_url: str
    variables: dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    verify_ssl: bool = True
    overrides: dict[str, Any] = field(default_factory=dict)
    priority: int = 0


@dataclass
class GlobalConfig:
    """全局测试配置。

    Attributes:
        name: 测试套件名称
        description: 测试套件描述
        profiles: 环境配置（dev、test、prod 等）
        active_profile: 当前激活的配置名称
        variables: 所有测试可访问的全局变量
        timeout: 所有步骤的全局超时时间
        retry_times: 失败步骤的默认重试次数
        concurrent: 是否启用并发执行
        concurrent_threads: 并发执行的线程数
        data_source: 数据驱动测试的数据源配置
            - type: 数据源类型（csv/json/database）
            - file_path: 文件路径（用于 CSV/JSON）
            - delimiter: CSV 分隔符（默认：","）
            - encoding: 文件编码（默认："utf-8"）
            - has_header: CSV 是否有表头（默认：True）
            - data_key: 提取数据的 JSON 键（用于 JSON）
            - db_type: 数据库类型（用于数据库）
            - connection_config: 数据库连接配置（用于数据库）
            - sql: SQL 查询（用于数据库）
        data_iterations: 是否迭代数据源（默认：False）
        variable_prefix: 数据变量的前缀（默认：""）
        websocket: WebSocket 实时推送配置
            - enabled: 是否启用 WebSocket 服务器
            - host: WebSocket 服务器主机（默认："localhost"）
            - port: WebSocket 服务器端口（默认：8765）
            - send_progress: 是否发送进度事件（默认：true）
            - send_logs: 是否发送日志事件（默认：true）
            - send_variables: 是否发送变量更新事件（默认：false）
        output: 测试结果输出配置
            - path: 输出文件路径（支持 ${timestamp} 等变量）
            - format: 输出格式（json/html/xml）
            - include_request: 在输出中包含请求详情
            - include_response: 在输出中包含响应详情
            - include_performance: 在输出中包含性能指标
            - include_variables: 在输出中包含变量快照
            - sensitive_data_mask: 掩码敏感数据（密码、令牌）
        debug: 调试模式配置
            - enabled: 启用调试模式
            - variable_tracking: 跟踪变量变化
            - show_request: 显示请求详情
            - show_response: 显示响应详情
            - log_level: 日志级别（DEBUG/INFO/WARN/ERROR）
        env_vars: 环境变量配置
            - prefix: 环境变量前缀（例如："API_"）
            - load_from_os: 是否从操作系统环境加载变量
            - overrides: 环境变量覆盖
        verbose: 启用详细输出（控制台）
    """

    name: str
    description: str = ''
    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    active_profile: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_times: int = 0
    concurrent: bool = False
    concurrent_threads: int = 3
    data_source: dict[str, Any] | None = None
    data_iterations: bool = False
    variable_prefix: str = ''
    websocket: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    debug: dict[str, Any] | None = None
    env_vars: dict[str, Any] | None = None
    verbose: bool = False


@dataclass
class ValidationRule:
    """验证规则。

    Attributes:
        type: 比较器类型（eq、ne、gt、lt、contains、regex 等）
              或逻辑运算符（and、or、not）
        path: 提取值的 JSONPath 表达式
        expect: 期望值
        description: 验证描述
        logical_operator: 复杂验证的逻辑运算符（and/or/not）
        sub_validations: 逻辑运算符的子验证规则列表
        error_message: 验证失败时显示的自定义错误消息
    """

    type: str
    path: str = ''
    expect: Any = None
    description: str = ''
    logical_operator: str | None = None
    sub_validations: list['ValidationRule'] = field(default_factory=list)
    error_message: str = ''


@dataclass
class Extractor:
    """变量提取配置。

    Attributes:
        name: 存储提取值的变量名
        type: 提取类型（jsonpath、regex、header、cookie）
        path: 提取路径或模式
        index: 多个匹配的索引（默认：0）
        extract_all: 提取所有匹配值为数组（默认：False）
        default: 提取失败时使用的默认值（默认：None）
        description: 提取器描述（默认：""）
        condition: 提取必须为真的条件表达式（默认：None）
        on_failure: 失败处理配置（默认：None）
    """

    name: str
    type: str
    path: str
    index: int = 0
    extract_all: bool = False
    default: Any = None
    description: str = ''
    condition: str | None = None
    on_failure: dict[str, Any] | None = None


@dataclass
class TestStep:
    """单个测试步骤。

    Attributes:
        name: 步骤名称
        type: 步骤类型（request、database、wait、loop、concurrent 等）
        method: HTTP 方法（用于 API 请求）
        url: 请求 URL
        params: 查询参数或数据库查询参数
        headers: 请求头
        body: 请求体
        validations: 验证规则列表
        extractors: 变量提取器列表
        skip_if: 条件跳过表达式
        only_if: 条件执行表达式
        depends_on: 此步骤依赖的步骤名称列表
        timeout: 步骤特定超时时间
        retry_times: 步骤特定重试次数
        setup: 前置钩子（步骤执行前）
        teardown: 后置钩子（步骤执行后）
        database: 数据库配置（用于数据库步骤）
            - type: 数据库类型（mysql/postgresql/sqlite）
            - host: 数据库主机（用于 MySQL/PostgreSQL）
            - port: 数据库端口（用于 MySQL/PostgreSQL）
            - user: 数据库用户（用于 MySQL/PostgreSQL）
            - password: 数据库密码（用于 MySQL/PostgreSQL）
            - database: 数据库名称（用于 MySQL/PostgreSQL）
            - path: 数据库文件路径（用于 SQLite）
        operation: 数据库操作类型（query/exec/executemany/script）
        sql: 要执行的 SQL 语句
        seconds: 等待持续时间（秒）（用于等待步骤）
        condition: 等待的条件表达式（用于等待步骤）
        interval: 轮询间隔（秒）（用于条件等待，默认：1）
        max_wait: 最大等待时间（秒）（用于条件等待，默认：60）
        loop_type: 循环类型（for/while）（用于循环步骤）
        loop_count: 循环迭代次数（用于 for 循环）
        loop_condition: 循环继续条件（用于 while 循环）
        loop_variable: 循环计数器的变量名（用于循环）
        loop_steps: 循环中执行的步骤（用于循环步骤）
        retry_policy: 增强重试策略配置
            - max_attempts: 最大重试次数
            - strategy: 重试策略（fixed/exponential/linear/custom）
            - base_delay: 基础延迟（秒）
            - max_delay: 最大延迟（秒）
            - backoff_multiplier: 指数退避乘数
            - jitter: 是否添加随机抖动
            - retry_on: 要重试的错误类型列表
            - stop_on: 停止重试的错误类型列表
        max_concurrency: 最大并发线程数（用于并发步骤）
        concurrent_steps: 并发执行的步骤（用于并发步骤）
        script: 要执行的脚本代码（用于脚本步骤）
        script_type: 脚本语言类型（python/javascript，默认：python）
        allow_imports: 是否允许脚本中的模块导入（默认：true）
        poll_config: 异步操作的轮询配置
            - condition: 轮询检查条件（jsonpath/status_code/script）
            - max_attempts: 最大轮询次数
            - interval: 轮询间隔（毫秒）
            - timeout: 总超时时间（毫秒）
            - backoff: 退避策略（fixed/exponential）
        on_timeout: 超时处理配置
            - behavior: 超时时的行为（fail/continue）
            - message: 超时消息
    """

    name: str
    type: str
    method: str | None = None
    url: str | None = None
    params: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
    body: Any | None = None
    validations: list[ValidationRule] = field(default_factory=list)
    extractors: list[Extractor] = field(default_factory=list)
    skip_if: str | None = None
    only_if: str | None = None
    depends_on: list[str] = field(default_factory=list)
    timeout: int | None = None
    retry_times: int | None = None
    setup: dict[str, Any] | None = None
    teardown: dict[str, Any] | None = None
    database: dict[str, Any] | None = None
    operation: str | None = None
    sql: str | None = None
    # Wait step fields
    seconds: float | None = None
    condition: str | None = None
    interval: float | None = None
    max_wait: float | None = None
    wait_condition: dict[str, Any] | None = None
    # Loop step fields
    loop_type: str | None = None
    loop_count: int | None = None
    loop_condition: str | None = None
    loop_variable: str | None = None
    loop_steps: list[dict[str, Any]] | None = None
    # Retry policy fields
    retry_policy: dict[str, Any] | None = None
    # Concurrent step fields
    max_concurrency: int | None = None
    concurrent_steps: list[dict[str, Any]] | None = None
    # Script step fields
    script: str | None = None
    script_file: str | None = None  # Path to external Python script file
    script_type: str | None = None
    allow_imports: bool | None = None
    args: dict[str, Any] | None = None  # Arguments to pass to script
    capture_output: bool | None = None  # Whether to capture script output
    # Poll step fields (for async operation polling)
    poll_config: dict[str, Any] | None = None
    on_timeout: dict[str, Any] | None = None


@dataclass
class TestCase:
    """测试用例定义。

    Attributes:
        name: 测试用例名称
        description: 测试用例描述
        config: 全局配置
        steps: 测试步骤列表
        setup: 全局前置钩子
        teardown: 全局后置钩子
        tags: 用于过滤的测试用例标签
        enabled: 测试用例是否启用
    """

    name: str
    description: str = ''
    config: GlobalConfig | None = None
    steps: list[TestStep] = field(default_factory=list)
    setup: dict[str, Any] | None = None
    teardown: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ErrorInfo:
    """详细错误信息。

    Attributes:
        type: 错误类型（异常类名）
        category: 错误类别
        message: 错误消息
        suggestion: 错误建议修复
        stack_trace: 完整堆栈跟踪
        context: 额外上下文信息（变量、步骤名等）
        timestamp: 错误发生时间
        severity: 错误严重程度（critical/high/medium/low）
        error_code: 机器可读的错误代码
    """

    type: str
    category: ErrorCategory
    message: str
    suggestion: str = ''
    stack_trace: str = ''
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None
    severity: str = 'medium'
    error_code: str = ''


@dataclass
class PerformanceMetrics:
    """步骤性能指标。

    Attributes:
        total_time: 总执行时间（毫秒）
        dns_time: DNS 查找时间（毫秒）
        tcp_time: TCP 连接时间（毫秒）
        tls_time: TLS 握手时间（毫秒）
        server_time: 服务器处理时间（毫秒）
        download_time: 下载时间（毫秒）
        upload_time: 上传时间（毫秒）
        size: 响应大小（字节）
    """

    total_time: float = 0.0
    dns_time: float = 0.0
    tcp_time: float = 0.0
    tls_time: float = 0.0
    server_time: float = 0.0
    download_time: float = 0.0
    upload_time: float = 0.0
    size: int = 0


@dataclass
class StepResult:
    """单个测试步骤执行结果。

    Attributes:
        name: 步骤名称
        status: 执行状态（success、failure、skipped、error）
        response: HTTP 响应数据
        extracted_vars: 提取的变量
        validation_results: 验证结果列表
        performance: 性能指标
        error_info: 失败时的错误信息
        start_time: 步骤开始时间戳
        end_time: 步骤结束时间戳
        retry_count: 执行的重试次数
        variables_snapshot: 执行前的变量状态
        retry_history: 详细的重试尝试历史
        variables_delta: 执行期间的变量变化（执行前 -> 执行后）
        variables_after: 执行后的变量状态
    """

    name: str
    status: str
    response: dict[str, Any] | None = None
    extracted_vars: dict[str, Any] = field(default_factory=dict)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    performance: PerformanceMetrics | None = None
    error_info: ErrorInfo | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    retry_count: int = 0
    variables_snapshot: dict[str, Any] = field(default_factory=dict)
    retry_history: list[dict[str, Any]] = field(default_factory=list)
    variables_delta: dict[str, Any] = field(default_factory=dict)
    variables_after: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCaseResult:
    """测试用例执行结果。

    Attributes:
        name: 测试用例名称
        status: 总体状态（passed、failed、skipped、error）
        start_time: 测试用例开始时间戳
        end_time: 测试用例结束时间戳
        duration: 总持续时间（秒）
        total_steps: 总步骤数
        passed_steps: 通过的步骤数
        failed_steps: 失败的步骤数
        skipped_steps: 跳过的步骤数
        step_results: 各个步骤的结果列表
        final_variables: 所有变量的最终状态
        error_info: 失败时的错误信息
    """

    name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration: float
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    step_results: list[StepResult] = field(default_factory=list)
    final_variables: dict[str, Any] = field(default_factory=dict)
    error_info: ErrorInfo | None = None
