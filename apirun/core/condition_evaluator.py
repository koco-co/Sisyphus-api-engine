"""Condition Evaluator for Sisyphus API Engine.

This module implements condition expression evaluation, supporting:
- String expressions with comparison operators
- Structured logical expressions (AND/OR/NOT)
- Concise expressions with Python-like operators
- Variable substitution and type inference

Following Google Python Style Guide.
"""

import re
from typing import Any

from apirun.utils.template import render_template


class ConditionEvaluator:
    """Evaluates condition expressions for step control.

    Supports three formats:
    1. String expression: "${var} != null"
    2. Structured logic: {and: ["${var1} != null", "${var2} != null"]}
    3. Concise expression: "${var1} and ${var2}"

    Attributes:
        variables: Dictionary of variables for substitution
    """

    # Comparison operators
    COMPARISON_OPS = {
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '>': lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
        '<': lambda a, b: a < b,
        '<=': lambda a, b: a <= b,
        'in': lambda a, b: a in b if isinstance(b, (list, tuple, str)) else False,
        'not_in': lambda a, b: (
            a not in b if isinstance(b, (list, tuple, str)) else True
        ),
        'contains': lambda a, b: b in a if isinstance(a, (list, tuple, str)) else False,
        'not_contains': lambda a, b: (
            b not in a if isinstance(a, (list, tuple, str)) else True
        ),
    }

    # Logical keywords for concise expressions
    LOGICAL_KEYWORDS = ['and', 'or', 'not']

    def __init__(self, variables: dict[str, Any]):
        """Initialize ConditionEvaluator.

        Args:
            variables: Dictionary of variables for substitution
        """
        self.variables = variables

    def evaluate(self, condition: Any) -> bool:
        """Evaluate a condition expression.

        Args:
            condition: Condition expression (string, dict, or list)

        Returns:
            True if condition evaluates to true, False otherwise

        Raises:
            ValueError: If condition format is invalid
        """
        if condition is None or condition == '':
            return True

        # String condition - support both formats
        if isinstance(condition, str):
            # Check for structured format indicator (not quoted)
            if condition.strip() in ['and', 'or', 'not']:
                raise ValueError(
                    f"Invalid condition: logical operator '{condition}' must be used in structured format"
                )

            # Try concise expression first (contains 'and', 'or')
            if self._has_logical_operators(condition):
                return self._evaluate_concise_expression(condition)

            # Fall back to simple string expression
            return self._evaluate_string_expression(condition)

        # Structured condition (dict with logical operators)
        elif isinstance(condition, dict):
            return self._evaluate_structured_condition(condition)

        # List condition (implicit AND)
        elif isinstance(condition, list):
            return all(self.evaluate(cond) for cond in condition)

        else:
            raise ValueError(f'Invalid condition type: {type(condition)}')

    def _has_logical_operators(self, expression: str) -> bool:
        """Check if expression contains logical operators.

        Args:
            expression: Expression string to check

        Returns:
            True if expression contains 'and', 'or', or 'not' operators
        """
        # Pattern to match 'and', 'or', 'not' as whole words (not part of other words)
        pattern = r'\b(and|or|not)\b'
        matches = re.findall(pattern, expression, re.IGNORECASE)
        return len(matches) > 0

    def _evaluate_string_expression(self, expression: str) -> bool:
        """Evaluate a simple string expression.

        Args:
            expression: String expression like "${var} != null"

        Returns:
            True if expression evaluates to true
        """
        # Render template
        rendered = render_template(expression, self.variables).strip()

        # Handle empty/whitespace-only expressions
        if not rendered:
            return False

        # Direct boolean check
        if rendered.lower() in ('true', '1', 'yes'):
            return True
        if rendered.lower() in ('false', '0', 'no', 'null', 'none'):
            return False

        # Try to evaluate as comparison expression
        try:
            return self._evaluate_comparison(rendered)
        except ValueError:
            # If not a comparison, check truthiness of rendered value
            return self._is_truthy(rendered)

    def _evaluate_comparison(self, expression: str) -> bool:
        """Evaluate a comparison expression.

        Args:
            expression: Expression like "value1 == value2" or "5 > 3"

        Returns:
            True if comparison is true

        Raises:
            ValueError: If expression format is invalid
        """
        # Try each comparison operator
        for op, func in self.COMPARISON_OPS.items():
            # Use regex to split on operator (but not inside strings)
            pattern = rf'\s+{re.escape(op)}\s+'
            parts = re.split(pattern, expression, maxsplit=1)

            if len(parts) == 2:
                left_str, right_str = parts
                left_value = self._parse_value(left_str.strip())
                right_value = self._parse_value(right_str.strip())
                return func(left_value, right_value)

        # No comparison operator found
        raise ValueError(f'Invalid comparison expression: {expression}')

    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value to its Python type.

        Args:
            value_str: String value to parse

        Returns:
            Parsed value (int, float, bool, str, None, etc.)
        """
        value_str = value_str.strip()

        # Null values
        if value_str.lower() in ('null', 'none'):
            return None

        # Boolean values
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False

        # Numeric values
        try:
            # Try integer first
            if '.' not in value_str and 'e' not in value_str.lower():
                return int(value_str)
            else:
                return float(value_str)
        except ValueError:
            pass

        # String values (remove quotes if present)
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]

        # Default: return as string
        return value_str

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy.

        Args:
            value: Value to check

        Returns:
            True if value is truthy
        """
        if value is None:
            return False
        if isinstance(value, str):
            return value.lower() not in ('', 'false', '0', 'no', 'null', 'none')
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, (list, tuple, dict)):
            return len(value) > 0
        return bool(value)

    def _evaluate_concise_expression(self, expression: str) -> bool:
        """Evaluate a concise expression with 'and', 'or', 'not' operators.

        Args:
            expression: Expression like "${var1} and ${var2} or ${var3}"

        Returns:
            True if expression evaluates to true

        Raises:
            ValueError: If expression is invalid
        """
        # First render variables
        rendered = render_template(expression, self.variables).strip()

        # Tokenize and evaluate using operator precedence
        # Precedence: NOT > AND > OR
        return self._evaluate_with_precedence(rendered)

    def _evaluate_with_precedence(self, expr: str) -> bool:
        """Evaluate expression with proper operator precedence.

        Args:
            expr: Expression string (already rendered)

        Returns:
            True if expression evaluates to true
        """
        # Tokenize into operands and operators
        tokens = self._tokenize_logical_expression(expr)

        # First pass: evaluate NOT operators (highest precedence)
        tokens = self._evaluate_not_operators(tokens)

        # Second pass: evaluate AND operators
        tokens = self._evaluate_and_operators(tokens)

        # Third pass: evaluate OR operators (lowest precedence)
        tokens = self._evaluate_or_operators(tokens)

        # Should have only one token left (the result)
        if len(tokens) == 1:
            return self._is_truthy(tokens[0])
        else:
            # Fallback: try to evaluate remaining tokens
            return self._evaluate_simple_condition(expr)

    def _tokenize_logical_expression(self, expr: str) -> list:
        """Tokenize logical expression into operands and operators.

        Args:
            expr: Expression string

        Returns:
            List of tokens (operands and operators)
        """
        tokens = []
        current = ''
        i = 0

        while i < len(expr):
            # Check for 'and', 'or', 'not' operators as whole words
            if expr[i : i + 3].lower() == 'and' and self._is_word_boundary(expr, i, 3):
                if current.strip():
                    tokens.append(current.strip())
                tokens.append('and')
                current = ''
                i += 3
            elif expr[i : i + 2].lower() == 'or' and self._is_word_boundary(expr, i, 2):
                if current.strip():
                    tokens.append(current.strip())
                tokens.append('or')
                current = ''
                i += 2
            elif expr[i : i + 3].lower() == 'not' and self._is_word_boundary(
                expr, i, 3
            ):
                if current.strip():
                    tokens.append(current.strip())
                tokens.append('not')
                current = ''
                i += 3
            else:
                current += expr[i]
                i += 1

        if current.strip():
            tokens.append(current.strip())

        return tokens

    def _is_word_boundary(self, expr: str, start: int, length: int) -> bool:
        """Check if substring is a whole word.

        Args:
            expr: Expression string
            start: Start index
            length: Length of substring

        Returns:
            True if substring is a whole word
        """
        # Check before
        if start > 0 and expr[start - 1].isalnum():
            return False
        # Check after
        if start + length < len(expr) and expr[start + length].isalnum():
            return False
        return True

    def _evaluate_not_operators(self, tokens: list) -> list:
        """Evaluate NOT operators in token list.

        Args:
            tokens: Token list

        Returns:
            Token list with NOT operators evaluated
        """
        result = []
        i = 0
        while i < len(tokens):
            if tokens[i] == 'not' and i + 1 < len(tokens):
                # Evaluate NOT operand
                operand_value = self._evaluate_simple_condition(tokens[i + 1])
                result.append('false' if operand_value else 'true')
                i += 2
            elif tokens[i] == 'not':
                # NOT at end - invalid, treat as operand
                result.append(tokens[i])
                i += 1
            else:
                result.append(tokens[i])
                i += 1
        return result

    def _evaluate_and_operators(self, tokens: list) -> list:
        """Evaluate AND operators in token list.

        Args:
            tokens: Token list

        Returns:
            Token list with AND operators evaluated
        """
        result = []
        i = 0
        while i < len(tokens):
            if tokens[i] == 'and':
                # Pop last operand from result
                if result:
                    left = result.pop()
                    if i + 1 < len(tokens):
                        right = tokens[i + 1]
                        left_value = self._is_truthy(left)
                        right_value = self._is_truthy(right)
                        result.append(
                            'true' if (left_value and right_value) else 'false'
                        )
                        i += 2
                        continue
                # Invalid AND, skip
                i += 1
            else:
                result.append(tokens[i])
                i += 1
        return result

    def _evaluate_or_operators(self, tokens: list) -> list:
        """Evaluate OR operators in token list.

        Args:
            tokens: Token list

        Returns:
            Token list with OR operators evaluated
        """
        result = []
        i = 0
        while i < len(tokens):
            if tokens[i] == 'or':
                # Pop last operand from result
                if result:
                    left = result.pop()
                    if i + 1 < len(tokens):
                        right = tokens[i + 1]
                        left_value = self._is_truthy(left)
                        right_value = self._is_truthy(right)
                        result.append(
                            'true' if (left_value or right_value) else 'false'
                        )
                        i += 2
                        continue
                # Invalid OR, skip
                i += 1
            else:
                result.append(tokens[i])
                i += 1
        return result

    def _evaluate_simple_condition(self, condition: str) -> bool:
        """Evaluate a simple condition (no logical operators).

        Args:
            condition: Condition string

        Returns:
            True if condition is true
        """
        condition = condition.strip()

        # Try comparison first
        try:
            return self._evaluate_comparison(condition)
        except ValueError:
            pass

        # Fall back to truthy check
        return self._is_truthy(self._parse_value(condition))

    def _evaluate_structured_condition(self, condition: dict[str, Any]) -> bool:
        """Evaluate a structured condition with logical operators.

        Args:
            condition: Dict like {and: [...]} or {or: [...]} or {not: ...}

        Returns:
            True if condition evaluates to true

        Raises:
            ValueError: If structure is invalid
        """
        if len(condition) != 1:
            raise ValueError(
                f'Structured condition must have exactly one key, got: {list(condition.keys())}'
            )

        op = list(condition.keys())[0].lower()
        value = condition[op]

        if op == 'and':
            if not isinstance(value, list):
                raise ValueError("'and' operator requires a list of conditions")
            return all(self.evaluate(cond) for cond in value)

        elif op == 'or':
            if not isinstance(value, list):
                raise ValueError("'or' operator requires a list of conditions")
            return any(self.evaluate(cond) for cond in value)

        elif op == 'not':
            return not self.evaluate(value)

        else:
            raise ValueError(f'Unknown logical operator: {op}')
