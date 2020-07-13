import json
import os

_config = None


def get_config():
    global _config
    if _config is None:
        if not os.path.exists('config.json'):
            _config = {}
        else:
            try:
                with open('config.json', encoding='utf-8') as f:
                    _config = json.load(f)
            except Exception:
                _config = {}
    return _config


def save_config():
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(_config or {}, f, indent=True, sort_keys=True)
