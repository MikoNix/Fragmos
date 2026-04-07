import os
import yaml

_MODES_PATH = os.path.join(os.path.dirname(__file__), 'modes.yaml')
_cache: dict | None = None


def get_mode(mode_id: str) -> dict:
    """Return the block-mapping dict for the given mode_id.

    Raises:
        ValueError: if mode_id is not defined in modes.yaml.
    """
    global _cache
    if _cache is None:
        with open(_MODES_PATH, encoding='utf-8') as f:
            _cache = yaml.safe_load(f)['modes']
    mode = _cache.get(mode_id)
    if mode is None:
        available = ', '.join(_cache.keys())
        raise ValueError(f"Unknown mode: {mode_id!r}. Available: {available}")
    return mode
