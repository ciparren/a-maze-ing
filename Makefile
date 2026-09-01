VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

.PHONY: install run debug clean lint lint-strict test

# Creates a local virtualenv the first time it's needed (avoids PEP 668
# "externally-managed-environment" errors on Debian/Ubuntu when installing
# packages).
$(VENV)/bin/python3:
	python3 -m venv $(VENV)

install: $(VENV)/bin/python3
	$(PIP) install -r requirements-dev.txt
	-$(PIP) install vendor/mlx-2.2-py3-none-any.whl

run: $(VENV)/bin/python3
	$(PYTHON) a_maze_ing.py config.txt

debug: $(VENV)/bin/python3
	$(PYTHON) -m pdb a_maze_ing.py config.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache build dist *.egg-info $(VENV)

lint: $(VENV)/bin/python3
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: $(VENV)/bin/python3
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

# Not graded (per the subject) -- convenience target for the pytest suite
# under tests/.
test: $(VENV)/bin/python3
	$(PYTHON) -m pytest
