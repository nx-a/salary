.DEFAULT_GOAL := help
UV      ?= uv
HOST    ?= 0.0.0.0
PORT    ?= 8091
RUN     := $(UV) run
CLI     := $(RUN) python -m salary.cli

include .env
export

.PHONY: help install env secret db-create migrate create-admin setup run dev test clean docker-up docker-down db-reset

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости (uv sync)
	$(UV) sync

env: ## Создать .env из .env.example (если отсутствует)
	@test -f .env || (cp .env.example .env && sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$$($(RUN) python -c 'import secrets;print(secrets.token_urlsafe(48))')|" .env && echo ".env создан")

secret: ## Сгенерировать секрет для JWT
	@$(RUN) python -c 'import secrets;print(secrets.token_urlsafe(48))'

db-create: ## Создать базу данных PostgreSQL
	$(CLI) db-create

migrate: ## Создать таблицы
	$(CLI) migrate

create-admin: ## Создать администратора из .env (или LOGIN=.. PASSWORD=..)
	$(CLI) create-admin $(if $(LOGIN),--login $(LOGIN)) $(if $(PASSWORD),--password $(PASSWORD))

setup: install env db-create migrate create-admin ## Полная первичная настройка

run: ## Запустить сервис
	$(RUN) uvicorn salary.main:app --app-dir src --host $(HOST) --port $(PORT)

dev: ## Запустить с автоперезагрузкой
	$(RUN) uvicorn salary.main:app --app-dir src --host $(HOST) --port $(PORT) --reload --reload-dir src --reload-dir static

test: ## Запустить тесты
	$(RUN) pytest -q

db-reset: ## Удалить и заново создать таблицы (ДАННЫЕ БУДУТ ПОТЕРЯНЫ)
	$(CLI) db-drop-schema
	$(CLI) migrate

docker-up: ## Поднять отдельный PostgreSQL в Docker (порт 5433)
	docker compose up -d --wait

docker-down: ## Остановить PostgreSQL в Docker
	docker compose down

clean: ## Удалить кэши
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
