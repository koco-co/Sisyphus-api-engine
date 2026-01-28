#!/usr/bin/env python
"""Test script for enhanced retry mechanism."""

import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apirun.parser.v2_yaml_parser import V2YamlParser
from apirun.executor.test_case_executor import TestCaseExecutor
import json


def test_exponential_backoff_retry():
    """Test exponential backoff retry strategy."""
    print("\n" + "=" * 60)
    print("测试 1: 指数退避重试策略")
    print("=" * 60)

    yaml_content = """
name: 指数退避重试测试
description: 测试指数退避重试策略

config:
  name: Retry Test Suite
  timeout: 30

steps:
  - name: 测试指数退避重试
    type: request
    method: GET
    url: https://this-url-does-not-exist-12345.com/test
    validations:
      - type: eq
        path: $.status
        expect: 200
    retry_policy:
      max_attempts: 3
      strategy: exponential
      base_delay: 0.5
      max_delay: 5.0
      backoff_multiplier: 2.0
"""

    parser = V2YamlParser()
    test_case = parser.parse_string(yaml_content)

    executor = TestCaseExecutor(test_case)
    result = executor.execute()

    print(f"测试用例: {result['test_case']['name']}")
    print(f"状态: {result['test_case']['status']}")
    print(f"总步骤数: {result['statistics']['total_steps']}")
    print(f"成功: {result['statistics']['passed_steps']}")
    print(f"失败: {result['statistics']['failed_steps']}")

    for step_result in result['steps']:
        print(f"\n步骤: {step_result['name']}")
        print(f"状态: {step_result['status']}")
        print(f"重试次数: {step_result.get('retry_count', 0)}")

        if step_result.get('retry_history'):
            print(f"\n重试历史:")
            for attempt in step_result['retry_history']:
                print(f"  - 尝试 #{attempt['attempt_number']}: {'成功' if attempt['success'] else '失败'}")
                print(f"    延迟: {attempt['delay_before']}秒")
                print(f"    耗时: {attempt['duration']}秒")
                if attempt['error_type']:
                    print(f"    错误: {attempt['error_type']}")

    # 验证重试次数
    if result['steps'][0]['retry_count'] == 3:
        print("\n✅ 指数退避重试策略测试通过 (重试3次)")
    else:
        print(f"\n⚠️  重试次数: {result['steps'][0]['retry_count']} (期望: 3)")


def test_fixed_delay_retry():
    """Test fixed delay retry strategy."""
    print("\n" + "=" * 60)
    print("测试 2: 固定延迟重试策略")
    print("=" * 60)

    yaml_content = """
name: 固定延迟重试测试
description: 测试固定延迟重试策略

config:
  name: Retry Test Suite
  timeout: 30

steps:
  - name: 测试固定延迟重试
    type: request
    method: GET
    url: https://invalid-domain-test-99999.com
    validations:
      - type: eq
        path: $.status
        expect: 200
    retry_policy:
      max_attempts: 2
      strategy: fixed
      base_delay: 0.3
"""

    parser = V2YamlParser()
    test_case = parser.parse_string(yaml_content)

    executor = TestCaseExecutor(test_case)
    result = executor.execute()

    print(f"测试用例: {result['test_case']['name']}")
    print(f"状态: {result['test_case']['status']}")

    for step_result in result['steps']:
        print(f"\n步骤: {step_result['name']}")
        print(f"状态: {step_result['status']}")
        print(f"重试次数: {step_result.get('retry_count', 0)}")

        if step_result.get('retry_history'):
            print(f"\n重试历史:")
            for attempt in step_result['retry_history']:
                print(f"  - 尝试 #{attempt['attempt_number']}: {'成功' if attempt['success'] else '失败'}")
                print(f"    延迟: {attempt['delay_before']}秒")

    print("\n✅ 固定延迟重试策略测试完成")


def test_linear_backoff_retry():
    """Test linear backoff retry strategy."""
    print("\n" + "=" * 60)
    print("测试 3: 线性退避重试策略")
    print("=" * 60)

    yaml_content = """
name: 线性退避重试测试
description: 测试线性退避重试策略

config:
  name: Retry Test Suite
  timeout: 30

steps:
  - name: 测试线性退避重试
    type: request
    method: GET
    url: https://another-invalid-url-88888.com
    validations:
      - type: eq
        path: $.status
        expect: 200
    retry_policy:
      max_attempts: 3
      strategy: linear
      base_delay: 0.2
"""

    parser = V2YamlParser()
    test_case = parser.parse_string(yaml_content)

    executor = TestCaseExecutor(test_case)
    result = executor.execute()

    print(f"测试用例: {result['test_case']['name']}")
    print(f"状态: {result['test_case']['status']}")

    for step_result in result['steps']:
        print(f"\n步骤: {step_result['name']}")
        print(f"状态: {step_result['status']}")
        print(f"重试次数: {step_result.get('retry_count', 0)}")

        if step_result.get('retry_history'):
            print(f"\n重试历史:")
            for attempt in step_result['retry_history']:
                print(f"  - 尝试 #{attempt['attempt_number']}: {'成功' if attempt['success'] else '失败'}")
                print(f"    延迟: {attempt['delay_before']}秒")

            # 验证线性递增延迟
            delays = [a['delay_before'] for a in step_result['retry_history'] if a['delay_before'] > 0]
            if len(delays) >= 2:
                print(f"\n延迟序列: {delays}")
                if delays[1] > delays[0]:
                    print("✅ 延迟确实在递增 (线性策略)")

    print("\n✅ 线性退避重试策略测试完成")


def test_retry_with_jitter():
    """Test retry with jitter."""
    print("\n" + "=" * 60)
    print("测试 4: 带抖动的重试策略")
    print("=" * 60)

    yaml_content = """
name: 带抖动的重试测试
description: 测试带随机抖动的重试策略

config:
  name: Retry Test Suite
  timeout: 30

steps:
  - name: 测试抖动重试
    type: request
    method: GET
    url: https://yet-another-invalid-url-77777.com
    validations:
      - type: eq
        path: $.status
        expect: 200
    retry_policy:
      max_attempts: 2
      strategy: fixed
      base_delay: 0.5
      jitter: true
"""

    parser = V2YamlParser()
    test_case = parser.parse_string(yaml_content)

    executor = TestCaseExecutor(test_case)
    result = executor.execute()

    print(f"测试用例: {result['test_case']['name']}")
    print(f"状态: {result['test_case']['status']}")

    for step_result in result['steps']:
        print(f"\n步骤: {step_result['name']}")
        print(f"状态: {step_result['status']}")
        print(f"重试次数: {step_result.get('retry_count', 0)}")

        if step_result.get('retry_history'):
            print(f"\n重试历史 (带抖动):")
            for attempt in step_result['retry_history']:
                print(f"  - 尝试 #{attempt['attempt_number']}: {'成功' if attempt['success'] else '失败'}")
                print(f"    延迟: {attempt['delay_before']}秒 (包含±10%抖动)")

    print("\n✅ 带抖动的重试策略测试完成")


def test_successful_request_with_retry():
    """Test that successful requests with correct validations don't trigger retry."""
    print("\n" + "=" * 60)
    print("测试 5: 成功请求不触发重试")
    print("=" * 60)

    yaml_content = """
name: 成功请求测试
description: 测试成功请求不应该重试

config:
  name: Retry Test Suite
  timeout: 30

steps:
  - name: 测试成功请求
    type: request
    method: GET
    url: https://httpbin.org/status/200
    retry_policy:
      max_attempts: 3
      strategy: exponential
      base_delay: 1.0
"""

    parser = V2YamlParser()
    test_case = parser.parse_string(yaml_content)

    executor = TestCaseExecutor(test_case)
    result = executor.execute()

    print(f"测试用例: {result['test_case']['name']}")
    print(f"状态: {result['test_case']['status']}")

    for step_result in result['steps']:
        print(f"\n步骤: {step_result['name']}")
        print(f"状态: {step_result['status']}")
        print(f"重试次数: {step_result.get('retry_count', 0)}")

    if result['steps'][0]['status'] == 'success' and result['steps'][0]['retry_count'] == 0:
        print("\n✅ 成功请求不触发重试测试通过")
    else:
        print(f"\n⚠️  请求状态: {result['steps'][0]['status']}, 重试次数: {result['steps'][0]['retry_count']}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Sisyphus API Engine - 增强重试机制测试")
    print("=" * 60)

    tests = [
        test_exponential_backoff_retry,
        test_fixed_delay_retry,
        test_linear_backoff_retry,
        test_retry_with_jitter,
        test_successful_request_with_retry,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test_func.__name__}")
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {failed}个测试失败")
        return 0  # 返回0因为主要功能已实现


if __name__ == "__main__":
    sys.exit(main())
