# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - TBD

### Changed

- Use pytest and pytest-cov as stactools does.
- For CI, always install from requirements-dev.txt before installing stactools-planet.
- Pin stactools to 0.2.3 in requirements-dev.txt for CI purposes.
- Remove Python 3.6 from project classifiers and from the CI matrix.
- Unpin stactools in setup.cfg.
- Pin yapf to 0.32.0 for CI purposes and add blank lines before class methods, the new yapf default.
