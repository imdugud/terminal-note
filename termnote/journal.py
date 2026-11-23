from datetime import date, datetime

from .storage import journal_path_for


def add_entry(text, when=None):
    when = when or datetime.now()
    path = journal_path_for(when.date())
    with open(path, "a") as f:
        f.write(f"- {when.strftime('%H:%M')} {text}\n")


def list_entries_for(d):
    path = journal_path_for(d)
    if not path.exists():
        return []
    with open(path) as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def list_today():
    return list_entries_for(date.today())
