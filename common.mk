# This file is included in both Makefile.local & Makefile.ci.

SRC := $(shell find transformer/ -name '*.py' ! -name 'test_*' ! -name 'builders_*' )
DIST := pyproject.toml poetry.lock

# Runs "poetry install" if pyproject.toml or poetry.lock have changed.
.PHONY: configure
configure: .make/configure

.make/configure: $(DIST)
	poetry install
	mkdir -p .make && touch .make/configure

# Runs pytest with coverage reporting.
.PHONY: unittest
unittest: configure
	poetry run pytest --failed-first --cov-config .coveragerc --cov-report xml --cov=. transformer/

.PHONY: functest
functest: configure
	$(MAKE) -C functional-tests/

.PHONY: functest
test: unittest functest

.PHONY: lint
lint: black flake8

.PHONY: flake8
flake8: configure
	poetry run flake8 $(SRC)
