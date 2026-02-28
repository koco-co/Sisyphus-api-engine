"""SQL 安全验证器"""

import re


class SQLValidator:
    """SQL 安全验证器"""

    DANGEROUS_PATTERNS: list[tuple[str, str]] = [
        (r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE)", "包含破坏性语句"),
        (r"--", "包含 SQL 注释符"),
        (r"/\*", "包含多行注释"),
        (r"\bor\s+1\s*=\s*1", "经典注入模式"),
        (r"\bunion\s+select", "UNION 注入"),
        (r"'.*or.*'.*'", "条件注入"),
        (r"exec\s*\(", "动态执行"),
    ]

    MAX_SQL_LENGTH = 10000

    def validate(self, sql: str) -> None:
        """验证 SQL 安全性"""
        from apirun.errors import DB_QUERY_ERROR, EngineError

        sql_upper = sql.upper()

        if len(sql) > self.MAX_SQL_LENGTH:
            raise EngineError(
                DB_QUERY_ERROR,
                "SQL 语句过长",
                detail=f"长度 {len(sql)} 超过限制 {self.MAX_SQL_LENGTH}",
            )

        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                raise EngineError(
                    DB_QUERY_ERROR,
                    f"SQL 安全检查失败: {description}",
                    detail=f"检测到模式: {pattern}",
                )
