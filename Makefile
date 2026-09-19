.PHONY: install test lint typecheck run api docker

install:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

test:
	.venv/bin/pytest --cov=changeguard --cov-report=term-missing

lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

typecheck:
	.venv/bin/mypy src

run:
	.venv/bin/streamlit run app.py

api:
	.venv/bin/uvicorn changeguard.api:app --reload --port 8080

docker:
	docker compose up --build
