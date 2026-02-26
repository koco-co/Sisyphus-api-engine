#!/bin/bash
# PyPI 自动发布脚本
#
# 使用方法:
#   1. 设置 PyPI token 环境变量:
#      export PYPI_API_TOKEN="your-token-here"
#   2. 运行脚本: ./publish.sh
#
# 或者使用 ~/.pypirc 配置文件

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="Sisyphus-api-engine"
VERSION=$(grep "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/' | tr -d '"')

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   PyPI 发布脚本${NC}"
echo -e "${BLUE}   项目: ${PROJECT_NAME}${NC}"
echo -e "${BLUE}   版本: ${VERSION}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 选择 Python 命令（python / python3）
PYTHON_CMD=""
echo -e "${YELLOW}⏳ 检查必要工具...${NC}"
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ 错误: 未找到 Python（python 或 python3）${NC}"
    exit 1
fi

if ! command -v twine &> /dev/null; then
    echo -e "${YELLOW}⚠️  警告: 未找到 twine，正在安装...${NC}"
    "$PYTHON_CMD" -m pip install twine
fi

echo -e "${GREEN}✅ 工具检查完成${NC}"
echo ""

# 清理旧的构建文件
echo -e "${YELLOW}🧹 清理旧的构建文件...${NC}"
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

# 运行测试（优先用 uv 跑项目环境，否则用当前 Python -m pytest）
echo -e "${YELLOW}🧪 运行测试...${NC}"
if [ -d "tests" ]; then
    if command -v uv &> /dev/null; then
        UV_PYTEST="uv run python -m pytest tests/ -v --tb=short"
    else
        UV_PYTEST="$PYTHON_CMD -m pytest tests/ -v --tb=short"
    fi
    if $UV_PYTEST; then
        echo -e "${GREEN}✅ 测试通过${NC}"
    else
        echo -e "${RED}❌ 测试失败，取消发布${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  未找到测试目录，跳过测试${NC}"
fi
echo ""

# 检查 git 状态
echo -e "${YELLOW}📋 检查 git 状态...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  警告: 有未提交的更改${NC}"
    git status --short
    read -p "是否继续发布？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 取消发布${NC}"
        exit 1
    fi
fi
echo ""

# 检查版本标签
echo -e "${YELLOW}🏷️  检查版本标签...${NC}"
if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  标签 v${VERSION} 已存在${NC}"
    read -p "是否继续发布？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 取消发布${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 版本标签检查通过${NC}"
fi
echo ""

# 构建包（优先用 uv 以使用项目环境中的 build）
echo -e "${YELLOW}🔨 构建发布包...${NC}"
if command -v uv &> /dev/null; then
    uv run python -m build
else
    "$PYTHON_CMD" -m build
fi
echo -e "${GREEN}✅ 构建完成${NC}"
echo ""

# 检查构建结果
echo -e "${YELLOW}📦 检查构建结果...${NC}"
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo -e "${RED}❌ 错误: dist 目录为空${NC}"
    exit 1
fi

ls -lh dist/
echo ""

# 确认发布
echo -e "${YELLOW}⚠️  即将发布到 PyPI:${NC}"
echo -e "  项目: ${PROJECT_NAME}"
echo -e "  版本: ${VERSION}"
echo ""
read -p "确认发布？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ 取消发布${NC}"
    exit 1
fi
echo ""

# 发布到 PyPI
echo -e "${YELLOW}📤 发布到 PyPI...${NC}"

# 检查 token
if [ -n "$PYPI_API_TOKEN" ]; then
    echo -e "${GREEN}✅ 使用环境变量中的 token${NC}"
    twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
elif [ -f ~/.pypirc ]; then
    echo -e "${GREEN}✅ 使用 ~/.pypirc 配置${NC}"
    twine upload dist/*
else
    echo -e "${RED}❌ 错误: 未找到 PyPI token${NC}"
    echo ""
    echo "请设置环境变量:"
    echo "  export PYPI_API_TOKEN=\"your-token-here\""
    echo ""
    echo "或配置 ~/.pypirc 文件:"
    echo "  [pypi]"
    echo "  username = __token__"
    echo "  password = your-token-here"
    exit 1
fi

# 检查发布结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   ✅ 发布成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "🔗 PyPI 页面:"
    echo -e "   https://pypi.org/project/${PROJECT_NAME}/"
    echo ""
    echo -e "📦 安装命令:"
    echo -e "   pip install ${PROJECT_NAME}==${VERSION}"
    echo ""

    # 创建 Git 标签（如果不存在）
    if ! git rev-parse "v${VERSION}" >/dev/null 2>&1; then
        echo -e "${YELLOW}🏷️  创建 Git 标签 v${VERSION}...${NC}"
        git tag -a "v${VERSION}" -m "Release v${VERSION}"
        echo -e "${YELLOW}💡 提示: 运行以下命令推送标签:${NC}"
        echo -e "   git push origin v${VERSION}"
    fi
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}   ❌ 发布失败${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
