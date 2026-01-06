@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ====================================
echo 内容数据分析系统 - 一键启动脚本
echo ====================================

:: 检查 Docker 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

echo.
echo [1/4] 启动 Docker 服务 (PostgreSQL + Redis)...
docker-compose -f docker-compose.dev.yml up -d
if errorlevel 1 (
    echo [错误] Docker 服务启动失败
    pause
    exit /b 1
)

echo.
echo [2/4] 等待数据库就绪...
timeout /t 3 /nobreak >nul

:: 检查数据库连接
:check_db
docker exec content-analytics-db-dev pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo 等待 PostgreSQL 启动...
    timeout /t 2 /nobreak >nul
    goto check_db
)
echo PostgreSQL 已就绪

echo.
echo [3/4] 启动后端服务...
start "后端服务" cmd /k "cd /d %~dp0backend && python run.py"

:: 等待后端启动
echo 等待后端服务启动...
timeout /t 3 /nobreak >nul

echo.
echo [4/4] 启动前端服务...
start "前端服务" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ====================================
echo 所有服务已启动！
echo ====================================
echo.
echo 服务地址:
echo   前端:     http://localhost:5173
echo   后端API:  http://localhost:8088
echo   API文档:  http://localhost:8088/api/docs
echo.
echo 默认账号: admin / admin123
echo.
echo 提示: 关闭此窗口不会停止服务
echo       使用 stop-dev.bat 停止所有服务
echo ====================================
echo.
pause
