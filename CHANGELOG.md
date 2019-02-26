# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased][]

### Added

  - `transformer.request.Request.name`: This attribute is default set as `Request.url`, 
  users can change `Request.name` in `OnTask` plugin. If `Request.name` is changed, 
  the locust request name argument will changed to `Request.name`.  (#32)

## [1.0.2] - 2019-02-21

### Added

  - `transformer.transform.{dump,dumps}`: Similar to `json.{dump,dumps}`, these
  high-level functions should be all most users need to know about Transformer.
  They convert lists of scenario paths and plugins into a final locustfile.
  They will replace the `transform` function, which requires more familiarity
  with Transformer's internals. (#14)
  - `transformer.locust.locustfile_lines`: Similar to `locustfile` but returns
  an iterator over lines (as strings) instead of a string containing the full
  locustfile. This design allows for more flexibility in `dump`/`dumps` and
  should result in smaller memory usage for huge locustfiles. (#14)
  - Preliminary support for new-generation plugins. (#25)

### Changed

  - The `dump`, `dumps`, and `transform` functions by default use the
  `sanitize_headers` plugin even if users don't provide it in the plugin list.
  This is because the resulting locustfile would almost certainly be broken
  without these plugins. Users can still opt-out from these default plugins
  by passing the keyword-argument `with_default_plugins=False` (e.g. if they
  implemented their own version). (#14)

### Deprecated

  - `transformer.transform.transform` (#14)
  - `transformer.locust.locustfile` (#14)

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

  - Open-sourcing of this project in https://github.com/zalando-incubator.
  - `transformer.plugins.Plugin` is renamed
  `transformer.plugins.contracts.OnTaskSequence`.

[Unreleased]: https://github.com/zalando-incubator/transformer/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/zalando-incubator/transformer/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/zalando-incubator/transformer/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zalando-incubator/transformer/compare/f842c4163e037dc345eaf1992187f58126b7d909...v1.0.0
