.PHONY: setup run test check

PYTHON ?= python3

setup:
	$(PYTHON) -m compileall -q coldchain

run:
	$(PYTHON) -m coldchain

test:
	$(PYTHON) -m unittest discover -s tests -v

check: test
	$(PYTHON) -m compileall -q coldchain tests
