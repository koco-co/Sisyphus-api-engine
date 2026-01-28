"""Command Line Interface for Sisyphus API Engine.

This module provides the CLI entry point for running test cases.
Following Google Python Style Guide.
"""

import argparse
import json
import sys
from typing import Optional
from pathlib import Path

from apirun.parser.v2_yaml_parser import V2YamlParser, YamlParseError
from apirun.executor.test_case_executor import TestCaseExecutor
from apirun.core.variable_manager import VariableManager
from apirun.utils.template import render_template
from apirun.data_driven.iterator import DataDrivenIterator


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Sisyphus API Engine - Enterprise-grade API Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
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
        """,
    )

    parser.add_argument(
        "--cases",
        type=str,
        required=True,
        help="Path to YAML test case file or directory",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path for JSON results",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate YAML syntax without execution",
    )

    parser.add_argument(
        "--profile",
        type=str,
        help="Active profile name (overrides config)",
    )

    args = parser.parse_args()

    try:
        if args.validate:
            return validate_yaml(args.cases)

        # Execute test case
        result = execute_test_case(args.cases, args.verbose, args.profile)

        if args.output:
            save_result(result, args.output)
            if args.verbose:
                print(f"\nResults saved to: {args.output}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except YamlParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def validate_main() -> int:
    """CLI entry point for validation-only mode.

    This is a dedicated command for validating YAML syntax without execution.

    Returns:
        Exit code (0 for valid, non-zero for invalid)
    """
    parser = argparse.ArgumentParser(
        description="Sisyphus API Engine - YAML Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single file
  sisyphus-api-validate test_case.yaml

  # Validate all files in a directory
  sisyphus-api-validate examples/

  # Validate multiple files
  sisyphus-api-validate test1.yaml test2.yaml test3.yaml
        """,
    )

    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="Path(s) to YAML file(s) or directory",
    )

    args = parser.parse_args()

    try:
        all_valid = True
        validator = V2YamlParser()

        for path_str in args.paths:
            path = Path(path_str)

            if not path.exists():
                print(f"Error: Path not found: {path_str}", file=sys.stderr)
                all_valid = False
                continue

            if path.is_file():
                yaml_files = [path]
            elif path.is_dir():
                yaml_files = list(path.glob("**/*.yaml"))
                if not yaml_files:
                    print(f"Warning: No YAML files found in {path_str}")
                    continue
            else:
                print(f"Error: Invalid path: {path_str}", file=sys.stderr)
                all_valid = False
                continue

            for yaml_file in yaml_files:
                print(f"Validating: {yaml_file}")
                errors = validator.validate_yaml(str(yaml_file))

                if errors:
                    all_valid = False
                    print(f"  ❌ Validation failed:")
                    for error in errors:
                        print(f"    - {error}")
                else:
                    print(f"  ✓ Valid")

        if all_valid:
            print("\n✓ All YAML files are valid!")
            return 0
        else:
            print("\n❌ Some YAML files have validation errors.")
            return 1

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def validate_yaml(case_path: str) -> int:
    """Validate YAML file syntax.

    Args:
        case_path: Path to YAML file or directory

    Returns:
        Exit code (0 for valid, non-zero for invalid)
    """
    parser = V2YamlParser()

    path = Path(case_path)
    yaml_files = []

    if path.is_file():
        yaml_files = [path]
    elif path.is_dir():
        yaml_files = list(path.glob("**/*.yaml"))
    else:
        print(f"Error: Path not found: {case_path}", file=sys.stderr)
        return 1

    all_valid = True
    for yaml_file in yaml_files:
        print(f"Validating: {yaml_file}")
        errors = parser.validate_yaml(str(yaml_file))

        if errors:
            all_valid = False
            print(f"  ❌ Validation failed:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✓ Valid")

    return 0 if all_valid else 1


def execute_test_case(
    case_path: str, verbose: bool = False, profile: Optional[str] = None
) -> dict:
    """Execute test case and return results.

    Args:
        case_path: Path to YAML file
        verbose: Enable verbose output
        profile: Active profile name (overrides config)

    Returns:
        Execution result as dictionary
    """
    # Parse YAML
    parser = V2YamlParser()
    test_case = parser.parse(case_path)

    # Override profile if specified
    if profile and test_case.config:
        test_case.config.active_profile = profile

    # Check if data-driven testing is enabled
    if (
        test_case.config
        and test_case.config.data_iterations
        and test_case.config.data_source
    ):
        return _execute_data_driven_test(test_case, verbose)
    else:
        return _execute_single_test(test_case, verbose)


def _execute_data_driven_test(test_case, verbose: bool = False) -> dict:
    """Execute data-driven test case.

    Args:
        test_case: Test case with data source configuration
        verbose: Enable verbose output

    Returns:
        Aggregated execution results
    """
    # Create data-driven iterator
    iterator = DataDrivenIterator(
        test_case,
        test_case.config.data_source,
        test_case.config.variable_prefix,
    )

    print(f"Executing: {test_case.name} (Data-Driven)")
    print(f"Description: {test_case.description}")
    print(f"Data iterations: {len(iterator)}")
    print(f"Steps: {len(test_case.steps)}")
    print()

    # Execute for each data row
    all_results = []
    total_passed = 0
    total_failed = 0

    for i, (data_row, augmented_test_case) in enumerate(iterator):
        print(f"\n--- Data Iteration #{i + 1} ---")
        if verbose:
            print(f"Data: {data_row}")

        result = _execute_single_test(augmented_test_case, verbose)
        all_results.append(result)

        # Update statistics
        if result["test_case"]["status"] == "passed":
            total_passed += 1
        else:
            total_failed += 1

    # Aggregate results
    aggregated_result = {
        "test_case": {
            "name": test_case.name,
            "status": "passed" if total_failed == 0 else "failed",
            "total_iterations": len(iterator),
            "passed_iterations": total_passed,
            "failed_iterations": total_failed,
            "pass_rate": (total_passed / len(iterator) * 100) if len(iterator) > 0 else 0,
        },
        "iterations": all_results,
    }

    # Print summary
    print(f"\n{'='*60}")
    print(f"Data-Driven Test Summary")
    print(f"Total Iterations: {len(iterator)}")
    print(f"Passed: {total_passed} ✓")
    print(f"Failed: {total_failed} ✗")
    print(f"Pass Rate: {aggregated_result['test_case']['pass_rate']:.1f}%")
    print(f"{'='*60}")

    return aggregated_result


def _execute_single_test(test_case, verbose: bool = False) -> dict:
    """Execute single test case.

    Args:
        test_case: Test case to execute
        verbose: Enable verbose output

    Returns:
        Execution result as dictionary
    """
    # Print test case info
    print(f"Executing: {test_case.name}")
    print(f"Description: {test_case.description}")
    print(f"Steps: {len(test_case.steps)}")

    # Execute test case
    executor = TestCaseExecutor(test_case)
    result = executor.execute()

    # Print summary
    print(f"\n{'='*60}")
    print(f"Status: {result['test_case']['status'].upper()}")
    print(f"Duration: {result['test_case']['duration']:.2f}s")
    print(f"Statistics:")
    print(f"  Total:   {result['statistics']['total_steps']}")
    print(f"  Passed:  {result['statistics']['passed_steps']} ✓")
    print(f"  Failed:  {result['statistics']['failed_steps']} ✗")
    print(f"  Skipped: {result['statistics']['skipped_steps']} ⊘")
    print(f"Pass Rate: {result['statistics']['pass_rate']:.1f}%")
    print(f"{'='*60}")

    # Print step results if verbose
    if verbose:
        print(f"\nStep Details:")
        for step in result["steps"]:
            status_icon = {
                "success": "✓",
                "failure": "✗",
                "skipped": "⊘",
                "error": "⚠",
            }.get(step["status"], "?")

            print(f"\n  {status_icon} {step['name']}")
            print(f"     Status: {step['status']}")

            if step.get("performance"):
                perf = step["performance"]
                print(f"     Time: {perf['total_time']:.2f}ms")

            if step.get("response", {}).get("status_code"):
                print(f"     Status Code: {step['response']['status_code']}")

            if step.get("error_info"):
                print(f"     Error: {step['error_info']['message']}")

    return result


def save_result(result: dict, output_path: str) -> None:
    """Save result to JSON file.

    Args:
        result: Result dictionary
        output_path: Output file path
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
