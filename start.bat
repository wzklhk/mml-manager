@echo off
chcp 65001 >nul
echo ========================================
echo MML配置管理系统 - 快速启动
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.x
    pause
    exit /b 1
)
echo ✅ Python环境正常

echo.
echo [2/3] 启动后端服务...
cd converter
start "MML Backend" cmd /k "python app.py"
cd ..
echo ✅ 后端服务已启动 (http://localhost:5000)

timeout /t 3 /nobreak >nul

echo.
echo [3/3] 启动前端服务...
cd frontend
if not exist node_modules (
    echo 首次运行，正在安装依赖...
    call npm install
)
start "MML Frontend" cmd /k "npm run serve"
cd ..
echo ✅ 前端服务已启动 (http://localhost:8080)

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo 后端API: http://localhost:5000
echo 前端界面: http://localhost:8080
echo.
echo 提示: 关闭命令行窗口即可停止服务
echo ========================================
pause
