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

.. _v2.0.0:

v2.0.0
======

- Release date: 2022-04-29 16:07

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.3.0...v2.0.0

Fixed
-----

UTF-8-encoded locustfiles are properly opened on Windows.
Thank you :user:`rishisharma108`, :user:`akshamat`, :user:`JustinRoll`, and :user:`bascr`,
for reporting this issue! (:pr:`74`)

All usages of the word "blacklist" have been replaced with a modern equivalent,
which is a breaking change (hence the new major version) because of some of
these usages were part of the public API (typically keyword argument names).

.. _v1.3.0:

v1.3.0
======

- Release date: 2020-06-18 10:00

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.7...v1.3.0

Added
-----

Generated locustfiles now support both current major versions of Locust
(``<1`` and ``~1``).

.. note::

   Please note that this support will most likely be *only temporary*, so all
   users of Transformer are kindly encouraged to upgrade their Locust (or tell us
   what's blocking them from upgrading).

   Since Transformer follows `semantic versioning`_, dropping support for some
   versions of Locust will only be done in a major Transformer version, most
   likely 2.0 (not yet planned).
   If you rely on a pre-1.0 Locust, you can therefore continue upgrading
   Transformer by following its *minor* updates
   (e.g. ``pip install -U har-transformer=~1``).


.. _v1.2.7:

v1.2.7
======

- Release date: 2020-06-03 10:42

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.6...v1.2.7

Fixed
-----

Feeding a Transformer-generated locustfile to a version of Locust more recent
than `0.99` (May 16, 2020) now displays a more helpful error message suggesting
to use a supported version of Locust.
Previously, users only saw Locust crash on a now-invalid `import` from the
locustfile.
Thank you :user:`TimSC` for reporting this issue! (:pr:`70`)

.. _v1.2.6:

v1.2.6
======

- Release date: 2019-10-18 14:09

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.5...v1.2.6

Any valid plugins that are in a current directory can be used by Transformer without previous installation.
Thank you :user:`jredrejo` for your contribution! (:pr:`63`)

.. _v1.2.5:

v1.2.5
======

- Release date: 2019-09-02 12:00

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.4...v1.2.5

Fixed
-----

The generated scenario classes always inherit from
:class:`~locust.TaskSequence` (instead of a :class:`~locust.TaskSet`) when they
use the `@seq_task` decorator.
Thank you :user:`kbrowns` for reporting this! (:pr:`62`)

.. _v1.2.4:

v1.2.4
======

- Release date: 2019-05-17 15:46

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.3...v1.2.4

Changed
-------

No functional changes in Transformer! Moved tests away from the Transformer package
and refactored them to use common fixtures.


.. _v1.2.3:

v1.2.3
======

- Release date: 2019-05-03 16:03

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.2...v1.2.3

Changed
-------

No functional changes in Transformer! Fixed: pushing tagged releases to Github.

.. _v1.2.2:

v1.2.2
======

- Release date: 2019-05-03 10:45

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.1...v1.2.2

Changed
-------

No functional changes in Transformer! Fixed the formatting of this Changelog and configured Travis to automatically
push tagged releases to GitHub.

.. _v1.2.1:

v1.2.1
======

- Release date: 2019-05-02 17:02

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.2.0...v1.2.1

Changed
-------

Added support for http PATCH method.

.. _v1.2.0:

v1.2.0
======

- Release date: 2019-05-02 11:52

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.1.3...v1.2.0

Changed
-------

:class:`Request <transformer.request.Request>`'s :attr:`headers <transformer.request.Request.headers>`
are now stored in a case-insensitive dictionary, making the implementation compatible
with the :mod:`requests` library (used by Locust).

.. _v1.1.3:

v1.1.3
======

- Release date: 2019-04-26 16:44

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.1.2...v1.1.3

Changed
-------

Denylisting mechanism now opens the `.urlignore` file once per execution of the program,
instead of once per :class:`Request <transformer.request.Request>`.

.. _v1.1.2:

v1.1.2
======

- Release date: 2019-04-25 14:49

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.1.1...v1.1.2

Added
-----

:attr:`transformer.request.Request.har_entry`
   This new read-only property contains the entry as recorded in a HAR file,
   corresponding to the specific :class:`Request <transformer.request.Request>` object.
   As requested by :user:`xinke2411` (:issue:`35`)

.. _v1.1.1:

v1.1.1
======

- Release date: 2019-03-11 16:03

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.1.0...v1.1.1

Changed
-------

A header in all generated HAR files now contains the version of Transformer and its new repository's URL.

.. _v1.1.0:

v1.1.0
======

- Release date: 2019-03-06 17:06

- Diff__.

__ https://github.com/zalando-incubator/transformer/compare/v1.0.2...v1.1.0

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

- The release process has changed: A new PyPI release is now published for each
  commit to the `master` branch.
  This should prevent situations where the documentation advertises features
  not yet released. (:pr:`46`)

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
