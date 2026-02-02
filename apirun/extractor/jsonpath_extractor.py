"""JSONPath Extractor for Sisyphus API Engine.

This module implements variable extraction using JSONPath with function support.
Following Google Python Style Guide.
"""

from typing import Any
from apirun.utils.enhanced_jsonpath import extract_value


class JSONPathExtractor:
    """Extract values from data using JSONPath expressions.

    Supports:
    - Root node: $
    - Child node: $.key
    - Nested node: $.parent.child
    - Wildcard: $.*
    - Array index: $.array[0]
    - Array slice: $.array[0:2]
    - Recursive search: $..key
    - Filter expressions: $.array[?(@.key > 10)]

    Enhanced Functions:
    - length(), size(), count(): Get array length
    - sum(): Sum of numeric values
    - avg(): Average of numeric values
    - min(), max(): Min/Max values
    - first(), last(): First/Last elements
    - keys(), values(): Object keys/values
    - reverse(), sort(), unique(): Array operations
    - flatten(): Flatten nested arrays
    - upper(), lower(), trim(): String operations
    - split(delimiter), join(delimiter): String operations
    - contains(value), starts_with(value), ends_with(value): Checks
    - matches(pattern): Regex match
    """

    def extract(self, path: str, data: Any, index: int = 0, default: Any = None) -> Any:
        """Extract value from data using JSONPath.

        Args:
            path: JSONPath expression (may include function calls)
            data: Data to extract from
            index: Index to return if multiple matches (default: 0)
            default: Default value to return if extraction fails (default: None)

        Returns:
            Extracted value or default value if extraction fails

        Raises:
            ValueError: If path is invalid and no default is provided

        Examples:
            >>> extractor = JSONPathExtractor()
            >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
            >>> extractor.extract("$.users", data)
            [{"name": "Alice"}, {"name": "Bob"}]
            >>> extractor.extract("$.users.length()", data)
            2
            >>> extractor.extract("$.users[0].name", data)
            "Alice"
            >>> extractor.extract("$.nonexistent", data, default="N/A")
            "N/A"
        """
        try:
            return extract_value(path, data, index)
        except Exception as e:
            # If default is provided, return it
            if default is not None:
                return default

            # Provide detailed and helpful error message
            error_msg = str(e)

            if "No value found" in error_msg or "not found" in error_msg.lower():
                # Path not found in data
                raise ValueError(
                    f"JSONPath 提取失败: 路径 '{path}' 在响应中未找到数据。\n"
                    f"请检查:\n"
                    f"  1. 路径是否正确（应以 $ 开头）\n"
                    f"  2. 字段名称是否正确（区分大小写）\n"
                    f"  3. 响应数据中是否包含该字段\n"
                    f"  4. 数组索引是否超出范围\n"
                    f"建议使用 -v 参数查看完整响应数据结构。"
                )
            elif "parse" in error_msg.lower() or "syntax" in error_msg.lower():
                # Path syntax error
                raise ValueError(
                    f"JSONPath 语法错误: '{path}'\n"
                    f"错误详情: {error_msg}\n"
                    f"请检查 JSONPath 表达式语法。\n"
                    f"参考: $.field 或 $.data[0].field"
                )
            else:
                # Other errors
                raise ValueError(
                    f"JSONPath 提取失败: {error_msg}\n"
                    f"路径: '{path}'\n"
                    f"建议检查路径表达式和响应数据结构是否匹配。"
                )
