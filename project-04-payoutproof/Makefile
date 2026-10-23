.PHONY: setup run test check

PYTHON ?= python3

setup:
	$(PYTHON) -m compileall -q payoutproof

run:
	$(PYTHON) -m payoutproof

test:
	$(PYTHON) -m unittest discover -s tests -v

check: test
	$(PYTHON) -m compileall -q payoutproof tests
