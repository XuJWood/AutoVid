# AutoVid

.PHONY: help install dev run-backend run-frontend docker-up docker-down test

help:
	@echo "AutoVid - AI短剧创作平台"
	@echo ""
	@echo "可用命令:"
	@echo "  make install       安装依赖"
	@echo "  make dev           启动开发环境"
	@echo "  make run-backend   启动后端服务"
	@echo "  make run-frontend  启动前端服务"
	@echo "  make docker-up     启动Docker服务"
	@echo "  make docker-down   停止Docker服务"
	@echo "  make test          运行测试"

install:
	cd src/backend && pip install -r ../../requirements.txt
	cd src/frontend && npm install

dev:
	@echo "请分别在两个终端运行:"
	@echo "  1. make run-backend"
	@echo "  2. make run-frontend"

run-backend:
	cd src/backend && uvicorn app.main:app --reload --port 8000

run-frontend:
	cd src/frontend && npm run dev

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src/backend --cov-report=html

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

# Database
db-init:
	cd src/backend && python -c "from app.core.database import *; import asyncio; asyncio.run(init_db())"

# Format code
format:
	black src/backend
	isort src/backend
