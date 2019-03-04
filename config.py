import toml

_config = None
with open("settings.toml", "r", encoding="utf-8") as f:
    _config = toml.load(f)


def get(key: str):
    global _config
    config = _config
    if config is None:
        raise Exception("Setting file is not loaded.")
    result = key.split(".")
    current = config
    for x in result:
        if current is None:
            return None
        if x not in current:
            return None
        current = current[x]
    return current
