# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for direct local RS485 serial device connections via `dev` parameter on `HeatmiserUH1` (issue #84).
- Comprehensive unit test suite for `HeatmiserThermostat` covering DCB parsing, temperature units, sensor options, program modes, and setters.
- Comprehensive unit test suite for `HeatmiserUH1` covering connection lifecycle, local serial devices, integer/string port parsing, and exception safety.
- Test doubles and fixtures (`FakeSerial`, `FakeUH1`) for simulation without physical hardware.
- Test coverage gate configured in `pyproject.toml` (enforcing >= 90% test coverage; reaching >95%).
- Standard `.flake8` configuration file for codebase styling.
- ADR 0003: Modernize tooling, resilience, and test coverage.
- Developer and contributor documentation (`CONTRIBUTING.md`).

### Fixed
- Fixed critical logic bug in `heatmiserv3/heatmiser.py` where temperature boundary checks (`set_target_temp`, `set_frost_protect_temp`, `set_floormax_temp`) used inverted chained comparisons (`17 < frost_temp < 7`) that could never evaluate to `True`.
- Fixed Python 3 bug in `heatmiserv3/connection.py` where `e.message` was accessed on `Exception`, causing an `AttributeError`.
- Fixed `HeatmiserUH1` port handling when port is passed as integer rather than string.
- Fixed `HeatmiserUH1.reopen(force=True)` to safely close existing serial port before creating a new connection.
- Fixed missing `self.uh1` assignment on `HeatmiserThermostat.__init__`, resolving `AttributeError` on serial reconnect.
- Fixed unhandled `UnboundLocalError` in `_hm_send_msg` when serial exceptions occur.
- Replaced library-level `logging.basicConfig()` with idiomatic module-level `logging.getLogger(__name__)`.
- Fixed `CODEROWNERS` typo, renaming to `.github/CODEOWNERS`.
- Fixed broken link to ADR documentation in `README.md` and consolidated canonical records under `docs/adrs/`.

### Changed
- Modernized packaging and build tooling: standardized on PEP 621 `pyproject.toml` with `hatchling` backend and `uv` package management; removed deprecated `setup.py`, `setup.cfg`, and `MANIFEST`.
- Hardened CI/CD workflows by pinning all external GitHub Actions to immutable full 40-character commit SHAs with inline semantic version comments.
- Updated `.devcontainer/devcontainer.json` to bootstrap with `uv sync`.

## [2.0.6] - 2026-01-07
- Updated packaging and lockfiles.
- Removed pytest from runtime dependencies.
