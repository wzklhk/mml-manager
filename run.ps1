# ============================================================
# MML 配置管理系统 - 一键构建 & 启动脚本 (PowerShell 版)
#
# 用法:
#   .\run.ps1             构建前端 + 启动后端
#   .\run.ps1 build       仅构建前端
#   .\run.ps1 start       仅启动后端（假定已构建）
#   .\run.ps1 dev         开发模式（后端 + 前端 dev server）
# ============================================================

$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$CONVERTER_DIR = Join-Path $ROOT_DIR "converter"
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"
$VENV_DIR = Join-Path $CONVERTER_DIR ".venv"

# ---- 颜色 ----
$CYAN = "Cyan"
$GREEN = "Green"
$YELLOW = "Yellow"
$RED = "Red"

function info { Write-Host "[INFO]  $args" -ForegroundColor $CYAN }
function ok { Write-Host "[OK]    $args" -ForegroundColor $GREEN }
function warn { Write-Host "[WARN]  $args" -ForegroundColor $YELLOW }
function err { Write-Host "[ERR]   $args" -ForegroundColor $RED }

# ---- 依赖检查 ----
function check_deps {
    $missing = $false

    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        err "Node.js is not installed"
        $missing = $true
    }

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        err "npm is not installed"
        $missing = $true
    }

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        err "Python is not installed"
        $missing = $true
    }

    if ($missing) { exit 1 }

    $nodeV = node -v
    $npmV = npm -v
    $pyV = python -V 2>&1
    ok "Dependency check passed (node=$nodeV, npm=$npmV, python=$pyV)"
}

# ---- Frontend build ----
function build_frontend {
    info "Building frontend..."
    Push-Location $FRONTEND_DIR

    if (-not (Test-Path "node_modules")) {
        info "Installing frontend dependencies (npm install)..."
        npm install
    }

    npm run build
    Pop-Location
    $st = Join-Path $CONVERTER_DIR "static"
    ok "Frontend build complete -> $st"
}

# ---- Python venv + dependencies ----
function ensure_venv {
    if (-not (Test-Path $VENV_DIR)) {
        info "Creating Python virtual environment..."
        python -m venv $VENV_DIR
    }

    $activate = Join-Path $VENV_DIR "Scripts\Activate.ps1"
    . $activate

    $flag = Join-Path $VENV_DIR ".deps_installed"
    if (-not (Test-Path $flag)) {
        info "Installing Python dependencies..."
        pip install -q -r (Join-Path $CONVERTER_DIR "requirements.txt")
        New-Item -ItemType File -Path $flag -Force | Out-Null
        ok "Python dependencies installed"
    }
}

# ---- Start backend ----
function start_backend {
    ensure_venv

    $index = Join-Path $CONVERTER_DIR "static\index.html"
    if (-not (Test-Path $index)) {
        warn "static\index.html not found, please run '.\run.ps1 build' first"
        warn "  or: cd frontend; npm run build"
        exit 1
    }

    info "Starting backend service..."
    Push-Location $CONVERTER_DIR
    python app.py
    Pop-Location
}

# ---- Dev mode ----
function start_dev {
    ensure_venv

    info "Starting backend (port 5000)..."
    Push-Location $CONVERTER_DIR
    $backendJob = Start-Job -ScriptBlock { param($d) Push-Location $d; python app.py; Pop-Location } -ArgumentList $CONVERTER_DIR
    Pop-Location

    info "Starting frontend dev server (port 8080)..."
    Push-Location $FRONTEND_DIR
    $frontendJob = Start-Job -ScriptBlock { param($d) Push-Location $d; npm run serve; Pop-Location } -ArgumentList $FRONTEND_DIR
    Pop-Location

    Write-Host ""
    Write-Host "======================================" -ForegroundColor $GREEN
    Write-Host "  Dev mode started" -ForegroundColor $GREEN
    Write-Host "  Frontend: http://localhost:8080" -ForegroundColor $GREEN
    Write-Host "  Backend:  http://localhost:5000" -ForegroundColor $GREEN
    Write-Host "  (Vue proxy forwards /api -> 5000)" -ForegroundColor $GREEN
    Write-Host "======================================" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services"

    try {
        while ($true) { Start-Sleep -Seconds 1 }
    }
    finally {
        Stop-Job $backendJob 2>$null
        Stop-Job $frontendJob 2>$null
        Remove-Job $backendJob 2>$null
        Remove-Job $frontendJob 2>$null
    }
}

# ---- Main ----
function show_help {
    Write-Host "Usage: run.ps1 [option]"
    Write-Host ""
    Write-Host "  (no arg)   Build frontend + start backend (one-click deploy)"
    Write-Host "  build      Build frontend only"
    Write-Host "  start      Start backend only (requires build first)"
    Write-Host "  dev        Dev mode (frontend + backend, hot reload)"
    Write-Host "  help       Show this help"
    exit 0
}

switch ($args[0]) {
    "build" {
        check_deps
        build_frontend
    }
    "start" {
        check_deps
        start_backend
    }
    "dev" {
        check_deps
        start_dev
    }
    "help" { show_help }
    default {
        check_deps
        build_frontend
        start_backend
    }
}
