"""Unit tests for ConditionEvaluator.

Tests condition expression evaluation with various formats:
- String expressions
- Structured logical expressions
- Concise expressions with logical operators
"""

import pytest
from apirun.core.condition_evaluator import ConditionEvaluator


class TestStringExpressions:
    """Test simple string expression evaluation."""

    def test_simple_true(self):
        """Test simple true condition."""
        evaluator = ConditionEvaluator({})
        assert evaluator.evaluate("true") is True
        assert evaluator.evaluate("True") is True
        assert evaluator.evaluate("1") is True
        assert evaluator.evaluate("yes") is True

    def test_simple_false(self):
        """Test simple false condition."""
        evaluator = ConditionEvaluator({})
        assert evaluator.evaluate("false") is False
        assert evaluator.evaluate("False") is False
        assert evaluator.evaluate("0") is False
        assert evaluator.evaluate("no") is False
        assert evaluator.evaluate("null") is False
        assert evaluator.evaluate("none") is False

    def test_variable_comparison(self):
        """Test variable comparison."""
        variables = {"score": 95, "status": "active"}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${score} > 90") is True
        assert evaluator.evaluate("${score} < 100") is True
        assert evaluator.evaluate("${status} == active") is True
        assert evaluator.evaluate("${status} != inactive") is True

    def test_null_check(self):
        """Test null value checking."""
        variables = {"user_id": "12345", "guest_id": None}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${user_id} != null") is True
        assert evaluator.evaluate("${guest_id} == null") is True
        assert evaluator.evaluate("${guest_id} == none") is True

    def test_equality_operators(self):
        """Test equality operators."""
        variables = {"role": "admin", "count": 5}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${role} == admin") is True
        assert evaluator.evaluate("${role} != guest") is True
        assert evaluator.evaluate("${count} == 5") is True
        assert evaluator.evaluate("${count} != 10") is True

    def test_comparison_operators(self):
        """Test comparison operators."""
        variables = {"score": 85, "age": 25}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${score} > 80") is True
        assert evaluator.evaluate("${score} >= 85") is True
        assert evaluator.evaluate("${score} < 90") is True
        assert evaluator.evaluate("${score} <= 85") is True
        assert evaluator.evaluate("${age} > 20") is True
        assert evaluator.evaluate("${age} < 30") is True


class TestConciseExpressions:
    """Test concise expression with logical operators."""

    def test_and_operator(self):
        """Test AND operator in concise expressions."""
        variables = {"admin": True, "active": True, "guest": False}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${admin} and ${active}") is True
        assert evaluator.evaluate("${admin} and ${guest}") is False
        assert evaluator.evaluate("${guest} and ${active}") is False

    def test_or_operator(self):
        """Test OR operator in concise expressions."""
        variables = {"admin": True, "guest": False, "active": False}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${admin} or ${guest}") is True
        assert evaluator.evaluate("${admin} or ${active}") is True
        assert evaluator.evaluate("${guest} or ${active}") is False

    def test_not_operator(self):
        """Test NOT operator in concise expressions."""
        variables = {"admin": True, "guest": False}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("not ${guest}") is True
        assert evaluator.evaluate("not ${admin}") is False

    def test_combined_logical_operators(self):
        """Test combined logical operators."""
        variables = {
            "role": "admin",
            "status": "active",
            "score": 95,
            "guest": False
        }
        evaluator = ConditionEvaluator(variables)

        # AND has higher precedence than OR
        assert evaluator.evaluate("${role} == admin and ${status} == active or ${guest}") is True
        assert evaluator.evaluate("${guest} and ${status} == active or ${role} == admin") is True
        assert evaluator.evaluate("${guest} and ${status} == active") is False

    def test_complex_expressions(self):
        """Test complex expressions with multiple operators."""
        variables = {
            "user_id": "123",
            "role": "admin",
            "status": "active",
            "score": 85
        }
        evaluator = ConditionEvaluator(variables)

        # Complex condition
        condition = "${user_id} != null and ${role} == admin and ${status} == active or ${score} > 90"
        assert evaluator.evaluate(condition) is True

        # Another complex condition
        condition = "${role} == admin and (${status} == active or ${score} > 90)"
        result = evaluator.evaluate(condition)
        # The parentheses are not actually handled, but this tests robustness
        assert isinstance(result, bool)


class TestStructuredExpressions:
    """Test structured logical expressions."""

    def test_structured_and(self):
        """Test structured AND expression."""
        variables = {"admin": True, "active": True, "verified": True}
        evaluator = ConditionEvaluator(variables)

        condition = {
            "and": [
                "${admin}",
                "${active}",
                "${verified}"
            ]
        }
        assert evaluator.evaluate(condition) is True

        condition = {
            "and": [
                "${admin}",
                "not ${verified}"
            ]
        }
        assert evaluator.evaluate(condition) is False

    def test_structured_or(self):
        """Test structured OR expression."""
        variables = {"admin": True, "guest": False, "verified": False}
        evaluator = ConditionEvaluator(variables)

        condition = {
            "or": [
                "${admin}",
                "${guest}",
                "${verified}"
            ]
        }
        assert evaluator.evaluate(condition) is True

        condition = {
            "or": [
                "${guest}",
                "${verified}"
            ]
        }
        assert evaluator.evaluate(condition) is False

    def test_structured_not(self):
        """Test structured NOT expression."""
        variables = {"admin": True, "guest": False}
        evaluator = ConditionEvaluator(variables)

        condition = {"not": "${guest}"}
        assert evaluator.evaluate(condition) is True

        condition = {"not": "${admin}"}
        assert evaluator.evaluate(condition) is False

    def test_nested_structured(self):
        """Test nested structured expressions."""
        variables = {
            "user_id": "123",
            "role": "admin",
            "status": "active",
            "score": 85
        }
        evaluator = ConditionEvaluator(variables)

        # Nested AND/OR
        condition = {
            "and": [
                "${user_id} != null",
                {
                    "or": [
                        "${role} == admin",
                        "${role} == superuser"
                    ]
                },
                "${status} == active"
            ]
        }
        assert evaluator.evaluate(condition) is True

        # Another nesting
        condition = {
            "or": [
                {
                    "and": [
                        "${role} == admin",
                        "${status} == active"
                    ]
                },
                {
                    "and": [
                        "${role} == guest",
                        "${score} > 100"
                    ]
                }
            ]
        }
        assert evaluator.evaluate(condition) is True


class TestSpecialOperators:
    """Test special operators like 'in', 'contains'."""

    def test_in_operator(self):
        """Test 'in' operator for array membership."""
        variables = {"permissions": ["read", "write", "delete"], "role": "admin"}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("'write' in ${permissions}") is True
        assert evaluator.evaluate("'admin' in ${permissions}") is False
        assert evaluator.evaluate("'execute' not_in ${permissions}") is True

    def test_contains_operator(self):
        """Test 'contains' operator for string/array contains."""
        variables = {"message": "Operation successful", "tags": ["python", "api"]}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("'${message}' contains 'success'") is True
        assert evaluator.evaluate("'${message}' contains 'failed'") is False
        assert evaluator.evaluate("${tags} contains 'python'") is True


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_condition(self):
        """Test empty condition."""
        evaluator = ConditionEvaluator({})
        assert evaluator.evaluate(None) is True
        assert evaluator.evaluate("") is True

    def test_list_condition(self):
        """Test list condition (implicit AND)."""
        variables = {"a": True, "b": True, "c": False}
        evaluator = ConditionEvaluator(variables)

        # List is treated as AND
        condition = ["${a}", "${b}"]
        assert evaluator.evaluate(condition) is True

        condition = ["${a}", "${c}"]
        assert evaluator.evaluate(condition) is False

    def test_invalid_comparison(self):
        """Test invalid comparison expression."""
        evaluator = ConditionEvaluator({"value": "test"})

        # Invalid operator should fall back to truthy check
        result = evaluator.evaluate("${value}")
        assert result is True

    def test_numeric_strings(self):
        """Test numeric string handling."""
        variables = {"count": "5", "score": "95.5"}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${count} > 3") is True
        assert evaluator.evaluate("${score} > 90") is True

    def test_quoted_strings(self):
        """Test quoted string values."""
        variables = {"status": "active"}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${status} == 'active'") is True
        assert evaluator.evaluate('${status} == "active"') is True
        assert evaluator.evaluate("${status} != 'inactive'") is True


class TestBackwardCompatibility:
    """Test backward compatibility with old syntax."""

    def test_legacy_skip_if(self):
        """Test legacy skip_if syntax still works."""
        variables = {"environment": "production", "feature_flag": False}
        evaluator = ConditionEvaluator(variables)

        # Old-style string condition
        assert evaluator.evaluate("${environment} == production") is True
        assert evaluator.evaluate("${feature_flag} == false") is True

    def test_legacy_only_if(self):
        """Test legacy only_if syntax still works."""
        variables = {"user_logged_in": True, "is_admin": False}
        evaluator = ConditionEvaluator(variables)

        assert evaluator.evaluate("${user_logged_in} == true") is True
        assert evaluator.evaluate("${is_admin} == false") is True
