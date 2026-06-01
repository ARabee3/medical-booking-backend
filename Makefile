.PHONY: install run test migrate superuser lint format shell

# Default Python interpreter
PYTHON ?= python3

# Install dependencies for local development
install:
	$(PYTHON) -m pip install -r requirements/local.txt

# Run development server
run:
	$(PYTHON) manage.py runserver

# Run all tests
pytest:
	pytest

# Run Django tests
test:
	$(PYTHON) manage.py test

# Apply database migrations
migrate:
	$(PYTHON) manage.py migrate

# Create a superuser
superuser:
	$(PYTHON) manage.py createsuperuser

# Make migrations
makemigrations:
	$(PYTHON) manage.py makemigrations

# Check for common issues
check:
	$(PYTHON) manage.py check

# Run development shell
shell:
	$(PYTHON) manage.py shell

# Seed demo data (once implemented)
seed:
	$(PYTHON) manage.py seed_demo_data

# Run Black code formatter
format:
	black .

# Check formatting (dry-run)
format-check:
	black --check .

# Run flake8 linter
lint:
	flake8 apps/ config/ shared/
