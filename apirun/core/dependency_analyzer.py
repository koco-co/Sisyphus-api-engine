"""Dependency Analyzer for Sisyphus API Engine.

This module implements intelligent dependency analysis:
- Automatic dependency graph construction
- Parallel execution opportunity detection
- Critical path analysis
- Topological sorting for execution planning

Following Google Python Style Guide.
"""

from typing import List, Dict, Set, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class StepNode:
    """Represents a step in the dependency graph.

    Attributes:
        name: Step name
        depends_on: List of step names this step depends on
        can_parallel: Whether this step can run in parallel with others
        level: Topological level (steps in same level can run in parallel)
    """

    name: str
    depends_on: List[str]
    can_parallel: bool = False
    level: int = 0


class DependencyAnalyzer:
    """Analyzes step dependencies and identifies parallel execution opportunities.

    This analyzer:
    - Builds dependency graph from step definitions
    - Identifies independent steps that can run in parallel
    - Groups steps into execution levels (batches)
    - Provides execution ordering recommendations

    Attributes:
        steps: List of step definitions
        graph: Dependency graph (adjacency list)
    """

    def __init__(self, steps: List[Dict[str, Any]]):
        """Initialize DependencyAnalyzer.

        Args:
            steps: List of step definition dictionaries
        """
        self.steps = steps
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self._build_graph()

    def _build_graph(self) -> None:
        """Build dependency graph from step definitions."""
        step_names = {step.get("name", f"step_{i}") for i, step in enumerate(self.steps)}

        for step in self.steps:
            step_name = step.get("name", "")
            if not step_name:
                continue

            # Get dependencies
            depends_on = step.get("depends_on", [])
            if depends_on:
                for dep in depends_on:
                    if dep in step_names:
                        self.graph[dep].add(step_name)
                        self.reverse_graph[step_name].add(dep)

    def analyze_parallel_opportunities(self) -> List[List[str]]:
        """Identify opportunities for parallel execution.

        Returns:
            List of step batches, where steps in each batch can run in parallel.
            Steps are ordered by dependency (batches must execute in sequence).
        """
        # Calculate in-degree for each node
        in_degree = {step.get("name", ""): 0 for step in self.steps}
        for step_name in self.graph:
            for dependent in self.graph[step_name]:
                if dependent in in_degree:
                    in_degree[dependent] += 1

        # Initialize queue with nodes having zero in-degree
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        levels = []
        visited = set()

        while queue:
            current_level = []
            level_size = len(queue)

            # Process all nodes at current level
            for _ in range(level_size):
                if not queue:
                    break
                node = queue.popleft()
                if node not in visited:
                    current_level.append(node)
                    visited.add(node)

                    # Reduce in-degree for neighbors
                    for neighbor in self.graph.get(node, set()):
                        if neighbor in in_degree:
                            in_degree[neighbor] -= 1
                            if in_degree[neighbor] == 0:
                                queue.append(neighbor)

            if current_level:
                levels.append(current_level)

        return levels

    def get_parallel_groups(self) -> Dict[int, List[str]]:
        """Get groups of steps that can run in parallel.

        Returns:
            Dictionary mapping level number to list of step names.
            Steps in the same level can run in parallel.
        """
        levels = self.analyze_parallel_opportunities()
        return {i: steps for i, steps in enumerate(levels)}

    def can_parallelize(self, step1_name: str, step2_name: str) -> bool:
        """Check if two steps can run in parallel.

        Args:
            step1_name: First step name
            step2_name: Second step name

        Returns:
            True if steps can run in parallel (no dependency relationship)
        """
        # Check if step1 depends on step2
        if step2_name in self.reverse_graph.get(step1_name, set()):
            return False

        # Check if step2 depends on step1
        if step1_name in self.reverse_graph.get(step2_name, set()):
            return False

        # Check for common dependencies (transitive dependency)
        step1_ancestors = self._get_ancestors(step1_name)
        step2_ancestors = self._get_ancestors(step2_name)

        # If one is ancestor of the other, they can't run in parallel
        if step2_name in step1_ancestors or step1_name in step2_ancestors:
            return False

        return True

    def _get_ancestors(self, step_name: str) -> Set[str]:
        """Get all ancestors of a step (transitive dependencies).

        Args:
            step_name: Step name

        Returns:
            Set of ancestor step names
        """
        ancestors = set()
        queue = deque(self.reverse_graph.get(step_name, set()))

        while queue:
            node = queue.popleft()
            if node not in ancestors:
                ancestors.add(node)
                queue.extend(self.reverse_graph.get(node, set()) - ancestors)

        return ancestors

    def suggest_execution_plan(self) -> Dict[str, Any]:
        """Suggest an optimized execution plan.

        Returns:
            Dictionary containing:
            - parallel_levels: List of parallel execution levels
            - sequential_count: Number of sequential execution batches
            - max_parallel: Maximum parallelism achievable
            - speedup_potential: Theoretical speedup factor
        """
        levels = self.analyze_parallel_opportunities()
        total_steps = sum(len(level) for level in levels)
        max_parallel = max((len(level) for level in levels), default=0)

        # Calculate theoretical speedup (assuming perfect parallelization)
        if levels:
            # Speedup = total_steps / number of levels
            speedup = total_steps / len(levels)
        else:
            speedup = 1.0

        return {
            "parallel_levels": levels,
            "sequential_count": len(levels),
            "total_steps": total_steps,
            "max_parallel": max_parallel,
            "speedup_potential": round(speedup, 2),
        }

    def find_critical_path(self) -> List[str]:
        """Find the critical path (longest dependency chain).

        Returns:
            List of step names in critical path order
        """
        # Use topological sort with longest path algorithm
        levels = self.analyze_parallel_opportunities()

        # The critical path is formed by taking one step from each level
        # that has the most dependencies
        critical_path = []
        for level in levels:
            if level:
                # Choose the step with most ancestors in the next levels
                best_step = None
                max_descendants = 0

                for step in level:
                    descendants = self._count_descendants(step)
                    if descendants > max_descendants:
                        max_descendants = descendants
                        best_step = step

                if best_step:
                    critical_path.append(best_step)

        return critical_path

    def _count_descendants(self, step_name: str) -> int:
        """Count all descendants of a step.

        Args:
            step_name: Step name

        Returns:
            Number of descendant steps
        """
        descendants = set()
        queue = deque(self.graph.get(step_name, set()))

        while queue:
            node = queue.popleft()
            if node not in descendants:
                descendants.add(node)
                queue.extend(self.graph.get(node, set()) - descendants)

        return len(descendants)


def analyze_test_case_parallelism(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze parallelism opportunities in a test case.

    Args:
        steps: List of step definitions

    Returns:
        Analysis results with recommendations
    """
    analyzer = DependencyAnalyzer(steps)
    execution_plan = analyzer.suggest_execution_plan()

    return {
        "analysis": execution_plan,
        "recommendations": _generate_recommendations(execution_plan),
        "critical_path": analyzer.find_critical_path(),
    }


def _generate_recommendations(execution_plan: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations.

    Args:
        execution_plan: Execution plan from DependencyAnalyzer

    Returns:
        List of recommendation strings
    """
    recommendations = []

    if execution_plan["max_parallel"] <= 1:
        recommendations.append("⚠️  当前测试用例没有并行执行机会")
        recommendations.append("   建议: 检查步骤依赖关系，移除不必要的 depends_on")
    else:
        recommendations.append(f"✅ 最多可以 {execution_plan['max_parallel']} 个步骤并行执行")

        if execution_plan["speedup_potential"] > 1.5:
            recommendations.append(f"✅ 理论加速比: {execution_plan['speedup_potential']}x")
            recommendations.append("   建议: 将独立步骤配置为 concurrent 类型")

        if execution_plan["sequential_count"] < execution_plan["total_steps"]:
            recommendations.append(f"ℹ️  可将 {execution_plan['total_steps']} 个步骤压缩为 {execution_plan['sequential_count']} 批次")

    return recommendations
