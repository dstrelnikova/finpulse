PROJECT_PATH=app
PYTEST=venv/bin/python -m pytest

.PHONY: fix lint test test-unit test-integration test-coverage

fix:
	autoflake --in-place --recursive $(PROJECT_PATH)
	isort $(PROJECT_PATH)
	black $(PROJECT_PATH)

lint:
	flake8 $(PROJECT_PATH)

test:
	$(PYTEST) tests

test-unit:
	$(PYTEST) -m unit tests/unit

test-integration:
	$(PYTEST) -m integration tests/integration

test-coverage:
	$(PYTEST) --cov=app --cov-report=term-missing --cov-fail-under=70 tests
