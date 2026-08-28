#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
echo "[StoryClaw] 启动核心服务..."
docker compose --env-file .env -f docker/docker-compose.yml up -d postgres redis milvus neo4j langgraph-server backend frontend
echo "[StoryClaw] 等待 backend 健康..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "[StoryClaw] backend OK"
    break
  fi
  sleep 2
done
echo "[StoryClaw] 前端:      http://localhost:5173"
echo "[StoryClaw] 后端 API:  http://localhost:8000/docs"
echo "[StoryClaw] LangGraph: http://localhost:8080"
