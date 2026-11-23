import re
from datetime import date

from .config import load_config, save_config
from .dates import format_date, parse_date_arg, parse_stored_date
from .domains import require_domain
from .storage import TASKS_PATH

METADATA_RE = re.compile(r"\(\d{2}-\d{2}-\d{4}\)|@\S+|#\S+|\^\d+")
LINE_RE = re.compile(r"-\s*\[( |x)\]\s*(.*)")


def parse_task_line(line):
    line = line.rstrip("\n")
    if not line.strip():
        return None
    m = LINE_RE.match(line)
    if not m:
        return None
    done = m.group(1) == "x"
    rest = m.group(2)
    tokens = METADATA_RE.findall(rest)
    text = METADATA_RE.sub("", rest).strip()
    task_date = next((t[1:-1] for t in tokens if t.startswith("(")), None)
    domain = next((t[1:] for t in tokens if t.startswith("@")), None)
    tags = [t[1:] for t in tokens if t.startswith("#")]
    task_id = next((int(t[1:]) for t in tokens if t.startswith("^")), None)
    return {
        "id": task_id,
        "done": done,
        "text": text,
        "date": task_date,
        "domain": domain,
        "tags": tags,
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


def read_tasks():
    if not TASKS_PATH.exists():
        return []
    tasks = []
    with open(TASKS_PATH) as f:
        for line in f:
            parsed = parse_task_line(line)
            if parsed:
                tasks.append(parsed)
    return tasks


def write_tasks(tasks):
    with open(TASKS_PATH, "w") as f:
        for t in tasks:
            f.write(format_task_line(t) + "\n")


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
    tasks = read_tasks()
    tasks.append(task)
    write_tasks(tasks)
    return task


def list_today():
    today = date.today()
    result = []
    for t in read_tasks():
        if t["done"] or not t["date"]:
            continue
        if parse_stored_date(t["date"]) == today:
            result.append(t)
    return result


def list_overdue():
    today = date.today()
    result = []
    for t in read_tasks():
        if t["done"] or not t["date"]:
            continue
        if parse_stored_date(t["date"]) < today:
            result.append(t)
    return result


def mark_done(task_id):
    tasks = read_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            write_tasks(tasks)
            return t
    raise ValueError(f"No task with id ^{task_id}")
