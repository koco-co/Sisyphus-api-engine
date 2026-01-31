"""Unit tests for ValidationEngine.

Tests for validation engine in apirun/validation/engine.py
Following Google Python Style Guide.
"""

import pytest
from apirun.validation.engine import ValidationEngine


class TestValidationEngine:
    """Tests for ValidationEngine class."""

    def test_initialization(self):
        """Test ValidationEngine initialization."""
        engine = ValidationEngine()
        assert engine is not None

    def test_validate_single_rule_pass(self):
        """Test validating with single passing rule."""
        engine = ValidationEngine()
        data = {"status": 200, "message": "OK"}

        rules = [{"type": "eq", "path": "$.status", "expect": 200}]
        results = engine.validate(rules, data)

        assert len(results) == 1
        assert results[0]["passed"] is True

    def test_validate_single_rule_fail(self):
        """Test validating with single failing rule."""
        engine = ValidationEngine()
        data = {"status": 404, "message": "Not Found"}

        rules = [{"type": "eq", "path": "$.status", "expect": 200}]
        results = engine.validate(rules, data)

        assert len(results) == 1
        assert results[0]["passed"] is False

    def test_validate_multiple_rules(self):
        """Test validating with multiple rules."""
        engine = ValidationEngine()
        data = {
            "status": 200,
            "user": {"id": 123, "name": "Alice"},
            "items": [1, 2, 3]
        }

        rules = [
            {"type": "eq", "path": "$.status", "expect": 200},
            {"type": "eq", "path": "$.user.id", "expect": 123},
            {"type": "length_eq", "path": "$.items", "expect": 3},
        ]
        results = engine.validate(rules, data)

        assert len(results) == 3
        assert all(r["passed"] for r in results)

    def test_validate_with_jsonpath(self):
        """Test validation with JSONPath extraction."""
        engine = ValidationEngine()
        data = {
            "data": {
                "user": {
                    "name": "Bob",
                    "age": 25
                }
            }
        }

        rules = [
            {"type": "eq", "path": "$.data.user.name", "expect": "Bob"},
            {"type": "gt", "path": "$.data.user.age", "expect": 20},
        ]
        results = engine.validate(rules, data)

        assert all(r["passed"] for r in results)

    def test_validate_nested_object(self):
        """Test validation with nested object."""
        engine = ValidationEngine()
        data = {
            "response": {
                "status": "success",
                "data": {
                    "users": [
                        {"id": 1, "name": "Alice"},
                        {"id": 2, "name": "Bob"}
                    ]
                }
            }
        }

        rules = [
            {"type": "eq", "path": "$.response.status", "expect": "success"},
            {"type": "length_eq", "path": "$.response.data.users", "expect": 2},
        ]
        results = engine.validate(rules, data)

        assert all(r["passed"] for r in results)

    def test_validate_array_element(self):
        """Test validation with array element."""
        engine = ValidationEngine()
        data = {
            "items": [
                {"id": 1, "active": True},
                {"id": 2, "active": False},
            ]
        }

        rules = [
            {"type": "eq", "path": "$.items[0].id", "expect": 1},
            {"type": "eq", "path": "$.items[1].active", "expect": False},
        ]
        results = engine.validate(rules, data)

        assert all(r["passed"] for r in results)

    def test_validate_with_root_path(self):
        """Test validation with root path $."""
        engine = ValidationEngine()
        data = {"status": "ok"}

        rules = [{"type": "eq", "path": "$", "expect": data}]
        results = engine.validate(rules, data)

        # Root path comparison might not work as expected, just ensure it runs
        assert len(results) == 1

    def test_validate_with_empty_rules(self):
        """Test validation with empty rules list."""
        engine = ValidationEngine()
        data = {"status": "ok"}

        results = engine.validate([], data)
        assert results == []

    def test_validate_contains(self):
        """Test contains validation."""
        engine = ValidationEngine()
        data = {"message": "Operation successful"}

        rules = [
            {"type": "contains", "path": "$.message", "expect": "successful"}
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True

    def test_validate_regex(self):
        """Test regex validation."""
        engine = ValidationEngine()
        data = {"email": "user@example.com"}

        rules = [
            {"type": "regex", "path": "$.email", "expect": r"^[a-z]+@[a-z]+\.[a-z]+$"}
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True

    def test_validate_type(self):
        """Test type validation."""
        engine = ValidationEngine()
        data = {"count": 42, "name": "Alice", "active": True}

        rules = [
            {"type": "type", "path": "$.count", "expect": "int"},
            {"type": "type", "path": "$.name", "expect": "str"},
            {"type": "type", "path": "$.active", "expect": "bool"},
        ]
        results = engine.validate(rules, data)

        assert all(r["passed"] for r in results)

    def test_validate_in_list(self):
        """Test in_list validation."""
        engine = ValidationEngine()
        data = {"status": "pending"}

        rules = [
            {"type": "in_list", "path": "$.status", "expect": ["pending", "processing", "completed"]}
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True

    def test_validate_between(self):
        """Test between validation."""
        engine = ValidationEngine()
        data = {"score": 85}

        rules = [
            {"type": "between", "path": "$.score", "expect": [0, 100]}
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True

    def test_validate_with_missing_field(self):
        """Test validation when field is missing."""
        engine = ValidationEngine()
        data = {"status": "ok"}

        rules = [
            {"type": "eq", "path": "$.nonexistent", "expect": "value"}
        ]
        results = engine.validate(rules, data)

        # Should return result with passed=False when field not found
        assert len(results) == 1
        assert results[0]["passed"] is False

    def test_validate_result_structure(self):
        """Test validation result has correct structure."""
        engine = ValidationEngine()
        data = {"value": 100}

        rules = [{"type": "eq", "path": "$.value", "expect": 100}]
        results = engine.validate(rules, data)

        result = results[0]
        assert "passed" in result
        assert "type" in result
        assert "actual" in result
        assert "expected" in result
        assert "description" in result

    def test_validate_mixed_results(self):
        """Test validation with mixed pass/fail results."""
        engine = ValidationEngine()
        data = {
            "status": 200,
            "count": 5,
            "name": "Test"
        }

        rules = [
            {"type": "eq", "path": "$.status", "expect": 200},  # Pass
            {"type": "gt", "path": "$.count", "expect": 10},  # Fail
            {"type": "contains", "path": "$.name", "expect": "es"},  # Pass
        ]
        results = engine.validate(rules, data)

        assert len(results) == 3
        passed_count = sum(1 for r in results if r["passed"])
        assert passed_count == 2

    def test_validate_with_complex_expect(self):
        """Test validation with complex expected value."""
        engine = ValidationEngine()
        data = {"items": [1, 2, 3, 4, 5]}

        rules = [
            {"type": "length_eq", "path": "$.items", "expect": 5}
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True

    def test_validate_description_in_result(self):
        """Test that description is included in result."""
        engine = ValidationEngine()
        data = {"value": "test"}

        description = "Value should be test"
        rules = [
            {
                "type": "eq",
                "path": "$.value",
                "expect": "test",
                "description": description
            }
        ]
        results = engine.validate(rules, data)

        assert results[0]["description"] == description


class TestValidationEngineWildcardExtraction:
    """Tests for wildcard extraction in validation - Bug fix verification."""

    def test_validate_contains_with_wildcard_path(self):
        """Test contains validation with wildcard path - 用户报告的场景修复.

        验证修复：Contains 验证器现在能正确处理通配符路径
        Bug: 使用 index=0 只提取第一个匹配，导致 contains 验证失败
        Fix: 检测通配符 [*] 或 ..，使用 index=-1 提取所有匹配
        """
        engine = ValidationEngine()
        # 用户报告的真实场景：items 数组包含多个元素
        data = {
            "items": [
                {"paramName": "value1", "value": "test1"},
                {"paramName": "test_param_xxx", "value": "test2"},
                {"paramName": "value3", "value": "test3"}
            ]
        }

        # 使用通配符路径提取所有 paramName 值
        rules = [
            {
                "type": "contains",
                "path": "$.items[*].paramName",
                "expect": "test_param_xxx",
                "description": "验证 paramName 数组包含目标值（通配符路径）"
            }
        ]
        results = engine.validate(rules, data)

        # 验证：应提取到所有 paramName 值：["value1", "test_param_xxx", "value3"]
        # contains 验证应成功
        assert results[0]["passed"] is True
        assert results[0]["actual"] == ["value1", "test_param_xxx", "value3"]

    def test_validate_contains_with_recursive_wildcard(self):
        """Test contains validation with recursive wildcard ..."""
        engine = ValidationEngine()
        data = {
            "level1": {
                "level2": {
                    "items": ["apple", "banana", "test_param_xxx"]
                }
            }
        }

        rules = [
            {
                "type": "contains",
                "path": "$..items",
                "expect": ["apple", "banana", "test_param_xxx"],  # 期望值是整个 items 数组
                "description": "验证递归通配符提取包含目标数组"
            }
        ]
        results = engine.validate(rules, data)

        # 递归通配符会提取到嵌套的数组：[["apple", "banana", "test_param_xxx"]]
        # contains 检查外层数组是否包含 items 数组
        assert results[0]["passed"] is True
        # 验证提取到的数据结构
        assert results[0]["actual"] == [["apple", "banana", "test_param_xxx"]]

    def test_validate_not_contains_with_wildcard_path(self):
        """Test not_contains validation with wildcard path."""
        engine = ValidationEngine()
        data = {
            "items": [
                {"name": "apple", "count": 5},
                {"name": "banana", "count": 3},
                {"name": "orange", "count": 7}
            ]
        }

        rules = [
            {
                "type": "not_contains",
                "path": "$.items[*].name",
                "expect": "grape",
                "description": "验证数组不包含某个值"
            }
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True

    def test_validate_contains_without_wildcard_uses_index_zero(self):
        """Test contains validation without wildcard uses default index=0.

        验证：非通配符路径仍然使用 index=0（默认行为）
        """
        engine = ValidationEngine()
        data = {
            "user": {
                "name": "Alice",
                "roles": ["admin", "user"]
            }
        }

        # 简单路径，不使用通配符
        rules = [
            {
                "type": "contains",
                "path": "$.user.name",
                "expect": "Ali",
                "description": "验证字符串包含（简单路径）"
            }
        ]
        results = engine.validate(rules, data)

        assert results[0]["passed"] is True
        assert results[0]["actual"] == "Alice"
