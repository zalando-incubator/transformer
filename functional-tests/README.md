Functional tests for Transformer's CLI.

They run in a special virtualenv where the `transformer` package, created
by `poetry build`, is installed.

This directory contains:
  - a Makefile,
  - Python scripts with a name starting with `test_`.

The Makefile sets up the appropriate environment: it builds transformer,
creates a virtualenv, installs transformer in that virtualenv, and finally runs
the `test_*` scripts with Pytest in that environment.

`test_*` scripts can be stored in arbitrary subdirectories, as long as these
also have a name starting with `test_`.

`make` will exit with 0 if (and only if) at least one test was run and all
of them were successful.
