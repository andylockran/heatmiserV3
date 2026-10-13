# Contributing to heatmiserv3

Thank you for considering contributing to `heatmiserv3`! This library provides an interface for Heatmiser thermostats communicating over the Heatmiser V3 protocol.

## Maintainer Note & Hardware Access

As noted in [ADR 0002](docs/adrs/0002-logic-led-development.md), active maintainers currently lack access to physical thermostats. Development is guided by:
1. Strict adherence to the official [Heatmiser V3 Protocol specification](heatmiser_v3_protocol_3.9.pdf).
2. Deterministic unit tests and test doubles (`FakeSerial`, `FakeUH1`).
3. Feedback and test results from community members with active physical hardware installations.

If you are interested in taking over maintenance or co-maintaining the project under a dedicated organization, please get in touch or open an issue!

## Development Setup

The project uses [uv](https://docs.astral.sh/uv/) for fast, deterministic dependency management and packaging.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/andylockran/heatmiserv3.git
   cd heatmiserv3
   ```

2. **Install `uv`** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

## Running Tests & Linting

Before submitting changes, ensure all tests pass and code conforms to linting standards:

```bash
# Run tests with coverage report
uv run pytest --cov=heatmiserv3 --cov-report=term-missing

# Run lint checks
uv run flake8

# Test package build
uv build
```

We enforce a minimum 90% test coverage threshold on the core library.

## Architecture & Decisions

When making non-trivial architectural changes or adopting new conventions, please record an Architecture Decision Record in `docs/adrs/` following the existing format (see [ADR 0001](docs/adrs/0001-record-architecture-decisions.md) and [ADR 0003](docs/adrs/0003-modernize-tooling-resilience-and-coverage.md)).

## Pull Request Guidelines

1. Create a descriptive feature branch (e.g. `feature/my-feature` or `fix/issue-description`).
2. Add unit tests for any new functionality or bug fixes.
3. Verify backward compatibility: ensure existing public interfaces (`HeatmiserThermostat`, `TM1Thermostat`, `HeatmiserUH1`) remain stable for consumers like Home Assistant.
4. Keep commit messages clear and descriptive following Conventional Commits format.
