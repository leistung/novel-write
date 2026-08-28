.RECIPEPREFIX := >
.PHONY: help up down up-all health logs build migrate backend-shell frontend-dev

help:
>@echo "StoryClaw dev commands:"
>@echo "  make up          启动核心服务 (postgres redis milvus neo4j langgraph backend frontend)"
>@echo "  make up-all      启动全部服务 (含 nginx/minio/etcd)"
>@echo "  make down        停止全部服务"
>@echo "  make health      健康检查"
>@echo "  make logs        查看日志 (Ctrl+C 退出)"
>@echo "  make build       构建镜像"
>@echo "  make migrate     执行数据库迁移"
>@echo "  make backend-shell  进入 backend 容器"
>@echo "  make frontend-dev   前端本地开发 (npm run dev)"

COMPOSE := docker compose --env-file .env -f docker/docker-compose.yml

up:
>$(COMPOSE) up -d postgres redis milvus neo4j backend frontend

up-all:
>$(COMPOSE) --profile infra up -d

down:
>$(COMPOSE) down

health:
>@echo "Checking services..."
>@curl -sf http://localhost:8000/health && echo " <- backend OK" || echo "backend DOWN"
>@curl -sf http://localhost:5173 >/dev/null && echo "frontend OK" || echo "frontend DOWN"
>$(COMPOSE) ps

logs:
>$(COMPOSE) logs -f --tail=200

build:
>$(COMPOSE) build

migrate:
>$(COMPOSE) exec backend alembic upgrade head

backend-shell:
>$(COMPOSE) exec backend bash

frontend-dev:
>cd frontend && npm run dev
