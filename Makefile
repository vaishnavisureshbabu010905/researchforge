.PHONY: install test test-cov lint format typecheck run mcp frontend docker-up docker-down clean evaluate

install:
	pip install -e ".[dev,anthropic,openai,linkup]" --break-system-packages 2>/dev/null || pip install -e ".[dev,anthropic,openai,linkup]"
	cd frontend && npm install

test:
	pytest -q

test-cov:
	pytest -q --cov=researchforge --cov-report=term-missing

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src

run:
	uvicorn researchforge.api.app:app --reload --host 0.0.0.0 --port 8000

mcp:
	python -m researchforge.mcp.server

frontend:
	cd frontend && npm run dev

evaluate:
	python evaluation/benchmark.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage researchforge.db
