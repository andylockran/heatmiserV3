"""Tests for model PRT-HW (from protocol PDF)."""
import pytest
import yaml
import importlib_resources


def _load_config():
    cfg_path = importlib_resources.files('heatmiserv3').joinpath('config.yml')
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def test_prt_hw_has_config_or_skip():
    cfg = _load_config()
    model_key = 'prt-hw'
    if model_key not in cfg:
        pytest.skip(f"No config for model '{model_key}' in config.yml")
    keys = cfg[model_key].get('keys')
    assert isinstance(keys, dict)
