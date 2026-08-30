.PHONY: test lint dev

test:
	cd services/marketplace-api && python -m pytest -q
	cd services/ai-api && python -m pytest -q
	cd services/event-worker && python -m pytest -q

lint:
	cd services/marketplace-api && python -m ruff check .

dev:
	docker compose up --build
