Functional tests for Transformer's CLI.

They run in a special virtualenv where the `transformer` package, created
by `poetry build`, is installed.

This directory contains a `run.py` script, and other scripts with a name
starting with `test-`.

The `run.py` script sets up the appropriate environment: it builds transformer,
creates a virtualenv, installs transformer in that virtualenv, and finally runs
the other `test-*` scripts in that environment.

`test-*` scripts can be stored in arbitrary subdirectories.

`run.py` will exit with 0 if (and only if) at least one test was run and all
of them were successful.
