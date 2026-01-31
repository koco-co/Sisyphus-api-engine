#!/bin/bash
# 彩色输出功能演示脚本

echo "========================================"
echo "Sisyphus API Engine 彩色输出功能演示"
echo "========================================"
echo ""

echo "1️⃣ 默认模式（中文 + 彩色 + Emoji）"
echo "---"
sisyphus-api-engine --cases examples/11_JSONPath函数演示.yaml 2>&1 | head -30
echo ""
echo ""

echo "2️⃣ 英文模式"
echo "---"
sisyphus-api-engine --lang en --cases examples/11_JSONPath函数演示.yaml 2>&1 | head -30
echo ""
echo ""

echo "3️⃣ 无 Emoji 模式"
echo "---"
sisyphus-api-engine --no-emoji --cases examples/11_JSONPath函数演示.yaml 2>&1 | head -30
echo ""
echo ""

echo "4️⃣ 详细模式（-v）"
echo "---"
sisyphus-api-engine --cases examples/11_JSONPath函数演示.yaml -v 2>&1 | head -50
echo ""
echo ""

echo "演示完成！"
echo "更多用法请参考: examples/彩色输出示例.md"
