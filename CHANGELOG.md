# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
## [Unreleased]
-->

## [1.0.1] - 2019-02-12

### Fixed

- Fix `transformer` command-line crash due to a missing version identifier. (#17)
- Publish development releases to PyPI for every merge to the `master` branch. (#17)

## [1.0.0] - 2019-02-11

### Added

- Plugin contracts aiming to eventually deprecate OnTaskSequence:
  OnTask, OnScenario, OnPythonProgram.
- Transformer can now be called using a `transformer` script installed by
  `pip`, or via `python -m transformer`. (#7)
- Transformer is now published to PyPI as [`har-transformer`] (it looks like
  the name `transformer` is already taken, unsurprisingly). (#3)
- Remove Pipenv completely; everything uses [Poetry] now.
- Add a general `transformer.plugins.contracts.Plugin` type covering all more
  specialized plugin types, like `OnTask`, `OnTaskSequence`, etc.

[har-transformer]: https://pypi.org/project/har-transformer
[Poetry]: https://github.com/sdispater/poetry

### Changed

- The plugin `sanitize_headers` is now used by default.
- Open-sourcing of this project in https://github.com/zalando-incubator.
- `transformer.plugins.Plugin` is renamed
  `transformer.plugins.contracts.OnTaskSequence`.

[Unreleased]: https://github.com/zalando-incubator/transformer/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/zalando-incubator/transformer/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zalando-incubator/transformer/compare/f842c4163e037dc345eaf1992187f58126b7d909...v1.0.0
