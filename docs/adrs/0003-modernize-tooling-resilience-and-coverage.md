# 3. Modernize tooling, resilience, and test coverage

Date: 2026-10-12

## Status

Accepted

## Context

The `heatmiserv3` library communicates with physical Heatmiser thermostats (such as PRT, PRT-E, PRT-HW, DT, and TM1) over an RS485 half-duplex serial network or serial-over-IP bridge (UH1). Because physical hardware access is not always available to active maintainers and contributors (per ADR 0002), the repository requires:

1. **Modern and fast tooling**: Consistent dependency and package management using `uv` and PEP 621 (`pyproject.toml` with `hatchling` backend), replacing legacy `setup.py` / `requirements.txt` workflows.
2. **Deterministic hardware-less verification**: Comprehensive test doubles (`FakeSerial`, `FakeUH1`) acting as digital twins that simulate thermostat responses, checksum calculation, and ACK/NACK behavior per the Heatmiser V3 protocol specification.
3. **Defensive runtime validation**: Explicit range checking on user inputs (e.g., target temperatures, frost protection temperatures, floor limits) before serial transmission, and resilient handling of connection/disconnection cycles.
4. **Automated multi-version CI/CD**: Verifying code quality and backward compatibility across supported Python versions (3.10 through 3.14) on every pull request and push.

## Decision

1. **Packaging Single Source of Truth**: `pyproject.toml` is the sole source of truth for build dependencies, packaging metadata, and test tool configuration. Legacy `setup.py` is deprecated in favor of Hatchling build backend.
2. **Defensive Validation**: Fix inverted range check conditions on all thermostat setters (`set_target_temp`, `set_frost_protect_temp`, `set_floormax_temp`) and eliminate Python 2 legacy artifacts (such as `e.message` or uninstantiated `self.uh1`).
3. **High Coverage Test Suite**: Expand unit tests for both `HeatmiserThermostat` and `HeatmiserUH1` using simulated serial mocks to achieve >95% test coverage without requiring physical hardware.
4. **Repository Polish**: Fix naming conventions (`CODEOWNERS`), standardize ADR documentation, update devcontainers to use `uv`, and maintain developer documentation.

## Consequences

- Maintainers and contributors can run test suites deterministically and rapidly using `uv run pytest`.
- Accidental out-of-range commands are rejected safely before reaching serial communication layers.
- The repository is fully aligned with modern Python ecosystem standards while preserving 100% backward compatibility for existing consumers (such as Home Assistant).
