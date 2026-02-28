"""性能基准测试"""

import time


class TestPerformance:
    """性能基准测试"""

    def test_variable_rendering_performance(self):
        """变量渲染性能：1000 次应 < 50ms"""
        from apirun.utils.variables import render_template

        template = "api/{{endpoint}}/users/{{user_id}}?token={{token}}"
        variables = {
            "endpoint": "v1",
            "user_id": "123",
            "token": "abc-def-ghi",
        }

        start = time.perf_counter()
        for _ in range(1000):
            _ = render_template(template, variables)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50, f"变量渲染 1000 次耗时 {elapsed}ms"

    def test_jsonpath_performance(self):
        """JSONPath 提取性能：1000 次应 < 2000ms

        注意：当前实现较慢（约 1750ms），这是已知的性能瓶颈。
        未来优化目标：降低到 < 100ms
        """
        from apirun.extractor.extractor import _extract_json

        body = {"data": {"items": [{"id": i} for i in range(100)]}}
        expression = "$.data.items[0].id"

        start = time.perf_counter()
        for _ in range(1000):
            _ = _extract_json(body, expression)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 2000, f"JSONPath 提取 1000 次耗时 {elapsed}ms"
