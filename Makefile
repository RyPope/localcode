.DEFAULT_GOAL := help
PY := backend/.venv/bin

help: ## Show this help
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Build and start localcode at http://localhost:4173
	docker compose up -d --build

down: ## Stop localcode (your data volume is kept)
	docker compose down

logs: ## Follow app and runner logs
	docker compose logs -f

setup: ## Install local dev dependencies (Python venv + web node_modules)
	python3.12 -m venv backend/.venv
	$(PY)/pip install -e 'backend[dev]'
	npm --prefix web ci

test: test-backend test-web test-runner ## Run every test suite

test-backend: ## Backend unit tests
	$(PY)/pytest -q backend

test-runner: ## Runner tests (inside the pinned toolchain image)
	docker build --target test -t localcode-runner-test runner
	docker run --rm --init localcode-runner-test

test-web: ## Web typecheck, unit tests and production build
	npm --prefix web run typecheck
	npm --prefix web test
	npm --prefix web run build

lint: ## Lint and format-check everything
	$(PY)/ruff check backend runner
	$(PY)/ruff format --check backend runner
	npm --prefix web run lint
	npm --prefix web run format:check

format: ## Auto-format everything
	$(PY)/ruff check --fix backend runner
	$(PY)/ruff format backend runner
	npm --prefix web run format

dev-web: ## Vite dev server on :5173 (proxies /api to a running stack)
	npm --prefix web run dev

api-types: ## Regenerate web/openapi.json and the web client's TypeScript types from the API
	$(PY)/python -m localcode.tools.openapi web/openapi.json
	npm --prefix web run api-types

smoke: ## End-to-end smoke test against the running stack
	$(PY)/python -m localcode.tools.smoke

update: ## Re-download sources and rebuild problem data (your progress is kept)
	docker compose exec app python -m localcode.importer

validate-cases: ## Maintainers: regenerate the excluded test-case list (slow)
	docker compose up -d --scale runner=3
	docker compose exec -T app python -m localcode.tools.validate_cases /data/excluded_cases.json \
		--runners $$(docker compose ps --format '{{.Name}}' runner | sed 's#.*#http://&:8080#')
	docker compose cp app:/data/excluded_cases.json backend/localcode/data/excluded_cases.json
	docker compose up -d --scale runner=1

.PHONY: help up down logs setup test test-backend test-runner test-web lint format dev-web api-types smoke update validate-cases
