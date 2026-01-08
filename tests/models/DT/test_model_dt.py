"""Tests for model DT (from protocol PDF)."""
import pytest
import yaml
import importlib_resources


def _load_config():
    cfg_path = importlib_resources.files('heatmiserv3').joinpath('config.yml')
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    # Synthesize `keys` from `meta` for backward compatibility in tests
    for model_key, model_cfg in list(cfg.items()):
        if model_key == 'defaults' or not isinstance(model_cfg, dict):
            continue
        if isinstance(model_cfg.get('keys'), dict):
            continue
        meta = model_cfg.get('meta')
        if not isinstance(meta, dict):
            continue
        keys = {}
        for k, v in meta.items():
            try:
                idx = int(k)
            except Exception:
                continue
            if isinstance(v, dict):
                keys[idx] = v.get('name')
            else:
                keys[idx] = v
        model_cfg['keys'] = keys

    return cfg


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
