# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2021-01-25

### Changed

- Use pytest and pytest-cov as stactools does ([#16](https://github.com/stactools-packages/planet/pull/15)).

PR [#15](https://github.com/stactools-packages/planet/pull/15) makes the following related changes:

- For CI, always install from requirements-dev.txt before installing stactools-planet.
- Pin stactools to 0.2.3 in requirements.txt for CI purposes.
- Remove Python 3.6 from project classifiers and from the CI matrix.
- Unpin stactools in setup.cfg.
- Pin yapf to 0.32.0 for CI purposes and add blank lines before class methods, the new yapf default.
