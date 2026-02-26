"""自定义关键字基类 - 供平台生成的关键字代码继承"""

from typing import Any


class Keyword:
    """自定义关键字基类。

    平台生成的关键字 Python 文件通过继承此类实现 execute()，
    由引擎在 custom 步骤中调用。
    """

    name: str = ""

    def execute(self, **kwargs: Any) -> Any:
        """执行关键字逻辑。子类重写此方法。

        Args:
            **kwargs: 步骤 parameters 传入的键值对

        Returns:
            任意可序列化结果，供后续 extract 或断言使用
        """
        raise NotImplementedError("Subclass must implement execute()")
