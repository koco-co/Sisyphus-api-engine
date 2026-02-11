"""示例 Python 脚本文件,供 Sisyphus 测试用例调用."""

from datetime import datetime


def calculate_sum(numbers):
    """计算数字列表的总和."""
    return sum(numbers)


def process_data(data):
    """处理数据."""
    return {
        "processed": True,
        "timestamp": datetime.now().isoformat(),
        "data_length": len(data)
    }


# 主脚本逻辑
if __name__ == "__main__":
    # 测试数据
    test_numbers = [1, 2, 3, 4, 5]

    # 计算总和
    result = calculate_sum(test_numbers)
    print(f"Sum of {test_numbers} = {result}")

    # 处理数据
    processed = process_data(test_numbers)
    print(f"Processed: {processed}")

    # 导出变量
    # 在 Sisyphus 环境中,这些变量会被自动捕获
    script_result = result
    processed_result = processed
