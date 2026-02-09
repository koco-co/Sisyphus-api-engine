"""Performance Benchmark Suite for Sisyphus API Engine.

This module provides performance benchmarking tools to measure
and track performance improvements across the codebase.

Performance Targets:
- Single API request: < 500ms
- 100 steps test case: < 30s
- Concurrent execution (10 threads): Stable
- Memory usage: < 200MB

Following Google Python Style Guide.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import time
import tracemalloc
from typing import Any


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run.

    Attributes:
        name: Benchmark name
        iterations: Number of iterations
        total_time: Total execution time (seconds)
        avg_time: Average time per iteration (seconds)
        min_time: Minimum time per iteration (seconds)
        max_time: Maximum time per iteration (seconds)
        memory_used: Memory used in MB
        timestamp: When benchmark was run
    """

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    memory_used: float
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'iterations': self.iterations,
            'total_time': f'{self.total_time:.4f}s',
            'avg_time': f'{self.avg_time:.4f}s',
            'min_time': f'{self.min_time:.4f}s',
            'max_time': f'{self.max_time:.4f}s',
            'memory_used': f'{self.memory_used:.2f}MB',
            'timestamp': self.timestamp.isoformat(),
        }


class Benchmark:
    """Performance benchmark runner.

    This class provides methods to run performance benchmarks
    and measure execution time, memory usage, etc.
    """

    def __init__(self):
        """Initialize Benchmark runner."""
        self.results: list[BenchmarkResult] = []

    def run(
        self, name: str, func: Callable, iterations: int = 100, *args, **kwargs
    ) -> BenchmarkResult:
        """Run a benchmark.

        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of iterations
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            BenchmarkResult object
        """
        # Start memory tracking
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        # Warm-up run (not counted)
        try:
            func(*args, **kwargs)
        except Exception:
            pass

        # Benchmark runs
        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception:
                pass
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Stop memory tracking
        end_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        # Calculate statistics
        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)
        memory_used = (end_memory - start_memory) / (1024 * 1024)  # Convert to MB

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            memory_used=memory_used,
            timestamp=datetime.now(),
        )

        self.results.append(result)
        return result

    def print_results(self) -> None:
        """Print all benchmark results."""
        print('\n' + '=' * 80)
        print('PERFORMANCE BENCHMARK RESULTS')
        print('=' * 80)

        for result in self.results:
            print(f'\n{result.name}:')
            print(f'  Iterations:     {result.iterations}')
            print(f'  Total Time:     {result.total_time:.4f}s')
            print(f'  Average Time:   {result.avg_time:.4f}s')
            print(f'  Min Time:       {result.min_time:.4f}s')
            print(f'  Max Time:       {result.max_time:.4f}s')
            print(f'  Memory Used:    {result.memory_used:.2f}MB')
            print(f'  Timestamp:      {result.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')

        print('\n' + '=' * 80)

    def check_targets(self) -> dict[str, bool]:
        """Check if benchmarks meet performance targets.

        Returns:
            Dictionary mapping target names to whether they passed
        """
        targets = {}

        for result in self.results:
            if 'variable_render' in result.name:
                targets[f'{result.name}_<5ms'] = result.avg_time < 0.005
            elif 'json_parse' in result.name:
                targets[f'{result.name}_<10ms'] = result.avg_time < 0.010
            elif 'validation' in result.name:
                targets[f'{result.name}_<50ms'] = result.avg_time < 0.050
            elif 'memory' in result.name:
                targets[f'{result.name}_<200MB'] = result.memory_used < 200

        return targets


def benchmark_variable_rendering():
    """Benchmark variable rendering performance."""
    from apirun.core.variable_manager import VariableManager

    print('\n🔍 Benchmarking: Variable Rendering')

    benchmark = Benchmark()

    # Test 1: Simple variable rendering
    vm = VariableManager()
    vm.set_variable('user_id', 12345)

    def simple_render():
        vm.render_string('${user_id}')

    result1 = benchmark.run('simple_variable_render', simple_render, iterations=1000)

    # Test 2: Complex template rendering
    vm.set_variable('base_url', 'https://api.example.com')
    vm.set_variable('api_key', 'secret_key_12345')
    vm.set_variable('timeout', 30)

    def complex_render():
        vm.render_string(
            '${base_url}/users/${user_id}?key=${api_key}&timeout=${timeout}'
        )

    result2 = benchmark.run('complex_template_render', complex_render, iterations=1000)

    # Test 3: Nested variable rendering
    vm.set_variable('config', {'api': {'v2': {'endpoint': '/v2/users'}}})

    def nested_render():
        vm.render_string('${config.api.v2.endpoint}/${user_id}')

    result3 = benchmark.run('nested_variable_render', nested_render, iterations=1000)

    return benchmark


def benchmark_json_operations():
    """Benchmark JSON parsing and serialization."""
    import json

    print('\n🔍 Benchmarking: JSON Operations')

    benchmark = Benchmark()

    # Test data
    large_dict = {
        'users': [
            {
                'id': i,
                'name': f'User{i}',
                'email': f'user{i}@example.com',
                'data': {'key1': 'value1', 'key2': 'value2'},
            }
            for i in range(100)
        ]
    }
    json_str = json.dumps(large_dict)

    # Test 1: JSON parsing
    def json_parse():
        json.loads(json_str)

    result1 = benchmark.run('json_parse_100_users', json_parse, iterations=1000)

    # Test 2: JSON serialization
    def json_serialize():
        json.dumps(large_dict)

    result2 = benchmark.run('json_serialize_100_users', json_serialize, iterations=1000)

    # Test 3: JSONPath extraction
    from jsonpath import jsonpath

    def jsonpath_extract():
        jsonpath(large_dict, '$.users[0].name')

    result3 = benchmark.run('jsonpath_extraction', jsonpath_extract, iterations=1000)

    return benchmark


def benchmark_validation():
    """Benchmark validation engine performance."""
    from apirun.validation.engine import ValidationEngine

    print('\n🔍 Benchmarking: Validation Engine')

    benchmark = Benchmark()
    engine = ValidationEngine()

    # Test data
    response_data = {
        'status_code': 200,
        'body': {
            'code': 0,
            'message': 'success',
            'data': {
                'user_id': 12345,
                'username': 'testuser',
                'email': 'test@example.com',
            },
        },
    }

    # Test 1: Single validation
    validations = [{'type': 'eq', 'path': '$.status_code', 'expect': 200}]

    def single_validation():
        engine.validate(validations, response_data)

    result1 = benchmark.run('single_validation', single_validation, iterations=1000)

    # Test 2: Multiple validations
    validations = [
        {'type': 'eq', 'path': '$.status_code', 'expect': 200},
        {'type': 'eq', 'path': '$.body.code', 'expect': 0},
        {'type': 'eq', 'path': '$.body.data.user_id', 'expect': 12345},
        {
            'type': 'regex',
            'path': '$.body.data.email',
            'expect': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        },
    ]

    def multiple_validations():
        engine.validate(validations, response_data)

    result2 = benchmark.run(
        'multiple_validations', multiple_validations, iterations=1000
    )

    # Test 3: Complex nested validation
    validations = [
        {'type': 'eq', 'path': '$.body.data.username', 'expect': 'testuser'},
        {'type': 'type', 'path': '$.body.data.user_id', 'expect': 'int'},
        {'type': 'exists', 'path': '$.body.data.email', 'expect': True},
    ]

    def complex_validation():
        engine.validate(validations, response_data)

    result3 = benchmark.run('complex_validation', complex_validation, iterations=1000)

    return benchmark


def benchmark_memory_usage():
    """Benchmark memory usage patterns."""
    from apirun.core.variable_manager import VariableManager

    print('\n🔍 Benchmarking: Memory Usage')

    benchmark = Benchmark()

    # Test 1: Creating many variables
    def create_many_variables():
        vm = VariableManager()
        for i in range(1000):
            vm.set_variable(f'var_{i}', f'value_{i}' * 100)

    result1 = benchmark.run(
        'create_1000_variables', create_many_variables, iterations=10
    )

    # Test 2: Variable snapshots
    vm = VariableManager()
    for i in range(100):
        vm.set_variable(f'var_{i}', f'value_{i}' * 100)

    def take_snapshot():
        vm.snapshot()

    result2 = benchmark.run('variable_snapshot_100_vars', take_snapshot, iterations=100)

    return benchmark


def run_all_benchmarks() -> dict[str, dict[str, bool]]:
    """Run all performance benchmarks.

    Returns:
        Dictionary mapping benchmark names to target results
    """
    print('\n' + '=' * 80)
    print('SISYPHUS API ENGINE - PERFORMANCE BENCHMARK SUITE')
    print('=' * 80)

    all_targets = {}

    # Variable rendering benchmarks
    vm_benchmark = benchmark_variable_rendering()
    vm_benchmark.print_results()
    all_targets.update(vm_benchmark.check_targets())

    # JSON operation benchmarks
    json_benchmark = benchmark_json_operations()
    json_benchmark.print_results()
    all_targets.update(json_benchmark.check_targets())

    # Validation benchmarks
    val_benchmark = benchmark_validation()
    val_benchmark.print_results()
    all_targets.update(val_benchmark.check_targets())

    # Memory usage benchmarks
    mem_benchmark = benchmark_memory_usage()
    mem_benchmark.print_results()
    all_targets.update(mem_benchmark.check_targets())

    # Print summary
    print('\n' + '=' * 80)
    print('PERFORMANCE TARGETS SUMMARY')
    print('=' * 80)

    for target, passed in all_targets.items():
        status = '✓ PASS' if passed else '✗ FAIL'
        print(f'{status}: {target}')

    print('\n' + '=' * 80)

    return all_targets


if __name__ == '__main__':
    run_all_benchmarks()
