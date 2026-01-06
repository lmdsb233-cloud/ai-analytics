@echo off
chcp 65001 >nul

echo ====================================
echo 内容数据分析系统 - 停止服务
echo ====================================

echo.
echo [1/3] 停止前端服务...
:: 通过窗口标题杀进程
taskkill /FI "WINDOWTITLE eq 前端服务*" /F >nul 2>&1
:: 通过端口杀进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo [2/3] 停止后端服务...
:: 通过窗口标题杀进程
taskkill /FI "WINDOWTITLE eq 后端服务*" /F >nul 2>&1
:: 通过端口杀进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8088 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo [3/3] 停止 Docker 服务...
docker-compose -f docker-compose.dev.yml down

echo.
echo ====================================
echo 所有服务已停止
echo ====================================
pause
