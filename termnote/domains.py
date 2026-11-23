from .config import MAX_DOMAINS, load_config, save_config


def add_domain(name):
    cfg = load_config()
    if name in cfg["domains"]:
        raise ValueError(f"Domain '{name}' already exists.")
    if len(cfg["domains"]) >= MAX_DOMAINS:
        raise ValueError(
            f"Maximum of {MAX_DOMAINS} domains reached: {', '.join(cfg['domains'])}"
        )
    domains = cfg["domains"] + [name]
    save_config(domains, cfg["last_id"])
    return domains


def list_domains():
    return load_config()["domains"]


def require_domain(name):
    cfg = load_config()
    if name not in cfg["domains"]:
        raise ValueError(
            f"Unknown domain '{name}'. Run 'note domain add {name}' first."
        )
