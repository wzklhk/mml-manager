#!/usr/bin/env bash
# ============================================================
# MML 配置管理系统 — 一键构建 & 启动脚本
#
# 用法:
#   ./run.sh             构建前端 + 启动后端
#   ./run.sh build       仅构建前端
#   ./run.sh start       仅启动后端（假定已构建）
#   ./run.sh dev         开发模式（后端 + 前端 dev server）
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONVERTER_DIR="$ROOT_DIR/converter"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$CONVERTER_DIR/.venv"

# ---- 颜色 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERR]${NC}   $1"; }

# ---- 依赖检查 ----
check_deps() {
    local missing=false

    if ! command -v node &>/dev/null; then
        err "Node.js 未安装"
        missing=true
    fi

    if ! command -v npm &>/dev/null; then
        err "npm 未安装"
        missing=true
    fi

    if ! command -v python3 &>/dev/null; then
        err "Python 3 未安装"
        missing=true
    fi

    if $missing; then
        exit 1
    fi

    ok "依赖检查通过 (node=$(node -v), npm=$(npm -v), python3=$(python3 -V 2>&1))"
}

# ---- 前端构建 ----
build_frontend() {
    info "构建前端..."
    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        info "安装前端依赖 (npm install)..."
        npm install
    fi

    npm run build
    ok "前端构建完成 → $CONVERTER_DIR/static/"
}

# ---- Python venv + 依赖 ----
ensure_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        info "创建 Python 虚拟环境..."
        python3 -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"

    if [ ! -f "$VENV_DIR/.deps_installed" ]; then
        info "安装 Python 依赖..."
        pip install -q -r "$CONVERTER_DIR/requirements.txt"
        touch "$VENV_DIR/.deps_installed"
        ok "Python 依赖安装完成"
    fi
}

# ---- 启动后端 ----
start_backend() {
    ensure_venv

    if [ ! -d "$CONVERTER_DIR/static" ] || [ ! -f "$CONVERTER_DIR/static/index.html" ]; then
        warn "static/index.html 不存在，请先运行 ./run.sh build"
        warn "  或: cd frontend && npm run build"
        exit 1
    fi

    info "启动后端服务..."
    cd "$CONVERTER_DIR"
    exec python app.py
}

# ---- 开发模式 ----
start_dev() {
    ensure_venv

    info "启动后端 (port 5000)..."
    cd "$CONVERTER_DIR"
    python app.py &
    BACKEND_PID=$!

    info "启动前端开发服务器 (port 8080)..."
    cd "$FRONTEND_DIR"
    npm run serve &
    FRONTEND_PID=$!

    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  开发模式已启动${NC}"
    echo -e "${GREEN}  前端: http://localhost:8080${NC}"
    echo -e "${GREEN}  后端: http://localhost:5000${NC}"
    echo -e "${GREEN}  (Vue proxy 自动转发 /api → 5000)${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo "按 Ctrl+C 停止所有服务"

    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
    wait
}

# ---- 主流程 ----
help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "  无参数     构建前端 + 启动后端（一键部署）"
    echo "  build      仅构建前端"
    echo "  start      仅启动后端（需先 build）"
    echo "  dev        开发模式（前后端分离，热重载）"
    echo "  help       显示此帮助"
    exit 0
}

case "${1:-}" in
    build)
        check_deps
        build_frontend
        ;;
    start)
        check_deps
        start_backend
        ;;
    dev)
        check_deps
        start_dev
        ;;
    help|--help|-h)
        help
        ;;
    *)
        check_deps
        build_frontend
        start_backend
        ;;
esac
