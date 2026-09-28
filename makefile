.PHONY: up down rebuild migrate logs test lint shell worker

up:
	docker compose up --build

down:
	docker compose down

rebuild:
	docker compose up --build --force-recreate

migrate:
	docker compose exec backend alembic upgrade head

logs:
	docker compose logs -f

worker:
	docker compose up --build worker

test:
	docker compose exec backend pytest

lint:
	docker compose exec backend ruff check .

shell:
	docker compose exec backend sh

.PHONY: backup restore

backup:
	docker compose exec -e BACKUP_DIR=/backups backend sh -c \
		"mkdir -p /backups && ./scripts/backup_postgres.sh"

restore:
	docker compose exec -e BACKUP_FILE=/backups/CHANGE_ME.dump backend sh -c \
		"./scripts/restore_postgres.sh"

.PHONY: migration-check

migration-check:
	docker compose exec backend alembic current
	docker compose exec backend alembic heads
	docker compose exec backend alembic check


