Functional tests for Transformer's CLI.

They run in a special virtualenv where the `transformer` package, created
by `poetry build`, is installed.

This directory contains:
  - a Makefile,
  - [Pytest][] scripts.

[Pytest]: https://docs.pytest.org/en/latest/

The Makefile sets up the appropriate environment: it builds transformer,
creates a virtualenv, installs transformer in that virtualenv, and finally runs
[Pytest][] in that environment.
