# src/utils/helpers.py
def safe_get(data, *keys, default=None):
    """Safely navigate nested dictionaries/lists"""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError, IndexError):
        return default
