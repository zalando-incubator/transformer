.. _changelog:

🕰 Changelog
************

All notable changes to this project are documented in this file.

The format is based on `Keep a Changelog`_, and this project adheres to
`Semantic Versioning`_.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html

.. contents::
   :local:
   :depth: 1

.. _unreleased:

Unreleased
==========

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.0.2...HEAD

Added
-----

:attr:`transformer.request.Request.name`
   Controls `Locust's URL grouping`_.
   Its default value is :attr:`~transformer.request.Request.url`, which usually
   does the right thing and ensures retrocompatibility.
   Thank you :user:`xinke2411` for this addition! (:pr:`34`)

.. _Locust's URL grouping: https://docs.locust.io/en/stable/writing-a-locustfile.html
   #grouping-requests-to-urls-with-dynamic-parameters

:class:`transformer.python.ExpressionView`
   An :class:`~transformer.python.Expression` that wraps a non-Expression
   (e.g. a :class:`~transformer.request.Request` instance), similarly to how
   :class:`~transformer.python.Standalone` is a
   :class:`~transformer.python.Statement` that wraps an Expression.
   Helps manipulating non-syntax tree objects as part of the syntax tree.
   (:pr:`33`)

**Functional test suite**
   A functional test suite in :file:`functional-tests/` (with only one simple
   test for starting).
   It is part of ``make test`` and can be run alone with ``make functest``.
   (:pr:`37`)

Changed
-------

- When processing HAR requests with the :mimetype:`application/json` MIME type,
  Transformer no longer uses the ``params`` field as a replacement for a
  missing ``text`` field.
  This was a mitigation for a bug in a different, Zalando-internal tool.
  (:pr:`33`)

- The documentation has migrated: from Markdown files (some in the repository,
  some in the GitHub wiki) and loosely Markdown-formatted docstrings in the
  code, to a Sphinx_ site under :file:`docs/` and rich docstrings.
  Most Markdown files have been converted to reStructuredText_ in the process,
  including this changelog. (:pr:`38`)

- The documentation is no longer accessible from the GitHub wiki, but is now
  hosted by Read The Docs at https://transformer.readthedocs.io. (:pr:`43`)

.. _Sphinx: http://www.sphinx-doc.org
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext

Fixed
-----

- A bug in the conversion between :class:`~transformer.task.Task` and
  :class:`~transformer.task.Task2` makes Transformer ignore all changes made by
  plugins to :attr:`~transformer.task.Task2.request`.
  Thank you :user:`xinke2411` for reporting this! (:pr:`33`)

- Lack of functional tests made us miss the fact that Transformer started
  crashing when run on the HAR files from the :file:`examples/` directory.
  Transformer was fixed and the appropriate unit and functional tests were
  added. (:pr:`44`)

Removed
-------

:meth:`transformer.task.Task.as_locust_action`
   As part of the merge between :class:`~transformer.task.Task` and
   :class:`~transformer.task.Task2` (:issue:`11`).

   :meth:`~transformer.task.Task.as_locust_action` generates locustfile code as
   a string, which is made obsolete by the :mod:`transformer.python` syntax
   tree framework. (:pr:`33`)

:mod:`transformer.decision`
   Unused API for combining a boolean (the decision itself) with a string
   (a user-friendly explanation for that decision). (:pr:`36`)

.. _v1.0.2:

v1.0.2
======

- Release date: 2019-02-22 11:38 CET
- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.0.1...v1.0.2

Added
-----

:func:`transformer.dump` & :func:`transformer.dumps`
   Named by analogy with :func:`json.dump` and :func:`json.dumps`, these
   high-level functions should be all most users need to know about the
   Transformer API.
   They convert lists of :term:`scenario` paths and plugins into a locustfile.

   They will replace :func:`~transformer.transform.transform`, which requires
   more familiarity with Transformer's internals. (:pr:`14`)

:func:`transformer.locust.locustfile_lines`
   Similar to :func:`~transformer.locust.locustfile` but returns an
   :class:`~typing.Iterator` :any:`str` over lines, instead of a unique string
   containing the full locustfile contents.

   This design allows for more flexibility in
   :func:`~transformer.dump`/:func:`~transformer.dumps` and should result in
   smaller memory usage for huge locustfiles. (:pr:`14`)

Hooks for :term:`OnTask`, :term:`OnScenario`, :term:`OnPythonProgram`
   Preliminary support for new-generation plugins. (:pr:`25`)

Changed
-------

- The :func:`~transformer.dump`, :func:`~transformer.dumps`, and
  :func:`~transformer.transform.transform` functions by default use the
  *Sanitize Headers* plugin, even if users don't provide it in the plugin list.

  This is because the resulting locustfile would almost certainly be broken
  without this plugin.
  Users can still opt-out from default plugins by passing the
  ``with_default_plugins=False`` keyword-argument to these functions. (:pr:`14`)

Deprecated
----------

:func:`transformer.transform.transform`
   Replaced with :func:`~transformer.dump` and :func:`~transformer.dumps`, see
   above. (:pr:`14`)

:func:`transformer.locust.locustfile`
   Replaced with :func:`~transformer.locust.locustfile_lines`, see above.
   (:pr:`14`)

.. _v1.0.1:

v1.0.1
======

- Release date: 2019-02-12 13:20 CET
- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.0.0...v1.0.1

Fixed
-----

- Fix a crash of the ``transformer`` command-line tool due to a missing version
  identifier. (:pr:`17`)

- Publish development releases to PyPI for every merge in the ``master``
  branch. (:pr:`17`)

v1.0.0
======

- Release date: 2019-02-12 10:30 CET
- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/
   f842c4163e037dc345eaf1992187f58126b7d909...v1.0.0

Added
-----

har-transformer_ on PyPI
  It looks like the package name ``transformer`` is already taken,
  unsurprisingly. (:pr:`3`)

.. _har-transformer: https://pypi.org/project/har-transformer

Command-line entrypoint
   Transformer can now be called using the ``transformer`` script installed by
   pip, or via ``python -m transformer``. (:pr:`7`)

Specification of :term:`OnTask`, :term:`OnScenario`, :term:`OnPythonProgram`
   Aiming at eventually deprecating *OnTaskSequence*.

:data:`transformer.plugins.contracts.Plugin`
   Represents an instantiated plugin.

Changed
-------

- This project is open-sourced in https://github.com/zalando-incubator.
  The git history prior that is removed per company policy.

- ``transformer.plugins.Plugin`` is renamed
  :class:`transformer.plugins.contracts.OnTaskSequence`.

Removed
-------

Pipenv_
  In favor of Poetry_.

.. _Pipenv: https://pipenv.readthedocs.io/
.. _Poetry: https://github.com/sdispater/poetry
