from pathlib import Path

NOTE_HOME = Path.home() / "Documents" / "note"
CONFIG_PATH = NOTE_HOME / "config"
TASKS_PATH = NOTE_HOME / "tasks.md"
CALENDAR_PATH = NOTE_HOME / "calendar.md"
IDEAS_PATH = NOTE_HOME / "ideas.md"
JOURNAL_DIR = NOTE_HOME / "journal"


def ensure_storage():
    NOTE_HOME.mkdir(parents=True, exist_ok=True)
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_PATH.touch(exist_ok=True)
    CONFIG_PATH.touch(exist_ok=True)


def journal_path_for(d):
    # Filenames use ISO (YYYY-MM-DD) so they sort chronologically with `ls`,
    # independent of the DD-MM-YYYY format used for dates shown to the user.
    return JOURNAL_DIR / f"{d.isoformat()}.md"
