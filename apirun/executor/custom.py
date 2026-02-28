"""自定义关键字执行器 — 按 keyword_name 查找并执行，返回 custom_detail（CST-001～CST-007）"""

import threading
import time
from typing import Any

from apirun.core.models import CustomParams
from apirun.errors import KEYWORD_EXECUTION_ERROR, KEYWORD_NOT_FOUND, EngineError
from apirun.result.models import CustomDetail

# 关键字注册表：keyword_name -> Keyword 子类
KEYWORD_REGISTRY: dict[str, type] = {}

# 线程锁，保护关键字注册表的并发访问
_REGISTRY_LOCK = threading.RLock()


def register_keyword(cls: type) -> type:
    """注册 Keyword 子类，以其 name 为 key（线程安全）。"""
    name = getattr(cls, "name", None)
    if name:
        with _REGISTRY_LOCK:
            KEYWORD_REGISTRY[name] = cls
    return cls


def execute_custom_step(
    keyword_name: str,
    params: CustomParams,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    执行自定义关键字步骤（CST-001～CST-007）。
    返回: custom_detail (dict), return_value (any), error (dict|None), extract 用 return_value 作为 body 源。
    """
    variables = variables or {}
    parameters = params.parameters or {}
    from apirun.utils.variables import render_template

    parameters_rendered = {k: render_template(v, variables) for k, v in parameters.items()}
    start = time.perf_counter()
    try:
        with _REGISTRY_LOCK:
            klass = KEYWORD_REGISTRY.get(keyword_name)
        if klass is None:
            raise EngineError(KEYWORD_NOT_FOUND, f"关键字未找到: {keyword_name}")
        instance = klass()
        return_value = instance.execute(**parameters_rendered)
    except EngineError:
        raise
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "custom_detail": CustomDetail(
                keyword_name=keyword_name,
                parameters_input=parameters_rendered,
                return_value=None,
                execution_time=elapsed_ms,
            ).model_dump(),
            "return_value": None,
            "error": {"code": KEYWORD_EXECUTION_ERROR, "message": str(e), "detail": None},
        }
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {
        "custom_detail": CustomDetail(
            keyword_name=keyword_name,
            parameters_input=parameters_rendered,
            return_value=return_value,
            execution_time=elapsed_ms,
        ).model_dump(),
        "return_value": return_value,
        "error": None,
    }


def execute_custom_step_safe(
    keyword_name: str,
    params: CustomParams,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """执行自定义步骤，捕获 EngineError 返回 error 字典。"""
    try:
        return execute_custom_step(keyword_name, params, variables)
    except EngineError as e:
        return {
            "custom_detail": None,
            "return_value": None,
            "error": e.to_dict(),
        }
