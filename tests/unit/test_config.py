"""配置管理系统测试"""


from apirun.config import Config


def test_config_singleton():
    """测试配置管理器单例模式"""

    config1 = Config()
    config2 = Config()

    assert config1 is config2, "应该是同一个实例"


def test_config_default_values():
    """测试配置默认值"""

    config = Config()

    # 安全配置
    assert config.MAX_RESPONSE_SIZE == 10 * 1024 * 1024  # 10MB
    assert config.MAX_FILE_SIZE == 50 * 1024 * 1024  # 50MB
    assert config.MAX_SQL_LENGTH == 10000
    assert config.ENABLE_SQL_VALIDATION is True

    # 性能配置
    assert config.REQUEST_TIMEOUT == 30
    assert config.STEP_TIMEOUT == 300
    assert config.DB_POOL_SIZE == 5
    assert config.MAX_WORKERS == 4

    # 日志配置
    assert config.LOG_LEVEL == "INFO"
    assert config.LOG_FILE is None

    # CSV 配置
    assert config.MAX_CSV_SIZE == 100 * 1024 * 1024  # 100MB
    assert config.MAX_CSV_ROWS == 1000000


def test_config_from_env(monkeypatch):
    """测试从环境变量加载配置"""

    # 设置环境变量
    monkeypatch.setenv("SISYPHUS_MAX_RESPONSE_SIZE", "20971520")  # 20MB
    monkeypatch.setenv("SISYPHUS_REQUEST_TIMEOUT", "60")
    monkeypatch.setenv("SISYPHUS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SISYPHUS_ENABLE_SQL_VALIDATION", "false")

    # 重置配置以重新加载
    Config.reset()
    config = Config()

    assert config.MAX_RESPONSE_SIZE == 20971520
    assert config.REQUEST_TIMEOUT == 60
    assert config.LOG_LEVEL == "DEBUG"
    assert config.ENABLE_SQL_VALIDATION is False

    # 清理
    Config.reset()


def test_config_invalid_env_values(monkeypatch):
    """测试无效的环境变量值使用默认值"""

    monkeypatch.setenv("SISYPHUS_REQUEST_TIMEOUT", "invalid")
    monkeypatch.setenv("SISYPHUS_ENABLE_SQL_VALIDATION", "not_a_bool")

    Config.reset()
    config = Config()

    # 应该回退到默认值
    assert config.REQUEST_TIMEOUT == 30
    assert config.ENABLE_SQL_VALIDATION is False  # "not_a_bool" 不是 true

    Config.reset()


def test_config_as_dict():
    """测试配置导出为字典"""

    Config.reset()
    config = Config()

    config_dict = config.as_dict()

    assert "security" in config_dict
    assert "performance" in config_dict
    assert "logging" in config_dict
    assert "csv" in config_dict
    assert "memory" in config_dict

    assert config_dict["security"]["max_response_size"] == 10 * 1024 * 1024
    assert config_dict["performance"]["request_timeout"] == 30


def test_config_reset():
    """测试配置重置"""

    config1 = Config()
    config_id = id(config1)

    Config.reset()
    config2 = Config()

    assert id(config2) != config_id, "重置后应该是新实例"
