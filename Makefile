.PHONY: help build up down logs shell test migrate

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker containers"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View logs"
	@echo "  make shell    - Enter backend container"
	@echo "  make test     - Run tests"
	@echo "  make migrate  - Run database migrations"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec backend bash

test:
	docker-compose exec backend pytest

migrate:
	docker-compose exec backend alembic upgrade head

dev:
	docker-compose up