"""Tests for model DT (from protocol PDF)."""
import pytest
import yaml
import importlib_resources


def _load_config():
    cfg_path = importlib_resources.files('heatmiserv3').joinpath('config.yml')
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def test_dt_has_config_or_skip():
    cfg = _load_config()
    model_key = 'dt'
    if model_key not in cfg:
        pytest.skip(f"No config for model '{model_key}' in config.yml")
    # basic assertions if present
    keys = cfg[model_key].get('keys')
    assert isinstance(keys, dict)
    # ensure at least address/index 11 exists
    assert 11 in keys
