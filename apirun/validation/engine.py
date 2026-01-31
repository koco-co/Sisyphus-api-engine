"""Validation Engine for Sisyphus API Engine.

This module implements the validation engine for running assertions.
Following Google Python Style Guide.
"""

from typing import Any, Dict, List

from apirun.validation.comparators import get_comparator, ComparatorError
from apirun.utils.enhanced_jsonpath import extract_value


class ValidationResult:
    """Result of a single validation.

    Attributes:
        passed: Whether validation passed
        type: Comparator type
        path: JSONPath expression
        actual: Actual value
        expected: Expected value
        description: Validation description
        error: Error message if validation failed
    """

    def __init__(
        self,
        passed: bool,
        type: str,
        path: str,
        actual: Any,
        expected: Any,
        description: str = "",
        error: str = "",
    ):
        """Initialize ValidationResult.

        Args:
            passed: Whether validation passed
            type: Comparator type
            path: JSONPath expression
            actual: Actual value
            expected: Expected value
            description: Validation description
            error: Error message if validation failed
        """
        self.passed = passed
        self.type = type
        self.path = path
        self.actual = actual
        self.expected = expected
        self.description = description
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "passed": self.passed,
            "type": self.type,
            "path": self.path,
            "actual": self.actual,
            "expected": self.expected,
            "description": self.description,
            "error": self.error,
        }


class ValidationEngine:
    """Engine for executing validation rules.

    This engine:
    - Extracts values using JSONPath
    - Applies comparator functions
    - Returns detailed validation results
    """

    def __init__(self):
        """Initialize ValidationEngine."""
        pass

    def validate(
        self, validations: List[Dict[str, Any]], response_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute list of validations.

        Args:
            validations: List of validation rules
            response_data: Response data to validate against

        Returns:
            List of validation results
        """
        results = []

        for validation in validations:
            result = self._validate_single(validation, response_data)
            results.append(result.to_dict())

        return results

    def _validate_single(
        self, validation: Dict[str, Any], response_data: Dict[str, Any]
    ) -> ValidationResult:
        """Execute a single validation.

        Args:
            validation: Validation rule
            response_data: Response data to validate against

        Returns:
            ValidationResult object
        """
        val_type = validation.get("type", "eq")
        path = validation.get("path", "$")
        expect = validation.get("expect")
        description = validation.get("description", "")

        # Check for logical operators
        if val_type in ("and", "or", "not"):
            return self._validate_logical(validation, response_data)

        try:
            # Extract value using JSONPath
            actual = self._extract_value(path, response_data)

            # Get comparator function
            comparator = get_comparator(val_type)

            # Perform comparison
            passed = comparator(actual, expect)

            # Generate error message if failed
            error = ""
            if not passed:
                error = self._generate_error_message(val_type, path, actual, expect)

            return ValidationResult(
                passed=passed,
                type=val_type,
                path=path,
                actual=actual,
                expected=expect,
                description=description,
                error=error,
            )

        except ComparatorError as e:
            return ValidationResult(
                passed=False,
                type=val_type,
                path=path,
                actual=None,
                expected=expect,
                description=description,
                error=f"Comparator error: {e}",
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                type=val_type,
                path=path,
                actual=None,
                expected=expect,
                description=description,
                error=f"Validation error: {e}",
            )

    def _validate_logical(
        self, validation: Dict[str, Any], response_data: Dict[str, Any]
    ) -> ValidationResult:
        """Execute logical validation (and/or/not).

        Args:
            validation: Validation rule with logical operator
            response_data: Response data to validate against

        Returns:
            ValidationResult object
        """
        val_type = validation.get("type")
        description = validation.get("description", "")
        sub_validations = validation.get("sub_validations", [])

        if not sub_validations:
            return ValidationResult(
                passed=False,
                type=val_type,
                path="",
                actual=None,
                expected=None,
                description=description,
                error=f"Logical operator '{val_type}' requires sub_validations",
            )

        # Recursively validate sub-validations
        sub_results = []
        for sub_val in sub_validations:
            result = self._validate_single(sub_val, response_data)
            sub_results.append(result)

        # Apply logical operation
        if val_type == "and":
            # All sub-validations must pass
            passed = all(r.passed for r in sub_results)
            failed_results = [r for r in sub_results if not r.passed]
            error = (
                f"AND validation failed: {len(failed_results)} out of {len(sub_results)} sub-validations failed. "
                f"Failed: {[r.error for r in failed_results]}"
                if failed_results
                else ""
            )

        elif val_type == "or":
            # At least one sub-validation must pass
            passed = any(r.passed for r in sub_results)
            if not passed:
                error = f"OR validation failed: All {len(sub_results)} sub-validations failed"
            else:
                error = ""

        elif val_type == "not":
            # All sub-validations must fail
            passed = not any(r.passed for r in sub_results)
            passed_results = [r for r in sub_results if r.passed]
            if passed_results:
                error = f"NOT validation failed: {len(passed_results)} sub-validations passed when all should fail"
            else:
                error = ""

        else:
            return ValidationResult(
                passed=False,
                type=val_type,
                path="",
                actual=None,
                expected=None,
                description=description,
                error=f"Unknown logical operator: {val_type}",
            )

        return ValidationResult(
            passed=passed,
            type=val_type,
            path="",
            actual=[r.to_dict() for r in sub_results],
            expected=None,
            description=description,
            error=error,
        )

    def _extract_value(self, path: str, data: Any) -> Any:
        """Extract value from data using enhanced JSONPath.

        Args:
            path: JSONPath expression (may include function calls)
            data: Data to extract from

        Returns:
            Extracted value

        Raises:
            ValueError: If path is invalid or value not found

        Examples:
            $.data                    # Get data field
            $.data.length()            # Get array length
            $.users.name               # Get all name fields
            $.items.sum()              # Sum of numeric values
        """
        try:
            return extract_value(path, data, index=0)
        except Exception as e:
            raise ValueError(f"Failed to extract value: {e}")

    def _generate_error_message(
        self, val_type: str, path: str, actual: Any, expected: Any
    ) -> str:
        """Generate descriptive error message.

        Args:
            val_type: Comparator type
            path: JSONPath expression
            actual: Actual value
            expected: Expected value

        Returns:
            Error message
        """
        messages = {
            "eq": f"Expected {expected} but got {actual}",
            "ne": f"Expected not equal to {expected} but got {actual}",
            "gt": f"Expected {actual} > {expected} but failed",
            "lt": f"Expected {actual} < {expected} but failed",
            "ge": f"Expected {actual} >= {expected} but failed",
            "le": f"Expected {actual} <= {expected} but failed",
            "contains": f"Expected '{actual}' to contain '{expected}'",
            "not_contains": f"Expected '{actual}' to not contain '{expected}'",
            "regex": f"'{actual}' does not match pattern '{expected}'",
            "type": f"Expected type {expected} but got {type(actual).__name__}",
            "in": f"Expected {actual} to be in {expected}",
            "not_in": f"Expected {actual} to not be in {expected}",
            "length_eq": f"Expected length {expected} but got {len(actual)}",
            "length_gt": f"Expected length > {expected} but got {len(actual)}",
            "length_lt": f"Expected length < {expected} but got {len(actual)}",
            "is_empty": f"Expected value to be empty but got {actual}",
            "is_null": f"Expected null but got {actual}",
            "status_code": f"Expected status code {expected} but got {actual}",
            "exists": f"Expected value to exist but got None or empty",
            "between": f"Expected {actual} to be between {expected[0]} and {expected[1]}",
        }

        return messages.get(
            val_type, f"Validation failed: path={path}, expected={expected}, actual={actual}"
        )
