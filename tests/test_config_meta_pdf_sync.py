import re
from pathlib import Path
import yaml


def _parse_pdf_docs(models):
    pages = sorted(Path('docs').glob('pdf_page_*.txt'))
    # regex capturing lines that may have an optional leading line-number followed by the real index
    val_re = re.compile(r"^\s*(?:\d+\s+)?(\d+)\s+.*?\s+(0x[0-9A-Fa-f]+|[0-9]{1,3}|FF|ff)\s*$")
    per_model = {m: {} for m in models}

    def detect_models(text):
        u = text.upper()
        found = set()
        if 'PRTHW' in u or 'PRT HW' in u or 'PRT-HW' in u:
            found.add('prt-hw')
        if 'WI-FI DT/DT-E/PRT/PRT-E' in u or 'DT/DT-E/PRT/PRT-E' in u:
            found.update(['dt', 'dt-e', 'prt', 'prt-e'])
        if 'DCB FOR PRTHW' in u or 'MODEL (PRTHW' in u:
            found.add('prt-hw')
        if 'DCB FOR DT/DT-E' in u or 'MODEL (DT/DT-E' in u:
            found.update(['dt', 'dt-e'])
        return sorted(found)

    for pf in pages:
        txt = pf.read_text(encoding='utf-8')
        page_models = detect_models(txt)
        if not page_models:
            # fallback: if the page contains the generic heading, assume common models
            if 'DT/DT-E/PRT/PRT-E' in txt.upper():
                page_models = ['dt', 'dt-e', 'prt', 'prt-e']
        if not page_models:
            continue
        for ln in txt.splitlines():
            m = val_re.match(ln)
            if not m:
                continue
            idx = int(m.group(1))
            val = m.group(2)
            if val.upper() == 'FF':
                v = 255
            elif val.lower().startswith('0x'):
                v = int(val, 16)
            else:
                v = int(val)
            if 0 <= idx <= 35:
                for model in page_models:
                    per_model[model][idx] = v
    return per_model


def test_config_meta_matches_pdf_transcription():
    # models present in config.yml we care about
    models = ['prt', 'dt', 'dt-e', 'prt-e', 'prt-hw']
    cfg = yaml.safe_load(Path('heatmiserv3/config.yml').read_text())
    parsed = _parse_pdf_docs(models)

    # Build defaults meta (if present) and use it as fallback for per-model meta
    defaults_meta_raw = cfg.get('defaults', {}).get('meta', {}) if isinstance(cfg.get('defaults'), dict) else {}

    def _build_effective_meta(model_key):
        model_meta_raw = cfg.get(model_key, {}).get('meta', {}) if isinstance(cfg.get(model_key), dict) else {}
        effective = {}
        # Start with defaults
        for k, v in defaults_meta_raw.items():
            try:
                ik = int(k)
            except Exception:
                continue
            effective[ik] = v
        # Overlay model-specific
        for k, v in model_meta_raw.items():
            try:
                ik = int(k)
            except Exception:
                continue
            effective[ik] = v
        return effective

    for model in models:
        effective_meta = _build_effective_meta(model)
        assert isinstance(effective_meta, dict), f"model {model} missing meta in config.yml"
        for idx, pdf_val in sorted(parsed.get(model, {}).items()):
            entry = effective_meta.get(idx)
            assert entry is not None, f"model {model} missing index {idx} in config meta"
            cfg_val = entry['default']
            assert cfg_val == pdf_val, (
                f"Mismatch for model={model} index={idx}: config={cfg_val} != pdf={pdf_val}"
            )
