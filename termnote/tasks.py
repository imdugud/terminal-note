import re
from datetime import date

from .config import load_config, save_config
from .dates import format_date, parse_date_arg, parse_stored_date
from .domains import require_domain
from .storage import TASKS_PATH

# Tokens must stand alone, so "x^2" or "a@b.com" in task text is not metadata.
METADATA_RE = re.compile(
    r"(?<!\S)(?:\(\d{2}-\d{2}-\d{4}\)|@\S+|#\S+|\^\d+)(?!\S)"
)
LINE_RE = re.compile(r"(\s*-\s*\[)([ xX])(\]\s*)(.*)")


def parse_task_line(line):
    m = LINE_RE.match(line.rstrip("\r\n"))
    if not m:
        return None
    rest = m.group(4)
    tags = []
    last = {}
    for token in METADATA_RE.finditer(rest):
        kind = token.group()[0]
        if kind == "#":
            tags.append(token)
        else:
            # format_task_line writes metadata after the text, so the last
            # token of a kind is the real one; earlier ones are task text.
            last[kind] = token

    text = rest
    metadata = tags + list(last.values())
    for token in sorted(metadata, key=lambda t: t.start(), reverse=True):
        # Join around the token, leaving other spacing in the text alone.
        before = text[: token.start()].rstrip()
        after = text[token.end() :].lstrip()
        text = f"{before} {after}"

    return {
        "id": int(last["^"].group()[1:]) if "^" in last else None,
        "done": m.group(2) != " ",
        "text": text.strip(),
        "date": last["("].group()[1:-1] if "(" in last else None,
        "domain": last["@"].group()[1:] if "@" in last else None,
        "tags": [t.group()[1:] for t in tags],
    }


def format_task_line(task):
    checkbox = "x" if task["done"] else " "
    parts = [f"- [{checkbox}] {task['text']}"]
    if task.get("date"):
        parts.append(f"({task['date']})")
    if task.get("domain"):
        parts.append(f"@{task['domain']}")
    parts += [f"#{t}" for t in task.get("tags", [])]
    if task.get("id") is not None:
        parts.append(f"^{task['id']}")
    return " ".join(parts)


def read_lines():
    if not TASKS_PATH.exists():
        return []
    # newline="" keeps the file's own line endings intact on rewrite.
    with open(TASKS_PATH, newline="") as f:
        return f.readlines()


def write_lines(lines):
    with open(TASKS_PATH, "w", newline="") as f:
        f.writelines(lines)


def read_tasks():
    parsed = (parse_task_line(line) for line in read_lines())
    return [t for t in parsed if t]


def next_task_id():
    """Self-healing ID assignment: never trust the stored counter alone,
    in case tasks.md was hand-edited with an ID higher than config tracks."""
    cfg = load_config()
    existing_ids = [t["id"] for t in read_tasks() if t["id"] is not None]
    max_existing = max(existing_ids) if existing_ids else 0
    next_id = max(cfg["last_id"], max_existing) + 1
    save_config(cfg["domains"], next_id)
    return next_id


def add_task(text, domain, tags=None, date_arg="today"):
    require_domain(domain)
    task_date = parse_date_arg(date_arg)
    task = {
        "id": next_task_id(),
        "done": False,
        "text": text,
        "date": format_date(task_date),
        "domain": domain,
        "tags": tags or [],
    }
    # Append rather than rewrite, so hand-edited content is never touched.
    lines = read_lines()
    needs_newline = bool(lines) and not lines[-1].endswith(("\n", "\r"))
    with open(TASKS_PATH, "a", newline="") as f:
        f.write(("\n" if needs_newline else "") + format_task_line(task) + "\n")
    return task


def _stored_date(task):
    """The task's date, or None if it is missing or impossible (hand-edited)."""
    if not task["date"]:
        return None
    try:
        return parse_stored_date(task["date"])
    except ValueError:
        return None


def list_today():
    today = date.today()
    return [t for t in read_tasks() if not t["done"] and _stored_date(t) == today]


def list_overdue():
    today = date.today()
    result = []
    for t in read_tasks():
        task_date = _stored_date(t)
        if not t["done"] and task_date and task_date < today:
            result.append(t)
    return result


def list_invalid_dates():
    """Open tasks whose date can't exist; no date listing can include them."""
    return [
        t
        for t in read_tasks()
        if not t["done"] and t["date"] and _stored_date(t) is None
    ]


def mark_done(task_id):
    lines = read_lines()
    for i, line in enumerate(lines):
        t = parse_task_line(line)
        if t and t["id"] == task_id:
            # Change only the checkbox, so the rest of the line stays as written.
            lines[i] = LINE_RE.sub(r"\g<1>x\g<3>\g<4>", line, count=1)
            write_lines(lines)
            t["done"] = True
            return t
    raise ValueError(f"No task with id ^{task_id}")
