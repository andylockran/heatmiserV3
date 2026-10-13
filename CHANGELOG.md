# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2026-10-13

### Added
- Specialized `TM1Thermostat` driver supporting time switch channels, countdown timers, override modes, and 5/2 & 7-day switching schedules.
- Specialized `PRTHWThermostat` driver supporting dual-channel heating and hot water boost regulation.
- Thread-safe bus arbiter with command pacing (`BUS_INTER_COMMAND_DELAY`), recovery pause (`BUS_RECOVERY_PAUSE`), and serial transaction mutex (`transact()`).
- High-performance DCB telemetry caching with configurable TTL (`DEFAULT_CACHE_TTL = 3.0`), automatic cache invalidation on write commands, and forced wire refresh (`read_dcb(force=True)`).
- Full suite of grouped convenience helpers for setpoint, frost protection, keylock, run mode, holiday hours, and temperature hold.
- Architecture Decision Records ADR 0001 (ADRs), ADR 0002 (Logic-Led Dev), ADR 0003 (Tooling & Coverage), and ADR 0004 (Bus Timing & Caching).
- Interactive multi-thermostat Whole-Home Digital Twin demo with floorplan visualization, Home Assistant Lovelace telemetry cards, and multi-button tactile chord helpers (`docs/twin.html`).
- Official Sphinx ReadTheDocs documentation suite with MyST Markdown, multi-language CRC-16 references (Python, C, TypeScript, Rust, Go), and API autodoc (`docs/conf.py`, `.readthedocs.yaml`).
- Support for direct local RS485 serial device connections via `dev` parameter on `HeatmiserUH1` (issue #84).
- CI workflow testing matrix expanded to include Python 3.14 and Python 3.15.

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
- Fixed temperature quantization to 0.5°C increments matching physical PRT-1 LCD hardware behavior.
- Fixed literal `&bull;` rendering in digital twin room badges.

### Changed
- Modernized packaging and build tooling: standardized on PEP 621 `pyproject.toml` with `hatchling` backend and `uv` package management; removed deprecated `setup.py`, `setup.cfg`, and `MANIFEST`.
- Hardened CI/CD workflows by pinning all external GitHub Actions to immutable full 40-character commit SHAs with inline semantic version comments.
- Updated `.devcontainer/devcontainer.json` to bootstrap with `uv sync`.
- Required Python `>=3.10,<4`.

## [2.0.6] - 2026-01-07
- Updated packaging and lockfiles.
- Removed pytest from runtime dependencies.
