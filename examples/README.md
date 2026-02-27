# 示例用例

本目录包含可独立运行的 YAML 示例，使用公共接口 httpbin.org，无需本地服务。

## 运行方式

```bash
# 安装依赖后（uv sync）
uv run python -m apirun.cli --case examples/01_simple_get.yaml -O text
uv run python -m apirun.cli --case examples/02_get_with_query.yaml -O text
uv run python -m apirun.cli --case examples/03_post_json.yaml -O text
```

或使用 `sisyphus` 命令（需先 `uv pip install -e .`）：

```bash
sisyphus --case examples/01_simple_get.yaml -O text
```

## 示例说明

| 文件 | 说明 |
|------|------|
| 01_simple_get.yaml | 最简 GET 请求 + status_code 断言 |
| 02_get_with_query.yaml | 场景变量 + URL 查询参数 |
| 03_post_json.yaml | POST JSON 与多条件断言 |
