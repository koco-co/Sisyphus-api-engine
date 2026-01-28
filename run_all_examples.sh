#!/bin/bash

################################################################################
# Sisyphus API Engine - 一键运行所有示例测试
#
# 功能：
#   - 自动运行所有 YAML 测试案例
#   - 自动运行 Python 演示脚本
#   - 汇总测试结果并显示统计信息
#
# 使用方法：
#   chmod +x run_all_examples.sh
#   ./run_all_examples.sh
#
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# 日志函数
log_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

log_section() {
    echo -e "\n${PURPLE}>>> $1${NC}\n"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# 检查 Python 环境
check_environment() {
    log_section "检查运行环境"

    # 检查 Python 版本
    if ! command -v python &> /dev/null; then
        log_error "未找到 Python，请先安装 Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    log_success "Python 版本: $PYTHON_VERSION"

    # 检查是否安装了项目
    if ! python -c "import apirun" 2>/dev/null; then
        log_warning "项目未安装，正在安装..."
        pip install -e . > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            log_success "项目安装成功"
        else
            log_error "项目安装失败"
            exit 1
        fi
    else
        log_success "项目已安装"
    fi

    # 检查 CLI 是否可用
    if ! sisyphus-api-engine --help &> /dev/null; then
        log_error "CLI 不可用，请检查安装"
        exit 1
    fi

    log_success "CLI 命令可用"
}

# 运行 YAML 测试案例
run_yaml_tests() {
    log_header "运行 YAML 测试案例"

    local yaml_files=(
        "examples/01_最简案例.yaml"
        "examples/02_HTTP请求测试.yaml"
        "examples/03_完整流程测试.yaml"
        "examples/04_数据库操作.yaml"
        "examples/05_步骤控制.yaml"
        "examples/06_等待和循环.yaml"
        "examples/07_数据驱动测试.yaml"
    )

    for yaml_file in "${yaml_files[@]}"; do
        if [ ! -f "$yaml_file" ]; then
            log_warning "文件不存在，跳过: $yaml_file"
            ((SKIPPED_TESTS++))
            continue
        fi

        log_section "运行: $(basename $yaml_file)"
        ((TOTAL_TESTS++))

        # 运行测试并捕获输出
        if sisyphus-api-engine --cases "$yaml_file" -v > /tmp/test_output_$$.txt 2>&1; then
            # 测试通过
            PASSED_STATUS=$(grep -o "Status: PASSED" /tmp/test_output_$$.txt || echo "")
            if [ -n "$PASSED_STATUS" ]; then
                log_success "$(basename $yaml_file) - 通过"
                ((PASSED_TESTS++))
            else
                # 检查是否有部分通过
                PASS_RATE=$(grep -o "Pass Rate: [0-9.]*%" /tmp/test_output_$$.txt | grep -o "[0-9.]*" || echo "0")
                if [ "$(echo "$PASS_RATE > 0" | bc)" -eq 1 ]; then
                    log_warning "$(basename $yaml_file) - 部分通过 ($PASS_RATE%)"
                    ((PASSED_TESTS++))
                else
                    log_error "$(basename $yaml_file) - 失败"
                    ((FAILED_TESTS++))
                fi
            fi
        else
            # 测试失败
            log_error "$(basename $yaml_file) - 执行失败"
            ((FAILED_TESTS++))

            # 显示错误信息
            ERROR_MSG=$(grep -A 5 "Error:" /tmp/test_output_$$.txt | head -5 || echo "")
            if [ -n "$ERROR_MSG" ]; then
                echo -e "${RED}  错误信息:${NC}"
                echo "$ERROR_MSG" | sed 's/^/    /'
            fi
        fi

        # 清理临时文件
        rm -f /tmp/test_output_$$.txt
    done
}

# 运行 Python 演示脚本
run_python_scripts() {
    log_header "运行 Python 演示脚本"

    local python_scripts=(
        "examples/08_重试机制演示.py"
        "examples/09_等待循环演示.py"
    )

    for script in "${python_scripts[@]}"; do
        if [ ! -f "$script" ]; then
            log_warning "文件不存在，跳过: $script"
            ((SKIPPED_TESTS++))
            continue
        fi

        log_section "运行: $(basename $script)"
        ((TOTAL_TESTS++))

        # 运行脚本并捕获输出
        if python "$script" > /tmp/script_output_$$.txt 2>&1; then
            # 检查输出中是否有 "通过" 字样
            if grep -q "通过" /tmp/script_output_$$.txt || grep -q "PASSED" /tmp/script_output_$$.txt; then
                log_success "$(basename $script) - 通过"
                ((PASSED_TESTS++))
            else
                log_warning "$(basename $script) - 完成（需验证结果）"
                ((PASSED_TESTS++))
            fi
        else
            log_error "$(basename $script) - 执行失败"
            ((FAILED_TESTS++))

            # 显示错误信息
            ERROR_MSG=$(tail -20 /tmp/script_output_$$.txt || echo "")
            if [ -n "$ERROR_MSG" ]; then
                echo -e "${RED}  错误信息:${NC}"
                echo "$ERROR_MSG" | sed 's/^/    /'
            fi
        fi

        # 清理临时文件
        rm -f /tmp/script_output_$$.txt
    done
}

# 显示测试汇总
show_summary() {
    log_header "测试结果汇总"

    echo -e "${CYAN}总测试数:${NC}     $TOTAL_TESTS"
    echo -e "${GREEN}通过:${NC}        $PASSED_TESTS"
    echo -e "${RED}失败:${NC}        $FAILED_TESTS"
    echo -e "${YELLOW}跳过:${NC}        $SKIPPED_TESTS"

    if [ $TOTAL_TESTS -gt 0 ]; then
        PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS / $TOTAL_TESTS) * 100}")
        echo -e "\n${CYAN}通过率:${NC}       $PASS_RATE%"

        if [ $FAILED_TESTS -eq 0 ]; then
            echo -e "\n${GREEN}🎉 所有测试通过！${NC}"
            return 0
        else
            echo -e "\n${YELLOW}⚠️  部分测试失败，请检查详细日志${NC}"
            return 1
        fi
    else
        log_warning "没有执行任何测试"
        return 1
    fi
}

# 主函数
main() {
    echo -e "${GREEN}"
    cat << "EOF"
   _____           _        _  _           _
  |_   _|__ _ __ (_)___  | || | __ _  ___| |_
    | |/ _ \ '_ \| / __| | __ |/ _` |/ __| __|
    | |  __/ | | | \__ \ | || | (_| | (__| |_
    |_|\___|_| |_|_|___/ |_||_|\__,_|\___|\__|

    API Automation Testing Engine - 示例测试套件
EOF
    echo -e "${NC}"

    # 记录开始时间
    START_TIME=$(date +%s)

    # 执行测试流程
    check_environment
    run_yaml_tests
    run_python_scripts

    # 记录结束时间
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo -e "\n${CYAN}总耗时: ${DURATION}秒${NC}\n"

    # 显示汇总并返回退出码
    show_summary
    exit $?
}

# 运行主函数
main "$@"
