"""大小限制器"""


from apirun.errors import ENGINE_INTERNAL_ERROR, EngineError


class SizeLimiter:
    """资源大小限制器"""

    MAX_RESPONSE_SIZE = 10 * 1024 * 1024
    MAX_CSV_SIZE = 10 * 1024 * 1024
    MAX_CSV_ROWS = 10000

    def limit_response(self, response: dict, max_size: int | None = None) -> dict:
        """限制响应体大小"""
        max_size = max_size or self.MAX_RESPONSE_SIZE

        headers = response.get("headers", {})
        content_length = headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > max_size:
                    import logging

                    logging.warning(f"响应体过大: {size} 字节")
                    return {
                        **response,
                        "body": f"<响应体过大 ({size} 字节，已截断)>",
                        "truncated": True,
                    }
            except (ValueError, TypeError):
                pass

        return response

    def check_csv_rows(self, rows: list, max_rows: int | None = None) -> None:
        """检查 CSV 行数"""
        max_rows = max_rows or self.MAX_CSV_ROWS

        if len(rows) > max_rows:
            raise EngineError(
                ENGINE_INTERNAL_ERROR,
                f"CSV 行数过多: {len(rows)} 行，超过限制 {max_rows} 行",
            )
