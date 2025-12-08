"""Tests for model PRT (from protocol PDF)."""
import pytest
import yaml
import importlib_resources


def _load_config():
    cfg_path = importlib_resources.files('heatmiserv3').joinpath('config.yml')
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def test_prt_has_config_and_keys(thermostat):
    # `prt` is present in the repository config.yml; use existing thermostat fixture
    cfg = _load_config()
    assert 'prt' in cfg
    keys = cfg['prt'].get('keys')
    assert isinstance(keys, dict)
    # confirm DCB mapping exists for index 0..35
    for i in range(0, 36):
        assert i in keys
