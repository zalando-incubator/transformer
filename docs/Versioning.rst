🚢 Versioning
=============

We use SemVer_ for versioning Transformer.

.. _SemVer: http://semver.org/

All user-facing changes are tracked in our :ref:`changelog`.

Only the most recent version is supported: bugs in *older* releases are
unlikely to be fixed if they don't exist in the most recent release.

For all available releases, see the `releases page`_.

.. contents::
   :local:

.. _releases page: https://github.com/zalando-incubator/Transformer/releases

Release process
---------------

Since :issue:`28`, a new release of Transformer is created for each merge in
the ``master`` branch.
This means that every pull request needs to update the following files:

:file:`pyproject.toml`
  Update the ``version`` field.

:file:`docs/Changelog.rst`
  Create a new section describing what changed in the new version.

:file:`docs/conf.py`
  Update the ``version`` and ``release`` fields.

Each step is described in more details in the next sections.

Choose the new version
''''''''''''''''''''''

The identifier of the new release must follow the :samp:`v{X}.{Y}.{Z}` format
(where *X*, *Y*, and *Z* are integers), but the actual values for *X*, *Y* and
*Z* totally depend on what has changed since the previous release.

- When you make **incompatible API changes**, **increment X** and set *Y* and
  *Z* to 0.

- Otherwise, when you **add functionality** in a **backwards-compatible**
  manner, **increment Y** and set *Z* to 0.

- Otherwise, when you make **backwards-compatible bug fixes**, **increment Z**.

In doubt, please refer to SemVer_, which is the source of these guidelines.

Update pyproject.toml
'''''''''''''''''''''

In :file:`pyproject.toml`, update the ``version`` value to ``X.Y.Z``.

.. code-block:: diff

     [tool.poetry]
     name = "har-transformer"
   - version = "A.B.C"
   + version = "X.Y.Z"

Update the Sphinx config
''''''''''''''''''''''''

In :file:`docs/conf.py`, update the ``version`` and ``release`` values:

.. code-block:: diff

     # The short X.Y version
   - version = "A.B"
   + version = "X.Y"
     # The full version, including alpha/beta/rc tags
   - release = "A.B.C"
   + release = "X.Y.Z"

Update the changelog
''''''''''''''''''''

Releasing a new version requires updating the :ref:`changelog` file to tell
users **what has changed** since the last version in **clear, concise and
accessible** terms.
The git history is often not suited for this.

Assuming the current stable version is ``vA.B.C`` and new version is
``vX.Y.Z``, you need to add a new "vX.Y.Z" section at the top of the file, just
after the introduction.
This new section should mention a release date and a GitHub link to observe
the actual code changes since the last release.

This is summarized by this patch:

.. code-block:: diff

    Unreleased
    ==========

    - Diff__.
   +
   +__ https://github.com/zalando-incubator/transformer/compare/vX.Y.Z...HEAD
   +
   +.. _vX.Y.Z:
   +
   +vX.Y.Z
   +======
   +
   +- Release date: YYYY-MM-DD HH:MM
   +- Diff__.

   -__ https://github.com/zalando-incubator/transformer/compare/vA.B.C...HEAD
   +__ https://github.com/zalando-incubator/transformer/compare/vA.B.C...vX.Y.Z

Don't forget to **update the release date!**

Update the Sphinx configuration
'''''''''''''''''''''''''''''''

In :file:`docs/conf.py`, update the ``version`` and ``release`` fields:

.. code-block:: diff

    # The short X.Y version
   -version = '{old_short}'",
   +version = '{new_short}'
    # The full version, including alpha/beta/rc tags
   -release = '{old_v}'
   +release = '{new_v}'
