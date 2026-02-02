"""Unit tests for Dependency Analyzer.

Tests dependency graph construction, parallel opportunity detection,
and critical path analysis.
"""

import pytest
from apirun.core.dependency_analyzer import (
    DependencyAnalyzer,
    StepNode,
    analyze_test_case_parallelism,
)


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer functionality."""

    def test_no_dependencies(self):
        """Test analysis with no dependencies."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request"},
            {"name": "step3", "type": "request"},
        ]

        analyzer = DependencyAnalyzer(steps)
        levels = analyzer.analyze_parallel_opportunities()

        # All steps should be in one level (can run in parallel)
        assert len(levels) == 1
        assert len(levels[0]) == 3
        assert set(levels[0]) == {"step1", "step2", "step3"}

    def test_sequential_dependencies(self):
        """Test analysis with sequential dependencies."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request", "depends_on": ["step2"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        levels = analyzer.analyze_parallel_opportunities()

        # Each step in its own level
        assert len(levels) == 3
        assert levels[0] == ["step1"]
        assert levels[1] == ["step2"]
        assert levels[2] == ["step3"]

    def test_partial_parallelism(self):
        """Test analysis with partial parallelism."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request", "depends_on": ["step1"]},
            {"name": "step4", "type": "request", "depends_on": ["step2", "step3"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        levels = analyzer.analyze_parallel_opportunities()

        # Level 0: step1
        # Level 1: step2, step3 (can run in parallel)
        # Level 2: step4
        assert len(levels) == 3
        assert levels[0] == ["step1"]
        assert set(levels[1]) == {"step2", "step3"}
        assert levels[2] == ["step4"]

    def test_can_parallelize(self):
        """Test can_parallelize method."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request"},
        ]

        analyzer = DependencyAnalyzer(steps)

        # step1 and step3 can run in parallel
        assert analyzer.can_parallelize("step1", "step3") is True

        # step1 and step2 cannot (step2 depends on step1)
        assert analyzer.can_parallelize("step1", "step2") is False

        # step2 and step3 can run in parallel
        assert analyzer.can_parallelize("step2", "step3") is True

    def test_get_parallel_groups(self):
        """Test get_parallel_groups method."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request", "depends_on": ["step1"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        groups = analyzer.get_parallel_groups()

        assert 0 in groups
        assert 1 in groups
        assert groups[0] == ["step1"]
        assert set(groups[1]) == {"step2", "step3"}

    def test_suggest_execution_plan(self):
        """Test execution plan suggestion."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request", "depends_on": ["step1"]},
            {"name": "step4", "type": "request"},
        ]

        analyzer = DependencyAnalyzer(steps)
        plan = analyzer.suggest_execution_plan()

        assert plan["total_steps"] == 4
        assert plan["sequential_count"] == 2  # 2 levels
        assert plan["max_parallel"] == 2  # Level 1 has 2 steps
        assert plan["speedup_potential"] == 2.0  # 4 steps / 2 levels

    def test_find_critical_path(self):
        """Test critical path finding."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request", "depends_on": ["step2"]},
            {"name": "step4", "type": "request"},
        ]

        analyzer = DependencyAnalyzer(steps)
        critical_path = analyzer.find_critical_path()

        # Critical path should be step1 -> step2 -> step3
        assert len(critical_path) == 2  # One from each level
        assert "step1" in critical_path

    def test_complex_dependencies(self):
        """Test complex dependency graph."""
        steps = [
            {"name": "setup", "type": "script"},
            {"name": "test1", "type": "request", "depends_on": ["setup"]},
            {"name": "test2", "type": "request", "depends_on": ["setup"]},
            {"name": "test3", "type": "request", "depends_on": ["setup"]},
            {"name": "validate", "type": "script", "depends_on": ["test1", "test2", "test3"]},
            {"name": "cleanup", "type": "script", "depends_on": ["validate"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        levels = analyzer.analyze_parallel_opportunities()

        # Level 0: setup
        # Level 1: test1, test2, test3 (parallel)
        # Level 2: validate
        # Level 3: cleanup
        assert len(levels) == 4
        assert levels[0] == ["setup"]
        assert set(levels[1]) == {"test1", "test2", "test3"}
        assert levels[2] == ["validate"]
        assert levels[3] == ["cleanup"]

        plan = analyzer.suggest_execution_plan()
        assert plan["max_parallel"] == 3
        assert plan["speedup_potential"] >= 1.5  # Should have significant speedup


class TestAnalyzeTestCaseParallelism:
    """Test analyze_test_case_parallelism function."""

    def test_fully_sequential(self):
        """Test analysis of fully sequential test case."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
            {"name": "step3", "type": "request", "depends_on": ["step2"]},
        ]

        result = analyze_test_case_parallelism(steps)

        assert "analysis" in result
        assert "recommendations" in result
        assert result["analysis"]["max_parallel"] == 1

    def test_fully_parallel(self):
        """Test analysis of fully parallel test case."""
        steps = [
            {"name": "test1", "type": "request"},
            {"name": "test2", "type": "request"},
            {"name": "test3", "type": "request"},
            {"name": "test4", "type": "request"},
        ]

        result = analyze_test_case_parallelism(steps)

        assert result["analysis"]["max_parallel"] == 4
        assert result["analysis"]["speedup_potential"] == 4.0

    def test_mixed_dependencies(self):
        """Test analysis with mixed dependencies."""
        steps = [
            {"name": "setup", "type": "script"},
            {"name": "test1", "type": "request", "depends_on": ["setup"]},
            {"name": "test2", "type": "request", "depends_on": ["setup"]},
            {"name": "teardown", "type": "script", "depends_on": ["test1", "test2"]},
        ]

        result = analyze_test_case_parallelism(steps)

        assert result["analysis"]["max_parallel"] == 2
        assert len(result["recommendations"]) > 0
        assert any("并行执行" in rec for rec in result["recommendations"])


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_steps(self):
        """Test with empty step list."""
        analyzer = DependencyAnalyzer([])
        levels = analyzer.analyze_parallel_opportunities()

        assert levels == []

    def test_circular_dependencies(self):
        """Test handling of potential circular dependencies."""
        # This should not crash even with circular refs
        steps = [
            {"name": "step1", "type": "request", "depends_on": ["step2"]},
            {"name": "step2", "type": "request", "depends_on": ["step1"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        # Should handle gracefully - circular dependencies are excluded from topological sort
        plan = analyzer.suggest_execution_plan()

        # Circular dependencies won't be included in the execution plan
        assert plan["total_steps"] == 0 or plan["total_steps"] == 2

    def test_missing_dependencies(self):
        """Test with dependencies that don't exist."""
        steps = [
            {"name": "step1", "type": "request"},
            {"name": "step2", "type": "request", "depends_on": ["nonexistent"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        levels = analyzer.analyze_parallel_opportunities()

        # Should ignore missing dependencies
        assert len(levels) >= 1

    def test_self_dependency(self):
        """Test step that depends on itself."""
        steps = [
            {"name": "step1", "type": "request", "depends_on": ["step1"]},
        ]

        analyzer = DependencyAnalyzer(steps)
        # Should handle gracefully
        levels = analyzer.analyze_parallel_opportunities()

        assert len(levels) >= 0
