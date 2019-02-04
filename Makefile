SRC := $(shell find transformer/ -name '*.py' ! -name 'test_*' ! -name 'builders_*' )

.PHONY: all
all: test

.PHONY: configure
configure: .configured

.configured: pyproject.toml poetry.lock
	poetry install
	touch .configured

.PHONY: test
test: configure
	poetry run pytest --cov-config .coveragerc --cov-report xml --cov=. transformer/

.PHONY: lint
lint: configure
	poetry run black --diff --check $(SRC)
	poetry run pylint $(SRC)
