"""线程安全测试"""

import threading
import time

from apirun.executor.custom import KEYWORD_REGISTRY, register_keyword


def test_concurrent_keyword_registration():
    """测试并发关键字注册的线程安全性"""

    registered_keywords = []

    def register_many_keywords(start_id: int) -> None:
        """在子线程中注册多个关键字"""
        for i in range(start_id, start_id + 10):
            # 创建临时关键字类
            class TempKeyword:
                name = f"keyword_{i}"

                def execute(self, **kwargs):  # type: ignore[method-override]
                    return f"result_{i}"

            register_keyword(TempKeyword)
            registered_keywords.append(f"keyword_{i}")
            time.sleep(0.001)  # 模拟处理延迟

    # 启动多个线程同时注册关键字
    threads = []
    for i in range(0, 50, 10):
        thread = threading.Thread(target=register_many_keywords, args=(i,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 验证所有关键字都已注册
    assert len(KEYWORD_REGISTRY) >= 50, f"至少应注册 50 个关键字，实际: {len(KEYWORD_REGISTRY)}"

    # 验证关键字可以正常访问
    for keyword_name in registered_keywords[:10]:  # 抽查前 10 个
        assert keyword_name in KEYWORD_REGISTRY, f"关键字 {keyword_name} 未注册"


def test_concurrent_keyword_read():
    """测试并发关键字读取的线程安全性"""

    # 先注册一些关键字
    class TestKeyword1:
        name = "test_keyword_1"

        def execute(self, **kwargs):  # type: ignore[method-override]
            return "result_1"

    class TestKeyword2:
        name = "test_keyword_2"

        def execute(self, **kwargs):  # type: ignore[method-override]
            return "result_2"

    register_keyword(TestKeyword1)
    register_keyword(TestKeyword2)

    read_counts = {"keyword_1": 0, "keyword_2": 0}

    def read_keywords_many_times() -> None:
        """在子线程中多次读取关键字"""
        for _ in range(100):
            # 读取关键字（模拟 execute_custom_step 中的查找）
            keyword_1 = KEYWORD_REGISTRY.get("test_keyword_1")
            keyword_2 = KEYWORD_REGISTRY.get("test_keyword_2")
            if keyword_1:
                read_counts["keyword_1"] += 1
            if keyword_2:
                read_counts["keyword_2"] += 1

    # 启动多个线程同时读取
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=read_keywords_many_times)
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 验证读取次数正确
    assert read_counts["keyword_1"] == 1000, f"keyword_1 应读取 1000 次，实际: {read_counts['keyword_1']}"
    assert read_counts["keyword_2"] == 1000, f"keyword_2 应读取 1000 次，实际: {read_counts['keyword_2']}"


def test_concurrent_register_and_read():
    """测试并发注册和读取的线程安全性"""

    success_count = {"value": 0}

    def register_keywords() -> None:
        """持续注册新关键字"""
        for i in range(100):
            class TempKeyword:
                name = f"temp_{i}"

                def execute(self, **kwargs):  # type: ignore[method-override]
                    return f"temp_result_{i}"

            register_keyword(TempKeyword)
            time.sleep(0.0001)

    def read_keywords() -> None:
        """持续读取关键字"""
        for _ in range(100):
            _ = KEYWORD_REGISTRY.get("test_keyword_1")
            success_count["value"] += 1
            time.sleep(0.0001)

    # 注册初始关键字
    class TestKeyword1:
        name = "test_keyword_1"

        def execute(self, **kwargs):  # type: ignore[method-override]
            return "result_1"

    register_keyword(TestKeyword1)

    # 同时启动注册和读取线程
    register_thread = threading.Thread(target=register_keywords)
    read_thread = threading.Thread(target=read_keywords)

    register_thread.start()
    read_thread.start()

    register_thread.join()
    read_thread.join()

    # 验证读取操作成功完成
    assert success_count["value"] == 100, f"应完成 100 次读取，实际: {success_count['value']}"
    # 验证至少有初始关键字
    assert "test_keyword_1" in KEYWORD_REGISTRY
