.PHONY: up down restart logs migrate-user migrate-category migrate-expense test-user test-category test-expense format lint

up:
	docker-compose up --build -d

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs -f

migrate-user:
	docker-compose exec user_service alembic upgrade head

migrate-category:
	docker-compose exec category_service alembic upgrade head

migrate-expense:
	docker-compose exec expense_service alembic upgrade head

test-user:
	docker-compose exec user_service pytest

test-category:
	docker-compose exec category_service pytest

test-expense:
	docker-compose exec expense_service pytest

format:
	black .

lint:
	ruff check .
