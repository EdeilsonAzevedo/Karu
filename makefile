.PHONY: test lint format check-format

run:
	poetry run python manage.py runserver
test:
	poetry run pytest -vv --tb=short --cov=apps --cov-report=term-missing --cov-report=html
lint:
	poetry run ruff check apps

format:
	poetry run ruff format apps
	poetry run ruff check --fix apps

check:
	poetry run ruff check apps
	poetry run ruff format --check apps

ci: check-format lint test