.PHONY: functest
functest: wheel-in-venv
	env PATH="$(VENV_DIR)/bin:$(PATH)" VIRTUAL_ENV=$(VENV_DIR) \
		pytest --failed-first -v
	rm -rf $(VENV_DIR)

VENV_DIR := $(shell mktemp --directory)

$(VENV_DIR)/bin:
	python3 -m venv --clear $(VENV_DIR)
	env PATH="$(VENV_DIR)/bin:$(PATH)" VIRTUAL_ENV=$(VENV_DIR) \
		pip install --upgrade pytest

.PHONY: venv
venv: $(VENV_DIR)/bin

.PHONY: wheel
wheel:
	cd .. && rm -rf dist/ && poetry build

WHEEL = $(shell find ../dist/ -name "*.whl" -print)

.PHONY: wheel-in-venv
wheel-in-venv: venv wheel
	env PATH="$(VENV_DIR)/bin:$(PATH)" VIRTUAL_ENV=$(VENV_DIR) \
		pip install --upgrade $(WHEEL)
