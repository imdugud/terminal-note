import configparser

from .storage import CONFIG_PATH

SECTION = "note"
MAX_DOMAINS = 3


def load_config():
    cp = configparser.ConfigParser()
    cp.read(CONFIG_PATH)
    domains_raw = cp.get(SECTION, "domains", fallback="")
    domains = [d.strip() for d in domains_raw.split(",") if d.strip()]
    last_id = cp.getint(SECTION, "last_id", fallback=0)
    return {"domains": domains, "last_id": last_id}


def save_config(domains, last_id):
    cp = configparser.ConfigParser()
    cp[SECTION] = {"domains": ", ".join(domains), "last_id": str(last_id)}
    with open(CONFIG_PATH, "w") as f:
        cp.write(f)
