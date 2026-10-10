PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin
IMAGE ?= task-api:local
PORT ?= 8000

.PHONY: help install lint format typecheck test check build smoke ci run compose-up compose-down clean

help:
	@printf '%s\n' \
	  'install      Create a Python 3.12 virtualenv and install the project' \
	  'lint         Run Ruff checks and confirm formatting' \
	  'format       Apply Ruff formatting and safe fixes' \
	  'typecheck    Run mypy in strict mode' \
	  'test         Run unit and integration tests' \
	  'check        Run lint, typecheck, and test' \
	  'build        Build the Docker image' \
	  'smoke        Run the image and call GET /health' \
	  'ci           Run the same quality gates as the pipeline' \
	  'run          Start the API locally with reload' \
	  'compose-up   Start the API with Docker Compose' \
	  'compose-down Stop the Compose stack' \
	  'clean        Remove caches and the local virtualenv'

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip

install: $(BIN)/python
	$(BIN)/python -m pip install -e ".[dev]"

lint: install
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format: install
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

typecheck: install
	$(BIN)/mypy src tests

test: install
	$(BIN)/pytest

check: lint typecheck test

build:
	docker build --tag $(IMAGE) .

smoke: build
	docker rm -f task-api-smoke >/dev/null 2>&1 || true
	docker run -d --name task-api-smoke -p $(PORT):8000 $(IMAGE)
	@i=0; \
	until $(PYTHON) -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$(PORT)/health')"; do \
	  i=$$((i+1)); \
	  if [ $$i -ge 30 ]; then \
	    docker logs task-api-smoke; \
	    docker rm -f task-api-smoke >/dev/null 2>&1 || true; \
	    exit 1; \
	  fi; \
	  sleep 1; \
	done
	docker rm -f task-api-smoke >/dev/null

ci: check build

run: install
	$(BIN)/uvicorn task_api.main:app --reload --host 127.0.0.1 --port $(PORT)

compose-up:
	docker compose up --build

compose-down:
	docker compose down

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
