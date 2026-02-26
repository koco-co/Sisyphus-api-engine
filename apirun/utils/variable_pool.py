"""变量池管理器 — 分层变量池与 scope 支持（VAR-010、VAR-011）"""

from typing import Any

# 优先级从高到低：data_driven > extracted > scenario > environment > global_params
_LAYER_ORDER = ("data_driven", "extracted", "scenario", "environment", "global_params")


class VariablePool:
    """
    分层变量池（VAR-010）。
    查找顺序：data_driven > extracted > scenario > environment > global_params。
    scope=global 写入 extracted 层，scope=environment 写入 environment 层（VAR-011）。
    """

    __slots__ = ("_data_driven", "_extracted", "_scenario", "_environment", "_global_params")

    def __init__(self) -> None:
        self._data_driven: dict[str, Any] = {}
        self._extracted: dict[str, Any] = {}
        self._scenario: dict[str, Any] = {}
        self._environment: dict[str, Any] = {}
        self._global_params: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        """按优先级查找，先找到先返回。"""
        for layer_name in _LAYER_ORDER:
            layer = getattr(self, f"_{layer_name}")
            if key in layer:
                return layer[key]
        raise KeyError(key)

    def get_or_none(self, key: str) -> Any:
        """按优先级查找，不存在返回 None。"""
        try:
            return self.get(key)
        except KeyError:
            return None

    def set(self, key: str, value: Any, scope: str = "global") -> None:
        """
        按 scope 写入对应层（VAR-011）。
        - scope=global → 写入 extracted 层（全局可见）
        - scope=environment → 写入 environment 层
        """
        if scope == "environment":
            self._environment[key] = value
        else:
            self._extracted[key] = value

    def set_scenario(self, variables: dict[str, Any] | None) -> None:
        """初始化/覆盖 scenario 层（config.variables）。"""
        self._scenario = dict(variables or {})

    def set_environment(self, variables: dict[str, Any] | None) -> None:
        """初始化/覆盖 environment 层（config.environment.variables）。"""
        self._environment = dict(variables or {})

    def set_data_driven(self, variables: dict[str, Any] | None) -> None:
        """注入数据驱动变量（单轮参数），优先级最高。"""
        self._data_driven = dict(variables or {})

    def set_global_params(self, variables: dict[str, Any] | None) -> None:
        """初始化 global_params 层，优先级最低。"""
        self._global_params = dict(variables or {})

    def as_dict(self) -> dict[str, Any]:
        """合并为单字典，供 render_template 使用；高优先级覆盖低优先级。"""
        out: dict[str, Any] = {}
        for layer_name in reversed(_LAYER_ORDER):
            layer = getattr(self, f"_{layer_name}")
            out.update(layer)
        return out

    def snapshot(self) -> dict[str, Any]:
        """当前可见变量快照（与 as_dict 一致），用于结果输出。"""
        return self.as_dict()
