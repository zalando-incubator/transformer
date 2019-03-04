🚢 Versioning
=============

We use SemVer_ for versioning Transformer.

.. _SemVer: http://semver.org/

All user-facing changes are tracked in our :ref:`changelog`.

Only the most recent version is supported: bugs in *older* releases are
unlikely to be fixed if they don't exist in the most recent release.

For all available releases, see the `releases page`_.

.. _releases page: https://github.com/zalando-incubator/Transformer/releases

Release process
---------------

.. warning::

   This section only describes the current process, which is planned to change
   soon. See :issue:`28` for details.

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

Update the changelog
''''''''''''''''''''

Releasing a new version requires updating the :ref:`changelog` file.
Assuming the current stable version is ``vA.B.C`` and new version is
``vX.Y.Z``, you need to:

- rename the current *Unreleased* section as "vX.Y.Z",

- create a new, empty *Unreleased* section on top,

- update the diff links accordingly.

This is summarized by this patch:

.. code-block:: diff

     Unreleased
     ==========

     - Diff__.
   +
   + __ https://github.com/zalando-incubator/transformer/compare/vX.Y.Z...HEAD
   +
   + .. _vX.Y.Z:
   +
   + vX.Y.Z
   + ======
   +
   + - Release date: YYYY-MM-DD HH:MM
   + - Diff__.

   - __ https://github.com/zalando-incubator/transformer/compare/vA.B.C...HEAD
   + __ https://github.com/zalando-incubator/transformer/compare/vA.B.C...vX.Y.Z

Don't forget to **update the release date!**

You can then open a pull-request with these changes and get it merged before
proceeding to the next step.

Trigger a release via Travis
''''''''''''''''''''''''''''

New releases of Transformer are automatically published to PyPI_ by Travis when
one of the maintainers publishes a new version tag on the ``master`` branch::

   $ git checkout master     # Make sure you're not on a feature branch.
   $ git pull origin master  # Make sure your repository is fresh.
   $ git tag -s vX.Y.Z       # Open your editor to write the release note.
   $ git push --tags         # Propagate the tag to GitHub.

.. _PyPI: https://pypi.org/project/har-transformer/

The contents of the release note should **include the most recent changelog
section**.
Do not use the output of ``git log`` for that purpose: it is usually much less
readable than our curated changelog.
However, you should strip all Sphinx-specific markup from the changelog section
you reuse, as they will not be rendered properly outside of Sphinx.
