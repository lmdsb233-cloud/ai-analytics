#!/bin/bash

echo "===================================="
echo "内容数据分析系统 - 一键启动脚本"
echo "===================================="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "[错误] Docker 未运行，请先启动 Docker"
    exit 1
fi

echo ""
echo "[1/4] 启动 Docker 服务 (PostgreSQL + Redis)..."
docker-compose -f docker-compose.dev.yml up -d
if [ $? -ne 0 ]; then
    echo "[错误] Docker 服务启动失败"
    exit 1
fi

echo ""
echo "[2/4] 等待数据库就绪..."
until docker exec content-analytics-db-dev pg_isready -U postgres > /dev/null 2>&1; do
    echo "等待 PostgreSQL 启动..."
    sleep 2
done
echo "PostgreSQL 已就绪"

echo ""
echo "[3/4] 启动后端服务..."
cd "$(dirname "$0")/backend"
python run.py &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

echo ""
echo "[4/4] 启动前端服务..."
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

# 保存 PID 到文件
cd "$(dirname "$0")"
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo ""
echo "===================================="
echo "所有服务已启动！"
echo "===================================="
echo ""
echo "服务地址:"
echo "  前端:     http://localhost:5173"
echo "  后端API:  http://localhost:8088"
echo "  API文档:  http://localhost:8088/api/docs"
echo ""
echo "默认账号: admin / admin123"
echo ""
echo "使用 ./stop-dev.sh 停止所有服务"
echo "===================================="

# 等待用户按 Ctrl+C
echo ""
echo "按 Ctrl+C 停止所有服务..."
wait
