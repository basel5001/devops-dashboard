.PHONY: install install-dev test lint dev docker-build docker-run clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

dev:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port $${PORT:-8000}

docker-build:
	docker build -t devops-dashboard .

docker-run:
	docker compose up -d

docker-stop:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
