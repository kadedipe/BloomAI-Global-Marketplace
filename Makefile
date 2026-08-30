.PHONY: test lint dev

test:
	python -m pytest services/marketplace-api/tests services/ai-api/tests -q

lint:
	python -m ruff check services

dev:
	docker compose up --build

