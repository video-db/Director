# Detect the shell (sh, bash, etc.)
SHELL := $(shell echo $$SHELL)

# Default target
.DEFAULT_GOAL := help

# Variables
BACKEND_DIR := backend
VENV_DIR := venv

# Phony targets
.PHONY: help venv init-sqlite-db install test lint run

help:
	@echo "--------------- HELP ---------------"
	@echo "To create virtual environment: make venv"
	@echo "To initialize sqlite database: make init-sqlite-db"
	@echo "To initialize turso database: make init-turso-db"
	@echo "To initialize postgres database: make init-postgres-db"
	@echo "To install dependencies: make install"
	@echo "To run tests: make test"
	@echo "To run lint: make lint"
	@echo "To start the backend server: make run"
	@echo "------------------------------------"

init-sqlite-db:
	source $(VENV_DIR)/bin/activate && \
	python director/db/sqlite/initialize.py

init-postgres-db:
	source $(VENV_DIR)/bin/activate && \
	python director/db/postgres/initialize.py


install:
	source $(VENV_DIR)/bin/activate && \
	pip install -r requirements.txt && \
	pip install -r requirements-dev.txt

test:
	source $(VENV_DIR)/bin/activate && \
	pytest -v -W ignore::DeprecationWarning

lint:
	source $(VENV_DIR)/bin/activate && \
	ruff check .

run:
	source $(VENV_DIR)/bin/activate && \
	python director/entrypoint/api/server.py
