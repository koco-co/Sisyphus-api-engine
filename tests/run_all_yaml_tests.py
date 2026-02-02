#!/usr/bin/env python
"""Test runner for all YAML test cases.

This script runs all YAML test cases in the examples directory
and generates a comprehensive test report.

Following Google Python Style Guide.
"""

import os
import subprocess
import sys
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# 获取脚本所在目录的绝对路径
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent


class TestCaseRunner:
    """Runner for YAML test cases.

    Attributes:
        examples_dir: Directory containing YAML test cases
        results: List of test results
    """

    def __init__(self, examples_dir: str = None):
        """Initialize TestCaseRunner.

        Args:
            examples_dir: Directory containing YAML test cases (relative to project root)
        """
        if examples_dir is None:
            # 默认使用项目根目录下的 examples 目录
            self.examples_dir = PROJECT_ROOT / "examples"
        else:
            # 如果是相对路径，基于项目根目录解析
            examples_path = Path(examples_dir)
            if examples_path.is_absolute():
                self.examples_dir = examples_path
            else:
                self.examples_dir = PROJECT_ROOT / examples_path

        self.results: List[Dict[str, Any]] = []

    def get_test_cases(self) -> List[Path]:
        """Get all YAML test case files.

        Returns:
            List of YAML file paths
        """
        if not self.examples_dir.exists():
            raise FileNotFoundError(f"Examples directory not found: {self.examples_dir}")

        yaml_files = sorted(self.examples_dir.glob("*.yaml"))
        return yaml_files

    def run_test_case(self, yaml_file: Path) -> Dict[str, Any]:
        """Run a single YAML test case.

        Args:
            yaml_file: Path to YAML test case file

        Returns:
            Test result dictionary
        """
        print(f"\n{'='*80}")
        print(f"Running: {yaml_file.name}")
        print(f"{'='*80}")

        result = {
            "name": yaml_file.stem,
            "file": str(yaml_file),
            "status": "unknown",
            "duration": 0,
            "output": "",
            "error": None,
        }

        start_time = datetime.now()

        try:
            # Run sisyphus command
            cmd = ["sisyphus", "--cases", str(yaml_file)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output, _ = process.communicate(timeout=120)  # 2分钟超时
            end_time = datetime.now()

            result["duration"] = (end_time - start_time).total_seconds()
            result["output"] = output

            # Check exit code
            if process.returncode == 0:
                # Parse output to determine if tests passed
                if "✓" in output or "PASS" in output or "passed" in output.lower():
                    # Extract statistics
                    lines = output.split('\n')
                    for line in lines:
                        if "Pass Rate:" in line:
                            result["status"] = "passed"
                            break
                        if "Status:" in line and "PASSED" in line.upper():
                            result["status"] = "passed"
                            break

                    if result["status"] == "unknown":
                        result["status"] = "passed"  # Assume passed if exit code is 0
                else:
                    result["status"] = "failed"
            else:
                result["status"] = "error"

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = "Test execution exceeded timeout (120s)"
            result["duration"] = (datetime.now() - start_time).total_seconds()

        except Exception as e:
            result["status"] = "exception"
            result["error"] = str(e)
            result["duration"] = (datetime.now() - start_time).total_seconds()

        # Print summary
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "error": "⚠️",
            "timeout": "⏰",
            "exception": "💥",
            "unknown": "❓"
        }.get(result["status"], "❓")

        print(f"\n{status_emoji} Status: {result['status'].upper()}")
        print(f"⏱️  Duration: {result['duration']:.2f}s")

        if result["error"]:
            print(f"❌ Error: {result['error']}")

        return result

    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all YAML test cases.

        Returns:
            List of test results
        """
        yaml_files = self.get_test_cases()

        print(f"\n{'='*80}")
        print(f"SISYPHUS API ENGINE - YAML TEST CASES RUNNER")
        print(f"{'='*80}")
        print(f"Found {len(yaml_files)} test cases")
        print(f"Starting execution...\n")

        for yaml_file in yaml_files:
            result = self.run_test_case(yaml_file)
            self.results.append(result)

        return self.results

    def generate_report(self) -> str:
        """Generate test report.

        Returns:
            Formatted test report string
        """
        if not self.results:
            return "No test results available."

        # Calculate statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] in ("failed", "error", "timeout", "exception"))
        pass_rate = (passed / total * 100) if total > 0 else 0

        total_duration = sum(r["duration"] for r in self.results)

        # Build report
        report = []
        report.append("\n" + "="*80)
        report.append("TEST EXECUTION SUMMARY")
        report.append("="*80)
        report.append(f"\nTotal Test Cases: {total}")
        report.append(f"Passed: {passed} ✅")
        report.append(f"Failed: {failed} ❌")
        report.append(f"Pass Rate: {pass_rate:.1f}%")
        report.append(f"Total Duration: {total_duration:.2f}s")
        report.append(f"Average Duration: {total_duration/total:.2f}s")

        # Detailed results
        report.append("\n" + "="*80)
        report.append("DETAILED RESULTS")
        report.append("="*80)

        for result in sorted(self.results, key=lambda x: x["name"]):
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "error": "⚠️",
                "timeout": "⏰",
                "exception": "💥",
                "unknown": "❓"
            }.get(result["status"], "❓")

            report.append(f"\n{status_emoji} {result['name']}")
            report.append(f"   File: {result['file']}")
            report.append(f"   Status: {result['status'].upper()}")
            report.append(f"   Duration: {result['duration']:.2f}s")

            if result["error"]:
                report.append(f"   Error: {result['error']}")

        # Failed tests details
        failed_results = [r for r in self.results if r["status"] != "passed"]
        if failed_results:
            report.append("\n" + "="*80)
            report.append("FAILED TESTS DETAILS")
            report.append("="*80)

            for result in failed_results:
                report.append(f"\n❌ {result['name']}")
                report.append(f"   Status: {result['status'].upper()}")
                if result["error"]:
                    report.append(f"   Error: {result['error']}")

                # Show last few lines of output
                if result["output"]:
                    output_lines = result["output"].split('\n')
                    report.append("   Last output:")
                    for line in output_lines[-10:]:
                        if line.strip():
                            report.append(f"     {line}")

        report.append("\n" + "="*80)

        return "\n".join(report)

    def save_report(self, filename: str = "test_results.yaml.txt") -> None:
        """Save test report to file.

        Args:
            filename: Output filename
        """
        report = self.generate_report()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 Test report saved to: {filename}")


def main():
    """Main entry point."""
    runner = TestCaseRunner()

    try:
        # Run all tests
        runner.run_all_tests()

        # Generate and print report
        print(runner.generate_report())

        # Save report
        runner.save_report()

        # Exit with appropriate code
        failed_count = sum(1 for r in runner.results if r["status"] != "passed")
        if failed_count > 0:
            print(f"\n⚠️  {failed_count} test(s) failed")
            sys.exit(1)
        else:
            print(f"\n✅ All tests passed!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
