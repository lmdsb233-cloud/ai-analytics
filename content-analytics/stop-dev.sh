#!/bin/bash

echo "===================================="
echo "内容数据分析系统 - 停止服务"
echo "===================================="

cd "$(dirname "$0")"

echo ""
echo "[1/3] 停止后端服务..."
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi
# 也尝试通过端口杀进程
lsof -ti:8088 | xargs kill -9 2>/dev/null

echo ""
echo "[2/3] 停止前端服务..."
if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi
# 也尝试通过端口杀进程
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo ""
echo "[3/3] 停止 Docker 服务..."
docker-compose -f docker-compose.dev.yml down

echo ""
echo "===================================="
echo "所有服务已停止"
echo "===================================="
