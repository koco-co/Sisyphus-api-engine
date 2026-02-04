"""核心数据模型单元测试。

本模块包含对 apirun/core/models.py 中所有数据模型的单元测试。
遵循 Google Python Style Guide。
"""

import pytest
from datetime import datetime
from dataclasses import asdict
from apirun.core.models import (
    HttpMethod,
    ErrorCategory,
    ProfileConfig,
    GlobalConfig,
    ValidationRule,
    Extractor,
    TestStep,
    TestCase,
    ErrorInfo,
    PerformanceMetrics,
    StepResult,
    TestCaseResult,
)


class TestHttpMethod:
    """测试 HttpMethod 枚举类。"""

    def test_http_method_values(self):
        """测试 HTTP 方法枚举值。"""
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.DELETE.value == "DELETE"
        assert HttpMethod.PATCH.value == "PATCH"
        assert HttpMethod.HEAD.value == "HEAD"
        assert HttpMethod.OPTIONS.value == "OPTIONS"

    def test_http_method_iteration(self):
        """测试 HTTP 方法枚举迭代。"""
        methods = list(HttpMethod)
        assert len(methods) == 7
        assert HttpMethod.GET in methods


class TestErrorCategory:
    """测试 ErrorCategory 枚举类。"""

    def test_error_category_values(self):
        """测试错误类别枚举值。"""
        assert ErrorCategory.ASSERTION.value == "assertion"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.PARSING.value == "parsing"
        assert ErrorCategory.BUSINESS.value == "business"
        assert ErrorCategory.SYSTEM.value == "system"


class TestProfileConfig:
    """测试 ProfileConfig 数据类。"""

    def test_profile_config_creation(self):
        """测试 ProfileConfig 创建。"""
        config = ProfileConfig(
            base_url="https://api.example.com",
            timeout=60,
            verify_ssl=False
        )
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60
        assert config.verify_ssl is False
        assert config.variables == {}
        assert config.overrides == {}
        assert config.priority == 0

    def test_profile_config_with_variables(self):
        """测试带变量的 ProfileConfig。"""
        config = ProfileConfig(
            base_url="https://api.test.com",
            variables={"api_key": "test123", "timeout": 30}
        )
        assert config.variables == {"api_key": "test123", "timeout": 30}

    def test_profile_config_defaults(self):
        """测试 ProfileConfig 默认值。"""
        config = ProfileConfig(base_url="https://api.default.com")
        assert config.timeout == 30  # 默认超时
        assert config.verify_ssl is True  # 默认验证 SSL
        assert config.priority == 0  # 默认优先级


class TestGlobalConfig:
    """测试 GlobalConfig 数据类。"""

    def test_global_config_creation(self):
        """测试 GlobalConfig 创建。"""
        config = GlobalConfig(name="测试套件")
        assert config.name == "测试套件"
        assert config.description == ""
        assert config.active_profile is None
        assert config.timeout == 30
        assert config.retry_times == 0
        assert config.concurrent is False

    def test_global_config_with_profiles(self):
        """测试带多个环境配置的 GlobalConfig。"""
        dev_profile = ProfileConfig(base_url="https://dev.api.com")
        prod_profile = ProfileConfig(base_url="https://prod.api.com")

        config = GlobalConfig(
            name="多环境测试",
            profiles={"dev": dev_profile, "prod": prod_profile},
            active_profile="dev"
        )
        assert len(config.profiles) == 2
        assert config.active_profile == "dev"
        assert config.profiles["dev"].base_url == "https://dev.api.com"

    def test_global_config_with_data_source(self):
        """测试带数据源配置的 GlobalConfig。"""
        data_source = {
            "type": "csv",
            "file_path": "data/test.csv",
            "delimiter": ",",
            "encoding": "utf-8"
        }

        config = GlobalConfig(
            name="数据驱动测试",
            data_source=data_source,
            data_iterations=True,
            variable_prefix="user"
        )
        assert config.data_source["type"] == "csv"
        assert config.data_iterations is True
        assert config.variable_prefix == "user"


class TestValidationRule:
    """测试 ValidationRule 数据类。"""

    def test_validation_rule_creation(self):
        """测试验证规则创建。"""
        rule = ValidationRule(
            type="eq",
            path="$.status",
            expect=200,
            description="验证状态码为200"
        )
        assert rule.type == "eq"
        assert rule.path == "$.status"
        assert rule.expect == 200
        assert rule.description == "验证状态码为200"

    def test_validation_rule_with_error_message(self):
        """测试带自定义错误消息的验证规则。"""
        rule = ValidationRule(
            type="contains",
            path="$.message",
            expect="success",
            error_message="响应消息必须包含'success'"
        )
        assert rule.error_message == "响应消息必须包含'success'"

    def test_validation_rule_logical_operator(self):
        """测试逻辑运算符验证规则。"""
        rule = ValidationRule(
            type="and",
            logical_operator="and",
            sub_validations=[
                ValidationRule(type="eq", path="$.code", expect=0),
                ValidationRule(type="eq", path="$.status", expect="success")
            ]
        )
        assert rule.logical_operator == "and"
        assert len(rule.sub_validations) == 2


class TestExtractor:
    """测试 Extractor 数据类。"""

    def test_jsonpath_extractor_creation(self):
        """测试 JSONPath 提取器创建。"""
        extractor = Extractor(
            name="user_id",
            type="jsonpath",
            path="$.data.user.id"
        )
        assert extractor.name == "user_id"
        assert extractor.type == "jsonpath"
        assert extractor.path == "$.data.user.id"
        assert extractor.index == 0
        assert extractor.default is None

    def test_extractor_with_default(self):
        """测试带默认值的提取器。"""
        extractor = Extractor(
            name="token",
            type="header",
            path="Authorization",
            default="Bearer default_token"
        )
        assert extractor.default == "Bearer default_token"

    def test_regex_extractor(self):
        """测试正则表达式提取器。"""
        extractor = Extractor(
            name="order_id",
            type="regex",
            path="Order ID: (\\d+)",
            index=1
        )
        assert extractor.type == "regex"
        assert extractor.index == 1


class TestStepModel:
    """测试 TestStep 数据类。"""

    def test_request_step_creation(self):
        """测试请求步骤创建。"""
        step = TestStep(
            name="获取用户信息",
            type="request",
            method="GET",
            url="https://api.example.com/users/1"
        )
        assert step.name == "获取用户信息"
        assert step.type == "request"
        assert step.method == "GET"
        assert step.url == "https://api.example.com/users/1"

    def test_step_with_validations(self):
        """测试带验证规则的步骤。"""
        step = TestStep(
            name="验证响应",
            type="request",
            url="https://api.example.com/status",
            validations=[
                ValidationRule(type="eq", path="$.code", expect=200),
                ValidationRule(type="contains", path="$.message", expect="OK")
            ]
        )
        assert len(step.validations) == 2
        assert step.validations[0].expect == 200

    def test_step_with_extractors(self):
        """测试带提取器的步骤。"""
        step = TestStep(
            name="提取变量",
            type="request",
            url="https://api.example.com/login",
            extractors=[
                Extractor(name="token", type="jsonpath", path="$.data.token"),
                Extractor(name="user_id", type="jsonpath", path="$.data.user_id")
            ]
        )
        assert len(step.extractors) == 2
        assert step.extractors[0].name == "token"

    def test_step_with_retry_policy(self):
        """测试带重试策略的步骤。"""
        retry_policy = {
            "max_attempts": 3,
            "strategy": "exponential",
            "base_delay": 1.0,
            "max_delay": 10.0
        }
        step = TestStep(
            name="重试步骤",
            type="request",
            url="https://api.example.com/unstable",
            retry_policy=retry_policy
        )
        assert step.retry_policy["max_attempts"] == 3
        assert step.retry_policy["strategy"] == "exponential"

    def test_step_with_dependencies(self):
        """测试带依赖关系的步骤。"""
        step = TestStep(
            name="使用 token",
            type="request",
            url="https://api.example.com/profile",
            depends_on=["登录步骤"]
        )
        assert "登录步骤" in step.depends_on


class TestModel:
    """测试 TestCase 数据类。"""

    def test_test_case_creation(self):
        """测试测试用例创建。"""
        case = TestCase(name="用户登录测试")
        assert case.name == "用户登录测试"
        assert case.description == ""
        assert case.enabled is True
        assert len(case.steps) == 0

    def test_test_case_with_steps(self):
        """测试带步骤的测试用例。"""
        steps = [
            TestStep(name="步骤1", type="request", url="https://api.example.com/step1"),
            TestStep(name="步骤2", type="request", url="https://api.example.com/step2")
        ]
        case = TestCase(
            name="多步骤测试",
            steps=steps
        )
        assert len(case.steps) == 2
        assert case.steps[0].name == "步骤1"

    def test_test_case_with_config(self):
        """测试带配置的测试用例。"""
        config = GlobalConfig(
            name="测试配置",
            variables={"base_url": "https://api.test.com"}
        )
        case = TestCase(
            name="配置测试",
            config=config
        )
        assert case.config is not None
        assert case.config.variables["base_url"] == "https://api.test.com"

    def test_test_case_with_tags(self):
        """测试带标签的测试用例。"""
        case = TestCase(
            name="标签测试",
            tags=["smoke", "critical", "auth"]
        )
        assert len(case.tags) == 3
        assert "smoke" in case.tags
        assert case.enabled is True


class TestErrorInfo:
    """测试 ErrorInfo 数据类。"""

    def test_error_info_creation(self):
        """测试错误信息创建。"""
        error = ErrorInfo(
            type="ValueError",
            category=ErrorCategory.BUSINESS,
            message="无效的参数值"
        )
        assert error.type == "ValueError"
        assert error.category == ErrorCategory.BUSINESS
        assert error.message == "无效的参数值"
        assert error.severity == "medium"

    def test_error_info_with_suggestion(self):
        """测试带建议的错误信息。"""
        error = ErrorInfo(
            type="ConnectionError",
            category=ErrorCategory.NETWORK,
            message="无法连接到服务器",
            suggestion="请检查网络连接和服务器状态"
        )
        assert error.suggestion == "请检查网络连接和服务器状态"

    def test_error_info_with_context(self):
        """测试带上下文的错误信息。"""
        error = ErrorInfo(
            type="AssertionError",
            category=ErrorCategory.ASSERTION,
            message="状态码不匹配",
            context={"step": "验证状态码", "expected": 200, "actual": 500}
        )
        assert error.context["step"] == "验证状态码"
        assert error.context["expected"] == 200


class TestPerformanceMetrics:
    """测试 PerformanceMetrics 数据类。"""

    def test_performance_metrics_creation(self):
        """测试性能指标创建。"""
        metrics = PerformanceMetrics(
            total_time=1500.0,
            dns_time=50.0,
            tcp_time=100.0,
            tls_time=200.0
        )
        assert metrics.total_time == 1500.0
        assert metrics.dns_time == 50.0
        assert metrics.tcp_time == 100.0
        assert metrics.tls_time == 200.0

    def test_performance_metrics_defaults(self):
        """测试性能指标默认值。"""
        metrics = PerformanceMetrics()
        assert metrics.total_time == 0.0
        assert metrics.size == 0


class TestStepResult:
    """测试 StepResult 数据类。"""

    def test_step_result_creation(self):
        """测试步骤结果创建。"""
        result = StepResult(
            name="测试步骤",
            status="success"
        )
        assert result.name == "测试步骤"
        assert result.status == "success"
        assert result.retry_count == 0

    def test_step_result_with_performance(self):
        """测试带性能指标的步骤结果。"""
        performance = PerformanceMetrics(total_time=500.0)
        result = StepResult(
            name="性能测试",
            status="success",
            performance=performance
        )
        assert result.performance is not None
        assert result.performance.total_time == 500.0

    def test_step_result_with_error(self):
        """测试带错误信息的步骤结果。"""
        error = ErrorInfo(
            type="TimeoutError",
            category=ErrorCategory.TIMEOUT,
            message="请求超时"
        )
        result = StepResult(
            name="超时步骤",
            status="error",
            error_info=error
        )
        assert result.error_info is not None
        assert result.error_info.category == ErrorCategory.TIMEOUT


class TestResultModel:
    """测试 TestCaseResult 数据类。"""

    def test_test_case_result_creation(self):
        """测试测试用例结果创建。"""
        now = datetime.now()
        result = TestCaseResult(
            name="测试用例",
            status="passed",
            start_time=now,
            end_time=now,
            duration=1.5,
            total_steps=5,
            passed_steps=5,
            failed_steps=0,
            skipped_steps=0
        )
        assert result.name == "测试用例"
        assert result.status == "passed"
        assert result.duration == 1.5
        assert result.passed_steps == 5

    def test_test_case_result_with_step_results(self):
        """测试带步骤结果的测试用例结果。"""
        step1 = StepResult(name="步骤1", status="success")
        step2 = StepResult(name="步骤2", status="success")
        now = datetime.now()

        result = TestCaseResult(
            name="多步骤用例",
            status="passed",
            start_time=now,
            end_time=now,
            duration=2.0,
            total_steps=2,
            passed_steps=2,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1, step2]
        )
        assert len(result.step_results) == 2
        assert result.step_results[0].name == "步骤1"

    def test_test_case_result_final_variables(self):
        """测试带最终变量的测试用例结果。"""
        now = datetime.now()
        result = TestCaseResult(
            name="变量测试",
            status="passed",
            start_time=now,
            end_time=now,
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            final_variables={"user_id": "123", "token": "abc"}
        )
        assert result.final_variables["user_id"] == "123"
        assert result.final_variables["token"] == "abc"
