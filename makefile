.PHONY: test lint format check-format

run:
	poetry run python manage.py runserver
test:
	poetry run pytest -vv --tb=short --create-db --cov=apps --cov-report=term-missing --cov-report=html
lint:
	poetry run ruff check apps

format:
	poetry run ruff format apps
	poetry run ruff check --fix apps

check:
	poetry run ruff check apps
	poetry run ruff format --check apps

ci: check-format lint test

populate_db:
	poetry run python manage.py populate_db --patients 30 --records 80 
