.PHONY: help lint

help:
	@echo "Available commands:"
	@echo "  help         Show this help message"
	@echo "  lint         Execute the linters and code formatters (black, isort, flake8)"

lint:
	black . --config=pyproject.toml
	isort . --profile black
	flake8 . --config=setup.cfg
