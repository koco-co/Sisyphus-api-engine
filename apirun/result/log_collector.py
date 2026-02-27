"""日志收集器 — 场景/步骤生命周期日志（RUN-024～RUN-026）"""

from datetime import UTC, datetime

from apirun.result.models import LogEntry


class LogCollector:
    """收集执行日志，生成 LogEntry 列表（RUN-024、RUN-025）。"""

    def __init__(self, verbose: bool = False) -> None:
        self.entries: list[LogEntry] = []
        self._verbose = verbose

    def _ts(self) -> str:
        return datetime.now(UTC).isoformat()

    def info(self, message: str, step_index: int | None = None) -> None:
        self.entries.append(
            LogEntry(timestamp=self._ts(), level="INFO", message=message, step_index=step_index)
        )

    def debug(self, message: str, step_index: int | None = None) -> None:
        if self._verbose:
            self.entries.append(
                LogEntry(
                    timestamp=self._ts(), level="DEBUG", message=message, step_index=step_index
                )
            )

    def to_list(self) -> list[dict]:
        """转为可序列化的 list[dict]。"""
        return [e.model_dump() for e in self.entries]
